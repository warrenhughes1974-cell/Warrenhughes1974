"""
Issue #59 — read-only MSTATUS precedence risk simulation.
Does not modify app.py, rulebooks, or Output.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PPOLC = ROOT / "QLA_Migration/Source/PPOLC_PolicyMaster_Extract_20260630.csv"
MSTR = ROOT / "QLA_Migration/Output/quikmstr.csv"
XWALK = ROOT / "QLA_Migration/Mapping/Master_Crosswalk.csv"
TRANS = ROOT / "QLA_Migration/Mapping/Master_Value_Translation.csv"
OUT = ROOT / "Issue_Log_Items/Issue_59/evidence/issue59_risk_mstatus_deltas.csv"


def norm(x: str | None) -> str:
    return (x or "").strip()


def load_st() -> dict[str, str]:
    st: dict[str, str] = {}
    with TRANS.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            k = norm(row.get("Source_Code"))
            if k.startswith("ST_"):
                st[k] = norm(row.get("QLA_Result"))
    return st


def composite_current(cc: str, cr: str, put: str, st: dict[str, str]) -> tuple[str, str]:
    cc, cr, put = norm(cc), norm(cr), norm(put)
    if cc == "T":
        key = f"T_{cr}" if cr else "T_"
    elif put in ("PU", "RU", "ET", "LE", "LP", "SP"):
        key = f"PUT_{put}"
    else:
        key = f"{cc}_{cr}" if cr else f"{cc}_"
    return key, st.get(f"ST_{key}", f"MISS:{key}")


def composite_proposed(cc: str, cr: str, put: str, st: dict[str, str]) -> tuple[str, str]:
    cc, cr, put = norm(cc), norm(cr), norm(put)
    if cc == "T":
        key = f"T_{cr}" if cr else "T_"
    elif cc == "S":
        key = f"S_{cr}" if cr else "S_"
    elif cc == "A" and put == "LP":
        key = "A_"
    elif put in ("PU", "RU", "ET", "LE", "LP", "SP"):
        key = f"PUT_{put}"
    else:
        key = f"{cc}_{cr}" if cr else f"{cc}_"
    return key, st.get(f"ST_{key}", f"MISS:{key}")


def main() -> None:
    st = load_st()
    cw = {}
    with XWALK.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            cw[norm(row.get("Old_Value"))] = norm(row.get("New_Value"))

    mstatus = {}
    with MSTR.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            mstatus[norm(row["MPOLICY"])] = norm(row["MSTATUS"])

    changes = []
    with PPOLC.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            pn = norm(row.get("POLICY_NUMBER"))
            ck, cur = composite_current(
                row.get("CONTRACT_CODE"), row.get("CONTRACT_REASON"), row.get("PAID_UP_TYPE"), st
            )
            pk, prop = composite_proposed(
                row.get("CONTRACT_CODE"), row.get("CONTRACT_REASON"), row.get("PAID_UP_TYPE"), st
            )
            if prop == cur:
                continue
            qla = cw.get(pn, "")
            changes.append(
                {
                    "lp": pn,
                    "qla": qla,
                    "cc": norm(row.get("CONTRACT_CODE")),
                    "cr": norm(row.get("CONTRACT_REASON")),
                    "put": norm(row.get("PAID_UP_TYPE")),
                    "cur_key": ck,
                    "prop_key": pk,
                    "sim_before": cur,
                    "sim_after": prop,
                    "output_before": mstatus.get(qla, "?"),
                    "output_visible_change": (
                        "Y"
                        if mstatus.get(qla, "?") != prop and mstatus.get(qla, "?") != "?"
                        else "N"
                    ),
                }
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(changes[0].keys()) if changes else [])
        if changes:
            w.writeheader()
            w.writerows(changes)

    visible = Counter(
        (c["output_before"], c["sim_after"]) for c in changes if c["output_visible_change"] == "Y"
    )
    print(f"provisional_key_changes={len(changes)}")
    print(f"output_visible={sum(visible.values())} dist={dict(visible)}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
