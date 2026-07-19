"""DG-R-008 apply: backup + delete blank-PLAN shells on CSO QuikPlan / QuikPl*."""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import dbf
from dbfread import DBF

DATA = Path(r"Q:\CSO\CSO_Test_6_30_2026")
BACKUP = Path(r"Q:\CSO\CSO_Test_6_30_2026_backup_DG-R-008_20260718")
ITEM_DIR = Path(__file__).resolve().parent
ARTIFACT = ITEM_DIR / "_apply_counts.json"

TABLES = [
    "QuikPlan",
    "QuikPlGp",
    "QuikPlDb",
    "QuikPlCv",
    "QuikPlTv",
    "QuikPlDv",
    "QuikPlGd",
    "QuikPlUw",
    "QuikPlBd",
]


def find_files(stem: str, folder: Path) -> list[Path]:
    return sorted(
        (
            p
            for p in folder.iterdir()
            if p.is_file() and p.stem.lower() == stem.lower()
        ),
        key=lambda x: x.name.lower(),
    )


def find_dbf(stem: str, folder: Path) -> Path:
    matches = [
        p
        for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() == ".dbf" and p.stem.lower() == stem.lower()
    ]
    if not matches:
        raise FileNotFoundError(f"No DBF for {stem} in {folder}")
    return matches[0]


def count_blank(stem: str, folder: Path) -> tuple[int, int]:
    path = find_dbf(stem, folder)
    rows = list(DBF(str(path), encoding="latin-1", ignore_missing_memofile=True))
    blank = sum(1 for r in rows if not str(r.get("PLAN", "") or "").strip())
    return len(rows), blank


def backup() -> None:
    if BACKUP.exists():
        print(f"Backup already exists: {BACKUP}")
        return
    BACKUP.mkdir(parents=True)
    copied = []
    for stem in TABLES:
        for src in find_files(stem, DATA):
            dst = BACKUP / src.name
            shutil.copy2(src, dst)
            copied.append(src.name)
    print(f"Backup -> {BACKUP} ({len(copied)} files)")
    (BACKUP / "_manifest.txt").write_text("\n".join(copied) + "\n", encoding="utf-8")


def delete_blank_plan_rows(stem: str) -> dict:
    path = find_dbf(stem, DATA)
    before_n, before_blank = count_blank(stem, DATA)
    if before_blank == 0:
        return {
            "table": stem,
            "before": before_n,
            "blank_before": 0,
            "deleted": 0,
            "after": before_n,
            "blank_after": 0,
            "skipped": True,
        }
    if before_blank != 1:
        raise RuntimeError(
            f"{stem}: expected exactly 1 blank PLAN row, found {before_blank}"
        )

    table = dbf.Table(str(path))
    table.open(mode=dbf.READ_WRITE)
    deleted = 0
    try:
        for record in table:
            plan = str(getattr(record, "PLAN", "") or "").strip()
            if not plan:
                dbf.delete(record)
                deleted += 1
        table.pack()
    finally:
        table.close()

    after_n, after_blank = count_blank(stem, DATA)
    if after_blank != 0:
        raise RuntimeError(f"{stem}: blank PLAN still present after delete")
    if after_n != before_n - deleted:
        raise RuntimeError(
            f"{stem}: row count mismatch before={before_n} deleted={deleted} after={after_n}"
        )
    return {
        "table": stem,
        "before": before_n,
        "blank_before": before_blank,
        "deleted": deleted,
        "after": after_n,
        "blank_after": after_blank,
        "skipped": False,
    }


def main() -> int:
    if not DATA.is_dir():
        print(f"BLOCKED: path not found: {DATA}")
        return 2

    print("Preflight blank counts:")
    pre = {}
    for stem in TABLES:
        n, b = count_blank(stem, DATA)
        pre[stem] = {"rows": n, "blank": b}
        print(f"  {stem}: rows={n} blank={b}")
        if b != 1:
            print(f"BLOCKED: {stem} blank count {b} != 1")
            return 2

    backup()
    results = []
    for stem in TABLES:
        info = delete_blank_plan_rows(stem)
        results.append(info)
        print(
            f"Deleted {stem}: {info['deleted']} blank "
            f"({info['before']} -> {info['after']})"
        )

    payload = {
        "applied_at_utc": datetime.now(timezone.utc).isoformat(),
        "data": str(DATA),
        "backup": str(BACKUP),
        "preflight": pre,
        "results": results,
    }
    ARTIFACT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {ARTIFACT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
