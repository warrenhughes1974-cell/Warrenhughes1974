"""Read-only Discovery research for Issue #120 — group / list bill."""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "Source" / "PPOLC_PolicyMaster_Extract_20260630.csv"
MSTR = ROOT / "Output" / "quikmstr.csv"


def main() -> None:
    with SRC.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        src_rows = list(csv.DictReader(f))

    # Drop dashed header artifact rows
    def real(row: dict) -> bool:
        pol = str(row.get("POLICY_NUMBER", "")).strip()
        return bool(pol) and not set(pol) <= {"-", " "}

    src_rows = [r for r in src_rows if real(r)]
    grp = [r for r in src_rows if str(r.get("GROUP_NUMBER", "")).strip()]
    lst = [r for r in src_rows if str(r.get("BILLING_FORM", "")).strip().upper() == "LST"]

    status_cols = [c for c in (src_rows[0].keys() if src_rows else []) if "STATUS" in c.upper()]
    print("STATUS columns:", status_cols)
    print("GROUP_NUMBER policies:", len(grp))
    print("LST policies:", len(lst))
    print("Distinct groups:", len({str(r.get("GROUP_NUMBER", "")).strip() for r in grp}))

    # Status breakdown for group policies
    print("\n--- Group policies by status fields ---")
    for r in sorted(grp, key=lambda x: (str(x.get("GROUP_NUMBER", "")), str(x.get("POLICY_NUMBER", "")))):
        st = {c: str(r.get(c, "")).strip() for c in status_cols[:6]}
        plan = str(r.get("PLAN_CODE", r.get("BASE_PLAN", r.get("PRODUCT_CODE", "")))).strip()
        # try common plan fields
        plan_fields = [c for c in r.keys() if "PLAN" in c.upper()][:4]
        plans = {c: str(r.get(c, "")).strip() for c in plan_fields}
        print(
            f"{r.get('POLICY_NUMBER')} | G={r.get('GROUP_NUMBER')!s} | BF={r.get('BILLING_FORM')!s} | "
            f"st={st} | plans={plans}"
        )

    # Active-ish filter guesses
    print("\n--- Candidate 'active' filters ---")
    for col in status_cols:
        vals = Counter(str(r.get(col, "")).strip() for r in grp)
        print(f"  {col}: {vals.most_common(12)}")

    with MSTR.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        mrows = list(csv.DictReader(f))

    with_g = [r for r in mrows if str(r.get("MGROUP", "")).strip()]
    print("\n--- Output quikmstr ---")
    print("rows with MGROUP:", len(with_g))
    print("distinct MGROUP:", len({str(r.get("MGROUP", "")).strip() for r in with_g}))
    print("MBILLFRM counts:", Counter(str(r.get("MBILLFRM", "")).strip() for r in mrows).most_common(20))
    print("MBILLFRM=3:", sum(1 for r in mrows if str(r.get("MBILLFRM", "")).strip() == "3"))

    # Join source group policies to output (POLICY_NUMBER may need C suffix)
    src_pols = {str(r.get("POLICY_NUMBER", "")).strip() for r in grp}
    print("\n--- Join source groups to Output ---")
    matched = []
    for r in mrows:
        p = str(r.get("MPOLICY", "")).strip()
        bare = p[:-1] if p.endswith("C") else p
        if p in src_pols or bare in src_pols or (bare + "C") in {x + "C" for x in src_pols}:
            if bare in src_pols or p.rstrip("C") in src_pols or p in {x + "C" for x in src_pols}:
                matched.append(r)

    # cleaner match
    src_keys = set()
    for r in grp:
        p = str(r.get("POLICY_NUMBER", "")).strip()
        src_keys.add(p)
        src_keys.add(p + "C")
        if p.endswith("C"):
            src_keys.add(p[:-1])

    matched = [r for r in mrows if str(r.get("MPOLICY", "")).strip() in src_keys]
    print("matched Output rows for source group policies:", len(matched))
    for r in sorted(matched, key=lambda x: (str(x.get("MGROUP", "")), str(x.get("MPOLICY", "")))):
        print(
            f"{r.get('MPOLICY')} | MGROUP={r.get('MGROUP')!r} | MBILLFRM={r.get('MBILLFRM')!r} | "
            f"MSTATUS={r.get('MSTATUS')!r} | MMODE={r.get('MMODE')!r} | MBILLTO={r.get('MBILLTO')!r}"
        )

    missing = []
    out_keys = {str(r.get("MPOLICY", "")).strip() for r in mrows}
    out_keys |= {k[:-1] for k in out_keys if k.endswith("C")}
    for r in grp:
        p = str(r.get("POLICY_NUMBER", "")).strip()
        if p not in out_keys and (p + "C") not in {str(x.get("MPOLICY", "")).strip() for x in mrows}:
            missing.append(p)
    print("source group policies missing from Output:", missing)

    # LST in output vs source
    src_lst_keys = set()
    for r in lst:
        p = str(r.get("POLICY_NUMBER", "")).strip()
        src_lst_keys.add(p)
        src_lst_keys.add(p + "C")
    out_lst3 = [r for r in mrows if str(r.get("MBILLFRM", "")).strip() == "3"]
    print("\nOutput MBILLFRM=3:", len(out_lst3))
    out_lst_in_src = [r for r in out_lst3 if str(r.get("MPOLICY", "")).strip() in src_lst_keys]
    print("of which in source LST:", len(out_lst_in_src))
    orphan_lst3 = [r for r in out_lst3 if str(r.get("MPOLICY", "")).strip() not in src_lst_keys]
    print("MBILLFRM=3 not in source LST sample:", [r.get("MPOLICY") for r in orphan_lst3[:10]], "count", len(orphan_lst3))


if __name__ == "__main__":
    main()
