"""
Issue #57 — read-only research: LifePRO NFO code 4 (ETI) / code 5 vs quikmstr.MNFOPT.
Does not modify conversion logic or outputs.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PPBENTYP = ROOT / "QLA_Migration" / "Source" / "PPBENTYP_BenefitType_Extract_20260630.csv"
CROSSWALK = ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"
QUIKMSTR = ROOT / "QLA_Migration" / "Output" / "quikmstr.csv"
OUT = ROOT / "Issue_Log_Items" / "Issue_57" / "evidence" / "issue57_nfo_code4_fleet.csv"

TRACE = ["010367131C", "010391895C", "010713704C", "010391876C", "010448806C"]


def seq1(v: str) -> bool:
    try:
        return int(float((v or "").strip())) == 1
    except Exception:
        return False


def load_crosswalk() -> dict[str, str]:
    cw: dict[str, str] = {}
    with CROSSWALK.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            old = (row.get("Old_Value") or "").strip()
            new = (row.get("New_Value") or "").strip()
            if old and new:
                cw[old] = new
    return cw


def load_mstr() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    with QUIKMSTR.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            pol = (row.get("MPOLICY") or "").strip()
            out[pol] = {
                "MNFOPT": (row.get("MNFOPT") or "").strip(),
                "MDIVOPT": (row.get("MDIVOPT") or "").strip(),
                "MSTATUS": (row.get("MSTATUS") or "").strip(),
            }
    return out


def effective_nfo(row: dict[str, str]) -> tuple[str, str, str]:
    tc = (row.get("TYPE_CODE") or "").strip()
    nf = (row.get("NON_FORFEITURE") or "").strip().replace(".0", "")
    bnf = (row.get("BF_NON_FORFEITURE") or "").strip().replace(".0", "")
    if tc == "BF" and bnf != "":
        return bnf, "BF_NON_FORFEITURE", tc
    return nf, "NON_FORFEITURE", tc


def main() -> None:
    cw = load_crosswalk()
    mstr = load_mstr()
    by_pol: dict[str, tuple[str, str, str]] = {}
    with PPBENTYP.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            if not seq1(row.get("BENEFIT_SEQ", "")):
                continue
            pol = (row.get("POLICY_NUMBER") or "").strip()
            eff, src, tc = effective_nfo(row)
            prev = by_pol.get(pol)
            if prev is None:
                by_pol[pol] = (eff, src, tc)
            elif src.startswith("BF") and eff != "":
                by_pol[pol] = (eff, src, tc)
            elif prev[0] == "" and eff != "":
                by_pol[pol] = (eff, src, tc)

    rows = []
    for lp, (eff, src, tc) in by_pol.items():
        qla = cw.get(lp)
        if not qla or qla not in mstr:
            continue
        if eff not in {"3", "4", "5"}:
            continue
        rows.append(
            {
                "LIFEPRO": lp,
                "MPOLICY": qla,
                "TYPE_CODE": tc,
                "SOURCE_FIELD": src,
                "LP_NFO_CODE": eff,
                "MNFOPT": mstr[qla]["MNFOPT"],
                "MDIVOPT": mstr[qla]["MDIVOPT"],
                "MSTATUS": mstr[qla]["MSTATUS"],
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "LIFEPRO",
                "MPOLICY",
                "TYPE_CODE",
                "SOURCE_FIELD",
                "LP_NFO_CODE",
                "MNFOPT",
                "MDIVOPT",
                "MSTATUS",
            ],
        )
        w.writeheader()
        w.writerows(rows)

    c4 = [r for r in rows if r["LP_NFO_CODE"] == "4"]
    c5 = [r for r in rows if r["LP_NFO_CODE"] == "5"]
    print(f"Wrote {OUT} ({len(rows)} rows)")
    print("code4", len(c4), "MNFOPT", dict(Counter(r["MNFOPT"] for r in c4)))
    print("code5", len(c5), "MNFOPT", dict(Counter(r["MNFOPT"] for r in c5)))
    print("would NF_4->2 (currently 0):", sum(1 for r in c4 if r["MNFOPT"] == "0"))
    print("would NF_5->3 (currently 0):", sum(1 for r in c5 if r["MNFOPT"] == "0"))
    for q in TRACE:
        hit = next((r for r in rows if r["MPOLICY"] == q), None)
        print("TRACE", q, hit or mstr.get(q))


if __name__ == "__main__":
    main()
