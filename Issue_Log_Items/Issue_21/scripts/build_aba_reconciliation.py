from pathlib import Path
"""Issue 21H — ABA routing-number reconciliation builder.

Joins the policy/account data in PPACH to the authoritative full 9-digit ABA in
PROD_PPCOM_PACAccountInformation_Extract (E_TRAN_ABA_NUMBER) via the bank ACCOUNT
NUMBER (PAC_ID schemes differ between the two files and do not join directly).

Outputs (analysis artifacts only; the engine reads aba_routing_lookup.csv):
  - aba_routing_lookup.csv          account_digits -> full_aba (UNIQUE matches only)
  - issue21h_aba_reconciliation.csv per-policy: truncated vs recovered ABA + status
  - issue21h_ambiguous_accounts.csv accounts that map to >1 routing number (client review)

Run:  python build_aba_reconciliation.py
Re-runnable and side-effect free apart from writing the three CSVs.
"""
import csv
import os
import re

REPO = Path(__file__).resolve().parents[2]
SRC = str(REPO / "QLA_Migration" / "Source")
PPACH = os.path.join(SRC, "PPACH.csv")
PPCOM = os.path.join(SRC, "PROD_PPCOM_PACAccountInformation_Extract_20260530.csv")
OUT_DIR = str(REPO / "Issue_Log_Items" / "Issue_21" / "evidence")
LOOKUP_OUT = os.path.join(OUT_DIR, "aba_routing_lookup.csv")
LOOKUP_ENGINE = os.path.join(SRC, "aba_routing_lookup.csv")  # location the converter reads
RECON_OUT = os.path.join(OUT_DIR, "issue21h_aba_reconciliation.csv")
AMBIG_OUT = os.path.join(OUT_DIR, "issue21h_ambiguous_accounts.csv")

# PPCOM column indices (37-col layout)
I_DATE, I_ACCT, I_ABA = 0, 8, 9


def clean(v):
    s = str(v or "").strip()
    if s.endswith(".0"):
        s = s[:-2]
    if s.lower() in ("nan", "none", "null"):
        s = ""
    return s


def digits(v):
    return re.sub(r"\D", "", str(v or ""))


def checksum_ok(a):
    if len(a) != 9 or not a.isdigit():
        return False
    d = [int(x) for x in a]
    return (3 * (d[0] + d[3] + d[6]) + 7 * (d[1] + d[4] + d[7]) + 1 * (d[2] + d[5] + d[8])) % 10 == 0


def normalize_aba(a):
    """Recover a 9-digit ABA. 8-digit values in PPCOM are leading-zero truncated."""
    a = clean(a)
    if not a.isdigit():
        return ""
    if len(a) == 8:
        a = a.zfill(9)
    return a if len(a) == 9 else ""


def main():
    # 1) in-scope accounts from PPACH (policy -> latest truncated aba + account)
    acct2pol = {}
    pol_rows = {}  # policy -> (acct_digits, acct_raw, ppach_aba_trunc, change_date)
    with open(PPACH, encoding="latin1", newline="") as fh:
        r = csv.DictReader(fh)
        r.fieldnames = [c.strip().upper() for c in r.fieldnames]
        for row in r:
            pol = clean(row.get("POLICY_NUMBER"))
            acct_raw = clean(row.get("E_ACCOUNT_NUMBER"))
            acct = digits(acct_raw)
            aba = clean(row.get("E_ABA_NUM"))
            cd = clean(row.get("CHANGE_DATE"))
            if not pol or not acct:
                continue
            acct2pol.setdefault(acct, set()).add(pol)
            prev = pol_rows.get(pol)
            if prev is None or cd >= prev[3]:
                pol_rows[pol] = (acct, acct_raw, aba, cd)
    print(f"PPACH: {len(acct2pol)} distinct in-scope accounts, {len(pol_rows)} policies")

    # 2) resolve full ABA per in-scope account from PPCOM
    acct_cand = {}  # acct_digits -> {norm_aba: latest_date}
    scanned = 0
    with open(PPCOM, encoding="latin1", newline="") as fh:
        r = csv.reader(fh)
        next(r)
        for row in r:
            if len(row) != 37:
                continue
            acct = digits(row[I_ACCT])
            if acct not in acct2pol:
                continue
            aba = normalize_aba(row[I_ABA])
            if not aba:
                continue
            dt = clean(row[I_DATE])
            cand = acct_cand.setdefault(acct, {})
            if aba not in cand or dt >= cand[aba]:
                cand[aba] = dt
            scanned += 1
    print(f"PPCOM: matched {scanned} rows across {len(acct_cand)} in-scope accounts")

    # 3) choose ABA per account (latest date; flag ambiguous)
    lookup = {}   # acct_digits -> full_aba (unique only)
    chosen = {}   # acct_digits -> (full_aba, status, candidate_count)
    ambiguous = []
    for acct, cand in acct_cand.items():
        distinct = list(cand.keys())
        best = max(distinct, key=lambda a: cand[a])  # latest date
        if len(distinct) == 1:
            status = "unique"
            lookup[acct] = best
        else:
            status = "ambiguous"
            ambiguous.append((acct, ";".join(sorted(distinct)), best))
        chosen[acct] = (best, status, len(distinct))

    # 4) write engine lookup (unique only) + a copy in Source for the converter
    for path in (LOOKUP_OUT, LOOKUP_ENGINE):
        with open(path, "w", encoding="latin1", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["ACCOUNT_DIGITS", "FULL_ABA"])
            for acct in sorted(lookup):
                w.writerow([acct, lookup[acct]])
    print(f"Wrote {len(lookup)} unique account->ABA pairs to lookup ({LOOKUP_OUT})")

    # 5) per-policy reconciliation
    counts = {"recovered_unique": 0, "ambiguous": 0, "not_found": 0, "unchanged": 0}
    with open(RECON_OUT, "w", encoding="latin1", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["POLICY_NUMBER", "ACCOUNT_RAW", "ACCOUNT_DIGITS",
                    "PPACH_ABA_TRUNCATED", "PPCOM_FULL_ABA", "STATUS", "CANDIDATE_COUNT"])
        for pol in sorted(pol_rows):
            acct, acct_raw, trunc, _cd = pol_rows[pol]
            if acct in chosen:
                full, status, cc = chosen[acct]
                if status == "unique":
                    counts["recovered_unique"] += 1
                else:
                    counts["ambiguous"] += 1
            else:
                full, status, cc = "", "not_found", 0
                counts["not_found"] += 1
            w.writerow([pol, acct_raw, acct, trunc, full, status, cc])
    print(f"Wrote per-policy reconciliation ({RECON_OUT})")

    # 6) ambiguous accounts for client review
    with open(AMBIG_OUT, "w", encoding="latin1", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ACCOUNT_DIGITS", "CANDIDATE_ABAS", "CHOSEN_LATEST"])
        for acct, cands, best in sorted(ambiguous):
            w.writerow([acct, cands, best])
    print(f"Wrote {len(ambiguous)} ambiguous accounts ({AMBIG_OUT})")

    print("SUMMARY:", counts)


if __name__ == "__main__":
    main()
