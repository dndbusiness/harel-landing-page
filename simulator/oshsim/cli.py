"""שורת פקודה.

  python3 -m oshsim inspect  statement.pdf
  python3 -m oshsim ingest   --client data/client1 data/client1/input/*.pdf
  python3 -m oshsim review   --client data/client1 [--approve TXN_ID קטגוריה [תת-קטגוריה]]
  python3 -m oshsim patterns --client data/client1
  python3 -m oshsim simulate --client data/client1 scenarios/salary_up.yaml [--pdf]
  python3 -m oshsim purge    --client data/client1 --yes
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path

from .categorize.rules import QueueItem, approve, categorize
from .engine.params import Params
from .engine.simulate import Scenario
from .model.money import fmt
from .model.transaction import Transaction
from .privacy.workspace import Workspace
from .validate.balance import ValidationError


def _ws(args) -> Workspace:
    ws = Workspace(args.client)
    if not ws.encrypted:
        print("אזהרה: OSHSIM_KEY לא מוגדר — קבצי הלקוח נשמרים לא מוצפנים", file=sys.stderr)
    return ws


def _load(ws: Workspace):
    d = ws.read_json("ledger.json")
    return [Transaction.from_dict(t) for t in d["transactions"]], d["opening"], d.get("log", []), d.get("account_hint", "")


def _period(ws: Workspace) -> str:
    return ws.read_json("ledger.json").get("period_label", "")


def _save(ws: Workspace, txns, opening, log, hint="", period=""):
    ws.write_json("ledger.json", {"opening": opening, "transactions": [t.to_dict() for t in txns],
                                  "log": log, "account_hint": hint, "period_label": period})


def cmd_inspect(args):
    from .ingest.mizrahi import MizrahiOshParser
    print(MizrahiOshParser().inspect(args.file, args.rows))


def cmd_ingest(args):
    from .pipeline import ingest
    ws = _ws(args)
    for f in args.files:
        ws.log("ingest", Path(f).name)
    try:
        loaded = ingest(args.files, Path(args.client))
    except ValidationError as e:
        print("הדף לא מתיישב — עצירה.\n" + str(e), file=sys.stderr)
        return 2
    _save(ws, loaded.txns, loaded.report.opening_agorot, loaded.log, loaded.account_hint, loaded.period_label)
    ws.write_json("queue.json", [asdict(q) for q in loaded.queue])
    print("\n".join(loaded.log))
    if loaded.queue:
        print(f"\n{len(loaded.queue)} תנועות ממתינות לאישור: python3 -m oshsim review --client {args.client}")
    return 0


def cmd_review(args):
    from .pipeline import rules_for
    ws = _ws(args)
    queue = [QueueItem(**q) for q in ws.read_json("queue.json")]
    if args.approve:
        txn_id, cat, *sub = args.approve
        item = next((q for q in queue if q.txn_id == txn_id), None)
        if not item:
            print(f"אין בתור תנועה {txn_id}", file=sys.stderr)
            return 1
        rule = approve(item, cat, sub[0] if sub else "", Path(args.client) / "rules.yaml")
        print(f"נשמר כלל {rule.id}: '{rule.description}' → {cat}")
        txns, opening, log, hint = _load(ws)
        res = categorize(txns, rules_for(Path(args.client)))
        _save(ws, txns, opening, log, hint, _period(ws))
        ws.write_json("queue.json", [asdict(q) for q in res.queue])
        queue = res.queue
    for q in queue:
        print(f"{q.txn_id}  {q.date}  {fmt(q.amount_agorot):>12}  {q.description}  →  הצעה: {q.suggested_category}"
              f"{'/' + q.suggested_subcategory if q.suggested_subcategory else ''} ({q.reason})")
    if not queue:
        print("התור ריק")
    return 0


def cmd_patterns(args):
    from .categorize.rules import rule_kind
    from .patterns.recurring import KIND_HE, detect, save_patterns
    from .pipeline import calendar_for, rules_for
    ws = _ws(args)
    txns, *_ = _load(ws)
    rules = rules_for(Path(args.client))
    pats = detect(txns, calendar_for(Path(args.client)), {"direct_channel_fee", "interest"}, lambda t: rule_kind(t, rules))
    save_patterns(pats, Path(args.client) / "patterns.yaml")
    for p in pats:
        if p.kind != "one_off":
            print(f"{p.id} {KIND_HE[p.kind]:<6} יום {p.day_of_month:>2}  {fmt(p.typical_amount):>12}  {p.counterparty}"
                  f"  [שישי: {p.friday_rule}, שבת/חג: {p.closed_rule}{'' if p.rule_learned else ' — ברירת מחדל'}]")
    print(f"\nנשמר ב-{Path(args.client) / 'patterns.yaml'} — לאישור היועץ")
    return 0


def cmd_simulate(args):
    from .outputs.excel import verify_with_libreoffice, write_excel
    from .outputs.compare import compare_html
    from .outputs.replica import replica_html
    from .outputs.html import html_to_pdf, report_html, statement_html
    from .pipeline import run_scenario
    ws = _ws(args)
    txns, opening, log, hint = _load(ws)
    params_path = Path(args.client) / "params.yaml"
    if not params_path.exists():
        print(f"חסר {params_path} — העתיקו מ-config/params.example.yaml ומלאו", file=sys.stderr)
        return 1
    params = Params.load(params_path)
    scenario = Scenario.load(args.scenario)
    tax = Path(args.tax) if args.tax else None
    out = run_scenario(txns, opening, params, scenario, Path(args.client), tax)
    od = Path(args.out or Path(args.client) / "out")
    od.mkdir(parents=True, exist_ok=True)
    slug = Path(args.scenario).stem

    log = log + ["בדיקת זהות: תרחיש ריק משחזר את הדף לאגורה ✓"]
    xlsx = od / f"{slug}.xlsx"
    check = write_excel(xlsx, txns, out.base, out.scenario, out.engine.patterns, params.table_rows(), log,
                        out.scenario_lines, params.credit_limit_agorot)
    problems = verify_with_libreoffice(xlsx, check) if not args.no_recalc else ["חישוב מחדש דולג (--no-recalc)"]
    st = od / f"{slug}_statement.html"
    st.write_text(statement_html(out.scenario, hint), encoding="utf-8")
    rpl = od / f"{slug}_replica.html"
    rpl.write_text(replica_html(txns, opening, out.scenario, hint, _period(ws)), encoding="utf-8")
    cp = od / f"{slug}_compare.html"
    cp.write_text(compare_html(txns, opening, out.scenario, hint), encoding="utf-8")
    rp = od / f"{slug}_report.html"
    rp.write_text(report_html(out.base, out.scenario, params.credit_limit_agorot, out.scenario_lines), encoding="utf-8")
    for p in (xlsx, st, rpl, cp, rp):
        ws.log("write", p.name)
    if args.pdf:
        for src, name in ((st, f"{slug}_statement.pdf"), (rpl, f"{slug}_replica.pdf"), (cp, f"{slug}_compare.pdf")):
            if html_to_pdf(src, od / name):
                ws.log("write", name)

    b, s = out.base, out.scenario
    print(f"תרחיש: {s.name} ({s.mode})")
    print(f"יתרת סגירה: בסיס {fmt(b.closing)} → תרחיש {fmt(s.closing)} (הפרש {fmt(s.closing - b.closing)})")
    print(f"יתרה מינימלית: בסיס {fmt(b.min_balance[1])} → תרחיש {fmt(s.min_balance[1])}")
    for n in s.notes:
        print("הערה:", n)
    if problems:
        print("\nבדיקת Excel:", *problems, sep="\n  ")
    else:
        print("בדיקת Excel: חישוב מחדש ב-LibreOffice זהה לחישוב בקוד ✓")
    print(f"\nפלטים ב-{od}")
    return 0 if not problems or args.no_recalc else 3


def cmd_audit(args):
    from .ingest.merge import load_statement
    from .outputs.audit_html import _in, audit_html
    from .outputs.html import html_to_pdf
    from .validate.audit import audit, reference_from_simulation
    st = load_statement(args.file)
    ref, label, ref_name = None, "המקור", ""
    if args.scenario:
        # הייחוס: מה שהסימולטור מחשב לתרחיש, על נתוני הלקוח
        from .pipeline import run_scenario
        if not args.client:
            print("--scenario דורש --client", file=sys.stderr)
            return 1
        ws = _ws(args)
        txns, opening, _log, _hint = _load(ws)
        scen = Scenario.load(args.scenario)
        out = run_scenario(txns, opening, Params.load(Path(args.client) / "params.yaml"), scen, Path(args.client))
        ref, label, ref_name = reference_from_simulation(out.scenario, txns[-1].date), "הסימולטור", f"הסימולטור ({scen.name})"
    elif args.original:
        ref, ref_name = load_statement(args.original).transactions, Path(args.original).name
    rep = audit(st.transactions, ref, label)
    out_path = Path(args.out or Path(args.file).with_name(Path(args.file).stem + "_audit.html"))
    out_path.write_text(audit_html(rep, source_name=Path(args.file).name, original_name=ref_name), encoding="utf-8")
    if args.pdf:
        html_to_pdf(out_path, out_path.with_suffix(".pdf"))
    print(f"{len(st.transactions)} תנועות, {rep.days_checked} ימים עם יתרה בדוח")
    if rep.has_original:
        changed = [r for r in rep.rows if r.status == "changed"]
        for r in changed:
            print(f"תנועה שונה {r.date:%d/%m} {r.description}: בדוח {fmt(r.amount)}, {_in(label)} {fmt(r.orig_amount)}")
        for r in rep.unsynced_days:
            print(f"פער {r.date:%d/%m}: בדוח {fmt(r.stated)}, לפי {label} {fmt(r.orig_stated)}, פער {fmt(r.gap)}")
        if not changed and not rep.unsynced_days:
            print(f"מסונכרן: כל היתרות זהות ל{label}")
    else:
        bad = [r for r in rep.rows if r.day_end and r.cum_error]
        for r in bad:
            print(f"פער {r.date:%d/%m}: בדוח {fmt(r.stated)}, לפי התנועות {fmt(r.running)}, פער {fmt(r.cum_error)}")
        if not bad:
            print("אין שגיאות: כל יתרה שווה לסכום המצטבר של התנועות")
    print(f"דוח: {out_path}")
    return 0 if (rep.ok and not rep.unsynced_days) else 4


def cmd_purge(args):
    if not args.yes:
        print("מחיקה בלתי הפיכה של כל קבצי הלקוח. הוסיפו --yes לאישור.", file=sys.stderr)
        return 1
    n = Workspace(args.client).purge()
    print(f"נמחקו {n} קבצים")
    return 0


def cmd_keygen(args):
    from .privacy.workspace import generate_key
    print(generate_key())
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="oshsim", description="סימולציה לדפי עו\"ש — כלי ליועץ פיננסי")
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("inspect", help="הצגת המילים והעמודות שנשלפו מ-PDF")
    p.add_argument("file"); p.add_argument("--rows", type=int, default=40); p.set_defaults(fn=cmd_inspect)

    p = sp.add_parser("ingest", help="קליטה, איחוד, ולידציה וקטגוריזציה")
    p.add_argument("--client", required=True); p.add_argument("files", nargs="+"); p.set_defaults(fn=cmd_ingest)

    p = sp.add_parser("review", help="תור אישור קטגוריות")
    p.add_argument("--client", required=True)
    p.add_argument("--approve", nargs="+", metavar=("TXN_ID", "CATEGORY"))
    p.set_defaults(fn=cmd_review)

    p = sp.add_parser("patterns", help="זיהוי תנועות קבועות וכללי תאריך")
    p.add_argument("--client", required=True); p.set_defaults(fn=cmd_patterns)

    p = sp.add_parser("simulate", help="הרצת תרחיש והפקת פלטים")
    p.add_argument("--client", required=True); p.add_argument("scenario")
    p.add_argument("--out"); p.add_argument("--tax", help="קובץ מס שנתי (לשינוי בברוטו)")
    p.add_argument("--pdf", action="store_true", help="גם PDF של הדף המדומה (דורש Chromium)")
    p.add_argument("--no-recalc", action="store_true")
    p.set_defaults(fn=cmd_simulate)

    p = sp.add_parser("audit", help="בדיקת יתרות בדף (וגם פירוק הפער מול דף מקורי)")
    p.add_argument("file"); p.add_argument("--original", help="דף ייחוס (למשל הדף המקורי)")
    p.add_argument("--client", help="תיקיית הלקוח (עם --scenario)")
    p.add_argument("--scenario", help="תרחיש: בודקים את הדוח מול מה שהסימולטור מחשב לו")
    p.add_argument("--out"); p.add_argument("--pdf", action="store_true")
    p.set_defaults(fn=cmd_audit)

    p = sp.add_parser("purge", help="מחיקה מסודרת של תיקיית לקוח")
    p.add_argument("--client", required=True); p.add_argument("--yes", action="store_true"); p.set_defaults(fn=cmd_purge)

    p = sp.add_parser("keygen", help="יצירת מפתח הצפנה (שומרים מחוץ לתיקיית הלקוח)")
    p.set_defaults(fn=cmd_keygen)

    args = ap.parse_args(argv)
    return args.fn(args) or 0


if __name__ == "__main__":
    sys.exit(main())
