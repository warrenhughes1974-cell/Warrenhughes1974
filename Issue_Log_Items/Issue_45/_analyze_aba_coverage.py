"""Issue 45 — ABA coverage for PPPAC-rescued exceptions (read-only)."""
import pandas as pd
import re
from pathlib import Path

SRC = Path(r"c:\Users\warren\Documents\GitHub\Warrenhughes1974\QLA_Migration\Source")
REP = Path(r"c:\Users\warren\Documents\GitHub\Warrenhughes1974\QLA_Migration\Reports")


def digits(s):
    return re.sub(r"\D", "", str(s or ""))


def norm(p):
    s = str(p).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return re.sub(r"\s+", "", s)


def usable_aba(a):
    d = digits(a)
    return len(d) >= 5 and set(d) != {"0"}


def load_pppac():
    df = pd.read_csv(
        SRC / "PPPAC_PACDetail_Extract_20260630.csv",
        dtype=str,
        encoding="latin1",
        low_memory=False,
        on_bad_lines="skip",
    ).fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    df = df[
        ~df["POLICY_NUMBER"].map(
            lambda v: bool(str(v).strip()) and set(str(v).strip()) <= {"-", " "}
        )
    ].copy()
    df["POL"] = df["POLICY_NUMBER"].map(norm)
    df["ACCT"] = df["E_ACCOUNT_NUMBER"].map(digits)
    return df


def main():
    exc = pd.read_csv(
        REP / "bank_draft_account_exceptions.csv", dtype=str
    ).fillna("")
    exc.columns = [c.strip().upper() for c in exc.columns]
    exc["POL"] = exc["SOURCE_POLICY"].map(norm)
    pppac = load_pppac()
    acct_by_pol = dict(zip(pppac["POL"], pppac["ACCT"]))
    rescued = [
        p
        for p in exc["POL"]
        if p in acct_by_pol and len(acct_by_pol[p]) >= 4
    ]
    print("rescued count", len(rescued))

    hdr = pd.read_csv(
        SRC / "RelationshipNameAddress_Extract_20260630.csv",
        dtype=str,
        encoding="latin1",
        nrows=0,
    )
    raw_cols = list(hdr.columns)
    colmap = {c.strip().upper(): c for c in raw_cols}
    need = ["POLICY_NUMBER", "ELEC_ABA_NUMBER", "PAPER_ABA_NUM"]
    use = [colmap[c] for c in need if c in colmap]
    print("RNA cols", use)
    rna = pd.read_csv(
        SRC / "RelationshipNameAddress_Extract_20260630.csv",
        dtype=str,
        encoding="latin1",
        usecols=use,
        low_memory=False,
        on_bad_lines="skip",
    ).fillna("")
    rna.columns = [c.strip().upper() for c in rna.columns]
    rna["POL"] = rna["POLICY_NUMBER"].map(norm)

    # index RNA by policy for speed
    rna_by = {}
    for _, r in rna.iterrows():
        rna_by.setdefault(r["POL"], []).append(r)

    rna_hit = 0
    rna_blank = 0
    multi = 0
    samples = []
    for p in rescued:
        rows = rna_by.get(p, [])
        abas = set()
        for r in rows:
            for c in ["ELEC_ABA_NUMBER", "PAPER_ABA_NUM"]:
                if c in r and usable_aba(r[c]):
                    abas.add(digits(r[c]))
        if abas:
            rna_hit += 1
            if len(abas) > 1:
                multi += 1
            if len(samples) < 5:
                samples.append((p, [a[-4:] for a in abas], len(rows)))
        else:
            rna_blank += 1
    print("rescued with RNA ABA:", rna_hit)
    print("rescued without RNA ABA:", rna_blank)
    print("rescued with multiple distinct RNA ABAs:", multi)
    print("samples last4:", samples)

    lk = pd.read_csv(SRC / "aba_routing_lookup.csv", dtype=str).fillna("")
    lk.columns = [c.strip().upper() for c in lk.columns]
    lk_map = {}
    for _, r in lk.iterrows():
        k = digits(r["ACCOUNT_DIGITS"]).lstrip("0") or "0"
        lk_map[k] = digits(r["FULL_ABA"])

    lookup_hit = sum(
        1
        for p in rescued
        if (acct_by_pol[p].lstrip("0") or "0") in lk_map
    )
    either = 0
    neither = 0
    both = 0
    only_lk = 0
    only_rna = 0
    for p in rescued:
        acct = acct_by_pol[p].lstrip("0") or "0"
        has_lk = acct in lk_map
        rows = rna_by.get(p, [])
        has_rna = any(
            usable_aba(r.get("ELEC_ABA_NUMBER", ""))
            or usable_aba(r.get("PAPER_ABA_NUM", ""))
            for r in rows
        )
        if has_lk and has_rna:
            both += 1
            either += 1
        elif has_lk:
            only_lk += 1
            either += 1
        elif has_rna:
            only_rna += 1
            either += 1
        else:
            neither += 1
    print("rescued lookup hit:", lookup_hit)
    print("rescued both lk+rna:", both)
    print("rescued only lookup:", only_lk)
    print("rescued only RNA:", only_rna)
    print("rescued with lookup OR RNA ABA:", either)
    print("rescued with NEITHER routing source:", neither)

    # PPACH STATUS_CODE D meaning for conflicts
    ppach = pd.read_csv(
        SRC / "PPACH_PACHistory_Extract_20260630.csv",
        dtype=str,
        encoding="latin1",
        low_memory=False,
        on_bad_lines="skip",
    ).fillna("")
    ppach.columns = [c.strip().upper() for c in ppach.columns]
    ppach = ppach[
        ~ppach["POLICY_NUMBER"].map(
            lambda v: bool(str(v).strip()) and set(str(v).strip()) <= {"-", " "}
        )
    ]
    print("PPACH STATUS_CODE counts:", ppach["STATUS_CODE"].value_counts().to_dict())

    # neither PAC: 15 breakdown
    ppolc = pd.read_csv(
        SRC / "PPOLC_PolicyMaster_Extract_20260630.csv",
        dtype=str,
        encoding="latin1",
        low_memory=False,
        on_bad_lines="skip",
    ).fillna("")
    ppolc.columns = [c.strip().upper() for c in ppolc.columns]
    ppolc = ppolc[
        ~ppolc["POLICY_NUMBER"].map(
            lambda v: bool(str(v).strip()) and set(str(v).strip()) <= {"-", " "}
        )
    ]
    ppolc["POL"] = ppolc["POLICY_NUMBER"].map(norm)
    pac = set(ppolc.loc[ppolc["BILLING_FORM"].str.upper().str.strip() == "PAC", "POL"])
    pppac_pols = set(pppac["POL"])
    # neither: PAC without usable PPPAC acct and without PPACH - already know 15
    # 13 missing from PPPAC + 2 too-short in PPPAC that are PAC?
    short = [p for p, a in acct_by_pol.items() if len(a) < 4]
    print("short acct pols:", short, "in PAC?", [p in pac for p in short])
    print("short in exceptions?", [p in set(exc["POL"]) for p in short])


if __name__ == "__main__":
    main()
