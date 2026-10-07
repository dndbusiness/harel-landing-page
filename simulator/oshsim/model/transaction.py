from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Optional

from .money import Agorot

DIRECT = "direct"   # (י) פעולה בערוץ ישיר
BANKER = "banker"   # (פ) פעולה של בנקאי


@dataclass
class Transaction:
    date: date
    description: str
    amount_agorot: Agorot                 # זכות +, חובה −
    reference: str = ""
    value_date: Optional[date] = None
    day_balance_agorot: Optional[Agorot] = None   # רק בשורה שמסיימת יום
    channel: Optional[str] = None         # DIRECT / BANKER / None
    category: str = ""
    subcategory: str = ""
    counterparty_id: str = ""
    recurring_id: Optional[str] = None
    source_file: str = ""
    page: Optional[int] = None
    raw_row: str = ""
    occurrence_index: int = 0             # מספר מופע של שורה זהה באותו יום
    id: str = ""

    def __post_init__(self):
        if isinstance(self.amount_agorot, float) or isinstance(self.day_balance_agorot, float):
            raise TypeError("float אסור במסלול כסף")
        if not self.id:
            self.id = self.make_id()

    def identity_key(self) -> tuple:
        """מפתח ייחוד בין קבצים חופפים (סעיף 3)."""
        return (self.date, self.description, self.amount_agorot, self.reference, self.occurrence_index)

    def make_id(self) -> str:
        raw = "|".join(str(x) for x in self.identity_key())
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["date"] = self.date.isoformat()
        d["value_date"] = self.value_date.isoformat() if self.value_date else None
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Transaction":
        d = dict(d)
        d["date"] = date.fromisoformat(d["date"])
        d["value_date"] = date.fromisoformat(d["value_date"]) if d.get("value_date") else None
        return cls(**d)


@dataclass
class Statement:
    """דף חשבון אחד אחרי פירוק. התנועות בסדר כרונולוגי (מהישן לחדש)."""
    source_file: str
    transactions: list[Transaction] = field(default_factory=list)
    account_hint: str = ""     # מספר חשבון כפי שנקרא — נשמר רק מוסתר בפלטים
    period_label: str = ""     # שורת התקופה כפי שמופיעה בראש הדף

    @property
    def start(self) -> date:
        return self.transactions[0].date

    @property
    def end(self) -> date:
        return self.transactions[-1].date


def days_newest_first_to_chronological(txns: list[Transaction]) -> list[Transaction]:
    """דף הבנק: הימים מהחדש לישן, ובתוך יום השורות בסדר הדף, עם היתרה בשורה האחרונה של היום.
    הופכים את סדר הימים בלבד, כך שהשורה שנושאת את יתרת סוף היום נשארת אחרונה ביומה."""
    days: dict = {}
    for t in txns:
        days.setdefault(t.date, []).append(t)
    return [t for d in reversed(list(days)) for t in days[d]]


def assign_occurrence_indices(txns: list[Transaction]) -> None:
    """שורות זהות באותו יום הן לגיטימיות — ממספרים אותן במקום למחוק."""
    seen: dict[tuple, int] = {}
    for t in txns:
        k = (t.date, t.description, t.amount_agorot, t.reference)
        t.occurrence_index = seen.get(k, 0)
        seen[k] = t.occurrence_index + 1
        t.id = t.make_id()
