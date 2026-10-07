import csv
from datetime import date

import pytest

from oshsim.ingest.common import ParseError, split_channel
from oshsim.ingest.csv_adapter import parse_csv
from oshsim.ingest.hebrew import visual_to_logical
from oshsim.ingest.merge import load_statement, merge_statements
from oshsim.ingest.mizrahi import MizrahiOshParser
from oshsim.validate.balance import validate


def test_visual_to_logical():
    assert visual_to_logical("תרוכשמ (י)") == "(י) משכורת"
    assert visual_to_logical(visual_to_logical("(י) העברה 4471")) == "(י) העברה 4471"
    assert visual_to_logical("4471 האוולה") == "הלוואה 4471"
    assert visual_to_logical("-1,234.56") == "-1,234.56"
    assert split_channel("(פ) משיכת מזומן") == ("משיכת מזומן", "banker")


def test_pdf_matches_csv(synthetic):
    """ה-PDF הסינתטי נכתב בעברית חזותית (הפוכה) — המפרק חייב להחזיר בדיוק את מה שב-CSV."""
    pdf = MizrahiOshParser().parse(synthetic["pdf"])
    ref = parse_csv(synthetic["csv"])
    key = lambda t: (t.date, t.description, t.amount_agorot, t.reference, t.channel, t.day_balance_agorot)  # noqa
    assert [key(t) for t in pdf.transactions] == [key(t) for t in ref.transactions]
    assert all(t.page and t.raw_row and t.source_file == "synthetic.pdf" for t in pdf.transactions)
    assert validate(pdf.transactions).ok


def test_pdf_without_table(tmp_path):
    from reportlab.pdfgen import canvas
    p = tmp_path / "empty.pdf"
    c = canvas.Canvas(str(p)); c.drawString(100, 700, "no table here"); c.showPage(); c.save()
    with pytest.raises(ParseError):
        MizrahiOshParser().parse(p)


def test_not_a_pdf(tmp_path):
    p = tmp_path / "broken.pdf"
    p.write_bytes(b"%PDF-1.4 truncated")
    with pytest.raises(Exception):
        MizrahiOshParser().parse(p)


def test_corrupt_amount_is_reported(tmp_path, synthetic):
    rows = list(csv.reader(synthetic["csv"].open(encoding="utf-8")))
    rows[5][3] = "12,34x"
    p = tmp_path / "bad.csv"
    csv.writer(p.open("w", encoding="utf-8", newline="")).writerows(rows)
    with pytest.raises(ParseError, match="שורה 6"):
        parse_csv(p)


def test_missing_row_fails_validation(tmp_path, synthetic):
    rows = list(csv.reader(synthetic["csv"].open(encoding="utf-8")))
    # מוחקים שורה שאין בה יתרה — היתרה של אותו יום כבר לא תתיישב
    idx = next(i for i, r in enumerate(rows[1:], 1) if not r[4])
    del rows[idx]
    p = tmp_path / "missing.csv"
    csv.writer(p.open("w", encoding="utf-8", newline="")).writerows(rows)
    rep = validate(parse_csv(p).transactions, raise_on_fail=False)
    assert not rep.ok and len(rep.gaps) == 1


def test_overlapping_files_merge(tmp_path, synthetic):
    rows = list(csv.reader(synthetic["csv"].open(encoding="utf-8")))
    header, body = rows[0], rows[1:]          # מהחדש לישן
    # חיתוך לפי ימים: הקובץ הראשון עד 31/07, השני מ-01/07 (חפיפה של חודש)
    d = lambda r: date(int(r[0][6:]), int(r[0][3:5]), int(r[0][:2]))  # noqa
    a = [r for r in body if d(r) <= date(2026, 7, 31)]
    b = [r for r in body if d(r) >= date(2026, 7, 1)]
    for name, part in (("a.csv", a), ("b.csv", b)):
        csv.writer((tmp_path / name).open("w", encoding="utf-8", newline="")).writerows([header] + part)
    m = merge_statements([load_statement(tmp_path / "b.csv"), load_statement(tmp_path / "a.csv")])
    full = parse_csv(synthetic["csv"]).transactions
    assert not m.issues
    assert [t.identity_key() for t in m.transactions] == [t.identity_key() for t in full]
    assert m.duplicates_dropped == len([r for r in body if date(2026, 7, 1) <= d(r) <= date(2026, 7, 31)])
    # שתי העברות זהות באותו יום נשמרו שתיהן
    same = [t for t in m.transactions if t.date == date(2026, 7, 6) and t.reference == "55555"]
    assert len(same) == 2
    assert validate(m.transactions).ok


def test_balance_row_is_last_of_its_day(synthetic):
    """בדף היתרה בשורה האחרונה של כל יום; אחרי ההמרה לכרונולוגי היא חייבת להישאר אחרונה ביומה."""
    for st in (MizrahiOshParser().parse(synthetic["pdf"]), parse_csv(synthetic["csv"])):
        txns = st.transactions
        for i, t in enumerate(txns):
            if t.day_balance_agorot is not None:
                assert i + 1 == len(txns) or txns[i + 1].date != t.date
