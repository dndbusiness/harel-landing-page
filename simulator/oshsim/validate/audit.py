"""בדיקת יתרות לדף שהועלה (מקורי, סימולציה או דף שנערך ידנית).

לכל יום: יתרה קודמת בדף + סכום התנועות של היום = היתרה שהייתה צריכה להופיע.
אם היא לא שווה ליתרה שבדף — זו שגיאת חישוב באותו יום.

כשמצרפים גם את הדף המקורי, הפער של כל יום מול המקור מתפרק ל:
  מועבר  — הפער שהיה כבר בסוף היום הקודם (שינויים מימים קודמים שעוד לא התקזזו)
  היום   — סכום השינויים בתנועות של אותו יום
  שגיאה  — מה שלא מוסבר בשניהם (חייב להיות 0 בדף תקין)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from ..model.transaction import Transaction


@dataclass
class AuditRow:
    date: date
    description: str
    channel: Optional[str]
    reference: str
    amount: int
    running: int                      # יתרה מחושבת אחרי השורה (מהפתיחה)
    stated: Optional[int]             # יתרה שבדף (רק בשורה האחרונה של היום)
    day_end: bool = False
    expected_day: Optional[int] = None   # יתרת היום הקודם בדף + תנועות היום
    error: int = 0                       # stated − expected_day
    orig_amount: Optional[int] = None    # הסכום במקור (None = אין מקור / שורה חדשה)
    status: str = "same"                 # same / changed / added
    orig_stated: Optional[int] = None    # יתרת סוף היום במקור
    gap: Optional[int] = None            # stated − orig_stated
    gap_carried: Optional[int] = None
    gap_today: Optional[int] = None


@dataclass
class AuditReport:
    rows: list[AuditRow]
    opening: int
    opening_source: str
    days_checked: int
    errors: list[AuditRow] = field(default_factory=list)
    removed: list[Transaction] = field(default_factory=list)
    has_original: bool = False

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def closing_stated(self) -> Optional[int]:
        return next((r.stated for r in reversed(self.rows) if r.stated is not None), None)

    @property
    def closing_computed(self) -> int:
        return self.rows[-1].running


def _key(txns: list[Transaction]) -> list[tuple]:
    """מפתח להתאמת שורות בין שני דפים — בלי הסכום, כי הסכום הוא מה שהשתנה."""
    seen: dict[tuple, int] = {}
    out = []
    for t in txns:
        k = (t.date, t.description, t.reference)
        n = seen.get(k, 0)
        seen[k] = n + 1
        out.append(k + (n,))
    return out


def _derived_opening(txns: list[Transaction]) -> int:
    first = next(t for t in txns if t.day_balance_agorot is not None)
    return first.day_balance_agorot - sum(t.amount_agorot for t in txns if t.date <= first.date)


def audit(txns: list[Transaction], original: Optional[list[Transaction]] = None) -> AuditReport:
    if original:
        opening, src = _derived_opening(original), "נגזרה מהדף המקורי"
    else:
        opening, src = _derived_opening(txns), "נגזרה מהיתרה הראשונה בדף"

    orig_by_key: dict[tuple, Transaction] = {}
    orig_day_bal: dict[date, int] = {}
    if original:
        orig_by_key = dict(zip(_key(original), original))
        for t in original:
            if t.day_balance_agorot is not None:
                orig_day_bal[t.date] = t.day_balance_agorot

    rows: list[AuditRow] = []
    running = opening
    for t, k in zip(txns, _key(txns)):
        running += t.amount_agorot
        o = orig_by_key.pop(k, None) if original else None
        status = "same"
        if original:
            status = "added" if o is None else ("changed" if o.amount_agorot != t.amount_agorot else "same")
        rows.append(AuditRow(t.date, t.description, t.channel, t.reference, t.amount_agorot, running,
                             t.day_balance_agorot, orig_amount=o.amount_agorot if o else None, status=status))
    removed = list(orig_by_key.values())

    # ימים: השורה האחרונה של היום, יתרה קודמת בדף + תנועות היום
    by_day: dict[date, list[AuditRow]] = {}
    for r in rows:
        by_day.setdefault(r.date, []).append(r)
    removed_by_day: dict[date, int] = {}
    for t in removed:
        removed_by_day[t.date] = removed_by_day.get(t.date, 0) - t.amount_agorot

    prev_stated, prev_gap, checked, errors = opening, 0, 0, []
    for d in sorted(by_day):
        day = by_day[d]
        day_sum = sum(r.amount for r in day)
        last = day[-1]
        last.day_end = True
        stated = next((r.stated for r in reversed(day) if r.stated is not None), None)
        expected = prev_stated + day_sum
        if original:
            today = sum(r.amount - (r.orig_amount or 0) for r in day) + removed_by_day.get(d, 0)
            last.gap_today, last.gap_carried = today, prev_gap
        if stated is not None:
            checked += 1
            last.expected_day, last.error = expected, stated - expected
            if last.error:
                errors.append(last)
            if original and d in orig_day_bal:
                last.orig_stated = orig_day_bal[d]
                last.gap = stated - orig_day_bal[d]
                prev_gap = last.gap
            prev_stated = stated
        else:
            prev_stated = expected           # יום בלי יתרה בדף — ממשיכים מהחישוב
            if original:
                prev_gap = prev_gap + last.gap_today
    return AuditReport(rows, opening, src, checked, errors, removed, bool(original))
