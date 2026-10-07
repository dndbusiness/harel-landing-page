"""סוגי שינויים בתרחיש (סעיף 8). כל שינוי פועל על רשימת שורות מתוזמנות לפני
חישוב היתרה היומית; עמלות וריבית מחושבות אחר כך מהשורות שהתקבלו.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Optional

from ..model.money import fmt, from_decimal, parse_amount, scale
from ..model.transaction import DIRECT
from ..patterns.calendar import BusinessCalendar
from .tax import TaxModel


@dataclass
class SimRow:
    date: date
    description: str
    amount: int
    channel: Optional[str] = None
    origin: str = "historical"     # historical / modified / removed / added / fee / interest / projected
    reference: str = ""
    category: str = ""
    subcategory: str = ""
    kind: str = ""                 # direct_channel_fee / interest / card_charge
    txn_id: str = ""
    recurring_id: Optional[str] = None
    base_amount: Optional[int] = None
    note: str = ""
    seq: int = 0                   # סדר בתוך היום


@dataclass
class Selector:
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None     # regex
    recurring_id: Optional[str] = None
    direction: Optional[str] = None       # credit / debit

    def matches(self, r: SimRow) -> bool:
        if r.kind in ("direct_channel_fee", "interest"):
            return False   # מחושבות — לא נבחרות ישירות
        if self.category and r.category != self.category:
            return False
        if self.subcategory and r.subcategory != self.subcategory:
            return False
        if self.description and not re.search(self.description, r.description):
            return False
        if self.recurring_id and r.recurring_id != self.recurring_id:
            return False
        if self.direction == "credit" and r.amount <= 0:
            return False
        if self.direction == "debit" and r.amount >= 0:
            return False
        return True

    def describe(self) -> str:
        names = {"category": "קטגוריה", "subcategory": "תת-קטגוריה", "description": "תיאור",
                 "recurring_id": "דפוס", "direction": "כיוון"}
        parts = [f"{names[k]} '{v}'" for k, v in vars(self).items() if v]
        return ", ".join(parts) or "כל התנועות"


def _in_range(d: date, start: Optional[date], end: Optional[date]) -> bool:
    return (start is None or d >= start) and (end is None or d <= end)


@dataclass
class Context:
    calendar: BusinessCalendar
    start: date
    end: date
    tax_model_path: Optional[Path] = None
    notes: list[str] = field(default_factory=list)


class Delta:
    label: str = ""

    def apply(self, rows: list[SimRow], ctx: Context) -> list[SimRow]:
        raise NotImplementedError


@dataclass
class ChangeAmount(Delta):
    """שכר גבוה/נמוך, הוצאה גבוהה/נמוכה בקטגוריה או מנפיק.
    pct: אחוז שינוי בגודל (10 = +10%). amount: ₪ שמתווספים לגודל כל שורה.
    set_to: ₪ — הגודל החדש של כל שורה שנבחרה (הסימן נשמר: זכות נשארת זכות).
    basis='gross': pct/amount חלים על ברוטו `gross_monthly`; ההפרש בנטו מחושב במודול המס.
    """
    select: Selector
    pct: Optional[Decimal] = None
    amount: Optional[int] = None
    start: Optional[date] = None
    end: Optional[date] = None
    basis: str = "net"
    gross_monthly: Optional[int] = None
    credit_points: Optional[Decimal] = None
    label: str = ""
    set_to: Optional[int] = None

    def apply(self, rows, ctx):
        if sum(x is not None for x in (self.pct, self.amount, self.set_to)) != 1:
            raise ValueError(f"{self.label}: צריך pct, amount או set_to (אחד בלבד)")
        if self.set_to is not None and self.basis == "gross":
            raise ValueError(f"{self.label}: set_to הוא סכום נטו בדף, לא ברוטו")
        net_delta = None
        if self.basis == "gross":
            if self.gross_monthly is None:
                raise ValueError(f"{self.label}: שינוי בברוטו דורש gross_monthly")
            tm = TaxModel.load(ctx.tax_model_path) if ctx.tax_model_path else TaxModel.load(Path("missing"))
            new_gross = (scale(self.gross_monthly, 1 + self.pct / 100) if self.pct is not None
                         else self.gross_monthly + self.amount)
            net_delta = tm.net(new_gross, self.credit_points) - tm.net(self.gross_monthly, self.credit_points)
            ctx.notes.append(f"{self.label}: ברוטו {fmt(self.gross_monthly)}→{fmt(new_gross)}, "
                             f"נטו {'+' if net_delta >= 0 else ''}{fmt(net_delta)} לחודש (מודל מס {tm.year}, {tm.source})")
        hit = card_hits = 0
        out = []
        for r in rows:
            if r.origin != "removed" and self.select.matches(r) and _in_range(r.date, self.start, self.end):
                sign = 1 if r.amount >= 0 else -1
                mag = abs(r.amount)
                if self.set_to is not None:
                    new_mag = abs(self.set_to)
                elif net_delta is not None:
                    new_mag = mag + net_delta
                elif self.pct is not None:
                    new_mag = scale(mag, 1 + self.pct / 100)
                else:
                    new_mag = mag + self.amount
                new_mag = max(0, new_mag)
                hit += 1
                if r.kind == "card_charge":
                    card_hits += 1
                out.append(replace(r, amount=sign * new_mag, origin="modified",
                                   base_amount=r.base_amount if r.base_amount is not None else r.amount,
                                   note=self.label))
            else:
                out.append(r)
        if card_hits:
            ctx.notes.append(f"{self.label}: {card_hits} חיובי כרטיס אשראי שונו כסכום כולל — זה לא שינוי "
                             "בקטגוריית הוצאה, כי אין דף אשראי מקושר שמפרק את החיוב")
        if hit == 0:
            ctx.notes.append(f"אזהרה — {self.label}: אין שורות שמתאימות ל-{self.select.describe()}")
        return out


@dataclass
class RemoveRows(Delta):
    """ביטול הוראת קבע / מנפיק בטווח תאריכים."""
    select: Selector
    start: Optional[date] = None
    end: Optional[date] = None
    label: str = ""

    def apply(self, rows, ctx):
        hit = 0
        out = []
        for r in rows:
            if r.origin != "removed" and self.select.matches(r) and _in_range(r.date, self.start, self.end):
                hit += 1
                out.append(replace(r, origin="removed", base_amount=r.amount, amount=0, note=self.label))
            else:
                out.append(r)
        if hit == 0:
            ctx.notes.append(f"אזהרה — {self.label}: אין שורות לביטול ({self.select.describe()})")
        return out


@dataclass
class AddRecurring(Delta):
    description: str
    amount: int
    day_of_month: int
    start: Optional[date] = None
    end: Optional[date] = None
    channel: Optional[str] = None
    friday_rule: str = "same"
    closed_rule: str = "forward"
    category: str = ""
    label: str = ""

    def apply(self, rows, ctx):
        s, e = max(self.start or ctx.start, ctx.start), min(self.end or ctx.end, ctx.end)
        y, m = s.year, s.month
        out = list(rows)
        while date(y, m, 1) <= e:
            nxt = date(y + (m == 12), m % 12 + 1, 1)
            nominal = date(y, m, min(self.day_of_month, (nxt - timedelta(days=1)).day))
            d = ctx.calendar.shift(nominal, self.friday_rule, self.closed_rule)
            if s <= d <= e:
                out.append(SimRow(d, self.description, self.amount, self.channel, "added",
                                  category=self.category, note=self.label))
            y, m = nxt.year, nxt.month
        return out


@dataclass
class OneOff(Delta):
    date: date
    amount: int
    description: str
    channel: Optional[str] = None
    category: str = ""
    label: str = ""

    def apply(self, rows, ctx):
        if not (ctx.start <= self.date <= ctx.end):
            ctx.notes.append(f"אזהרה — {self.label}: התאריך {self.date:%d/%m/%Y} מחוץ לטווח הסימולציה")
            return rows
        return rows + [SimRow(self.date, self.description, self.amount, self.channel, "added",
                              category=self.category, note=self.label)]


@dataclass
class LoanSchedule(Delta):
    """פירעון/מחזור הלוואה לפי לוח סילוקין מהלקוח — לא ניחוש.
    מבטל את תשלומי ההלוואה הקיימים מ-start, ומוסיף את שורות הלוח (ואופציונלית סכום פירעון).
    """
    select: Selector
    start: date
    schedule: list[tuple[date, int]] = field(default_factory=list)
    payoff_amount: Optional[int] = None
    description: str = "החזר הלוואה (תרחיש)"
    channel: Optional[str] = None
    label: str = ""

    @staticmethod
    def read_schedule(path: str | Path) -> list[tuple[date, int]]:
        """CSV עם עמודות date,amount (חובה בסימן מינוס או חיובי — נרשם כחובה)."""
        out = []
        with Path(path).open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                out.append((date.fromisoformat(r["date"]), -abs(parse_amount(r["amount"]))))
        if not out:
            raise ValueError(f"לוח סילוקין ריק: {path}")
        return out

    def apply(self, rows, ctx):
        rows = RemoveRows(self.select, self.start, None, self.label).apply(rows, ctx)
        out = list(rows)
        if self.payoff_amount:
            out.append(SimRow(self.start, "פירעון מוקדם (תרחיש)", -abs(self.payoff_amount), self.channel,
                              "added", category="הלוואות", note=self.label))
        for d, a in self.schedule:
            if ctx.start <= d <= ctx.end:
                out.append(SimRow(d, self.description, a, self.channel, "added", category="הלוואות", note=self.label))
        return out


@dataclass
class RateChange(Delta):
    """טבלת ריביות חלופית לתרחיש. לא נוגעת בשורות — המנוע קורא אותה בחישוב הריבית."""
    rates: list = field(default_factory=list)   # list[RatePeriod]
    label: str = ""

    def apply(self, rows, ctx):
        return rows


# ---------- טעינה מ-YAML ----------

def _d(v) -> Optional[date]:
    return date.fromisoformat(str(v)) if v not in (None, "") else None


def _money(v) -> Optional[int]:
    if v in (None, ""):
        return None
    if isinstance(v, float):
        raise TypeError("סכומים בתרחיש נכתבים כמחרוזת ('500.00'), לא כמספר עשרוני")
    return from_decimal(str(v))


def _pct(v) -> Optional[Decimal]:
    if v in (None, ""):
        return None
    if isinstance(v, float):
        raise TypeError("אחוזים בתרחיש נכתבים כמחרוזת או מספר שלם ('7.5'), לא כמספר עשרוני")
    return Decimal(str(v))


def delta_from_dict(d: dict, base_dir: Path) -> Delta:
    from .params import Params
    t = d["type"]
    label = d.get("label", t)
    sel = Selector(**(d.get("select") or {}))
    ch = DIRECT if d.get("channel") == "direct" else d.get("channel")
    if t == "change_amount":
        # date: קיצור לשינוי בתנועות של יום אחד (start = end = date)
        start, end = (_d(d["date"]), _d(d["date"])) if d.get("date") else (_d(d.get("start")), _d(d.get("end")))
        return ChangeAmount(sel, _pct(d.get("pct")), _money(d.get("amount")), start, end,
                            d.get("basis", "net"), _money(d.get("gross_monthly")), _pct(d.get("credit_points")), label,
                            _money(d.get("set_to")))
    if t == "remove":
        return RemoveRows(sel, _d(d.get("start")), _d(d.get("end")), label)
    if t == "add_recurring":
        return AddRecurring(d["description"], _money(d["amount"]), int(d["day_of_month"]), _d(d.get("start")),
                            _d(d.get("end")), ch, d.get("friday_rule", "same"), d.get("closed_rule", "forward"),
                            d.get("category", ""), label)
    if t == "one_off":
        return OneOff(_d(d["date"]), _money(d["amount"]), d["description"], ch, d.get("category", ""), label)
    if t == "loan_schedule":
        sched = LoanSchedule.read_schedule(base_dir / d["schedule_csv"]) if d.get("schedule_csv") else []
        if not sched and not d.get("payoff_amount"):
            raise ValueError(f"{label}: נדרש לוח סילוקין (schedule_csv) או סכום פירעון מהלקוח")
        return LoanSchedule(sel, _d(d["start"]), sched, _money(d.get("payoff_amount")),
                            d.get("description", "החזר הלוואה (תרחיש)"), ch, label)
    if t == "rate_change":
        return RateChange(Params.from_dict({"interest": {"rates": d["rates"]}}).interest.rates, label)
    raise ValueError(f"סוג שינוי לא מוכר: {t}")
