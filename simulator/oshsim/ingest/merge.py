"""איחוד כמה דפים, כולל דפים עם טווחי תאריכים חופפים.

ייחוד לפי (date, description, amount, reference, occurrence_index): שתי שורות זהות
באותו יום באותו קובץ הן שתי תנועות, ושורה שמופיעה בשני קבצים חופפים היא אחת.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from ..model.transaction import Statement, Transaction
from .common import ParseError


@dataclass
class MergeResult:
    transactions: list[Transaction]
    issues: list[str] = field(default_factory=list)
    duplicates_dropped: int = 0


def load_statement(path: str | Path) -> Statement:
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        from .mizrahi import MizrahiOshParser
        return MizrahiOshParser().parse(p)
    if p.suffix.lower() == ".csv":
        from .csv_adapter import parse_csv
        return parse_csv(p)
    raise ParseError(f"סוג קובץ לא נתמך: {p.name}")


def merge_statements(statements: list[Statement]) -> MergeResult:
    statements = sorted(statements, key=lambda s: (s.start, s.end))
    issues: list[str] = []
    by_key: dict[tuple, Transaction] = {}
    order: list[tuple] = []
    day_balance: dict[date, tuple[int, str]] = {}
    dropped = 0

    for st in statements:
        for t in st.transactions:
            k = t.identity_key()
            if k in by_key:
                dropped += 1
                prev = by_key[k]
                if prev.day_balance_agorot is None and t.day_balance_agorot is not None:
                    prev.day_balance_agorot = t.day_balance_agorot
                continue
            by_key[k] = t
            order.append(k)
            if t.day_balance_agorot is not None:
                if t.date in day_balance and day_balance[t.date][0] != t.day_balance_agorot:
                    issues.append(
                        f"{t.date:%d/%m/%Y}: יתרת סוף יום שונה בין {day_balance[t.date][1]} ({day_balance[t.date][0]}) "
                        f"ל-{st.source_file} ({t.day_balance_agorot})")
                day_balance.setdefault(t.date, (t.day_balance_agorot, st.source_file))

    # רציפות: אם יש פער תאריכים בין דפים, אין לנו דרך לדעת מה היה באמצע
    for a, b in zip(statements, statements[1:]):
        if b.start > a.end and (b.start - a.end).days > 7:
            issues.append(f"פער בין {a.source_file} (עד {a.end:%d/%m/%Y}) ל-{b.source_file} (מ-{b.start:%d/%m/%Y})")

    # סדר: כרונולוגי לפי תאריך, ובתוך יום — סדר ההופעה הראשון
    pos = {k: i for i, k in enumerate(order)}
    txns = sorted((by_key[k] for k in order), key=lambda t: (t.date, pos[t.identity_key()]))
    return MergeResult(transactions=txns, issues=issues, duplicates_dropped=dropped)
