"""Issue A A3 — default PVO member + key inventory."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
QP = ROOT / "QLA_Migration" / "Output" / "quikplan.csv"
RATES = ROOT / "QLA_Migration" / "Output" / "rates"
OUT = ROOT / "Issue_Log_Items" / "Issue_A" / "Reports" / "A3_pvo_default_inventory.csv"

MEMBER_TABLES = ("QuikPlGd", "QuikPlBd", "QuikPlUw", "QuikPlSt")
KEY_TABLES = ("QuikPlGp", "QuikPlDb", "QuikPlCv", "QuikPlTv", "QuikPlDv")


def load_plans() -> list[str]:
    with QP.open(newline="", encoding="utf-8-sig") as f:
        return [r["PLAN"].strip() for r in csv.DictReader(f) if (r.get("PLAN") or "").strip()]


def load_member_plans(table: str) -> dict[str, set[str]]:
    path = RATES / f"{table}.csv"
    if not path.is_file():
        return {}
    out: dict[str, set[str]] = defaultdict(set)
    with path.open(newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            plan = (r.get("PLAN") or "").strip()
            if plan:
                out[plan].add(table)
    return out


def load_key_plans(table: str) -> set[str]:
    path = RATES / f"{table}.csv"
    if not path.is_file():
        return set()
    plans = set()
    with path.open(newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            plan = (r.get("PLAN") or "").strip()
            if plan:
                plans.add(plan)
    return plans


def has_gp_rates(plan: str) -> bool:
    for t in ("QuikPlGp", "QuikGps"):
        p = RATES / f"{t}.csv"
        if not p.is_file():
            continue
        with p.open(newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if (r.get("PLAN") or "").strip() == plan:
                    return True
    return False


def main() -> None:
    plans = load_plans()
    member_by_plan: dict[str, set[str]] = defaultdict(set)
    for t in MEMBER_TABLES:
        for plan in load_key_plans(t):
            member_by_plan[plan].add(t)

    key_presence = {t: load_key_plans(t) for t in KEY_TABLES}

    rows = []
    missing_all_members = []
    missing_any_member = []
    no_keys_at_all = []

    for plan in sorted(plans):
        mem = member_by_plan.get(plan, set())
        missing_mem = [t for t in MEMBER_TABLES if t not in mem]
        keys_present = [t for t in KEY_TABLES if plan in key_presence[t]]
        gp = has_gp_rates(plan)
        if not mem:
            missing_all_members.append(plan)
        elif missing_mem:
            missing_any_member.append((plan, missing_mem))
        if not keys_present and not gp:
            no_keys_at_all.append(plan)
        rows.append(
            {
                "PLAN": plan,
                "member_tables": "|".join(sorted(mem)) or "",
                "missing_members": "|".join(missing_mem) or "",
                "key_tables": "|".join(keys_present) or "",
                "has_gp_rates": "Y" if gp else "N",
                "a3_gap": "Y" if missing_mem else "N",
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"plans: {len(plans)}")
    print(f"missing ALL 4 member tables: {len(missing_all_members)}")
    if missing_all_members:
        print(" ", ", ".join(missing_all_members))
    print(f"missing ANY member table: {sum(1 for r in rows if r['a3_gap']=='Y')}")
    print(f"no rate keys AND no GP rates: {len(no_keys_at_all)}")
    print(f"TESTRD in quikplan: {'TESTRD' in plans}")
    print(f"inventory: {OUT}")


if __name__ == "__main__":
    main()
