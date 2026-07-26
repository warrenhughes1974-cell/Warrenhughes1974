"""Dump every PACTG posting that touches the dividend accumulation account for a policy."""
import csv
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
PACTG = BASE / "QLA_Migration" / "Source" / "PACTG_Accounting_Extract20260630.csv"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10 ** 7)

wanted = set(sys.argv[1:]) or {"9010382426"}


def norm(v):
    s = "".join(c for c in str(v).strip() if c.isdigit())
    return s.zfill(4)[-4:] if s else ""


with open(PACTG, newline="", encoding="latin-1") as fh:
    reader = csv.reader(fh)
    header = [c.replace("\ufeff", "").strip().upper() for c in next(reader)]
    ix = {n: header.index(n) for n in (
        "CREDIT_CODE", "DEBIT_CODE", "POLICY_NUMBER", "TRANS_AMOUNT",
        "EFFECTIVE_DATE", "DATE_REVERSED", "TRANS_CODE",
    ) if n in header}
    hits = []
    for raw in reader:
        if len(raw) < len(header):
            continue
        pol = raw[ix["POLICY_NUMBER"]].strip()
        if pol not in wanted:
            continue
        cr, dr = norm(raw[ix["CREDIT_CODE"]]), norm(raw[ix["DEBIT_CODE"]])
        if "0310" not in (cr, dr):
            continue
        hits.append((
            raw[ix["EFFECTIVE_DATE"]].strip(), dr, cr,
            raw[ix["TRANS_AMOUNT"]].strip(),
            raw[ix["DATE_REVERSED"]].strip(),
            raw[ix.get("TRANS_CODE", 0)].strip() if "TRANS_CODE" in ix else "",
        ))

hits.sort()
print(f"{'EFF_DATE':<12}{'DR':<6}{'CR':<6}{'AMOUNT':>14}  {'REVERSED':<12}TRANS")
running = 0.0
for eff, dr, cr, amt, rev, tc in hits:
    val = float(amt or 0)
    sign = "+" if cr == "0310" else "-"
    running += val if cr == "0310" else -val
    print(f"{eff:<12}{dr:<6}{cr:<6}{sign}{val:>13,.2f}  {rev or '-':<12}{tc}   net {running:>12,.2f}")
print(f"\n{len(hits)} postings; net movement {running:,.2f}")
