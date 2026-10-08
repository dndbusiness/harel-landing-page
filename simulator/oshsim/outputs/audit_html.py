"""דוח בדיקת יתרות — באותה פריסה של דף הבנק, עם גוש היתרות המצטברות מודגש בצד שמאל.

עם דף ייחוס (הסימולטור או המקור): לכל יום — היתרה בדוח מול היתרה לפי הייחוס, הפער,
ומאיפה הוא בא (תנועה שסכומה שונה, פער שנגרר מיום קודם, או יתרה שנרשמה לא נכון).
בלי ייחוס: היתרה בדוח מול הסכום המצטבר של התנועות שבדוח עצמו.
"""
from __future__ import annotations

import html

from ..model.money import fmt
from ..validate.audit import AuditReport
from .html import WATERMARK

CHANNEL_SUFFIX = {"direct": " (י)", "banker": " (פ)"}

CSS = """
@page{size:A4 landscape;margin:14pt 12pt 18pt}
*{box-sizing:border-box}
html,body{margin:0;background:#fff;color:#222;direction:rtl;font-family:"Assistant","Heebo","Arial Hebrew",Arial,"DejaVu Sans",sans-serif}
.page{max-width:1120px;margin:0 auto;padding:14px 16px}
h1{font-size:17pt;font-weight:400;margin:0 0 2pt}
.sub{font-size:9.5pt;color:#555;margin:0 0 10pt}
.verdict{border-radius:6px;padding:9px 12px;font-size:10.5pt;margin:0 0 10pt}
.verdict.ok{background:#e3f5ea;border:1px solid #16a35f}
.verdict.bad{background:#fde6e4;border:1px solid #d22b2b}
.verdict ul{margin:4pt 0 0;padding-inline-start:16pt}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin:0 0 10pt}
.card{border:1px solid #dfe3e3;border-radius:6px;padding:7px 9px}
.card .k{font-size:8pt;color:#666}.card .v{font-size:12pt;direction:ltr;text-align:right;font-variant-numeric:tabular-nums}
.scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:8.8pt}
th,td{padding:3.5pt 5pt;border-bottom:.6pt solid #e3e6e6;text-align:right;white-space:nowrap;vertical-align:middle}
td.desc{white-space:normal;min-width:120pt}
td.why{white-space:normal;min-width:150pt;font-size:8.2pt}
thead th{background:#eaecec;font-weight:700}
thead tr:not(.grp) th{white-space:normal;line-height:1.15}
thead tr.grp th{font-size:9.5pt;text-align:center;border-bottom:0}
.n{direction:ltr;unicode-bidi:isolate;text-align:left;font-variant-numeric:tabular-nums}
.neg{color:#e0303f}.pos{color:#16a35f}
/* גוש היתרות המצטברות — צד שמאל */
thead th.balgrp{background:#1f4e79;color:#fff;border-inline-start:2.5pt solid #1f4e79}
th.bal,td.bal{background:#eaf2fb}
th.bal.first,td.bal.first{border-inline-start:2.5pt solid #1f4e79}
td.run{color:#7a8a99}
tr.dayend td{border-bottom:1.4pt solid #b9c3c3}
tr.dayend td.stated{font-weight:700}
td.ok{color:#16a35f;font-weight:700}
td.err{background:#ffd6d2;color:#b3121b;font-weight:700}
tr.changed td.amt{background:#fff1b8;font-weight:700}
tr.added td{background:#dff3ea}
.was{font-size:7.5pt;color:#555;display:block;font-weight:400}
.mark{font-size:7pt;font-weight:700;background:#ffd84d;color:#5a3d00;border-radius:6pt;padding:0 4pt;margin-inline-start:3pt}
.flag{border:1.5pt solid #c0262d;color:#c0262d;font-weight:700;font-size:8.5pt;padding:3pt 7pt;border-radius:3pt;float:left}
thead{display:table-header-group} tr{break-inside:avoid}
"""


def _m(a):
    if a is None:
        return ""
    cls = "neg" if a < 0 else "pos" if a > 0 else ""
    return f'<span class="{cls}">{fmt(a)}</span>'


def _signed(a):
    if a is None:
        return ""
    return ("+" if a > 0 else "") + fmt(a)


def _in(label: str) -> str:
    """'ב' + שם: 'הסימולטור' → 'בסימולטור', 'המקור' → 'במקור'."""
    return "ב" + (label[1:] if label.startswith("ה") else label)


def _why(r, label: str) -> str:
    """מאיפה הפער של היום מול הייחוס: גרירה מאתמול + תנועות שונות היום + יתרה שנרשמה לא נכון."""
    parts = []
    if r.gap_carried:
        parts.append(f"{_signed(r.gap_carried)} נגרר מיום קודם")
    if r.gap_today:
        parts.append(f"{_signed(r.gap_today)} מתנועה שסכומה שונה מ{label}")
    if r.error:
        parts.append(f"{_signed(r.error)} היתרה נרשמה לא נכון ביום הזה")
    if not parts:
        return ""
    if r.gap == 0:
        return " ועוד ".join(parts) + " — הפער נסגר"
    return " ועוד ".join(parts)


def audit_html(rep: AuditReport, title: str = "בדיקת יתרות", source_name: str = "", original_name: str = "") -> str:
    o = rep.has_original
    label = rep.reference_label
    if o:
        head_grp = '<tr class="grp"><th colspan="4"></th><th class="balgrp" colspan="5">יתרות מצטברות</th></tr>'
        head = ("<tr><th>תאריך</th><th>סוג תנועה</th><th>זכות/חובה</th><th>אסמכתה</th>"
                f'<th class="bal first">יתרה בדוח</th><th class="bal">יתרה לפי {html.escape(label)}</th>'
                '<th class="bal">פער</th><th class="bal">בדיקה</th><th class="bal">מאיפה הפער</th></tr>')
    else:
        head_grp = '<tr class="grp"><th colspan="4"></th><th class="balgrp" colspan="4">יתרות מצטברות</th></tr>'
        head = ("<tr><th>תאריך</th><th>סוג תנועה</th><th>זכות/חובה</th><th>אסמכתה</th>"
                '<th class="bal first">יתרה בדוח</th><th class="bal">יתרה מצטברת לפי התנועות</th>'
                '<th class="bal">פער</th><th class="bal">בדיקה</th></tr>')

    days: dict = {}
    for r in rep.rows:
        days.setdefault(r.date, []).append(r)
    body = []
    for d in sorted(days, reverse=True):          # כמו בדף: ימים מהחדש לישן
        for r in days[d]:
            desc = html.escape(r.description + CHANNEL_SUFFIX.get(r.channel or "", ""))
            amt = _m(r.amount)
            if r.status == "changed":
                desc += f'<span class="mark">שונה מ{html.escape(label)}</span>'
                amt += f'<span class="was">{html.escape(_in(label))} {fmt(r.orig_amount)}</span>'
            elif r.status == "added":
                desc += '<span class="mark">חדשה</span>'
            cls = " ".join(x for x in (r.status if r.status != "same" else "", "dayend" if r.day_end else "") if x)
            if r.day_end and r.stated is not None:
                if o:
                    ref = r.orig_stated
                    gap = r.gap or 0
                    check = '<td class="bal ok">✓ זהה</td>' if gap == 0 else f'<td class="bal err">✗ {_signed(gap)}</td>'
                    bal = (f'<td class="n bal first stated">{_m(r.stated)}</td><td class="n bal">{_m(ref)}</td>'
                           f'<td class="n bal">{_signed(gap) if gap else "0.00"}</td>{check}'
                           f'<td class="bal why">{html.escape(_why(r, label))}</td>')
                else:
                    gap = r.cum_error or 0
                    check = '<td class="bal ok">✓ תקין</td>' if gap == 0 else f'<td class="bal err">✗ {_signed(gap)}</td>'
                    bal = (f'<td class="n bal first stated">{_m(r.stated)}</td><td class="n bal">{_m(r.running)}</td>'
                           f'<td class="n bal">{_signed(gap) if gap else "0.00"}</td>{check}')
            else:
                bal = '<td class="bal first"></td><td class="bal"></td><td class="bal"></td><td class="bal"></td>' \
                      + ('<td class="bal"></td>' if o else "")
            body.append(f'<tr class="{cls}"><td>{r.date:%d/%m/%y}</td><td class="desc">{desc}</td>'
                        f'<td class="n amt">{amt}</td><td class="n">{html.escape(r.reference)}</td>{bal}</tr>')

    # שורת סיכום בראש הדוח
    if o:
        bad = rep.unsynced_days
        changed = [r for r in rep.rows if r.status == "changed"]
        if not bad and not changed:
            verdict = (f'<div class="verdict ok"><b>הדוח מסונכרן עם {html.escape(label)}.</b> כל {rep.days_checked} '
                       f'יתרות סוף היום זהות, ואין תנועה שסכומה שונה.</div>')
        else:
            items = [f"<li>{r.date:%d/%m/%Y} {html.escape(r.description)}: בדוח {fmt(r.amount)}, "
                     f"{html.escape(_in(label))} {fmt(r.orig_amount)} ({_signed(r.amount - r.orig_amount)})</li>" for r in changed]
            items += [f"<li>{r.date:%d/%m/%Y}: בדוח {fmt(r.stated)}, לפי {html.escape(label)} {fmt(r.orig_stated)} — "
                      f"פער {_signed(r.gap)}</li>" for r in bad]
            verdict = (f'<div class="verdict bad"><b>הדוח לא מסונכרן עם {html.escape(label)}:</b> '
                       f'{"תנועה אחת" if len(changed) == 1 else f"{len(changed)} תנועות"} בסכום שונה, ו-{"יום אחד" if len(bad) == 1 else f"{len(bad)} ימים"} שבהם היתרה המצטברת שונה.'
                       f'<ul>{"".join(items)}</ul></div>')
    else:
        bad = [r for r in rep.rows if r.day_end and r.cum_error]
        if not bad:
            verdict = (f'<div class="verdict ok"><b>אין שגיאות.</b> בכל {rep.days_checked} הימים, היתרה בדוח שווה '
                       f'לסכום המצטבר של התנועות.</div>')
        else:
            items = "".join(f"<li>{r.date:%d/%m/%Y}: בדוח {fmt(r.stated)}, לפי התנועות {fmt(r.running)} — "
                            f"פער {_signed(r.cum_error)}</li>" for r in bad)
            verdict = (f'<div class="verdict bad"><b>ב-{len(bad)} ימים היתרה בדוח לא שווה לסכום המצטבר של התנועות.</b>'
                       f'<ul>{items}</ul></div>')

    ends = [r for r in rep.rows if r.day_end and r.stated is not None]
    cards = [("יתרת פתיחה", fmt(rep.opening), rep.opening_source),
             ("ימים שנבדקו", str(rep.days_checked), ""),
             ("יתרת סגירה בדוח", fmt(rep.closing_stated), "")]
    if o:
        cards += [(f"יתרת סגירה לפי {label}", fmt(ends[-1].orig_stated) if ends else "", ""),
                  ("ימים עם פער", str(len(rep.unsynced_days)), "")]
    else:
        cards += [("יתרת סגירה לפי התנועות", fmt(rep.closing_computed), ""),
                  ("ימים עם פער", str(sum(1 for r in ends if r.cum_error)), "")]
    cards_html = "".join(f'<div class="card"><div class="k">{k}</div><div class="v">{v}</div><div class="k">{d}</div></div>'
                         for k, v, d in cards)
    files = html.escape(source_name) + (f" מול {html.escape(original_name)}" if original_name else "")
    return f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>{CSS}</style></head>
<body><div class="page">
<span class="flag">{WATERMARK}</span>
<h1>{html.escape(title)}</h1><p class="sub">{files}</p>
{verdict}<div class="cards">{cards_html}</div>
<div class="scroll"><table><thead>{head_grp}{head}</thead><tbody>{''.join(body)}</tbody></table></div>
</div></body></html>"""
