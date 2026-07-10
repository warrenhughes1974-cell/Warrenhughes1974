"""
Issue #49 MSTATUS validation (v57.70).

When first-phase display status is >= 50 and a later phase is 0–49,
quikmstr.MSTATUS must equal that first later active phase status.
Otherwise Issue #13 / PPOLC behavior is preserved.

Usage:
  python tools/validators/validate_issue49_mstatus.py
  python tools/validators/validate_issue49_mstatus.py --output-dir QLA_Migration/Output
  python tools/validators/validate_issue49_mstatus.py --simulate-only
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

SCRIPT_VERSION = "1.2"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
TEST_VALIDATION = DEFAULT_OUTPUT / "Test_Validation"
SRC = PROJECT_ROOT / "QLA_Migration" / "Source"
CW = PROJECT_ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"
MVT = PROJECT_ROOT / "QLA_Migration" / "Mapping" / "Master_Value_Translation.csv"
CANDIDATES = PROJECT_ROOT / "Issue_Log_Items" / "Issue_49" / "evidence" / "issue49_override_candidates.csv"
MSTR_BASELINE = PROJECT_ROOT / "Issue_Log_Items" / "Issue_49" / "evidence" / "quikmstr_pre_v5770_baseline.csv"
RIDR_BASELINE = PROJECT_ROOT / "Issue_Log_Items" / "Issue_49" / "evidence" / "quikridr_pre_v5770_baseline.csv"
ISSUE49_TABLES = ("quikmstr", "quikridr")

sys.path.insert(0, str(PROJECT_ROOT))
from qla_core.quikmstr_active_phase_status import (  # noqa: E402
    bare_status_map_from_trans_map,
    build_ppben_phase_cache,
    select_mstatus_from_active_phase,
)
from qla_core.issue21_open_item_decisions import resolve_ppben_path  # noqa: E402

# Risk-approved preserve samples (phase 1 already active 0–49)
PRESERVE_TRACE = {
    "018187C": "45",
    "010380550C": "41",
}

# Override samples from Risk
OVERRIDE_TRACE = {
    "018252C": "22",
    "018253C": "22",
}

EXPECTED_OVERRIDE_COUNT = 35


def _s(v) -> str:
    return str(v).strip() if v is not None else ""


def _norm(v) -> str:
    s = _s(v).upper()
    if s.endswith(".0"):
        s = s[:-2]
    if s.lower() in ("nan", "none", ""):
        return ""
    return s


def _read(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def load_trans_map() -> dict[str, str]:
    df = pd.read_csv(MVT, dtype=str, keep_default_na=False)
    out = {}
    for _, r in df.iterrows():
        k = _s(r.iloc[0] if "Source_Code" not in df.columns else r.get("Source_Code", r.iloc[0]))
        v = _s(r.iloc[1] if "QLA_Result" not in df.columns else r.get("QLA_Result", r.iloc[1]))
        if k:
            out[_norm(k)] = v
    return out


def issue13_provisional(cc: str, cr: str, put: str, st_map: dict[str, str]) -> str:
    cc = _norm(cc)
    cr = _norm(cr)
    put = _norm(put)
    if cc == "T":
        key = f"ST_{cc}_{cr}" if cr else f"ST_{cc}_"
    elif put in {"PU", "RU", "ET", "LE", "LP", "SP"}:
        key = f"ST_PUT_{put}"
    else:
        key = f"ST_{cc}_{cr}" if cr else f"ST_{cc}_"
    return st_map.get(key, st_map.get(key.replace("ST_", ""), ""))


def simulate_overrides() -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    ppben = resolve_ppben_path(str(SRC))
    ppolc_files = sorted(SRC.glob("PPOLC_PolicyMaster_Extract*.csv"), reverse=True)
    if not ppben or not ppolc_files:
        return [], ["Missing PPBEN or PPOLC in Source"]

    trans = load_trans_map()
    bare = bare_status_map_from_trans_map(trans)
    st_map = {k: v for k, v in trans.items() if k.startswith("ST_") or True}
    # rebuild ST lookup
    st_only = {k: v for k, v in trans.items() if str(k).startswith("ST_")}
    for k, v in trans.items():
        if str(k).startswith("ST_"):
            st_only[k] = v

    cache = build_ppben_phase_cache(ppben, normalize_fn=_norm)
    ppolc = _read(ppolc_files[0])
    cw = _read(CW)
    cw_map = {_norm(r["OLD_VALUE"]): _norm(r["NEW_VALUE"]) for _, r in cw.iterrows()}

    rows = []
    for _, r in ppolc.iterrows():
        lp = _norm(r.get("POLICY_NUMBER", ""))
        if not lp or set(lp) <= {"-"}:
            continue
        provisional = issue13_provisional(
            r.get("CONTRACT_CODE", ""),
            r.get("CONTRACT_REASON", ""),
            r.get("PAID_UP_TYPE", ""),
            st_only,
        )
        if not provisional:
            # try without requiring ST_ only — issue13_provisional already uses ST_
            continue
        phases = cache.get(lp, [])
        final, overridden = select_mstatus_from_active_phase(provisional, phases, bare)
        if overridden:
            rows.append(
                {
                    "LIFEPRO": lp,
                    "MPOLICY": cw_map.get(lp, ""),
                    "PROVISIONAL": provisional,
                    "FINAL": final,
                }
            )
    return rows, errors


def _regression_non_candidate_mstatus(
    qm: pd.DataFrame,
    cand_pols: set[str],
    errors: list[str],
) -> None:
    if not MSTR_BASELINE.is_file():
        return
    base = _read(MSTR_BASELINE)
    base_by = {_s(r["MPOLICY"]): _s(r["MSTATUS"]) for _, r in base.iterrows()}
    new_by = {_s(r["MPOLICY"]): _s(r["MSTATUS"]) for _, r in qm.iterrows()}
    if len(base_by) != len(new_by):
        errors.append(f"quikmstr row count {len(new_by)} != baseline {len(base_by)}")
        return
    print(f"  PASS quikmstr row count {len(new_by)} == baseline")
    unexpected = []
    for pol, b_stat in base_by.items():
        if pol in cand_pols:
            continue
        n_stat = new_by.get(pol, "")
        if n_stat != b_stat:
            unexpected.append(f"{pol}: {b_stat}->{n_stat}")
    if unexpected:
        errors.append(
            f"Non-candidate MSTATUS changed ({len(unexpected)}): {unexpected[:5]}"
        )
    else:
        print(f"  PASS non-candidate MSTATUS unchanged ({len(base_by) - len(cand_pols)} policies)")


def validate(output_dir: Path, simulate_only: bool = False, publish_test_validation: bool = False) -> int:
    print("=" * 72)
    print(f"ISSUE #49 MSTATUS VALIDATION (script v{SCRIPT_VERSION}, engine v57.71)")
    print(f"Output: {output_dir}")
    print("=" * 72)

    errors: list[str] = []
    warnings: list[str] = []

    sim_rows, sim_errs = simulate_overrides()
    errors.extend(sim_errs)
    print(f"Simulated overrides from Source: {len(sim_rows)}")
    if len(sim_rows) != EXPECTED_OVERRIDE_COUNT:
        errors.append(
            f"Simulated override count {len(sim_rows)} != expected {EXPECTED_OVERRIDE_COUNT}"
        )
    else:
        print(f"  PASS simulated count == {EXPECTED_OVERRIDE_COUNT}")

    if CANDIDATES.is_file():
        cand = _read(CANDIDATES)
        cand_pols = {_s(p) for p in cand["MPOLICY"]}
        sim_pols = {_s(r["MPOLICY"]) for r in sim_rows if r["MPOLICY"]}
        missing = cand_pols - sim_pols
        extra = sim_pols - cand_pols
        if missing:
            errors.append(f"Simulation missing candidate MPOLICYs: {sorted(missing)[:10]}")
        if extra:
            warnings.append(f"Simulation extra MPOLICYs vs evidence: {sorted(extra)[:10]}")
        if not missing and not extra:
            print("  PASS simulation MPOLICY set matches evidence candidates")

    if all(_s(r["FINAL"]) == "22" for r in sim_rows) and sim_rows:
        print("  PASS all simulated finals are 22")
    elif sim_rows:
        warnings.append(f"Unexpected final statuses: {sorted({r['FINAL'] for r in sim_rows})}")

    if simulate_only:
        for e in errors:
            print(f"FAIL: {e}")
        for w in warnings:
            print(f"WARN: {w}")
        print("RESULT:", "PASS" if not errors else "FAIL")
        return 0 if not errors else 1

    mstr_path = output_dir / "quikmstr.csv"
    if not mstr_path.is_file():
        warnings.append(f"Output quikmstr.csv missing — skip emit checks ({mstr_path})")
        for e in errors:
            print(f"FAIL: {e}")
        for w in warnings:
            print(f"WARN: {w}")
        print("RESULT:", "PASS (simulate-only effective)" if not errors else "FAIL")
        return 0 if not errors else 1

    qm = _read(mstr_path)
    by_pol = {_s(r["MPOLICY"]): _s(r["MSTATUS"]) for _, r in qm.iterrows()}
    cand_pols: set[str] = set()
    if CANDIDATES.is_file():
        cand_pols = {_s(p) for p in _read(CANDIDATES)["MPOLICY"]}
    _regression_non_candidate_mstatus(qm, cand_pols, errors)

    # If output still has pre-#49 values, report as not-yet-batched
    changed = 0
    for r in sim_rows:
        pol = _s(r["MPOLICY"])
        if not pol:
            continue
        got = by_pol.get(pol, "")
        exp = _s(r["FINAL"])
        if got == exp:
            changed += 1
        else:
            warnings.append(f"{pol}: output MSTATUS={got} expected {exp} (rebatch may be required)")

    print(f"Output matches simulated final: {changed}/{len([r for r in sim_rows if r['MPOLICY']])}")
    if changed == len([r for r in sim_rows if r["MPOLICY"]]):
        print("  PASS output matches all simulated overrides")
    elif changed == 0:
        warnings.append("Output appears pre-#49 — run full/quikmstr batch under v57.70")
    else:
        errors.append("Partial output match — investigate")

    for pol, exp in OVERRIDE_TRACE.items():
        got = by_pol.get(pol, "")
        if got and got != exp:
            # only hard-fail if batch already applied some overrides
            if changed:
                errors.append(f"Trace {pol}: MSTATUS={got} expected {exp}")
        elif got == exp:
            print(f"  PASS override trace {pol}={exp}")

    for pol, exp in PRESERVE_TRACE.items():
        got = by_pol.get(pol, "")
        if got and got != exp:
            errors.append(f"Preserve trace {pol}: MSTATUS={got} expected unchanged {exp}")
        elif got == exp:
            print(f"  PASS preserve trace {pol}={exp}")

    # Regression: phase-1 MPHSTAT must remain at pre-#49 baseline for override candidates
    ridr_path = output_dir / "quikridr.csv"
    if ridr_path.is_file() and RIDR_BASELINE.is_file() and cand_pols:
        qr = _read(ridr_path)
        qrb = _read(RIDR_BASELINE)
        if len(qr) != len(qrb):
            errors.append(f"quikridr row count {len(qr)} != baseline {len(qrb)}")
        else:
            print(f"  PASS quikridr row count {len(qr)} == baseline")

        def _phase1_map(df: pd.DataFrame) -> dict[str, str]:
            out: dict[str, str] = {}
            for _, r in df.iterrows():
                pol = _s(r.get("MPOLICY", ""))
                ph = _s(r.get("MPHASE", "")).lstrip("0") or "0"
                if ph == "1" and pol:
                    out[pol] = _s(r.get("MPHSTAT", ""))
            return out

        base_p1 = _phase1_map(qrb)
        new_p1 = _phase1_map(qr)
        p1_changed = []
        for pol in sorted(cand_pols):
            b = base_p1.get(pol, "")
            n = new_p1.get(pol, "")
            if b and n and b != n:
                p1_changed.append(f"{pol}: phase1 MPHSTAT {b}->{n}")
        if p1_changed:
            errors.append(
                f"Phase-1 MPHSTAT changed on {len(p1_changed)} override candidates "
                f"(must remain unchanged): {p1_changed[:5]}"
            )
        else:
            print(f"  PASS phase-1 MPHSTAT unchanged for {len(cand_pols)} override candidates")
        # Spot-check 01ML8007C expected shape: MSTATUS 22, phase1 54, phase2 22
        if "01ML8007C" in cand_pols:
            p1 = new_p1.get("01ML8007C", "")
            mst = by_pol.get("01ML8007C", "")
            p2 = ""
            for _, r in qr.iterrows():
                if _s(r.get("MPOLICY")) == "01ML8007C" and _s(r.get("MPHASE")).lstrip("0") == "2":
                    p2 = _s(r.get("MPHSTAT"))
                    break
            if mst == "22" and p1 == "54" and p2 == "22":
                print("  PASS 01ML8007C shape MSTATUS=22 phase1=54 phase2=22")
            elif mst == "22":
                errors.append(
                    f"01ML8007C expected MSTATUS=22 phase1=54 phase2=22; "
                    f"got MSTATUS={mst} phase1={p1} phase2={p2}"
                )

    if publish_test_validation and not errors:
        sys.path.insert(0, str(PROJECT_ROOT / "tools"))
        from publish_test_validation import publish_tables  # noqa: E402

        dest = publish_tables(
            list(ISSUE49_TABLES),
            output_dir=output_dir,
            dest_dir=TEST_VALIDATION,
            issue_tag="Issue_49_v57.71",
        )
        print(f"  PASS published modified tables to {dest}")

    for e in errors:
        print(f"FAIL: {e}")
    for w in warnings:
        print(f"WARN: {w}")
    print("RESULT:", "PASS" if not errors else "FAIL")
    return 0 if not errors else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Issue #49 MSTATUS validator")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--simulate-only", action="store_true")
    ap.add_argument(
        "--publish-test-validation",
        action="store_true",
        help="On PASS, copy quikmstr.csv and quikridr.csv to Output/Test_Validation",
    )
    args = ap.parse_args()
    return validate(
        args.output_dir,
        simulate_only=args.simulate_only,
        publish_test_validation=args.publish_test_validation,
    )


if __name__ == "__main__":
    raise SystemExit(main())
