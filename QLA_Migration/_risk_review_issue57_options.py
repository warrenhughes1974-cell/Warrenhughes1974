"""Issue #57 Risk — Option A (translation only) vs B (+ remove PAID_UP_TYPE→MNFOPT)."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PPBENTYP = ROOT / "QLA_Migration" / "Source" / "PPBENTYP_BenefitType_Extract_20260630.csv"
PPOLC = ROOT / "QLA_Migration" / "Source" / "PPOLC_PolicyMaster_Extract_20260630.csv"
CROSSWALK = ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"
QUIKMSTR = ROOT / "QLA_Migration" / "Output" / "quikmstr.csv"
OUT = ROOT / "Issue_Log_Items" / "Issue_57" / "evidence" / "issue57_risk_options.csv"

PROP_LP = {"0": "0", "1": "1", "2": "1", "3": "1", "4": "2", "5": "3", "6": "0", "7": "0", "8": "0", "9": "0", "": "0"}
PUT_MAP = {"LE": "2", "ET": "2", "RU": "3", "PU": "0", "LP": "0", "SP": "0"}


def seq1(v: str) -> bool:
    try:
        return int(float((v or "").strip())) == 1
    except Exception:
        return False


def effective_nfo(row: dict[str, str]) -> str:
    tc = (row.get("TYPE_CODE") or "").strip()
    nf = (row.get("NON_FORFEITURE") or "").strip().replace(".0", "")
    bnf = (row.get("BF_NON_FORFEITURE") or "").strip().replace(".0", "")
    if tc == "BF" and bnf != "":
        return bnf
    return nf


def option_a(lp: str, put: str) -> str:
    """Translation fix only; PAID_UP_TYPE still last-write when non-blank."""
    # NFO_OPT path then PUT overwrite
    nfo = PROP_LP.get(lp, "0")
    if put:
        return PUT_MAP.get(put, "0")
    return nfo


def option_b(lp: str, put: str) -> str:
    """Translation fix + ignore PAID_UP_TYPE for MNFOPT (PPBENTYP authority)."""
    return PROP_LP.get(lp, "0")


def main() -> None:
    cw = {}
    with CROSSWALK.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            o = (row.get("Old_Value") or "").strip()
            n = (row.get("New_Value") or "").strip()
            if o and n:
                cw[o] = n

    mstr = {}
    with QUIKMSTR.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            mstr[(row.get("MPOLICY") or "").strip()] = (row.get("MNFOPT") or "").strip() or "0"

    put_by = {}
    with PPOLC.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            put_by[(row.get("POLICY_NUMBER") or "").strip()] = (row.get("PAID_UP_TYPE") or "").strip()

    by = {}
    with PPBENTYP.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            if not seq1(row.get("BENEFIT_SEQ", "")):
                continue
            pol = (row.get("POLICY_NUMBER") or "").strip()
            eff = effective_nfo(row)
            tc = (row.get("TYPE_CODE") or "").strip()
            prev = by.get(pol)
            if prev is None:
                by[pol] = eff
            elif tc == "BF" and eff != "":
                by[pol] = eff
            elif prev == "" and eff != "":
                by[pol] = eff

    rows = []
    for lp, eff in by.items():
        q = cw.get(lp)
        if not q or q not in mstr:
            continue
        put = put_by.get(lp, "")
        before = mstr[q]
        a = option_a(eff, put)
        b = option_b(eff, put)
        rows.append(
            {
                "MPOLICY": q,
                "LIFEPRO": lp,
                "LP_CODE": eff,
                "PAID_UP_TYPE": put,
                "BEFORE": before,
                "OPT_A": a,
                "OPT_B": b,
                "A_CHANGED": "Y" if before != a else "N",
                "B_CHANGED": "Y" if before != b else "N",
                "ERIC_ETI": "Y" if q in ("010367131C", "010148272C", "010143726C") else "",
                "ERIC_RPU": "Y" if q == "010392763C" else "",
                "ERIC_APL": "Y" if q == "011221309C" else "",
            }
        )

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    def summarize(label: str, key: str) -> None:
        ch = [r for r in rows if r[key] == "Y"]
        after_key = "OPT_A" if "A_" in key else "OPT_B"
        print(f"\n=== {label} ===")
        print(f"changed {len(ch)} / {len(rows)}")
        print("transitions", dict(Counter(f"{r['BEFORE']}->{r[after_key]}" for r in ch).most_common(12)))
        print("AFTER dist", dict(Counter(r[after_key] for r in rows)))

    summarize("Option A translation only", "A_CHANGED")
    summarize("Option B translation + drop PUT->MNFOPT", "B_CHANGED")

    print("\n=== Eric examples ===")
    for q in ["010367131C", "010148272C", "010143726C", "010392763C", "011221309C"]:
        r = next(x for x in rows if x["MPOLICY"] == q)
        exp = {"010367131C": "2", "010148272C": "2", "010143726C": "2", "010392763C": "3", "011221309C": "1"}[q]
        print(
            q,
            f"LP={r['LP_CODE']}",
            f"PUT={r['PAID_UP_TYPE'] or '-'}",
            f"now={r['BEFORE']}",
            f"A={r['OPT_A']}",
            f"B={r['OPT_B']}",
            f"want={exp}",
            f"A={'PASS' if r['OPT_A']==exp else 'FAIL'}",
            f"B={'PASS' if r['OPT_B']==exp else 'FAIL'}",
        )

    # Option A failures among intentional LP 3/4/5
    a_fail_45 = [
        r
        for r in rows
        if r["LP_CODE"] in ("4", "5")
        and PROP_LP[r["LP_CODE"]] != r["OPT_A"]
    ]
    print(f"\nOption A still wrong vs Product Book for LP 4/5: {len(a_fail_45)}")
    print("  by PUT", dict(Counter(r["PAID_UP_TYPE"] for r in a_fail_45)))
    print("  sample", [(r["MPOLICY"], r["LP_CODE"], r["PAID_UP_TYPE"], r["OPT_A"]) for r in a_fail_45[:8]])

    # Option B deltas that are PUT-sourced today (collateral)
    b_put = [r for r in rows if r["B_CHANGED"] == "Y" and r["PAID_UP_TYPE"] and r["OPT_A"] != r["OPT_B"]]
    print(f"\nOption B collateral (PUT previously drove MNFOPT): {len(b_put)}")
    print("  transitions", dict(Counter(f"PUT{r['PAID_UP_TYPE']}|LP{r['LP_CODE']}|{r['BEFORE']}->{r['OPT_B']}" for r in b_put).most_common(15)))


if __name__ == "__main__":
    main()
