"""Rebuild PFSA_Annuity_interest/QUIKAINT.DBF from 'Copy of PFSA_Interest_Rates.xlsx'.

Scope: the 7 annuity plans already present in the delivered QUIKAINT.DBF
(1200WT, A103RO, A104ES, A105IR, A106PR, A108SP, A109IM). Life plans on the
sheet (1205IS, 1206UL) belong to QuikUint and are excluded.

Column mapping ("Current Products" sheet, one DBF row per plan per year,
MEFFDATE = Jan 1 of the year):

  2019  MINTRATE=MINTRATE1 = D (2019 Crediting)
  2020  MINTRATE=MINTRATE1 = E
  2021  MINTRATE=MINTRATE1 = F
  2022  MINTRATE=MINTRATE1 = G
  2023  MINTRATE=MINTRATE1 = R (2023 Crediting)
  2024  MINTRATE = H (2024 Renewal),  MINTRATE1 = J (2024 Promotional)
  2025  MINTRATE = K (2025 Renewal),  MINTRATE1 = M (2025 Promotional)
  2026  MINTRATE = N (2026 Renewal),  MINTRATE1 = P (2026 Promotional)

A "CORRECT RATES" row directly under a plan row overrides any column where it
has a value ('N/A' override means the year is skipped). MINTRATE1 falls back
to the renewal rate when no promotional rate exists. Years with N/A renewal
are skipped (A109IM 2025/2026).

The DBF header (162 bytes) is cloned from the existing QUIKAINT.DBF so the
physical layout matches QLAdmin exactly; only record count and update date
change. The prior file is saved as QUIKAINT_backup_<date>.DBF.
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
OUT_DBF = os.path.join(FOLDER, "QUIKAINT.DBF")

HEADER_LEN = 162
RECORD_LEN = 29

ANNUITY_PLANS = {"1200WT", "A103RO", "A104ES", "A105IR", "A106PR", "A108SP", "A109IM"}

# year -> (renewal column index, promo column index or None); 0-based, A=0 .. R=17
YEAR_COLS = {
    2019: (3, None),   # D
    2020: (4, None),   # E
    2021: (5, None),   # F
    2022: (6, None),   # G
    2023: (17, None),  # R  (2023 Crediting)
    2024: (7, 9),      # H renewal, J promo
    2025: (10, 12),    # K renewal, M promo
    2026: (13, 15),    # N renewal, P promo
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

        # Effective cell values = plan row overlaid by its CORRECT RATES row.
        cells = list(r)
        if i + 1 < len(rows) and str(rows[i + 1][2] or "").strip().upper() == "CORRECT RATES":
            for idx, v in enumerate(rows[i + 1]):
                if idx >= 3 and v is not None:
                    cells[idx] = v

        for year in sorted(YEAR_COLS):
            ren_idx, promo_idx = YEAR_COLS[year]
            renewal = parse_rate(cells[ren_idx])
            if renewal is None or renewal == "NA":
                continue
            promo = parse_rate(cells[promo_idx]) if promo_idx is not None else None
            if promo == "NA":
                promo = None
            mintrate1 = promo if promo is not None else renewal
            for plan in plans:
                records.append({
                    "MPLAN": plan,
                    "MEFFDATE": f"{year}0101",
                    "MINTRATE": round(renewal, 4),
                    "MINTRATE1": round(mintrate1, 4),
                })

    records.sort(key=lambda x: (x["MPLAN"], x["MEFFDATE"]))
    return records


def read_old_records():
    old = {}
    for rec in DBF(OUT_DBF, load=True).records:
        key = (rec["MPLAN"].strip(), rec["MEFFDATE"].strftime("%Y%m%d"))
        old[key] = (float(rec["MINTRATE"]), float(rec["MINTRATE1"]))
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
                + f"{r['MINTRATE']:7.4f}".encode("ascii")
                + f"{r['MINTRATE1']:7.4f}".encode("ascii")
            )
            assert len(rec) == RECORD_LEN, (len(rec), r)
            f.write(rec)
        f.write(b"\x1a")


def main():
    with open(OUT_DBF, "rb") as f:
        header = f.read(HEADER_LEN)

    old = read_old_records()
    records = read_sheet_records()
    new = {(r["MPLAN"], r["MEFFDATE"]): (r["MINTRATE"], r["MINTRATE1"]) for r in records}

    print("=== Diff (old -> new) ===")
    changes = 0
    for key in sorted(set(old) | set(new)):
        o, n = old.get(key), new.get(key)
        if o == n:
            continue
        changes += 1
        if o is None:
            print(f"ADDED   {key[0]} {key[1]}: MINTRATE={n[0]:.4f} MINTRATE1={n[1]:.4f}")
        elif n is None:
            print(f"REMOVED {key[0]} {key[1]}: was MINTRATE={o[0]:.4f} MINTRATE1={o[1]:.4f}")
        else:
            print(f"CHANGED {key[0]} {key[1]}: "
                  f"MINTRATE {o[0]:.4f}->{n[0]:.4f}  MINTRATE1 {o[1]:.4f}->{n[1]:.4f}")
    print(f"Rows: {len(old)} -> {len(records)}   changed/added/removed: {changes}")

    backup = os.path.join(FOLDER, f"QUIKAINT_backup_{datetime.date.today():%Y%m%d}.DBF")
    if not os.path.exists(backup):
        shutil.copy2(OUT_DBF, backup)
        print(f"Backup: {backup}")

    write_dbf(records, header)
    print(f"Wrote {len(records)} records -> {OUT_DBF}")

    # Verify round-trip
    check = read_old_records()
    assert check == new, "Round-trip verification failed"
    print("Round-trip verification: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
