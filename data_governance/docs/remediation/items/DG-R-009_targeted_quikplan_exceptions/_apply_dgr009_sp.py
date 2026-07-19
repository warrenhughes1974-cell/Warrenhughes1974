"""DG-R-009: backup QuikPlan + set PAYYRS=1 / PAYAGE=0 on six SPWL plans."""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import dbf
from dbfread import DBF

DATA = Path(r"Q:\CSO\CSO_Test_6_30_2026")
BACKUP = Path(r"Q:\CSO\CSO_Test_6_30_2026_backup_DG-R-009_20260718")
ITEM_DIR = Path(__file__).resolve().parent
ARTIFACT = ITEM_DIR / "_apply_counts.json"

SP_PLANS = {
    "1668SP",
    "10L171",
    "10L172",
    "17MJPO",
    "1L17SP",
    "117JPO",
}


def find_files(stem: str, folder: Path) -> list[Path]:
    return sorted(
        p
        for p in folder.iterdir()
        if p.is_file() and p.stem.lower() == stem.lower()
    )


def find_dbf(stem: str, folder: Path) -> Path:
    matches = [
        p
        for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() == ".dbf" and p.stem.lower() == stem.lower()
    ]
    if not matches:
        raise FileNotFoundError(stem)
    return matches[0]


def main() -> int:
    if not DATA.is_dir():
        print("BLOCKED: data path missing")
        return 2

    path = find_dbf("QuikPlan", DATA)
    rows = list(DBF(str(path), encoding="latin-1", ignore_missing_memofile=True))
    present = {
        str(r.get("PLAN") or "").strip().upper()
        for r in rows
        if str(r.get("PLAN") or "").strip().upper() in SP_PLANS
    }
    missing = sorted(SP_PLANS - present)
    if missing:
        print("BLOCKED: missing plans", missing)
        return 2
    print("Preflight SP plans present:", sorted(present))

    if not BACKUP.exists():
        BACKUP.mkdir(parents=True)
        for src in find_files("QuikPlan", DATA):
            shutil.copy2(src, BACKUP / src.name)
        print("Backup ->", BACKUP)
    else:
        print("Backup exists:", BACKUP)

    table = dbf.Table(str(path))
    table.open(mode=dbf.READ_WRITE)
    updated = []
    try:
        for record in table:
            plan = str(getattr(record, "PLAN", "") or "").strip().upper()
            if plan not in SP_PLANS:
                continue
            before = (record.PAYYRS, record.PAYAGE)
            dbf.write(
                record,
                PAYYRS=1,
                PAYAGE=0,
                SEMI=0,
                QTRL=0,
                MTHD=0,
                MTHB=0,
            )
            after = (record.PAYYRS, record.PAYAGE)
            updated.append({"PLAN": plan, "before": before, "after": after})
    finally:
        table.close()

    # verify
    rows2 = list(DBF(str(path), encoding="latin-1", ignore_missing_memofile=True))
    bad = []
    for r in rows2:
        plan = str(r.get("PLAN") or "").strip().upper()
        if plan in SP_PLANS:
            if int(float(r.get("PAYYRS") or 0)) != 1 or int(float(r.get("PAYAGE") or 0)) != 0:
                bad.append((plan, r.get("PAYYRS"), r.get("PAYAGE")))
    if bad:
        print("VERIFY FAIL", bad)
        return 3

    payload = {
        "applied_at_utc": datetime.now(timezone.utc).isoformat(),
        "data": str(DATA),
        "backup": str(BACKUP),
        "updated": updated,
    }
    ARTIFACT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"Updated {len(updated)} plans")
    for u in updated:
        print(" ", u)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
