"""קלט CSV — לתנועות שהוזנו ידנית או נקראו חזותית כש-PDF לא נשלף נקי.

עמודות: date, value_date, description, amount, balance, reference, channel
(channel: direct / banker / ריק; או שהתיאור מכיל (י)/(פ)).
סדר השורות כמו בדף הבנק (ימים מהחדש לישן, יתרה בשורה האחרונה של היום) או כרונולוגי — נקבע לפי `order`.
"""
from __future__ import annotations

import csv
from pathlib import Path

from ..model.money import parse_amount
from ..model.transaction import (Statement, Transaction, assign_occurrence_indices,
                                 days_newest_first_to_chronological)
from .common import ParseError, is_date, parse_date, split_channel


def parse_csv(path: str | Path, order: str = "auto") -> Statement:
    path = Path(path)
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    txns: list[Transaction] = []
    for i, r in enumerate(rows, start=2):
        try:
            desc, channel = split_channel(r.get("description", ""))
            ch = (r.get("channel") or "").strip() or channel
            if ch not in (None, "direct", "banker"):
                raise ParseError(f"channel לא חוקי: {ch!r}")
            bal = (r.get("balance") or "").strip()
            vd = (r.get("value_date") or "").strip()
            txns.append(Transaction(
                date=parse_date(r["date"]),
                value_date=parse_date(vd) if is_date(vd) else None,
                description=desc,
                amount_agorot=parse_amount(r["amount"]),
                day_balance_agorot=parse_amount(bal) if bal else None,
                reference=(r.get("reference") or "").strip(),
                channel=ch,
                source_file=path.name,
                page=None,
                raw_row=",".join(f"{k}={v}" for k, v in r.items()),
            ))
        except (KeyError, ValueError) as e:
            raise ParseError(f"{path.name} שורה {i}: {e}") from e
    if not txns:
        raise ParseError(f"{path.name}: קובץ ריק")
    if order == "auto":
        order = "newest_first" if txns[0].date > txns[-1].date else "chronological"
    if order == "newest_first":
        txns = days_newest_first_to_chronological(txns)
    assign_occurrence_indices(txns)
    return Statement(source_file=path.name, transactions=txns)
