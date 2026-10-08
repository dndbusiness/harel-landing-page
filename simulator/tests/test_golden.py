"""Golden test על הדף האמיתי (מזרחי טפחות, 18/06/26–14/09/26) — סעיף 10.

הדף עצמו הוא נתוני לקוח ולכן לא נשמר במאגר. מריצים עם:
    OSHSIM_GOLDEN_PDF=/path/to/statement.pdf python3 -m pytest tests/test_golden.py
"""
import os
from datetime import date
from pathlib import Path

import pytest

from oshsim.engine.params import Params
from oshsim.engine.simulate import Scenario, identity_mismatches
from oshsim.pipeline import ingest, run_scenario

PDF = os.environ.get("OSHSIM_GOLDEN_PDF")
pytestmark = pytest.mark.skipif(not PDF or not Path(PDF).exists(), reason="OSHSIM_GOLDEN_PDF לא הוגדר")


@pytest.fixture(scope="module")
def real():
    return ingest([PDF])


def test_balances(real):
    assert real.report.ok
    assert real.report.opening_agorot == -3558968            # −35,589.68
    assert real.report.closing_agorot == -4554299            # −45,542.99 ב-14/09
    bal = {t.date: t.day_balance_agorot for t in real.txns if t.day_balance_agorot is not None}
    assert bal[date(2026, 9, 14)] == -4554299
    assert bal[date(2026, 8, 10)] == -2343520                # −23,435.20
    assert bal[date(2026, 9, 1)] == -1375460                 # −13,754.60


def test_direct_fee_rows(real):
    out = run_scenario(real.txns, real.report.opening_agorot,
                       Params.from_dict({"direct_channel_fee": {"rate": "1.76"}}), Scenario("בסיס"))
    cal = out.base.fee_calibration
    assert [(c.reference_count, -c.actual_amount) for c in cal] == [(35, 6160), (45, 7920), (36, 6336)]
    assert all(c.ok for c in cal)
    assert identity_mismatches(out.scenario, real.txns) == []
