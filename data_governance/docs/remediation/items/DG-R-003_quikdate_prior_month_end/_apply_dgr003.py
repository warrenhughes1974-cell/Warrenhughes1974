"""DG-R-003 apply: backup QUIKDATE.*, set PACBILL/DIRBILL/REINBILL to 2026-06-30."""
from __future__ import annotations

import json
import shutil
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import dbf
from dbfread import DBF

DATA = Path(r"Q:\CSO\CSO_Test_6_30_2026")
BACKUP = Path(r"Q:\CSO\CSO_Test_6_30_2026_backup_DG-R-003_20260718")
TARGET = date(2026, 6, 30)
ITEM_DIR = Path(__file__).resolve().parent
ARTIFACT = ITEM_DIR / "_apply_counts.json"


def find_files(stem: str, folder: Path) -> list[Path]:
    out = []
    for p in folder.iterdir():
        if p.is_file() and p.stem.lower() == stem.lower():
            out.append(p)
    return sorted(out, key=lambda x: x.name.lower())


def find_dbf(stem: str, folder: Path) -> Path:
    matches = [
        p
        for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() == ".dbf" and p.stem.lower() == stem.lower()
    ]
    if not matches:
        raise FileNotFoundError(f"No DBF for {stem} in {folder}")
    return matches[0]


def _date_val(v):
    if v is None:
        return None
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if isinstance(v, datetime):
        return v.date()
    return v


def preflight_or_stop() -> dict:
    if not DATA.is_dir():
        print(f"BLOCKED: path not found: {DATA}")
        sys.exit(2)

    path = find_dbf("QuikDate", DATA)
    table = DBF(str(path), load=True, ignore_missing_memofile=True)
    counts: dict = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "data_path": str(DATA),
        "quikdate_path": str(path),
        "quikdate_row_count": len(table),
        "field_names": list(table.field_names),
    }
    records = list(table)
    if len(records) != 1:
        print(f"STOP: Unexpected QuikDate row count ≠ 1: {len(records)}")
        sys.exit(3)

    counts["quikdate_row_count"] = len(records)
    row = records[0]
    before = {
        "PACBILL": str(_date_val(row.get("PACBILL"))),
        "DIRBILL": str(_date_val(row.get("DIRBILL"))),
        "REINBILL": str(_date_val(row.get("REINBILL"))),
        "ACHFILEID": row.get("ACHFILEID"),
        "ACHFILEID2": (str(row.get("ACHFILEID2")).strip() if row.get("ACHFILEID2") is not None else ""),
        "ESC_DATE": str(_date_val(row.get("ESC_DATE"))),
        "PROCDATE": str(_date_val(row.get("PROCDATE"))),
        "GRPBILL": str(_date_val(row.get("GRPBILL"))),
        "APLBILL": str(_date_val(row.get("APLBILL"))),
        "LOANBILL": str(_date_val(row.get("LOANBILL"))),
        "CCBILL": str(_date_val(row.get("CCBILL"))),
        "VERSION": row.get("VERSION"),
        "UPDATENUM": row.get("UPDATENUM"),
    }
    counts["before"] = before
    print("PREFLIGHT OK")
    print(f"  rows={counts['quikdate_row_count']}")
    print(f"  before={before}")
    return counts


def create_backup() -> list[str]:
    if BACKUP.exists():
        existing = [p for p in BACKUP.iterdir() if p.is_file()]
        if existing:
            if not find_files("QuikDate", BACKUP):
                print(f"BLOCKED: backup exists but missing QUIKDATE.*: {BACKUP}")
                sys.exit(4)
            print(f"Using existing backup (already populated): {BACKUP}")
            return [p.name for p in existing]

    BACKUP.mkdir(parents=True, exist_ok=True)
    files = find_files("QuikDate", DATA)
    if not files:
        print("BLOCKED: no QUIKDATE.* files to back up")
        sys.exit(4)
    copied = []
    for src in files:
        dst = BACKUP / src.name
        shutil.copy2(src, dst)
        copied.append(src.name)
        print(f"  backed up {src.name} -> {dst}")
    if not any(p.suffix.lower() == ".dbf" for p in find_files("QuikDate", BACKUP)):
        print("BLOCKED: backup missing QUIKDATE.dbf")
        sys.exit(4)
    print(f"BACKUP OK: {BACKUP} ({len(copied)} files)")
    return copied


def apply_bill_dates() -> dict:
    path = find_dbf("QuikDate", DATA)
    table = dbf.Table(str(path))
    table.open(mode=dbf.READ_WRITE)
    try:
        if len(table) != 1:
            print(f"STOP: Unexpected QuikDate row count ≠ 1 during write: {len(table)}")
            sys.exit(5)
        record = table[0]
        dbf.write(record, PACBILL=TARGET, DIRBILL=TARGET, REINBILL=TARGET)
    finally:
        table.close()
    return {"path": str(path), "updated_fields": ["PACBILL", "DIRBILL", "REINBILL"], "target": TARGET.isoformat()}


def post_verify(pre: dict) -> dict:
    path = find_dbf("QuikDate", DATA)
    table = DBF(str(path), load=True, ignore_missing_memofile=True)
    records = list(table)
    if len(records) != 1:
        print(f"STOP: post-verify row count ≠ 1: {len(records)}")
        sys.exit(6)
    row = records[0]
    after = {
        "PACBILL": _date_val(row.get("PACBILL")),
        "DIRBILL": _date_val(row.get("DIRBILL")),
        "REINBILL": _date_val(row.get("REINBILL")),
        "ACHFILEID": row.get("ACHFILEID"),
        "ACHFILEID2": (str(row.get("ACHFILEID2")).strip() if row.get("ACHFILEID2") is not None else ""),
        "ESC_DATE": _date_val(row.get("ESC_DATE")),
        "PROCDATE": _date_val(row.get("PROCDATE")),
        "GRPBILL": _date_val(row.get("GRPBILL")),
        "APLBILL": _date_val(row.get("APLBILL")),
        "LOANBILL": _date_val(row.get("LOANBILL")),
        "CCBILL": _date_val(row.get("CCBILL")),
        "VERSION": row.get("VERSION"),
        "UPDATENUM": row.get("UPDATENUM"),
    }
    out = {"quikdate_row_count": len(records), "after": {k: str(v) for k, v in after.items()}}

    for fld in ("PACBILL", "DIRBILL", "REINBILL"):
        if after[fld] != TARGET:
            print(f"STOP: {fld} expected {TARGET}, got {after[fld]}")
            sys.exit(7)

    before = pre["before"]
    for fld in ("ACHFILEID", "ACHFILEID2", "PROCDATE", "GRPBILL", "APLBILL", "LOANBILL", "CCBILL", "VERSION", "UPDATENUM"):
        # compare string forms
        if str(after[fld]) != str(before[fld]) and not (
            after[fld] is None and before[fld] in ("None", "", None)
        ):
            # normalize None displays
            b = before[fld]
            a = after[fld]
            if str(a) == str(b):
                continue
            if a is None and (b in ("None", "") or b is None):
                continue
            if fld == "PROCDATE" and str(a) == str(b):
                continue
            # VERSION may have trailing spaces from DBF
            if fld == "VERSION" and str(a).strip() == str(b).strip():
                continue
            if str(a) != str(b):
                # Allow date equality via iso
                if hasattr(a, "isoformat") and str(a) == str(b):
                    continue
                print(f"STOP: non-target field changed: {fld} before={b!r} after={a!r}")
                sys.exit(8)

    # ESC_DATE should remain blank/None
    if after["ESC_DATE"] is not None:
        print(f"STOP: ESC_DATE unexpectedly set: {after['ESC_DATE']}")
        sys.exit(9)

    print("POST-VERIFY OK")
    print(f"  after={out['after']}")
    return out


def main() -> None:
    pre = preflight_or_stop()
    backed_up = create_backup()
    if not BACKUP.is_dir() or not find_files("QuikDate", BACKUP):
        print("BLOCKED: backup missing after create_backup")
        sys.exit(4)
    apply_info = apply_bill_dates()
    post = post_verify(pre)
    payload = {
        "item": "DG-R-003",
        "preflight": pre,
        "backup_dir": str(BACKUP),
        "backed_up_files": backed_up,
        "apply": apply_info,
        "post_verify": post,
    }
    ARTIFACT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {ARTIFACT}")
    print("DG-R-003 APPLY COMPLETE")


if __name__ == "__main__":
    main()
