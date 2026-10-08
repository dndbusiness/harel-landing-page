import copy

from oshsim.ingest.csv_adapter import parse_csv
from oshsim.outputs.audit_html import audit_html
from oshsim.validate.audit import audit


def test_clean_statement_has_no_errors(synthetic):
    rep = audit(parse_csv(synthetic["csv"]).transactions)
    assert rep.ok and rep.days_checked > 40
    assert rep.closing_computed == rep.closing_stated == synthetic["closing"]


def test_wrong_balance_is_caught_on_its_day(synthetic):
    txns = copy.deepcopy(parse_csv(synthetic["csv"]).transactions)
    rows = [t for t in txns if t.day_balance_agorot is not None]
    bad = rows[20]
    bad.day_balance_agorot += 10000                    # יתרה שגויה ב-100 ₪ ביום אחד
    rep = audit(txns)
    assert [r.date for r in rep.errors] == [bad.date, rows[21].date]
    assert rep.errors[0].error == 10000 and rep.errors[1].error == -10000
    assert "✗" in audit_html(rep)


def test_gap_vs_original_splits_into_carried_and_today(synthetic):
    orig = parse_csv(synthetic["csv"]).transactions
    new = copy.deepcopy(orig)
    sal = [t for t in new if "משכורת" in t.description]
    sal[0].amount_agorot += 50000                      # +500 ₪ במשכורת הראשונה
    run = None
    for t in new:                                      # מעדכנים את יתרות הדף כמו שסימולציה הייתה עושה
        if t.date >= sal[0].date and t.day_balance_agorot is not None:
            t.day_balance_agorot += 50000
    rep = audit(new, orig)
    assert rep.ok
    days = [r for r in rep.rows if r.day_end and r.gap is not None]
    first = next(r for r in days if r.gap)
    assert first.date == sal[0].date and first.gap_today == 50000 and first.gap_carried == 0
    later = [r for r in days if r.date > sal[0].date]
    assert all(r.gap == 50000 and r.gap_carried == 50000 and r.gap_today == 0 for r in later)
    h = audit_html(rep)
    assert "יתרות מצטברות" in h and "נגרר מיום קודם" in h


def test_report_vs_simulator_reference(loaded, params):
    """הדוח נבדק מול מה שהסימולטור חישב: תנועה ששונתה ויתרה שנרשמה לא נכון מסומנות."""
    from decimal import Decimal

    from oshsim.engine.deltas import ChangeAmount, Selector
    from oshsim.engine.simulate import Scenario
    from oshsim.pipeline import run_scenario
    from oshsim.validate.audit import reference_from_simulation
    sc = Scenario("שכר", deltas=[ChangeAmount(Selector(subcategory="משכורת"), pct=Decimal(10), label="x")])
    out = run_scenario(loaded.txns, loaded.report.opening_agorot, params, sc)
    ref = reference_from_simulation(out.scenario, loaded.txns[-1].date)
    assert audit(copy.deepcopy(ref), ref, "הסימולטור").unsynced_days == []      # הסימולטור מול עצמו
    report = copy.deepcopy(ref)
    days = [t for t in report if t.day_balance_agorot is not None]
    days[10].day_balance_agorot += 5000                                          # יתרה אחת שנרשמה לא נכון
    rep = audit(report, ref, "הסימולטור")
    assert [r.date for r in rep.unsynced_days] == [days[10].date]
    assert "לפי הסימולטור" in audit_html(rep)


def test_annotate_marks_wrong_balance_on_pdf(tmp_path, synthetic):
    import pdfplumber

    from oshsim.ingest.mizrahi import MizrahiOshParser
    from oshsim.outputs.annotate import annotate_pdf
    rep = audit(MizrahiOshParser().parse(synthetic["pdf"]).transactions)
    assert annotate_pdf(synthetic["pdf"], rep, tmp_path / "clean.pdf") == 0
    day = [r for r in rep.rows if r.day_end][5]
    day.stated += 10000                                  # כאילו בדוח נרשמה יתרה שגויה
    assert annotate_pdf(synthetic["pdf"], rep, tmp_path / "m.pdf") == 1
    with pdfplumber.open(tmp_path / "m.pdf") as p:
        assert len(p.pages) == len(pdfplumber.open(synthetic["pdf"]).pages)
        assert sum(len(pg.rects) for pg in p.pages) >= 1
