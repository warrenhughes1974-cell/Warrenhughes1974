"""Issue A A2 — read-only deficiency (Calc Dfcy) fleet inventory."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
QP = ROOT / "QLA_Migration" / "Output" / "quikplan.csv"
OUT = ROOT / "Issue_Log_Items" / "Issue_A" / "Reports" / "A2_deficiency_inventory.csv"

# Heuristic indeterminate-premium markers (awaiting CSO authoritative list)
INDET_KEYWORDS = (
    "INTEREST-SENSITIVE",
    "ISWL",
    "UNIVERSAL",
    "FLEXIBLE",
    "INDETERMINATE",
    "VARIABLE",
)


def is_indeterminate_heuristic(descr: str) -> bool:
    u = (descr or "").upper()
    return any(k in u for k in INDET_KEYWORDS)


def deficiency_applies(plan: str) -> bool:
    if not plan:
        return False
    first = plan[0].upper()
    return first.isalpha() or first == "9"


def main() -> None:
    rows = list(csv.DictReader(QP.open(newline="", encoding="utf-8-sig")))
    OUT.parent.mkdir(parents=True, exist_ok=True)

    inv = []
    for r in rows:
        plan = r.get("PLAN", "")
        indet = is_indeterminate_heuristic(r.get("DESCR", ""))
        inv.append(
            {
                "PLAN": plan,
                "DESCR": r.get("DESCR", ""),
                "DEFICIENCY": r.get("DEFICIENCY", ""),
                "PRODUCT": r.get("PRODUCT", ""),
                "PAYYRS": r.get("PAYYRS", ""),
                "PAYAGE": r.get("PAYAGE", ""),
                "indeterminate_heuristic": "Y" if indet else "N",
                "dg020_applies": "Y" if deficiency_applies(plan) else "N",
                "a2_candidate_if_cso_yes": "Y" if not indet else "N",
            }
        )

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(inv[0].keys()))
        w.writeheader()
        w.writerows(inv)

    total = len(inv)
    indet_n = sum(1 for x in inv if x["indeterminate_heuristic"] == "Y")
    cand_n = total - indet_n
    def_n = sum(1 for x in inv if (x["DEFICIENCY"] or "").strip().upper() == "N")
    dg020 = sum(1 for x in inv if x["dg020_applies"] == "Y")

    print(f"quikplan rows: {total}")
    print(f"DEFICIENCY=N today: {def_n}/{total}")
    print(f"Indeterminate (DESCR heuristic): {indet_n}")
    print(f"A2 candidates if CSO says yes (non-indet heuristic): {cand_n}")
    print(f"Plans where DG-QUIKPLAN-020 applies (A/9 prefix): {dg020}")
    print(f"Inventory: {OUT}")
    print("\nIndeterminate heuristic plans:")
    for x in inv:
        if x["indeterminate_heuristic"] == "Y":
            print(f"  {x['PLAN']}: {x['DESCR']}")


if __name__ == "__main__":
    main()
