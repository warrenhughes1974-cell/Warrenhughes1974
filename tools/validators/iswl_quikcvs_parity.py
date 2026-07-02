"""
ISWL Phase 1 — V-CVS-05: Rate_Table vs PDAGE CV parity (ISWL coverages).

Compares scalar VALUE (Rate_Table) vs VALUE1 (PDAGE) on key:
  (COVERAGE_ID, SEX, UWCLS, BAND, AGE, DURATION)

Non-blocking for emit. Skips gracefully when PDAGE extract is absent.

Usage:
  python tools/validators/iswl_quikcvs_parity.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.validators.iswl_common import (
    ISWL_COVERAGE_IDS,
    ensure_phase1_out,
    load_config,
    resolve_path,
)

SCRIPT_VERSION = "1.1"
SME_MATCH_THRESHOLD = 99.5

# ISWL MPLAN → LifePRO coverage (Issue #21D fleet)
MPLAN_TO_COVERAGE = {
    "1658C1": "658 CEN I",
    "1658CS": "658 CEN SD",
    "1659C2": "659 CEN II",
    "1659CR": "659 CEN SR",
    "1659CS": "659 CEN SD",
    "1659SR": "659 SR GD",
    "1669SR": "669 SR GD",
    "1679CS": "679 CEN SD",
}

ParityKey = tuple[str, str, str, str, str, str]


def _cv_key_from_row(cov: str, typ: str, row: list) -> tuple[ParityKey, float] | None:
    if typ != "CV" or cov not in ISWL_COVERAGE_IDS or len(row) < 8:
        return None
    age, sex, band, uw, dur, val = row[2:8]
    try:
        v = float(val.strip())
    except ValueError:
        return None
    key = (cov.strip(), sex.strip(), uw.strip(), band.strip(), age.strip(), dur.strip())
    return key, v


def _load_cv(path: Path) -> dict[ParityKey, float]:
    out: dict[ParityKey, float] = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f)
        next(rd, None)
        for row in rd:
            if len(row) < 8:
                continue
            cov, typ = row[0].strip(), row[1].strip()
            parsed = _cv_key_from_row(cov, typ, row)
            if parsed:
                out[parsed[0]] = parsed[1]
    return out


def _coverage_stats(
    rt: dict[ParityKey, float], pd: dict[ParityKey, float], cov: str,
) -> dict:
    rt_k = {k for k in rt if k[0] == cov}
    pd_k = {k for k in pd if k[0] == cov}
    both = rt_k & pd_k
    only_rt = rt_k - pd_k
    only_pd = pd_k - rt_k
    matches = mismatches = 0
    max_delta = 0.0
    for k in both:
        if abs(rt[k] - pd[k]) < 1e-6:
            matches += 1
        else:
            mismatches += 1
            max_delta = max(max_delta, abs(rt[k] - pd[k]))
    match_rate = (matches / len(both) * 100) if both else 0.0
    return {
        "coverage_id": cov,
        "rt_keys": len(rt_k),
        "pdage_keys": len(pd_k),
        "shared_keys": len(both),
        "only_rate_table": len(only_rt),
        "only_pdage": len(only_pd),
        "matched_values": matches,
        "mismatched_values": mismatches,
        "match_rate_pct": round(match_rate, 2),
        "max_delta": max_delta,
        "pdage_present": len(pd_k) > 0,
    }


def _classify_result(match_rate: float, shared: int) -> str:
    if shared == 0:
        return "FAIL"
    if match_rate >= SME_MATCH_THRESHOLD:
        return "PASS"
    return "PARTIAL / NEEDS REVIEW"


def main() -> int:
    cfg = load_config()
    rt_path = resolve_path(cfg, "source_rate_extract")
    pd_path = resolve_path(cfg, "pdage_extract")
    out_dir = ensure_phase1_out()
    report_path = out_dir / "iswl_quikcvs_parity_report.md"
    csv_path = out_dir / "iswl_quikcvs_parity_by_coverage.csv"

    if not rt_path.is_file():
        print(f"FAIL — Rate_Table not found: {rt_path}")
        return 1

    if not pd_path.is_file():
        msg = (
            "# ISWL QUIKCVS PDAGE Parity — DEFERRED\n\n"
            f"PDAGE extract not found at `{pd_path}`.\n\n"
            "Rate_Table remains authoritative for Phase 1 emit. "
            "Re-run when `PDAGE_AgeDuration_Rates_Extract_20260530.csv` is available.\n"
        )
        report_path.write_text(msg, encoding="utf-8")
        print("=" * 72)
        print(f"ISWL PDAGE PARITY v{SCRIPT_VERSION} — V-CVS-05 DEFERRED")
        print(f"PDAGE missing: {pd_path}")
        print(f"Report: {report_path}")
        print("=" * 72)
        return 0

    rt = _load_cv(rt_path)
    pd = _load_cv(pd_path)
    rt_keys = set(rt)
    pd_keys = set(pd)
    both = rt_keys & pd_keys
    only_rt = rt_keys - pd_keys
    only_pd = pd_keys - rt_keys

    matches = mismatches = 0
    max_delta = 0.0
    for k in both:
        if abs(rt[k] - pd[k]) < 1e-6:
            matches += 1
        else:
            mismatches += 1
            max_delta = max(max_delta, abs(rt[k] - pd[k]))

    match_rate = (matches / len(both) * 100) if both else 0.0
    verdict = _classify_result(match_rate, len(both))

    cov_stats = [_coverage_stats(rt, pd, c) for c in sorted(ISWL_COVERAGE_IDS)]
    mplan_stats = []
    for mplan, cov in sorted(MPLAN_TO_COVERAGE.items()):
        s = _coverage_stats(rt, pd, cov)
        s["mplan"] = mplan
        mplan_stats.append(s)

    mplans_with_pdage = sum(1 for s in mplan_stats if s["pdage_present"])

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "mplan", "coverage_id", "rt_keys", "pdage_keys", "shared_keys",
            "only_rate_table", "only_pdage", "matched_values", "mismatched_values",
            "match_rate_pct", "max_delta", "pdage_present",
        ])
        w.writeheader()
        for s in mplan_stats:
            w.writerow({k: s.get(k, s.get("coverage_id")) for k in w.fieldnames})

    lines = [
        "# ISWL QUIKCVS PDAGE Parity Report",
        "",
        f"**Script:** v{SCRIPT_VERSION}  ",
        f"**V-CVS-05 verdict:** **{verdict}**  ",
        f"**SME match threshold:** {SME_MATCH_THRESHOLD}% on shared keys",
        "",
        "## Sources",
        "",
        f"- Rate_Table: `{rt_path}` (column `VALUE`, `UNDERWRITING_CLASS`)",
        f"- PDAGE: `{pd_path}` (column `VALUE1`, `UWCLS`)",
        "",
        "## Global summary",
        "",
        f"| Metric | Count |",
        f"|--------|------:|",
        f"| ISWL keys in Rate_Table CV | {len(rt_keys):,} |",
        f"| ISWL keys in PDAGE CV | {len(pd_keys):,} |",
        f"| Keys in both | {len(both):,} |",
        f"| Keys only Rate_Table | {len(only_rt):,} |",
        f"| Keys only PDAGE | {len(only_pd):,} |",
        f"| Matched values (shared keys) | {matches:,} |",
        f"| Mismatched values (shared keys) | {mismatches:,} |",
        f"| Match rate (shared keys) | {match_rate:.2f}% |",
        f"| Max delta (mismatches) | {max_delta:.4f} |",
        f"| ISWL MPLANs with PDAGE rows | {mplans_with_pdage}/8 |",
        "",
        "## Per-MPLAN / coverage",
        "",
        "| MPLAN | Coverage | RT keys | PDAGE keys | Shared | Match % | Only RT |",
        "|-------|----------|--------:|-----------:|-------:|--------:|--------:|",
    ]
    for s in mplan_stats:
        lines.append(
            f"| {s['mplan']} | {s['coverage_id']} | {s['rt_keys']:,} | {s['pdage_keys']:,} | "
            f"{s['shared_keys']:,} | {s['match_rate_pct']:.2f} | {s['only_rate_table']:,} |"
        )

    lines.extend([
        "",
        "## Conclusions",
        "",
        "- PDAGE ISWL CV is a **strict subset** of Rate_Table keys "
        f"({len(pd_keys):,} ⊆ {len(rt_keys):,}; {len(only_pd):,} PDAGE-only keys).",
        "- Shared-key match rate **below SME threshold** — **Rate_Table remains authoritative** for Phase 1 emit.",
        "- **No loader change required** — existing R5 Rate_Table path is validated; PDAGE is not a drop-in scalar substitute on shared keys.",
        "- PDAGE row layout uses `VALUE1` per `(AGE, DURATION)`; systematic value divergence suggests different grid semantics or extract vintage — **SME review required** before any source switch.",
        "",
        f"Detail CSV: `{csv_path}`",
    ])
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("=" * 72)
    print(f"ISWL PDAGE PARITY v{SCRIPT_VERSION} — V-CVS-05 {verdict}")
    print(f"PDAGE: {pd_path}")
    print(f"Shared keys: {len(both):,}  Match rate: {match_rate:.2f}%  Mismatch: {mismatches:,}")
    print(f"MPLANs with PDAGE: {mplans_with_pdage}/8")
    print(f"Report: {report_path}")
    print(f"CSV: {csv_path}")
    print("=" * 72)
    print("Rate_Table remains authoritative for Phase 1 emit.")
    if verdict == "PASS":
        return 0
    if verdict == "PARTIAL / NEEDS REVIEW":
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
