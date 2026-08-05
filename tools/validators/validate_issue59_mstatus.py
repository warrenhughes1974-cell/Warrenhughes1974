"""
Issue #59 MSTATUS validation.

Scoped client-policy outcomes (Issue #2 MPOLICY = source + C):
  - 6 Active+LP policies: MSTATUS = 22
  - 9010521213C (client 010521213C):
      * when LifePRO is Suspended/Death Pending (S/DP) → 50
      * when LifePRO later terminates as Death Claim (T/DC) → 53
        (7/31+ source; Issue #13 termination mapping — do not force 50)

Hard guard: vs pre-v58.52 current-package baseline (901…C keyspace), NO other
MPOLICY may change MSTATUS except 9010521213C, which may move to the
source-derived expected status.

Usage:
  python tools/validators/validate_issue59_mstatus.py
  python tools/validators/validate_issue59_mstatus.py --output-dir QLA_Migration/Output
  python tools/validators/validate_issue59_mstatus.py --simulate-only
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

SCRIPT_VERSION = "2.2"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
DEFAULT_SOURCE = PROJECT_ROOT / "QLA_Migration" / "Source"
TEST_VALIDATION = DEFAULT_OUTPUT / "Test_Validation"
# Midyear 901…C package baseline (pre #59/#49 Death Claim Pending guard).
# Package-wide unexpected-delta hard guard applies only on that same cut.
BASELINE = (
    PROJECT_ROOT
    / "Issue_Log_Items"
    / "Issue_59"
    / "evidence"
    / "quikmstr_pre_issue59_v5852_baseline.csv"
)
BASELINE_VALUATION_DATE = "20260630"
MVT = PROJECT_ROOT / "QLA_Migration" / "Mapping" / "Master_Value_Translation.csv"

# Exact current-package QLA keys (Issue #2 source+C) — Active+LP fixed at 22
EXPECTED_ACTIVE_LP = {
    "901122D991C": "22",
    "9014FG8217C": "22",
    "9016FG8217C": "22",
    "901ML8171C": "22",
    "901ML8250C": "22",
    "901ML8522C": "22",
}

DEATH_CLAIM_POLICY = "9010521213C"
ALLOWED_DELTA_KEYS = {DEATH_CLAIM_POLICY}

# Issue #49 preserve samples (must remain unchanged vs baseline; 901…C keyspace)
ISSUE49_PRESERVE = (
    "9018252C",
    "9018253C",
    "901ML8007C",
    "9018187C",
    "9010380550C",
)


def _norm(v) -> str:
    s = str(v).strip() if v is not None else ""
    if s.endswith(".0"):
        s = s[:-2]
    if s.lower() in ("nan", "none"):
        return ""
    return s


def load_st() -> dict[str, str]:
    out: dict[str, str] = {}
    with MVT.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            k = _norm(row.get("Source_Code"))
            if k.startswith("ST_"):
                out[k] = _norm(row.get("QLA_Result"))
    return out


def load_mstatus(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return {_norm(r["MPOLICY"]): _norm(r["MSTATUS"]) for r in csv.DictReader(f)}


def _ppolc_row_for_death_claim(source_root: Path) -> dict[str, str]:
    """Return PPOLC fields for LifePRO 9010521213 from the active valuation package."""
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from qla_core.valuation_date import apply_valuation_date_env, select_ppolc_path

    vd, _src = apply_valuation_date_env(source_root)
    ppolc = Path(select_ppolc_path(source_root, vd))
    with ppolc.open(newline="", encoding="latin-1", errors="replace") as f:
        for row in csv.DictReader(f):
            if _norm(row.get("POLICY_NUMBER")) == "9010521213":
                return {
                    "CONTRACT_CODE": _norm(row.get("CONTRACT_CODE")).upper(),
                    "CONTRACT_REASON": _norm(row.get("CONTRACT_REASON")).upper(),
                    "PAID_UP_TYPE": _norm(row.get("PAID_UP_TYPE")).upper(),
                    "ppolc": str(ppolc),
                    "valuation_date": vd,
                }
    raise FileNotFoundError(f"9010521213 not found in {ppolc}")


def expected_death_claim_mstatus(source_root: Path) -> tuple[str, str]:
    """
    Source-aware expected MSTATUS for 9010521213C.

    Midyear S/DP → 50 (Issue #59 original). Later T/DC → 53 (Issue #13 / ST_T_DC).
    """
    st = load_st()
    src = _ppolc_row_for_death_claim(source_root)
    code = src["CONTRACT_CODE"]
    reason = src["CONTRACT_REASON"]
    key = f"ST_{code}_{reason}" if reason else f"ST_{code}_"
    expected = st.get(key, "")
    detail = (
        f"{src['valuation_date']} {Path(src['ppolc']).name} "
        f"CONTRACT={code}/{reason} -> {key}={expected}"
    )
    if not expected:
        raise ValueError(f"No ST translation for {key} ({detail})")
    return expected, detail


def simulate_scoped_keys(source_root: Path) -> dict[str, str]:
    """Expected ST results for the scoped policies (Active+LP fixed; DP source-aware)."""
    st = load_st()
    dp_exp, _ = expected_death_claim_mstatus(source_root)
    out = {pol: st["ST_A_"] for pol in EXPECTED_ACTIVE_LP}
    out[DEATH_CLAIM_POLICY] = dp_exp
    return out


def publish_test_validation(output_dir: Path) -> None:
    TEST_VALIDATION.mkdir(parents=True, exist_ok=True)
    for name in ("quikmstr.csv",):
        src = output_dir / name
        if src.exists():
            dst = TEST_VALIDATION / name
            dst.write_bytes(src.read_bytes())
            print(f"Published {dst}")


def _active_valuation_date(source_root: Path) -> str:
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from qla_core.valuation_date import apply_valuation_date_env

    vd, _ = apply_valuation_date_env(source_root)
    return vd


def main() -> int:
    ap = argparse.ArgumentParser(description="Issue #59 MSTATUS scoped validation")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--simulate-only", action="store_true")
    ap.add_argument("--publish-test-validation", action="store_true")
    ap.add_argument(
        "--strict-baseline",
        action="store_true",
        help=(
            "Fail on any MSTATUS delta outside ALLOWED_DELTA_KEYS vs midyear "
            f"package baseline ({BASELINE_VALUATION_DATE}). Default: only when "
            "active valuation matches that baseline cut."
        ),
    )
    args = ap.parse_args()

    print(f"validate_issue59_mstatus.py {SCRIPT_VERSION}")
    errors: list[str] = []

    try:
        dp_expected, dp_detail = expected_death_claim_mstatus(args.source_dir)
        active_vd = _active_valuation_date(args.source_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL - cannot resolve death-claim source expectation: {exc}")
        return 1

    expected_mstatus = dict(EXPECTED_ACTIVE_LP)
    expected_mstatus[DEATH_CLAIM_POLICY] = dp_expected
    print(f"  Death-claim expectation: {DEATH_CLAIM_POLICY}={dp_expected} ({dp_detail})")

    sim = simulate_scoped_keys(args.source_dir)
    for pol, exp in expected_mstatus.items():
        if sim.get(pol) != exp:
            errors.append(
                f"SIM translation mismatch {pol}: got {sim.get(pol)} expected {exp}"
            )

    if args.simulate_only:
        if errors:
            print("FAIL (simulate)")
            for e in errors:
                print(" ", e)
            return 1
        print(
            f"PASS (simulate) - ST_A_=22 and death-claim source map "
            f"{DEATH_CLAIM_POLICY}={dp_expected}"
        )
        return 0

    mstr_path = args.output_dir / "quikmstr.csv"
    if not mstr_path.exists():
        print(f"FAIL - missing {mstr_path}")
        return 1
    if not BASELINE.exists():
        print(f"FAIL - missing baseline {BASELINE}")
        return 1

    current = load_mstatus(mstr_path)
    baseline = load_mstatus(BASELINE)

    # Trace expectations (exact seven client outcomes; DP is source-aware)
    for pol, exp in expected_mstatus.items():
        got = current.get(pol)
        if got != exp:
            errors.append(f"TRACE {pol}: MSTATUS={got!r} expected {exp!r}")

    same_cut_baseline = active_vd == BASELINE_VALUATION_DATE or args.strict_baseline
    if same_cut_baseline:
        # Hard guard: only ALLOWED_DELTA_KEYS may differ from midyear package baseline
        unexpected: list[str] = []
        for pol, before in baseline.items():
            after = current.get(pol)
            if after is None:
                continue
            if after == before:
                continue
            if pol not in ALLOWED_DELTA_KEYS:
                unexpected.append(f"{pol}: {before} -> {after}")
            elif after != expected_mstatus.get(pol):
                errors.append(
                    f"ALLOWED delta wrong {pol}: {before} -> {after} "
                    f"(want {expected_mstatus.get(pol)})"
                )

        if unexpected:
            errors.append(f"UNEXPECTED MSTATUS changes ({len(unexpected)}):")
            for u in unexpected[:25]:
                errors.append(f"  {u}")
            if len(unexpected) > 25:
                errors.append(f"  ... +{len(unexpected) - 25} more")

        # Six Active+LP traces must already be correct in baseline and stay correct
        for pol, exp in EXPECTED_ACTIVE_LP.items():
            before = baseline.get(pol)
            after = current.get(pol)
            if before != exp:
                errors.append(
                    f"BASELINE unexpected for {pol}: {before!r} "
                    f"(expected package {exp!r})"
                )
            if after != exp:
                errors.append(
                    f"Active+LP trace broken {pol}: {after!r} expected {exp!r}"
                )

        # #49 samples unchanged vs package baseline
        for pol in ISSUE49_PRESERVE:
            if pol in baseline and baseline[pol] != current.get(pol):
                errors.append(
                    f"Issue #49 preserve broken {pol}: "
                    f"{baseline[pol]} -> {current.get(pol)}"
                )

        only_cur = set(current) - set(baseline)
        only_base = set(baseline) - set(current)
        if only_cur or only_base:
            errors.append(
                f"MPOLICY set drift: +{len(only_cur)} / -{len(only_base)} "
                "vs package baseline"
            )
    else:
        print(
            f"  Skipping package-wide baseline hard guard "
            f"(active valuation {active_vd} != baseline cut "
            f"{BASELINE_VALUATION_DATE}; use --strict-baseline to force)"
        )

    # Death-claim policy must match source-derived expected
    for pol in ALLOWED_DELTA_KEYS:
        after = current.get(pol)
        exp = expected_mstatus[pol]
        if after != exp:
            errors.append(
                f"{pol} after={after} expected {exp} "
                f"(baseline was {baseline.get(pol)}; {dp_detail})"
            )

    if errors:
        print("FAIL")
        for e in errors:
            print(" ", e)
        return 1

    print("PASS")
    print(f"  Scoped traces OK ({len(expected_mstatus)})")
    print(f"  Death-claim {DEATH_CLAIM_POLICY}={dp_expected} matches source")
    if same_cut_baseline:
        print("  No unexpected MSTATUS deltas vs pre-v58.52 package baseline")
        print("  Issue #49 preserve samples unchanged")
    if args.publish_test_validation:
        publish_test_validation(args.output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
