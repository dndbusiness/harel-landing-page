"""דף השוואה: הדף האמיתי מול הדף החדש, שורה מול שורה, במסך אחד.

כל תנועה מהדף מופיעה בשורה אחת עם הסכום והיתרה הרצה בשני הצדדים, ועמודת הפרש
ביתרה ביניהם. תנועה שנוספה בתרחיש מופיעה רק בצד החדש, ותנועה שבוטלה רק בצד האמיתי.
"""
from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import date
from typing import Optional

from ..engine.simulate import SimResult
from ..model.money import fmt
from ..model.transaction import Transaction
from ..privacy.masking import mask_account, mask_text
from .html import WATERMARK

CHANNEL_MARK = {"direct": "(י) ", "banker": "(פ) "}


@dataclass
class CompareRow:
    date: date
    description: str
    channel: Optional[str]
    reference: str
    old_amount: Optional[int]       # None = לא קיימת בדף האמיתי (נוספה)
    new_amount: Optional[int]       # None = בוטלה בתרחיש
    old_balance: Optional[int]      # יתרה רצה אחרי השורה; None כשהשורה לא קיימת בצד הזה
    new_balance: Optional[int]
    status: str                     # same / changed / added / removed / projected
    note: str = ""
    day_end: bool = False           # השורה האחרונה של היום — כאן הבנק מציג יתרה

    @property
    def balance_gap(self) -> int:
        """הפרש היתרה הרצה (חדש פחות אמיתי) אחרי השורה."""
        return (self.new_balance if self.new_balance is not None else 0) - \
               (self.old_balance if self.old_balance is not None else 0)


def compare_rows(txns: list[Transaction], opening: int, scen: SimResult) -> list[CompareRow]:
    """שורות בסדר כרונולוגי. היתרה הרצה ממשיכה בכל צד גם בשורות שקיימות רק בצד השני."""
    by_tid = {r.txn_id: r for r in scen.rows() if r.txn_id}
    removed = {r.txn_id for r in scen.removed if r.txn_id}
    added_by_day: dict[date, list] = {}
    for r in scen.rows():
        if not r.txn_id:
            added_by_day.setdefault(r.date, []).append(r)

    out: list[CompareRow] = []
    old_bal = new_bal = opening
    days = sorted({t.date for t in txns} | set(added_by_day))
    by_day: dict[date, list[Transaction]] = {}
    for t in txns:
        by_day.setdefault(t.date, []).append(t)
    for d in days:
        day_rows: list[CompareRow] = []
        for t in by_day.get(d, []):
            old_bal += t.amount_agorot
            if t.id in removed:
                day_rows.append(CompareRow(d, t.description, t.channel, t.reference, t.amount_agorot, None,
                                           old_bal, new_bal, "removed", "בוטלה בתרחיש"))
                continue
            r = by_tid.get(t.id)
            amt = r.amount if r is not None else t.amount_agorot
            new_bal += amt
            status = "same" if amt == t.amount_agorot else "changed"
            day_rows.append(CompareRow(d, t.description, t.channel, r.reference if r is not None else t.reference,
                                       t.amount_agorot, amt, old_bal, new_bal, status,
                                       (r.note if r is not None and status == "changed" else "")))
        for r in added_by_day.get(d, []):
            new_bal += r.amount
            day_rows.append(CompareRow(d, r.description, r.channel, r.reference, None, r.amount,
                                       old_bal if d <= txns[-1].date else None, new_bal,
                                       "projected" if r.origin in ("projected", "fee", "interest") else "added", r.note))
        if day_rows:
            day_rows[-1].day_end = True
        out.extend(day_rows)
    return out


CSS = """
:root{--bg:#F3F5F4;--surface:#FFFFFF;--sunk:#E8EDEC;--line:#D3DCDA;--ink:#0B2730;--muted:#4E666E;
  --old:#5B6B73;--new:#178379;--neg:#B42318;--pos:#16794A;--chg:#FFF1CF;--chg-ink:#7A5200;--add:#E2F4EE;--del:#FBE4E1;
  --gapup:#16794A;--gapdown:#B42318;--wm:rgba(180,35,24,.08);--mast:#061A22;--mast-ink:#F4F1EA}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#08161C;--surface:#0E222B;--sunk:#133039;--line:#21424D;
  --ink:#E8EEEC;--muted:#9DB3B8;--old:#A9B8BE;--new:#4FD6C8;--neg:#FF8A80;--pos:#5BD99A;--chg:#3A3014;--chg-ink:#F2C766;
  --add:#0F3A32;--del:#3D1A17;--gapup:#5BD99A;--gapdown:#FF8A80;--wm:rgba(255,138,128,.08);--mast:#040F14;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#08161C;--surface:#0E222B;--sunk:#133039;--line:#21424D;--ink:#E8EEEC;--muted:#9DB3B8;--old:#A9B8BE;
  --new:#4FD6C8;--neg:#FF8A80;--pos:#5BD99A;--chg:#3A3014;--chg-ink:#F2C766;--add:#0F3A32;--del:#3D1A17;--gapup:#5BD99A;
  --gapdown:#FF8A80;--wm:rgba(255,138,128,.08);--mast:#040F14;color-scheme:dark}
*{box-sizing:border-box}
html{direction:rtl}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 "Heebo","Arial Hebrew",Arial,"DejaVu Sans",sans-serif}
.mast{background:var(--mast);color:var(--mast-ink);padding:16px}
.mast .in{max-width:1400px;margin:0 auto;display:flex;flex-wrap:wrap;gap:6px 18px;align-items:baseline}
.mast h1{margin:0;font-size:1.3rem}
.mast .sub{opacity:.75;font-size:.88rem}
.flag{margin-inline-start:auto;border:1.5px solid #E0584B;color:#FF9A8F;border-radius:6px;padding:3px 10px;font-weight:700;font-size:.82rem}
main{max-width:1400px;margin:0 auto;padding:16px;display:flex;flex-direction:column;gap:14px}
.sum{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,190px),1fr));gap:10px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:10px 12px;display:flex;flex-direction:column;gap:2px}
.card .k{font-size:.78rem;color:var(--muted)}
.card .v{font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace;font-size:1.1rem;direction:ltr;text-align:right}
.card .d{font-size:.76rem;color:var(--muted)}
.tools{display:flex;flex-wrap:wrap;gap:14px;align-items:center;font-size:.88rem}
.legend{display:flex;flex-wrap:wrap;gap:12px;color:var(--muted);font-size:.8rem}
.sw{display:inline-block;width:12px;height:12px;border-radius:3px;vertical-align:-2px;margin-inline-end:4px;border:1px solid var(--line)}
.scroll{overflow:auto;max-height:calc(100vh - 230px);background:var(--surface);border:1px solid var(--line);border-radius:10px;position:relative}
.wm{position:sticky;top:40%;height:0;pointer-events:none;z-index:0}
.wm span{position:absolute;left:4%;transform:rotate(-18deg);font-size:46px;font-weight:800;color:var(--wm);white-space:nowrap}
table{width:100%;border-collapse:separate;border-spacing:0;font-size:.86rem;position:relative;z-index:1}
th,td{padding:5px 8px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
td.desc{white-space:normal;min-width:170px}
thead th{position:sticky;background:var(--sunk);z-index:2;font-size:.78rem;color:var(--muted)}
thead tr.g th{top:0;font-size:.85rem;color:var(--ink);text-align:center;border-bottom:0}
thead tr.c th{top:30px}
th.old,td.old{background:color-mix(in srgb,var(--old) 6%,transparent)}
th.new,td.new{background:color-mix(in srgb,var(--new) 7%,transparent)}
thead tr.g th.old{color:var(--old)} thead tr.g th.new{color:var(--new)}
.sep{border-inline-start:2px solid var(--line)}
.n{font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace;font-variant-numeric:tabular-nums;direction:ltr;text-align:left}
.neg{color:var(--neg)} .pos{color:var(--pos)}
tr.dayend td{border-bottom:2px solid var(--line)}
tr.dayend td.bal{font-weight:700}
td.bal.mid{color:var(--muted);font-weight:400}
tr.changed td{background:var(--chg)}
tr.changed td.amt.new{color:var(--chg-ink);font-weight:700}
tr.added td{background:var(--add)}
tr.removed td{background:var(--del)}
tr.removed td.desc{text-decoration:line-through}
td.gap.up{color:var(--gapup);font-weight:700} td.gap.down{color:var(--gapdown);font-weight:700}
td.gap.zero{color:var(--muted)}
.tag{display:inline-block;font-size:.7rem;font-weight:700;border-radius:99px;padding:0 7px;margin-inline-start:6px;background:var(--sunk);color:var(--muted)}
tr.changed .tag{background:var(--chg-ink);color:var(--surface)}
.note{color:var(--muted);font-size:.74rem}
body.only-changes tr.quiet{display:none}
@media print{
  @page{size:A4 landscape;margin:10mm}
  body{background:#fff;color:#000}
  .mast{background:#fff;color:#000;border-bottom:2px solid #000}
  .tools{display:none}
  .scroll{max-height:none;overflow:visible;border:0}
  thead{display:table-header-group} tr{break-inside:avoid}
  thead th{position:static}
  .wm{position:fixed;top:45%;left:0;right:0}
  .wm span{color:rgba(180,35,24,.10)}
}
"""

JS = """
const cb=document.getElementById('onlyChanges');
cb.addEventListener('change',()=>document.body.classList.toggle('only-changes',cb.checked));
"""


def _cls(a: Optional[int]) -> str:
    return "" if a is None else "neg" if a < 0 else "pos" if a > 0 else ""


def _m(a: Optional[int]) -> str:
    return "" if a is None else f'<span class="{_cls(a)}">{fmt(a)}</span>'


def compare_html(txns: list[Transaction], opening: int, scen: SimResult, account_hint: str = "") -> str:
    rows = compare_rows(txns, opening, scen)
    changed_days = {r.date for r in rows if r.status != "same" or r.balance_gap != 0}
    status_tag = {"changed": "שונה", "added": "נוספה", "removed": "בוטלה", "projected": "הקרנה"}

    body_rows = []
    days: dict[date, list[CompareRow]] = {}
    for r in rows:
        days.setdefault(r.date, []).append(r)
    for d in sorted(days, reverse=True):              # כמו בדף: ימים מהחדש לישן
        for r in days[d]:                              # בתוך היום בסדר הדף, יתרה בשורה האחרונה
            gap = r.balance_gap
            gcls = "up" if gap > 0 else "down" if gap < 0 else "zero"
            quiet = "" if d in changed_days else " quiet"
            mark = CHANNEL_MARK.get(r.channel or "", "")
            tag = f'<span class="tag">{status_tag[r.status]}</span>' if r.status in status_tag else ""
            note = f'<div class="note">{html.escape(r.note)}</div>' if r.note else ""
            bal_cls = "bal" if r.day_end else "bal mid"
            body_rows.append(
                f'<tr class="{r.status}{" dayend" if r.day_end else ""}{quiet}">'
                f"<td>{r.date:%d/%m/%y}</td>"
                f'<td class="desc">{html.escape(mark + mask_text(r.description))}{tag}{note}</td>'
                f'<td class="n old amt sep">{_m(r.old_amount)}</td>'
                f'<td class="n old {bal_cls}">{_m(r.old_balance) if r.old_amount is not None else ""}</td>'
                f'<td class="n new amt sep">{_m(r.new_amount)}</td>'
                f'<td class="n new {bal_cls}">{_m(r.new_balance) if r.new_amount is not None or r.status == "removed" else ""}</td>'
                f'<td class="n gap sep {gcls}">{("+" if gap > 0 else "") + fmt(gap) if gap else "0.00"}</td>'
                f'<td class="n">{html.escape(r.reference)}</td></tr>')

    hist_end = txns[-1].date
    old_close = next(r.old_balance for r in reversed(rows) if r.old_balance is not None)
    new_close = rows[-1].new_balance
    gaps = [(r.balance_gap, r.date) for r in rows]
    max_up = max(gaps)
    max_down = min(gaps)
    n_changed = sum(r.status != "same" for r in rows)
    eod = {}
    for r in rows:
        if r.day_end:
            eod[r.date] = r.balance_gap
    same_days = sum(1 for g in eod.values() if g == 0)
    acct = mask_account(account_hint)
    period = f"{rows[0].date:%d/%m/%Y} – {rows[-1].date:%d/%m/%Y}"

    def card(k, v, d=""):
        return f'<div class="card"><span class="k">{k}</span><span class="v">{v}</span><span class="d">{d}</span></div>'

    cards = "".join([
        card(f"יתרת סגירה, דף אמיתי ({hist_end:%d/%m})", _m(old_close)),
        card(f"יתרת סגירה, דף חדש ({rows[-1].date:%d/%m})", _m(new_close),
             f"הפרש {('+' if new_close - old_close > 0 else '') + fmt(new_close - old_close)}"),
        card("תנועות ששונו", str(n_changed), f"מתוך {len(rows)} שורות"),
        card("ימים עם אותה יתרת סוף יום", f"{same_days} / {len(eod)}"),
        card("פער יתרה גבוה ביותר", _m(max_up[0]) if max_up[0] > 0 else "0.00",
             f"{max_up[1]:%d/%m/%Y}" if max_up[0] > 0 else "אין יום שבו החדש גבוה יותר"),
        card("פער יתרה נמוך ביותר", _m(max_down[0]) if max_down[0] < 0 else "0.00",
             f"{max_down[1]:%d/%m/%Y}" if max_down[0] < 0 else "אין יום שבו החדש נמוך יותר"),
    ])
    title = f"השוואה: {scen.name}"
    return f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title>
<style>{CSS}</style></head><body>
<header class="mast"><div class="in"><h1>דף אמיתי מול דף חדש</h1>
<span class="sub">{html.escape(scen.name)} · {period}{' · חשבון ' + acct if acct else ''}</span>
<span class="flag">{WATERMARK}</span></div></header>
<main>
<section class="sum">{cards}</section>
<div class="tools"><label><input type="checkbox" id="onlyChanges"> רק ימים עם שינוי</label>
<span class="legend"><span><i class="sw" style="background:var(--chg)"></i>סכום שונה</span>
<span><i class="sw" style="background:var(--add)"></i>נוספה בתרחיש</span>
<span><i class="sw" style="background:var(--del)"></i>בוטלה בתרחיש</span>
<span>יתרה מודגשת = יתרת סוף יום, כמו בדף הבנק</span>
<span>הפרש ביתרה = יתרה רצה בדף החדש פחות בדף האמיתי</span></span></div>
<div class="scroll"><div class="wm" aria-hidden="true"><span>{WATERMARK}</span></div>
<table><thead>
<tr class="g"><th colspan="2"></th><th class="old sep" colspan="2">דף אמיתי</th><th class="new sep" colspan="2">דף חדש (סימולציה)</th><th class="sep" colspan="2"></th></tr>
<tr class="c"><th>תאריך</th><th>סוג תנועה</th><th class="old sep">זכות/חובה</th><th class="old">יתרה רצה</th>
<th class="new sep">זכות/חובה</th><th class="new">יתרה רצה</th><th class="sep">הפרש ביתרה</th><th>אסמכתה</th></tr>
</thead><tbody>{''.join(body_rows)}</tbody></table></div>
<p class="note">הופק בכלי סימולציה מנתוני לקוח. הדף החדש אינו מסמך בנקאי. יתרת פתיחה {fmt(opening)}.</p>
</main><script>{JS}</script></body></html>"""
