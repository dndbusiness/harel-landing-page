"""לקוח סימולציה ריאליסטי עם "תשובות נכונות" — לניסוי הכנת השדות.

כל השמות והסכומים מומצאים. מה שכן מכוון להיות ריאליסטי: ניסוחי תיאור כמו שהם
מופיעים בדפי בנק (שם מעסיק בלי המילה "משכורת", קיצורים כמו ב.לאומי, BIT באנגלית,
כ.א.ל עם נקודות), הוראות קבע עם כללי הזזה שונים, משכנתה צמודה, עמלת ערוץ ישיר
עם מונה באסמכתה, וריבית חובה חודשית בשיעור ידוע.

לכל שורה יש truth_cat / truth_sub — הסיווג שיועץ היה נותן — כדי למדוד דיוק.
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

START, END = date(2026, 6, 18), date(2026, 9, 14)
OPENING = -2_183_450                 # −21,834.50
FEE_RATE = 176
TRUE_DEBIT_RATE = Decimal("13.25")   # % שנתי — "הודעת הבנק" של הלקוח
FRI, SAT = 4, 5
HOLIDAYS = {date(2026, 9, 12), date(2026, 9, 13)}   # ראש השנה (מתוך pyluach)

# (תיאור כפי שמופיע בדף, יום, סכום לפי חודש או קבוע, ערוץ, כלל שישי, קטגוריה, תת-קטגוריה)
MONTHLY = [
    ('אלביט מערכות בע"מ', 9, 1_684_000, None, "back", "הכנסות", "משכורת"),
    ("שכר - עיריית חיפה", 1, {7: 742_310, 8: 742_310, 9: 751_980}, None, "same", "הכנסות", "משכורת"),
    ("ב.לאומי-ילדים", 20, 34_200, None, "forward", "הכנסות", "קצבאות"),
    ("טפחות-משכנתאות", 1, {7: -612_480, 8: -614_115, 9: -615_760}, None, "same", "דיור/משכנתה", "משכנתה"),
    ("ארנונה עיריית חיפה", 1, -48_700, None, "same", "דיור/משכנתה", "ארנונה"),
    ("הלוואה 77812 קרן", 10, -185_000, None, "forward", "הלוואות", "החזר הלוואה"),
    ("הראל ביטוח בריאות", 15, -21_840, None, "same", "ביטוחים", "בריאות"),
    ("מגדל חיים ריסק", 15, -9_620, None, "same", "ביטוחים", "חיים"),
    ("מכבי שירותי בריאות", 5, -16_400, None, "same", "בריאות", "קופת חולים"),
    ("בזק בינלאומי", 18, -11_990, None, "same", "תקשורת", "אינטרנט וטלפון"),
    ("כרטיסי אשראי לישראל-כ.א.ל", 2, {7: -824_533, 8: -768_910, 9: -903_145}, None, "same", "כרטיסי אשראי", "חיוב מרוכז"),
    ("מקס איט פיננסים", 10, {7: -214_000, 8: -187_640, 9: -233_380}, None, "same", "כרטיסי אשראי", "חיוב מרוכז"),
    ("ביטוח לאומי דמי ביטוח", 15, -31_200, None, "same", "מיסים", "ביטוח לאומי (תשלום)"),
    ("הו\"ק גן הילדים", 3, -165_000, None, "same", "ילדים", "גן"),
]
BIMONTHLY = [  # (תיאור, חודשים, יום, סכום, קטגוריה, תת)
    ("חברת החשמל לישראל", (7, 9), 22, -62_480, "דיור/משכנתה", "חשבונות"),
    ("מי כרמל תאגיד מים", (8,), 25, -23_115, "דיור/משכנתה", "חשבונות"),
]
DIRECT = [  # פעולות (י) אקראיות: (תיאור, קטגוריה, תת, טווח באגורות)
    ("העברה ב-BIT", "העברות", "העברה יוצאת", (2_000, 45_000)),
    ("העב' לאחר-נייד", "העברות", "העברה יוצאת", (10_000, 150_000)),
    ("פייבוקס", "העברות", "העברה יוצאת", (3_000, 30_000)),
    ("תשלום ועד בית", "דיור/משכנתה", "ועד בית", (25_000, 25_000)),
]
ONE_OFF = [
    (date(2026, 7, 14), "החזר מס הכנסה", 412_300, "banker", "הכנסות", "החזרי מס"),
    (date(2026, 8, 6), "העברה מאת: כהן דוד", 150_000, None, "העברות", "העברה נכנסת"),
    (date(2026, 8, 23), "דמי ניהול חשבון", -1_490, None, "עמלות וריבית", "עמלות אחרות"),
    (date(2026, 7, 27), "תרומה עמותת לתת", -18_000, "direct", "שונות", "תרומות"),
    (date(2026, 9, 3), "משיכה מקופת גמל", 2_500_000, None, "הכנסות", "משיכות פנסיה"),
]


def is_closed(d):
    return d.weekday() == SAT or d in HOLIDAYS


def biz(d):
    return not is_closed(d) and d.weekday() != FRI


def shift(nom, fri):
    if nom.weekday() == FRI and not is_closed(nom):
        if fri == "same":
            return nom
        step = 1 if fri == "forward" else -1
    elif is_closed(nom):
        step = 1
    else:
        return nom
    d = nom + timedelta(days=step)
    while not biz(d):
        d += timedelta(days=step)
    return d


def first_biz(y, m):
    d = date(y, m, 1)
    while not biz(d):
        d += timedelta(days=1)
    return d


def build() -> list[dict]:
    rng = random.Random(2026)
    rows = []

    def add(d, desc, amt, ref, ch, cat, sub, kind=""):
        if START <= d <= END:
            rows.append(dict(date=d, description=desc, amount=amt, reference=str(ref), channel=ch,
                             truth_cat=cat, truth_sub=sub, kind=kind))

    for y, m in ((2026, 6), (2026, 7), (2026, 8), (2026, 9)):
        for desc, dom, amt, ch, fri, cat, sub in MONTHLY:
            a = amt.get(m) if isinstance(amt, dict) else amt
            if a is None:
                continue
            add(shift(date(y, m, dom), fri), desc, a, 800000 + dom * 10 + len(desc) % 10, ch, cat, sub)
        for desc, months, dom, amt, cat, sub in BIMONTHLY:
            if m in months:
                add(shift(date(y, m, dom), "same"), desc, amt, 700000 + dom, None, cat, sub)
    d = START
    while d <= END:
        if biz(d) and rng.random() < 0.6:
            for _ in range(rng.choice((1, 1, 2))):
                desc, cat, sub, (lo, hi) = rng.choice(DIRECT)
                amt = -(lo if lo == hi else rng.randrange(lo, hi, 10))
                add(d, desc, amt, rng.randrange(10000, 99999), "direct", cat, sub)
        if d.weekday() == 3 and rng.random() < 0.5:
            add(d, "משיכת מזומנים", -rng.choice((30_000, 50_000, 100_000)), rng.randrange(1000, 9999), "banker", "מזומן", "")
        d += timedelta(days=1)
    for d, desc, amt, ch, cat, sub in ONE_OFF:
        add(d, desc, amt, rng.randrange(1000, 9999), ch, cat, sub)
    rows.sort(key=lambda r: r["date"])

    def direct_count(y, m):
        return sum(1 for r in rows if r["channel"] == "direct" and (r["date"].year, r["date"].month) == (y, m))

    for (y, m), extra in (((2026, 6), 19), ((2026, 7), 0), ((2026, 8), 0)):
        post = first_biz(y + (m == 12), m % 12 + 1)
        n = direct_count(y, m) + extra
        add(post, "עמלת פעולה בערוץ ישיר", -n * FEE_RATE, n, None, "עמלות וריבית", "עמלת ערוץ ישיר", "fee")
    rows.sort(key=lambda r: r["date"])

    # ריבית חובה חודשית: נרשמת ביום העסקים הראשון על החודש הקודם (יתרה יומית × שיעור ÷ 365)
    for (y, m) in ((2026, 6), (2026, 7), (2026, 8)):
        post = first_biz(y + (m == 12), m % 12 + 1)
        acc, bal = Decimal(0), OPENING
        by = {}
        for r in rows:
            by.setdefault(r["date"], 0)
            by[r["date"]] += r["amount"]
        day = date(2026, 6, 1)
        while day < post:
            if day >= START:
                bal += by.get(day, 0)
            if day >= date(y, m, 1) and bal < 0:
                acc += Decimal(bal) * TRUE_DEBIT_RATE / Decimal(36500)
            day += timedelta(days=1)
        interest = int(acc.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        idx = next(i for i, r in enumerate(rows) if r["date"] >= post)
        rows.insert(idx, dict(date=post, description="ריבית חובה", amount=interest, reference="0", channel=None,
                              truth_cat="עמלות וריבית", truth_sub="ריבית חובה", kind="interest"))
    return rows


def with_balances(rows):
    bal = OPENING
    for i, r in enumerate(rows):
        bal += r["amount"]
        r["balance"] = bal if (i + 1 == len(rows) or rows[i + 1]["date"] != r["date"]) else None
    return rows
