"""DG-R-001 apply: backup, delete QuikList test groups, remap QuikChrt G/V -> C."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import dbf
from dbfread import DBF

DATA = Path(r"Q:\CSO\CSO_Test_6_30_2025")
BACKUP = Path(r"Q:\CSO\CSO_Test_6_30_2025_backup_DG-R-001_20260718")
DELETE_GROUPS = {"GTEST01", "TERMG", "TEST1"}
BACKUP_STEMS = ["QuikList", "QuikChrt", "QuikAgts", "QuikActg", "QuikComp"]
ITEM_DIR = Path(__file__).resolve().parent
ARTIFACT = ITEM_DIR / "_apply_counts.json"


def find_files(stem: str, folder: Path) -> list[Path]:
    """Case-insensitive match for stem.* (dbf/dbt/ntx/etc)."""
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


def norm(v) -> str:
    if v is None:
        return ""
    return str(v).strip()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def preflight_or_stop() -> dict:
    counts: dict = {"timestamp_utc": datetime.now(timezone.utc).isoformat()}

    comp_path = find_dbf("QuikComp", DATA)
    comp = DBF(str(comp_path), load=True, ignore_missing_memofile=True)
    comp_cnt = Counter(norm(r.get("MCOMP")) for r in comp if norm(r.get("MCOMP")))
    counts["quikcomp_distinct"] = dict(comp_cnt)
    if comp_cnt.get("C", 0) != 1:
        print("BLOCKED: C missing or not unique in QuikComp:", dict(comp_cnt))
        sys.exit(2)
    if comp_cnt.get("G", 0) or comp_cnt.get("V", 0):
        print("NOTE: G/V unexpectedly present in QuikComp:", dict(comp_cnt))

    lst_path = find_dbf("QuikList", DATA)
    lst = DBF(str(lst_path), load=True, ignore_missing_memofile=True)
    delete_rows = []
    for i, r in enumerate(lst):
        g = norm(r.get("MGROUP"))
        c = norm(r.get("MCOMP"))
        if g in DELETE_GROUPS:
            delete_rows.append({"idx": i, "MGROUP": g, "MCOMP": c})
    counts["quiklist_total"] = len(lst)
    counts["quiklist_delete"] = delete_rows
    counts["quiklist_delete_count"] = len(delete_rows)
    if len(delete_rows) != 3:
        print("STOP: QuikList delete count != 3:", len(delete_rows), delete_rows)
        sys.exit(3)

    for stem in ["QuikList", "QuikChrt", "QuikAgts", "QuikActg"]:
        path = find_dbf(stem, DATA)
        t = DBF(str(path), load=True, ignore_missing_memofile=True)
        gv = Counter()
        for r in t:
            c = norm(r.get("MCOMP"))
            if c in ("G", "V"):
                gv[c] += 1
        counts[f"{stem.lower()}_gv"] = dict(gv)
        counts[f"{stem.lower()}_gv_total"] = sum(gv.values())
        counts[f"{stem.lower()}_total"] = len(t)

    mst = DBF(str(find_dbf("QuikMstr", DATA)), load=True, ignore_missing_memofile=True)
    cg = cv = 0
    for r in mst:
        p = norm(r.get("MPOLICY"))
        if not p:
            continue
        if p[-1] == "G":
            cg += 1
        elif p[-1] == "V":
            cv += 1
    counts["quikmstr_lastchar_G"] = cg
    counts["quikmstr_lastchar_V"] = cv
    counts["flag_only_policy_suffix"] = {"G": cg, "V": cv}

    # regression baselines for untouched tables
    untouched = {}
    for stem in ["QuikPlan", "QuikDate", "QuikComp", "QuikAgts", "QuikActg"]:
        try:
            p = find_dbf(stem, DATA)
        except FileNotFoundError:
            continue
        untouched[stem] = {
            "path": str(p),
            "size": p.stat().st_size,
            "mtime": p.stat().st_mtime,
            "sha256": file_sha256(p),
        }
    counts["untouched_baseline"] = untouched

    # QuikList keep-set (should be empty after)
    keep = []
    for r in lst:
        g = norm(r.get("MGROUP"))
        if g not in DELETE_GROUPS:
            keep.append(g)
    counts["quiklist_keep_groups"] = keep

    print("PREFLIGHT OK")
    for k in sorted(counts):
        if k == "untouched_baseline":
            continue
        print(f"  {k}: {counts[k]}")
    return counts


def create_backup() -> list[str]:
    if BACKUP.exists():
        existing = list(BACKUP.iterdir())
        if existing:
            print(f"Backup folder already exists with {len(existing)} files: {BACKUP}")
            # verify required stems present
            missing = []
            for stem in BACKUP_STEMS:
                if not find_files(stem, BACKUP):
                    missing.append(stem)
            if missing:
                print("BLOCKED: backup exists but missing stems:", missing)
                sys.exit(4)
            print("Using existing backup (already populated).")
            return [p.name for p in BACKUP.iterdir() if p.is_file()]

    BACKUP.mkdir(parents=True, exist_ok=True)
    copied = []
    for stem in BACKUP_STEMS:
        files = find_files(stem, DATA)
        if not files:
            print(f"WARNING: no files found for stem {stem}")
            continue
        for src in files:
            dst = BACKUP / src.name
            shutil.copy2(src, dst)
            copied.append(src.name)
            print(f"  backed up {src.name} -> {dst}")
    if not copied:
        print("BLOCKED: backup produced no files")
        sys.exit(4)
    # require at least the DBFs
    for stem in BACKUP_STEMS:
        if not any(p.suffix.lower() == ".dbf" for p in find_files(stem, BACKUP)):
            print(f"BLOCKED: backup missing DBF for {stem}")
            sys.exit(4)
    print(f"BACKUP OK: {BACKUP} ({len(copied)} files)")
    return copied


def apply_quiklist_deletes() -> dict:
    path = find_dbf("QuikList", DATA)
    table = dbf.Table(str(path))
    table.open(mode=dbf.READ_WRITE)
    deleted = []
    try:
        for record in table:
            g = norm(getattr(record, "MGROUP", ""))
            if g in DELETE_GROUPS:
                c = norm(getattr(record, "MCOMP", ""))
                deleted.append({"MGROUP": g, "MCOMP": c})
                dbf.delete(record)
        before_active = len(table)
        table.pack()
        after = len(table)
    finally:
        table.close()
    result = {
        "path": str(path),
        "deleted": deleted,
        "deleted_count": len(deleted),
        "rows_after": after,
        "rows_before_pack_note": before_active,
    }
    if len(deleted) != 3:
        print("STOP after delete: unexpected deleted_count", result)
        sys.exit(5)
    print(f"QuikList: deleted {len(deleted)} rows; rows_after={after}")
    return result


def apply_mcomp_remap(stem: str) -> dict:
    path = find_dbf(stem, DATA)
    table = dbf.Table(str(path))
    table.open(mode=dbf.READ_WRITE)
    updated = Counter()
    try:
        for record in table:
            c = norm(getattr(record, "MCOMP", ""))
            if c in ("G", "V"):
                # preserve field width via assignment
                dbf.write(record, MCOMP="C")
                updated[c] += 1
    finally:
        table.close()
    result = {
        "path": str(path),
        "updated_from": dict(updated),
        "updated_total": sum(updated.values()),
    }
    print(f"{stem}: remapped {result['updated_total']} rows {dict(updated)}")
    return result


def post_verify(pre: dict) -> dict:
    out: dict = {}
    # QuikList empty of delete groups and G/V
    lst = DBF(str(find_dbf("QuikList", DATA)), load=True, ignore_missing_memofile=True)
    remaining_del = [
        norm(r.get("MGROUP")) for r in lst if norm(r.get("MGROUP")) in DELETE_GROUPS
    ]
    remaining_gv = [norm(r.get("MCOMP")) for r in lst if norm(r.get("MCOMP")) in ("G", "V")]
    out["quiklist_rows"] = len(lst)
    out["quiklist_remaining_delete_groups"] = remaining_del
    out["quiklist_remaining_gv"] = remaining_gv

    for stem in ["QuikChrt", "QuikAgts", "QuikActg"]:
        t = DBF(str(find_dbf(stem, DATA)), load=True, ignore_missing_memofile=True)
        gv = sum(1 for r in t if norm(r.get("MCOMP")) in ("G", "V"))
        out[f"{stem.lower()}_remaining_gv"] = gv
        out[f"{stem.lower()}_total"] = len(t)

    comp = DBF(str(find_dbf("QuikComp", DATA)), load=True, ignore_missing_memofile=True)
    out["quikcomp"] = dict(
        Counter(norm(r.get("MCOMP")) for r in comp if norm(r.get("MCOMP")))
    )

    # untouched hashes
    untouched_after = {}
    for stem, meta in pre["untouched_baseline"].items():
        p = Path(meta["path"])
        untouched_after[stem] = {
            "size": p.stat().st_size,
            "mtime": p.stat().st_mtime,
            "sha256": file_sha256(p),
            "unchanged": file_sha256(p) == meta["sha256"],
        }
    out["untouched_after"] = untouched_after
    print("POST-VERIFY:")
    for k, v in out.items():
        if k != "untouched_after":
            print(f"  {k}: {v}")
    for stem, meta in untouched_after.items():
        print(f"  untouched {stem}: unchanged={meta['unchanged']}")
    return out


def main() -> None:
    print("=== DG-R-001 APPLY ===")
    pre = preflight_or_stop()
    copied = create_backup()
    pre["backup_files"] = copied
    pre["backup_path"] = str(BACKUP)

    # Refuse to mutate if backup missing required DBFs
    for stem in BACKUP_STEMS:
        if not any(p.suffix.lower() == ".dbf" for p in find_files(stem, BACKUP)):
            print("BLOCKED: backup missing", stem)
            sys.exit(4)

    list_result = apply_quiklist_deletes()
    chrt_result = apply_mcomp_remap("QuikChrt")
    agts_result = apply_mcomp_remap("QuikAgts")
    actg_result = apply_mcomp_remap("QuikActg")

    post = post_verify(pre)
    payload = {
        "preflight": pre,
        "quiklist": list_result,
        "quikchrt": chrt_result,
        "quikagts": agts_result,
        "quikactg": actg_result,
        "post": post,
    }
    ARTIFACT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {ARTIFACT}")

    # hard fail if residual G/V on in-scope tables
    if post["quiklist_remaining_delete_groups"] or post["quiklist_remaining_gv"]:
        print("FAIL: QuikList residuals remain")
        sys.exit(6)
    if post["quikchrt_remaining_gv"] or post["quikagts_remaining_gv"] or post["quikactg_remaining_gv"]:
        print("FAIL: G/V remain on Chrt/Agts/Actg")
        sys.exit(6)
    if post["quikcomp"].get("C") != 1 or "G" in post["quikcomp"] or "V" in post["quikcomp"]:
        print("FAIL: QuikComp integrity")
        sys.exit(6)
    print("APPLY COMPLETE")


if __name__ == "__main__":
    main()
