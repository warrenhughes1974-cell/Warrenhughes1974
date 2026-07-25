"""
Issue #60 PUA phase validation.

Chris plan / Track A:
  - PUA rows only (synthetic *PA MPLAN): MEFFDATE/MAGE/MPAYUP/MLASTANN align to base phase 1
  - MPHSTAT=41 when base MPHSTAT < 50
  - Non-PUA later-phase riders: MEFFDATE/MAGE unchanged vs pre-v57.85 baseline

NFO carve-out (Issue #108D, v58.32): when the policy is ETI/RPU the PUA benefit is folded
into the base and its coverage terminates, so the PUA row carries MPHSTAT=54 and keeps its
own MAGE/MLASTANN rather than inheriting the base values that Issue #108B reset to the NFO
date. Those rows are checked against the NFO contract instead of the inheritance contract.

Baseline keys predate Issue #2 (v58.29), which widened MPOLICY from 10 to 11 characters.
All baseline lookups go through _canon so the guard actually compares rows; before v2.0 of
this script every lookup missed and the guard passed vacuously.

Usage:
  python tools/validators/validate_issue60_pua_phase.py
  python tools/validators/validate_issue60_pua_phase.py --strict-baseline
  python tools/validators/validate_issue60_pua_phase.py --publish-test-validation
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_VERSION = "2.0"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
TEST_VALIDATION = DEFAULT_OUTPUT / "Test_Validation"
EVIDENCE_DIR = PROJECT_ROOT / "Issue_Log_Items" / "Issue_60" / "evidence"
BASELINE = EVIDENCE_DIR / "quikridr_pre_v5785_baseline.csv"
DRIFT_REPORT = EVIDENCE_DIR / "issue60_cross_release_drift.csv"

GOLDEN = "010310404C"
MIXED_POLICY = "010150910C"  # PUA + ADB — other rider must not move
NFO_STATUSES = {"44", "45"}

# Fields the PUA alignment owns. Any movement here is a real regression.
HARD_FIELDS = ("MEFFDATE", "MAGE", "MPHSTAT", "MPAYUP")
# MLASTANN is measured from the batch valuation date, which v57.86 made configurable after
# this baseline was captured, so a uniform shift is expected. It is still checked: the shift
# must be identical on every row, since a scattered delta would mean a real duration bug.
# MPREM is compared numerically so "0.00" vs "0" is not counted as drift.
SOFT_FIELDS = ("MLASTANN", "MPREM")


def _norm(v) -> str:
    s = str(v).strip() if v is not None else ""
    if s.endswith(".0"):
        s = s[:-2]
    if s.lower() in ("nan", "none"):
        return ""
    return s


def _canon(v) -> str:
    """Policy identity that matches across the Issue #2 key change."""
    s = _norm(v).upper()
    if s.endswith("C"):
        s = s[:-1]
    if s.startswith("9"):
        s = s[1:]
    return s


def _same_value(field: str, a: object, b: object) -> bool:
    """Compare a field, treating MPREM numerically so decimal formatting is not drift."""
    x, y = _norm(a), _norm(b)
    if x == y:
        return True
    if field == "MPREM":
        try:
            return float(x or 0) == float(y or 0)
        except ValueError:
            return False
    return False


def _status_int(raw: str) -> int:
    try:
        return int("".join(c for c in _norm(raw) if c.isdigit()) or "99")
    except ValueError:
        return 99


def is_pua_mplan(mplan: str) -> bool:
    p = _norm(mplan)
    return len(p) >= 6 and p.endswith("PA")


def load_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def row_key(row: dict) -> tuple[str, str, str]:
    return (_canon(row.get("MPOLICY")), _norm(row.get("MPHASE")), _norm(row.get("MPLAN")))


def publish_test_validation(output_dir: Path) -> None:
    TEST_VALIDATION.mkdir(parents=True, exist_ok=True)
    src = output_dir / "quikridr.csv"
    if src.exists():
        dst = TEST_VALIDATION / "quikridr.csv"
        dst.write_bytes(src.read_bytes())
        print(f"Published {dst}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Issue #60 PUA phase validation")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--publish-test-validation", action="store_true")
    ap.add_argument(
        "--strict-baseline",
        action="store_true",
        help="fail on any drift vs the v57.85 baseline instead of reporting it",
    )
    args = ap.parse_args()

    print(f"validate_issue60_pua_phase.py {SCRIPT_VERSION}")
    errors: list[str] = []

    ridr_path = args.output_dir / "quikridr.csv"
    mstr_path = args.output_dir / "quikmstr.csv"
    for p in (ridr_path, mstr_path):
        if not p.exists():
            print(f"FAIL — missing {p}")
            return 1
    if not BASELINE.exists():
        print(f"FAIL — missing baseline {BASELINE}")
        return 1

    current = load_rows(ridr_path)
    mstatus = {_canon(r.get("MPOLICY")): _norm(r.get("MSTATUS")) for r in load_rows(mstr_path)}
    baseline_by_key = {row_key(r): r for r in load_rows(BASELINE)}

    by_pol_cur: dict[str, list[dict]] = defaultdict(list)
    for r in current:
        by_pol_cur[_canon(r.get("MPOLICY"))].append(r)

    def base_of(pol: str) -> dict | None:
        for r in by_pol_cur.get(pol, []):
            if _norm(r.get("MPHASE")) in ("1", "01"):
                return r
        return None

    def is_nfo(pol: str) -> bool:
        return mstatus.get(pol, "") in NFO_STATUSES

    pua_rows = [r for r in current if is_pua_mplan(r.get("MPLAN", ""))]
    other_later = [
        r for r in current
        if not is_pua_mplan(r.get("MPLAN", "")) and _norm(r.get("MPHASE")) not in ("1", "01")
    ]

    # Golden trace — inheritance contract (asserted non-NFO so the trace stays meaningful)
    golden_pua = next((r for r in pua_rows if _canon(r["MPOLICY"]) == _canon(GOLDEN)), None)
    golden_base = base_of(_canon(GOLDEN))
    if not golden_pua or not golden_base:
        errors.append(f"TRACE missing golden policy {GOLDEN}")
    elif is_nfo(_canon(GOLDEN)):
        errors.append(f"TRACE golden {GOLDEN} is now NFO — pick a non-NFO inheritance trace")
    else:
        exp = {
            "MPHSTAT": "41",
            "MEFFDATE": _norm(golden_base.get("MEFFDATE")),
            "MAGE": _norm(golden_base.get("MAGE")),
            "MPAYUP": _norm(golden_base.get("MEFFDATE")),
            "MLASTANN": _norm(golden_base.get("MLASTANN")),
        }
        for f, v in exp.items():
            got = _norm(golden_pua.get(f))
            if got != v:
                errors.append(f"TRACE {GOLDEN} PUA {f}={got!r} expected {v!r}")

    # Mixed policy — the ADB rider must not move when the PUA row is aligned
    for r in current:
        if _canon(r["MPOLICY"]) != _canon(MIXED_POLICY) or _norm(r.get("MPLAN")) != "920ADB":
            continue
        bk = baseline_by_key.get(row_key(r))
        if not bk:
            errors.append(f"TRACE {MIXED_POLICY} ADB missing in baseline")
            break
        for f in HARD_FIELDS:
            if not _same_value(f, r.get(f), bk.get(f)):
                errors.append(
                    f"TRACE {MIXED_POLICY} ADB {f} changed "
                    f"{_norm(bk.get(f))!r} -> {_norm(r.get(f))!r}"
                )

    # Fleet PUA rules
    pua_violations = 0
    nfo_pua = 0

    def flag(msg: str) -> None:
        nonlocal pua_violations
        pua_violations += 1
        if pua_violations <= 5:
            errors.append(msg)

    for r in pua_rows:
        pol = _canon(r["MPOLICY"])
        base = base_of(pol)
        if not base:
            errors.append(f"PUA {_norm(r['MPOLICY'])} ph={_norm(r.get('MPHASE'))}: no base phase")
            continue
        if is_nfo(pol):
            # Issue #108D: PUA folds into the base and terminates.
            nfo_pua += 1
            if _norm(r.get("MPHSTAT")) != "54":
                flag(f"PUA {_norm(r['MPOLICY'])}: NFO base expects MPHSTAT=54, got {_norm(r.get('MPHSTAT'))}")
            continue
        be = _norm(base.get("MEFFDATE"))
        bl = _norm(base.get("MLASTANN"))
        if _norm(r.get("MEFFDATE")) != be:
            flag(f"PUA {_norm(r['MPOLICY'])}: MEFFDATE != base")
        if _norm(r.get("MAGE")) != _norm(base.get("MAGE")):
            flag(f"PUA {_norm(r['MPOLICY'])}: MAGE != base")
        if _norm(r.get("MPAYUP")) != be:
            flag(f"PUA {_norm(r['MPOLICY'])}: MPAYUP != base MEFFDATE")
        if bl and _norm(r.get("MLASTANN")) != bl:
            flag(f"PUA {_norm(r['MPOLICY'])}: MLASTANN != base")
        bs = _status_int(base.get("MPHSTAT", ""))
        if bs < 50 and _norm(r.get("MPHSTAT")) != "41":
            flag(f"PUA {_norm(r['MPOLICY'])}: expected MPHSTAT=41 (base active)")
        if bs >= 50 and _norm(r.get("MPHSTAT")) == "41":
            flag(f"PUA {_norm(r['MPOLICY'])}: forced 41 on terminated base")

    if pua_violations > 5:
        errors.append(f"PUA fleet violations: {pua_violations} (first 5 listed)")

    # Drift vs the v57.85 baseline. NFO rows are excluded because Issue #108 deliberately
    # rewrites them. HARD_FIELDS always fail; SOFT_FIELDS are reported and only fail under
    # --strict-baseline, because the baseline predates the configurable valuation date.
    drift: list[dict] = []

    def compare(scope: str, rows: list[dict], fields: tuple[str, ...]) -> None:
        for r in rows:
            pol = _canon(r.get("MPOLICY"))
            if is_nfo(pol):
                continue
            bk = baseline_by_key.get(row_key(r))
            if not bk:
                continue
            for f in fields:
                if not _same_value(f, r.get(f), bk.get(f)):
                    drift.append({
                        "SCOPE": scope,
                        "MPOLICY": _norm(r.get("MPOLICY")),
                        "MPHASE": _norm(r.get("MPHASE")),
                        "MPLAN": _norm(r.get("MPLAN")),
                        "FIELD": f,
                        "BASELINE": _norm(bk.get(f)),
                        "CURRENT": _norm(r.get(f)),
                    })

    compare("NON_PUA_LATER", other_later, ("MEFFDATE", "MAGE"))
    compare(
        "PHASE1",
        [r for r in current if _norm(r.get("MPHASE")) in ("1", "01")],
        HARD_FIELDS + SOFT_FIELDS,
    )

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    with DRIFT_REPORT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["SCOPE", "MPOLICY", "MPHASE", "MPLAN", "FIELD", "BASELINE", "CURRENT"],
        )
        w.writeheader()
        w.writerows(drift)

    hard_drift = [d for d in drift if d["FIELD"] in HARD_FIELDS]
    soft_drift = [d for d in drift if d["FIELD"] in SOFT_FIELDS]

    for d in hard_drift[:5]:
        errors.append(
            f"BASELINE drift {d['SCOPE']} {d['MPOLICY']} ph{d['MPHASE']} {d['FIELD']}: "
            f"{d['BASELINE']!r} -> {d['CURRENT']!r}"
        )
    if len(hard_drift) > 5:
        errors.append(f"date/age/status drift rows: {len(hard_drift)} (see {DRIFT_REPORT.name})")

    # A uniform MLASTANN shift is the valuation-date change; a scattered one is a real bug.
    mlast_deltas: set[int] = set()
    mlast_nonnum = 0
    for d in soft_drift:
        if d["FIELD"] != "MLASTANN":
            continue
        try:
            mlast_deltas.add(int(d["CURRENT"]) - int(d["BASELINE"]))
        except ValueError:
            mlast_nonnum += 1
    if len(mlast_deltas) > 1:
        errors.append(
            f"MLASTANN drift is not uniform (deltas {sorted(mlast_deltas)}) — a global "
            "valuation-date shift would move every row by the same amount"
        )
    if mlast_nonnum:
        errors.append(f"MLASTANN drift with non-numeric values on {mlast_nonnum} rows")

    if soft_drift and args.strict_baseline:
        errors.append(f"strict baseline: {len(soft_drift)} valuation/format drift rows")

    print(f"PUA rows checked: {len(pua_rows)} (NFO-terminated: {nfo_pua})")
    print(f"Other later-phase rows checked: {len(other_later)}")
    print(f"Baseline drift vs v57.85: date/age/status={len(hard_drift)} "
          f"valuation-sensitive={len(soft_drift)} -> {DRIFT_REPORT.name}")
    if mlast_deltas:
        print(f"  MLASTANN uniform shift: {sorted(mlast_deltas)} year(s) on "
              f"{sum(1 for d in soft_drift if d['FIELD'] == 'MLASTANN')} rows")

    if errors:
        print("FAIL")
        for e in errors:
            print(" ", e)
        return 1

    print("PASS — Issue #60 Track A PUA phase rules; NFO PUA terminated per #108D")
    if args.publish_test_validation:
        publish_test_validation(args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
