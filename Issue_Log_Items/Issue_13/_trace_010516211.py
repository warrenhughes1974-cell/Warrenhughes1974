#!/usr/bin/env python3
"""Trace LifePRO status fields for policy 9010516211 / 010516211C."""
import os
import pandas as pd

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
SOURCE = os.path.join(ROOT, "QLA_Migration", "Source")
OUTPUT = os.path.join(ROOT, "QLA_Migration", "Output")
POL = "9010516211"
QLA = "010516211C"

STATUS_KEYS = (
    "STATUS", "CONTRACT", "PAID", "REASON", "CODE", "TYPE",
    "BILL", "PAYMENT", "NON_FORFEIT", "NFO", "LAPSE", "TERM",
)


def s(v):
    return str(v).strip() if v is not None else ""


def load(name):
    path = os.path.join(SOURCE, name)
    df = pd.read_csv(path, encoding="latin1", dtype=str, keep_default_na=False)
    df.columns = [c.strip() for c in df.columns]
    return df


def rel_cols(cols):
    return [c for c in cols if any(k in c.upper() for k in STATUS_KEYS)]


def main():
    print(f"Policy trace: {POL} / {QLA}\n{'='*60}")

    ppol = load("PPOLC_PolicyMaster_Extract_20260530.csv")
    ppben = load("PPBEN_PolicyBenefit_Extract_20260530.csv")

    # PPOLC — primary driver for quikmstr MSTATUS
    pr = ppol[ppol["POLICY_NUMBER"].str.strip() == POL]
    print("\n## PPOLC (Policy Master) — quikmstr MSTATUS source")
    print("Relevant columns:", rel_cols(ppol.columns))
    if not pr.empty:
        r = pr.iloc[0]
        for c in [
            "POLICY_NUMBER", "CONTRACT_CODE", "CONTRACT_REASON", "CONTRACT_DATE",
            "PAID_UP_TYPE", "STATUS_CODE", "STATUS_REASON",
            "BILLING_CODE", "BILLING_REASON", "PAYMENT_CODE", "PAYMENT_REASON",
            "NON_FORFEITURE_OPTION", "PLAN_CODE",
        ]:
            if c in ppol.columns:
                print(f"  {c}: {s(r.get(c))}")
        # any other non-empty status-ish cols
        print("  --- other non-empty status-related cols ---")
        for c in rel_cols(ppol.columns):
            if c not in {
                "POLICY_NUMBER", "CONTRACT_CODE", "CONTRACT_REASON", "CONTRACT_DATE",
                "PAID_UP_TYPE", "STATUS_CODE", "STATUS_REASON",
                "BILLING_CODE", "BILLING_REASON", "PAYMENT_CODE", "PAYMENT_REASON",
            }:
                v = s(r.get(c))
                if v:
                    print(f"  {c}: {v}")

    # PPBEN — what Eric sees on benefit screen
    br = ppben[ppben["POLICY_NUMBER"].str.strip() == POL]
    print(f"\n## PPBEN (Policy Benefit) — {len(br)} rows")
    for _, r in br.iterrows():
        print(
            f"  SEQ={s(r.get('BENEFIT_SEQ'))} "
            f"TYPE={s(r.get('BENEFIT_TYPE'))} "
            f"STATUS_CODE={s(r.get('STATUS_CODE'))} "
            f"STATUS_REASON={s(r.get('STATUS_REASON'))} "
            f"PLAN={s(r.get('PLAN_CODE'))}"
        )

    # PPBENTYP if present
    bentyp_path = os.path.join(SOURCE, "PPBENTYP_BenefitType_Extract_20260530.csv")
    if os.path.isfile(bentyp_path):
        bt = load("PPBENTYP_BenefitType_Extract_20260530.csv")
        btr = bt[bt["POLICY_NUMBER"].str.strip() == POL] if "POLICY_NUMBER" in bt.columns else pd.DataFrame()
        if not btr.empty:
            print(f"\n## PPBENTYP — {len(btr)} rows (NFO-related cols)")
            nf_cols = [c for c in bt.columns if "NON_FORFEIT" in c.upper() or "NFO" in c.upper() or "STATUS" in c.upper()]
            for _, r in btr.iterrows():
                print(f"  BENEFIT_SEQ={s(r.get('BENEFIT_SEQ',''))}")
                for c in nf_cols[:12]:
                    print(f"    {c}: {s(r.get(c))}")

    # Conversion path
    cc = s(pr.iloc[0]["CONTRACT_CODE"]) if not pr.empty else ""
    cr = s(pr.iloc[0]["CONTRACT_REASON"]) if not pr.empty else ""
    put = s(pr.iloc[0]["PAID_UP_TYPE"]) if not pr.empty else ""
    print("\n## QLAdmin conversion path (app.py MSTATUS interceptor)")
    print(f"  Step 1 rulebook: CONTRACT_CODE -> MSTATUS (overridden by interceptor)")
    print(f"  Step 2 interceptor: PAID_UP_TYPE='{put}' in [PU,RU,ET,LE,LP,SP] -> composite key PUT_{put}")
    print(f"  Step 3 translation: ST_PUT_{put} -> Master_Value_Translation -> MSTATUS 44 (Extended Term)")
    print(f"  Ignored for MSTATUS: CONTRACT_CODE={cc}, CONTRACT_REASON={cr} -> would be ST_T_LP -> 54 (Lapsed)")
    print(f"  PPBEN STATUS_CODE/REASON (T/LP) is NOT used for quikmstr.MSTATUS")

    qm_path = os.path.join(OUTPUT, "quikmstr.csv")
    if os.path.isfile(qm_path):
        qm = pd.read_csv(qm_path, dtype=str, keep_default_na=False)
        out = qm[qm["MPOLICY"].str.strip() == QLA]
        if not out.empty:
            print(f"\n## quikmstr output: MSTATUS={s(out.iloc[0].get('MSTATUS'))}")

    # Fleet T+LP count
    tlp = ppol[
        (ppol["CONTRACT_CODE"].str.strip().str.upper() == "T")
        & (ppol["CONTRACT_REASON"].str.strip().str.upper() == "LP")
    ]
    print(f"\n## Fleet: CONTRACT_CODE=T, CONTRACT_REASON=LP: {len(tlp)} policies")
    if "PAID_UP_TYPE" in tlp.columns:
        print(tlp["PAID_UP_TYPE"].str.strip().value_counts().to_string())


if __name__ == "__main__":
    main()
