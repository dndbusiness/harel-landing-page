"""סימון פערים ישירות על קובץ ה-PDF שהועלה.

כל יתרה שגויה מוקפת באדום, ומתחתיה כתוב באדום איך היא הייתה צריכה להירשם.
תנועה שסכומה שונה מהייחוס (למשל מהסימולטור) מסומנת בצהוב עם הסכום בייחוס.
הקובץ המקורי לא משתנה — נוצר עותק מסומן.
"""
from __future__ import annotations

import io
from pathlib import Path

from ..ingest.common import is_date
from ..ingest.hebrew import visual_to_logical
from ..ingest.mizrahi import MizrahiOshParser
from ..model.money import fmt
from ..validate.audit import AuditReport

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _vis(s: str) -> str:
    # reportlab מצייר משמאל לימין; עברית נכתבת בסדר חזותי (אותה פונקציה הופכת בשני הכיוונים)
    return visual_to_logical(s)


def _label_and_number(c, x_right: float, y: float, label: str, number: str, size: float) -> None:
    """תווית עברית מימין ומספר משמאלה — מצוירים בנפרד כדי שהמינוס יישאר לפני המספר."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    w_label = stringWidth(label + " ", "DejaVu", size)
    w = w_label + stringWidth(number, "DejaVu", size)
    fill = c._fillColorObj
    c.setFillColorRGB(1, 1, 1)
    c.rect(x_right - w - 1.5, y - 1.8, w + 3, size + 2.4, fill=1, stroke=0)
    c.setFillColor(fill)
    c.setFont("DejaVu", size)
    c.drawRightString(x_right, y, _vis(label))
    c.drawRightString(x_right - w_label, y, number)


def _display_order(rep: AuditReport):
    days: dict = {}
    for r in rep.rows:
        days.setdefault(r.date, []).append(r)
    return [r for d in sorted(days, reverse=True) for r in days[d]]


def _located_rows(pdf_path: Path):
    """שורות הטבלה בסדר התצוגה: (עמוד, טקסט תאריך, bbox של עמודת סכום, bbox של עמודת יתרה)."""
    import pdfplumber
    from collections import Counter

    from ..ingest.mizrahi import MAX_TEXT_RATIO, MIN_TEXT_RATIO, _Word
    parser = MizrahiOshParser()
    out = []
    centers = None
    rev = False
    with pdfplumber.open(str(pdf_path)) as pdf:
        for pno, page in enumerate(pdf.pages):
            sizes = Counter(round(c["size"], 1) for c in page.chars)
            if sizes:
                body = sizes.most_common(1)[0][0]
                lo, hi = body * MIN_TEXT_RATIO, body * MAX_TEXT_RATIO
                page = page.filter(lambda o: o.get("object_type") != "char" or lo <= o.get("size", 0) <= hi)
            page = page.filter(lambda o: o.get("object_type") != "char" or not str(o.get("text", "")).startswith("(cid:"))
            words = [_Word(w["text"], w["x0"], w["x1"], w["top"]) for w in
                     page.extract_words(x_tolerance=1.5, y_tolerance=2)]
            bottoms = {(round(w["x0"], 1), round(w["top"], 1)): w["bottom"] for w in
                       page.extract_words(x_tolerance=1.5, y_tolerance=2)}
            rows = parser._rows(words)
            hdr = parser._detect_header(rows)
            if hdr:
                idx, centers, rev = hdr
                rows = rows[idx + 1:]
            elif centers is None:
                continue
            for row in rows:
                cells: dict = {}
                for w in row:
                    cells.setdefault(parser._nearest(w.xc, centers), []).append(w)
                dt = parser._line_text(cells.get("date", []), rev)
                if not is_date(dt):
                    continue

                def box(ws):
                    if not ws:
                        return None
                    b = max(bottoms.get((round(w.x0, 1), round(w.top, 1)), w.top + 9) for w in ws)
                    return (min(w.x0 for w in ws), min(w.top for w in ws), max(w.x1 for w in ws), b)
                out.append((pno, dt, box(cells.get("amount")), box(cells.get("balance")), centers.get("balance")))
    return out


def _desc_right_edge(pdf_path: Path) -> float:
    """הקצה הימני של עמודת התיאור: באמצע בין מרכז "סוג תנועה" למרכז העמודה שמימינה."""
    import pdfplumber
    parser = MizrahiOshParser()
    from ..ingest.mizrahi import _Word
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            words = [_Word(w["text"], w["x0"], w["x1"], w["top"]) for w in page.extract_words(x_tolerance=1.5)]
            hdr = parser._detect_header(parser._rows(words))
            if hdr:
                c = hdr[1]
                right = c.get("value_date", c.get("date"))
                return (c["description"] + right) / 2 + 12
    return 440.0


def annotate_pdf(src: str | Path, rep: AuditReport, dst: str | Path, against_reference: bool = False,
                 suggest_offset: bool = False) -> int:
    """→ מספר הסימונים. against_reference: היתרה הנכונה היא זו של הייחוס (הסימולטור), לא סכום התנועות בדוח.
    suggest_offset: ליד תנועה שסכומה שונה מהייחוס כותבים את תנועת הקיזוז האחת שמחזירה את הייחוס,
    במקום את הסכום בייחוס — כך התנועה עצמה נשארת כפי שהיא בדוח."""
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    pdfmetrics.registerFont(TTFont("DejaVu", FONT))
    reader = PdfReader(str(src))
    located = _located_rows(Path(src))
    ordered = _display_order(rep)
    if len(located) != len(ordered):
        raise ValueError(f"לא הצלחתי להתאים את שורות הקובץ ({len(located)}) לשורות שנבדקו ({len(ordered)})")

    marks_by_page: dict[int, list] = {}
    n = 0
    for (pno, dt, amt_box, bal_box, bal_center), r in zip(located, ordered):
        if dt[:5] != f"{r.date:%d/%m}":
            raise ValueError(f"שורה לא תואמת: {dt} מול {r.date:%d/%m/%y}")
        if r.status == "changed" and amt_box:
            marks_by_page.setdefault(pno, []).append(("amt", amt_box, r))
            n += 1
        if r.day_end and r.stated is not None:
            correct = r.orig_stated if against_reference else r.running
            if correct is not None and correct != r.stated:
                marks_by_page.setdefault(pno, []).append(("bal", bal_box, r, correct, bal_center))
                n += 1

    desc_right = _desc_right_edge(Path(src))
    writer = PdfWriter()
    total_bal = sum(1 for ms in marks_by_page.values() for m in ms if m[0] == "bal")
    for pno, page in enumerate(reader.pages):
        H = float(page.mediabox.height)
        W = float(page.mediabox.width)
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=(W, H))
        if pno == 0:
            c.setFillColorRGB(0.75, 0.1, 0.12)
            c.setFont("DejaVu", 9)
            basis = "לפי הסימולטור" if against_reference else "לפי סכום התנועות בדוח"
            c.drawRightString(W - 30, H - 16, _vis(f"סומנו {total_bal} יתרות שגויות. הערך הנכון ({basis}) כתוב באדום מתחת לכל אחת."))
            if suggest_offset:
                c.setFillColorRGB(0.45, 0.28, 0)
                c.drawRightString(W - 30, H - 28, _vis("בצהוב: התנועה שנוספה מעבר לסימולטור, ומתחתיה תנועת הקיזוז האחת שמבטלת את הפער."))
        for m in marks_by_page.get(pno, []):
            if m[0] == "amt":
                _, (x0, top, x1, bottom), r = m
                c.setFillColorRGB(1, 0.85, 0.2, alpha=0.35)
                c.setStrokeColorRGB(0.85, 0.6, 0)
                c.rect(x0 - 3, H - bottom - 2, (x1 - x0) + 6, (bottom - top) + 4, fill=1, stroke=1)
                c.setFillAlpha(1)
                c.setFillColorRGB(0.45, 0.28, 0)
                if suggest_offset:
                    # מתחת לתיאור התנועה (עמודת "סוג תנועה"), כדי לא להתנגש בתיקון היתרה באותה שורה
                    off = r.orig_amount - r.amount
                    _label_and_number(c, desc_right, H - bottom - 9.5, "להוסיף ביום זה תנועת קיזוז של",
                                      ("+" if off > 0 else "") + fmt(off), 7.4)
                else:
                    _label_and_number(c, x1 + 3, H - bottom - 9.5, "בסימולטור", fmt(r.orig_amount), 7)
            else:
                _, b, r, correct, center = m
                if b is None:     # יתרה שלא נקראה — מסמנים לפי מיקום העמודה
                    continue
                x0, top, x1, bottom = b
                c.setStrokeColorRGB(0.85, 0.1, 0.12)
                c.setLineWidth(1.1)
                c.rect(x0 - 3, H - bottom - 2, (x1 - x0) + 6, (bottom - top) + 4, fill=0, stroke=1)
                c.setFillColorRGB(0.85, 0.1, 0.12)
                c.setFillColorRGB(0.7, 0, 0.05)
                _label_and_number(c, x1 + 3, H - bottom - 9.5, "צ\"ל", fmt(correct), 7.4)
        c.showPage()          # גם עמוד בלי סימונים צריך עמוד שכבה
        c.save()
        buf.seek(0)
        overlay = PdfReader(buf).pages[0]
        page.merge_page(overlay)
        writer.add_page(page)
    with open(dst, "wb") as f:
        writer.write(f)
    return n
