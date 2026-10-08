"""דוח בדיקת יתרות — באותה פריסה של דף הבנק, עם גוש היתרות המצטברות מודגש בצד שמאל."""
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
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin:0 0 10pt}
.card{border:1px solid #dfe3e3;border-radius:6px;padding:7px 9px}
.card .k{font-size:8pt;color:#666}.card .v{font-size:12pt;direction:ltr;text-align:right;font-variant-numeric:tabular-nums}
.explain{font-size:9.5pt;margin:0 0 10pt;padding:8px 12px;background:#f4f7f7;border-radius:6px}
.explain ul{margin:4pt 0 0;padding-inline-start:16pt}
.explain li{margin:2pt 0}
.scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:8.6pt}
th,td{padding:3.5pt 5pt;border-bottom:.6pt solid #e3e6e6;text-align:right;white-space:nowrap;vertical-align:middle}
td.desc{white-space:normal;min-width:110pt}
thead tr:not(.grp) th{white-space:normal;line-height:1.15}
thead th{background:#eaecec;font-weight:700}
thead tr.grp th{font-size:9.5pt;text-align:center;border-bottom:0}
.n{direction:ltr;unicode-bidi:isolate;text-align:left;font-variant-numeric:tabular-nums}
.neg{color:#e0303f}.pos{color:#16a35f}
/* גוש היתרות המצטברות — צד שמאל */
thead th.balgrp{background:#1f4e79;color:#fff;border-inline-start:2pt solid #1f4e79}
th.bal,td.bal{background:#eaf2fb}
td.bal.first{border-inline-start:2pt solid #1f4e79}
th.bal.first{border-inline-start:2pt solid #1f4e79}
td.run{color:#7a8a99}
tr.dayend td{border-bottom:1.4pt solid #b9c3c3}
tr.dayend td.stated{font-weight:700}
td.ok{color:#16a35f;font-weight:700}
td.err{background:#ffd6d2;color:#b3121b;font-weight:700}
/* פער מול המקור */
thead th.gapgrp{background:#7a5200;color:#fff;border-inline-start:2pt solid #7a5200}
th.gap,td.gap{background:#fff8e6}
td.gap.first,th.gap.first{border-inline-start:2pt solid #7a5200}
tr.changed td.amt{background:#fff1b8;font-weight:700}
tr.added td{background:#dff3ea}
.was{font-size:7.5pt;color:#666;display:block}
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


def audit_html(rep: AuditReport, title: str = "בדיקת יתרות", source_name: str = "", original_name: str = "") -> str:
    o = rep.has_original
    head_grp = ('<tr class="grp"><th colspan="4"></th>'
                + ('<th class="gapgrp" colspan="3">פער מול הדף המקורי</th>' if o else "")
                + '<th class="balgrp" colspan="4">יתרות מצטברות</th></tr>')
    head = ("<tr><th>תאריך</th><th>סוג תנועה</th><th>זכות/חובה</th><th>אסמכתה</th>"
            + ('<th class="gap first">מועבר מימים קודמים</th><th class="gap">משינויי היום</th><th class="gap">סה"כ פער</th>' if o else "")
            + '<th class="bal first">יתרה רצה (חישוב)</th><th class="bal">יתרה בדף</th>'
              '<th class="bal">צפוי (קודמת + היום)</th><th class="bal">בדיקה</th></tr>')

    days: dict = {}
    for r in rep.rows:
        days.setdefault(r.date, []).append(r)
    body = []
    for d in sorted(days, reverse=True):          # כמו בדף: ימים מהחדש לישן
        for r in days[d]:
            desc = html.escape(r.description + CHANNEL_SUFFIX.get(r.channel or "", ""))
            amt = _m(r.amount)
            if r.status == "changed":
                desc += '<span class="mark">שונה</span>'
                amt += f'<span class="was">במקור {fmt(r.orig_amount)}</span>'
            elif r.status == "added":
                desc += '<span class="mark">חדשה</span>'
            cls = " ".join(x for x in (r.status if r.status != "same" else "", "dayend" if r.day_end else "") if x)
            gap_cells = ""
            if o:
                if r.day_end:
                    gap_cells = (f'<td class="n gap first">{_signed(r.gap_carried)}</td>'
                                 f'<td class="n gap">{_signed(r.gap_today)}</td>'
                                 f'<td class="n gap"><b>{_signed(r.gap) if r.gap is not None else ""}</b></td>')
                else:
                    gap_cells = '<td class="gap first"></td><td class="gap"></td><td class="gap"></td>'
            if r.day_end and r.stated is not None:
                check = ('<td class="ok">✓ תקין</td>' if r.error == 0 else
                         f'<td class="err">✗ פער {_signed(r.error)}</td>')
                bal_cells = (f'<td class="n bal first run">{fmt(r.running)}</td>'
                             f'<td class="n bal stated">{_m(r.stated)}</td>'
                             f'<td class="n bal">{fmt(r.expected_day)}</td>{check}')
            else:
                bal_cells = (f'<td class="n bal first run">{fmt(r.running)}</td><td class="bal"></td>'
                             '<td class="bal"></td><td class="bal"></td>')
            body.append(f'<tr class="{cls}"><td>{r.date:%d/%m/%y}</td><td class="desc">{desc}</td>'
                        f'<td class="n amt">{amt}</td><td class="n">{html.escape(r.reference)}</td>'
                        f"{gap_cells}{bal_cells}</tr>")

    if rep.ok:
        verdict = (f'<div class="verdict ok"><b>אין שגיאות חישוב.</b> בכל {rep.days_checked} הימים, היתרה בדף שווה '
                   f'ליתרה של היום הקודם ועוד התנועות של היום.</div>')
    else:
        lst = "".join(f"<li>{r.date:%d/%m/%Y}: בדף {fmt(r.stated)}, צפוי {fmt(r.expected_day)} — פער {_signed(r.error)}</li>"
                      for r in rep.errors)
        verdict = (f'<div class="verdict bad"><b>נמצאו {len(rep.errors)} ימים שבהם היתרה בדף לא מתיישבת עם התנועות.</b>'
                   f'<ul>{lst}</ul></div>')

    explain = ""
    if o:
        lines = []
        ends = [r for r in rep.rows if r.day_end and r.gap is not None]
        i = 0
        while i < len(ends):
            r = ends[i]
            if not (r.gap or r.gap_today or r.gap_carried or r.error):
                i += 1
                continue
            if r.gap_today == 0 and not r.error and r.gap:
                # ימים רצופים שבהם הפער רק עובר הלאה — שורה אחת לטווח
                j = i
                while j + 1 < len(ends) and ends[j + 1].gap_today == 0 and not ends[j + 1].error \
                        and ends[j + 1].gap == r.gap:
                    j += 1
                rng = f"{r.date:%d/%m}" if j == i else f"{r.date:%d/%m}–{ends[j].date:%d/%m}"
                lines.append(f'<li><b>{rng}</b>: הפער {_signed(r.gap)} נמשך מימים קודמים, '
                             f'בלי שינוי בתנועות ({"יום אחד" if j == i else f"{j - i + 1} ימים"})</li>')
                i = j + 1
                continue
            parts = []
            if r.gap_carried:
                parts.append(f"{_signed(r.gap_carried)} שהועברו מימים קודמים")
            if r.gap_today:
                parts.append(f"{_signed(r.gap_today)} משינויי היום")
            if r.error:
                parts.append(f"{_signed(r.error)} שגיאת חישוב")
            closed = " — הפער נסגר" if r.gap == 0 and (r.gap_carried or r.gap_today) else ""
            lines.append(f"<li><b>{r.date:%d/%m}</b>: פער {_signed(r.gap) if r.gap else '0.00'} = "
                         f"{' ועוד '.join(parts)}{closed}</li>")
            i += 1
        n_changed = sum(r.status == "changed" for r in rep.rows)
        explain = (f'<div class="explain"><b>למה היתרה שונה מהמקור?</b> {n_changed} תנועות שונו. פער שנפתח ביום מסוים '
                   f'ממשיך לכל הימים שאחריו, עד שתנועה אחרת מקזזת אותו.'
                   f'<ul>{"".join(lines) or "<li>אין פער מול המקור באף יום</li>"}</ul></div>')

    cards = [("יתרת פתיחה", fmt(rep.opening), rep.opening_source),
             ("ימים שנבדקו", str(rep.days_checked), ""),
             ("ימים עם שגיאת חישוב", str(len(rep.errors)), ""),
             ("יתרת סגירה בדף", fmt(rep.closing_stated), ""),
             ("יתרת סגירה מחושבת", fmt(rep.closing_computed), "")]
    cards_html = "".join(f'<div class="card"><div class="k">{k}</div><div class="v">{v}</div><div class="k">{d}</div></div>'
                         for k, v, d in cards)
    files = html.escape(source_name) + (f" מול המקור {html.escape(original_name)}" if original_name else "")
    return f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>{CSS}</style></head>
<body><div class="page">
<span class="flag">{WATERMARK}</span>
<h1>{html.escape(title)}</h1><p class="sub">{files}</p>
{verdict}<div class="cards">{cards_html}</div>{explain}
<div class="scroll"><table><thead>{head_grp}{head}</thead><tbody>{''.join(body)}</tbody></table></div>
</div></body></html>"""
