"""Apply Issue #75 PPCOM MBANKNO fills to Output/quikmstr.csv using converter helpers.

Mirrors v58.35 PPACH/PPPAC + aba_routing_lookup path (MBANKNO column only).
Run after rebuild_aba_routing_lookup_from_ppcom.py. Full batch still preferred for UAT.
"""
from __future__ import annotations

import csv
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "QLA_Migration" / "Source"
OUT = ROOT / "QLA_Migration" / "Output" / "quikmstr.csv"
EV = ROOT / "Issue_Log_Items" / "Issue_75" / "evidence"
REPORTS = ROOT / "QLA_Migration" / "Reports"


def main() -> int:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "QLA_Migration"))
    import app as qla_app  # noqa: WPS433

    eng = qla_app.QLAdminEnterpriseIntegrationSuite.__new__(
        qla_app.QLAdminEnterpriseIntegrationSuite
    )

    lk = {}
    with (SRC / "aba_routing_lookup.csv").open(encoding="latin1", newline="") as fh:
        for row in csv.DictReader(fh):
            lk[(row.get("ACCOUNT_DIGITS") or "").strip()] = (row.get("FULL_ABA") or "").strip()

    def norm_pol(p: str) -> str:
        p = (p or "").strip()
        if not p:
            return ""
        return p if p.endswith("C") else p + "C"

    # latest PPACH per policy
    ppach = {}
    with (SRC / "PPACH_PACHistory_Extract_20260630.csv").open(encoding="latin1", newline="") as fh:
        r = csv.DictReader(fh)
        r.fieldnames = [c.strip().upper() for c in (r.fieldnames or [])]
        for row in r:
            pol = eng.normalize(row.get("POLICY_NUMBER"))
            if not pol:
                continue
            cd = (row.get("CHANGE_DATE") or "").strip()
            ct = (row.get("CHANGE_TIME") or "").strip()
            prev = ppach.get(pol)
            if prev is None or (cd, ct) >= prev["key"]:
                ppach[pol] = {
                    "key": (cd, ct),
                    "acct": row.get("E_ACCOUNT_NUMBER") or "",
                    "aba": row.get("E_ABA_NUM") or "",
                }

    pppac = {}
    with (SRC / "PPPAC_PACDetail_Extract_20260630.csv").open(encoding="latin1", newline="") as fh:
        r = csv.DictReader(fh)
        r.fieldnames = [c.strip().upper() for c in (r.fieldnames or [])]
        for row in r:
            pol = eng.normalize(row.get("POLICY_NUMBER"))
            if not pol:
                continue
            acct = row.get("E_ACCOUNT_NUMBER") or ""
            if eng._issue75_usable_acct_digits(acct):
                pppac[pol] = acct

    bank_map = {}
    meta = {}
    for pol, rec in ppach.items():
        acct_d = eng._issue75_usable_acct_digits(rec["acct"])
        if not acct_d:
            continue
        aba = eng._issue75_usable_aba_digits(rec["aba"], acct_d, lk)
        mb = eng._issue75_build_mbankno(aba, acct_d)
        if mb:
            bank_map[pol] = mb
            meta[pol] = ("PPACH", aba, acct_d)

    for pol, acct_raw in pppac.items():
        if pol in bank_map:
            continue
        acct_d = eng._issue75_usable_acct_digits(acct_raw)
        if not acct_d:
            continue
        aba = eng._issue45_lookup_aba_for_account(acct_d, lk)
        mb = eng._issue75_build_mbankno(aba, acct_d)
        if mb:
            bank_map[pol] = mb
            meta[pol] = ("PPPAC", aba, acct_d)

    print(f"bank_map size={len(bank_map)} lookup_keys={len(lk)}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = EV / f"quikmstr_before_issue75_v5835_{ts}.csv"
    EV.mkdir(parents=True, exist_ok=True)
    shutil.copy2(OUT, backup)

    rows = []
    with OUT.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fields = reader.fieldnames or []
        changed = filled_new = unchanged = blanked = 0
        audit = []
        for row in reader:
            pol = (row.get("MPOLICY") or "").strip()
            # Converter bank_map keys = source POLICY_NUMBER (no trailing C); Output MPOLICY has C.
            src_key = pol[:-1] if pol.endswith("C") else pol
            src_key = eng.normalize(src_key)
            pulled = bank_map.get(src_key) or bank_map.get(pol)
            before = (row.get("MBANKNO") or "").strip()
            bf = (row.get("MBILLFRM") or "").strip()
            after = before
            if pulled and eng._issue75_mbankno_is_ql_safe(pulled):
                after = pulled
            elif bf == "2" and before and not eng._issue75_mbankno_is_ql_safe(before):
                after = ""
                blanked += 1
            if after != before:
                changed += 1
                if before == "" and after:
                    filled_new += 1
                src, aba, acct = meta.get(src_key) or meta.get(pol) or ("", "", "")
                audit.append(
                    {
                        "MPOLICY": pol,
                        "MBILLFRM": bf,
                        "MBANKNO_BEFORE": before,
                        "MBANKNO_AFTER": after,
                        "BANK_SOURCE": src,
                        "ABA": aba,
                        "ACCT": acct,
                    }
                )
            else:
                unchanged += 1
            row["MBANKNO"] = after
            rows.append(row)

    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    REPORTS.mkdir(parents=True, exist_ok=True)
    audit_path = REPORTS / "issue75_ppcom_mbankno_apply_audit.csv"
    with audit_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=["MPOLICY", "MBILLFRM", "MBANKNO_BEFORE", "MBANKNO_AFTER", "BANK_SOURCE", "ABA", "ACCT"],
        )
        w.writeheader()
        w.writerows(audit)

    tv = ROOT / "QLA_Migration" / "Output" / "Test_Validation"
    tv.mkdir(parents=True, exist_ok=True)
    shutil.copy2(OUT, tv / "quikmstr.csv")

    print(f"changed={changed} newly_filled={filled_new} blanked_unsafe={blanked} unchanged={unchanged}")
    print(f"backup={backup}")
    print(f"audit={audit_path}")
    print(f"published Test_Validation/quikmstr.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
