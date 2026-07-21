"""In-place delete-and-append reload of QUIKAINT.DBF / QUIKAING.DBF.

Per business direction 2026-07-20: do NOT create new tables. The header of
each table is restored byte-for-byte from the original Advantage-created file
(the _backup copy) -- including the last-update date bytes -- and only the
record count (header bytes 4-7) and the record data area are changed.
Files are opened r+b so the existing file (identity, ACLs, attributes) is
kept; nothing is deleted or recreated.

Data comes from the build scripts' readers (already validated against the
spreadsheet): build_quikaint_pfsa.read_sheet_records() and
build_quikaing_pfsa.read_sheet_records().
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import build_quikaint_pfsa as aint
import build_quikaing_pfsa as aing

FOLDER = os.path.dirname(os.path.abspath(__file__))
HEADER_LEN = 162


def reload_inplace(dbf_path, backup_path, records, encode_record, record_len):
    with open(backup_path, "rb") as f:
        header = bytearray(f.read(HEADER_LEN))
    struct.pack_into("<L", header, 4, len(records))

    with open(dbf_path, "r+b") as f:
        f.seek(0)
        f.write(header)
        for r in records:
            rec = encode_record(r)
            assert len(rec) == record_len, (len(rec), r)
            f.write(rec)
        f.write(b"\x1a")
        f.truncate()
    print(f"{os.path.basename(dbf_path)}: {len(records)} records written in place")


def encode_aint(r):
    return (b" "
            + r["MPLAN"].ljust(6).encode("ascii")
            + r["MEFFDATE"].encode("ascii")
            + f"{r['MINTRATE']:7.4f}".encode("ascii")
            + f"{r['MINTRATE1']:7.4f}".encode("ascii"))


def encode_aing(r):
    return (b" "
            + r["MPLAN"].ljust(6).encode("ascii")
            + r["MEFFDATE"].encode("ascii")
            + f"{r['MGTDRATE']:7.4f}".encode("ascii")
            + r["MISSUEST"].ljust(2).encode("ascii"))


def main():
    reload_inplace(
        os.path.join(FOLDER, "QUIKAINT.DBF"),
        os.path.join(FOLDER, "QUIKAINT_backup_20260720.DBF"),
        aint.read_sheet_records(), encode_aint, 29)
    reload_inplace(
        os.path.join(FOLDER, "QUIKAING.DBF"),
        os.path.join(FOLDER, "QUIKAING_backup_20260720.DBF"),
        aing.read_sheet_records(), encode_aing, 24)

    # Verify: header identical to original except record count; data readable.
    from dbfread import DBF
    for name in ("QUIKAINT", "QUIKAING"):
        cur = open(os.path.join(FOLDER, f"{name}.DBF"), "rb").read()
        orig = open(os.path.join(FOLDER, f"{name}_backup_20260720.DBF"), "rb").read()
        diffs = [i for i in range(HEADER_LEN) if cur[i] != orig[i] and not (4 <= i <= 7)]
        n = len(DBF(os.path.join(FOLDER, f"{name}.DBF"), load=True).records)
        print(f"{name}: header diffs outside record-count field: {diffs}; "
              f"readable records: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
