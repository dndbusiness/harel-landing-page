"""מחשבון ברוטו→נטו לשכיר. מודול נפרד; כל המספרים מקובץ פרמטרים עם שנה ומקור.

אין כאן אף מדרגה או שיעור. בלי קובץ מלא — המודול מסרב לחשב.
מודל מפושט: מס הכנסה מדורג פחות נקודות זיכוי, ביטוח לאומי ומס בריאות מדורגים
(חלק העובד). לא מטפל בהפרשות פנסיה, זקיפות שווי וזיכויים מיוחדים — אלה קלט ידני.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import yaml

from ..model.money import from_decimal, scale


class TaxParamsMissing(RuntimeError):
    pass


@dataclass
class Bracket:
    up_to: int | None      # אגורות לחודש; None = ללא תקרה
    rate_pct: Decimal


def _brackets(raw, name) -> list[Bracket]:
    if not raw:
        raise TaxParamsMissing(f"חסרות מדרגות: {name}")
    out = []
    for b in raw:
        if b.get("rate_pct") in (None, ""):
            raise TaxParamsMissing(f"שיעור חסר ב-{name}")
        out.append(Bracket(from_decimal(str(b["up_to"])) if b.get("up_to") not in (None, "") else None,
                           Decimal(str(b["rate_pct"]))))
    return out


def _progressive(amount: int, brackets: list[Bracket]) -> int:
    total, lower = 0, 0
    for b in brackets:
        top = amount if b.up_to is None else min(amount, b.up_to)
        if top > lower:
            total += scale(top - lower, b.rate_pct / 100)
        if b.up_to is None or amount <= b.up_to:
            break
        lower = b.up_to
    return total


@dataclass
class TaxModel:
    year: int
    source: str
    income_tax: list[Bracket]
    national_insurance: list[Bracket]
    health: list[Bracket]
    credit_point_value: int
    default_credit_points: Decimal

    @classmethod
    def load(cls, path: str | Path) -> "TaxModel":
        p = Path(path)
        if not p.exists():
            raise TaxParamsMissing(f"אין קובץ מס: {p}. קלט שכר בנטו, או מלאו את הקובץ ממקור רשמי.")
        d = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        if not d.get("source"):
            raise TaxParamsMissing("קובץ המס חייב לציין מקור")
        for k in ("credit_point_monthly_value", "default_credit_points"):
            if d.get(k) in (None, ""):
                raise TaxParamsMissing(f"חסר {k}")
        return cls(year=int(d["year"]), source=d["source"],
                   income_tax=_brackets(d.get("income_tax_brackets_monthly"), "מס הכנסה"),
                   national_insurance=_brackets(d.get("national_insurance_brackets_monthly"), "ביטוח לאומי"),
                   health=_brackets(d.get("health_tax_brackets_monthly"), "מס בריאות"),
                   credit_point_value=from_decimal(str(d["credit_point_monthly_value"])),
                   default_credit_points=Decimal(str(d["default_credit_points"])))

    def net(self, gross: int, credit_points: Decimal | None = None) -> int:
        pts = self.default_credit_points if credit_points is None else credit_points
        tax = max(0, _progressive(gross, self.income_tax) - scale(self.credit_point_value, pts))
        return gross - tax - _progressive(gross, self.national_insurance) - _progressive(gross, self.health)
