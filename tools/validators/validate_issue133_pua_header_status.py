"""Issue #133 — quikmstr.MSTATUS header is not re-activated by a terminal-base PUA.

Client report: on death-claim-pending policies (LifePRO PPOLC CONTRACT_CODE/
CONTRACT_REASON = S/DP -> Master_Value_Translation ST_S_DP = 50), the base
benefit (BENEFIT_TYPE=BA) correctly inherits 50, but the paid-up-addition
rider (BENEFIT_TYPE=PU) is still coded "A"/Active in PPBEN. The Issue #49
"first active later phase" override then promotes quikmstr.MSTATUS from 50
back to 22 (Active) because it only looked at the PUA phase's bare-letter
STATUS_CODE translation, not the base's terminal status.

Fix: `qla_core/quikmstr_active_phase_status.simulate_display_phase_statuses`
now mirrors the Issue #160 quikridr PUA terminal-status inheritance rule
(`app.py _apply_pua_rider_inheritance`) inside the #49 header-override
simulation: when the base display status is terminal (>=50, excluding
44/45) a later PUA (BENEFIT_TYPE=PU) phase's display status is forced to
the base's display status instead of its own bare STATUS_CODE translation,
so it can no longer win the #49 "first active later phase" check.

This does NOT touch the non-PUA rider population that Issue #49 already
owns (SU/OR riders on a Lapsed (54) base correctly keep overriding MSTATUS
to the active rider's status — verified against
`Issue_Log_Items/Issue_49/evidence/issue49_override_candidates.csv`, all 35
of which are SU/OR, never PU).

Golds (2026-08-31 LifePRO extract, PPOLC S/DP -> ST_S_DP=50):
  9010439999C  base BA STATUS_CODE=A/DP, PUA STATUS_CODE=A/DP -> MSTATUS stays 50
  9010468945C  base BA STATUS_CODE=T/DC, PUA STATUS_CODE=T/DC -> MSTATUS stays 53
    (already terminal on both legs; included as a non-regressing control)

Fail-closed:
  1. A synthetic unit-level check (no source dependency) proves the module
     contract directly: PUA-on-terminal-base is never picked as the #49
     override winner, and PUA-on-44/45 / non-PUA-on-terminal-base are
     unaffected (guards against over-widening into Issue #49/#160/#108D).
  2. If current source (PPBEN + PPOLC) is available, re-derives the golden
     policies directly and asserts MSTATUS is not overridden.
  3. Runs `validate_issue49_mstatus.py --simulate-only` as a sub-check so a
     regression that changes the Closed #49 override population (35 SU/OR
     policies) is caught here too.
  4. If `QLA_Migration/Output/quikmstr.csv` is fresh enough to contain the
     golden policy, checks the emitted MSTATUS directly (WARN, not FAIL, if
     Output is missing/stale — mirrors the #49/#160 validator pattern).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qla_core.quikmstr_active_phase_status import (  # noqa: E402
    bare_status_map_from_trans_map,
    build_ppben_phase_cache,
    select_mstatus_from_active_phase,
)
from qla_core.issue21_open_item_decisions import resolve_ppben_path  # noqa: E402

SCRIPT_VERSION = "1.0"
SRC = ROOT / "QLA_Migration" / "Source"
MVT = ROOT / "QLA_Migration" / "Mapping" / "Master_Value_Translation.csv"
CW = ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"
OUT_MSTR = ROOT / "QLA_Migration" / "Output" / "quikmstr.csv"

GOLDS = {
    # lp POLICY_NUMBER -> (expected quikmstr.MSTATUS, description)
    "9010439999": ("50", "S/DP base + Active PUA -> stays Death Claim Pending"),
    "9010468945": ("53", "T/DC base + terminal PUA -> stays Terminated/Death (control)"),
}

DEFAULT_BARE = {
    "A": "22", "T": "56", "P": "41", "S": "55", "D": "53", "L": "54", "W": "32", "I": "10",
}


def _s(v) -> str:
    return str(v).strip() if v is not None else ""


def unit_level_checks(errors: list[str]) -> None:
    """Prove the module contract directly, no source files required."""
    bare = dict(DEFAULT_BARE)

    # 1) PUA on a terminal (50) base must NOT win the #49 override.
    phases = [(1, 0, "50", "BA"), (2, 1, "A", "PU")]
    final, overridden = select_mstatus_from_active_phase("50", phases, bare)
    if overridden or final != "50":
        errors.append(
            f"unit check 1 FAILED: PUA on terminal base 50 must not override; "
            f"got final={final!r} overridden={overridden}"
        )
    else:
        print("  PASS unit check 1: PUA (BENEFIT_TYPE=PU) on base=50 does not override MSTATUS")

    # 2) PUA on a Lapsed (54) base must NOT win either (base >=50, not 44/45).
    phases = [(1, 0, "54", "BA"), (2, 1, "A", "PU")]
    final, overridden = select_mstatus_from_active_phase("54", phases, bare)
    if overridden or final != "54":
        errors.append(
            f"unit check 2 FAILED: PUA on terminal base 54 must not override; "
            f"got final={final!r} overridden={overridden}"
        )
    else:
        print("  PASS unit check 2: PUA on base=54 does not override MSTATUS")

    # 3) Non-PUA rider (e.g. SU) on a Lapsed (54) base MUST still win — this is
    #    the already-Closed Issue #49 population; do not widen the carve-out.
    phases = [(1, 0, "54", "BA"), (2, 1, "A", "SU")]
    final, overridden = select_mstatus_from_active_phase("54", phases, bare)
    if not overridden or final != "22":
        errors.append(
            f"unit check 3 FAILED (Issue #49 regression): non-PUA rider on "
            f"base=54 must still override to 22; got final={final!r} "
            f"overridden={overridden}"
        )
    else:
        print("  PASS unit check 3: non-PUA rider (SU) on base=54 still overrides to 22 (#49 intact)")

    # 4) PUA on a 44/45 (ETI/RPU) base is untouched here (#108D handles 44/45
    #    -> 54 at the quikridr row level, not in this header simulation).
    phases = [(1, 0, "44", "BA"), (2, 1, "A", "PU")]
    final, overridden = select_mstatus_from_active_phase("44", phases, bare)
    # base 44 is not >=50 so #49's own inactive-check should not even fire.
    if overridden or final != "44":
        errors.append(
            f"unit check 4 FAILED: base 44 must preserve provisional "
            f"(not inactive by #49 definition); got final={final!r} overridden={overridden}"
        )
    else:
        print("  PASS unit check 4: base 44 (ETI) provisional preserved, #49 does not fire")


def source_level_checks(errors: list[str], warnings: list[str]) -> None:
    import pandas as pd

    ppben = resolve_ppben_path(str(SRC))
    ppolc_files = sorted(SRC.glob("PPOLC_PolicyMaster_Extract*.csv"), reverse=True)
    if not ppben or not ppolc_files or not MVT.is_file() or not CW.is_file():
        warnings.append("Source PPBEN/PPOLC/translation/crosswalk not fully available — skipped source-level check")
        return

    trans: dict[str, str] = {}
    df = pd.read_csv(MVT, dtype=str, keep_default_na=False)
    for _, r in df.iterrows():
        k = _s(r.iloc[0])
        v = _s(r.iloc[1])
        if k:
            trans[k.upper()] = v
    bare = bare_status_map_from_trans_map(trans)
    st_only = {k: v for k, v in trans.items() if k.startswith("ST_")}

    def issue13_provisional(cc: str, cr: str, put: str) -> str:
        cc = _s(cc).upper()
        cr = _s(cr).upper()
        put = _s(put).upper()
        if cc == "T":
            key = f"ST_{cc}_{cr}" if cr else f"ST_{cc}_"
        elif put in {"PU", "RU", "ET", "LE", "LP", "SP"}:
            key = f"ST_PUT_{put}"
        else:
            key = f"ST_{cc}_{cr}" if cr else f"ST_{cc}_"
        return st_only.get(key, "")

    cache = build_ppben_phase_cache(ppben, normalize_fn=lambda v: _s(v).upper())
    ppolc = pd.read_csv(ppolc_files[0], dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    ppolc.columns = [c.strip().upper() for c in ppolc.columns]

    by_lp: dict[str, dict] = {}
    for _, r in ppolc.iterrows():
        lp = _s(r.get("POLICY_NUMBER", "")).upper()
        if lp:
            by_lp[lp] = r

    found_any = False
    for lp, (expected_final, desc) in GOLDS.items():
        row = by_lp.get(lp)
        if row is None:
            warnings.append(f"{lp} not present in current PPOLC extract — skipped ({desc})")
            continue
        found_any = True
        provisional = issue13_provisional(
            row.get("CONTRACT_CODE", ""), row.get("CONTRACT_REASON", ""), row.get("PAID_UP_TYPE", "")
        )
        phases = cache.get(lp, [])
        final, overridden = select_mstatus_from_active_phase(provisional, phases, bare)
        if final != expected_final:
            errors.append(
                f"{lp} ({desc}): expected MSTATUS={expected_final} got {final!r} "
                f"(provisional={provisional!r} overridden={overridden} phases={phases})"
            )
        else:
            print(f"  PASS source check {lp}: MSTATUS={final} ({desc})")

    if not found_any:
        warnings.append("Neither golden policy present in current PPOLC extract — source-level check skipped")


def issue49_regression_check(errors: list[str]) -> None:
    script = ROOT / "tools" / "validators" / "validate_issue49_mstatus.py"
    if not script.is_file():
        errors.append("validate_issue49_mstatus.py missing — cannot confirm Closed #49 is intact")
        return
    r = subprocess.run(
        [sys.executable, str(script), "--simulate-only"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        tail = ((r.stdout or "") + (r.stderr or ""))[-1200:]
        errors.append(f"validate_issue49_mstatus.py --simulate-only FAILED (Closed #49 disturbed):\n{tail}")
    else:
        print("  PASS validate_issue49_mstatus.py --simulate-only (Closed #49 population unchanged)")


def output_level_check(warnings: list[str]) -> None:
    if not OUT_MSTR.is_file():
        warnings.append(f"missing {OUT_MSTR} — skipped Output-level check")
        return
    import pandas as pd

    qm = pd.read_csv(OUT_MSTR, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    qm.columns = [c.strip().upper() for c in qm.columns]
    by_pol = {_s(r["MPOLICY"]): _s(r["MSTATUS"]) for _, r in qm.iterrows()}
    hit = by_pol.get("010439999C") or by_pol.get("9010439999C")
    if hit is None:
        warnings.append("9010439999C not found in Output/quikmstr.csv — Output may be stale/pre-8/31; skipped")
        return
    if hit == "22":
        warnings.append(
            "Output/quikmstr.csv MSTATUS=22 for 9010439999C - Output predates this fix; rebatch required before Closure"
        )
    elif hit == "50":
        print("  PASS Output/quikmstr.csv MSTATUS=50 for 9010439999C")
    else:
        warnings.append(f"Output/quikmstr.csv MSTATUS={hit!r} for 9010439999C — unexpected, investigate")


def main() -> int:
    print("=" * 72)
    print(f"ISSUE #133 PUA HEADER STATUS VALIDATOR (script v{SCRIPT_VERSION})")
    print("=" * 72)
    errors: list[str] = []
    warnings: list[str] = []

    unit_level_checks(errors)
    source_level_checks(errors, warnings)
    issue49_regression_check(errors)
    output_level_check(warnings)

    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"FAIL: {e}")
    print("RESULT:", "PASS" if not errors else "FAIL")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
