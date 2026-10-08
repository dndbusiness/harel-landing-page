"""העתק פריסה של דף העו"ש המקורי עם נתוני התרחיש, וכל פרט ששונה מודגש.

אותן עמודות, רוחבים, גופנים, צבעי סכומים, יתרה בשורה האחרונה של כל יום ושורת
המקרא בתחתית — כך שאפשר להניח את שני הדפים זה לצד זה ולראות רק את מה שזז.

במכוון לא מועתקים: לוגו ושם הבנק, מספר חשבון מלא ושם הלקוח. במקומם מופיע בכל עמוד
"סימולציה — אינו מסמך בנקאי" (סעיף 9ב במפרט), כדי שהמסמך לא ישמש כדף בנק אמיתי.
"""
from __future__ import annotations

import html
from datetime import datetime

from ..engine.simulate import SimResult
from ..model.money import fmt
from ..model.transaction import Transaction
from ..privacy.masking import mask_account
from .compare import compare_rows
from .html import WATERMARK

CHANNEL_SUFFIX = {"direct": " (י)", "banker": " (פ)"}

# מידות בנקודות, כפי שנמדדו מהדף המקורי (A4 לאורך, 595×842)
CSS = """
@page{size:A4 portrait;margin:18pt 0 30pt}
*{box-sizing:border-box}
html,body{margin:0;background:#fff;color:#222;direction:rtl;
  font-family:"Assistant","Heebo","Arial Hebrew",Arial,"DejaVu Sans",sans-serif}
.page{width:595pt;padding:8pt 32pt 0 26.5pt;position:relative}
.top{display:flex;justify-content:space-between;align-items:flex-start;padding-inline:4pt}
.meta{font-size:9.6pt;line-height:13pt}
.flag{border:1.5pt solid #c0262d;color:#c0262d;font-weight:700;font-size:9pt;padding:5pt 8pt;border-radius:3pt;text-align:center;line-height:12pt;margin-top:4pt}
h1{font-size:13.6pt;font-weight:400;margin:14pt 4pt 0}
h2{font-size:20.4pt;font-weight:400;margin:26pt 10pt 0}
.period{font-size:9.1pt;margin:36pt 4pt 10pt}
table{width:537pt;border-collapse:collapse;font-size:9.1pt}
col.c-date{width:47.6pt} col.c-vdate{width:75.9pt} col.c-desc{width:146.1pt}
col.c-amt{width:79.9pt} col.c-bal{width:81pt} col.c-ref{width:73.6pt} col.c-pad{width:32.9pt}
thead th{background:#eaecec;font-weight:700;height:25pt;padding:0 6pt;text-align:right;border:0}
th.amt,th.bal,td.amt,td.bal{text-align:left;padding-left:8pt}
th.ref,td.ref{text-align:left;padding-left:8pt}
tbody td{height:25.4pt;padding:0 6pt;border-bottom:.6pt solid #e3e6e6;vertical-align:middle;white-space:nowrap}
tbody{border-inline:.6pt solid #e3e6e6}
td.desc{white-space:normal}
tr.section td{font-size:9.1pt;height:25.4pt}
.n{direction:ltr;unicode-bidi:isolate;font-variant-numeric:tabular-nums}
.neg{color:#e0303f} .pos{color:#16a35f}
/* הדגשת שינויים */
td.chg{background:#fff1b8;box-shadow:inset 0 0 0 1.2pt #e0a800}
td.chg .was{display:block;font-size:7.6pt;line-height:9.5pt;color:#555;margin-top:1pt}
td.balchg{background:#ffe2c6;box-shadow:inset 0 0 0 1.2pt #f08a24}
td.balchg .was{display:block;font-size:7.6pt;line-height:9.5pt;color:#555;margin-top:1pt}
tr.added td{background:#dff3ea}
tr.removed td{background:#fbe1de;text-decoration:line-through}
.mark{display:inline-block;font-size:6.8pt;font-weight:700;color:#7a5200;background:#ffd84d;border-radius:6pt;padding:0 4pt;margin-inline-start:3pt}
.legend{font-size:9.1pt;margin:8pt 4pt 0}
.keys{display:flex;flex-wrap:wrap;gap:4pt 14pt;font-size:8pt;color:#444;margin:0 4pt 8pt}
.keys i{display:inline-block;width:10pt;height:10pt;vertical-align:-1.5pt;margin-inline-end:3pt;border-radius:2pt}
.wm{position:fixed;top:-18pt;left:0;width:595pt;height:842pt;display:flex;align-items:center;justify-content:center;pointer-events:none;z-index:9}
.wm span{transform:rotate(-35deg);font-size:46pt;font-weight:800;color:rgba(192,38,45,.09);white-space:nowrap}
.foot{position:fixed;bottom:-20pt;left:0;width:595pt;text-align:center;font-size:7.5pt;color:#c0262d;font-weight:700}
thead{display:table-header-group} tr{break-inside:avoid}
@media screen{body{background:#e9ecec}.page{margin:16px auto;background:#fff;box-shadow:0 2px 12px rgba(0,0,0,.15)}
  .wm,.foot{position:absolute}}
"""


def _amt(a: int | None) -> str:
    if a is None:
        return ""
    cls = "neg" if a < 0 else "pos" if a > 0 else ""
    return f'<span class="n {cls}">{fmt(a)}</span>'


def replica_html(txns: list[Transaction], opening: int, scen: SimResult, account_hint: str = "",
                 period_label: str = "", generated: datetime | None = None, was_label: str = "במקור",
                 compare_to_stated: bool = False) -> str:
    """txns: הדף שמולו מסמנים שינויים. compare_to_stated: היתרה "לפני" היא מה שרשום בדף
    (ולא סכום התנועות שלו) — לדוח שנערך ידנית ויתרותיו לא מתיישבות."""
    rows = compare_rows(txns, opening, scen)
    days: dict = {}
    for r in rows:
        days.setdefault(r.date, []).append(r)
    old_day_bal = {r.date: r.old_balance for r in rows if r.day_end}
    if compare_to_stated:
        old_day_bal = {t.date: t.day_balance_agorot for t in txns if t.day_balance_agorot is not None}

    body = []
    n_amt = n_bal = 0
    for d in sorted(days, reverse=True):                 # כמו בדף: ימים מהחדש לישן
        for r in days[d]:                                 # בתוך יום בסדר הדף, יתרה בשורה האחרונה
            desc = html.escape(r.description + CHANNEL_SUFFIX.get(r.channel or "", ""))
            amt_cell = f'<td class="amt">{_amt(r.new_amount if r.status != "removed" else r.old_amount)}</td>'
            tr_cls = ""
            if r.status == "changed":
                n_amt += 1
                amt_cell = (f'<td class="amt chg">{_amt(r.new_amount)}'
                            f'<span class="was">{was_label} <s class="n">{fmt(r.old_amount)}</s></span></td>')
                desc += '<span class="mark">שונה</span>'
            elif r.status in ("added", "projected"):
                tr_cls = "added"
                desc += '<span class="mark">נוספה</span>'
            elif r.status == "removed":
                tr_cls = "removed"
            bal_cell = '<td class="bal"></td>'
            if r.day_end:
                new_b = r.new_balance
                old_b = old_day_bal.get(d)
                if old_b is not None and new_b != old_b:
                    n_bal += 1
                    bal_cell = (f'<td class="bal balchg">{_amt(new_b)}'
                                f'<span class="was">{was_label} <s class="n">{fmt(old_b)}</s></span></td>')
                else:
                    bal_cell = f'<td class="bal">{_amt(new_b)}</td>'
            body.append(f'<tr class="{tr_cls}"><td>{d:%d/%m/%y}</td><td></td><td class="desc">{desc}</td>'
                        f'{amt_cell}{bal_cell}<td class="ref n">{html.escape(r.reference)}</td><td></td></tr>')

    acct = mask_account(account_hint)
    gen = (generated or datetime.now()).strftime("%d/%m/%Y %H:%M")
    start, end = rows[0].date, rows[-1].date
    period = period_label or f"תנועות בחשבון מתאריך {start:%d/%m/%Y} עד {end:%d/%m/%Y}"
    return f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>סימולציה: {html.escape(scen.name)}</title>
<style>{CSS}</style></head><body>
<div class="wm" aria-hidden="true"><span>{WATERMARK}</span></div>
<div class="foot">{WATERMARK} · הופק בכלי סימולציה מנתוני לקוח · התרחיש: {html.escape(scen.name)}</div>
<div class="page">
  <div class="top">
    <div class="meta">הופק בסימולציה בתאריך {gen}<br>חשבון מספר {acct or '—'}<br>&nbsp;</div>
    <div class="flag">{WATERMARK}</div>
  </div>
  <h1>עובר ושב -יתרה ותנועות בחשבון</h1>
  <h2>יתרה ותנועות בחשבון</h2>
  <p class="period">{html.escape(period)}</p>
  <div class="keys"><span><i style="background:#fff1b8;box-shadow:inset 0 0 0 1pt #e0a800"></i>סכום תנועה ששונה ({n_amt})</span>
    <span><i style="background:#ffe2c6;box-shadow:inset 0 0 0 1pt #f08a24"></i>יתרת סוף יום ששונתה ({n_bal})</span>
    <span>הערך המקורי מופיע מתחת לערך החדש</span></div>
  <table>
    <colgroup><col class="c-date"><col class="c-vdate"><col class="c-desc"><col class="c-amt"><col class="c-bal"><col class="c-ref"><col class="c-pad"></colgroup>
    <thead><tr><th>תאריך</th><th>תאריך ערך</th><th>סוג תנועה</th><th class="amt">זכות/חובה</th><th class="bal">יתרה בש"ח</th><th class="ref">אסמכתה</th><th></th></tr></thead>
    <tbody><tr class="section"><td colspan="7">תנועות אחרונות</td></tr>{''.join(body)}</tbody>
  </table>
  <p class="legend">(י)-פעולה בערוץ ישיר. (פ)-פעולה על ידי בנקאי.</p>
</div></body></html>"""
