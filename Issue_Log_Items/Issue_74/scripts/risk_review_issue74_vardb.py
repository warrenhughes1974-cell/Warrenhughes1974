"""Read-only risk simulation for Issue #74 — VARDB 4 → 0 only.

Does not modify production mapping or Output.
Keeps structure codes 1/2/3 unchanged (Option B preserved).
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
QUIKPLAN = ROOT / "QLA_Migration" / "Output" / "quikplan.csv"
EVIDENCE = Path(__file__).resolve().parents[1] / "evidence"


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    with QUIKPLAN.open(newline="", encoding="utf-8", errors="replace") as f:
        rows = list(csv.DictReader(f))

    sim: list[dict[str, str]] = []
    for r in rows:
        before = (r.get("VARDB") or "").strip()
        after = "0" if before == "4" else before
        sim.append(
            {
                "PLAN": (r.get("PLAN") or "").strip(),
                "VARDB_before": before,
                "VARDB_after": after,
                "changed": "Y" if before != after else "N",
                "VARGP": (r.get("VARGP") or "").strip(),
                "PRODUCT": (r.get("PRODUCT") or "").strip(),
                "PLANTYPE": (r.get("PLANTYPE") or "").strip(),
                "DESCR": (r.get("DESCR") or "").strip()[:60],
            }
        )

    before_c = Counter(s["VARDB_before"] for s in sim)
    after_c = Counter(s["VARDB_after"] for s in sim)
    changed = sum(1 for s in sim if s["changed"] == "Y")
    kept = len(sim) - changed

    summary = EVIDENCE / "issue74_risk_impact_summary.csv"
    with summary.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "count"])
        w.writerow(["quikplan_rows", len(sim)])
        for k, v in sorted(before_c.items()):
            w.writerow([f"VARDB_before_{k or 'BLANK'}", v])
        for k, v in sorted(after_c.items()):
            w.writerow([f"VARDB_after_{k or 'BLANK'}", v])
        w.writerow(["would_change_4_to_0", changed])
        w.writerow(["unchanged_structure_1_2_3", kept])
        w.writerow(["residual_VARDB_4_after_target", 0])

    sim_path = EVIDENCE / "issue74_risk_vardb_simulation.csv"
    with sim_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(sim[0].keys()))
        w.writeheader()
        w.writerows(sim)

    keeps = [s for s in sim if s["changed"] == "N"]
    keep_path = EVIDENCE / "issue74_risk_structure_plans_unchanged.csv"
    with keep_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(keeps[0].keys()))
        w.writeheader()
        w.writerows(keeps)

    print(f"rows={len(sim)} changed={changed} kept={kept}")
    print(f"before={dict(before_c)} after={dict(after_c)}")
    print(f"wrote {summary}")
    print(f"wrote {sim_path}")
    print(f"wrote {keep_path}")


if __name__ == "__main__":
    main()
