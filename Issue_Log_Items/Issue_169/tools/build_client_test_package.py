"""Issue #169 - assemble the client UAT test package for the 667 ART reserve fix.

Copies the eight rate DBFs built by the Desktop DBF Append Tool (never rebuilt here -
see .cursor/rules/dbf-append-only.mdc) plus the test note and anchor list, verifies each
DBF's record count against the Output CSV it came from, and zips the result.
"""

import csv
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APPEND_OUT = Path(r"C:\Users\warren\Desktop\DBF_Append_Tool\output")
TEMPLATES = Path(r"C:\Users\warren\Desktop\DBF_Append_Tool\templates")
RATES = ROOT / "QLA_Migration/Output/rates"
STAGE = ROOT / "QLA_Migration/Output/Test_Validation/Issue169_667ART_rates"
ISSUE = ROOT / "Issue_Log_Items/Issue_169"

TABLES = [
    "QuikNps",
    "QuikPlTv",
    "QuikTvs",
    "QuikCvs",
    "QuikNff",
    "QuikPlCv",
    "QuikPlDb",
    "QuikPlDv",
]
DOCS = [
    ISSUE / "Issue_169_UAT_Test_Instructions.md",
    ISSUE / "Issue_169_UAT_Test_Anchors.csv",
]


def dbf_record_count(path: Path) -> int:
    with path.open("rb") as fh:
        return struct.unpack("<I", fh.read(8)[4:8])[0]


def csv_row_count(path: Path) -> int:
    with path.open(encoding="utf-8-sig") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def plan_rows(path: Path, plan: str) -> int:
    with path.open(encoding="utf-8-sig") as fh:
        return sum(1 for r in csv.DictReader(fh) if (r.get("PLAN") or "").strip() == plan)


if STAGE.exists():
    shutil.rmtree(STAGE)
STAGE.mkdir(parents=True)

problems = []
# The QuikPl* master templates each ship one all-zero, blank-PLAN key row, and APPEND adds
# our rows after it, so a correct DBF is template records + CSV rows. Same offset as the
# 8/31 L14 delivery (QuikPlTv 389 CSV -> 390 DBF), so it is the standing pattern, not drift.
print("{:10s} {:>9s} {:>9s} {:>5s}  {}".format("TABLE", "DBF", "CSV", "SEED", "MATCH"))
for t in TABLES:
    dbf, src, tpl = APPEND_OUT / f"{t}.dbf", RATES / f"{t}.csv", TEMPLATES / f"{t}.dbf"
    if not dbf.is_file():
        problems.append(f"{t}: missing {dbf} - run the Append Tool, do not hand-build")
        continue
    n_dbf, n_csv = dbf_record_count(dbf), csv_row_count(src)
    seed = dbf_record_count(tpl) if tpl.is_file() else 0
    ok = n_dbf == n_csv + seed
    if not ok:
        problems.append(
            f"{t}: DBF {n_dbf} rows != Output CSV {n_csv} + template seed {seed}"
        )
    print(
        "{:10s} {:9,d} {:9,d} {:5d}  {}".format(
            t, n_dbf, n_csv, seed, "OK" if ok else "MISMATCH"
        )
    )
    shutil.copy2(dbf, STAGE / dbf.name)

for d in DOCS:
    if not d.is_file():
        problems.append(f"missing doc {d.name}")
        continue
    shutil.copy2(d, STAGE / d.name)

print()
print("5667AT content check (the fix):")
for t in ("QuikNps", "QuikPlTv"):
    n = plan_rows(RATES / f"{t}.csv", "5667AT")
    print(f"  {t}: {n} rows for 5667AT")
    if n == 0:
        problems.append(f"{t}: no 5667AT rows - fix is not in this package")

zip_path = STAGE.with_suffix(".zip")
if zip_path.exists():
    zip_path.unlink()
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for f in sorted(STAGE.iterdir()):
        zf.write(f, f.name)

print()
if problems:
    print("PROBLEMS:")
    for p in problems:
        print("  -", p)
    raise SystemExit(1)

print("PACKAGE OK")
print(f"  folder: {STAGE.relative_to(ROOT)}")
print(f"  zip:    {zip_path.relative_to(ROOT)}  ({zip_path.stat().st_size / 1024 / 1024:.1f} MB)")
print(f"  files:  {len(TABLES)} rate DBFs + {len(DOCS)} docs")
