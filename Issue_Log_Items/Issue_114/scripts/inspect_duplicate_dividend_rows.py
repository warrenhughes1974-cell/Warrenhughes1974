"""Issue #114 — confirm the 2 repeated dividend rows are real PACTG postings (READ-ONLY)."""
import collections
import csv
import os

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
BENH = os.path.join(REPO, "QLA_Migration", "Output", "quikbenh.csv")
PACTG = os.path.join(REPO, "QLA_Migration", "Source", "PACTG_Accounting_Extract20260630.csv")
DIV = {"1", "2", "3", "4", "5"}
ELECT = {"0514", "0515", "0516", "0517", "0518"}
csv.field_size_limit(10 ** 7)

rows = [r for r in csv.DictReader(open(BENH, encoding="utf-8-sig"))
        if r["MBENTYP"].strip() in DIV]
counts = collections.Counter(
    (r["MPOLICY"].strip(), r["MBENTYP"].strip(), r["MDATE"].strip(), r["MBEN"].strip())
    for r in rows
)
dupes = {k: n for k, n in counts.items() if n > 1}
print(f"dividend rows: {len(rows)}   repeated combinations: {len(dupes)}")
for k, n in dupes.items():
    print(f"  {k} x{n}")

targets = {k[0] for k in dupes}
print("\nAll quikbenh dividend rows for the affected policies:")
for r in rows:
    if r["MPOLICY"].strip() in targets:
        print(f"  {r['MPOLICY'].strip():>12} type={r['MBENTYP']:>2} {r['MDATE']} {r['MBEN']:>10}")


def code(v):
    s = "".join(c for c in str(v).strip() if c.isdigit())
    return s.zfill(4)[-4:] if s else ""


print("\nUnderlying PACTG dividend-election transactions:")
src = {t.rstrip("C").strip() for t in targets}
with open(PACTG, newline="", encoding="latin-1") as fh:
    rdr = csv.reader(fh)
    head = [c.replace("\ufeff", "").strip().upper() for c in next(rdr)]
    ix = {n: head.index(n) for n in
          ["CREDIT_CODE", "DEBIT_CODE", "POLICY_NUMBER", "TRANS_AMOUNT",
           "EFFECTIVE_DATE", "DATE_REVERSED", "CONTROL_NUMBER"]}
    for r in rdr:
        if len(r) < len(head):
            continue
        pol = r[ix["POLICY_NUMBER"]].strip()
        if pol not in src:
            continue
        cr, db = code(r[ix["CREDIT_CODE"]]), code(r[ix["DEBIT_CODE"]])
        if cr not in ELECT and db not in ELECT:
            continue
        print(f"  {pol} cr={cr} db={db} eff={r[ix['EFFECTIVE_DATE']].strip()} "
              f"amt={r[ix['TRANS_AMOUNT']].strip():>10} "
              f"control={r[ix['CONTROL_NUMBER']].strip()} "
              f"reversed={r[ix['DATE_REVERSED']].strip()}")
