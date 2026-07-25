"""
Issue #114 — is the dividend election code the debit leg, the credit leg, or both?

Emitting both legs double-counts a dividend. This measures the split and checks
whether credit-side rows always mirror a debit-side row on the same policy/date/amount.
READ-ONLY.
"""
import collections
import csv
import os

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PACTG = os.path.join(REPO, "QLA_Migration", "Source", "PACTG_Accounting_Extract20260630.csv")
ELECT = {"0514", "0515", "0516", "0517", "0518"}
csv.field_size_limit(10 ** 7)


def code(v):
    s = "".join(c for c in str(v).strip() if c.isdigit())
    return s.zfill(4)[-4:] if s else ""


def money(v):
    try:
        return float(str(v or "").strip().replace(",", ""))
    except ValueError:
        return 0.0


debit_rows, credit_rows = [], []
pair_counter = collections.Counter()

with open(PACTG, newline="", encoding="latin-1") as fh:
    rdr = csv.reader(fh)
    head = [c.replace("\ufeff", "").strip().upper() for c in next(rdr)]
    ix = {n: head.index(n) for n in
          ["CREDIT_CODE", "DEBIT_CODE", "POLICY_NUMBER", "TRANS_AMOUNT",
           "EFFECTIVE_DATE", "DATE_REVERSED"]}
    for r in rdr:
        if len(r) < len(head):
            continue
        pol = r[ix["POLICY_NUMBER"]].strip()
        if not pol or pol.startswith("---"):
            continue
        if (r[ix["DATE_REVERSED"]].strip().lstrip("0") or "") not in ("",):
            continue
        cr, db = code(r[ix["CREDIT_CODE"]]), code(r[ix["DEBIT_CODE"]])
        rec = (pol, r[ix["EFFECTIVE_DATE"]].strip(), round(abs(money(r[ix["TRANS_AMOUNT"]])), 2))
        if db in ELECT:
            debit_rows.append((db, rec))
            pair_counter[f"debit {db} / credit {cr}"] += 1
        elif cr in ELECT:
            credit_rows.append((cr, rec))
            pair_counter[f"credit {cr} / debit {db}"] += 1

print(f"election code on DEBIT side : {len(debit_rows):>6,} rows")
print(f"election code on CREDIT side: {len(credit_rows):>6,} rows")
print(f"total currently emitted     : {len(debit_rows) + len(credit_rows):>6,} rows")

debit_keys = collections.Counter(rec for _, rec in debit_rows)
mirrored = sum(1 for _, rec in credit_rows if debit_keys.get(rec, 0))
print(f"\ncredit-side rows that mirror a debit-side row (same policy/date/amount): "
      f"{mirrored} of {len(credit_rows)}")

print("\nCode pairings (top 25):")
for k, n in pair_counter.most_common(25):
    print(f"  {k:<28} {n:>6,}")

print("\nCredit-side rows by election code:")
for c, n in sorted(collections.Counter(c for c, _ in credit_rows).items()):
    print(f"  {c}: {n:>5,}")
print("\nDebit-side rows by election code:")
for c, n in sorted(collections.Counter(c for c, _ in debit_rows).items()):
    print(f"  {c}: {n:>5,}")

print("\nSample credit-side rows:")
for c, rec in credit_rows[:12]:
    tag = "MIRRORS a debit row" if debit_keys.get(rec) else "no debit twin"
    print(f"  code={c} policy={rec[0]} eff={rec[1]} amt={rec[2]:>10,.2f}   {tag}")
