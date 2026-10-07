import ast
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from oshsim.model.money import MoneyParseError, fmt, from_decimal, parse_amount, scale
from oshsim.model.transaction import Transaction
from oshsim.validate.balance import ValidationError, validate

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("text,expected", [
    ("1,234.56", 123456), ("-1,234.56", -123456), ("1,234.56-", -123456), ("−1,234.56", -123456),
    ("400", 40000), ("0.5", 50), ("₪ 12.30", 1230), ("-35,189.68", -3518968),
])
def test_parse_amount(text, expected):
    assert parse_amount(text) == expected


@pytest.mark.parametrize("bad", ["", "abc", "-12-", "1.234,56", "12.345"])
def test_parse_amount_rejects(bad):
    with pytest.raises(MoneyParseError):
        parse_amount(bad)


def test_rounding_and_float_guard():
    assert scale(1001, Decimal("0.5")) == 501          # חצי למעלה
    assert from_decimal("61.60") == 6160
    assert fmt(-4554299) == "-45,542.99"
    with pytest.raises(TypeError):
        from_decimal(61.6)
    with pytest.raises(TypeError):
        Transaction(date(2026, 1, 1), "x", 1.5)


MONEY_PACKAGES = ["model", "validate", "ingest", "engine", "categorize", "patterns"]


def test_no_float_in_money_path():
    """אין ליטרל float ואין קריאה ל-float() במסלול הכסף (מותר רק isinstance(x, float) כשומר)."""
    offenders = []
    for pkg in MONEY_PACKAGES:
        for f in (ROOT / "oshsim" / pkg).rglob("*.py"):
            tree = ast.parse(f.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, float):
                    offenders.append(f"{f.name}:{node.lineno} ליטרל {node.value}")
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "float":
                    offenders.append(f"{f.name}:{node.lineno} float()")
    # ROW_TOLERANCE בפרסר הוא קואורדינטה בעמוד, לא כסף
    offenders = [o for o in offenders if not o.startswith("mizrahi.py") or "float()" in o]
    assert not offenders, offenders


def _t(d, amount, bal=None, desc="x"):
    return Transaction(d, desc, amount, day_balance_agorot=bal)


def test_opening_derived_like_spec_example():
    # סעיף 5: סגירה 18/06 היא −35,189.68 והתנועה באותו יום +400 → פתיחה −35,589.68
    rep = validate([_t(date(2026, 6, 18), 40000, -3518968)])
    assert rep.opening_agorot == -3558968 and rep.ok


def test_gap_stops_with_report():
    txns = [_t(date(2026, 6, 18), 40000, -3518968),
            _t(date(2026, 6, 19), -10000),
            _t(date(2026, 6, 19), -5000, -3533968),     # צפוי −35,339.68
            _t(date(2026, 6, 21), 100, -3533968)]
    txns[2].day_balance_agorot = -3534068               # פער של 1.00 ₪
    with pytest.raises(ValidationError) as e:
        validate(txns)
    gap = e.value.report.gaps[0]
    assert (gap.day, gap.expected, gap.actual, gap.diff) == (date(2026, 6, 19), -3533968, -3534068, -100)
    # אחרי הפער ממשיכים מהיתרה בדף — היום הבא נבדק בנפרד ונמצא תקין
    assert len(e.value.report.gaps) == 1


def test_last_day_without_balance_is_error():
    with pytest.raises(ValidationError):
        validate([_t(date(2026, 6, 18), 100, 100), _t(date(2026, 6, 19), 100)])


def test_synthetic_validates(loaded, synthetic):
    assert loaded.report.ok
    assert loaded.report.opening_agorot == synthetic["opening"]
    assert loaded.report.closing_agorot == synthetic["closing"]
