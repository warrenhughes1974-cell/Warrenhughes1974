"""
Issue #95 — Independent QuikUint / PDINTTBL declared-interest validation.

Oracle is computed from PDINTTBL + quikplan + Eric bucket rules.
Does NOT call qla_core.quikuint_loader for expected rates/membership.

Usage:
  python tools/validators/validate_issue95_quikuint_pdinttbl.py
  python tools/validators/validate_issue95_quikuint_pdinttbl.py --publish-test-validation
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qla_core.cso_mortality_crosswalk import ISWL_MPLAN_ALLOWLIST  # noqa: E402
from qla_core.valuation_date import apply_valuation_date_env  # noqa: E402

SCRIPT_VERSION = "1.1"
SOURCE_ROOT = PROJECT_ROOT / "QLA_Migration" / "Source"
QUIKPLAN = PROJECT_ROOT / "QLA_Migration" / "Output" / "quikplan.csv"
QUIKUINT = PROJECT_ROOT / "QLA_Migration" / "Output" / "rates" / "QuikUint.csv"
QUIKAINT = PROJECT_ROOT / "QLA_Migration" / "Output" / "rates" / "QuikAint.csv"
EVIDENCE = PROJECT_ROOT / "Issue_Log_Items" / "Issue_95" / "evidence"
BASELINE = EVIDENCE / "issue95_prechange_baseline.json"
TEST_VALIDATION = PROJECT_ROOT / "QLA_Migration" / "Output" / "Test_Validation" / "rates"


def resolve_pdinttbl(source_root: Path, valuation_date: str) -> Path:
    """Resolve PDINTTBL for the active valuation date (Source root or dated package folder)."""
    vd = "".join(c for c in valuation_date if c.isdigit())[:8]
    name = f"PDINTTBL_DeclaredInterestRates_Extract_{vd}.csv"
    candidates = [
        source_root / name,
        source_root / f"LifePRO_Extracts_{vd}" / name,
    ]
    for path in candidates:
        if path.is_file():
            return path
    matches = sorted(source_root.rglob(name))
    if matches:
        return matches[-1]
    raise FileNotFoundError(
        f"PDINTTBL extract missing for QLA_VALUATION_DATE={vd}: "
        f"expected {candidates[0]} or {candidates[1]}"
    )

RATE_450 = frozenset(
    {
        "1668SP",
        "1669SR",
        "1658C1",
        "1658CS",
        "1659C2",
        "1659CR",
        "1659CS",
        "1659SR",
        "1679CS",
    }
)
RATE_200 = frozenset({"1SALOL", "1SALML"})
CENII_ISWL = frozenset(
    {
        "1658C1",
        "1658CS",
        "1659C2",
        "1659CR",
        "1659CS",
        "1659SR",
        "1669SR",
        "1679CS",
    }
)
EXPECTED_UNION = {
    "19800101": "11.0000",
    "19890101": "9.0000",
    "19990101": "5.0000",
    "20020101": "4.5000",
}
ERIC_CURRENT = {
    "CENII": "4.5000",
    "SPWL": "4.5000",
    "SAL01": "2.0000",
    "DAR01": "3.5000",
    "DIV01": "3.5000",
    "IBA01": "3.5000",
    "L1001": "3.5000",
}


def _s(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def _norm_row(d: dict) -> dict[str, str]:
    return {k.strip(): _s(v) for k, v in d.items()}


def _fmt_rate(v: str) -> str:
    try:
        return f"{float(v):.4f}"
    except ValueError:
        return _s(v)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [_norm_row(r) for r in csv.DictReader(f)]


def oracle_pdinttbl_current(path: Path) -> dict[str, dict[str, str]]:
    """Independent current-tier oracle: max START_DATE per IDENT (then DINT_RULE)."""
    by_ident: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in _load_csv(path):
        ident = r.get("IDENT", "")
        if not ident or ident == "-----":
            continue
        start = r.get("START_DATE", "")
        if len(start) != 8:
            continue
        by_ident[ident].append(r)
    out: dict[str, dict[str, str]] = {}
    for ident, rows in by_ident.items():
        cur = max(rows, key=lambda x: (x.get("START_DATE", ""), x.get("DINT_RULE", "")))
        out[ident] = {
            "START_DATE": cur["START_DATE"],
            "END_DATE": cur.get("END_DATE", ""),
            "DECLARED_RATE": _fmt_rate(cur.get("DECLARED_RATE", "")),
            "TYPE_CODE": cur.get("TYPE_CODE", ""),
            "DINT_RULE": cur.get("DINT_RULE", ""),
        }
    return out


def oracle_cenii_union(path: Path) -> dict[str, str]:
    """Independent CENII A1 union_merge (rules 0+3; tie-break prefer 3)."""
    by_start: dict[str, dict[str, str]] = {}
    for r in _load_csv(path):
        if r.get("IDENT") != "CENII" or r.get("TYPE_CODE") != "A1":
            continue
        rule = r.get("DINT_RULE", "")
        if rule not in ("0", "3"):
            continue
        start = r.get("START_DATE", "")
        if len(start) != 8:
            continue
        existing = by_start.get(start)
        if existing is None or rule == "3":
            by_start[start] = {
                "START_DATE": start,
                "DECLARED_RATE": _fmt_rate(r.get("DECLARED_RATE", "")),
                "DINT_RULE": rule,
            }
    return {k: by_start[k]["DECLARED_RATE"] for k in sorted(by_start)}


def oracle_membership(plans: set[str]) -> dict[str, object]:
    residual = {
        p
        for p in plans
        if p not in RATE_450
        and p not in RATE_200
        and not p.startswith("9")
        and not p.startswith("A")
    }
    excluded_9 = {
        p for p in plans if p not in RATE_450 and p not in RATE_200 and p.startswith("9")
    }
    excluded_a = {
        p for p in plans if p not in RATE_450 and p not in RATE_200 and p.startswith("A")
    }
    expected_rate: dict[str, str] = {}
    for p in RATE_450 & plans:
        expected_rate[p] = "4.5000"
    for p in RATE_200 & plans:
        expected_rate[p] = "2.0000"
    for p in residual:
        expected_rate[p] = "3.5000"
    return {
        "plans": sorted(plans),
        "rate_450": sorted(RATE_450 & plans),
        "rate_200": sorted(RATE_200 & plans),
        "residual_safe": sorted(residual),
        "excluded_9": sorted(excluded_9),
        "excluded_a": sorted(excluded_a),
        "expected_rate": expected_rate,
        "expected_distinct_mplans": len(expected_rate),
        # 8 ISWL × 4 history + 1 SPWL + 2 SAL + residual current-only
        "expected_rows": (len(CENII_ISWL & plans) * 4)
        + (1 if "1668SP" in plans else 0)
        + len(RATE_200 & plans)
        + len(residual),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Issue #95 QuikUint buckets")
    ap.add_argument("--publish-test-validation", action="store_true")
    ap.add_argument("--quikuint", type=Path, default=QUIKUINT)
    ap.add_argument(
        "--valuation-date",
        default="",
        help="YYYYMMDD override (default: QLA_VALUATION_DATE / active PPOLC)",
    )
    ap.add_argument(
        "--pdinttbl",
        type=Path,
        default=None,
        help="Optional explicit PDINTTBL path (default: resolve from valuation date)",
    )
    args = ap.parse_args()

    try:
        valuation_date, val_src = apply_valuation_date_env(
            SOURCE_ROOT,
            explicit=args.valuation_date or None,
        )
    except ValueError as exc:
        print(f"FAIL: valuation date unresolved: {exc}")
        return 1

    try:
        pdinttbl = args.pdinttbl if args.pdinttbl else resolve_pdinttbl(SOURCE_ROOT, valuation_date)
    except FileNotFoundError as exc:
        print(f"FAIL: {exc}")
        return 1

    print(f"validate_issue95_quikuint_pdinttbl.py v{SCRIPT_VERSION}")
    print(f"valuation_date={valuation_date} ({val_src})")
    print(f"pdinttbl={pdinttbl}")
    print(f"quikuint={args.quikuint}")

    fails: list[str] = []
    checks: dict[str, bool] = {}

    if not pdinttbl.is_file():
        print(f"FAIL: PDINTTBL extract missing: {pdinttbl}")
        return 1
    if not QUIKPLAN.is_file():
        print("FAIL: quikplan.csv missing")
        return 1
    if not args.quikuint.is_file():
        print(f"FAIL: QuikUint missing: {args.quikuint}")
        return 1

    current = oracle_pdinttbl_current(pdinttbl)
    # R-95-01 source vs Eric
    r9501 = True
    for ident, exp in ERIC_CURRENT.items():
        got = current.get(ident, {}).get("DECLARED_RATE")
        if got != exp:
            r9501 = False
            fails.append(f"R-95-01 {ident}: source current {got} != Eric {exp}")
    checks["R-95-01"] = r9501

    plans = {r.get("PLAN", "") for r in _load_csv(QUIKPLAN) if r.get("PLAN")}
    mem = oracle_membership(plans)
    expected_rate: dict[str, str] = mem["expected_rate"]  # type: ignore[assignment]

    uint_rows = _load_csv(args.quikuint)
    fields = list(uint_rows[0].keys()) if uint_rows else []
    schema_ok = fields == ["MPLAN", "MEFFDATE", "MGTDRATE", "MCURRATE"]
    if not schema_ok:
        fails.append(f"R-95-05 schema {fields}")
    keys = [(r.get("MPLAN"), r.get("MEFFDATE")) for r in uint_rows]
    dupes = len(keys) - len(set(keys))
    mirror_bad = sum(
        1 for r in uint_rows if r.get("MGTDRATE") != r.get("MCURRATE")
    )
    checks["R-95-05"] = schema_ok and dupes == 0 and mirror_bad == 0
    if dupes:
        fails.append(f"R-95-05 duplicate keys={dupes}")
    if mirror_bad:
        fails.append(f"R-95-05 MGTDRATE!=MCURRATE rows={mirror_bad}")

    by_plan: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in uint_rows:
        by_plan[r.get("MPLAN", "")].append(r)

    # R-95-02 current rate per expected plan
    wrong_current: list[str] = []
    missing_plans: list[str] = []
    for plan, exp_rate in sorted(expected_rate.items()):
        rows = by_plan.get(plan, [])
        if not rows:
            missing_plans.append(plan)
            continue
        cur = max(rows, key=lambda x: x.get("MEFFDATE", ""))
        got = _fmt_rate(cur.get("MCURRATE", ""))
        if got != exp_rate:
            wrong_current.append(f"{plan}:{got}!={exp_rate}")
    checks["R-95-02"] = not missing_plans and not wrong_current
    if missing_plans:
        fails.append(f"R-95-02 missing MPLANs ({len(missing_plans)}): {missing_plans[:8]}")
    if wrong_current:
        fails.append(f"R-95-02 wrong current rates: {wrong_current[:8]}")

    # R-95-03 CENII history for 8 ISWL
    union = oracle_cenii_union(pdinttbl)
    cenii_ok = union == EXPECTED_UNION
    for plan in sorted(CENII_ISWL):
        rows = by_plan.get(plan, [])
        got_map = {r.get("MEFFDATE"): _fmt_rate(r.get("MCURRATE", "")) for r in rows}
        if got_map != EXPECTED_UNION:
            cenii_ok = False
            fails.append(f"R-95-03 schedule mismatch {plan}: {got_map}")
            break
        if any(r.get("MGTDRATE") != r.get("MCURRATE") for r in rows):
            cenii_ok = False
            fails.append(f"R-95-03 mirror fail {plan}")
            break
    checks["R-95-03"] = cenii_ok

    # R-95-04 allowlist freeze
    allow_ok = (
        len(ISWL_MPLAN_ALLOWLIST) == 8
        and "1668SP" not in ISWL_MPLAN_ALLOWLIST
        and ISWL_MPLAN_ALLOWLIST == CENII_ISWL
    )
    checks["R-95-04"] = allow_ok
    if not allow_ok:
        fails.append(
            f"R-95-04 ISWL_MPLAN_ALLOWLIST n={len(ISWL_MPLAN_ALLOWLIST)} "
            f"has_1668SP={'1668SP' in ISWL_MPLAN_ALLOWLIST}"
        )

    # R-95-06 exclusions
    bad_excl = sorted(
        p for p in by_plan if p.startswith("9") or p.startswith("A")
    )
    checks["R-95-06"] = not bad_excl
    if bad_excl:
        fails.append(f"R-95-06 excluded plans present: {bad_excl[:10]}")

    # R-95-08 1668SP SPWL current-only (not CENII historical date set)
    spwl_rows = by_plan.get("1668SP", [])
    spwl_cur = current.get("SPWL", {})
    spwl_dates = {r.get("MEFFDATE") for r in spwl_rows}
    r9508 = (
        len(spwl_rows) == 1
        and spwl_rows[0].get("MEFFDATE") == spwl_cur.get("START_DATE")
        and _fmt_rate(spwl_rows[0].get("MCURRATE", "")) == "4.5000"
        and spwl_dates != set(EXPECTED_UNION.keys())
    )
    checks["R-95-08"] = bool(r9508)
    if not r9508:
        fails.append(
            f"R-95-08 1668SP rows={len(spwl_rows)} "
            f"dates={[r.get('MEFFDATE') for r in spwl_rows]} "
            f"expect SPWL start={spwl_cur.get('START_DATE')}"
        )

    # Non-ISWL current-only (A-HIST)
    multi_tier_non_iswl = [
        p
        for p, rows in by_plan.items()
        if p not in CENII_ISWL and len(rows) != 1
    ]
    a_hist_ok = not multi_tier_non_iswl
    if multi_tier_non_iswl:
        fails.append(f"A-HIST multi-tier non-ISWL: {multi_tier_non_iswl[:8]}")

    # Counts
    row_count = len(uint_rows)
    mplan_count = len(by_plan)
    expected_rows = int(mem["expected_rows"])  # type: ignore[arg-type]
    expected_mplans = int(mem["expected_distinct_mplans"])  # type: ignore[arg-type]
    counts_ok = row_count == expected_rows and mplan_count == expected_mplans
    if not counts_ok:
        fails.append(
            f"counts rows={row_count} expect={expected_rows}; "
            f"mplans={mplan_count} expect={expected_mplans}"
        )

    # R-95-07 non-impact spot checks (presence / stable stubs)
    aint_ok = True
    aint_detail = {}
    if QUIKAINT.is_file():
        aint_rows = _load_csv(QUIKAINT)
        aint_plans = {
            r.get("PLAN") or r.get("MPLAN") or "" for r in aint_rows
        }
        aint_detail = {"rows": len(aint_rows), "plans": sorted(p for p in aint_plans if p)}
        if not ({"A60MIR", "A96DAR"} <= aint_plans or {"A60MIR", "A96DAR"} <= set(by_plan)):
            # QuikAint should still carry annuity stubs; they must not move to QuikUint
            if "A60MIR" in by_plan or "A96DAR" in by_plan:
                aint_ok = False
                fails.append("R-95-07 annuity plans leaked into QuikUint")
        if "A60MIR" not in aint_plans or "A96DAR" not in aint_plans:
            # warn but do not fail if QuikAint schema uses different key — check row count > 0
            if len(aint_rows) == 0:
                aint_ok = False
                fails.append("R-95-07 QuikAint empty")
    else:
        aint_ok = False
        fails.append("R-95-07 QuikAint missing")
    checks["R-95-07"] = aint_ok and "1668SP" not in ISWL_MPLAN_ALLOWLIST

    # Baseline compare for CENII 32-row schedule if baseline present
    baseline_cenii_ok = True
    baseline_meta = {}
    if BASELINE.is_file():
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
        baseline_meta = {
            "pre_rows": baseline.get("quikuint_detail", {}).get("row_count"),
            "pre_sha256": baseline.get("quikuint", {}).get("sha256"),
        }
        pre_sched = baseline.get("quikuint_detail", {}).get("issue32_cenii_schedule_by_mplan", {})
        for plan in sorted(CENII_ISWL):
            pre = {
                d: {
                    "MGTDRATE": _fmt_rate(v.get("MGTDRATE", "")),
                    "MCURRATE": _fmt_rate(v.get("MCURRATE", "")),
                }
                for d, v in (pre_sched.get(plan) or {}).items()
            }
            now = {
                r.get("MEFFDATE"): {
                    "MGTDRATE": _fmt_rate(r.get("MGTDRATE", "")),
                    "MCURRATE": _fmt_rate(r.get("MCURRATE", "")),
                }
                for r in by_plan.get(plan, [])
            }
            if pre and pre != now:
                baseline_cenii_ok = False
                fails.append(f"baseline CENII drift {plan}")
                break

    # Sample traces
    traces = {}
    for plan in ("1659C2", "1669SR", "1668SP", "1SALOL", "1SALML", "1SALMI", "1L1095", "9ADB10", "A96DAR"):
        rows = by_plan.get(plan, [])
        if not rows:
            traces[plan] = {"present": False}
        else:
            cur = max(rows, key=lambda x: x.get("MEFFDATE", ""))
            traces[plan] = {
                "present": True,
                "tiers": len(rows),
                "MEFFDATE": cur.get("MEFFDATE"),
                "MCURRATE": _fmt_rate(cur.get("MCURRATE", "")),
                "MGTDRATE": _fmt_rate(cur.get("MGTDRATE", "")),
            }

    # Reconcile matrix counts
    source_accepted = len(expected_rate)
    excluded = len(mem["excluded_9"]) + len(mem["excluded_a"])  # type: ignore[arg-type]
    emitted = mplan_count
    reconcile = {
        "source_plans_quikplan": len(plans),
        "accepted_for_quikuint": source_accepted,
        "excluded_rider_annuity": excluded,
        "emitted_mplans": emitted,
        "emitted_rows": row_count,
        "duplicate_keys": dupes,
        "missing_vs_accepted": missing_plans,
        "extra_vs_accepted": sorted(set(by_plan) - set(expected_rate)),
        "differences_investigated": {
            "missing_count": len(missing_plans),
            "wrong_current_count": len(wrong_current),
            "extra_count": len(set(by_plan) - set(expected_rate)),
        },
    }
    if reconcile["extra_vs_accepted"]:
        fails.append(f"extra MPLANs not in oracle: {reconcile['extra_vs_accepted'][:8]}")

    passed = (
        len(fails) == 0
        and counts_ok
        and a_hist_ok
        and baseline_cenii_ok
        and all(checks.get(k) for k in (
            "R-95-01", "R-95-02", "R-95-03", "R-95-04",
            "R-95-05", "R-95-06", "R-95-07", "R-95-08",
        ))
    )

    published = False
    if passed and args.publish_test_validation:
        TEST_VALIDATION.mkdir(parents=True, exist_ok=True)
        dest = TEST_VALIDATION / "QuikUint.csv"
        shutil.copy2(args.quikuint, dest)
        published = True
        print(f"Published Test_Validation: {dest}")

    summary = {
        "script_version": SCRIPT_VERSION,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "valuation_date": valuation_date,
        "valuation_source": val_src,
        "pdinttbl_path": str(pdinttbl),
        "verdict": "PASS" if passed else "FAIL",
        "checks": checks,
        "a_hist_current_only_non_iswl": a_hist_ok,
        "baseline_cenii_preserved": baseline_cenii_ok,
        "counts": {
            "quikuint_rows": row_count,
            "distinct_mplans": mplan_count,
            "expected_rows": expected_rows,
            "expected_mplans": expected_mplans,
        },
        "pdinttbl_current_oracle": current,
        "cenii_union_oracle": union,
        "membership": {
            "rate_450": mem["rate_450"],
            "rate_200": mem["rate_200"],
            "residual_safe_count": len(mem["residual_safe"]),  # type: ignore[arg-type]
            "excluded_9_count": len(mem["excluded_9"]),  # type: ignore[arg-type]
            "excluded_a_count": len(mem["excluded_a"]),  # type: ignore[arg-type]
        },
        "reconcile": reconcile,
        "traces": traces,
        "quikaint_spot": aint_detail,
        "baseline_meta": baseline_meta,
        "quikuint_sha256": _sha256(args.quikuint),
        "iswl_allowlist_size": len(ISWL_MPLAN_ALLOWLIST),
        "1668SP_in_iswl_allowlist": "1668SP" in ISWL_MPLAN_ALLOWLIST,
        "published_test_validation": published,
        "fails": fails,
    }

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    out_json = EVIDENCE / "issue95_quikuint_reconcile.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (EVIDENCE / "issue95_validation_summary.json").write_text(
        json.dumps(
            {
                "verdict": summary["verdict"],
                "counts": summary["counts"],
                "checks": summary["checks"],
                "fails": fails,
                "published_test_validation": published,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 72)
    print(f"Issue #95 QuikUint validation — {summary['verdict']}")
    print(
        f"rows={row_count} (expect {expected_rows}) "
        f"mplans={mplan_count} (expect {expected_mplans})"
    )
    for cid in sorted(checks):
        print(f"  {cid}: {'PASS' if checks[cid] else 'FAIL'}")
    print(f"  A-HIST non-ISWL current-only: {'PASS' if a_hist_ok else 'FAIL'}")
    print(f"  baseline CENII preserved: {'PASS' if baseline_cenii_ok else 'FAIL'}")
    print(f"evidence: {out_json}")
    if fails:
        print("FAIL detail:")
        for f in fails[:20]:
            print(f"  - {f}")
        return 1
    print("PASS — Issue #95 QuikUint / PDINTTBL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
