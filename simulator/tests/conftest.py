import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "fixtures"))


@pytest.fixture(scope="session")
def synthetic(tmp_path_factory):
    import synthetic as syn
    out = tmp_path_factory.mktemp("synthetic")
    info = syn.generate(out)
    info["dir"] = out
    info["csv"] = out / "synthetic.csv"
    info["pdf"] = out / "synthetic.pdf"
    return info


@pytest.fixture
def loaded(synthetic):
    from oshsim.pipeline import ingest
    return ingest([synthetic["csv"]])


@pytest.fixture
def params():
    from oshsim.engine.params import Params
    return Params.from_dict({"direct_channel_fee": {"rate": "1.76", "free_quota": 0}})


@pytest.fixture
def params_rates():
    from oshsim.engine.params import Params
    return Params.from_dict({
        "direct_channel_fee": {"rate": "1.76"},
        "interest": {"rates": [{"from": "2026-01-01", "debit_annual_pct": "12.5", "credit_annual_pct": "0"}]},
        "credit_limit": {"amount": "40000"},
    })
