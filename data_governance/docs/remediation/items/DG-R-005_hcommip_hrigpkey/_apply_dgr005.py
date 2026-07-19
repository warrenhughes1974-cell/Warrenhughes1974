"""DG-R-005 apply: backup QuikPlan.*, set HCOMMIP/HRIGPKEY False for non-MEDS."""
from __future__ import annotations

import json
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import dbf
from dbfread import DBF

DATA = Path(r"Q:\CSO\CSO_Test_6_30_2026")
BACKUP = Path(r"Q:\CSO\CSO_Test_6_30_2026_backup_DG-R-005_20260718")
ITEM_DIR = Path(__file__).resolve().parent
ARTIFACT = ITEM_DIR / "_apply_counts.json"
EXPECTED_ROWS = 142


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


def _plan_type(row: dict) -> str:
    v = row.get("PLANTYPE")
    if v is None:
        return ""
    return str(v).strip().casefold()


def _logical_repr(v) -> str:
    if v is None:
        return "None"
    if isinstance(v, bool):
        return "True" if v else "False"
    return repr(v)


def preflight_or_stop() -> dict:
    if not DATA.is_dir():
        print(f"BLOCKED: path not found: {DATA}")
        sys.exit(2)

    path = find_dbf("QuikPlan", DATA)
    table = DBF(str(path), load=True, ignore_missing_memofile=True)
    records = list(table)
    n = len(records)

    from data_governance.rules.plan_setup_integrity.common import decode_logical

    plantype_counts: Counter[str] = Counter()
    meds = 0
    non_meds = 0
    hcomm_dec: Counter[str] = Counter()
    hrig_dec: Counter[str] = Counter()

    for row in records:
        pt = _plan_type(row)
        plantype_counts[pt if pt else "(blank)"] += 1
        if pt == "meds":
            meds += 1
        else:
            non_meds += 1
        hc, _, _ = decode_logical(row.get("HCOMMIP"))
        hr, _, _ = decode_logical(row.get("HRIGPKEY"))
        hcomm_dec[_logical_repr(hc)] += 1
        hrig_dec[_logical_repr(hr)] += 1

    hcomm_bytes, hrig_bytes = _scan_logical_raw_bytes(path)

    counts: dict = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "data_path": str(DATA),
        "quikplan_path": str(path),
        "row_count": n,
        "meds_count": meds,
        "non_meds_count": non_meds,
        "plantype_counts": dict(plantype_counts),
        "hcommip_decoded": dict(hcomm_dec),
        "hrigpkey_decoded": dict(hrig_dec),
        "hcommip_raw_bytes": dict(hcomm_bytes),
        "hrigpkey_raw_bytes": dict(hrig_bytes),
        "field_names_has_targets": {
            "HCOMMIP": "HCOMMIP" in table.field_names,
            "HRIGPKEY": "HRIGPKEY" in table.field_names,
            "PLANTYPE": "PLANTYPE" in table.field_names,
        },
    }

    print("PREFLIGHT")
    print(f"  rows={n} (expected ~{EXPECTED_ROWS})")
    print(f"  meds={meds} non_meds={non_meds}")
    print(f"  plantype={dict(plantype_counts)}")
    print(f"  HCOMMIP decoded={dict(hcomm_dec)}")
    print(f"  HRIGPKEY decoded={dict(hrig_dec)}")
    print(f"  HCOMMIP raw bytes={dict(hcomm_bytes)}")
    print(f"  HRIGPKEY raw bytes={dict(hrig_bytes)}")

    if n != EXPECTED_ROWS:
        print(f"STOP: Unexpected QuikPlan row count: {n} (expected {EXPECTED_ROWS})")
        sys.exit(3)
    if meds != 0:
        print(f"STOP: Unexpected MEDS count: {meds} (expected 0)")
        sys.exit(3)

    # Most should be ? or space
    raw_ok_chars = {"?", " ", "None"}
    hcomm_mostly = sum(v for k, v in hcomm_bytes.items() if k in raw_ok_chars or k in ("?", " "))
    hrig_mostly = sum(v for k, v in hrig_bytes.items() if k in raw_ok_chars or k in ("?", " "))
    if hcomm_mostly < n * 0.9 or hrig_mostly < n * 0.9:
        print(
            f"STOP: Unexpected logical raw distribution "
            f"(HCOMMIP={dict(hcomm_bytes)} HRIGPKEY={dict(hrig_bytes)})"
        )
        sys.exit(3)

    print("PREFLIGHT OK")
    return counts


def _scan_logical_raw_bytes(dbf_path: Path) -> tuple[Counter[str], Counter[str]]:
    """Scan Logical field storage bytes directly from DBF file."""
    with open(dbf_path, "rb") as f:
        header = f.read(32)
        num_records = int.from_bytes(header[4:8], "little")
        header_len = int.from_bytes(header[8:10], "little")
        record_len = int.from_bytes(header[10:12], "little")

        # Field descriptors: 32 bytes each until 0x0D
        fields = []
        f.seek(32)
        while True:
            desc = f.read(32)
            if not desc or desc[0] == 0x0D:
                break
            name = desc[0:11].split(b"\x00", 1)[0].decode("ascii", errors="replace")
            ftype = chr(desc[11])
            # For dBase III, offset is cumulative; size at bytes 16
            size = desc[16]
            fields.append((name, ftype, size))

        # Compute offsets (skip delete flag at 0)
        offset = 1
        offsets = {}
        for name, ftype, size in fields:
            offsets[name] = (offset, size, ftype)
            offset += size

        if "HCOMMIP" not in offsets or "HRIGPKEY" not in offsets:
            raise KeyError("HCOMMIP/HRIGPKEY missing from QuikPlan schema")

        hcomm_off, _, _ = offsets["HCOMMIP"]
        hrig_off, _, _ = offsets["HRIGPKEY"]

        hcomm: Counter[str] = Counter()
        hrig: Counter[str] = Counter()
        f.seek(header_len)
        for _ in range(num_records):
            rec = f.read(record_len)
            if len(rec) < record_len:
                break
            if rec[0:1] == b"*":  # deleted
                continue
            hb = rec[hcomm_off : hcomm_off + 1]
            rb = rec[hrig_off : hrig_off + 1]
            hcomm[hb.decode("latin-1")] += 1
            hrig[rb.decode("latin-1")] += 1

    return hcomm, hrig


def create_backup() -> list[str]:
    if BACKUP.exists():
        existing = [p for p in BACKUP.iterdir() if p.is_file()]
        if existing:
            if not find_files("QuikPlan", BACKUP):
                print(f"BLOCKED: backup exists but missing QuikPlan.*: {BACKUP}")
                sys.exit(4)
            print(f"Using existing backup (already populated): {BACKUP}")
            return [p.name for p in existing]

    BACKUP.mkdir(parents=True, exist_ok=True)
    files = find_files("QuikPlan", DATA)
    if not files:
        print("BLOCKED: no QuikPlan.* files to back up")
        sys.exit(4)
    copied = []
    for src in files:
        dst = BACKUP / src.name
        shutil.copy2(src, dst)
        copied.append(src.name)
        print(f"  backed up {src.name} -> {dst}")
    if not any(p.suffix.lower() == ".dbf" for p in find_files("QuikPlan", BACKUP)):
        print("BLOCKED: backup missing QuikPlan.dbf")
        sys.exit(4)
    print(f"BACKUP OK: {BACKUP} ({len(copied)} files)")
    return copied


def apply_flags() -> dict:
    path = find_dbf("QuikPlan", DATA)
    table = dbf.Table(str(path))
    table.open(mode=dbf.READ_WRITE)
    non_meds_updated = 0
    meds_updated = 0
    try:
        if len(table) != EXPECTED_ROWS:
            print(f"STOP: Unexpected QuikPlan row count during write: {len(table)}")
            sys.exit(5)
        for record in table:
            pt = str(record.PLANTYPE or "").strip().casefold()
            if pt == "meds":
                dbf.write(record, HCOMMIP=True, HRIGPKEY=True)
                meds_updated += 1
            else:
                dbf.write(record, HCOMMIP=False, HRIGPKEY=False)
                non_meds_updated += 1
    finally:
        table.close()
    return {
        "path": str(path),
        "non_meds_set_false": non_meds_updated,
        "meds_set_true": meds_updated,
    }


def post_verify() -> dict:
    from data_governance.rules.plan_setup_integrity.common import decode_logical

    path = find_dbf("QuikPlan", DATA)
    table = DBF(str(path), load=True, ignore_missing_memofile=True)
    records = list(table)
    if len(records) != EXPECTED_ROWS:
        print(f"STOP: post-verify row count ≠ {EXPECTED_ROWS}: {len(records)}")
        sys.exit(6)

    hcomm_raw, hrig_raw = _scan_logical_raw_bytes(path)
    bad = []
    true_false_ok = 0
    for i, row in enumerate(records, start=1):
        pt = _plan_type(row)
        hc, _, _ = decode_logical(row.get("HCOMMIP"))
        hr, _, _ = decode_logical(row.get("HRIGPKEY"))
        if pt == "meds":
            if hc is not True or hr is not True:
                bad.append({"row": i, "PLANTYPE": pt, "HCOMMIP": hc, "HRIGPKEY": hr})
        else:
            if hc is not False or hr is not False:
                bad.append({"row": i, "PLANTYPE": pt, "HCOMMIP": hc, "HRIGPKEY": hr})
            else:
                true_false_ok += 1

    out = {
        "row_count": len(records),
        "decode_false_false_non_meds": true_false_ok,
        "bad_rows": bad[:20],
        "bad_count": len(bad),
        "hcommip_raw_bytes_after": dict(hcomm_raw),
        "hrigpkey_raw_bytes_after": dict(hrig_raw),
    }

    if bad:
        print(f"STOP: post-verify decode failures: {len(bad)}")
        print(bad[:5])
        sys.exit(7)

    # Expect F (or equivalent false byte from dbf package)
    false_like = {"F", "f", "N", "n", "0"}
    hcomm_false = sum(v for k, v in hcomm_raw.items() if k in false_like)
    hrig_false = sum(v for k, v in hrig_raw.items() if k in false_like)
    if hcomm_false != EXPECTED_ROWS or hrig_false != EXPECTED_ROWS:
        print(
            f"STOP: raw bytes not all False-like: "
            f"HCOMMIP={dict(hcomm_raw)} HRIGPKEY={dict(hrig_raw)}"
        )
        sys.exit(8)

    print("POST-VERIFY OK")
    print(f"  decode False/False non-MEDS={true_false_ok}")
    print(f"  HCOMMIP raw after={dict(hcomm_raw)}")
    print(f"  HRIGPKEY raw after={dict(hrig_raw)}")
    return out


def main() -> None:
    pre = preflight_or_stop()
    backed_up = create_backup()
    if not BACKUP.is_dir() or not find_files("QuikPlan", BACKUP):
        print("BLOCKED: backup missing after create_backup")
        sys.exit(4)
    apply_info = apply_flags()
    post = post_verify()
    payload = {
        "item": "DG-R-005",
        "preflight": pre,
        "backup_dir": str(BACKUP),
        "backed_up_files": backed_up,
        "apply": apply_info,
        "post_verify": post,
        "wpa_writes": 0,
        "rule_changed": False,
    }
    ARTIFACT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {ARTIFACT}")
    print("DG-R-005 APPLY COMPLETE")


if __name__ == "__main__":
    main()
