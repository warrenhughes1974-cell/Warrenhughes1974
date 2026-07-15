"""Read-only Issue #76 risk simulation: ETI/RPU phase-1 MPAYUP/MLASTANN."""
from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "QLA_Migration" / "Output"
EV = Path(__file__).resolve().parents[1] / "evidence"

SYS_YEAR = datetime.now().year
VAL_YEAR = 2025


def n(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def ymd(v: object) -> str:
    digits = "".join(c for c in n(v) if c.isdigit())
    return digits[:8] if len(digits) >= 8 else ""


def is_pua_plan(plan: object) -> bool:
    p = n(plan).upper()
    return p.endswith("PA") or "PUA" in p


def main() -> None:
    mstr = {
        n(r["MPOLICY"]): r
        for r in csv.DictReader(
            (OUT / "quikmstr.csv").open(newline="", encoding="utf-8", errors="replace")
        )
    }
    ridr = list(
        csv.DictReader(
            (OUT / "quikridr.csv").open(newline="", encoding="utf-8", errors="replace")
        )
    )

    rows_out: list[dict[str, str]] = []
    blank_paidto = 0
    for r in ridr:
        pol = n(r.get("MPOLICY"))
        phase = n(r.get("MPHASE"))
        m = mstr.get(pol)
        if not m:
            continue
        st = n(m.get("MSTATUS"))
        if st not in ("44", "45") or phase != "1":
            continue
        paidto = ymd(m.get("MPAIDTO"))
        payup = ymd(r.get("MPAYUP"))
        mlast = n(r.get("MLASTANN"))
        plan = n(r.get("MPLAN"))
        if not paidto:
            blank_paidto += 1
            continue
        new_payup = paidto
        new_mlast_sys = str(SYS_YEAR - int(new_payup[:4]))
        new_mlast_val = str(VAL_YEAR - int(new_payup[:4]))
        rows_out.append(
            {
                "MPOLICY": pol,
                "MSTATUS": st,
                "MPLAN": plan,
                "MEFFDATE": ymd(r.get("MEFFDATE")),
                "MPAIDTO": paidto,
                "MPAYUP_BEFORE": payup,
                "MPAYUP_AFTER": new_payup,
                "MLASTANN_BEFORE": mlast,
                "MLASTANN_AFTER_SYS": new_mlast_sys,
                "MLASTANN_AFTER_VAL": new_mlast_val,
                "PAYUP_CHANGED": "Y" if new_payup != payup else "N",
                "MLAST_CHANGED_SYS": "Y" if new_mlast_sys != mlast else "N",
                "IS_PUA_PLAN": "Y" if is_pua_plan(plan) else "N",
            }
        )

    EV.mkdir(parents=True, exist_ok=True)
    path = EV / "issue76_risk_phase1_simulation.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()) if rows_out else ["MPOLICY"])
        w.writeheader()
        w.writerows(rows_out)

    summary = EV / "issue76_risk_impact_summary.csv"
    with summary.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "count"])
        w.writerow(["sys_year", SYS_YEAR])
        w.writerow(["candidates_phase1_44_45_with_paidto", len(rows_out)])
        w.writerow(["blank_mpaidto_skipped", blank_paidto])
        w.writerow(["payup_changed", sum(1 for r in rows_out if r["PAYUP_CHANGED"] == "Y")])
        w.writerow(["mlastann_changed_sys", sum(1 for r in rows_out if r["MLAST_CHANGED_SYS"] == "Y")])
        w.writerow(["pua_plan_on_phase1", sum(1 for r in rows_out if r["IS_PUA_PLAN"] == "Y")])
        w.writerow(["status_44", sum(1 for r in rows_out if r["MSTATUS"] == "44")])
        w.writerow(["status_45", sum(1 for r in rows_out if r["MSTATUS"] == "45")])

    print(f"candidates={len(rows_out)} blank_paidto={blank_paidto}")
    print(
        "payup_chg",
        sum(1 for r in rows_out if r["PAYUP_CHANGED"] == "Y"),
        "mlast_chg",
        sum(1 for r in rows_out if r["MLAST_CHANGED_SYS"] == "Y"),
    )
    print("status", Counter(r["MSTATUS"] for r in rows_out))
    print("wrote", path)
    print("wrote", summary)


if __name__ == "__main__":
    main()
