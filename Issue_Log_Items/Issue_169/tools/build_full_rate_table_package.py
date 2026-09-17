"""Issue #169 - package the complete rate table set for the client's CSO region.

Takes the rate DBFs built by the Desktop DBF Append Tool (never rebuilt here - see
.cursor/rules/dbf-append-only.mdc), verifies each one's record count against the Output
CSV it was appended from, and stages them for zipping.

The QuikPl* master templates each carry one all-zero blank-PLAN seed row, so a correct
DBF is template records + CSV rows. That offset is the standing Append Tool pattern.
"""

import csv
import shutil
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APPEND_OUT = Path(r"C:\Users\warren\Desktop\DBF_Append_Tool\output")
TEMPLATES = Path(r"C:\Users\warren\Desktop\DBF_Append_Tool\templates")
RATES = ROOT / "QLA_Migration/Output/rates"
STAGE = ROOT / "QLA_Migration/Output/Test_Validation/CSO_All_Rate_Tables"


def dbf_records(path: Path) -> int:
    with path.open("rb") as fh:
        return struct.unpack("<I", fh.read(8)[4:8])[0]


def csv_rows(path: Path) -> int:
    with path.open(encoding="utf-8-sig") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def plan_rows(path: Path, plan: str) -> int:
    with path.open(encoding="utf-8-sig") as fh:
        return sum(1 for r in csv.DictReader(fh) if (r.get("PLAN") or "").strip() == plan)


tables = sorted(
    p.stem for p in RATES.glob("*.csv") if p.stem != "rate_csv_manifest"
)

if STAGE.exists():
    shutil.rmtree(STAGE)
STAGE.mkdir(parents=True)

problems = []
print(f"{'TABLE':12s} {'DBF':>9s} {'CSV':>9s} {'SEED':>5s}  RESULT")
for t in tables:
    dbf, src, tpl = APPEND_OUT / f"{t}.dbf", RATES / f"{t}.csv", TEMPLATES / f"{t}.dbf"
    if not dbf.is_file():
        problems.append(f"{t}: no DBF in Append Tool output - run the Append Tool")
        print(f"{t:12s} {'-':>9s} {'-':>9s} {'-':>5s}  MISSING")
        continue
    n_dbf, n_csv = dbf_records(dbf), csv_rows(src)
    seed = dbf_records(tpl) if tpl.is_file() else 0
    ok = n_dbf == n_csv + seed
    if not ok:
        problems.append(f"{t}: DBF {n_dbf} != CSV {n_csv} + seed {seed}")
    print(f"{t:12s} {n_dbf:9,d} {n_csv:9,d} {seed:5d}  {'OK' if ok else 'MISMATCH'}")
    shutil.copy2(dbf, STAGE / dbf.name)

print()
print("667 ART (5667AT) content, the Issue 169 fix:")
for t in ("QuikNps", "QuikPlTv"):
    print(f"  {t}: {plan_rows(RATES / f'{t}.csv', '5667AT')} rows")

print()
print(f"staged {len(list(STAGE.glob('*.dbf')))} rate DBFs -> {STAGE.relative_to(ROOT)}")
if problems:
    print()
    print("PROBLEMS:")
    for p in problems:
        print("  -", p)
    raise SystemExit(1)
print("ALL TABLES VERIFIED")
