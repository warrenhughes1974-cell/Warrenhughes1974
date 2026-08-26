"""Read-only #146 research: allowlist vs leftover QuikIsrr / companions."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "QLA_Migration" / "Output"
SRC = REPO / "QLA_Migration" / "Source"

PC19 = [
    "9010758550",
    "9010765198",
    "9010770062",
    "9010771070",
    "9010773468",
    "9010776813",
    "9010777059",
    "9010787639",
    "9010788679",
    "9010810228",
    "9010811998",
    "9010816969",
    "9010817956",
    "9010821435",
    "9010826551",
    "9010849882",
    "9010943849",
    "9011048543",
    "9011077629",
]
BLANK_EX = "9010808831"
KEEP = ["9010761639", "9010760840"]
ALLOW = PC19 + [BLANK_EX]


def _norm(pol: str) -> str:
    return str(pol or "").strip().replace(".0", "").rstrip("C").lstrip("0") or str(pol or "").strip()


def _keys(pol: str) -> set[str]:
    raw = str(pol or "").strip()
    n = _norm(raw)
    return {raw, raw.strip(), n, n + "C", raw.rstrip("C"), raw.rstrip("C") + "C"}


def _in_set(pol: str, members: set[str]) -> bool:
    return bool(_keys(pol) & members)


def _read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="", errors="replace") as f:
        return list(csv.DictReader(f))


def _ps_clms(row: dict) -> bool:
    claim = str(row.get("CLAIMNUM") or "")
    cause = str(row.get("CAUSE") or "").strip().upper()
    phase = str(row.get("MPHASE") or "").strip()
    return claim.startswith("PS-") or cause == "SRR" or phase == "0"


def _type8(row: dict) -> bool:
    return str(row.get("MBENTYP") or "").strip() in ("8", "8.0")


def _phase0(row: dict) -> bool:
    return str(row.get("MPHASE") or "").strip() in ("0", "0.0")


def _amt(row: dict, *cols: str) -> float:
    for c in cols:
        try:
            return float(str(row.get(c) or "0").replace(",", "").strip() or 0)
        except ValueError:
            continue
    return 0.0


def main() -> int:
    allow_keys = set()
    keep_keys = set()
    for p in ALLOW:
        allow_keys |= _keys(p)
    for p in KEEP:
        keep_keys |= _keys(p)

    ppolc = {}
    ppolc_path = SRC / "PPOLC_PolicyMaster_Extract_20260630.csv"
    with ppolc_path.open(encoding="utf-8-sig", newline="", errors="replace") as f:
        for row in csv.DictReader(f):
            p = str(row.get("POLICY_NUMBER") or "").strip()
            if not p or p.startswith("-"):
                continue
            ppolc[p] = {
                "billing_reason": str(row.get("BILLING_REASON") or "").strip().upper(),
                "contract": str(row.get("CONTRACT_CODE") or "").strip().upper(),
                "reason": str(row.get("CONTRACT_REASON") or "").strip().upper(),
                "ann": _amt(row, "ANNUAL_PREMIUM"),
            }

    isrr = _read(OUT / "QuikIsrr.csv")
    clms = _read(OUT / "quikclms.csv")
    clmp = _read(OUT / "quikclmp.csv")
    benh = _read(OUT / "quikbenh.csv")
    ridr = _read(OUT / "quikridr.csv")

    def bucket(pol: str) -> str:
        if _in_set(pol, allow_keys):
            return "allow"
        if _in_set(pol, keep_keys):
            return "keep_gold"
        return "other"

    isrr_by = defaultdict(list)
    for r in isrr:
        isrr_by[bucket(str(r.get("MPOLICY") or ""))].append(r)

    clms_ps = [r for r in clms if _ps_clms(r)]
    clmp0 = [r for r in clmp if _phase0(r)]
    benh8 = [r for r in benh if _type8(r)]

    def count_bucket(rows: list[dict]) -> dict[str, int]:
        out = defaultdict(int)
        for r in rows:
            out[bucket(str(r.get("MPOLICY") or ""))] += 1
        return dict(out)

    allow_detail = []
    missing_isrr = []
    for p in ALLOW:
        src = ppolc.get(p, {})
        rows = [r for r in isrr if _in_set(str(r.get("MPOLICY") or ""), _keys(p))]
        munit = ""
        for r in ridr:
            if _in_set(str(r.get("MPOLICY") or ""), _keys(p)) and str(r.get("MPHASE") or "").strip() == "1":
                munit = r.get("MUNIT", "")
                break
        amts = [_amt(r, "MSURRAMT") for r in rows]
        allow_detail.append({
            "policy": p,
            "billing_reason": src.get("billing_reason") or "(blank)",
            "contract": src.get("contract", ""),
            "contract_reason": src.get("reason", ""),
            "annual_premium": src.get("ann", 0),
            "isrr_rows": len(rows),
            "isrr_amt": round(sum(amts), 2),
            "amts_match_prem": sum(1 for a in amts if abs(a - float(src.get("ann") or 0)) < 0.51),
            "munit": munit,
        })
        if not rows:
            missing_isrr.append(p)

    keep_detail = []
    for p in KEEP:
        src = ppolc.get(p, {})
        rows = [r for r in isrr if _in_set(str(r.get("MPOLICY") or ""), _keys(p))]
        keep_detail.append({
            "policy": p,
            "billing_reason": src.get("billing_reason") or "(blank)",
            "isrr_rows": len(rows),
            "isrr_amt": round(sum(_amt(r, "MSURRAMT") for r in rows), 2),
        })

    non_vb_pols = set()
    for r in isrr:
        mp = str(r.get("MPOLICY") or "").strip()
        src_p = mp.rstrip("C")
        br = (ppolc.get(src_p) or {}).get("billing_reason", "")
        if br != "VB":
            non_vb_pols.add(src_p)

    summary = {
        "cut": "20260630",
        "allowlist_count": len(ALLOW),
        "pc19": PC19,
        "blank_exception": BLANK_EX,
        "keep_golds": KEEP,
        "quikisrr_total": len(isrr),
        "quikisrr_allow": len(isrr_by["allow"]),
        "quikisrr_keep_gold": len(isrr_by["keep_gold"]),
        "quikisrr_other": len(isrr_by["other"]),
        "quikisrr_allow_amt": round(sum(_amt(r, "MSURRAMT") for r in isrr_by["allow"]), 2),
        "allow_policies_with_isrr": len({_norm(r.get("MPOLICY")) for r in isrr_by["allow"]}),
        "allow_missing_isrr": missing_isrr,
        "companions": {
            "clms_ps": count_bucket(clms_ps),
            "clmp_phase0": count_bucket(clmp0),
            "benh_type8": count_bucket(benh8),
        },
        "non_vb_isrr_policies": len(non_vb_pols),
        "leftover_after_146": len(isrr) - len(isrr_by["allow"]),
        "allow_detail": allow_detail,
        "keep_detail": keep_detail,
    }
    outp = REPO / "Issue_Log_Items" / "Issue_146" / "evidence"
    outp.mkdir(parents=True, exist_ok=True)
    (outp / "issue146_research_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("allow_detail", "pc19")}, indent=2))
    print("--- allow ---")
    for d in allow_detail:
        print(f"{d['policy']} br={d['billing_reason']} n={d['isrr_rows']} amt={d['isrr_amt']} match={d['amts_match_prem']} munit={d['munit']}")
    print("--- keep ---")
    for d in keep_detail:
        print(d)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
