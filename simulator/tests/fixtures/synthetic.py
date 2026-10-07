"""דף עו"ש סינתטי בפורמט מזרחי טפחות, לבדיקות. כל השמות והסכומים מומצאים.

נבנה כך שיתנהג כמו הדף שנצפה: יתרה רק בשורה האחרונה של כל יום, (י)/(פ), אין שבת,
מנפיקים שונים מתנהגים אחרת בשישי, עמלת ערוץ ישיר עם מונה באסמכתה, וחיוב ריבית
אחד שמחושב בשיעור ידוע מהיתרות היומיות.
"""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

START, END = date(2026, 6, 18), date(2026, 9, 14)
OPENING = -1_250_000          # אגורות
FEE_RATE = 176
DEBIT_RATE = Decimal("12.5")  # % שנתי, רק לבדיקת הכיול
FRI, SAT = 4, 5


def _shift(d: date, friday: str) -> date:
    if d.weekday() == FRI:
        return d if friday == "same" else d + timedelta(days=2)
    if d.weekday() == SAT:
        return d + timedelta(days=1)
    return d


def build() -> list[dict]:
    """→ שורות כרונולוגיות: date, description, amount, reference, channel, kind."""
    rng = random.Random(7)
    rows: list[dict] = []

    def add(d, desc, amount, ref, channel=None, kind=""):
        rows.append(dict(date=d, description=desc, amount=amount, reference=str(ref), channel=channel, kind=kind))

    # הוראות קבע חודשיות: (תיאור, יום, סכום, ערוץ, כלל שישי)
    monthly = [
        ("משכורת חברת דוגמה בע\"מ", 10, 1_423_000, None, "forward"),
        ("משכנתא טפחות", 1, -512_340, None, "same"),
        ("הוראת קבע ביטוח בריאות דמו", 15, -23_480, None, "same"),
        ("הלוואה 4471", 20, -150_000, None, "forward"),
        ("ישראכרט חיוב חודשי", 2, None, None, "same"),
        ("קצבת ילדים ביטוח לאומי", 20, 18_900, None, "forward"),
    ]
    card = {7: -612_455, 8: -583_120, 9: -701_990}
    mortgage_drift = {6: -512_340, 7: -513_102, 8: -513_871, 9: -514_640}

    d = START
    while d <= END:
        if d.weekday() != SAT:
            for desc, dom, amt, ch, fri in monthly:
                nominal = d.replace(day=dom) if dom <= 28 else d
                if _shift(nominal, fri) == d and nominal.month == d.month:
                    if "ישראכרט" in desc:
                        amt = card.get(d.month)
                        if amt is None:
                            continue
                    if "משכנתא" in desc:
                        amt = mortgage_drift[d.month]
                    add(d, desc, amt, 900000 + dom, ch)
            # פעולות בערוץ ישיר: העברות, ביט, תשלומים
            if d.weekday() != FRI and rng.random() < 0.55:
                for _ in range(rng.choice((1, 1, 2))):
                    add(d, rng.choice(["העברה לחשבון אחר", "תשלום חשבון חשמל", "העברה ביט"]),
                        -rng.randrange(5_000, 90_000, 10), rng.randrange(10000, 99999), "direct")
            if d.weekday() == 2 and rng.random() < 0.5:
                add(d, "משיכת מזומן כספומט", -rng.choice((20_000, 40_000, 100_000)), rng.randrange(1000, 9999), "banker")
        d += timedelta(days=1)

    # שתי תנועות זהות באותו יום — לגיטימי
    add(date(2026, 7, 6), "העברה ביט", -5_000, 55555, "direct")
    add(date(2026, 7, 6), "העברה ביט", -5_000, 55555, "direct")
    add(date(2026, 6, 18), "הפקדת שיק", 40_000, 3141, "banker")
    rows.sort(key=lambda r: r["date"])

    # עמלת ערוץ ישיר: יום העסקים הראשון בחודש הבא, אסמכתה = מונה
    def direct_count(y, m):
        return sum(1 for r in rows if r["channel"] == "direct" and (r["date"].year, r["date"].month) == (y, m))

    june_before_start = 14   # פעולות (י) ביוני לפני תחילת הדף — לא נראות, אבל נספרות
    for (y, m), post in (((2026, 6), date(2026, 7, 1)), ((2026, 7), date(2026, 8, 2)), ((2026, 8), date(2026, 9, 1))):
        n = direct_count(y, m) + (june_before_start if m == 6 else 0)
        rows.append(dict(date=post, description="עמלת פעולות בערוץ ישיר", amount=-n * FEE_RATE,
                         reference=str(n), channel=None, kind="fee"))
    rows.sort(key=lambda r: r["date"])

    # ריבית חובה: נרשמת 01/09 על התקופה 01/07–31/08 (שיעור ידוע)
    post = date(2026, 9, 1)
    bal, acc, day = OPENING, Decimal(0), START
    by_day = {}
    for r in rows:
        by_day.setdefault(r["date"], []).append(r["amount"])
    while day < post:
        bal += sum(by_day.get(day, []))
        if day >= date(2026, 7, 1) and bal < 0:
            acc += Decimal(bal) * DEBIT_RATE / Decimal(36500)
        day += timedelta(days=1)
    interest = int(acc.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    # נרשמת לפני העמלה באותו יום
    idx = next(i for i, r in enumerate(rows) if r["date"] == post)
    rows.insert(idx, dict(date=post, description="ריבית חובה", amount=interest, reference="0",
                          channel=None, kind="interest"))
    return rows


def with_balances(rows: list[dict]) -> list[dict]:
    bal = OPENING
    for i, r in enumerate(rows):
        bal += r["amount"]
        last_of_day = i + 1 == len(rows) or rows[i + 1]["date"] != r["date"]
        r["balance"] = bal if last_of_day else None
    return rows


def _money(a):
    if a is None:
        return ""
    s = f"{abs(a) // 100:,}.{abs(a) % 100:02d}"
    return "-" + s if a < 0 else s


def _desc(r):
    mark = {"direct": "(י) ", "banker": "(פ) "}.get(r["channel"] or "", "")
    return mark + r["description"]


def bank_order(rows):
    """כמו בדף: ימים מהחדש לישן, בתוך יום כרונולוגי — היתרה בשורה האחרונה של היום."""
    days = {}
    for r in rows:
        days.setdefault(r["date"], []).append(r)
    return [r for d in reversed(list(days)) for r in days[d]]


def write_csv(rows, path: Path):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "value_date", "description", "amount", "balance", "reference", "channel"])
        for r in bank_order(rows):
            w.writerow([r["date"].strftime("%d/%m/%Y"), "", _desc(r), _money(r["amount"]),
                        _money(r["balance"]), r["reference"], ""])


def write_pdf(rows, path: Path, visual_order: bool = True):
    """PDF בפריסת הדף: עמודות מימין לשמאל. visual_order=True כותב עברית בסדר חזותי
    (כמו ש-PDF בנקאי רבים שומרים), כך שהשליפה מחזירה טקסט הפוך שהמפרק צריך לתקן."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    from oshsim.ingest.hebrew import visual_to_logical

    pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    c = canvas.Canvas(str(path), pagesize=A4)
    W, H = A4
    # מרכזי עמודות (x) מימין לשמאל: תאריך, תאריך ערך, סוג תנועה, זכות/חובה, יתרה, אסמכתה
    cols = {"date": 535, "value_date": 470, "description": 360, "amount": 225, "balance": 140, "reference": 60}
    headers = {"date": "תאריך", "value_date": "תאריך ערך", "description": "סוג תנועה",
               "amount": "זכות/חובה", "balance": "יתרה", "reference": "אסמכתה"}

    def txt(s):
        # visual_to_logical הוא אינוולוציה על טקסט עברי — אותה פונקציה הופכת לחזותי
        return visual_to_logical(s) if visual_order else s

    def header():
        c.setFont("DejaVu", 11)
        c.drawRightString(W - 40, H - 40, txt("עובר ושב - יתרה ותנועות בחשבון"))
        c.setFont("DejaVu", 8)
        for k, x in cols.items():
            c.drawCentredString(x, H - 80, txt(headers[k]))

    disp = bank_order(rows)
    per_page = 48
    for p in range(0, len(disp), per_page):
        header()
        y = H - 100
        for r in disp[p:p + per_page]:
            c.drawCentredString(cols["date"], y, r["date"].strftime("%d/%m/%y"))
            c.drawCentredString(cols["description"], y, txt(_desc(r)))
            c.drawCentredString(cols["amount"], y, _money(r["amount"]))
            if r["balance"] is not None:
                c.drawCentredString(cols["balance"], y, _money(r["balance"]))
            c.drawCentredString(cols["reference"], y, r["reference"])
            y -= 14
        c.setFont("DejaVu", 7)
        c.drawCentredString(W / 2, 30, txt(f"עמוד {p // per_page + 1}"))
        c.showPage()
    c.save()


def generate(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = with_balances(build())
    write_csv(rows, out_dir / "synthetic.csv")
    write_pdf(rows, out_dir / "synthetic.pdf")
    return {"rows": rows, "opening": OPENING, "closing": rows[-1]["balance"]}


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    info = generate(Path(sys.argv[1] if len(sys.argv) > 1 else "."))
    print(len(info["rows"]), "rows; closing", _money(info["closing"]))
