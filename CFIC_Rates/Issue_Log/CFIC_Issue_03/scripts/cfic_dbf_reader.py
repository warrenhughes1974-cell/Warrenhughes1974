"""Minimal FoxPro DBF reader for Citizens reserve/plan tables (read-only)."""
from __future__ import annotations

import struct
from pathlib import Path


def load_dbf(path: str | Path) -> tuple[list[tuple[str, str, int, int]], list[dict[str, str]]]:
    data = Path(path).read_bytes()
    numrec = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    rec_len = struct.unpack("<H", data[10:12])[0]
    fields: list[tuple[str, str, int, int]] = []
    pos = 32
    while pos < header_len - 1:
        name = data[pos : pos + 11].split(b"\x00")[0].decode("ascii", errors="replace").strip()
        if not name or name == "\x0d":
            break
        fields.append((name, chr(data[pos + 11]), data[pos + 16], data[pos + 17]))
        pos += 32
    start = header_len
    rows: list[dict[str, str]] = []
    for i in range(numrec):
        rec = data[start + i * rec_len : start + (i + 1) * rec_len]
        pos = 1
        row: dict[str, str] = {}
        for name, ftype, flen, _fdec in fields:
            raw = rec[pos : pos + flen]
            pos += flen
            row[name] = raw.decode("cp437" if ftype in "CV" else "ascii", errors="replace").strip()
        rows.append(row)
    return fields, rows
