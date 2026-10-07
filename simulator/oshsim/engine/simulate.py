"""מנוע התרחישים (סעיף 8).

Replay: משחזר את ההיסטוריה עם שינויים. Forward: ממשיך קדימה לפי הדפוסים (הערכה).

עמלות וריבית בהיסטוריה מעוגנות בסכום שנרשם בפועל, ובתרחיש מתווסף רק ההפרש שהמודל
מחשב (עמלה: לפי שינוי במספר פעולות (י); ריבית: לפי שינוי ביתרה היומית או בשיעור).
כך תרחיש ריק זהה לאגורה לדף, גם כשהמודל עצמו לא מושלם — ואחוז הטעות של המודל
מוצג בנפרד בכיול.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Callable, Optional

import yaml

from ..model.money import Agorot, fmt
from ..model.transaction import DIRECT, Transaction
from ..patterns.calendar import BusinessCalendar
from ..patterns.recurring import ONE_OFF, VARIABLE, RecurringPattern
from .deltas import Context, Delta, RateChange, SimRow, delta_from_dict
from .params import Params, RatePeriod

FEE, INTEREST = "direct_channel_fee", "interest"


def _month(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _prev_month(d: date) -> str:
    first = d.replace(day=1) - timedelta(days=1)
    return _month(first)


def _round(x: Decimal) -> int:
    return int(x.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


@dataclass
class Scenario:
    name: str
    mode: str = "replay"
    deltas: list[Delta] = field(default_factory=list)
    forward_months: int = 3
    description: str = ""

    @classmethod
    def load(cls, path: str | Path) -> "Scenario":
        p = Path(path)
        d = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return cls(name=d.get("name", p.stem), mode=d.get("mode", "replay"),
                   deltas=[delta_from_dict(x, p.parent) for x in d.get("deltas") or []],
                   forward_months=int(d.get("forward_months", 3)), description=d.get("description", ""))


@dataclass
class DayEntry:
    date: date
    rows: list[SimRow]
    balance: Agorot


@dataclass
class FeeCalibration:
    posting_date: date
    month: str
    observed_count: int
    reference_count: Optional[int]
    model_amount: Optional[int]
    actual_amount: int

    @property
    def ok(self) -> Optional[bool]:
        return None if self.model_amount is None else self.model_amount == self.actual_amount


@dataclass
class InterestCalibration:
    posting_date: date
    period_start: date
    period_end: date
    model_amount: int
    actual_amount: int
    partial_period: bool

    @property
    def error_pct(self) -> Optional[Decimal]:
        if self.actual_amount == 0:
            return None
        return (Decimal(self.model_amount - self.actual_amount) / abs(Decimal(self.actual_amount)) * 100
                ).quantize(Decimal("0.1"))


@dataclass
class SimResult:
    name: str
    mode: str
    opening: Agorot
    days: list[DayEntry]
    daily_balance: dict[date, Agorot]
    start: date
    end: date
    projected_from: Optional[date] = None
    notes: list[str] = field(default_factory=list)
    fee_calibration: list[FeeCalibration] = field(default_factory=list)
    interest_calibration: list[InterestCalibration] = field(default_factory=list)
    interest_recomputed: bool = False
    interest_is_estimate: bool = True
    unposted_interest: Agorot = 0
    removed: list[SimRow] = field(default_factory=list)

    def rows(self) -> list[SimRow]:
        return [r for d in self.days for r in d.rows]

    @property
    def closing(self) -> Agorot:
        return self.daily_balance[self.end]

    @property
    def min_balance(self) -> tuple[date, Agorot]:
        d = min(self.daily_balance, key=lambda k: (self.daily_balance[k], k))
        return d, self.daily_balance[d]

    def days_over_limit(self, limit: Optional[int]) -> Optional[int]:
        if limit is None:
            return None
        return sum(1 for b in self.daily_balance.values() if b < -limit)

    def total_of(self, kind: str) -> Agorot:
        return sum(r.amount for r in self.rows() if r.kind == kind)


class Engine:
    def __init__(self, txns: list[Transaction], opening: Agorot, params: Params,
                 calendar: BusinessCalendar, kind_of: Callable[[Transaction], str],
                 patterns: Optional[list[RecurringPattern]] = None, tax_model_path: Optional[Path] = None):
        self.txns = txns
        self.opening = opening
        self.params = params
        self.cal = calendar
        self.kind_of = kind_of
        self.patterns = patterns or []
        self.tax_model_path = tax_model_path
        self.hist_rows = [SimRow(t.date, t.description, t.amount_agorot, t.channel, "historical", t.reference,
                                 t.category, t.subcategory, kind_of(t), t.id, t.recurring_id, seq=i)
                          for i, t in enumerate(txns)]
        self.first, self.last = txns[0].date, txns[-1].date
        self.hist_counts = self._direct_counts(self.hist_rows)
        self.hist_balance = self._balances(self.hist_rows, self.first, self.last)

    # ---------- עזר ----------
    @staticmethod
    def _direct_counts(rows: list[SimRow]) -> dict[str, int]:
        c: dict[str, int] = defaultdict(int)
        for r in rows:
            if r.origin != "removed" and r.channel == DIRECT and r.kind not in (FEE, INTEREST):
                c[_month(r.date)] += 1
        return c

    def _balances(self, rows, start, end) -> dict[date, int]:
        by_day: dict[date, int] = defaultdict(int)
        for r in rows:
            by_day[r.date] += r.amount
        out, bal, d = {}, self.opening, start
        while d <= end:
            bal += by_day.get(d, 0)
            out[d] = bal
            d += timedelta(days=1)
        return out

    def _daily_interest(self, bal: int, d: date, table: list[RatePeriod]) -> Decimal:
        """ריבית של יום אחד באגורות (שלילי = חיוב). Decimal — מעוגל רק ברישום."""
        r = self.params.interest.rate_on(d, table)
        if r is None or bal == 0:
            return Decimal(0)
        dc = Decimal(100 * self.params.interest.day_count)
        if bal > 0:
            return Decimal(bal) * r.credit_annual_pct / dc
        limit = self.params.credit_limit_agorot
        if limit is not None and r.overlimit_annual_pct is not None and -bal > limit:
            return (Decimal(-limit) * r.debit_annual_pct + Decimal(bal + limit) * r.overlimit_annual_pct) / dc
        return Decimal(bal) * r.debit_annual_pct / dc

    def _fee_total(self, r: SimRow) -> tuple[str, int]:
        """(חודש, מספר פעולות אמיתי) לשורת עמלה היסטורית. האסמכתה היא המונה כשהיא מספר."""
        m = _prev_month(r.date)
        ref = r.reference.strip()
        return m, int(ref) if ref.isdigit() else self.hist_counts.get(m, 0)

    # ---------- כיול ----------
    def calibrate_fees(self) -> list[FeeCalibration]:
        out = []
        for r in self.hist_rows:
            if r.kind != FEE:
                continue
            m = _prev_month(r.date)
            ref = int(r.reference) if r.reference.strip().isdigit() else None
            total = ref if ref is not None else self.hist_counts.get(m, 0)
            model = -self.params.direct_fee.fee(total) if self.params.direct_fee else None
            out.append(FeeCalibration(r.date, m, self.hist_counts.get(m, 0), ref, model, r.amount))
        return out

    def calibrate_interest(self) -> list[InterestCalibration]:
        if not self.params.interest.known:
            return []
        out, prev = [], None
        for r in self.hist_rows:
            if r.kind != INTEREST:
                continue
            start = prev or self.first
            acc = Decimal(0)
            d = start
            while d < r.date:
                acc += self._daily_interest(self.hist_balance[d], d, self.params.interest.rates)
                d += timedelta(days=1)
            out.append(InterestCalibration(r.date, start, r.date - timedelta(days=1), _round(acc), r.amount,
                                           partial_period=prev is None))
            prev = r.date
        return out

    # ---------- Forward ----------
    def _project(self, start: date, end: date) -> list[SimRow]:
        rows: list[SimRow] = []
        y, m = start.year, start.month
        while date(y, m, 1) <= end:
            nxt = date(y + (m == 12), m % 12 + 1, 1)
            month = f"{y:04d}-{m:02d}"
            for p in self.patterns:
                if p.kind == ONE_OFF:
                    continue
                nominal = date(y, m, min(p.day_of_month, (nxt - timedelta(days=1)).day))
                d = self.cal.shift(nominal, p.friday_rule, p.closed_rule)
                if start <= d <= end:
                    rows.append(SimRow(d, p.counterparty, p.amount_for(month), p.channel, "projected",
                                       category=p.category, recurring_id=p.id,
                                       note="הערכה — סכום חציוני" if p.kind == VARIABLE else "הערכה"))
            fee_day = self.cal.first_business_day(y, m)
            if self.params.direct_fee and start <= fee_day <= end:
                rows.append(SimRow(fee_day, "עמלת פעולות בערוץ ישיר (הערכה)", 0, None, "fee", kind=FEE,
                                   category="עמלות וריבית", note="מחושב ממספר פעולות (י) בחודש הקודם"))
            if self.params.interest.known and m in self.params.interest.forward_posting_months:
                post = self.cal.first_business_day(y, m)
                if start <= post <= end:
                    rows.append(SimRow(post, "ריבית (הערכה)", 0, None, "interest", kind=INTEREST,
                                       category="עמלות וריבית", note="מודל ריבית — הערכה"))
            y, m = nxt.year, nxt.month
        return rows

    # ---------- ריצה ----------
    def run(self, scenario: Scenario) -> SimResult:
        start, end = self.first, self.last
        rows = [replace(r) for r in self.hist_rows]
        projected_from = None
        notes: list[str] = []
        if scenario.mode == "forward":
            projected_from = self.last + timedelta(days=1)
            e = self.last.replace(day=1)
            for _ in range(scenario.forward_months + 1):
                e = (e + timedelta(days=32)).replace(day=1)
            end = e - timedelta(days=1)
            rows += self._project(projected_from, end)
            notes.append(f"מ-{projected_from:%d/%m/%Y} התנועות הן הקרנה לפי דפוסים — הערכה בלבד")
            if not self.params.interest.known:
                notes.append("לא הוזן שיעור ריבית: בהקרנה אין חיובי ריבית")

        ctx = Context(self.cal, start, end, self.tax_model_path, notes)
        rate_table = self.params.interest.rates
        for delta in scenario.deltas:
            rows = delta.apply(rows, ctx)
            if isinstance(delta, RateChange):
                if not self.params.interest.known:
                    raise ValueError("שינוי ריבית דורש שיעור בסיס בקובץ הפרמטרים (אחרת אין מול מה להשוות)")
                rate_table = delta.rates

        interest_recomputed = self.params.interest.known
        if not interest_recomputed and scenario.deltas:
            notes.append("לא הוזן שיעור ריבית: ריבית העו\"ש נשארה כפי שנרשמה בפועל ולא הותאמה לשינוי ביתרה")
        if not self.params.direct_fee and scenario.deltas:
            notes.append("לא הוגדרה עמלת ערוץ ישיר: העמלה נשארה כפי שנרשמה בפועל")

        counts = self._direct_counts(rows)
        removed = [r for r in rows if r.origin == "removed"]
        live = sorted((r for r in rows if r.origin != "removed"),
                      key=lambda r: (r.date, 0 if r.txn_id else 1, r.seq))   # שורה מהדף שומרת על מקומה גם אחרי שינוי
        by_day: dict[date, list[SimRow]] = defaultdict(list)
        for r in live:
            by_day[r.date].append(r)

        days: list[DayEntry] = []
        daily: dict[date, int] = {}
        bal = self.opening
        acc_run = Decimal(0)    # ריבית שנצברה בריצה הזו מאז הרישום הקודם
        acc_hist = Decimal(0)   # אותו דבר על יתרות הבסיס ושיעורי הבסיס
        d = start
        while d <= end:
            todays = []
            for r in by_day.get(d, []):
                if r.kind == FEE and self.params.direct_fee:
                    fee = self.params.direct_fee
                    if r.origin == "historical":
                        m, base_total = self._fee_total(r)
                        run_total = base_total + counts.get(m, 0) - self.hist_counts.get(m, 0)
                        diff = fee.fee(run_total) - fee.fee(base_total)
                        if diff:
                            r = replace(r, origin="modified", base_amount=r.amount, amount=r.amount - diff,
                                        reference=str(run_total), note=f"עמלה מחושבת מחדש: {run_total} פעולות (י)")
                    else:
                        n = counts.get(_prev_month(d), 0)
                        r = replace(r, amount=-fee.fee(n), reference=str(n))
                elif r.kind == INTEREST and interest_recomputed:
                    if r.origin == "historical":
                        diff = _round(acc_run - acc_hist)
                        if diff:
                            r = replace(r, origin="modified", base_amount=r.amount, amount=r.amount + diff,
                                        note="ריבית הותאמה לשינוי ביתרה/בשיעור")
                    else:
                        r = replace(r, amount=_round(acc_run))
                    acc_run = acc_hist = Decimal(0)
                todays.append(r)
            bal += sum(r.amount for r in todays)
            daily[d] = bal
            if interest_recomputed:
                acc_run += self._daily_interest(bal, d, rate_table)
                if d in self.hist_balance:
                    acc_hist += self._daily_interest(self.hist_balance[d], d, self.params.interest.rates)
            if todays:
                days.append(DayEntry(d, todays, bal))
            d += timedelta(days=1)

        res = SimResult(scenario.name, scenario.mode, self.opening, days, daily, start, end, projected_from,
                        notes, removed=removed, interest_recomputed=interest_recomputed)
        res.fee_calibration = self.calibrate_fees()
        res.interest_calibration = self.calibrate_interest()
        full = [c for c in res.interest_calibration if not c.partial_period and c.error_pct is not None]
        res.interest_is_estimate = (not interest_recomputed or not full or
                                    any(abs(c.error_pct) > self.params.interest.max_calibration_error_pct for c in full))
        if interest_recomputed:
            res.unposted_interest = _round(acc_run)
        return res


def identity_mismatches(result: SimResult, txns: list[Transaction]) -> list[str]:
    """קריטריון קבלה: תרחיש ריק = הדף המקורי, שורה-שורה ויתרה-יתרה."""
    out = []
    rows = result.rows()
    if len(rows) != len(txns):
        out.append(f"מספר שורות: {len(rows)} מול {len(txns)}")
    for r, t in zip(rows, txns):
        if (r.date, r.description, r.amount, r.reference) != (t.date, t.description, t.amount_agorot, t.reference):
            out.append(f"{t.date:%d/%m/%Y} {t.description}: {fmt(r.amount)} מול {fmt(t.amount_agorot)}")
    for t in txns:
        if t.day_balance_agorot is not None and result.daily_balance.get(t.date) != t.day_balance_agorot:
            out.append(f"יתרה {t.date:%d/%m/%Y}: {fmt(result.daily_balance.get(t.date))} מול {fmt(t.day_balance_agorot)}")
    return out
