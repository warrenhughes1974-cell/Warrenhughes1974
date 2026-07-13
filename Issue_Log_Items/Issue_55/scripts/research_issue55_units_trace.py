"""
Issue #55 — read-only units trace (PPBEN NUMBER_OF_UNITS vs quikridr.MUNIT).

No conversion / rulebook changes. Run from repo root:
  python Issue_Log_Items/Issue_55/scripts/research_issue55_units_trace.py
"""
from __future__ import annotations

import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
POLICIES = {
    "018495BC": "9018495B",
    "018499CC": "9018499C",
    "018510C": "9018510",
}
EXPECTED = {
    ("018495BC", "1"): "0.00001",
    ("018495BC", "2"): "0.53",
    ("018499CC", "1"): "0.00001",
    ("018499CC", "2"): "1.05",
    ("018510C", "1"): "0.00001",
    ("018510C", "2"): "0.647",
}
OUT = REPO / "Issue_Log_Items" / "Issue_55" / "evidence" / "issue55_trace_three_policies.csv"


def _f(x: str):
    try:
        return round(float(str(x).strip()), 5)
    except (TypeError, ValueError):
        return None


def main() -> int:
    ppben_path = REPO / "QLA_Migration" / "Source" / "PPBEN_PolicyBenefit_Extract_20260630.csv"
    ridr_path = REPO / "QLA_Migration" / "Output" / "quikridr.csv"
    mstr_path = REPO / "QLA_Migration" / "Output" / "quikmstr.csv"

    lp_set = set(POLICIES.values())
    ppben = {}
    with open(ppben_path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            pol = (row.get("POLICY_NUMBER") or "").strip()
            if pol in lp_set:
                seq = (row.get("BENEFIT_SEQ") or "").strip().lstrip("0") or "0"
                if seq == "0":
                    seq = "0"
                ppben[(pol, seq)] = row

    ridr = {}
    with open(ridr_path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            pol = (row.get("MPOLICY") or "").strip()
            if pol in POLICIES:
                seq = (row.get("MPHASE") or "").strip().lstrip("0") or "0"
                ridr[(pol, seq)] = row

    mstr = {}
    with open(mstr_path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            pol = (row.get("MPOLICY") or "").strip()
            if pol in POLICIES:
                mstr[pol] = row

    rows = []
    mismatches = 0
    for qla, lp in POLICIES.items():
        for seq in ("1", "2"):
            src = ppben.get((lp, seq), {})
            tgt = ridr.get((qla, seq), {})
            su = (src.get("NUMBER_OF_UNITS") or "").strip()
            mu = (tgt.get("MUNIT") or "").strip()
            mvpu = (tgt.get("MVPU") or "").strip()
            try:
                face = float(mu) * float(mvpu)
                face_s = f"{face:.5f}"
            except (TypeError, ValueError):
                face_s = ""
            exp = EXPECTED[(qla, seq)]
            match_client = "Y" if _f(mu) == _f(exp) else "N"
            match_src = "Y" if _f(mu) == _f(su) else "N"
            if match_client != "Y" or match_src != "Y":
                mismatches += 1
            rows.append(
                {
                    "QLA_POLICY": qla,
                    "LP_POLICY": lp,
                    "MPHASE": seq,
                    "MSTATUS_MASTER": (mstr.get(qla, {}).get("MSTATUS") or "").strip(),
                    "MPHSTAT": (tgt.get("MPHSTAT") or "").strip(),
                    "MPLAN": (tgt.get("MPLAN") or "").strip(),
                    "PPBEN_PLAN_CODE": (src.get("PLAN_CODE") or "").strip(),
                    "PPBEN_STATUS_REASON": (src.get("STATUS_REASON") or "").strip(),
                    "PPBEN_NUMBER_OF_UNITS_AC": su,
                    "QUIKRIDR_MUNIT": mu,
                    "QUIKRIDR_MVPU": mvpu,
                    "COMPUTED_FACE_MUNIT_x_MVPU": face_s,
                    "CLIENT_EXPECTED_UNITS": exp,
                    "CSV_MATCHES_CLIENT": match_client,
                    "CSV_MATCHES_PPBEN": match_src,
                }
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {OUT}")
    print(f"Phase rows: {len(rows)}; mismatches: {mismatches}")
    for r in rows:
        print(
            f"{r['QLA_POLICY']} P{r['MPHASE']}: PPBEN={r['PPBEN_NUMBER_OF_UNITS_AC']} "
            f"MUNIT={r['QUIKRIDR_MUNIT']} face={r['COMPUTED_FACE_MUNIT_x_MVPU']} "
            f"client={r['CSV_MATCHES_CLIENT']} src={r['CSV_MATCHES_PPBEN']}"
        )
    return 0 if mismatches == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
