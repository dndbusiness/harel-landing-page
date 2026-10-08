"""Adapter: מזרחי טפחות — "עובר ושב — יתרה ותנועות בחשבון" (PDF).

שליפה לפי קואורדינטות עם pdfplumber:
1. מזהים את שורת הכותרת לפי שמות העמודות (כולל גרסה הפוכה של הטקסט).
2. כל מילה משויכת לעמודה הקרובה ביותר לפי מרכז ה-x.
3. שורה שמתחילה בתאריך היא תנועה; שורה בלי תאריך היא המשך תיאור.
4. הדף מהחדש לישן — הופכים לסדר כרונולוגי.

**לא נבדק עדיין מול PDF אמיתי של הבנק.** כינויי הכותרות כאן הם מה שנצפה בדף;
אם הבנק משנה פורמט, מריצים `oshsim inspect file.pdf` ומעדכנים את HEADER_ALIASES.
כל שורה נשמרת עם raw_row ועמוד, והולידציה שאחרי הפירוק עוצרת על כל פער.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from ..model.money import MoneyParseError, looks_like_amount, parse_amount
from ..model.transaction import (Statement, Transaction, assign_occurrence_indices,
                                 days_newest_first_to_chronological)
from .common import ParseError, is_date, parse_date, split_channel
from .hebrew import has_hebrew, normalize_spaces, visual_to_logical

# עמודה → צירופי מילים אפשריים בכותרת (בסדר לוגי)
HEADER_ALIASES: dict[str, list[str]] = {
    "date": ["תאריך"],
    "value_date": ["תאריך ערך", "ערך"],
    "description": ["סוג תנועה", "תיאור", "פירוט"],
    "amount": ["זכות/חובה", "זכות / חובה", "חובה/זכות", "סכום"],
    "balance": ["יתרה", "יתרה בש\"ח"],
    "reference": ["אסמכתה", "אסמכתא"],
}

ROW_TOLERANCE = 3.0   # נקודות — מילים באותו גובה בערך הן אותה שורה
ORPHAN_TOLERANCE = 8.0  # נקודות — מספר שהוזח מעט מעל/מתחת לשורה שלו (תא עם שתי שורות)
# גודל טקסט ביחס לגופן העיקרי בעמוד: קטן מ-90% = הערות ("במקור ..."), גדול פי 2.5 = סימן מים.
# בדף הבנק: גוף 9.1, כותרת 20.4.
MIN_TEXT_RATIO, MAX_TEXT_RATIO = 0.9, 2.5


@dataclass
class _Word:
    text: str
    x0: float
    x1: float
    top: float

    @property
    def xc(self) -> float:
        return (self.x0 + self.x1) / 2


class MizrahiOshParser:
    bank = "mizrahi_tefahot"
    layout = "osh_balance_and_transactions"

    def __init__(self, header_aliases: dict[str, list[str]] | None = None):
        self.aliases = header_aliases or HEADER_ALIASES

    # ---------- פתיחת הקובץ ----------
    def _pages(self, path: Path):
        import pdfplumber  # טעינה מאוחרת: הבדיקות שלא נוגעות ב-PDF לא צריכות אותו

        with pdfplumber.open(str(path)) as pdf:
            for pno, page in enumerate(pdf.pages, start=1):
                # סימן מים גדול והערות קטנות (בדף סימולציה) אינם חלק מהטבלה
                sizes = Counter(round(c["size"], 1) for c in page.chars)
                if sizes:
                    body = sizes.most_common(1)[0][0]
                    lo, hi = body * MIN_TEXT_RATIO, body * MAX_TEXT_RATIO
                    page = page.filter(lambda o: o.get("object_type") != "char" or lo <= o.get("size", 0) <= hi)
                words = page.extract_words(x_tolerance=1.5, y_tolerance=2, keep_blank_chars=False)
                yield pno, [_Word(w["text"], w["x0"], w["x1"], w["top"]) for w in words]

    # ---------- כלים ----------
    @staticmethod
    def _rows(words: list[_Word]) -> list[list[_Word]]:
        rows: list[list[_Word]] = []
        for w in sorted(words, key=lambda w: (w.top, w.x0)):
            if rows and abs(rows[-1][0].top - w.top) <= ROW_TOLERANCE:
                rows[-1].append(w)
            else:
                rows.append([w])
        return rows

    @staticmethod
    def _line_text(row: list[_Word], reversed_text: bool) -> str:
        # עברית: קוראים מימין לשמאל
        ordered = sorted(row, key=lambda w: -w.xc)
        parts = [visual_to_logical(w.text) if reversed_text else w.text for w in ordered]
        return normalize_spaces(" ".join(parts))

    def _detect_header(self, rows) -> tuple[int, dict[str, float], bool] | None:
        for reversed_text in (False, True):
            for i, row in enumerate(rows):
                line = self._line_text(row, reversed_text)
                found = {col: a for col, al in self.aliases.items() for a in al if a in line}
                if {"date", "description", "amount", "balance"} <= found.keys():
                    return i, self._column_centers(row, reversed_text), reversed_text
        return None

    def _column_centers(self, row: list[_Word], reversed_text: bool) -> dict[str, float]:
        """מרכז x לכל עמודה. כותרת של כמה מילים ("סוג תנועה") — ממוצע המילים."""
        # סדר קריאה עברי: מימין לשמאל
        ordered = sorted(row, key=lambda w: -w.xc)
        texts = [visual_to_logical(w.text) if reversed_text else w.text for w in ordered]
        centers: dict[str, float] = {}
        used: set[int] = set()
        # כינויים ארוכים קודם, כדי ש"תאריך ערך" לא ייבלע ב"תאריך"
        pairs = sorted(((col, a) for col, al in self.aliases.items() for a in al), key=lambda p: -len(p[1]))
        for col, alias in pairs:
            if col in centers:
                continue
            tokens = alias.split()
            for i in range(len(texts) - len(tokens) + 1):
                span = set(range(i, i + len(tokens)))
                if texts[i: i + len(tokens)] == tokens and not used & span:
                    centers[col] = sum(ordered[k].xc for k in span) / len(span)
                    used |= span
                    break
        return centers

    @staticmethod
    def _nearest(xc: float, centers: dict[str, float]) -> str:
        return min(centers, key=lambda c: abs(centers[c] - xc))

    # ---------- פירוק ----------
    def parse(self, path: str | Path) -> Statement:
        path = Path(path)
        display_rows: list[dict] = []     # לפי סדר התצוגה (מהחדש לישן)
        account_hint = period_label = ""
        centers: dict[str, float] | None = None
        reversed_text = False

        for pno, words in self._pages(path):
            rows = self._rows(words)
            hdr = self._detect_header(rows)
            if hdr is not None:
                idx, centers, reversed_text = hdr
                if pno == 1:
                    # ראש הדף: מספר חשבון (נשמר רק כדי להציג אותו מוסתר) ושורת התקופה
                    for line in (self._line_text(r, reversed_text) for r in rows[:idx]):
                        m = re.search(r"חשבון מספר\s*([\d\-]{6,})", line)
                        if m and not account_hint:
                            account_hint = m.group(1)
                        if "תנועות בחשבון מתאריך" in line and not period_label:
                            period_label = line
                rows = rows[idx + 1:]
            elif centers is None:
                continue  # עמוד שער/סיכום לפני הטבלה
            orphans: list[tuple[float, dict]] = []   # סכומים שנמצאו בשורה בלי תאריך
            for row in rows:
                cells: dict[str, list[_Word]] = {}
                for w in row:
                    cells.setdefault(self._nearest(w.xc, centers), []).append(w)
                text = {c: self._line_text(ws, reversed_text) for c, ws in cells.items()}
                raw = self._line_text(row, reversed_text)
                top = row[0].top
                date_txt = text.get("date", "")
                if is_date(date_txt):
                    rec = {"cells": text, "page": pno, "raw": raw, "top": top}
                    display_rows.append(rec)
                    # מספר שהופיע ממש מעל השורה (תא מודגש עם שתי שורות) שייך לה
                    for o_top, o_cells in orphans:
                        if abs(o_top - top) <= ORPHAN_TOLERANCE:
                            self._fill_missing(rec, o_cells)
                    orphans = []
                    continue
                numeric = {c: v for c, v in text.items() if c in ("amount", "balance") and looks_like_amount(v)}
                if numeric and set(text) <= {"amount", "balance"}:
                    last = display_rows[-1] if display_rows else None
                    if last and last["page"] == pno and abs(last["top"] - top) <= ORPHAN_TOLERANCE:
                        self._fill_missing(last, numeric)
                    else:
                        orphans.append((top, numeric))
                elif display_rows and text.get("description") and not text.get("amount") \
                        and not display_rows[-1]["cells"].get("description", "").endswith(text["description"]):
                    # שורת המשך של תיאור ארוך
                    display_rows[-1]["cells"]["description"] = normalize_spaces(
                        display_rows[-1]["cells"].get("description", "") + " " + text["description"])
                    display_rows[-1]["raw"] += " | " + raw
                # כל השאר (כותרות עמוד, סיכומים) — מדלגים

        if not display_rows:
            raise ParseError(f"{path.name}: לא נמצאה טבלת תנועות. הריצו `oshsim inspect` לבדיקה.")

        txns = [self._to_txn(r, path.name) for r in display_rows]
        txns = days_newest_first_to_chronological(txns)
        assign_occurrence_indices(txns)
        return Statement(source_file=path.name, transactions=txns, account_hint=account_hint,
                         period_label=period_label)

    @staticmethod
    def _fill_missing(rec: dict, cells: dict) -> None:
        for c, v in cells.items():
            if not rec["cells"].get(c):
                rec["cells"][c] = v
                rec["raw"] += f" | {v}"

    @staticmethod
    def _to_txn(r: dict, source: str) -> Transaction:
        c = dict(r["cells"])
        # טקסט שאינו מספר שגלש לעמודת סכום/יתרה (למשל "(י)" בתיאור שנשבר לשתי שורות) — שייך לתיאור
        for col in ("amount", "balance"):
            toks = (c.get(col) or "").split()
            nums = [t for t in toks if looks_like_amount(t)]
            extra = [t for t in toks if not looks_like_amount(t)]
            if extra and len(nums) <= 1:
                c[col] = " ".join(nums)
                c["description"] = normalize_spaces((c.get("description") or "") + " " + " ".join(extra))
        try:
            amount = parse_amount(c.get("amount", ""))
        except MoneyParseError as e:
            raise ParseError(f"עמוד {r['page']}: {e} | שורה: {r['raw']}") from e
        bal_txt = c.get("balance", "")
        balance = parse_amount(bal_txt) if bal_txt and looks_like_amount(bal_txt) else None
        if bal_txt and balance is None:
            raise ParseError(f"עמוד {r['page']}: יתרה לא חוקית {bal_txt!r} | שורה: {r['raw']}")
        vd = c.get("value_date", "")
        desc, channel = split_channel(c.get("description", ""))
        ref = re.sub(r"\s+", "", c.get("reference", ""))
        if has_hebrew(ref):
            raise ParseError(f"עמוד {r['page']}: אסמכתה לא צפויה {ref!r} | שורה: {r['raw']}")
        return Transaction(
            date=parse_date(c["date"]),
            value_date=parse_date(vd) if is_date(vd) else None,
            description=desc,
            amount_agorot=amount,
            day_balance_agorot=balance,
            reference=ref,
            channel=channel,
            source_file=source,
            page=r["page"],
            raw_row=r["raw"],
        )

    # ---------- עזר לכיול פורמט חדש ----------
    def inspect(self, path: str | Path, max_rows: int = 40) -> str:
        out = []
        for pno, words in self._pages(Path(path)):
            rows = self._rows(words)
            hdr = self._detect_header(rows)
            out.append(f"--- עמוד {pno}: כותרת {'נמצאה' if hdr else 'לא נמצאה'}"
                       + (f", טקסט הפוך={hdr[2]}, עמודות={ {k: round(v) for k, v in hdr[1].items()} }" if hdr else ""))
            for row in rows[:max_rows]:
                out.append("  " + " ‖ ".join(f"{w.text}@{round(w.xc)}" for w in sorted(row, key=lambda w: -w.xc)))
        return "\n".join(out)
