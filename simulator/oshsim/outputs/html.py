"""(ב) סימולציה בפורמט דף עו"ש, ו-(ג) דוח השוואה — HTML בעברית, RTL.

הדף המדומה נושא "סימולציה — אינו מסמך בנקאי" בכל עמוד מודפס (סימן מים קבוע +
כותרת טבלה שחוזרת בכל עמוד), בלי שם בנק, בלי לוגו ובלי מספר חשבון מלא.
"""
from __future__ import annotations

import html
import shutil
import subprocess
from collections import defaultdict
from datetime import date
from pathlib import Path

from ..engine.simulate import SimResult
from ..model.money import fmt
from ..privacy.masking import mask_account, mask_text

WATERMARK = "סימולציה — אינו מסמך בנקאי"
CHANNEL_MARK = {"direct": "(י) ", "banker": "(פ) "}

BASE_CSS = """
:root{--ink:#1d2433;--muted:#5b6475;--line:#d9dee7;--bg:#ffffff;--panel:#f5f7fa;--neg:#b42318;--pos:#1a7f37;
      --mark:#fff4d6;--wm:rgba(180,35,24,.12);--accent:#1f3a5f}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--ink:#e6e9ef;--muted:#a3abba;--line:#2f3645;
      --bg:#141820;--panel:#1c212b;--neg:#ff7b72;--pos:#56d364;--mark:#3a3220;--wm:rgba(255,123,114,.12);--accent:#8fb3e8}}
:root[data-theme="dark"]{--ink:#e6e9ef;--muted:#a3abba;--line:#2f3645;--bg:#141820;--panel:#1c212b;--neg:#ff7b72;
      --pos:#56d364;--mark:#3a3220;--wm:rgba(255,123,114,.12);--accent:#8fb3e8}
*{box-sizing:border-box}
body{margin:0;padding:24px 16px;background:var(--bg);color:var(--ink);font:14px/1.5 "Arial Hebrew",Arial,"DejaVu Sans",sans-serif}
main{max-width:980px;margin:0 auto}
h1{font-size:20px;margin:0 0 4px}
.sub{color:var(--muted);margin:0 0 16px}
.banner{border:2px solid var(--neg);color:var(--neg);font-weight:700;text-align:center;padding:8px;margin:0 0 16px;border-radius:6px}
.wm{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;pointer-events:none;z-index:5}
.wm span{transform:rotate(-28deg);font-size:clamp(28px,8vw,72px);font-weight:800;color:var(--wm);white-space:nowrap}
.scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}
th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:right;vertical-align:top}
th{background:var(--panel);font-weight:600}
td.num{text-align:left;direction:ltr;white-space:nowrap}
.neg{color:var(--neg)} .pos{color:var(--pos)}
tr.changed td{background:var(--mark)}
tr.daystart td{border-top:2px solid var(--line)}
thead tr.wmrow th{background:transparent;color:var(--neg);font-weight:700;border:0;text-align:center}
.legend{color:var(--muted);font-size:12px;margin-top:12px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:16px 0}
.card{background:var(--panel);border-radius:8px;padding:12px}
.card .k{color:var(--muted);font-size:12px} .card .v{font-size:18px;font-weight:700;direction:ltr;text-align:right}
.est{display:inline-block;background:var(--mark);border-radius:4px;padding:0 6px;font-size:12px}
svg text{fill:var(--muted);font-size:11px}
@media print{body{padding:0}.wm span{color:rgba(180,35,24,.14)} thead{display:table-header-group} tr{break-inside:avoid}}
"""


def _cls(a: int) -> str:
    return "neg" if a < 0 else "pos" if a > 0 else ""


def _page(title: str, body: str) -> str:
    return (f'<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{html.escape(title)}</title><style>{BASE_CSS}</style></head>"
            f'<body><div class="wm" aria-hidden="true"><span>{WATERMARK}</span></div><main>{body}</main></body></html>')


def statement_html(res: SimResult, account_hint: str = "", client_label: str = "") -> str:
    acct = mask_account(account_hint)
    rows_html = []
    for day in reversed(res.days):              # מהחדש לישן
        rows = list(reversed(day.rows))         # השורה הכרונולוגית האחרונה למעלה, עם היתרה
        for i, r in enumerate(rows):
            changed = r.origin != "historical"
            mark = {"modified": " ✱", "added": " ＋", "projected": " ~", "fee": " ~", "interest": " ~"}.get(r.origin, "")
            cls = " ".join(c for c in ("changed" if changed else "", "daystart" if i == 0 else "") if c)
            rows_html.append(
                f'<tr class="{cls}"><td>{r.date:%d/%m/%y}</td><td></td>'
                f"<td>{html.escape(CHANNEL_MARK.get(r.channel or '', '') + mask_text(r.description))}{mark}</td>"
                f'<td class="num {_cls(r.amount)}">{fmt(r.amount)}</td>'
                f'<td class="num {_cls(day.balance)}">{fmt(day.balance) if i == 0 else ""}</td>'
                f"<td>{html.escape(r.reference)}</td></tr>")
    period = f"{res.start:%d/%m/%Y} – {res.end:%d/%m/%Y}"
    body = f"""
<div class="banner">{WATERMARK}</div>
<h1>סימולציית תנועות בחשבון — {html.escape(res.name)}</h1>
<p class="sub">תקופה: {period}{' · חשבון ' + acct if acct else ''}{' · ' + html.escape(client_label) if client_label else ''}
{'<br><span class="est">מ-' + f'{res.projected_from:%d/%m/%Y}' + ' הקרנה — הערכה בלבד</span>' if res.projected_from else ''}</p>
<div class="scroll"><table>
<thead><tr class="wmrow"><th colspan="6">{WATERMARK}</th></tr>
<tr><th>תאריך</th><th>תאריך ערך</th><th>סוג תנועה</th><th>זכות/חובה</th><th>יתרה</th><th>אסמכתה</th></tr></thead>
<tbody>{''.join(rows_html)}</tbody></table></div>
<p class="legend">✱ סכום שונה בתרחיש · ＋ תנועה שנוספה בתרחיש · ~ חושב/הוקרן (הערכה) ·
תאריך ערך לא מופיע בדף המקור ולכן ריק · יתרת פתיחה {fmt(res.opening)} ·
מסמך זה הופק בכלי סימולציה מנתוני לקוח ואינו דף חשבון.</p>"""
    return _page(f"סימולציה — {res.name}", body)


def _chart(base: SimResult, scen: SimResult, limit: int | None) -> str:
    days = sorted(set(base.daily_balance) | set(scen.daily_balance))
    vals = [v for r in (base, scen) for v in r.daily_balance.values()] + ([-limit] if limit else []) + [0]
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    W, H, P = 900, 280, 40
    n = max(1, len(days) - 1)
    idx = {d: i for i, d in enumerate(days)}

    def xy(d, v):
        return P + idx[d] * (W - 2 * P) // n, H - P - (v - lo) * (H - 2 * P) // span

    def line(res, color, dash=""):
        pts = " ".join(f"{x},{y}" for x, y in (xy(d, v) for d, v in sorted(res.daily_balance.items())))
        return f'<polyline fill="none" stroke="{color}" stroke-width="2" {dash} points="{pts}"/>'

    zero_y = xy(days[0], 0)[1]
    parts = [f'<line x1="{P}" x2="{W - P}" y1="{zero_y}" y2="{zero_y}" stroke="var(--line)"/>',
             f'<text x="{W - P + 4}" y="{zero_y + 4}">0</text>']
    if limit:
        ly = xy(days[0], -limit)[1]
        parts.append(f'<line x1="{P}" x2="{W - P}" y1="{ly}" y2="{ly}" stroke="var(--neg)" stroke-dasharray="4 4"/>'
                     f'<text x="{P}" y="{ly - 4}">מסגרת {fmt(-limit)}</text>')
    for d in days:
        if d.day == 1:
            x = xy(d, 0)[0]
            parts.append(f'<line x1="{x}" x2="{x}" y1="{P}" y2="{H - P}" stroke="var(--line)" stroke-dasharray="2 4"/>'
                         f'<text x="{x + 3}" y="{H - P + 14}">{d:%m/%y}</text>')
    parts.append(line(base, "var(--muted)", 'stroke-dasharray="6 3"'))
    parts.append(line(scen, "var(--accent)"))
    for v in (lo, hi):
        parts.append(f'<text x="{W - P + 4}" y="{xy(days[0], v)[1] + 4}">{fmt(v)}</text>')
    return (f'<svg viewBox="0 0 {W + 60} {H}" width="100%" role="img" aria-label="יתרה יומית: בסיס מול תרחיש">'
            + "".join(parts) + "</svg>"
            '<p class="legend">— קו מלא: תרחיש · - - קו מקווקו: בסיס</p>')


def report_html(base: SimResult, scen: SimResult, limit: int | None, scenario_lines: list[str]) -> str:
    def card(k, b, s, money=True):
        f = fmt if money else (lambda x: "—" if x is None else str(x))
        diff = None if (b is None or s is None) else s - b
        return (f'<div class="card"><div class="k">{k}</div><div class="v">{f(s)}</div>'
                f'<div class="k">בסיס {f(b)} · הפרש {f(diff) if diff is not None else "—"}</div></div>')

    bmin_d, bmin = base.min_balance
    smin_d, smin = scen.min_balance
    cum = scen.closing - base.closing

    # השפעות משניות: עמלות וריבית לפי תאריך רישום
    def by_post(res, kind):
        out = defaultdict(int)
        for r in res.rows():
            if r.kind == kind:
                out[r.date] += r.amount
        return out

    sec_rows = []
    for kind, label in (("direct_channel_fee", "עמלת ערוץ ישיר"), ("interest", "ריבית")):
        b, s = by_post(base, kind), by_post(scen, kind)
        for d in sorted(set(b) | set(s)):
            sec_rows.append(f"<tr><td>{label}</td><td>{d:%d/%m/%Y}</td><td class='num'>{fmt(b.get(d, 0))}</td>"
                            f"<td class='num'>{fmt(s.get(d, 0))}</td><td class='num {_cls(s.get(d, 0) - b.get(d, 0))}'>"
                            f"{fmt(s.get(d, 0) - b.get(d, 0))}</td></tr>")
    if scen.unposted_interest or base.unposted_interest:
        sec_rows.append(f"<tr><td>ריבית שנצברה ולא נרשמה עד סוף התקופה</td><td>—</td>"
                        f"<td class='num'>{fmt(base.unposted_interest)}</td><td class='num'>{fmt(scen.unposted_interest)}</td>"
                        f"<td class='num'>{fmt(scen.unposted_interest - base.unposted_interest)}</td></tr>")

    fee_cal = "".join(
        f"<li>{c.month}: {c.observed_count} פעולות (י) בדף, מונה באסמכתה {c.reference_count if c.reference_count is not None else '—'}"
        f" — מודל {fmt(c.model_amount) if c.model_amount is not None else '—'} מול בפועל {fmt(c.actual_amount)}"
        f" {'✓' if c.ok else '✗' if c.ok is False else ''}</li>" for c in base.fee_calibration) or "<li>אין שורות עמלה</li>"
    int_cal = "".join(
        f"<li>{c.period_start:%d/%m/%Y}–{c.period_end:%d/%m/%Y}{' (תקופה חלקית בדף)' if c.partial_period else ''}: "
        f"מודל {fmt(c.model_amount)} מול בפועל {fmt(c.actual_amount)} — טעות {c.error_pct}%</li>"
        for c in base.interest_calibration) or "<li>לא בוצע — לא הוזן שיעור ריבית</li>"

    body = f"""
<div class="banner">{WATERMARK}</div>
<h1>דוח השוואה: בסיס מול "{html.escape(scen.name)}"</h1>
<p class="sub">{base.start:%d/%m/%Y} – {scen.end:%d/%m/%Y} · מצב {'Forward (הקרנה — הערכה)' if scen.mode == 'forward' else 'Replay (מה היה קורה)'}
{' · <span class="est">ריבית: הערכה</span>' if scen.interest_is_estimate else ''}</p>
<div class="cards">
{card("יתרת סגירה", base.closing, scen.closing)}
{card(f"יתרה מינימלית ({smin_d:%d/%m})", bmin, smin)}
{card("הפרש מצטבר", 0, cum)}
{card("ימים בחריגה ממסגרת", base.days_over_limit(limit), scen.days_over_limit(limit), money=False)}
{card("עלות ריבית", base.total_of("interest"), scen.total_of("interest"))}
{card("עמלות ערוץ ישיר", base.total_of("direct_channel_fee"), scen.total_of("direct_channel_fee"))}
</div>
<h2>יתרה יומית</h2>
{_chart(base, scen, limit)}
<h2>השינויים בתרחיש</h2>
<ul>{''.join(f'<li>{html.escape(l)}</li>' for l in scenario_lines) or '<li>ללא שינויים (בסיס)</li>'}</ul>
<h2>השפעות משניות</h2>
<div class="scroll"><table><thead><tr><th>רכיב</th><th>תאריך רישום</th><th>בסיס</th><th>תרחיש</th><th>הפרש</th></tr></thead>
<tbody>{''.join(sec_rows) or '<tr><td colspan="5">אין</td></tr>'}</tbody></table></div>
<h2>כיול</h2>
<p><b>עמלת ערוץ ישיר</b></p><ul>{fee_cal}</ul>
<p><b>ריבית</b></p><ul>{int_cal}</ul>
<h2>הערות והנחות</h2>
<ul>{''.join(f'<li>{html.escape(n)}</li>' for n in scen.notes) or '<li>אין</li>'}
<li>מסגרת אשראי: {fmt(limit) if limit is not None else 'לא הוזנה — ימי חריגה לא חושבו'}</li></ul>"""
    return _page(f"השוואה — {scen.name}", body)


def chromium_path() -> str | None:
    for p in ("/opt/pw-browsers/chromium-1194/chrome-linux/chrome",):
        if Path(p).exists():
            return p
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        if shutil.which(name):
            return shutil.which(name)
    found = sorted(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome")) if Path("/opt/pw-browsers").exists() else []
    return str(found[-1]) if found else None


def html_to_pdf(html_path: str | Path, pdf_path: str | Path) -> bool:
    exe = chromium_path()
    if not exe:
        return False
    subprocess.run([exe, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={Path(pdf_path).resolve()}", Path(html_path).resolve().as_uri()],
                   check=True, capture_output=True, timeout=120)
    return Path(pdf_path).exists()
