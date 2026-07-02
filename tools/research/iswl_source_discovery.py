#!/usr/bin/env python3
"""ISWL LifePRO source discovery analysis — research only, no converter changes."""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
OUT = BASE / "Issue_Log_Items" / "Issue_ISWL_Research"

ISWL_COV = {
    "658 CEN I", "658 CEN SD", "659 CEN II", "659 CEN SR", "659 CEN SD",
    "659 SR GD", "669 SR GD", "679 CEN SD",
}
ISWL_MPLAN = {
    "1658C1", "1658CS", "1659C2", "1659CR", "1659CS", "1659SR", "1669SR", "1679CS",
}
COV_TO_MPLAN = {
    "658 CEN I": "1658C1", "658 CEN SD": "1658CS", "659 CEN II": "1659C2",
    "659 CEN SR": "1659CR", "659 CEN SD": "1659CS", "659 SR GD": "1659SR",
    "669 SR GD": "1669SR", "679 CEN SD": "1679CS",
}


def analyze_rate_table():
    path = BASE / "plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv"
    total = iswl = 0
    types = Counter()
    by_cov_type = defaultdict(lambda: defaultdict(set))
    value_samples = defaultdict(list)

    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        for row in reader:
            total += 1
            cov = row.get("COVERAGE_ID", "").strip()
            if cov not in ISWL_COV:
                continue
            iswl += 1
            tc = row.get("TYPE_CODE", "").strip()
            types[(cov, tc)] += 1
            types[tc] += 1
            for d in ["SEX", "BAND", "UNDERWRITING_CLASS", "DURATION", "AGE"]:
                v = row.get(d, "").strip()
                if v:
                    by_cov_type[(cov, tc)][d].add(v)
            if len(value_samples[(cov, tc)]) < 3:
                value_samples[(cov, tc)].append(row.get("VALUE", ""))

    return {
        "file": str(path.relative_to(BASE)),
        "total_rows": total,
        "iswl_rows": iswl,
        "columns": cols,
        "type_counts": dict(types),
        "dimensions": {f"{k[0]}|{k[1]}": {d: sorted(v) for d, v in dims.items()} for k, dims in by_cov_type.items()},
        "value_samples": {f"{k[0]}|{k[1]}": v for k, v in value_samples.items()},
    }


def analyze_paagerat():
    path = BASE / "plan_analysis/source_data/rates/PAAGERAT_AttainedAge_Rates_Extract_20260428.csv"
    total = iswl = 0
    type_counts = Counter()
    by_cov_type = defaultdict(lambda: defaultdict(set))
    value_stats = defaultdict(lambda: {"min": None, "max": None, "n": 0})

    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        for row in reader:
            total += 1
            cov = row.get("COVERAGE_ID", "").strip()
            if cov not in ISWL_COV:
                continue
            iswl += 1
            tc = row.get("TYPE_CODE", "").strip()
            type_counts[(cov, tc)] += 1
            type_counts[tc] += 1
            kt = (cov, tc)
            for d in ["SEX", "BAND", "UWCLS", "AAGE_KEY0", "VALUE_INFO", "RECORD_SEQ", "SEQ"]:
                v = row.get(d, "").strip()
                if v:
                    by_cov_type[kt][d].add(v)
            try:
                vf = float(row.get("VALUE_FLOAT", "") or 0)
                st = value_stats[kt]
                st["n"] += 1
                st["min"] = vf if st["min"] is None else min(st["min"], vf)
                st["max"] = vf if st["max"] is None else max(st["max"], vf)
            except ValueError:
                pass

    return {
        "file": str(path.relative_to(BASE)),
        "total_rows": total,
        "iswl_rows": iswl,
        "columns": cols,
        "type_counts": {str(k): v for k, v in type_counts.items()},
        "dimensions": {f"{k[0]}|{k[1]}": {d: sorted(v) for d, v in dims.items()} for k, dims in by_cov_type.items()},
        "value_stats": {f"{k[0]}|{k[1]}": v for k, v in value_stats.items()},
    }


def analyze_iswl_prem():
    path = BASE / "PFSA Rates/iswl-prem.csv"
    segments = Counter()
    durations = set()
    ages = []
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader)
        ages = [h for h in header[1:] if h.strip()]
        rows = 0
        for row in reader:
            rows += 1
            label = row[0].strip()
            parts = label.split()
            if len(parts) >= 3:
                segments[f"{parts[0]} {parts[1]}"] += 1
                durations.add(parts[2])
    return {
        "file": str(path.relative_to(BASE)),
        "data_rows": rows,
        "age_columns": len(ages),
        "age_range": f"{ages[0]}-{ages[-1]}" if ages else "",
        "segment_keys": dict(segments),
        "duration_count": len(durations),
    }


def analyze_pcovr():
    path = BASE / "plan_analysis/source_data/coverage/PCOVR.csv"
    interest_cols = []
    iswl_rows = []
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        interest_cols = [
            c for c in cols
            if any(x in c.upper() for x in ["INT", "RATE", "GUAR", "EXP", "COI", "SURR", "PREM", "CASH", "LOAN"])
        ]
        for row in reader:
            cov = row.get("COVERAGE_ID", "").strip()
            if cov in ISWL_COV:
                iswl_rows.append({c: row.get(c, "") for c in ["COVERAGE_ID", "DESCRIPTION", "PLAN_TYPE", "PRODUCT_TYPE"] + interest_cols[:20]})
    return {"file": str(path.relative_to(BASE)), "interest_cols": interest_cols, "iswl_rows": iswl_rows}


def scan_all_type_codes():
    """All TYPE_CODE values in rate files for ISWL and globally."""
    rt_path = BASE / "plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv"
    pa_path = BASE / "plan_analysis/source_data/rates/PAAGERAT_AttainedAge_Rates_Extract_20260428.csv"
    rt_global = Counter()
    rt_iswl = Counter()
    pa_global = Counter()
    pa_iswl = Counter()
    coi_like = {"COI", "GCOI", "NC", "U6", "SC", "SUR", "ISSC", "EXP", "GP", "PR", "CV", "NP", "RV", "DB", "DV"}

    with open(rt_path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            tc = row.get("TYPE_CODE", "").strip()
            rt_global[tc] += 1
            if row.get("COVERAGE_ID", "").strip() in ISWL_COV:
                rt_iswl[tc] += 1

    with open(pa_path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            tc = row.get("TYPE_CODE", "").strip()
            pa_global[tc] += 1
            if row.get("COVERAGE_ID", "").strip() in ISWL_COV:
                pa_iswl[tc] += 1

    return {
        "rate_table_global_types": dict(rt_global.most_common(30)),
        "rate_table_iswl_types": dict(rt_iswl.most_common()),
        "paagerat_global_types": dict(pa_global.most_common(30)),
        "paagerat_iswl_types": dict(pa_iswl.most_common()),
        "coi_like_in_iswl_rt": {k: rt_iswl[k] for k in coi_like if rt_iswl[k]},
        "coi_like_in_iswl_pa": {k: pa_iswl[k] for k in coi_like if pa_iswl[k]},
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = {
        "rate_table": analyze_rate_table(),
        "paagerat": analyze_paagerat(),
        "iswl_prem": analyze_iswl_prem(),
        "pcovr": analyze_pcovr(),
        "type_code_scan": scan_all_type_codes(),
    }
    out_path = OUT / "_analysis_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(json.dumps(results, indent=2)[:8000])


if __name__ == "__main__":
    main()
