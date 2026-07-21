"""Extract Citizens Reserve file (cifi0007.DBF) to staging CSV."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cfic_crosswalk import decode_segmentation, load_crosswalk, resolve_ql_plan  # noqa: E402
from cfic_dbf_reader import load_dbf  # noqa: E402

ROOT = SCRIPT_DIR.parents[2]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))
from qla_core import rate_dbf_schema as S  # noqa: E402

RESERVE_DBF = ROOT / "docs" / "cifi0007.DBF"
PLANS_DBF = ROOT / "docs" / "cifi0004.dbf"
STAGING_ROOT = ROOT / "extracted_reserve" / "staging"

STAGING_FIELDS = [
    "cfic_plan",
    "ql_plan",
    "gender",
    "uwclass",
    "band",
    "issue_age",
    "policy_year",
    "cash_value",
    "pup_ins",
    "term_rsv",
    "mean_rsv",
    "rl_netprem",
    "fy_netprem",
    "death_ben",
    "source_file",
]


def load_plan_descriptions() -> dict[str, str]:
    if not PLANS_DBF.exists():
        return {}
    _, rows = load_dbf(PLANS_DBF)
    return {r["PL_PLAN"].strip().upper(): r.get("PL_DESC", "").strip() for r in rows}


def extract_plans(
    reserve_rows: list[dict[str, str]],
    plan_filter: set[str] | None,
    crosswalk: dict,
    descriptions: dict[str, str],
) -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = {}
    for row in reserve_rows:
        cfic = row["PLAN_CODE"].strip().upper()
        if plan_filter and cfic not in plan_filter:
            continue
        ql_plan, _ = resolve_ql_plan(cfic, crosswalk)
        gender, uwclass, band = decode_segmentation(cfic, descriptions.get(cfic, ""))
        try:
            iss_age = int(row["ISS_AGE"])
            pol_year = int(row["POL_YEAR"])
        except ValueError:
            continue
        if iss_age < 0 or pol_year < 1:
            continue
        if iss_age > S.MAX_AGE:
            continue  # junk ages (e.g. 272, 966) — do not cap into age 99 grid
        rec = {
            "cfic_plan": cfic,
            "ql_plan": ql_plan.strip(),
            "gender": gender,
            "uwclass": uwclass,
            "band": band,
            "issue_age": str(iss_age),
            "policy_year": str(pol_year),
            "cash_value": row.get("CASH_VALUE", ""),
            "pup_ins": row.get("PUP_INS", ""),
            "term_rsv": row.get("TERM_RSV", ""),
            "mean_rsv": row.get("MEAN_RSV", ""),
            "rl_netprem": row.get("RL_NETPREM", ""),
            "fy_netprem": row.get("FY_NETPREM", ""),
            "death_ben": row.get("DEATH_BEN", ""),
            "source_file": RESERVE_DBF.name,
        }
        out.setdefault(cfic, []).append(rec)

    # Source DBF occasionally has duplicate (issue_age, policy_year) rows — keep last.
    for cfic, rows in out.items():
        dedup: dict[tuple[str, str], dict[str, str]] = {}
        for rec in rows:
            dedup[(rec["issue_age"], rec["policy_year"])] = rec
        out[cfic] = list(dedup.values())

    return out


def write_staging(by_plan: dict[str, list[dict[str, str]]]) -> int:
    total = 0
    for cfic, rows in sorted(by_plan.items()):
        rows.sort(key=lambda r: (int(r["issue_age"]), int(r["policy_year"])))
        out_dir = STAGING_ROOT / cfic
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "reserve_grid.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=STAGING_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        total += len(rows)
        print(f"  {cfic}: {len(rows)} rows -> {path}")
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract cifi0007.DBF to staging CSV")
    parser.add_argument(
        "--plans",
        default="P7MN",
        help="Comma-separated CFIC plan codes (default P7MN). Use ALL for every plan in reserve.",
    )
    parser.add_argument("--dbf", default=str(RESERVE_DBF), help="Path to reserve DBF")
    args = parser.parse_args()

    dbf_path = Path(args.dbf)
    if not dbf_path.exists():
        raise SystemExit(f"Reserve DBF not found: {dbf_path}")

    _, reserve_rows = load_dbf(dbf_path)
    crosswalk = load_crosswalk()
    descriptions = load_plan_descriptions()

    if args.plans.strip().upper() == "ALL":
        plan_filter = None
    else:
        plan_filter = {p.strip().upper() for p in args.plans.split(",") if p.strip()}

    by_plan = extract_plans(reserve_rows, plan_filter, crosswalk, descriptions)
    if not by_plan:
        raise SystemExit("No rows extracted — check --plans filter")

    print(f"Extracting {len(by_plan)} plan(s) from {dbf_path.name}:")
    total = write_staging(by_plan)
    print(f"Wrote {total} staging rows under {STAGING_ROOT}")


if __name__ == "__main__":
    main()
