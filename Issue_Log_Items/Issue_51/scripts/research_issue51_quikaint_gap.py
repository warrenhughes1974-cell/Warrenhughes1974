"""
Issue #51 — read-only research: A60MIR / A96DAR missing QuikAint interest table.

Does NOT modify conversion code or outputs.
Writes evidence CSVs under Issue_Log_Items/Issue_51/evidence/.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1] / "evidence"
OUT.mkdir(parents=True, exist_ok=True)

TARGET_PLANS = ("A60MIR", "A96DAR")
LP_FORMS = {"863": "A60MIR", "896 DAR": "A96DAR"}


def _norm(row: dict) -> dict[str, str]:
    return {((k or "").strip()): ((v or "").strip()) for k, v in row.items()}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [_norm(r) for r in csv.DictReader(f)]


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main() -> None:
    quikplan = REPO / "QLA_Migration" / "Output" / "quikplan.csv"
    quikridr = REPO / "QLA_Migration" / "Output" / "quikridr.csv"
    ppben = REPO / "QLA_Migration" / "Source" / "PPBEN_PolicyBenefit_Extract_20260630.csv"
    quikaint_trace = (
        REPO / "plan_analysis" / "phase_r6_quikaint_rates" / "quikaint_emit_trace.csv"
    )
    rates_dir = REPO / "QLA_Migration" / "Output" / "rates"

    plan_rows = [r for r in _read_csv(quikplan) if r.get("PLAN") in TARGET_PLANS]
    ridr_rows = [r for r in _read_csv(quikridr) if r.get("MPLAN") in TARGET_PLANS]

    # QuikAint presence in load package
    rates_files = sorted(p.name for p in rates_dir.glob("*")) if rates_dir.is_dir() else []
    aint_in_rates = any(n.lower().startswith("quikaint") for n in rates_files)
    uint_path = rates_dir / "QuikUint.csv"
    uint_rows = _read_csv(uint_path) if uint_path.is_file() else []
    uint_targets = [r for r in uint_rows if r.get("MPLAN") in TARGET_PLANS]

    # PFSA QuikAint builder coverage
    aint_plans: set[str] = set()
    if quikaint_trace.is_file():
        aint_plans = {r.get("MPLAN", "") for r in _read_csv(quikaint_trace) if r.get("MPLAN")}

    # PPBEN FV_GUAR_RATE for LifePRO forms 863 / 896 DAR
    ppben_rows = []
    rate_counter: Counter[tuple[str, str]] = Counter()
    if ppben.is_file():
        for r in _read_csv(ppben):
            plan = r.get("PLAN_CODE", "")
            if plan not in LP_FORMS:
                continue
            qla = LP_FORMS[plan]
            rate = r.get("FV_GUAR_RATE", "")
            rate_counter[(qla, rate)] += 1
            ppben_rows.append(
                {
                    "POLICY_NUMBER": r.get("POLICY_NUMBER", ""),
                    "BENEFIT_SEQ": r.get("BENEFIT_SEQ", ""),
                    "BENEFIT_TYPE": r.get("BENEFIT_TYPE", ""),
                    "STATUS_CODE": r.get("STATUS_CODE", ""),
                    "STATUS_REASON": r.get("STATUS_REASON", ""),
                    "PLAN_CODE": plan,
                    "QLA_MPLAN": qla,
                    "FV_GUAR_RATE": rate,
                    "FV_BALANCE1": r.get("FV_BALANCE1", ""),
                    "FV_BALANCE2": r.get("FV_BALANCE2", ""),
                    "FV_GUAR_DEPOSITS": r.get("FV_GUAR_DEPOSITS", ""),
                }
            )

    # Evidence: plan catalog snapshot
    _write_csv(
        OUT / "issue51_quikplan_a_plans.csv",
        plan_rows,
        [
            "PLAN",
            "FORM",
            "DESCR",
            "PAR",
            "SEX",
            "BASIS",
            "NFOINT",
            "LOANINT",
            "LOANINTX",
            "DEPINT",
            "VARDB",
            "VARGP",
            "PLANTYPE",
        ],
    )

    # Evidence: rider population
    _write_csv(
        OUT / "issue51_quikridr_population.csv",
        ridr_rows,
        ["MPOLICY", "MPHASE", "MPHSTAT", "MPLAN", "MEFFDATE", "MEXPRY", "MUNITS", "MFACE"],
    )

    # Evidence: PPBEN interest/balance
    _write_csv(
        OUT / "issue51_ppben_fv_guar_rate.csv",
        ppben_rows,
        [
            "POLICY_NUMBER",
            "BENEFIT_SEQ",
            "BENEFIT_TYPE",
            "STATUS_CODE",
            "STATUS_REASON",
            "PLAN_CODE",
            "QLA_MPLAN",
            "FV_GUAR_RATE",
            "FV_BALANCE1",
            "FV_BALANCE2",
            "FV_GUAR_DEPOSITS",
        ],
    )

    # Evidence: QuikAint gap summary
    summary = [
        {
            "metric": "quikplan_A_star_plans",
            "value": str(len(plan_rows)),
            "notes": ",".join(TARGET_PLANS),
        },
        {
            "metric": "quikridr_rows_target_plans",
            "value": str(len(ridr_rows)),
            "notes": "all MPHSTAT=56 expected",
        },
        {
            "metric": "quikridr_active_mphstat_ne_56",
            "value": str(sum(1 for r in ridr_rows if r.get("MPHSTAT") != "56")),
            "notes": "",
        },
        {
            "metric": "quikridr_terminated_mphstat_56",
            "value": str(sum(1 for r in ridr_rows if r.get("MPHSTAT") == "56")),
            "notes": "",
        },
        {
            "metric": "output_rates_has_QuikAint",
            "value": "Y" if aint_in_rates else "N",
            "notes": ";".join(rates_files[:30]),
        },
        {
            "metric": "pfsa_quikaint_contains_A60MIR",
            "value": "Y" if "A60MIR" in aint_plans else "N",
            "notes": f"pfsa_mplan_count={len(aint_plans)}",
        },
        {
            "metric": "pfsa_quikaint_contains_A96DAR",
            "value": "Y" if "A96DAR" in aint_plans else "N",
            "notes": "",
        },
        {
            "metric": "quikuint_rows_total",
            "value": str(len(uint_rows)),
            "notes": "ISWL-only path; not fix for A-prefix riders",
        },
        {
            "metric": "quikuint_rows_target_plans",
            "value": str(len(uint_targets)),
            "notes": "",
        },
        {
            "metric": "ppben_863_896dar_rows",
            "value": str(len(ppben_rows)),
            "notes": "",
        },
        {
            "metric": "ppben_nonzero_fv_guar_rate",
            "value": str(
                sum(
                    1
                    for r in ppben_rows
                    if r.get("FV_GUAR_RATE")
                    and abs(float(r["FV_GUAR_RATE"].replace(",", "") or "0")) > 1e-9
                )
            ),
            "notes": "LifePRO authority for stub rate",
        },
    ]
    for (qla, rate), n in sorted(rate_counter.items()):
        summary.append(
            {
                "metric": f"ppben_rate_dist_{qla}",
                "value": str(n),
                "notes": f"FV_GUAR_RATE={rate}",
            }
        )

    # Proposed stub rows (documentation only — not written to Output)
    stubs = [
        {
            "MPLAN": "A60MIR",
            "MEFFDATE": "19000101",
            "MINTRATE": "0.0000",
            "MINTRATE1": "0.0000",
            "AUTHORITY": "PPBEN.FV_GUAR_RATE=.00 on all in-force 863 OR rows; crash-stop for PLAN-023",
        },
        {
            "MPLAN": "A96DAR",
            "MEFFDATE": "19000101",
            "MINTRATE": "0.0000",
            "MINTRATE1": "0.0000",
            "AUTHORITY": "PPBEN.FV_GUAR_RATE=.00 on all in-force 896 DAR OR rows; crash-stop for PLAN-023",
        },
    ]
    _write_csv(
        OUT / "issue51_proposed_quikaint_stubs.csv",
        stubs,
        ["MPLAN", "MEFFDATE", "MINTRATE", "MINTRATE1", "AUTHORITY"],
    )
    _write_csv(
        OUT / "issue51_gap_summary.csv",
        summary,
        ["metric", "value", "notes"],
    )

    print(f"Wrote evidence to {OUT}")
    for s in summary:
        print(f"  {s['metric']}={s['value']} {s['notes']}")


if __name__ == "__main__":
    main()
