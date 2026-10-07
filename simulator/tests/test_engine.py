from datetime import date
from decimal import Decimal

import pytest

from oshsim.categorize.rules import approve, categorize, load_rules
from oshsim.engine.deltas import (AddRecurring, ChangeAmount, LoanSchedule, OneOff, RateChange, RemoveRows,
                                  Selector)
from oshsim.engine.params import DirectFeeParams, Params, RatePeriod
from oshsim.engine.simulate import Scenario, identity_mismatches
from oshsim.engine.tax import TaxModel, TaxParamsMissing
from oshsim.patterns.calendar import BusinessCalendar
from oshsim.patterns.recurring import DRIFTING, FIXED, VARIABLE
from oshsim.pipeline import CONFIG, run_scenario

SALARY = Selector(category="הכנסות", subcategory="משכורת")


def run(loaded, params, *deltas, mode="replay", months=3):
    return run_scenario(loaded.txns, loaded.report.opening_agorot, params,
                        Scenario("t", mode=mode, deltas=list(deltas), forward_months=months))


# ---------- עמלת ערוץ ישיר ----------

@pytest.mark.parametrize("count,fee", [(35, 6160), (45, 7920), (36, 6336)])
def test_direct_fee_spec_calibration(count, fee):
    """סעיף 8: 1.76 ₪ × פעולות (י) — 35→61.60, 45→79.20, 36→63.36."""
    assert Params.from_dict({"direct_channel_fee": {"rate": "1.76"}}).direct_fee.fee(count) == fee


def test_fee_calibration_on_synthetic(loaded, params):
    out = run(loaded, params)
    cal = out.base.fee_calibration
    assert len(cal) == 3 and all(c.ok for c in cal)
    # ביוני הדף מתחיל באמצע החודש — המונה באסמכתה גדול ממה שרואים
    assert cal[0].reference_count > cal[0].observed_count


# ---------- זהות ----------

@pytest.mark.parametrize("which", ["params", "params_rates"])
def test_identity_empty_scenario(loaded, which, request):
    out = run(loaded, request.getfixturevalue(which))
    assert identity_mismatches(out.scenario, loaded.txns) == []
    assert out.scenario.closing == loaded.report.closing_agorot
    assert [r.amount for r in out.scenario.rows()] == [t.amount_agorot for t in loaded.txns]


def test_identity_without_any_params(loaded):
    out = run(loaded, Params.from_dict({}))
    assert identity_mismatches(out.scenario, loaded.txns) == []


# ---------- תרחישים ----------

def test_salary_up_monotonic(loaded, params_rates):
    base = run(loaded, params_rates).scenario
    for pct in (1, 5, 10, 25):
        s = run(loaded, params_rates, ChangeAmount(SALARY, pct=Decimal(pct), label="שכר")).scenario
        assert s.closing >= base.closing
        assert all(s.daily_balance[d] >= base.daily_balance[d] for d in base.daily_balance)


def test_salary_up_exact_without_interest(loaded, params):
    out = run(loaded, params, ChangeAmount(SALARY, pct=Decimal(10), start=date(2026, 7, 1), label="שכר"))
    salaries = [t for t in loaded.txns if t.subcategory == "משכורת" and t.date >= date(2026, 7, 1)]
    assert out.scenario.closing - out.base.closing == sum(t.amount_agorot // 10 for t in salaries)


def test_higher_balance_means_less_debit_interest(loaded, params_rates):
    base = run(loaded, params_rates).scenario
    s = run(loaded, params_rates, ChangeAmount(SALARY, amount=100000, label="שכר +1000")).scenario
    assert s.total_of("interest") > base.total_of("interest")      # חיוב ריבית קטן יותר (פחות שלילי)
    # השפעה משנית: הפרש הסגירה גדול מסכום התוספת עצמה
    added = 100000 * len([t for t in loaded.txns if t.subcategory == "משכורת"])
    assert s.closing - base.closing > added


def test_rate_change(loaded, params_rates):
    base = run(loaded, params_rates).scenario
    higher = [RatePeriod(date(2026, 1, 1), Decimal("15"))]
    s = run(loaded, params_rates, RateChange(higher, label="ריבית 15%")).scenario
    assert s.total_of("interest") < base.total_of("interest")


def test_rate_change_requires_base_rate(loaded, params):
    with pytest.raises(ValueError):
        run(loaded, params, RateChange([RatePeriod(date(2026, 1, 1), Decimal("15"))], label="x"))


def test_removing_direct_rows_lowers_next_month_fee(loaded, params):
    july_direct = [t for t in loaded.txns if t.channel == "direct" and t.date.month == 7]
    out = run(loaded, params, RemoveRows(Selector(description="ביט"), date(2026, 7, 1), date(2026, 7, 31), "בלי ביט"))
    removed = [r for r in out.scenario.removed if r.channel == "direct"]
    fee_aug = [r for r in out.scenario.rows() if r.kind == "direct_channel_fee" and r.date.month == 8][0]
    base_fee = [r for r in out.base.rows() if r.kind == "direct_channel_fee" and r.date.month == 8][0]
    assert 0 < len(removed) <= len(july_direct)
    assert fee_aug.amount - base_fee.amount == 176 * len(removed)
    assert int(fee_aug.reference) == int(base_fee.reference) - len(removed)


def test_add_recurring_direct_adds_fee(loaded, params):
    out = run(loaded, params, AddRecurring("חיסכון", -50000, 12, channel="direct", label="חיסכון"))
    added = [r for r in out.scenario.rows() if r.origin == "added"]
    # 12/09 הוא שבת → 13/09 ראש השנה → 14/09, אחרי סוף הדף
    assert [r.date for r in added] == [date(2026, 7, 12), date(2026, 8, 12)]
    fees = {r.date.month: r.amount for r in out.scenario.rows() if r.kind == "direct_channel_fee"}
    base = {r.date.month: r.amount for r in out.base.rows() if r.kind == "direct_channel_fee"}
    assert fees[8] - base[8] == -176 and fees[9] - base[9] == -176


def test_one_off_and_card_note(loaded, params):
    out = run(loaded, params, OneOff(date(2026, 8, 15), 300000, "מענק", label="מענק"),
              ChangeAmount(Selector(category="כרטיסי אשראי"), pct=Decimal(-15), label="כרטיס"))
    assert any("סכום כולל" in n for n in out.scenario.notes)
    assert out.scenario.closing > out.base.closing


def test_loan_schedule_requires_client_schedule(loaded, params):
    sched = [(date(2026, 8, 20), -90000)]
    out = run(loaded, params, LoanSchedule(Selector(description="הלוואה"), date(2026, 8, 1), sched, label="מחזור"))
    rows = [r for r in out.scenario.rows() if "הלוואה" in r.description]
    assert [(r.date, r.amount) for r in rows if r.date >= date(2026, 8, 1)] == [(date(2026, 8, 20), -90000)]
    from oshsim.engine.deltas import delta_from_dict
    with pytest.raises(ValueError):
        delta_from_dict({"type": "loan_schedule", "select": {"description": "הלוואה"}, "start": "2026-08-01"}, CONFIG)


def test_warns_when_nothing_matches(loaded, params):
    out = run(loaded, params, RemoveRows(Selector(description="לא קיים"), label="ריק"))
    assert any("אין שורות" in n for n in out.scenario.notes)


def test_forward_mode(loaded, params_rates):
    out = run(loaded, params_rates, ChangeAmount(SALARY, pct=Decimal(10), label="שכר"), mode="forward", months=3)
    s = out.scenario
    assert s.projected_from == date(2026, 9, 14) and s.end == date(2026, 12, 31)
    proj = [r for r in s.rows() if r.origin == "projected"]
    assert proj and all("הערכה" in r.note for r in proj)
    assert any(r.kind == "direct_channel_fee" and r.date > date(2026, 9, 14) for r in s.rows())
    assert any(r.kind == "interest" and r.date > date(2026, 9, 14) for r in s.rows())
    assert s.closing > out.base.closing
    # ההיסטוריה עצמה עדיין זהה לבסיס עד הנקודה שבה התרחיש מתחיל
    assert out.base.daily_balance[date(2026, 6, 30)] == s.daily_balance[date(2026, 6, 30)]


# ---------- דפוסים ולוח שנה ----------

def test_patterns(loaded, params):
    pats = {p.counterparty: p for p in run(loaded, params).engine.patterns}
    salary = next(p for k, p in pats.items() if k.startswith("משכורת"))
    assert salary.kind == FIXED and salary.day_of_month == 10 and salary.friday_rule == "forward"
    mortgage = next(p for k, p in pats.items() if k.startswith("משכנתא"))
    assert mortgage.kind == DRIFTING and mortgage.friday_rule == "same"
    assert len(mortgage.amounts_by_month) == 3
    card = next(p for k, p in pats.items() if k.startswith("ישראכרט"))
    assert card.kind == VARIABLE


def test_calendar():
    cal = BusinessCalendar()
    assert cal.is_closed(date(2026, 9, 12)) and cal.is_closed(date(2026, 9, 13))   # ראש השנה
    assert cal.is_closed(date(2026, 9, 21))                                        # יום כיפור
    assert cal.first_business_day(2026, 9) == date(2026, 9, 1)
    assert cal.shift(date(2026, 9, 11), "forward", "forward") == date(2026, 9, 14)  # שישי → אחרי ר"ה
    assert cal.shift(date(2026, 9, 11), "same", "forward") == date(2026, 9, 11)
    assert cal.shift(date(2026, 9, 12), "same", "back") == date(2026, 9, 10)


# ---------- קטגוריזציה ----------

def test_categorize_and_approve(tmp_path, loaded):
    rules = load_rules(CONFIG / "rules.yaml")
    res = categorize(loaded.txns, rules)
    item = next(q for q in res.queue if "חשמל" in q.description)
    approve(item, "דיור/משכנתה", "חשבונות", tmp_path / "rules.yaml")
    res2 = categorize(loaded.txns, load_rules(CONFIG / "rules.yaml", tmp_path / "rules.yaml"))
    assert all("חשמל" not in q.description for q in res2.queue)
    assert {t.subcategory for t in loaded.txns if "חשמל" in t.description} == {"חשבונות"}


def test_external_suggester_requires_consent():
    from oshsim.categorize.rules import ExternalModelSuggester
    with pytest.raises(PermissionError):
        ExternalModelSuggester(consent=False, client=None)


# ---------- מס ----------

def test_tax_refuses_without_params(tmp_path):
    with pytest.raises(TaxParamsMissing):
        TaxModel.load(tmp_path / "2026.yaml")
    with pytest.raises(TaxParamsMissing):
        TaxModel.load(CONFIG / "tax" / "TEMPLATE.yaml")


def test_tax_with_made_up_test_params(tmp_path):
    # מספרים מומצאים לבדיקה בלבד — לא מדרגות אמיתיות
    (tmp_path / "t.yaml").write_text("""
year: 1999
source: "בדיקה — מספרים מומצאים"
income_tax_brackets_monthly: [{up_to: "1000", rate_pct: "10"}, {up_to: null, rate_pct: "20"}]
credit_point_monthly_value: "10"
default_credit_points: "2"
national_insurance_brackets_monthly: [{up_to: null, rate_pct: "1"}]
health_tax_brackets_monthly: [{up_to: null, rate_pct: "1"}]
""", encoding="utf-8")
    tm = TaxModel.load(tmp_path / "t.yaml")
    # ברוטו 2000: מס 100+200−20=280, ב"ל 20, בריאות 20 → נטו 1680
    assert tm.net(200000) == 168000


def test_interest_calibration_full_period():
    """שתי רשימות ריבית: הראשונה חלקית (הדף מתחיל באמצע), השנייה מלאה ומכוילת לאגורה."""
    from datetime import timedelta

    from oshsim.engine.simulate import Engine
    from oshsim.model.transaction import Transaction
    p = Params.from_dict({"interest": {"rates": [{"from": "2026-01-01", "debit_annual_pct": "10"}]}})
    bal = -1_000_000                       # −10,000 ₪ קבוע
    d0 = date(2026, 1, 5)
    t = [Transaction(d0, "פתיחה", 0, day_balance_agorot=bal)]
    first_post, second_post = date(2026, 2, 1), date(2026, 3, 1)
    i1 = round(Decimal(bal) * 10 / 36500 * (first_post - d0).days)
    t.append(Transaction(first_post, "ריבית חובה", int(i1), day_balance_agorot=bal + int(i1)))
    days = (second_post - first_post).days
    i2 = (Decimal(bal + int(i1)) * 10 / 36500 * days).quantize(Decimal("1"))
    t.append(Transaction(second_post, "ריבית חובה", int(i2), day_balance_agorot=bal + int(i1) + int(i2)))
    eng = Engine(t, bal, p, BusinessCalendar(), lambda x: "interest" if "ריבית" in x.description else "")
    res = eng.run(Scenario("בסיס"))
    cal = res.interest_calibration
    assert cal[0].partial_period and not cal[1].partial_period
    assert cal[1].error_pct == 0 and not res.interest_is_estimate
    assert identity_mismatches(res, t) == []
