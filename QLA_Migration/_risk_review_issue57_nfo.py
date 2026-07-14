"""Issue #57 Risk — read-only before/after simulation for NFO translation fix."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PPBENTYP = ROOT / "QLA_Migration" / "Source" / "PPBENTYP_BenefitType_Extract_20260630.csv"
PPOLC = ROOT / "QLA_Migration" / "Source" / "PPOLC_PolicyMaster_Extract_20260630.csv"
CROSSWALK = ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"
QUIKMSTR = ROOT / "QLA_Migration" / "Output" / "quikmstr.csv"
OUT = ROOT / "Issue_Log_Items" / "Issue_57" / "evidence" / "issue57_risk_simulation.csv"

ERIC = [
    "010367131C",
    "010148272C",
    "010143726C",
    "010392763C",
    "011221309C",
]

# Proposed LP numeric -> QLA (Product Book + Eric)
PROP_LP = {
    "0": "0",
    "1": "1",
    "2": "1",
    "3": "1",
    "4": "2",
    "5": "3",
    "6": "0",
    "7": "0",
    "8": "0",
    "9": "0",
}

# Current LP numeric behavior (post-#21A, pre-#57)
def current_lp(code: str) -> str:
    if code in ("1", "2"):
        return "1"
    if code == "3":
        return "3"  # passthrough bug
    if code in ("4", "5", "9"):
        return "0"
    if code in ("0", ""):
        return "0"
    return code


# PAID_UP_TYPE text -> MNFOPT via NF_ prefix (unchanged by #57)
PUT_MAP = {
    "LE": "2",  # NF_LE -> 2
    "ET": "2",  # NF_ET -> 2
    "RU": "3",  # NF_RU -> 3
    "PU": "0",  # NF_PU -> 0
    "LP": "0",
    "SP": "0",
}


def seq1(v: str) -> bool:
    try:
        return int(float((v or "").strip())) == 1
    except Exception:
        return False


def effective_nfo(row: dict[str, str]) -> tuple[str, str, str]:
    tc = (row.get("TYPE_CODE") or "").strip()
    nf = (row.get("NON_FORFEITURE") or "").strip().replace(".0", "")
    bnf = (row.get("BF_NON_FORFEITURE") or "").strip().replace(".0", "")
    if tc == "BF" and bnf != "":
        return bnf, "BF", tc
    return nf, "NF", tc


def simulate(lp_code: str, put: str, lp_mapper) -> str:
    """Approximate engine: PAID_UP_TYPE overwrites blank NFO_OPT; enrich-on-zero; NF_ translate."""
    val = put if put else "0"
    if val in ("", "0"):
        raw = lp_code if lp_code != "" else "0"
        return lp_mapper(raw)
    return PUT_MAP.get(val, "0")


def main() -> None:
    cw: dict[str, str] = {}
    with CROSSWALK.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            old = (row.get("Old_Value") or "").strip()
            new = (row.get("New_Value") or "").strip()
            if old and new:
                cw[old] = new

    mstr: dict[str, dict[str, str]] = {}
    with QUIKMSTR.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            pol = (row.get("MPOLICY") or "").strip()
            mstr[pol] = {
                "MNFOPT": (row.get("MNFOPT") or "").strip() or "0",
                "MDIVOPT": (row.get("MDIVOPT") or "").strip(),
                "MSTATUS": (row.get("MSTATUS") or "").strip(),
            }

    put_by_lp: dict[str, str] = {}
    with PPOLC.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            put_by_lp[(row.get("POLICY_NUMBER") or "").strip()] = (
                row.get("PAID_UP_TYPE") or ""
            ).strip()

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
            elif src == "BF" and eff != "":
                by_pol[pol] = (eff, src, tc)
            elif prev[0] == "" and eff != "":
                by_pol[pol] = (eff, src, tc)

    rows = []
    mismatch = 0
    for lp, (eff, src, tc) in by_pol.items():
        qla = cw.get(lp)
        if not qla or qla not in mstr:
            continue
        put = put_by_lp.get(lp, "")
        before = mstr[qla]["MNFOPT"]
        pred_before = simulate(eff, put, current_lp)
        after = simulate(eff, put, lambda c: PROP_LP.get(c, "0"))
        if pred_before != before:
            mismatch += 1
        rows.append(
            {
                "MPOLICY": qla,
                "LIFEPRO": lp,
                "LP_CODE": eff,
                "TYPE_CODE": tc,
                "SOURCE_FIELD": src,
                "PAID_UP_TYPE": put,
                "BEFORE_MNFOPT": before,
                "PRED_BEFORE": pred_before,
                "AFTER_MNFOPT": after,
                "CHANGED": "Y" if before != after else "N",
                "MDIVOPT": mstr[qla]["MDIVOPT"],
                "MSTATUS": mstr[qla]["MSTATUS"],
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    changed = [r for r in rows if r["CHANGED"] == "Y"]
    print(f"Wrote {OUT} ({len(rows)} policies)")
    print(f"Model mismatch vs actual before: {mismatch}")
    print(f"Would change: {len(changed)} | Unchanged: {len(rows) - len(changed)}")
    print("BEFORE dist", dict(Counter(r["BEFORE_MNFOPT"] for r in rows)))
    print("AFTER dist", dict(Counter(r["AFTER_MNFOPT"] for r in rows)))
    print(
        "Transitions",
        dict(
            Counter(
                f"{r['BEFORE_MNFOPT']}->{r['AFTER_MNFOPT']}" for r in changed
            ).most_common(20)
        ),
    )

    buckets: Counter[str] = Counter()
    for r in changed:
        lp, b, a, put = r["LP_CODE"], r["BEFORE_MNFOPT"], r["AFTER_MNFOPT"], r["PAID_UP_TYPE"]
        if lp == "4" and a == "2":
            buckets[f"code4 ETI ->2 (was {b})"] += 1
        elif lp == "5" and a == "3":
            buckets[f"code5 RPU ->3 (was {b})"] += 1
        elif lp == "3" and a == "1":
            buckets[f"code3 APL ->1 (was {b})"] += 1
        elif lp in ("1", "2") and a == "1":
            buckets[f"code{lp} residual ->1 (was {b})"] += 1
        else:
            buckets[f"OTHER LP{lp} PUT{put} {b}->{a}"] += 1
    print("Buckets", dict(buckets))

    for q in ERIC:
        r = next(x for x in rows if x["MPOLICY"] == q)
        print(
            "ERIC",
            q,
            f"LP={r['LP_CODE']}",
            f"PUT={r['PAID_UP_TYPE'] or '(blank)'}",
            f"{r['BEFORE_MNFOPT']}->{r['AFTER_MNFOPT']}",
            "PASS" if (
                (q in ERIC[:3] and r["AFTER_MNFOPT"] == "2")
                or (q == "010392763C" and r["AFTER_MNFOPT"] == "3")
                or (q == "011221309C" and r["AFTER_MNFOPT"] == "1")
            ) else "CHECK",
        )


if __name__ == "__main__":
    main()
