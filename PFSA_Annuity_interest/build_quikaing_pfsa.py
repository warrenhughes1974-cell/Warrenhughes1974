"""Rebuild PFSA_Annuity_interest/QUIKAING.DBF from 'Copy of PFSA_Interest_Rates.xlsx'.

QUIKAING = annuity minimum guaranteed interest table:
  MPLAN C(6), MEFFDATE D(8), MGTDRATE N(7,4), MISSUEST C(2)

Scope: same 7 annuity plans as QUIKAINT (1200WT, A103RO, A104ES, A105IR,
A106PR, A108SP, A109IM). The spreadsheet only publishes minimum/guaranteed
rates for 2024-2026 ("Current Products" sheet):

  2024  MGTDRATE = column I (2024 Minimum Interest)
  2025  MGTDRATE = column L (2025 Minimum Interest)
  2026  MGTDRATE = column O (2026 Minimum Guarantee)

"CORRECT RATES" override rows apply as in the QUIKAINT build; an 'N/A'
(original or override) skips that year (A109IM 2025/2026). MISSUEST is
defaulted to '00' on every row per business direction 2026-07-20.

Header cloned from the existing QUIKAING.DBF (header 162, record 24); prior
file saved as QUIKAING_backup_<date>.DBF.
"""

import datetime
import os
import shutil
import struct
import sys

import openpyxl
from dbfread import DBF

FOLDER = os.path.dirname(os.path.abspath(__file__))
XLSX = os.path.join(FOLDER, "Copy of PFSA_Interest_Rates.xlsx")
OUT_DBF = os.path.join(FOLDER, "QUIKAING.DBF")

HEADER_LEN = 162
RECORD_LEN = 24
MISSUEST_DEFAULT = "00"

ANNUITY_PLANS = {"1200WT", "A103RO", "A104ES", "A105IR", "A106PR", "A108SP", "A109IM"}

# year -> minimum/guaranteed column index; 0-based, A=0 (I=8, L=11, O=14)
YEAR_COLS = {
    2024: 8,
    2025: 11,
    2026: 14,
}


def parse_rate(value):
    """Return float percent, 'NA' for explicit N/A, or None for blank."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    if s.upper() in ("N/A", "NA"):
        return "NA"
    if s.endswith("%"):
        s = s[:-1]
    try:
        v = float(s)
    except ValueError:
        return None
    return v * 100.0 if v < 1.0 else v


def split_plans(cell):
    if cell is None:
        return []
    s = str(cell).strip()
    if not s or "no match" in s.lower():
        return []
    return [p.strip() for p in s.split("/") if p.strip()]


def read_sheet_records():
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    ws = wb["Current Products"]
    rows = list(ws.iter_rows(values_only=True))

    records = []
    for i, r in enumerate(rows):
        plans = [p for p in split_plans(r[1]) if p in ANNUITY_PLANS]
        if not plans:
            continue

        cells = list(r)
        if i + 1 < len(rows) and str(rows[i + 1][2] or "").strip().upper() == "CORRECT RATES":
            for idx, v in enumerate(rows[i + 1]):
                if idx >= 3 and v is not None:
                    cells[idx] = v

        for year in sorted(YEAR_COLS):
            rate = parse_rate(cells[YEAR_COLS[year]])
            if rate is None or rate == "NA":
                continue
            for plan in plans:
                records.append({
                    "MPLAN": plan,
                    "MEFFDATE": f"{year}0101",
                    "MGTDRATE": round(rate, 4),
                    "MISSUEST": MISSUEST_DEFAULT,
                })

    records.sort(key=lambda x: (x["MPLAN"], x["MEFFDATE"]))
    return records


def read_old_records():
    old = {}
    for rec in DBF(OUT_DBF, load=True).records:
        key = (rec["MPLAN"].strip(), rec["MEFFDATE"].strftime("%Y%m%d"))
        old[key] = (float(rec["MGTDRATE"]), rec["MISSUEST"].strip())
    return old


def write_dbf(records, header):
    today = datetime.date.today()
    header = bytearray(header)
    header[1] = today.year - 1900
    header[2] = today.month
    header[3] = today.day
    struct.pack_into("<L", header, 4, len(records))

    with open(OUT_DBF, "wb") as f:
        f.write(header)
        for r in records:
            rec = (
                b" "
                + r["MPLAN"].ljust(6).encode("ascii")
                + r["MEFFDATE"].encode("ascii")
                + f"{r['MGTDRATE']:7.4f}".encode("ascii")
                + r["MISSUEST"].ljust(2).encode("ascii")
            )
            assert len(rec) == RECORD_LEN, (len(rec), r)
            f.write(rec)
        f.write(b"\x1a")


def main():
    with open(OUT_DBF, "rb") as f:
        header = f.read(HEADER_LEN)

    old = read_old_records()
    records = read_sheet_records()
    new = {(r["MPLAN"], r["MEFFDATE"]): (r["MGTDRATE"], r["MISSUEST"]) for r in records}

    print("=== Diff (old -> new) ===")
    changes = 0
    for key in sorted(set(old) | set(new)):
        o, n = old.get(key), new.get(key)
        if o == n:
            continue
        changes += 1
        if o is None:
            print(f"ADDED   {key[0]} {key[1]}: MGTDRATE={n[0]:.4f} MISSUEST={n[1]!r}")
        elif n is None:
            print(f"REMOVED {key[0]} {key[1]}: was MGTDRATE={o[0]:.4f} MISSUEST={o[1]!r}")
        else:
            print(f"CHANGED {key[0]} {key[1]}: "
                  f"MGTDRATE {o[0]:.4f}->{n[0]:.4f}  MISSUEST {o[1]!r}->{n[1]!r}")
    print(f"Rows: {len(old)} -> {len(records)}   changed/added/removed: {changes}")

    backup = os.path.join(FOLDER, f"QUIKAING_backup_{datetime.date.today():%Y%m%d}.DBF")
    if not os.path.exists(backup):
        shutil.copy2(OUT_DBF, backup)
        print(f"Backup: {backup}")

    write_dbf(records, header)
    print(f"Wrote {len(records)} records -> {OUT_DBF}")

    check = read_old_records()
    assert check == new, "Round-trip verification failed"
    print("Round-trip verification: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
