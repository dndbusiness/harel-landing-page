"""לוח עסקים ישראלי: שבת + חגים מ-pyluach + תאריכים נוספים מקובץ הגדרות.

חגים לא נכתבים מהזיכרון. pyluach נותן ימי יום-טוב (לוח ארץ ישראל). ימי סגירה
שאינם יום-טוב (יום העצמאות, ערבי חג לפי נוהל הבנק) נכנסים ל-extra_closed_dates
בקובץ config/calendar.yaml ממקור הבנק.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

import yaml

FRIDAY, SATURDAY = 4, 5


@lru_cache(maxsize=4096)
def _yom_tov(d: date) -> str | None:
    from pyluach import dates, hebrewcal
    return hebrewcal.festival(dates.GregorianDate.from_pydate(d), israel=True,
                              include_working_days=False, hebrew=True)


@dataclass
class BusinessCalendar:
    friday_is_business_day: bool = False
    extra_closed: set[date] = field(default_factory=set)
    use_pyluach: bool = True

    @classmethod
    def load(cls, path: str | Path | None) -> "BusinessCalendar":
        if not path or not Path(path).exists():
            return cls()
        d = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        extra = {date.fromisoformat(str(x["date"]) if isinstance(x, dict) else str(x))
                 for x in d.get("extra_closed_dates") or []}
        return cls(friday_is_business_day=bool(d.get("friday_is_business_day", False)),
                   extra_closed=extra, use_pyluach=d.get("holiday_source", "pyluach") == "pyluach")

    def holiday(self, d: date) -> str | None:
        if d in self.extra_closed:
            return "סגירה (הגדרות)"
        return _yom_tov(d) if self.use_pyluach else None

    def is_closed(self, d: date) -> bool:
        """יום שאין בו רישום כלל: שבת או חג."""
        return d.weekday() == SATURDAY or self.holiday(d) is not None

    def is_business_day(self, d: date) -> bool:
        if self.is_closed(d):
            return False
        return self.friday_is_business_day or d.weekday() != FRIDAY

    def next_business_day(self, d: date) -> date:
        while not self.is_business_day(d):
            d += timedelta(days=1)
        return d

    def prev_business_day(self, d: date) -> date:
        while not self.is_business_day(d):
            d -= timedelta(days=1)
        return d

    def first_business_day(self, year: int, month: int) -> date:
        return self.next_business_day(date(year, month, 1))

    def shift(self, nominal: date, friday_rule: str, closed_rule: str) -> date:
        """הזזת תאריך לפי כלל המנפיק.
        friday_rule: same / back / forward — מה קורה כשהתאריך הנקוב נופל בשישי.
        closed_rule: back / forward — מה קורה בשבת/חג.
        """
        d = nominal
        if d.weekday() == FRIDAY and not self.is_closed(d):
            if friday_rule == "same":
                return d
            d = self._move(d, friday_rule)
            return d
        if self.is_closed(d):
            d = self._move(d, closed_rule)
        return d

    def _move(self, d: date, direction: str) -> date:
        step = timedelta(days=1 if direction == "forward" else -1)
        d += step
        while not self.is_business_day(d):
            d += step
        return d
