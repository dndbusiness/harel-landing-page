"""טבלת פרמטרים (סעיף 1.5): כל ריבית/עמלה/מסגרת עם מקור ותאריך, לא בקוד."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

import yaml

from ..model.money import from_decimal


def _dec(v) -> Optional[Decimal]:
    if v is None or v == "":
        return None
    if isinstance(v, float):
        raise TypeError("ערכים בקובץ פרמטרים חייבים להיכתב כמחרוזת ('1.76'), לא כמספר עשרוני")
    return Decimal(str(v))


@dataclass
class DirectFeeParams:
    rate_agorot: int
    free_quota: int = 0
    source: str = ""
    as_of: str = ""
    calibrated_for: str = ""

    def fee(self, count: int) -> int:
        return max(0, count - self.free_quota) * self.rate_agorot


@dataclass
class RatePeriod:
    start: date
    debit_annual_pct: Decimal
    credit_annual_pct: Decimal = Decimal(0)
    overlimit_annual_pct: Optional[Decimal] = None
    source: str = ""


@dataclass
class InterestParams:
    rates: list[RatePeriod] = field(default_factory=list)
    day_count: int = 365
    max_calibration_error_pct: Decimal = Decimal(5)
    forward_posting_months: tuple[int, ...] = (1, 4, 7, 10)

    def rate_on(self, d: date, table: list[RatePeriod] | None = None) -> RatePeriod | None:
        table = self.rates if table is None else table
        cur = None
        for r in sorted(table, key=lambda r: r.start):
            if r.start <= d:
                cur = r
        return cur

    @property
    def known(self) -> bool:
        return bool(self.rates)


@dataclass
class Params:
    direct_fee: Optional[DirectFeeParams]
    interest: InterestParams
    credit_limit_agorot: Optional[int] = None
    credit_limit_source: str = ""
    raw: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path) -> "Params":
        d = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return cls.from_dict(d)

    @classmethod
    def from_dict(cls, d: dict) -> "Params":
        fee = None
        f = d.get("direct_channel_fee")
        if f and f.get("rate") is not None:
            fee = DirectFeeParams(rate_agorot=from_decimal(_dec(f["rate"])), free_quota=int(f.get("free_quota") or 0),
                                  source=f.get("source", ""), as_of=str(f.get("date", "")),
                                  calibrated_for=f.get("calibrated_for", ""))
        i = d.get("interest") or {}
        rates = [RatePeriod(start=date.fromisoformat(str(r["from"])),
                            debit_annual_pct=_dec(r["debit_annual_pct"]),
                            credit_annual_pct=_dec(r.get("credit_annual_pct")) or Decimal(0),
                            overlimit_annual_pct=_dec(r.get("overlimit_annual_pct")),
                            source=r.get("source", ""))
                 for r in i.get("rates") or []]
        interest = InterestParams(rates=rates, day_count=int(i.get("day_count", 365)),
                                  max_calibration_error_pct=_dec(i.get("max_calibration_error_pct")) or Decimal(5),
                                  forward_posting_months=tuple(i.get("forward_posting_months") or (1, 4, 7, 10)))
        cl = d.get("credit_limit") or {}
        limit = from_decimal(_dec(cl["amount"])) if cl.get("amount") not in (None, "") else None
        return cls(direct_fee=fee, interest=interest, credit_limit_agorot=limit,
                   credit_limit_source=cl.get("source", ""), raw=d)

    def table_rows(self) -> list[tuple[str, str, str, str]]:
        """(פרמטר, ערך, מקור, תאריך/הערה) — לגיליון 'הנחות ופרמטרים'."""
        rows = []
        if self.direct_fee:
            f = self.direct_fee
            rows.append(("עמלת ערוץ ישיר לפעולה", f"{f.rate_agorot // 100}.{f.rate_agorot % 100:02d} ₪",
                         f.source, f.as_of))
            rows.append(("מכסת פעולות חינם", str(f.free_quota), f.source, f.calibrated_for))
        else:
            rows.append(("עמלת ערוץ ישיר", "לא הוגדר — לא מחושבת מחדש", "", ""))
        if self.interest.rates:
            for r in self.interest.rates:
                rows.append((f"ריבית חובה שנתית מ-{r.start:%d/%m/%Y}", f"{r.debit_annual_pct}%", r.source, "קלט יועץ"))
                rows.append((f"ריבית זכות שנתית מ-{r.start:%d/%m/%Y}", f"{r.credit_annual_pct}%", r.source, "קלט יועץ"))
                if r.overlimit_annual_pct is not None:
                    rows.append((f"ריבית חריגה שנתית מ-{r.start:%d/%m/%Y}", f"{r.overlimit_annual_pct}%", r.source, "קלט יועץ"))
        else:
            rows.append(("ריבית עו\"ש", "לא הוזנה — הריבית ההיסטורית נשמרת, ההשפעה המשנית לא מחושבת", "", ""))
        rows.append(("בסיס ימים לריבית", str(self.interest.day_count), "", ""))
        if self.credit_limit_agorot is not None:
            a = self.credit_limit_agorot
            rows.append(("מסגרת אשראי", f"{a // 100:,}.{a % 100:02d} ₪", self.credit_limit_source, "קלט יועץ"))
        else:
            rows.append(("מסגרת אשראי", "לא הוזנה — ימי חריגה לא מחושבים", "", ""))
        return rows
