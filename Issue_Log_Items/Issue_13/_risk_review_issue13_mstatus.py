#!/usr/bin/env python3
"""Issue #13 Option A risk simulation — termination-first MSTATUS when CONTRACT_CODE=T."""
from __future__ import annotations

import os
import sys
from collections import Counter

import pandas as pd

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
SOURCE = os.path.join(ROOT, "QLA_Migration", "Source")
OUTPUT = os.path.join(ROOT, "QLA_Migration", "Output")
MVT_PATH = os.path.join(ROOT, "Master_Value_Translation.csv")
CW_PATH = os.path.join(ROOT, "QLA_Migration", "Mapping", "Master_Crosswalk.csv")
OUT_CSV = os.path.join(os.path.dirname(__file__), "Issue_13_Risk_Simulation.csv")
OUT_MD = os.path.join(os.path.dirname(__file__), "Issue_13_Risk_Simulation_Summary.txt")

MSTATUS_DESC = {
    "22": "Active", "32": "Waiver", "41": "Paid Up", "42": "Special Active",
    "44": "Extended Term", "45": "Reduced Paid Up", "50": "Suspended",
    "53": "Terminated/Death", "54": "Lapsed", "55": "Surrendered",
    "56": "Expired", "57": "Matured", "90": "Cash Value", "10": "Inactive", "12": "Inactive Pending",
}

SAMPLES = ["9011101663", "9010516211", "9010397318", "9010464590", "9010784054"]


def s(v) -> str:
    return str(v).strip() if v is not None else ""


def load_st_translation() -> dict[str, str]:
    df = pd.read_csv(MVT_PATH, dtype=str, keep_default_na=False)
    return {s(r["Source_Code"]): s(r["QLA_Result"]) for _, r in df.iterrows() if s(r["Source_Code"]).startswith("ST_")}


def current_key(cc: str, cr: str, put: str) -> str:
    put = s(put).upper()
    cc = s(cc).upper()
    cr = s(cr).upper()
    if put in {"PU", "RU", "ET", "LE", "LP", "SP"}:
        return f"ST_PUT_{put}"
    return f"ST_{cc}_{cr}" if cr else f"ST_{cc}_"


def proposed_key(cc: str, cr: str, put: str) -> str:
    cc = s(cc).upper()
    cr = s(cr).upper()
    put = s(put).upper()
    if cc == "T":
        return f"ST_{cc}_{cr}" if cr else f"ST_{cc}_"
    if put in {"PU", "RU", "ET", "LE", "LP", "SP"}:
        return f"ST_PUT_{put}"
    return f"ST_{cc}_{cr}" if cr else f"ST_{cc}_"


def translate(st_map: dict[str, str], key: str) -> str:
    return st_map.get(key, "")


def main() -> int:
    st_map = load_st_translation()
    ppol = pd.read_csv(
        os.path.join(SOURCE, "PPOLC_PolicyMaster_Extract_20260530.csv"),
        encoding="latin1", dtype=str, keep_default_na=False,
    )
    ppol.columns = [c.strip() for c in ppol.columns]

    cw = pd.read_csv(CW_PATH, dtype=str, keep_default_na=False)
    l2q = {s(a): s(b) for a, b in zip(cw.iloc[:, 0], cw.iloc[:, 1]) if s(a)}

    qm = {}
    qm_path = os.path.join(OUTPUT, "quikmstr.csv")
    if os.path.isfile(qm_path):
        qdf = pd.read_csv(qm_path, dtype=str, keep_default_na=False)
        qm = {s(r["MPOLICY"]): s(r.get("MSTATUS", "")) for _, r in qdf.iterrows()}

    rows = []
    change_counter = Counter()
    unmapped = Counter()
    transition = Counter()

    for _, r in ppol.iterrows():
        pol = s(r.get("POLICY_NUMBER", ""))
        if not pol:
            continue
        cc = s(r.get("CONTRACT_CODE", ""))
        cr = s(r.get("CONTRACT_REASON", ""))
        put = s(r.get("PAID_UP_TYPE", ""))
        qla = l2q.get(pol, pol)

        ck = current_key(cc, cr, put)
        pk = proposed_key(cc, cr, put)
        cur_ms = translate(st_map, ck)
        prop_ms = translate(st_map, pk)
        emitted = qm.get(qla, "")

        would_change = cur_ms != prop_ms
        if would_change:
            change_counter[(cur_ms, prop_ms)] += 1
            transition[f"{cur_ms or '?'} -> {prop_ms or '?'}"] += 1
        if prop_ms == "" and pk not in st_map:
            unmapped[pk] += 1

        rows.append({
            "POLICY_NUMBER": pol,
            "MPOLICY": qla,
            "CONTRACT_CODE": cc,
            "CONTRACT_REASON": cr,
            "PAID_UP_TYPE": put,
            "CURRENT_KEY": ck,
            "PROPOSED_KEY": pk,
            "CURRENT_MSTATUS": cur_ms,
            "PROPOSED_MSTATUS": prop_ms,
            "EMITTED_MSTATUS": emitted,
            "WOULD_CHANGE": would_change,
            "PROPOSED_UNMAPPED": prop_ms == "",
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    total = len(df)
    changes = int(df["WOULD_CHANGE"].sum())
    unmapped_n = int(df["PROPOSED_UNMAPPED"].sum())
    t_put = int(((df["CONTRACT_CODE"].str.upper() == "T") & df["PAID_UP_TYPE"].str.strip().isin(["PU", "RU", "ET", "LE", "LP", "SP"])).sum())

    lines = [
        f"Issue #13 Option A simulation — {total} PPOLC policies",
        f"Would change MSTATUS: {changes}",
        f"Unchanged: {total - changes}",
        f"T + non-blank PAID_UP_TYPE: {t_put}",
        f"Proposed unmapped (missing ST_* key): {unmapped_n}",
        "",
        "Top transitions (current -> proposed):",
    ]
    for k, n in transition.most_common(15):
        lines.append(f"  {k}: {n}")
    if unmapped:
        lines.extend(["", "Unmapped proposed keys:"])
        for k, n in unmapped.most_common(10):
            lines.append(f"  {k}: {n}")
    lines.extend(["", "Sample policies:"])
    for pol in SAMPLES:
        sub = df[df["POLICY_NUMBER"] == pol]
        if sub.empty:
            continue
        r = sub.iloc[0]
        cd = MSTATUS_DESC.get(r["CURRENT_MSTATUS"], r["CURRENT_MSTATUS"])
        pd_ = MSTATUS_DESC.get(r["PROPOSED_MSTATUS"], r["PROPOSED_MSTATUS"])
        lines.append(
            f"  {pol} / {r['MPOLICY']}: {r['CURRENT_MSTATUS']}({cd}) -> {r['PROPOSED_MSTATUS']}({pd_}) "
            f"[{r['CONTRACT_CODE']}/{r['CONTRACT_REASON']} PUT={r['PAID_UP_TYPE']}]"
        )

    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print("\n".join(lines))
    print(f"\nWrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
