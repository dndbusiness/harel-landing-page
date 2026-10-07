"""ולידציה מול סכום ביקורת (סעיף 5). כשל = עצירה עם דוח פערים, בלי תיקון שקט."""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import date

from ..model.money import Agorot, fmt
from ..model.transaction import Transaction


@dataclass
class Gap:
    day: date
    expected: Agorot     # יתרה קודמת + סכום התנועות
    actual: Agorot       # מה שכתוב בדף

    @property
    def diff(self) -> Agorot:
        return self.actual - self.expected

    def __str__(self) -> str:
        return (f"{self.day:%d/%m/%Y}: צפוי {fmt(self.expected)}, בפועל {fmt(self.actual)}, "
                f"הפרש {fmt(self.diff)}")


@dataclass
class ValidationReport:
    opening_agorot: Agorot | None
    closing_agorot: Agorot | None
    days_checked: int
    gaps: list[Gap] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    log: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.gaps and not self.errors

    def summary(self) -> str:
        lines = [f"ימים שנבדקו: {self.days_checked}",
                 f"יתרת פתיחה (נגזרת): {fmt(self.opening_agorot)}",
                 f"יתרת סגירה: {fmt(self.closing_agorot)}"]
        lines += [f"שגיאה: {e}" for e in self.errors]
        lines += [f"פער: {g}" for g in self.gaps]
        lines.append("תקין" if self.ok else "נכשל — אין להמשיך עד שהפער מוסבר")
        return "\n".join(lines)


class ValidationError(RuntimeError):
    def __init__(self, report: ValidationReport):
        super().__init__(report.summary())
        self.report = report


def group_by_day(txns: list[Transaction]) -> "OrderedDict[date, list[Transaction]]":
    days: OrderedDict[date, list[Transaction]] = OrderedDict()
    for t in txns:
        days.setdefault(t.date, []).append(t)
    return days


def day_balances(txns: list[Transaction]) -> tuple[dict[date, Agorot], list[str]]:
    """יתרת סוף יום כפי שמופיעה בדף. יותר מיתרה אחת שונה ביום = שגיאה."""
    out: dict[date, Agorot] = {}
    errors: list[str] = []
    for t in txns:
        if t.day_balance_agorot is None:
            continue
        if t.date in out and out[t.date] != t.day_balance_agorot:
            errors.append(f"{t.date:%d/%m/%Y}: שתי יתרות שונות באותו יום ({fmt(out[t.date])}, {fmt(t.day_balance_agorot)})")
        out.setdefault(t.date, t.day_balance_agorot)
    return out, errors


def validate(txns: list[Transaction], raise_on_fail: bool = True) -> ValidationReport:
    if any(isinstance(t.amount_agorot, float) for t in txns):
        raise TypeError("float במסלול כסף")
    days = group_by_day(txns)
    balances, errors = day_balances(txns)
    rep = ValidationReport(opening_agorot=None, closing_agorot=None, days_checked=0, errors=errors)

    if not balances:
        rep.errors.append("אין אף יתרה בדף — אי אפשר לאמת")
    else:
        # פתיחה = יתרה ראשונה − סכום כל הימים עד אליה (כולל)
        first_day = next(d for d in days if d in balances)
        upto = sum(t.amount_agorot for d, ts in days.items() if d <= first_day for t in ts)
        rep.opening_agorot = balances[first_day] - upto
        rep.log.append(f"פתיחה נגזרה מ-{first_day:%d/%m/%Y}: {fmt(balances[first_day])} − ({fmt(upto)})")

        running = rep.opening_agorot
        for d, ts in days.items():
            running += sum(t.amount_agorot for t in ts)
            if d in balances:
                rep.days_checked += 1
                if balances[d] != running:
                    rep.gaps.append(Gap(d, running, balances[d]))
                    running = balances[d]   # ממשיכים מהיתרה בדף כדי לאתר כל פער בנפרד
        last_day = next(d for d in reversed(days) if d in balances)
        if last_day != next(reversed(days)):
            rep.errors.append(f"היום האחרון בדף ({next(reversed(days)):%d/%m/%Y}) בלי יתרה — אין סכום ביקורת לסוף התקופה")
        rep.closing_agorot = running
        missing = [d for d in days if d not in balances]
        if missing:
            rep.log.append(f"ימים בלי יתרה בדף (נבדקים בעקיפין דרך היום הבא): {len(missing)}")

    if raise_on_fail and not rep.ok:
        raise ValidationError(rep)
    return rep
