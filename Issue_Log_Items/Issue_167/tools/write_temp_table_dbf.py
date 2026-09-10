"""Write Issue #167 Temp table (MPOLICY, MPHASE, MLASTANN) as DBF + CDX.

Desktop destination requested by Warren 2026-09-10. Not a QLAdmin load table.
"""

from __future__ import annotations

import csv
import struct
from pathlib import Path

import dbf

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "QLA_Migration" / "Output" / "Test_Validation" / "quikridr.csv"
CSV_OUT = ROOT / "QLA_Migration" / "Output" / "Test_Validation" / "Temp table.csv"
DEST_DIR = Path(r"C:\Users\warren\Desktop")
DBF_PATH = DEST_DIR / "Temp table.dbf"
CDX_PATH = DEST_DIR / "Temp table.cdx"

PAGE = 512
KEY_LEN = 11
TAG_NAME = "MPOLICY"
KEY_EXPR = "MPOLICY"


def _n(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def _load_rows() -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    with SRC.open(newline="", encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            rows.append((_n(r.get("MPOLICY")), _n(r.get("MPHASE")), _n(r.get("MLASTANN"))))
    if not rows:
        raise SystemExit("FAIL: no quikridr rows")
    return rows


def _write_csv(rows: list[tuple[str, str, str]]) -> None:
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["MPOLICY", "MPHASE", "MLASTANN"])
        w.writerows(rows)


def _write_dbf(rows: list[tuple[str, str, str]]) -> None:
    for side in (DBF_PATH, CDX_PATH, DEST_DIR / "Temp table.fpt"):
        if side.is_file():
            side.unlink()
    table = dbf.Table(
        str(DBF_PATH),
        "MPOLICY C(11); MPHASE N(2,0); MLASTANN N(3,0)",
        dbf_type="vfp",
    )
    table.open(mode=dbf.READ_WRITE)
    for pol, phase, dur in rows:
        table.append((pol[:11].ljust(11), int(phase or 0), int(dur or 0)))
    table.close()
    # VFP table flag: bit 0x01 = structural CDX present
    with DBF_PATH.open("r+b") as fh:
        fh.seek(28)
        flags = fh.read(1)[0] | 0x01
        fh.seek(28)
        fh.write(bytes([flags]))


def _u16(n: int) -> bytes:
    return struct.pack("<H", n & 0xFFFF)


def _i32(n: int) -> bytes:
    return struct.pack("<i", n)


def _u32(n: int) -> bytes:
    return struct.pack("<I", n & 0xFFFFFFFF)


def _pad(data: bytes, size: int, fill: int = 0) -> bytes:
    if len(data) > size:
        return data[:size]
    return data + bytes([fill]) * (size - len(data))


def _node(attr: int, nkeys: int, left: int, right: int, body: bytes) -> bytes:
    raw = _u16(attr) + _u16(nkeys) + _i32(left) + _i32(right) + body
    return _pad(raw, PAGE)


def _write_cdx(rows: list[tuple[str, str, str]]) -> None:
    """FoxPro 2.x-style non-compact compound CDX, one tag MPOLICY (duplicates OK)."""
    entries = sorted(
        ((pol[:11].ljust(11).encode("ascii", "replace"), recno) for recno, (pol, _, _) in enumerate(rows, start=1)),
        key=lambda x: (x[0], x[1]),
    )
    entry_size = 4 + KEY_LEN + 4  # child/0 + key + recno
    keys_per = (PAGE - 12) // entry_size
    if keys_per < 2:
        raise SystemExit("FAIL: CDX page cannot hold keys")

    def pack_entries(items: list[tuple[bytes, int, int]]) -> bytes:
        # items: (key, recno, child_or_zero)
        buf = bytearray()
        for key, recno, child in items:
            buf.extend(_i32(child))
            buf.extend(_pad(key, KEY_LEN, 0x20))
            buf.extend(_u32(recno))
        return bytes(buf)

    # Build leaf pages (attr 2, or 3 if single page)
    leaves: list[bytes] = []
    leaf_maxkeys: list[tuple[bytes, int]] = []
    chunks = [entries[i : i + keys_per] for i in range(0, len(entries), keys_per)]
    for i, chunk in enumerate(chunks):
        left = i - 1 if i else -1
        right = i + 1 if i + 1 < len(chunks) else -1
        packed = pack_entries([(k, rec, 0) for k, rec in chunk])
        leaves.append((left, right, packed, len(chunk)))
        leaf_maxkeys.append(chunk[-1])

    pages: list[bytes] = []

    def add(page: bytes) -> int:
        pages.append(_pad(page, PAGE))
        return len(pages)  # 1-based page number (page 0 header is separate)

    # Page 0 written last. Page 1 = tag-index leaf. Page 2 = tag header.
    # Data leaves start at 3.
    tag_index_page = 1
    tag_header_page = 2
    first_leaf_page = 3

    leaf_pages_n = []
    for i, (left, right, packed, nkeys) in enumerate(leaves):
        attr = 3 if len(leaves) == 1 else 2
        lptr = (first_leaf_page + left) if left >= 0 else -1
        rptr = (first_leaf_page + right) if right >= 0 else -1
        # placeholders until we know page numbers — sequential
        leaf_pages_n.append(first_leaf_page + i)

    # Rebuild leaves with actual sibling pointers
    leaf_blobs = []
    for i, (left, right, packed, nkeys) in enumerate(leaves):
        attr = 3 if len(leaves) == 1 else 2
        lptr = leaf_pages_n[left] if left >= 0 else -1
        rptr = leaf_pages_n[right] if right >= 0 else -1
        leaf_blobs.append(_node(attr, nkeys, lptr, rptr, packed))

    # Interior levels over leaves
    def build_level(child_pages: list[int], child_max: list[tuple[bytes, int]], is_root: bool) -> tuple[list[int], list[tuple[bytes, int]], list[bytes]]:
        blobs: list[bytes] = []
        pages_out: list[int] = []
        max_out: list[tuple[bytes, int]] = []
        groups = [
            list(zip(child_pages[i : i + keys_per], child_max[i : i + keys_per]))
            for i in range(0, len(child_pages), keys_per)
        ]
        # page numbers assigned after we know how many interiors we add — caller handles
        return groups  # type: ignore

    # Assign data leaf pages first (we already know numbers)
    # Interiors come after all leaves
    next_page = first_leaf_page + len(leaf_blobs)
    levels = [(leaf_pages_n, leaf_maxkeys, leaf_blobs)]

    cur_pages, cur_max, cur_blobs = leaf_pages_n, leaf_maxkeys, leaf_blobs
    interior_blobs: list[tuple[int, bytes]] = []  # (page_no, blob) filled after numbering

    pending_groups: list[list[tuple[int, tuple[bytes, int]]]] = []
    while len(cur_pages) > 1 or not interior_blobs and len(cur_pages) > 1:
        groups = [
            list(zip(cur_pages[i : i + keys_per], cur_max[i : i + keys_per]))
            for i in range(0, len(cur_pages), keys_per)
        ]
        if len(groups) == 1 and len(cur_pages) <= keys_per:
            # single interior/root will be emitted
            pending_groups.append(groups[0])
            break
        if len(groups) == 1:
            pending_groups.append(groups[0])
            break
        pending_groups.append(None)  # placeholder to compute bottom-up differently
        break

    # Simpler: always build interiors from the bottom until one root
    all_numbered: list[tuple[int, bytes]] = []
    for i, blob in enumerate(leaf_blobs):
        all_numbered.append((leaf_pages_n[i], blob))

    level_pages = leaf_pages_n
    level_max = leaf_maxkeys
    while len(level_pages) > 1:
        groups = [
            list(zip(level_pages[i : i + keys_per], level_max[i : i + keys_per]))
            for i in range(0, len(level_pages), keys_per)
        ]
        new_pages: list[int] = []
        new_max: list[tuple[bytes, int]] = []
        is_root = len(groups) == 1
        for gi, grp in enumerate(groups):
            pno = next_page
            next_page += 1
            packed = pack_entries([(k, rec, child) for child, (k, rec) in grp])
            left = -1
            right = -1
            if not is_root:
                left = (pno - 1) if gi else -1
                # right filled in second pass — keep -1 for interiors (siblings optional)
            attr = 1 if is_root else 0
            blob = _node(attr, len(grp), left, right, packed)
            all_numbered.append((pno, blob))
            new_pages.append(pno)
            new_max.append(grp[-1][1])
        level_pages, level_max = new_pages, new_max

    data_root = level_pages[0]

    # Tag header (page 2)
    tag = bytearray(PAGE)
    tag[0:4] = _u32(data_root)
    tag[4:8] = _i32(-1)
    tag[8:12] = _u32(1)
    tag[12] = KEY_LEN
    tag[13] = 0x40  # compound, not compact, not unique
    tag[14:16] = _u16(1)
    # key expression at 0xF8 (248)
    tag[248:248 + len(KEY_EXPR)] = KEY_EXPR.encode("ascii")
    # tag name at 0x1E8 (488)
    tag[488:488 + 10] = _pad(TAG_NAME.encode("ascii"), 10, 0x20)

    # Tag-index leaf (page 1): one key = tag name -> tag header page
    tag_leaf_body = pack_entries([( _pad(TAG_NAME.encode("ascii"), 10, 0x20) + b" ", 0, tag_header_page)])
    # tag-index key length is 10, not 11 — pack manually
    tag_leaf_body = _i32(tag_header_page) + _pad(TAG_NAME.encode("ascii"), 10, 0x20) + _u32(0)
    tag_leaf = _node(3, 1, -1, -1, tag_leaf_body)

    # File header (page 0) — header of the tag-name index
    header = bytearray(PAGE)
    header[0:4] = _u32(tag_index_page)  # root of tag index
    header[4:8] = _i32(-1)
    header[8:12] = _u32(next_page)  # next unused page
    header[12] = 10  # tag-name key length
    header[13] = 0x40
    header[14:16] = _u16(1)

    out = bytearray()
    out.extend(header)  # page 0
    # pages 1.. must be placed by number
    by_no = {1: tag_leaf, 2: bytes(tag)}
    for pno, blob in all_numbered:
        by_no[pno] = blob
    max_no = max(by_no)
    for pno in range(1, max_no + 1):
        if pno not in by_no:
            raise SystemExit(f"FAIL: CDX hole at page {pno}")
        out.extend(_pad(by_no[pno], PAGE))

    # fix next-unused in header
    unused = max_no + 1
    out[8:12] = _u32(unused)
    CDX_PATH.write_bytes(bytes(out))


def main() -> int:
    rows = _load_rows()
    _write_csv(rows)
    _write_dbf(rows)
    _write_cdx(rows)
    table = dbf.Table(str(DBF_PATH))
    table.open()
    n = len(table)
    gold = [
        (r.mpolicy.strip(), int(r.mphase), int(r.mlastann))
        for r in table
        if r.mpolicy.strip() == "9010397528C"
    ]
    print("structure", table.structure())
    table.close()
    print(f"csv {CSV_OUT} rows={len(rows)}")
    print(f"dbf {DBF_PATH} records={n} bytes={DBF_PATH.stat().st_size}")
    print(f"cdx {CDX_PATH} bytes={CDX_PATH.stat().st_size} tag={TAG_NAME}")
    print(f"gold {gold}")
    if n != len(rows):
        print("FAIL: dbf count mismatch")
        return 1
    if gold != [("9010397528C", 1, 54), ("9010397528C", 2, 54)]:
        print("FAIL: gold mismatch")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
