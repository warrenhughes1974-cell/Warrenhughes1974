"""Issue #75 reopen — rebuild aba_routing_lookup.csv from June PPCOM.

Joins PPACH + PPPAC policy accounts to PPCOM by account digits (exact, then
strip-leading-zeros). Emits 9-digit ABA only when native 9 or checksum-valid
pad of PPCOM 8-digit. Ambiguous accounts use latest EFFECTIVE_DATE.

Outputs:
  - QLA_Migration/Source/aba_routing_lookup.csv  (engine)
  - Issue_Log_Items/Issue_75/evidence/aba_routing_lookup.csv
  - Issue_Log_Items/Issue_75/evidence/issue75_ppcom_ambiguous_accounts.csv
"""
from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "QLA_Migration" / "Source"
EV = ROOT / "Issue_Log_Items" / "Issue_75" / "evidence"

PPCOM = SRC / "PPCOM_PACAccountInformation_Extract_20260630.csv"
PPACH = SRC / "PPACH_PACHistory_Extract_20260630.csv"
PPPAC = SRC / "PPPAC_PACDetail_Extract_20260630.csv"

I_DATE, I_ACCT, I_ABA = 0, 8, 9


def clean(v: str) -> str:
    s = str(v or "").strip()
    if s.endswith(".0"):
        s = s[:-2]
    if s.lower() in ("nan", "none", "null"):
        return ""
    return s


def digits(v: str) -> str:
    return re.sub(r"\D", "", str(v or ""))


def checksum_ok(a: str) -> bool:
    if len(a) != 9 or not a.isdigit():
        return False
    d = [int(x) for x in a]
    return (3 * (d[0] + d[3] + d[6]) + 7 * (d[1] + d[4] + d[7]) + (d[2] + d[5] + d[8])) % 10 == 0


def to_aba9(raw: str) -> str:
    a = digits(raw)
    if len(a) == 9 and checksum_ok(a) and set(a) != {"0"}:
        return a
    if len(a) == 8:
        p = a.zfill(9)
        if checksum_ok(p):
            return p
    return ""


def collect_source_accounts() -> tuple[set[str], dict[str, set[str]]]:
    """Return target account digits + strip-index -> exact forms."""
    targets: set[str] = set()
    strip_index: dict[str, set[str]] = defaultdict(set)

    def add_acct(acct_raw: str) -> None:
        ad = digits(clean(acct_raw))
        if len(ad) < 4 or set(ad) == {"0"}:
            return
        targets.add(ad)
        strip_index[ad.lstrip("0") or "0"].add(ad)

    if PPACH.is_file():
        with PPACH.open(encoding="latin1", newline="") as fh:
            r = csv.DictReader(fh)
            r.fieldnames = [c.strip().upper() for c in (r.fieldnames or [])]
            for row in r:
                add_acct(row.get("E_ACCOUNT_NUMBER", ""))

    if PPPAC.is_file():
        with PPPAC.open(encoding="latin1", newline="") as fh:
            r = csv.DictReader(fh)
            r.fieldnames = [c.strip().upper() for c in (r.fieldnames or [])]
            for row in r:
                add_acct(row.get("E_ACCOUNT_NUMBER", ""))

    return targets, strip_index


def main() -> int:
    EV.mkdir(parents=True, exist_ok=True)
    targets, strip_index = collect_source_accounts()
    print(f"Source accounts in scope: {len(targets)}")

    # acct_exact -> {aba9: latest_date}
    cand: dict[str, dict[str, str]] = defaultdict(dict)
    scanned = hits = 0
    with PPCOM.open(encoding="latin1", newline="") as fh:
        r = csv.reader(fh)
        next(r, None)
        for row in r:
            scanned += 1
            if len(row) < 10:
                continue
            acct_raw = clean(row[I_ACCT])
            if not acct_raw or set(acct_raw) <= {"-"}:
                continue
            ad = digits(acct_raw)
            if not ad:
                continue
            match_keys: list[str] = []
            if ad in targets:
                match_keys = [ad]
            else:
                st = ad.lstrip("0") or "0"
                if st in strip_index:
                    match_keys = list(strip_index[st])
            if not match_keys:
                continue
            aba9 = to_aba9(row[I_ABA])
            if not aba9:
                continue
            dt = clean(row[I_DATE])
            for mk in match_keys:
                prev = cand[mk].get(aba9, "")
                if dt >= prev:
                    cand[mk][aba9] = dt
            hits += 1
            if scanned % 500000 == 0:
                print(f"... scanned {scanned:,} hits {hits:,}")

    print(f"PPCOM scanned {scanned:,} hits {hits:,} matched accts {len(cand)}")

    lookup: dict[str, str] = {}
    ambiguous: list[tuple[str, str, str, int]] = []
    unique = ambig = none = 0
    for acct in sorted(targets):
        cands = cand.get(acct, {})
        if not cands:
            none += 1
            continue
        distinct = list(cands.keys())
        best = max(distinct, key=lambda a: cands[a])
        if len(distinct) == 1:
            unique += 1
            status = "unique"
        else:
            ambig += 1
            status = "ambiguous_latest"
            ambiguous.append((acct, ";".join(sorted(distinct)), best, len(distinct)))
        lookup[acct] = best
        # Also index stripped form when not colliding with a different ABA
        stripped = acct.lstrip("0") or "0"
        if stripped != acct:
            existing = lookup.get(stripped)
            if existing is None or existing == best:
                lookup[stripped] = best

    engine_path = SRC / "aba_routing_lookup.csv"
    evidence_path = EV / "aba_routing_lookup.csv"
    for path in (engine_path, evidence_path):
        with path.open("w", encoding="latin1", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["ACCOUNT_DIGITS", "FULL_ABA"])
            for acct in sorted(lookup):
                w.writerow([acct, lookup[acct]])

    ambig_path = EV / "issue75_ppcom_ambiguous_accounts.csv"
    with ambig_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ACCOUNT_DIGITS", "CANDIDATE_ABAS", "CHOSEN_LATEST", "CANDIDATE_COUNT"])
        for row in sorted(ambiguous):
            w.writerow(row)

    print(
        f"SUMMARY unique={unique} ambiguous_latest={ambig} not_found={none} "
        f"lookup_keys={len(lookup)}"
    )
    print(f"Wrote {engine_path}")
    print(f"Wrote {evidence_path}")
    print(f"Wrote {ambig_path} ({len(ambiguous)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
