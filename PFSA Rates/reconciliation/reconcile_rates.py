"""
Read-only reconciliation: PFSA premium CSVs vs QuikGps.dbf gross-premium factors.
Exact text match using QLAdmin format_factor convention.
"""
from __future__ import annotations

import csv
import struct
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from qla_core.rate_dbf_schema import format_factor  # noqa: E402

RATES_DIR = Path(__file__).resolve().parents[1]
DBF_PATH = RATES_DIR / "QuikGps.dbf"
OUT_DIR = Path(__file__).resolve().parent

TERM_COL_MAP = {
    "MRN": ("M", "RN"),
    "MRT": ("M", "RT"),
    "FRN": ("F", "RN"),
    "FRT": ("F", "RT"),
    "MSP": ("M", "SP"),
    "MPN": ("M", "PN"),
    "FSP": ("F", "SP"),
    "FPN": ("F", "PN"),
}

UL_COL_MAP = {
    "B1MaleNonsmoker": ("M", "NS", "01"),
    "B1MaleSmoker": ("M", "SM", "01"),
    "B1FemaleNonsmoker": ("F", "NS", "01"),
    "B1FemaleSmoker": ("F", "SM", "01"),
    "B2MaleSuperPreferred": ("M", "SP", "02"),
    "B2MalePreferred": ("M", "PN", "02"),
    "B2MaleResidual": ("M", "RN", "02"),
    "B2MaleSmoker": ("M", "SM", "02"),
    "B2FemaleSuperPreferred": ("F", "SP", "02"),
    "B2FemalePreferred": ("F", "PN", "02"),
    "B2FemaleResidual": ("F", "RN", "02"),
    "B2FemaleSmoker": ("F", "SM", "02"),
}

PAY_COL_MAP = {
    "MNT": ("M", "nt"),
    "MTB": ("M", "tb"),
    "FNT": ("F", "nt"),
    "FTB": ("F", "tb"),
}

PLAN_CONFIG = [
    ("110PYL", "age_in_grid", "10-pay-prem.csv", "pay"),
    ("120PYL", "age_in_grid", "20-pay-prem.csv", "pay"),
    ("1206UL", "age_in_grid", "ul-prem.csv", "ul"),
    ("5210TB", "duration_in_grid", "term-15-prem.csv", "term"),
    ("5202TB", "duration_in_grid", "term-20-prem.csv", "term"),
    ("5203TB", "duration_in_grid", "term-30-30-guarantee-prem.csv", "term"),
    ("5204TB", "duration_in_grid", "term-30-20-guarantee-prem.csv", "term"),
    ("9ADB10", "age_in_grid", "adb-prem.csv", "adb"),
    ("9ADB20", "age_in_grid", "adb-prem.csv", "adb"),
    ("9ADBIS", "age_in_grid", "adb-prem.csv", "adb"),
    ("9ADBPY", "age_in_grid", "adb-prem.csv", "adb"),
]

SKIP_BANDS = {"MX"}
SKIP_GENDERS = {"0"}


def factor_equal(a: str, b: str) -> bool:
    if a == b:
        return True
    if not a or not b:
        return False
    try:
        return float(a) == float(b)
    except ValueError:
        return False


def fmt_csv_rate(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    try:
        if float(raw) == 0.0:
            return ""
    except ValueError:
        pass
    text, fits, _ = format_factor(raw)
    return text if fits else raw


def pay_uwclass(age: int, tobacco: str) -> str:
    if age < 18:
        return "JV"
    return "NT" if tobacco == "nt" else "TB"


def parse_dbf(path: Path) -> list[dict]:
    with open(path, "rb") as f:
        hdr = f.read(32)
        nrec = struct.unpack("<I", hdr[4:8])[0]
        hsize = struct.unpack("<H", hdr[8:10])[0]
        rsize = struct.unpack("<H", hdr[10:12])[0]
        fields = []
        while True:
            fd = f.read(32)
            if not fd or fd[0] == 0x0D:
                break
            fields.append((fd[0:11].split(b"\x00")[0].decode("ascii", "replace"), fd[16], fd[17]))
        f.seek(hsize)
        rows = []
        for _ in range(nrec):
            rec = f.read(rsize)
            if not rec or len(rec) < rsize or rec[0:1] == b"*":
                continue
            off = 1
            vals = {}
            for name, flen, _ in fields:
                vals[name] = rec[off : off + flen].decode("latin-1", "replace").strip()
                off += flen
            rows.append(vals)
    return rows


def expand_ql(rows: list[dict], included_plans: set[str]) -> dict[tuple, str]:
    out = {}
    gp_cols = [f"GP{i}" for i in range(10)]
    plan_axis = {p: axis for p, axis, _, _ in PLAN_CONFIG}

    for r in rows:
        plan = r["PLAN"]
        if plan not in included_plans:
            continue
        if r["BAND"] in SKIP_BANDS or r["GENDER"] in SKIP_GENDERS:
            continue
        axis = plan_axis[plan]
        for ci, col in enumerate(gp_cols):
            val = r.get(col, "")
            if not val or val in ("0.00", "0", ".00"):
                continue
            dur_slot = int(r["CNTL"]) * 10 + ci
            if axis == "age_in_grid":
                age = dur_slot
                duration = 0
            else:
                age = int(r["AGE"])
                duration = dur_slot + 1
            key = (plan, age, r["GENDER"], r["UWCLASS"], r["BAND"], duration)
            out[key] = val
    return out


def parse_pay_csv(path: Path, plan: str) -> dict[tuple, str]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    headers = rows[0]
    out = {}
    for row in rows[1:]:
        if not row or not row[0].strip().isdigit():
            continue
        age = int(row[0].strip())
        for i, hdr in enumerate(headers):
            if hdr not in PAY_COL_MAP or i >= len(row):
                continue
            gender, tobacco = PAY_COL_MAP[hdr]
            text = fmt_csv_rate(row[i])
            if not text:
                continue
            key = (plan, age, gender, pay_uwclass(age, tobacco), "00", 0)
            out[key] = text
    return out


def parse_ul_csv(path: Path, plan: str) -> dict[tuple, str]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    headers = rows[0]
    out = {}
    for row in rows[1:]:
        if not row or not row[0].strip().isdigit():
            continue
        age = int(row[0].strip())
        for i, hdr in enumerate(headers):
            if hdr not in UL_COL_MAP or i >= len(row):
                continue
            gender, uw, band = UL_COL_MAP[hdr]
            if age < 18:
                uw = "JV"
            text = fmt_csv_rate(row[i])
            if not text:
                continue
            key = (plan, age, gender, uw, band, 0)
            out[key] = text
    return out


def parse_adb_csv(path: Path, plan: str) -> dict[tuple, str]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    out = {}
    for row in rows[1:]:
        if not row or not row[0].strip().isdigit():
            continue
        age = int(row[0].strip())
        if len(row) > 1:
            text = fmt_csv_rate(row[1])
            if text:
                out[(plan, age, "M", "00", "00", 0)] = text
        if len(row) > 3:
            text = fmt_csv_rate(row[3])
            if text:
                out[(plan, age, "F", "00", "00", 0)] = text
    return out


def parse_term_csv(path: Path, plan: str) -> dict[tuple, str]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    hdr0, hdr1 = rows[0], rows[1]
    segments = []
    current_band = None
    for i, (g0, g1) in enumerate(zip(hdr0, hdr1)):
        if g0 and "Band" in g0:
            try:
                current_band = str(int(g0.split("Band")[-1].strip())).zfill(2)
            except ValueError:
                current_band = None
        if g1 in TERM_COL_MAP and current_band:
            gender, uw = TERM_COL_MAP[g1]
            segments.append((i, current_band, gender, uw))

    out = {}
    for row in rows[2:]:
        if not row or not row[0].strip().isdigit():
            continue
        age = int(row[0].strip())
        for col_idx, band, gender, uw in segments:
            if col_idx >= len(row):
                continue
            text = fmt_csv_rate(row[col_idx])
            if not text:
                continue
            key = (plan, age, gender, uw, band, 1)
            out[key] = text
    return out


def load_csv_rates() -> dict[tuple, str]:
    loaders = {
        "pay": parse_pay_csv,
        "ul": parse_ul_csv,
        "adb": parse_adb_csv,
        "term": parse_term_csv,
    }
    out = {}
    for _plan, _axis, csv_name, layout in PLAN_CONFIG:
        path = RATES_DIR / csv_name
        chunk = loaders[layout](path, _plan)
        out.update(chunk)
    return out


def reconcile():
    included = {p for p, _, _, _ in PLAN_CONFIG}
    ql = expand_ql(parse_dbf(DBF_PATH), included)
    csv_rates = load_csv_rates()

    all_keys = set(ql) | set(csv_rates)
    rows = []
    summary = defaultdict(lambda: {"match": 0, "match_numeric": 0, "mismatch": 0, "ql_only": 0, "csv_only": 0})

    for key in sorted(all_keys):
        plan, age, gender, uw, band, duration = key
        qv = ql.get(key, "")
        cv = csv_rates.get(key, "")
        if qv and cv:
            if qv == cv:
                status = "MATCH"
                summary[plan]["match"] += 1
            elif factor_equal(qv, cv):
                status = "MATCH_NUMERIC"
                summary[plan]["match_numeric"] += 1
            else:
                status = "MISMATCH"
                summary[plan]["mismatch"] += 1
        elif qv:
            status = "QL_ONLY"
            summary[plan]["ql_only"] += 1
        else:
            status = "CSV_ONLY"
            summary[plan]["csv_only"] += 1
        rows.append({
            "status": status,
            "plan": plan,
            "age": age,
            "gender": gender,
            "uwclass": uw,
            "band": band,
            "duration": duration,
            "quikgps_factor": qv,
            "csv_factor": cv,
        })

    diff_path = OUT_DIR / "rate_diff.csv"
    with open(diff_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    sum_path = OUT_DIR / "reconciliation_summary.csv"
    with open(sum_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["plan", "match", "match_numeric", "mismatch", "ql_only", "csv_only"])
        w.writeheader()
        for plan in sorted(summary):
            s = summary[plan]
            w.writerow({"plan": plan, **s})

    mismatches = [r for r in rows if r["status"] == "MISMATCH"]
    print(f"Compared {len(all_keys)} keys across {len(included)} plans")
    print(f"  MATCH:          {sum(1 for r in rows if r['status']=='MATCH')}")
    print(f"  MATCH_NUMERIC:  {sum(1 for r in rows if r['status']=='MATCH_NUMERIC')}")
    print(f"  MISMATCH:       {len(mismatches)}")
    print(f"  QL_ONLY:   {sum(1 for r in rows if r['status']=='QL_ONLY')}")
    print(f"  CSV_ONLY:  {sum(1 for r in rows if r['status']=='CSV_ONLY')}")
    print(f"Wrote {diff_path}")
    print(f"Wrote {sum_path}")
    if mismatches[:5]:
        print("Sample mismatches:")
        for r in mismatches[:5]:
            print(f"  {r['plan']} age={r['age']} {r['gender']}/{r['uwclass']} band={r['band']} dur={r['duration']}: ql={r['quikgps_factor']} csv={r['csv_factor']}")


if __name__ == "__main__":
    reconcile()
