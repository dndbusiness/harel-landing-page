"""חיבור השלבים: PDF → פירוק → ולידציה → קטגוריזציה → דפוסים → מנוע → פלטים."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .categorize.rules import QueueItem, categorize, load_rules, rule_kind
from .engine.deltas import ChangeAmount, Delta, LoanSchedule, RateChange, RemoveRows
from .engine.params import Params
from .engine.simulate import Engine, Scenario, SimResult, identity_mismatches
from .ingest.merge import load_statement, merge_statements
from .model.money import fmt
from .model.transaction import Transaction
from .patterns.calendar import BusinessCalendar
from .patterns.recurring import detect
from .validate.balance import ValidationReport, validate

PKG_ROOT = Path(__file__).resolve().parents[1]
CONFIG = PKG_ROOT / "config"


@dataclass
class Loaded:
    txns: list[Transaction]
    report: ValidationReport
    queue: list[QueueItem]
    log: list[str] = field(default_factory=list)
    account_hint: str = ""
    period_label: str = ""


def rules_for(client_dir: Path | None):
    paths = [CONFIG / "rules.yaml"]
    if client_dir:
        paths.append(Path(client_dir) / "rules.yaml")
    return load_rules(*paths)


def calendar_for(client_dir: Path | None) -> BusinessCalendar:
    if client_dir and (Path(client_dir) / "calendar.yaml").exists():
        return BusinessCalendar.load(Path(client_dir) / "calendar.yaml")
    return BusinessCalendar.load(CONFIG / "calendar.yaml")


def ingest(files: list[str | Path], client_dir: Path | None = None) -> Loaded:
    statements = [load_statement(f) for f in files]
    merged = merge_statements(statements)
    log = [f"קובץ {s.source_file}: {len(s.transactions)} תנועות, {s.start:%d/%m/%Y}–{s.end:%d/%m/%Y}" for s in statements]
    if merged.duplicates_dropped:
        log.append(f"איחוד: {merged.duplicates_dropped} שורות הופיעו ביותר מקובץ אחד ונספרו פעם אחת")
    if merged.issues:
        from .validate.balance import ValidationError
        rep = ValidationReport(None, None, 0, errors=merged.issues)
        raise ValidationError(rep)
    report = validate(merged.transactions)          # עוצר בכשל
    log += report.log + [report.summary()]
    cat = categorize(merged.transactions, rules_for(client_dir))
    log.append(f"קטגוריזציה: {cat.matched} סווגו לפי כללים, {len(cat.queue)} בתור אישור")
    hint = next((s.account_hint for s in statements if s.account_hint), "")
    period = statements[0].period_label if len(statements) == 1 else ""
    return Loaded(merged.transactions, report, cat.queue, log, hint, period)


def describe_delta(d: Delta) -> str:
    rng = ""
    if getattr(d, "start", None) or getattr(d, "end", None):
        s, e = getattr(d, "start", None), getattr(d, "end", None)
        if s and s == e:
            rng = f" ({s:%d/%m/%Y})"
        else:
            rng = f" ({s:%d/%m/%Y}" if s else " (מההתחלה"
            rng += f" עד {e:%d/%m/%Y})" if e else " והלאה)"
    if isinstance(d, ChangeAmount):
        if d.set_to is not None:
            what = f"סכום חדש {fmt(d.set_to)} ₪"
        elif d.pct is not None:
            what = f"{'+' if d.pct > 0 else ''}{d.pct}%"
        else:
            what = f"{'+' if d.amount > 0 else ''}{fmt(d.amount)} ₪ לשורה"
        basis = " בברוטו" if d.basis == "gross" else ""
        return f"{d.label}: {what}{basis} על {d.select.describe()}{rng}"
    if isinstance(d, LoanSchedule):
        return f"{d.label}: לוח סילוקין חדש ({len(d.schedule)} תשלומים) במקום {d.select.describe()} מ-{d.start:%d/%m/%Y}"
    if isinstance(d, RemoveRows):
        return f"{d.label}: ביטול {d.select.describe()}{rng}"
    if isinstance(d, RateChange):
        return f"{d.label}: טבלת ריבית חלופית — " + ", ".join(
            f"מ-{r.start:%d/%m/%Y} חובה {r.debit_annual_pct}%" for r in d.rates)
    return d.label


@dataclass
class RunOutput:
    base: SimResult
    scenario: SimResult
    engine: Engine
    scenario_lines: list[str]


def run_scenario(txns: list[Transaction], opening: int, params: Params, scenario: Scenario,
                 client_dir: Path | None = None, tax_model_path: Path | None = None) -> RunOutput:
    rules = rules_for(client_dir)
    cal = calendar_for(client_dir)
    kinds = {t.id: rule_kind(t, rules) for t in txns}
    kind_of = lambda t: kinds.get(t.id, "")  # noqa: E731
    patterns = detect(txns, cal, exclude_kinds={"direct_channel_fee", "interest"}, kind_of=kind_of)
    eng = Engine(txns, opening, params, cal, kind_of, patterns, tax_model_path)

    # עיקרון 4: שחזור לפני סימולציה
    base_replay = eng.run(Scenario("בסיס"))
    bad = identity_mismatches(base_replay, txns)
    if bad:
        raise RuntimeError("הסימולטור לא משחזר את הדף — אסור להריץ תרחישים:\n" + "\n".join(bad[:20]))

    base = eng.run(Scenario("בסיס", mode=scenario.mode, forward_months=scenario.forward_months))
    scen = eng.run(scenario)
    return RunOutput(base, scen, eng, [describe_delta(d) for d in scenario.deltas])
