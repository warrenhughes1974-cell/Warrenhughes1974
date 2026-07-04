#!/usr/bin/env python3
"""Trace Issue #13 sample policies — source vs converted MSTATUS."""
import os
import sys

import pandas as pd

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
SOURCE = os.path.join(ROOT, "QLA_Migration", "Source")
OUTPUT = os.path.join(ROOT, "QLA_Migration", "Output")

MSTATUS_DESC = {
    "22": "Active",
    "41": "Paid Up",
    "44": "Extended Term",
    "45": "Reduced Paid Up",
    "53": "Terminated/Death",
    "54": "Lapsed",
    "55": "Surrendered",
    "56": "Expired",
    "57": "Matured",
}

ST_TRANSLATION = {
    "ST_A_": "22", "ST_A_RS": "22", "ST_A_RI": "22",
    "ST_T_DC": "53", "ST_T_SR": "55", "ST_T_LP": "54",
    "ST_T_MA": "57", "ST_T_EX": "56", "ST_T_CV": "90",
    "ST_S_DP": "50", "ST_A_SP": "42", "ST_P_": "41",
    "ST_P_PUP": "41", "ST_P_RPU": "45", "ST_P_ETI": "44",
    "ST_I_": "10", "ST_I_PND": "10", "ST_I_INP": "12",
    "ST_D_": "53", "ST_D_DTH": "53", "ST_D_PND": "50",
    "ST_PUT_PU": "41", "ST_PUT_RU": "45", "ST_PUT_ET": "44",
    "ST_PUT_LE": "44", "ST_PUT_LP": "54", "ST_PUT_SP": "42",
}

SAMPLES = [
    ("9011101663", "011101663C", "FPU (41) vs Terminated/Expired"),
    ("9010516211", "010516211C", "ETI (44) vs Terminated/Lapsed"),
]


def s(val) -> str:
    return str(val).strip() if val is not None else ""


def derive_mstatus(contract_code, contract_reason, paid_up_type):
    put = s(paid_up_type).upper()
    if put in {"PU", "RU", "ET", "LE", "LP", "SP"}:
        key = f"ST_PUT_{put}"
    else:
        cc = s(contract_code).upper()
        cr = s(contract_reason).upper()
        key = f"ST_{cc}_{cr}" if cr else f"ST_{cc}_"
    return ST_TRANSLATION.get(key, ""), key


def alt_mstatus_if_termination_first(contract_code, contract_reason, paid_up_type):
    """What MSTATUS would be if CONTRACT_CODE/REASON took precedence."""
    cc = s(contract_code).upper()
    cr = s(contract_reason).upper()
    key = f"ST_{cc}_{cr}" if cr else f"ST_{cc}_"
    return ST_TRANSLATION.get(key, ""), key


def main():
    ppol_path = os.path.join(SOURCE, "PPOLC_PolicyMaster_Extract_20260530.csv")
    ppben_path = os.path.join(SOURCE, "PPBEN_PolicyBenefit_Extract_20260530.csv")
    qm_path = os.path.join(OUTPUT, "quikmstr.csv")

    ppol = pd.read_csv(ppol_path, encoding="latin1", dtype=str, keep_default_na=False)
    ppol.columns = [c.strip() for c in ppol.columns]
    ppben = pd.read_csv(ppben_path, encoding="latin1", dtype=str, keep_default_na=False)
    ppben.columns = [c.strip() for c in ppben.columns]

    qm = None
    if os.path.isfile(qm_path):
        qm = pd.read_csv(qm_path, dtype=str, keep_default_na=False)

    rows = []
    print("Issue #13 — Sample Policy Trace\n" + "=" * 60)
    for legacy, qla, note in SAMPLES:
        pol = ppol[ppol["POLICY_NUMBER"].str.strip() == legacy]
        ben = ppben[
            (ppben["POLICY_NUMBER"].str.strip() == legacy)
            & (ppben["BENEFIT_SEQ"].str.strip() == "1")
        ]
        print(f"\nPolicy: {legacy} / {qla}")
        print(f"Issue note: {note}")

        if pol.empty:
            print("  PPOLC: NOT FOUND")
            cc = cr = put = ""
        else:
            r = pol.iloc[0]
            cc = s(r.get("CONTRACT_CODE", ""))
            cr = s(r.get("CONTRACT_REASON", ""))
            put = s(r.get("PAID_UP_TYPE", ""))
            print(f"  PPOLC CONTRACT_CODE: {cc}")
            print(f"  PPOLC CONTRACT_REASON: {cr}")
            print(f"  PPOLC PAID_UP_TYPE: {put}")

        if not ben.empty:
            b = ben.iloc[0]
            print(f"  PPBEN STATUS_CODE: {s(b.get('STATUS_CODE', ''))}")
            print(f"  PPBEN STATUS_REASON: {s(b.get('STATUS_REASON', ''))}")
            print(f"  PPBEN BENEFIT_TYPE: {s(b.get('BENEFIT_TYPE', ''))}")

        derived, key = derive_mstatus(cc, cr, put)
        alt, alt_key = alt_mstatus_if_termination_first(cc, cr, put)
        print(f"  Converter composite key (PAID_UP_TYPE first): {key} -> MSTATUS {derived} ({MSTATUS_DESC.get(derived, '?')})")
        print(f"  If termination-first: {alt_key} -> MSTATUS {alt} ({MSTATUS_DESC.get(alt, '?')})")

        if qm is not None:
            out = qm[qm["MPOLICY"].str.strip() == qla]
            if out.empty:
                print("  quikmstr output: NOT FOUND")
                emitted = ""
            else:
                emitted = s(out.iloc[0].get("MSTATUS", ""))
                print(f"  quikmstr output MSTATUS: {emitted} ({MSTATUS_DESC.get(emitted, '?')})")
        else:
            emitted = ""

        mismatch = derived != alt and bool(put) and cc == "T"
        rows.append({
            "legacy_policy": legacy,
            "qla_policy": qla,
            "contract_code": cc,
            "contract_reason": cr,
            "paid_up_type": put,
            "ppben_status": s(ben.iloc[0].get("STATUS_CODE", "")) if not ben.empty else "",
            "ppben_reason": s(ben.iloc[0].get("STATUS_REASON", "")) if not ben.empty else "",
            "converter_key": key,
            "converter_mstatus": derived,
            "termination_first_key": alt_key,
            "termination_first_mstatus": alt,
            "emitted_mstatus": emitted,
            "issue13_pattern": "Y" if mismatch else "N",
        })

    # Fleet count: T + non-blank PAID_UP_TYPE where keys differ
    print("\n" + "=" * 60)
    print("Fleet scan: CONTRACT_CODE=T with PAID_UP_TYPE in PU/RU/ET/LE/LP/SP")
    count = 0
    diff_examples = []
    for _, r in ppol.iterrows():
        cc = s(r.get("CONTRACT_CODE", "")).upper()
        put = s(r.get("PAID_UP_TYPE", "")).upper()
        if cc != "T" or put not in {"PU", "RU", "ET", "LE", "LP", "SP"}:
            continue
        count += 1
        cr = s(r.get("CONTRACT_REASON", ""))
        d, _ = derive_mstatus(cc, cr, put)
        a, _ = alt_mstatus_if_termination_first(cc, cr, put)
        if d != a and len(diff_examples) < 10:
            diff_examples.append((s(r.get("POLICY_NUMBER", "")), put, cr, d, a))

    print(f"  Total policies matching pattern: {count}")
    print(f"  Where PAID_UP_TYPE-first != termination-first: (see key diff when PUT present + T)")
    for ex in diff_examples[:5]:
        print(f"    {ex[0]}: PUT={ex[1]} reason={ex[2]} -> current={ex[3]} alt={ex[4]}")

    out_csv = os.path.join(os.path.dirname(__file__), "Issue_13_Sample_Trace.csv")
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"\nWrote {out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
