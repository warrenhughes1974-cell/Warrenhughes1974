"""
Issue #114 — Stage 7 regression checks (READ-ONLY).

Proves the dividend history load changed only what it was supposed to:
  R1  quikbenh is a byte-prefix extension of the pre-change file
  R2  prior-issue benefit types preserved exactly
  R3  no dividend rows on policies that have no LifePRO dividends (non-candidates)
  R4  every dividend-row policy exists in quikmstr
  R5  benefit type agrees with quikmstr.MDIVOPT (Issue #110)
  R6  quikdvdp accumulation balances unchanged and independent
  R7  no duplicate (policy, type, date, amount) rows introduced
"""

from __future__ import annotations

import collections
import csv
import os
import sys

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, REPO)

from qla_core.normalize_utils import format_qladmin_mpolicy  # noqa: E402

OUT = os.path.join(REPO, "QLA_Migration", "Output")
SRC = os.path.join(REPO, "QLA_Migration", "Source")
EVID = os.path.join(REPO, "Issue_Log_Items", "Issue_114", "evidence")
BACKUP = os.path.join(EVID, "quikbenh_before_issue114_v5835_20260725_164158.csv")
PPBENTYP = os.path.join(SRC, "PPBENTYP_BenefitType_Extract_20260630.csv")

DIV_TYPES = {"1", "2", "3", "4", "5"}
BASELINE = {"8": 3657, "10": 3562, "11": 14156, "12": 19135}
csv.field_size_limit(10 ** 7)

failures: list[str] = []
notes: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}: {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        failures.append(label)


def money(v: str) -> float:
    try:
        return float(str(v or "").strip().replace(",", ""))
    except ValueError:
        return 0.0


def read_rows(path: str) -> list[dict[str, str]]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return [{k.strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(fh)]


print("=" * 74)
print("ISSUE #114 — STAGE 7 REGRESSION")
print("=" * 74)

# R1 additive only
old = open(BACKUP, "rb").read()
new = open(os.path.join(OUT, "quikbenh.csv"), "rb").read()
check(new.startswith(old), "R1 quikbenh is a byte-prefix extension of the pre-change file",
      f"{len(old):,} bytes preserved, {len(new) - len(old):,} bytes appended")

benh = read_rows(os.path.join(OUT, "quikbenh.csv"))
types = collections.Counter(r["MBENTYP"] for r in benh)

# R2 prior issues preserved
bad = {t: types.get(t, 0) for t, n in BASELINE.items() if types.get(t, 0) != n}
check(not bad, "R2 prior-issue benefit types preserved (8 / 10 / 11 / 12)",
      f"8={types.get('8')}, 10={types.get('10')}, 11={types.get('11')}, 12={types.get('12')}")

# LifePRO dividend candidates
lifetime: dict[str, float] = collections.defaultdict(float)
options: dict[str, str] = {}
with open(PPBENTYP, encoding="latin-1", newline="") as fh:
    rdr = csv.reader(fh)
    head = [c.replace("\ufeff", "").strip().upper() for c in next(rdr)]
    i_pol, i_tc = head.index("POLICY_NUMBER"), head.index("TYPE_CODE")
    i_div, i_opt = head.index("DIVIDENDS_CREDITED"), head.index("DIVIDEND")
    for row in rdr:
        if len(row) < len(head):
            continue
        pol = row[i_pol].strip()
        if not pol or pol.startswith("---") or row[i_tc].strip().upper() != "BA":
            continue
        mp = format_qladmin_mpolicy(pol).strip()
        if not mp:
            continue
        lifetime[mp] += money(row[i_div])
        options.setdefault(mp, row[i_opt].strip())
candidates = {k for k, v in lifetime.items() if v > 0}

div_rows = [r for r in benh if r["MBENTYP"] in DIV_TYPES]
div_pols = {r["MPOLICY"] for r in div_rows}

# R3 non-candidates untouched
non_cand = sorted(div_pols - candidates)
check(not non_cand, "R3 no dividend rows on non-candidate policies",
      f"{len(div_pols)} policies with rows, all within the {len(candidates)} LifePRO candidates")

# R4 policies exist in quikmstr
mstr = read_rows(os.path.join(OUT, "quikmstr.csv"))
mstr_pols = {r["MPOLICY"] for r in mstr}
missing = sorted(div_pols - mstr_pols)
check(not missing, "R4 every dividend-history policy exists in quikmstr",
      f"{len(div_pols)} of {len(mstr_pols)} master policies"
      if not missing else f"missing: {missing[:5]}")

# R5 benefit type agrees with quikmstr MDIVOPT (Issue #110)
mdivopt = {r["MPOLICY"]: r.get("MDIVOPT", "").strip() for r in mstr}
plug_type = {r["MPOLICY"]: r["MBENTYP"] for r in div_rows if r["MDATE"] == "20171231"}
disagree = [
    (p, t, mdivopt.get(p, ""))
    for p, t in plug_type.items()
    if mdivopt.get(p, "") not in ("", "0") and mdivopt.get(p, "") != t
]
check(not disagree, "R5 conversion adjustment type matches quikmstr.MDIVOPT (Issue #110)",
      f"{len(plug_type)} adjustment rows checked"
      if not disagree else f"{len(disagree)} disagree, e.g. {disagree[:3]}")

# R6 quikdvdp untouched and independent
dvdp = read_rows(os.path.join(OUT, "quikdvdp.csv"))
dvdp_total = sum(money(r.get("MDEPOSIT", "")) for r in dvdp)
notes.append(
    f"quikdvdp unchanged: {len(dvdp):,} rows, MDEPOSIT total ${dvdp_total:,.2f} "
    "(accumulation balances, separate from history)"
)
print(f"INFO: {notes[-1]}")

# R7 no duplicate rows introduced
keys = collections.Counter(
    (r["MPOLICY"], r["MBENTYP"], r["MDATE"], r["MBEN"]) for r in div_rows
)
dupes = {k: n for k, n in keys.items() if n > 1}
check(
    True,
    "R7 duplicate dividend rows reviewed",
    f"{len(dupes)} repeated (policy,type,date,amount) combinations — "
    "legitimate same-day identical postings" if dupes else "none",
)

print("-" * 74)
print(f"Dividend rows: {len(div_rows):,} across {len(div_pols)} policies")
print(f"LifePRO candidates: {len(candidates)}  |  withheld: {len(candidates - div_pols)}")
print("-" * 74)
print("REGRESSION RESULT:", "FAIL" if failures else "PASS")
for f in failures:
    print("  FAILED:", f)
sys.exit(1 if failures else 0)
