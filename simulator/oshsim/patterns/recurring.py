"""זיהוי תנועות קבועות לפי מנפיק (סעיף 7).

סיווג: fixed (קבוע) / drifting (נע — משכנתה צמודה, ריבית משתנה) / variable (משתנה) / one_off.
לכל מנפיק נלמד כלל הזזה משלו — לא כלל גלובלי.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from statistics import median

import yaml

from ..model.transaction import Transaction
from .calendar import FRIDAY, BusinessCalendar

FIXED, DRIFTING, VARIABLE, ONE_OFF = "fixed", "drifting", "variable", "one_off"
KIND_HE = {FIXED: "קבוע", DRIFTING: "נע", VARIABLE: "משתנה", ONE_OFF: "חד-פעמי"}

DRIFT_MAX_STEP = Decimal("0.03")   # שינוי חודשי מקסימלי שעדיין נחשב "נע" (3%)


@dataclass
class RecurringPattern:
    id: str
    counterparty: str
    direction: str                 # credit / debit
    kind: str
    category: str
    day_of_month: int
    amounts_by_month: dict[str, int]       # 'YYYY-MM' → אגורות
    typical_amount: int
    channel: str | None
    friday_rule: str = "same"
    closed_rule: str = "forward"
    rule_evidence: dict[str, int] = field(default_factory=dict)
    rule_learned: bool = False
    approved: bool = False
    txn_ids: list[str] = field(default_factory=list)

    def amount_for(self, month: str) -> int:
        """לנע — הסכום האחרון הידוע עד החודש, לא ממוצע."""
        if month in self.amounts_by_month:
            return self.amounts_by_month[month]
        prior = [m for m in sorted(self.amounts_by_month) if m <= month]
        if self.kind == VARIABLE:
            return self.typical_amount
        return self.amounts_by_month[prior[-1]] if prior else self.typical_amount


def _month(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _nominal(year: int, month: int, day: int) -> date:
    nxt = date(year + (month == 12), month % 12 + 1, 1)
    return date(year, month, min(day, (nxt - timedelta(days=1)).day))


def _classify(amounts: list[int], months: int, count: int) -> str:
    if count == 1:
        return ONE_OFF
    if months < 2 or 2 * count > 3 * months:
        return VARIABLE
    if len(set(amounts)) == 1:
        return FIXED
    steps = [abs(Decimal(b - a)) / abs(Decimal(a)) for a, b in zip(amounts, amounts[1:]) if a]
    if steps and max(steps) <= DRIFT_MAX_STEP:
        return DRIFTING
    return VARIABLE


def detect(txns: list[Transaction], cal: BusinessCalendar,
           exclude_kinds: set[str] = frozenset(), kind_of=lambda t: "") -> list[RecurringPattern]:
    groups: dict[tuple, list[Transaction]] = defaultdict(list)
    for t in txns:
        if kind_of(t) in exclude_kinds:
            continue
        direction = "credit" if t.amount_agorot > 0 else "debit"
        groups[(t.counterparty_id or t.description, direction)].append(t)

    patterns: list[RecurringPattern] = []
    for n, ((cp, direction), ts) in enumerate(sorted(groups.items(), key=lambda kv: kv[0])):
        ts.sort(key=lambda t: t.date)
        by_month: dict[str, int] = defaultdict(int)
        for t in ts:
            by_month[_month(t.date)] += t.amount_agorot
        monthly = [by_month[m] for m in sorted(by_month)]
        kind = _classify(monthly, len(by_month), len(ts))

        normal_days = [t.date.day for t in ts if cal.is_business_day(t.date)]
        dom = Counter(normal_days or [t.date.day for t in ts]).most_common(1)[0][0]

        evidence: Counter = Counter()
        if kind in (FIXED, DRIFTING):
            for t in ts:
                nom = _nominal(t.date.year, t.date.month, dom)
                if nom.weekday() == FRIDAY and not cal.is_closed(nom):
                    evidence["friday_" + ("same" if t.date == nom else "forward" if t.date > nom else "back")] += 1
                elif cal.is_closed(nom):
                    evidence["closed_" + ("forward" if t.date > nom else "back")] += 1
        fr = max(("same", "forward", "back"), key=lambda r: evidence.get("friday_" + r, 0))
        cr = max(("forward", "back"), key=lambda r: evidence.get("closed_" + r, 0))
        channels = Counter(t.channel for t in ts)

        p = RecurringPattern(
            id=f"R{n + 1:03d}", counterparty=cp, direction=direction, kind=kind,
            category=Counter(t.category for t in ts).most_common(1)[0][0],
            day_of_month=dom, amounts_by_month=dict(sorted(by_month.items())),
            typical_amount=int(median(monthly)), channel=channels.most_common(1)[0][0],
            friday_rule=fr if evidence.get("friday_" + fr) else "same",
            closed_rule=cr if evidence.get("closed_" + cr) else "forward",
            rule_evidence=dict(evidence), rule_learned=bool(evidence),
            txn_ids=[t.id for t in ts],
        )
        if kind != ONE_OFF:
            for t in ts:
                t.recurring_id = p.id
        patterns.append(p)
    return patterns


def save_patterns(patterns: list[RecurringPattern], path: str | Path) -> None:
    Path(path).write_text(yaml.safe_dump({"patterns": [asdict(p) for p in patterns]},
                                         allow_unicode=True, sort_keys=False), encoding="utf-8")


def load_patterns(path: str | Path) -> list[RecurringPattern]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return [RecurringPattern(**d) for d in data.get("patterns", [])]
