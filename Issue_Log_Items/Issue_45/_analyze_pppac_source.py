"""Issue 45 — read-only analysis of PPPAC vs bank-draft exceptions / PPACH.
Does not modify conversion code or source extracts.
"""
import pandas as pd
import re
from collections import Counter, defaultdict
from pathlib import Path

SRC = Path(r"c:\Users\warren\Documents\GitHub\Warrenhughes1974\QLA_Migration\Source")
REP = Path(r"c:\Users\warren\Documents\GitHub\Warrenhughes1974\QLA_Migration\Reports")
OUT = Path(r"c:\Users\warren\Documents\GitHub\Warrenhughes1974\Issue_Log_Items\Issue_45")


def clean_cols(df):
    df = df.copy()
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df


def is_sep_row(val):
    s = str(val).strip()
    return bool(s) and set(s) <= {"-", " "}


def load_lifepro_csv(path):
    df = pd.read_csv(
        path, dtype=str, encoding="latin1", low_memory=False, on_bad_lines="skip"
    ).fillna("")
    df = clean_cols(df)
    key = "POLICY_NUMBER" if "POLICY_NUMBER" in df.columns else df.columns[0]
    mask = ~df[key].map(is_sep_row)
    if "COMPANY_CODE" in df.columns:
        mask &= ~df["COMPANY_CODE"].map(is_sep_row)
    df = df.loc[mask].copy()
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
        df[c] = df[c].replace({"nan": "", "None": "", "none": ""})
    return df


def normalize_policy(p):
    s = str(p).strip()
    if s.endswith(".0"):
        s = s[:-2]
    s = re.sub(r"\s+", "", s)
    return s


def digits_only(s):
    return re.sub(r"\D", "", str(s or ""))


def is_usable_account(acct):
    raw = str(acct or "").strip()
    if not raw or raw.lower() in ("nan", "none", "null", "n/a", "na"):
        return False
    if re.search(r"[xX*]{2,}|REDACT|MASK|HIDDEN|XXXX", raw, re.I):
        return False
    d = digits_only(raw)
    if not d:
        return False
    if set(d) <= {"0"}:
        return False
    if len(d) < 4:
        return False
    if d in {"1234", "123456", "123456789", "0000", "1111", "9999", "999999999"}:
        return False
    return True


def is_usable_routing(aba):
    raw = str(aba or "").strip()
    if not raw or raw.lower() in ("nan", "none", "null", "n/a", "na"):
        return False
    if re.search(r"[xX*]{2,}|REDACT|MASK|HIDDEN|XXXX", raw, re.I):
        return False
    d = digits_only(raw)
    if not d or set(d) <= {"0"}:
        return False
    if len(d) < 5:
        return False
    return True


def mask_acct(acct):
    d = digits_only(acct)
    if len(d) < 4:
        return "****(invalid/short)"
    return f"****{d[-4:]}"


def mask_aba(aba):
    d = digits_only(aba)
    if len(d) < 4:
        return "*****(invalid/short)"
    return f"*****{d[-4:]}"


def classify_acct(a):
    raw = str(a).strip()
    if not raw:
        return "blank"
    d = digits_only(raw)
    if not d:
        return "non_digit"
    if set(d) <= {"0"}:
        return "zero_filled"
    if re.search(r"[xX*]{2,}", raw):
        return "masked"
    if len(d) < 4:
        return "too_short"
    if is_usable_account(raw):
        return "usable"
    return "other_invalid"


def main():
    lines = []

    def out(s=""):
        print(s)
        lines.append(str(s))

    pppac = load_lifepro_csv(SRC / "PPPAC_PACDetail_Extract_20260630.csv")
    ppach = load_lifepro_csv(SRC / "PPACH_PACHistory_Extract_20260630.csv")
    exc = pd.read_csv(REP / "bank_draft_account_exceptions.csv", dtype=str).fillna("")
    exc.columns = [c.strip().upper() for c in exc.columns]
    exc["SRC_POL_N"] = exc["SOURCE_POLICY"].map(normalize_policy)

    # optional PPOLC for BILLING_FORM context
    ppolc_path = SRC / "PPOLC_PolicyMaster_Extract_20260630.csv"
    ppolc = load_lifepro_csv(ppolc_path)
    ppolc["POL_N"] = ppolc["POLICY_NUMBER"].map(normalize_policy)
    bill_col = None
    for c in ppolc.columns:
        if "BILL" in c and "FORM" in c:
            bill_col = c
            break
    pac_pols = set()
    if bill_col:
        pac_pols = set(
            ppolc.loc[ppolc[bill_col].str.upper().str.strip() == "PAC", "POL_N"]
        )

    out("=== STRUCTURE ===")
    out(f"PPPAC rows: {len(pppac)}")
    out(f"PPPAC cols: {list(pppac.columns)}")
    out(f"PPACH rows: {len(ppach)}")
    out(f"PPACH cols: {list(ppach.columns)}")
    out(f"Exceptions: {len(exc)}")
    out(f"PPOLC bill form col: {bill_col}")
    out(f"PPOLC PAC policies: {len(pac_pols)}")

    out("\n=== PPPAC POLICY UNIQUENESS ===")
    pppac["POL_N"] = pppac["POLICY_NUMBER"].map(normalize_policy)
    out(f"unique POLICY_NUMBER: {pppac['POL_N'].nunique()}")
    dup_pols = pppac["POL_N"].value_counts()
    out(f"policies with >1 row: {int((dup_pols > 1).sum())}")
    out(f"max rows per policy: {int(dup_pols.max()) if len(dup_pols) else 0}")
    if (dup_pols > 1).any():
        out(f"sample multi-row policies: {dup_pols[dup_pols > 1].head(10).to_dict()}")
    out(f"PAC_ID uniqueness: {pppac['PAC_ID'].nunique()} of {len(pppac)}")
    out(f"COMPANY_CODE value counts: {pppac['COMPANY_CODE'].value_counts().to_dict()}")

    pppac["ACCT_OK"] = pppac["E_ACCOUNT_NUMBER"].map(is_usable_account)
    pppac["PACCT_OK"] = pppac["P_ACCOUNT_NUMBER"].map(is_usable_account)
    out(f"\nPPPAC E_ACCOUNT usable: {int(pppac['ACCT_OK'].sum())}")
    out(f"PPPAC P_ACCOUNT usable: {int(pppac['PACCT_OK'].sum())}")
    out(
        f"PPPAC either account usable: {int((pppac['ACCT_OK'] | pppac['PACCT_OK']).sum())}"
    )

    pppac["E_CLASS"] = pppac["E_ACCOUNT_NUMBER"].map(classify_acct)
    out(f"PPPAC E_ACCOUNT class: {pppac['E_CLASS'].value_counts().to_dict()}")
    pppac["P_CLASS"] = pppac["P_ACCOUNT_NUMBER"].map(classify_acct)
    out(f"PPPAC P_ACCOUNT class: {pppac['P_CLASS'].value_counts().to_dict()}")

    for col in [
        "PAC_DATE",
        "BASE_DRAW_DATE",
        "PRENOTE_DATE",
        "FST_DRAW_DATE",
        "CHG_DATE",
    ]:
        if col in pppac.columns:
            vals = pppac[col].replace({"0": "", "00000000": ""})
            nonzero = vals[vals.str.len() > 0]
            out(
                f"{col}: nonblank={len(nonzero)}, min={nonzero.min() if len(nonzero) else None}, max={nonzero.max() if len(nonzero) else None}"
            )

    out(f"E_TRAN_CODE top: {pppac['E_TRAN_CODE'].value_counts().head(10).to_dict()}")
    out(
        f"CHANGE_TEMP_CODE top: {pppac['CHANGE_TEMP_CODE'].value_counts().head(10).to_dict()}"
    )
    out(f"LOAN_INT_IND top: {pppac['LOAN_INT_IND'].value_counts().head(10).to_dict()}")
    aba_like = [
        c
        for c in pppac.columns
        if any(x in c for x in ("ABA", "ROUT", "BANK", "TRANSIT"))
    ]
    out(f"PPPAC ABA/routing-like cols: {aba_like}")

    # account digit length distribution for usable
    usable_lens = pppac.loc[pppac["ACCT_OK"], "E_ACCOUNT_NUMBER"].map(
        lambda x: len(digits_only(x))
    )
    out(f"usable E_ACCOUNT digit-length counts: {usable_lens.value_counts().sort_index().to_dict()}")

    out("\n=== PPACH ACCOUNTABILITY ===")
    ppach["POL_N"] = ppach["POLICY_NUMBER"].map(normalize_policy)
    ppach["ACCT_OK"] = ppach["E_ACCOUNT_NUMBER"].map(is_usable_account)
    ppach["ABA_OK"] = ppach["E_ABA_NUM"].map(is_usable_routing)
    out(f"unique policies: {ppach['POL_N'].nunique()}")
    out(f"rows with usable E_ACCOUNT: {int(ppach['ACCT_OK'].sum())}")
    out(f"rows with usable E_ABA: {int(ppach['ABA_OK'].sum())}")
    out(f"STATUS_CODE top: {ppach['STATUS_CODE'].value_counts().head(15).to_dict()}")
    dup_h = ppach["POL_N"].value_counts()
    out(f"PPACH policies with >1 history row: {int((dup_h > 1).sum())}")
    out(f"max history rows/policy: {int(dup_h.max())}")

    ppach_sorted = ppach.sort_values(
        by=["CHANGE_DATE", "CHANGE_TIME"], ascending=[True, True]
    )
    ppach_last_complete = {}
    ppach_last_any_acct = {}
    ppach_any_row = set()
    for _, r in ppach_sorted.iterrows():
        pol = r["POL_N"]
        ppach_any_row.add(pol)
        acct = r["E_ACCOUNT_NUMBER"]
        aba = r["E_ABA_NUM"]
        if is_usable_account(acct) and is_usable_routing(aba):
            ppach_last_complete[pol] = {
                "acct": acct,
                "aba": aba,
                "status": r.get("STATUS_CODE", ""),
                "chg": r.get("CHANGE_DATE", ""),
            }
        if is_usable_account(acct):
            ppach_last_any_acct[pol] = {
                "acct": acct,
                "aba": aba if is_usable_routing(aba) else "",
                "status": r.get("STATUS_CODE", ""),
                "chg": r.get("CHANGE_DATE", ""),
            }
    out(f"PPACH policies with last usable acct+aba: {len(ppach_last_complete)}")
    out(f"PPACH policies with last usable acct (any aba): {len(ppach_last_any_acct)}")

    pppac_sorted = pppac.sort_values(
        by=["PAC_DATE", "CHG_DATE", "CHG_TIME"], ascending=[True, True, True]
    )
    pppac_last = {}
    pppac_rows_by_pol = defaultdict(list)
    for _, r in pppac_sorted.iterrows():
        pol = r["POL_N"]
        pppac_rows_by_pol[pol].append(r)
        pppac_last[pol] = r
    out(f"PPPAC map size: {len(pppac_last)}")

    # Relation to PPOLC PAC / bank draft universe
    out("\n=== RELATION TO PPOLC PAC ===")
    pppac_pols = set(pppac["POL_N"])
    out(f"PPPAC intersect PPOLC PAC: {len(pppac_pols & pac_pols)}")
    out(f"PPPAC not in PPOLC PAC: {len(pppac_pols - pac_pols)}")
    out(f"PPOLC PAC not in PPPAC: {len(pac_pols - pppac_pols)}")
    out(f"PPPAC row count vs PPOLC PAC count: {len(pppac)} vs {len(pac_pols)}")

    # === EXCEPTION RECONCILIATION ===
    out("\n=== EXCEPTION RECONCILIATION ===")
    exc_pols = set(exc["SRC_POL_N"])
    out(f"exception policies: {len(exc_pols)}")

    found = 0
    usable_acct = 0
    usable_routing = 0
    both = 0
    still_missing_acct = 0
    not_found = 0
    dup_conflict = 0
    masked_invalid = 0
    blank_in_pppac = 0
    samples = []

    for pol in sorted(exc_pols):
        rows = pppac_rows_by_pol.get(pol, [])
        if not rows:
            not_found += 1
            still_missing_acct += 1
            continue
        found += 1
        if len(rows) > 1:
            accts = {
                digits_only(r["E_ACCOUNT_NUMBER"])
                for r in rows
                if is_usable_account(r["E_ACCOUNT_NUMBER"])
            }
            if len(accts) > 1:
                dup_conflict += 1
        r = pppac_last[pol]
        e_ok = is_usable_account(r["E_ACCOUNT_NUMBER"])
        p_ok = is_usable_account(r["P_ACCOUNT_NUMBER"])
        eclass = classify_acct(r["E_ACCOUNT_NUMBER"])
        if eclass in (
            "masked",
            "zero_filled",
            "too_short",
            "non_digit",
            "other_invalid",
        ) and r["E_ACCOUNT_NUMBER"]:
            masked_invalid += 1
        if eclass == "blank" and not p_ok:
            blank_in_pppac += 1
        if e_ok or p_ok:
            usable_acct += 1
            if len(samples) < 20:
                samples.append(
                    {
                        "SOURCE_POLICY": pol,
                        "MPOLICY": exc.loc[
                            exc["SRC_POL_N"] == pol, "MPOLICY"
                        ].iloc[0]
                        if (exc["SRC_POL_N"] == pol).any()
                        else "",
                        "PPPAC_ACCOUNT": mask_acct(
                            r["E_ACCOUNT_NUMBER"] if e_ok else r["P_ACCOUNT_NUMBER"]
                        ),
                        "PPPAC_ACCT_DIGITS": len(
                            digits_only(
                                r["E_ACCOUNT_NUMBER"]
                                if e_ok
                                else r["P_ACCOUNT_NUMBER"]
                            )
                        ),
                        "PAC_DATE": r.get("PAC_DATE", ""),
                        "E_TRAN_CODE": r.get("E_TRAN_CODE", ""),
                        "PRENOTE_DATE": r.get("PRENOTE_DATE", ""),
                        "DUP_ROWS": len(rows),
                        "IN_PPACH": pol in ppach_any_row,
                        "PPACH_HAS_ACCT": pol in ppach_last_any_acct,
                    }
                )
        else:
            still_missing_acct += 1

    out(f"found in PPPAC: {found}")
    out(f"usable account in PPPAC: {usable_acct}")
    out(f"usable routing in PPPAC: {usable_routing}")
    out(f"both acct+routing: {both}")
    out(f"still missing account: {still_missing_acct}")
    out(f"not found: {not_found}")
    out(f"duplicate conflicting accounts: {dup_conflict}")
    out(f"masked/invalid present values among found: {masked_invalid}")
    out(f"found but blank/unusable account in PPPAC: {blank_in_pppac}")

    exc_with_pppac_acct = [
        pol
        for pol in exc_pols
        if pol in pppac_last
        and (
            is_usable_account(pppac_last[pol]["E_ACCOUNT_NUMBER"])
            or is_usable_account(pppac_last[pol]["P_ACCOUNT_NUMBER"])
        )
    ]
    out(f"exceptions rescued by PPPAC account: {len(exc_with_pppac_acct)}")
    out(
        f"of rescued, present in PPACH at all: {sum(1 for p in exc_with_pppac_acct if p in ppach_any_row)}"
    )
    out(
        f"of rescued, PPACH has usable acct: {sum(1 for p in exc_with_pppac_acct if p in ppach_last_any_acct)}"
    )
    out(
        f"exceptions with any PPACH rows: {sum(1 for p in exc_pols if p in ppach_any_row)}"
    )
    out(
        f"exceptions with NO PPACH rows: {sum(1 for p in exc_pols if p not in ppach_any_row)}"
    )

    # Why exception despite PPACH rows?
    blank_last = 0
    hist_but_blank_last = 0
    for p in exc_pols:
        hist = ppach[ppach["POL_N"] == p]
        if len(hist) == 0:
            continue
        h = hist.sort_values(by=["CHANGE_DATE", "CHANGE_TIME"]).iloc[-1]
        hist_but_blank_last += 1
        if not is_usable_account(h["E_ACCOUNT_NUMBER"]):
            blank_last += 1
    out(f"exceptions with PPACH rows: {hist_but_blank_last}")
    out(f"exceptions with PPACH rows but last E_ACCOUNT not usable: {blank_last}")

    out("\nSAMPLES (masked):")
    for s in samples[:12]:
        out(s)

    out("\n=== POLICY FORMAT ===")
    out(f"exc SOURCE_POLICY lens: {Counter(exc['SRC_POL_N'].str.len()).most_common(5)}")
    out(f"PPPAC POLICY lens: {Counter(pppac['POL_N'].str.len()).most_common(5)}")
    out(f"exc sample: {exc['SRC_POL_N'].head(3).tolist()}")
    out(f"PPPAC sample: {pppac['POL_N'].head(3).tolist()}")
    exc_stripped = set(p.lstrip("0") or "0" for p in exc_pols)
    pppac_stripped = set(p.lstrip("0") or "0" for p in pppac["POL_N"])
    out(f"exact match found: {found}")
    out(
        f"match after strip leading zeros (exc in pppac): {sum(1 for p in exc_stripped if p in pppac_stripped)}"
    )
    out(f"PAC_ID format sample: {pppac['PAC_ID'].head(3).tolist()}")
    out(
        f"PAC_ID == COMPANY+POLICY?: {(pppac['PAC_ID'] == (pppac['COMPANY_CODE'] + pppac['POLICY_NUMBER'])).mean()}"
    )

    # === FULL UNIVERSE PPACH vs PPPAC COMPARISON (PAC policies) ===
    out("\n=== PPACH vs PPPAC BANKING COMPARISON (all PPPAC policies) ===")
    # For each PPPAC policy, compare last usable accounts
    both_agree = 0
    both_differ = 0
    only_ppach = 0
    only_pppac = 0
    neither = 0
    differ_samples = []

    # universe: union of PAC policies and PPPAC/PPACH banking policies that are PAC
    universe = pac_pols | (pppac_pols & pac_pols)
    # Also compare on PPPAC policies that are bank-draft related
    compare_pols = pppac_pols | (ppach_any_row & pac_pols)

    # Focus comparison on bank-draft (PAC) policies from PPOLC
    for pol in sorted(pac_pols):
        p_acct = None
        p_aba = None
        if pol in ppach_last_any_acct:
            p_acct = digits_only(ppach_last_any_acct[pol]["acct"])
            p_aba = digits_only(ppach_last_any_acct[pol]["aba"]) if ppach_last_any_acct[pol]["aba"] else ""
        c_acct = None
        if pol in pppac_last:
            r = pppac_last[pol]
            if is_usable_account(r["E_ACCOUNT_NUMBER"]):
                c_acct = digits_only(r["E_ACCOUNT_NUMBER"])
            elif is_usable_account(r["P_ACCOUNT_NUMBER"]):
                c_acct = digits_only(r["P_ACCOUNT_NUMBER"])

        has_p = bool(p_acct)
        has_c = bool(c_acct)
        if has_p and has_c:
            if p_acct == c_acct:
                both_agree += 1
            else:
                both_differ += 1
                if len(differ_samples) < 10:
                    differ_samples.append(
                        {
                            "pol": pol,
                            "ppach": mask_acct(p_acct),
                            "pppac": mask_acct(c_acct),
                            "ppach_aba": mask_aba(p_aba) if p_aba else "",
                        }
                    )
        elif has_p and not has_c:
            only_ppach += 1
        elif has_c and not has_p:
            only_pppac += 1
        else:
            neither += 1

    out(f"PAC universe size: {len(pac_pols)}")
    out(f"both agree (account digits): {both_agree}")
    out(f"both differ: {both_differ}")
    out(f"only PPACH has account: {only_ppach}")
    out(f"only PPPAC has account: {only_pppac}")
    out(f"neither has usable account: {neither}")
    out(f"differ samples: {differ_samples}")

    # Among bank-draft policies that currently convert with PPACH (non-exceptions)
    out("\n=== NON-EXCEPTION BANK-DRAFT POLICIES ===")
    non_exc_pac = pac_pols - exc_pols
    out(f"PAC not in exceptions: {len(non_exc_pac)}")
    non_exc_with_ppach = sum(1 for p in non_exc_pac if p in ppach_last_any_acct)
    non_exc_with_pppac = sum(
        1
        for p in non_exc_pac
        if p in pppac_last
        and (
            is_usable_account(pppac_last[p]["E_ACCOUNT_NUMBER"])
            or is_usable_account(pppac_last[p]["P_ACCOUNT_NUMBER"])
        )
    )
    out(f"non-exc with PPACH usable acct: {non_exc_with_ppach}")
    out(f"non-exc with PPPAC usable acct: {non_exc_with_pppac}")

    # Cross-check: policies in exceptions file that match PPPAC count ~2133?
    out("\n=== BANK DRAFT COUNT CROSSCHECK ===")
    out(f"PPPAC total rows: {len(pppac)}")
    out(f"PPOLC PAC: {len(pac_pols)}")
    out(f"exceptions: {len(exc_pols)}")
    out(f"implied with banking from prior: 2132-763=1369")
    with_bank_est = len(pac_pols) - len(exc_pols)
    out(f"PAC minus exceptions: {with_bank_est}")

    # Check if PPPAC has spaces in accounts (common LifePRO padding)
    spaced = pppac.loc[pppac["ACCT_OK"], "E_ACCOUNT_NUMBER"].head(5).tolist()
    out(f"sample usable accounts (masked): {[mask_acct(x) for x in spaced]}")
    # Does account contain internal spaces?
    has_space = pppac["E_ACCOUNT_NUMBER"].str.contains(r"\s").sum()
    out(f"E_ACCOUNT_NUMBER values containing whitespace: {int(has_space)}")

    # PPACH ABA coverage for PPPAC-rescued exceptions
    out("\n=== ROUTING GAP FOR RESCUED EXCEPTIONS ===")
    rescued_with_ppach_aba = 0
    rescued_need_alt_aba = 0
    for p in exc_with_pppac_acct:
        if p in ppach_last_complete:
            rescued_with_ppach_aba += 1
        elif p in ppach_last_any_acct and ppach_last_any_acct[p]["aba"]:
            rescued_with_ppach_aba += 1
        else:
            # any historical ABA on any PPACH row?
            hist = ppach[(ppach["POL_N"] == p) & (ppach["ABA_OK"])]
            if len(hist):
                rescued_with_ppach_aba += 1
            else:
                rescued_need_alt_aba += 1
    out(f"rescued exceptions with some PPACH ABA history: {rescued_with_ppach_aba}")
    out(f"rescued exceptions with NO PPACH ABA anywhere: {rescued_need_alt_aba}")

    # Check aba_routing_lookup / RelationshipNameAddress availability for rescued
    aba_lk = SRC / "aba_routing_lookup.csv"
    if aba_lk.exists():
        lk = pd.read_csv(aba_lk, dtype=str).fillna("")
        lk.columns = [c.strip().upper() for c in lk.columns]
        out(f"aba_routing_lookup rows: {len(lk)} cols: {list(lk.columns)}")
        if "ACCOUNT_DIGITS" in lk.columns:
            lk_set = set(lk["ACCOUNT_DIGITS"].astype(str).str.strip())
            hit = 0
            for p in exc_with_pppac_acct:
                r = pppac_last[p]
                acct = digits_only(
                    r["E_ACCOUNT_NUMBER"]
                    if is_usable_account(r["E_ACCOUNT_NUMBER"])
                    else r["P_ACCOUNT_NUMBER"]
                )
                if acct in lk_set:
                    hit += 1
            out(f"rescued exceptions with account in aba_routing_lookup: {hit}")

    # Write raw stats sidecar (no full account numbers)
    stats_path = OUT / "_pppac_analysis_stats.txt"
    OUT.mkdir(parents=True, exist_ok=True)
    stats_path.write_text("\n".join(lines), encoding="utf-8")
    out(f"\nWrote {stats_path}")


if __name__ == "__main__":
    main()
