"""קטגוריזציה לפי טבלת כללים (config/rules.yaml) + תור אישור ליועץ.

קוד רגיל בלבד. הצעה למודל שפה היא אופציונלית, דורשת הסכמה מפורשת, ואף פעם
לא נכנסת לתוקף בלי אישור היועץ.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Optional, Protocol

import yaml

from ..model.money import from_decimal
from ..model.transaction import Transaction

UNCATEGORIZED = "לא מסווג"


def counterparty_key(description: str) -> str:
    """מפתח מנפיק: התיאור בלי ספרות ופיסוק (מספרי הוראה/חודש משתנים)."""
    s = re.sub(r"[\d.,/\\\-:#()\"']+", " ", description)
    return re.sub(r"\s+", " ", s).strip()


@dataclass
class Rule:
    id: str
    category: str
    subcategory: str = ""
    priority: int = 0
    description: Optional[str] = None     # regex על התיאור
    reference: Optional[str] = None       # regex על האסמכתה
    min: Optional[int] = None             # אגורות, ערך מוחלט
    max: Optional[int] = None
    direction: str = "any"                # credit / debit / any
    kind: str = ""                        # direct_channel_fee / interest / card_charge
    source: str = ""                      # מאיפה הכלל (ברירת מחדל / אישור יועץ)

    def __post_init__(self):
        self._desc = re.compile(self.description) if self.description else None
        self._ref = re.compile(self.reference) if self.reference else None

    def matches(self, t: Transaction) -> bool:
        if self._desc and not self._desc.search(t.description):
            return False
        if self._ref and not self._ref.search(t.reference or ""):
            return False
        a = abs(t.amount_agorot)
        if self.min is not None and a < self.min:
            return False
        if self.max is not None and a > self.max:
            return False
        if self.direction == "credit" and t.amount_agorot <= 0:
            return False
        if self.direction == "debit" and t.amount_agorot >= 0:
            return False
        return True

    @classmethod
    def from_dict(cls, d: dict, source: str) -> "Rule":
        d = dict(d)
        for k in ("min", "max"):
            if d.get(k) is not None:
                d[k] = from_decimal(str(d[k]))
        d.setdefault("source", source)
        return cls(**d)

    def to_dict(self) -> dict:
        d = {k: getattr(self, k) for k in ("id", "category", "subcategory", "priority", "description",
                                          "reference", "direction", "kind", "source")}
        for k in ("min", "max"):
            v = getattr(self, k)
            if v is not None:
                d[k] = f"{v // 100}.{v % 100:02d}"
        return {k: v for k, v in d.items() if v not in (None, "")}


def load_rules(*paths: str | Path) -> list[Rule]:
    rules: list[Rule] = []
    for p in paths:
        p = Path(p)
        if not p.exists():
            continue
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        for d in data.get("rules", []):
            rules.append(Rule.from_dict(d, source=p.name))
    rules.sort(key=lambda r: -r.priority)
    return rules


class Suggester(Protocol):
    def suggest(self, t: Transaction, categorized: list[Transaction]) -> tuple[str, str, str]:
        """→ (category, subcategory, נימוק)"""


class HeuristicSuggester:
    """מציע לפי הדמיון הכי גבוה למילים בתנועות שכבר סווגו. מקומי לגמרי."""

    def suggest(self, t, categorized):
        words = set(counterparty_key(t.description).split())
        best, best_score = None, Fraction(0)
        for c in categorized:
            if c.category in ("", UNCATEGORIZED):
                continue
            cw = set(counterparty_key(c.description).split())
            if not cw or not words:
                continue
            score = Fraction(len(words & cw), len(words | cw))
            if score > best_score:
                best, best_score = c, score
        if best is None or best_score < Fraction(1, 3):
            return UNCATEGORIZED, "", "אין תנועה דומה מסווגת"
        return best.category, best.subcategory, f"דומה ל-'{best.description}' ({best_score:.0%})"


class ExternalModelSuggester:
    """נקודת חיבור למודל שפה. חסום עד שהלקוח נתן הסכמה מפורשת (סעיף 11)."""

    def __init__(self, consent: bool, client):
        if not consent:
            raise PermissionError("שליחת נתוני לקוח לשירות חיצוני דורשת הסכמה מפורשת")
        self.client = client  # callable(description, amount_agorot, categories) → (cat, sub, reason)

    def suggest(self, t, categorized):
        cats = sorted({(c.category, c.subcategory) for c in categorized if c.category})
        return self.client(t.description, t.amount_agorot, cats)


@dataclass
class QueueItem:
    txn_id: str
    date: str
    description: str
    amount_agorot: int
    suggested_category: str
    suggested_subcategory: str
    reason: str


@dataclass
class CategorizeResult:
    queue: list[QueueItem] = field(default_factory=list)
    matched: int = 0


def categorize(txns: list[Transaction], rules: list[Rule],
               suggester: Suggester | None = None) -> CategorizeResult:
    suggester = suggester or HeuristicSuggester()
    res = CategorizeResult()
    for t in txns:
        t.counterparty_id = counterparty_key(t.description)
        rule = next((r for r in rules if r.matches(t)), None)
        if rule:
            t.category, t.subcategory = rule.category, rule.subcategory
            res.matched += 1
        else:
            t.category, t.subcategory = UNCATEGORIZED, ""
    done = [t for t in txns if t.category != UNCATEGORIZED]
    for t in txns:
        if t.category == UNCATEGORIZED:
            cat, sub, why = suggester.suggest(t, done)
            res.queue.append(QueueItem(t.id, t.date.isoformat(), t.description, t.amount_agorot, cat, sub, why))
    return res


def rule_kind(t: Transaction, rules: list[Rule]) -> str:
    rule = next((r for r in rules if r.matches(t)), None)
    return rule.kind if rule else ""


def approve(item: QueueItem, category: str, subcategory: str, client_rules_path: str | Path,
            by_reference: bool = False) -> Rule:
    """החלטת היועץ נשמרת ככלל בקובץ הכללים של הלקוח, לשימוש חוזר."""
    p = Path(client_rules_path)
    data = (yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else None) or {"rules": []}
    key = counterparty_key(item.description)
    rule = Rule(
        id=f"client-{len(data['rules']) + 1}",
        category=category, subcategory=subcategory, priority=1000,
        description=r"[\d\s.,/\\\-:#()\"']*".join(re.escape(w) for w in key.split()) if key else None,
        direction="credit" if item.amount_agorot > 0 else "debit",
        source="אישור יועץ",
    )
    data["rules"].append(rule.to_dict())
    p.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return rule
