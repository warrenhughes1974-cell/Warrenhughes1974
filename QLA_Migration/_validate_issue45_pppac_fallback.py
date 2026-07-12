"""
Issue #45 — validate PPPAC account fallback for bank-draft MBANKNO.

Read-only checks against Source extracts (simulates v57.77 banking cache rules):
1. PPPAC fallback candidates ~750; recoverable with ABA ~748
2. Trace policies 010157076C, 010161748C, 010348734C resolve account+ABA
3. PPACH-primary policies (non-exception) retain PPACH account digits
4. Exception fleet shrinks from 763 toward ~15
5. No full account/routing numbers printed (masked)

Exit 0 on PASS, 1 on FAIL.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

MIG = Path(__file__).resolve().parent
SRC = MIG / "Source"
REP = MIG / "Reports"
CW = MIG / "Mapping" / "Master_Crosswalk.csv"
EVIDENCE = MIG.parent / "Issue_Log_Items" / "Issue_45" / "evidence"
EVIDENCE.mkdir(parents=True, exist_ok=True)

TRACE_MPOLICIES = ("010157076C", "010161748C", "010348734C")
NEITHER_SOURCE = ("9015000043",)


def digits(s: str) -> str:
    return re.sub(r"\D", "", str(s or ""))


def norm_pol(p) -> str:
    s = str(p).strip().upper()
    if s.endswith(".0"):
        s = s[:-2]
    return re.sub(r"\s+", "", s)


def usable_account(acct_raw: str) -> str:
    raw = str(acct_raw or "").strip()
    if not raw or raw.lower() in ("nan", "none", ""):
        return ""
    if re.search(r"[xX*]{2,}|REDACT|MASK|HIDDEN|XXXX", raw, re.I):
        return ""
    acct_d = digits(raw)
    if not acct_d or set(acct_d) <= {"0"} or len(acct_d) < 4:
        return ""
    if acct_d in ("1234", "123456", "123456789", "0000", "1111", "9999", "999999999"):
        return ""
    return re.sub(r"\s+", "", raw)


def lookup_aba(acct_d: str, aba_lookup: dict) -> tuple[str, str]:
    for lk_key in (acct_d, acct_d.lstrip("0") or "0", acct_d.zfill(17)):
        full = aba_lookup.get(lk_key)
        if not full:
            continue
        aba = digits(str(full).strip())
        if len(aba) >= 5 and set(aba) != {"0"}:
            return aba, "LOOKUP"
    return "", ""


def mask_bank(mbankno: str) -> str:
    if not mbankno or "/" not in mbankno:
        return mbankno or "(blank)"
    aba, acct = mbankno.split("/", 1)
    ad, cd = digits(aba), digits(acct)
    return f"*****{ad[-4:] if len(ad) >= 4 else '????'}/****{cd[-4:] if len(cd) >= 4 else '????'}"


def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", low_memory=False, on_bad_lines="skip").fillna("")
    df.columns = [str(c).strip().upper() for c in df.columns]
    key = "POLICY_NUMBER" if "POLICY_NUMBER" in df.columns else df.columns[0]
    mask = ~df[key].map(lambda v: bool(str(v).strip()) and set(str(v).strip()) <= {"-", " "})
    return df.loc[mask].copy()


def build_bank_maps() -> dict:
    aba_lookup = {}
    lk_path = SRC / "aba_routing_lookup.csv"
    if lk_path.is_file():
        lk = pd.read_csv(lk_path, dtype=str).fillna("")
        lk.columns = [c.strip().upper() for c in lk.columns]
        aba_lookup = dict(zip(lk["ACCOUNT_DIGITS"].astype(str).str.strip(), lk["FULL_ABA"].astype(str).str.strip()))

    ppach = load_csv(SRC / "PPACH_PACHistory_Extract_20260630.csv")
    ppach = ppach.sort_values(["CHANGE_DATE", "CHANGE_TIME"], ascending=[True, True])
    bank_map: dict[str, str] = {}
    meta: dict[str, dict] = {}
    for _, r in ppach.iterrows():
        pol = norm_pol(r.get("POLICY_NUMBER", ""))
        aba = str(r.get("E_ABA_NUM", "")).strip()
        acct = str(r.get("E_ACCOUNT_NUMBER", "")).strip()
        if aba.endswith(".0"):
            aba = aba[:-2]
        if acct.endswith(".0"):
            acct = acct[:-2]
        if pol and aba and acct and aba.lower() not in ("nan", "none", "") and acct.lower() not in ("nan", "none", ""):
            full_aba = lookup_aba(digits(acct), aba_lookup)[0] or digits(aba)
            bank_map[pol] = f"{full_aba}/{acct}"
            meta[pol] = {"aba": full_aba, "account": acct, "bank_source": "PPACH"}

    rna_aba_by_pol: dict[str, list[str]] = {}
    rna_path = SRC / "RelationshipNameAddress_Extract_20260630.csv"
    if rna_path.is_file():
        rna = pd.read_csv(
            rna_path,
            dtype=str,
            encoding="latin1",
            usecols=lambda c: c.strip().upper() in ("POLICY_NUMBER", "ELEC_ABA_NUMBER", "PAPER_ABA_NUM"),
            low_memory=False,
            on_bad_lines="skip",
        ).fillna("")
        rna.columns = [c.strip().upper() for c in rna.columns]
        for _, rr in rna.iterrows():
            pol = norm_pol(rr.get("POLICY_NUMBER", ""))
            if not pol:
                continue
            abas = set(rna_aba_by_pol.get(pol, []))
            for col in ("ELEC_ABA_NUMBER", "PAPER_ABA_NUM"):
                if col not in rna.columns:
                    continue
                aba_d = digits(str(rr.get(col, "")).strip())
                if len(aba_d) >= 5 and set(aba_d) != {"0"}:
                    abas.add(aba_d)
            if abas:
                rna_aba_by_pol[pol] = sorted(abas)

    pppac = load_csv(SRC / "PPPAC_PACDetail_Extract_20260630.csv")
    pppac_only: dict[str, dict] = {}
    fallback = 0
    for _, pr in pppac.iterrows():
        pol = norm_pol(pr.get("POLICY_NUMBER", ""))
        if not pol or pol in bank_map:
            continue
        display_acct = usable_account(str(pr.get("E_ACCOUNT_NUMBER", "")).strip())
        if not display_acct:
            continue
        acct_d = digits(display_acct)
        use_aba, aba_src = lookup_aba(acct_d, aba_lookup)
        if not use_aba:
            pol_abas = rna_aba_by_pol.get(pol, [])
            if len(pol_abas) == 1:
                use_aba, aba_src = pol_abas[0], "RNA"
            elif len(pol_abas) > 1:
                pppac_only[pol] = {"account": display_acct, "aba_source": "RNA_AMBIGUOUS"}
                continue
        if not use_aba:
            pppac_only[pol] = {"account": display_acct, "aba_source": ""}
            continue
        bank_map[pol] = f"{use_aba}/{display_acct}"
        meta[pol] = {"aba": use_aba, "account": display_acct, "bank_source": "PPPAC", "aba_source": aba_src}
        fallback += 1

    # Prefer pre-batch snapshot when present (post-batch exception file is already reduced).
    before_exc = (
        MIG.parent
        / "Issue_Log_Items"
        / "Issue_45"
        / "evidence"
        / "before_batch_v57.77"
        / "bank_draft_account_exceptions.csv"
    )
    exc_path = before_exc if before_exc.is_file() else (REP / "bank_draft_account_exceptions.csv")
    old_exc_pols = set()
    if exc_path.is_file():
        exc = pd.read_csv(exc_path, dtype=str).fillna("")
        exc.columns = [c.strip().upper() for c in exc.columns]
        old_exc_pols = set(exc["SOURCE_POLICY"].map(norm_pol))

    ppolc = load_csv(SRC / "PPOLC_PolicyMaster_Extract_20260630.csv")
    pac_pols = set(ppolc.loc[ppolc["BILLING_FORM"].str.upper().str.strip() == "PAC", "POLICY_NUMBER"].map(norm_pol))

    still_exc = []
    for pol in sorted(old_exc_pols):
        if pol not in bank_map:
            still_exc.append(pol)

    rescued = old_exc_pols - set(still_exc)

    cw = pd.read_csv(CW, dtype=str).fillna("") if CW.is_file() else pd.DataFrame()
    pol_to_mpolicy = {}
    if not cw.empty and "Old_Value" in cw.columns and "New_Value" in cw.columns:
        for _, r in cw.iterrows():
            pol_to_mpolicy[norm_pol(r["Old_Value"])] = str(r["New_Value"]).strip()

    return {
        "bank_map": bank_map,
        "meta": meta,
        "pppac_only": pppac_only,
        "fallback": fallback,
        "old_exc_count": len(old_exc_pols),
        "still_exc": still_exc,
        "rescued": rescued,
        "pac_pols": pac_pols,
        "pol_to_mpolicy": pol_to_mpolicy,
    }


def main() -> int:
    errors: list[str] = []
    data = build_bank_maps()
    bank_map = data["bank_map"]
    meta = data["meta"]
    pol_to_mpolicy = data["pol_to_mpolicy"]

    print("=== Issue #45 PPPAC fallback validation ===")
    print(f"PPPAC fallback applied (sim): {data['fallback']}")
    print(f"Old exceptions: {data['old_exc_count']}")
    print(f"Still exceptions (sim): {len(data['still_exc'])}")
    print(f"Rescued from old exception set: {len(data['rescued'])}")

    if data["fallback"] < 700:
        errors.append(f"PPPAC fallback count too low: {data['fallback']} (expected ~750)")
    if len(data["rescued"]) < 700:
        errors.append(f"Rescued count too low: {len(data['rescued'])} (expected ~748)")
    if len(data["still_exc"]) > 25:
        errors.append(f"Remaining exceptions too high: {len(data['still_exc'])} (expected ~15)")

    for mp in TRACE_MPOLICIES:
        src_pol = ""
        for pol, mpol in pol_to_mpolicy.items():
            if mpol == mp:
                src_pol = pol
                break
        if not src_pol:
            errors.append(f"Trace policy {mp} not in crosswalk")
            continue
        mb = bank_map.get(src_pol, "")
        if not mb or "/" not in mb:
            errors.append(f"Trace {mp} ({src_pol}): expected MBANKNO, got blank")
        else:
            m = meta.get(src_pol, {})
            print(f"Trace {mp}: {mask_bank(mb)} source={m.get('bank_source')} aba_src={m.get('aba_source')}")

    for pol in NEITHER_SOURCE:
        if pol in bank_map:
            errors.append(f"Neither-source policy {pol} should remain without banking")

    # PPACH-primary: non-exception policies should still use PPACH source
    ppach_primary = [p for p, m in meta.items() if m.get("bank_source") == "PPACH" and p not in data["rescued"]]
    if len(ppach_primary) < 1300:
        errors.append(f"PPACH-primary count low: {len(ppach_primary)}")

    # Write masked evidence
    rows = []
    for pol in sorted(data["rescued"])[:20]:
        mp = pol_to_mpolicy.get(pol, "")
        rows.append({
            "MPOLICY": mp,
            "SOURCE_POLICY": pol,
            "MBANKNO_MASKED": mask_bank(bank_map.get(pol, "")),
            "BANK_SOURCE": meta.get(pol, {}).get("bank_source", ""),
            "ABA_SOURCE": meta.get(pol, {}).get("aba_source", ""),
        })
    if rows:
        pd.DataFrame(rows).to_csv(EVIDENCE / "issue45_rescued_sample_masked.csv", index=False)

    still_rows = [{"SOURCE_POLICY": p, "REASON": "no_account_or_aba"} for p in data["still_exc"][:20]]
    if still_rows:
        pd.DataFrame(still_rows).to_csv(EVIDENCE / "issue45_still_exception_sample.csv", index=False)

    if errors:
        print("FAIL:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
