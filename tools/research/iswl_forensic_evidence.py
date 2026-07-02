#!/usr/bin/env python3
"""Generate reproducible forensic evidence JSON for ISWL audit — research only."""
import csv
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
OUT = BASE / "Issue_Log_Items" / "Issue_ISWL_Research" / "ISWL_Forensic_Evidence.json"

ISWL_COV = {
    "658 CEN I", "658 CEN SD", "659 CEN II", "659 CEN SR", "659 CEN SD",
    "659 SR GD", "669 SR GD", "679 CEN SD",
}
ISWL_MPLAN = {
    "1658C1", "1658CS", "1659C2", "1659CR", "1659CS", "1659SR", "1669SR", "1679CS",
}


def count_lines(path):
    with open(path, "rb") as f:
        return sum(1 for _ in f)


def rate_table_evidence():
    path = BASE / "plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv"
    total = iswl = 0
    by_cov_type = Counter()
    samples = defaultdict(list)
    pr_iswl = 0
    sc_like = Counter()

    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        cols = [c.strip() for c in reader.fieldnames]
        col_map = {c.strip(): c for c in reader.fieldnames}
        for row in reader:
            total += 1
            cov = row[col_map["COVERAGE_ID"]].strip()
            tc = row[col_map["TYPE_CODE"]].strip()
            if tc in ("SC", "SUR", "ISSC", "EXP", "GCOI", "COI"):
                sc_like[tc] += 1
            if cov not in ISWL_COV:
                continue
            iswl += 1
            by_cov_type[(cov, tc)] += 1
            if tc == "PR":
                pr_iswl += 1
            key = (cov, tc)
            if len(samples[key]) < 3:
                samples[key].append({
                    "COVERAGE_ID": cov,
                    "TYPE_CODE": tc,
                    "AGE": row[col_map.get("AGE", "AGE")].strip() if "AGE" in col_map else "",
                    "SEX": row[col_map["SEX"]].strip(),
                    "BAND": row[col_map["BAND"]].strip(),
                    "UNDERWRITING_CLASS": row[col_map["UNDERWRITING_CLASS"]].strip(),
                    "DURATION": row[col_map["DURATION"]].strip(),
                    "VALUE": row[col_map.get("VALUE", "VALUE")].strip() if "VALUE" in col_map else "",
                })

    cv_total = sum(v for (c, t), v in by_cov_type.items() if t == "CV")
    return {
        "path": str(path.relative_to(BASE)),
        "file_rows_including_header": count_lines(path),
        "data_rows_total": total,
        "iswl_data_rows": iswl,
        "columns": cols,
        "iswl_pr_rows": pr_iswl,
        "global_sc_like_type_counts": dict(sc_like),
        "iswl_type_counts": {f"{c}|{t}": n for (c, t), n in sorted(by_cov_type.items(), key=lambda x: -x[1])},
        "iswl_cv_row_total": cv_total,
        "samples": {f"{k[0]}|{k[1]}": v for k, v in samples.items() if k[1] in ("CV", "NP", "PR", "TP", "TX")},
    }


def paagerat_evidence():
    path = BASE / "plan_analysis/source_data/rates/PAAGERAT_AttainedAge_Rates_Extract_20260428.csv"
    total = iswl = 0
    by_cov_type = Counter()
    samples = defaultdict(list)
    pr_iswl = 0
    sc_like = Counter()
    seq_col = None

    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        cols = [c.strip() for c in reader.fieldnames]
        col_map = {c.strip(): c for c in reader.fieldnames}
        seq_col = col_map.get("SEQ") or [c for c in reader.fieldnames if "SEQ" in c and "RECORD" not in c][0]
        for row in reader:
            total += 1
            cov = row[col_map["COVERAGE_ID"]].strip()
            tc = row[col_map["TYPE_CODE"]].strip()
            if tc in ("SC", "SUR", "ISSC", "EXP", "GCOI", "COI"):
                sc_like[tc] += 1
            if cov not in ISWL_COV:
                continue
            iswl += 1
            by_cov_type[(cov, tc)] += 1
            if tc == "PR":
                pr_iswl += 1
            key = (cov, tc)
            if len(samples[key]) < 3 and tc in ("NC", "U6", "BP", "PR", "NF"):
                samples[key].append({
                    "COVERAGE_ID": cov,
                    "TYPE_CODE": tc,
                    "SEX": row[col_map["SEX"]].strip(),
                    "BAND": row[col_map["BAND"]].strip(),
                    "UWCLS": row[col_map["UWCLS"]].strip(),
                    "SEQ": row[seq_col].strip(),
                    "VALUE_INFO": row[[c for c in reader.fieldnames if "VALUE_INFO" in c][0]].strip(),
                    "VALUE_FLOAT": row[[c for c in reader.fieldnames if "VALUE_FLOAT" in c][0]].strip(),
                })

    return {
        "path": str(path.relative_to(BASE)),
        "file_rows_including_header": count_lines(path),
        "data_rows_total": total,
        "iswl_data_rows": iswl,
        "columns": cols,
        "iswl_pr_rows": pr_iswl,
        "global_sc_like_type_counts": dict(sc_like),
        "iswl_type_counts": {f"{c}|{t}": n for (c, t), n in sorted(by_cov_type.items(), key=lambda x: -x[1])},
        "samples": {f"{k[0]}|{k[1]}": v for k, v in samples.items()},
    }


def cso_evidence():
    path = BASE / "plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv"
    rows = []
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            plan = row.get("qla_plan_code", "").strip()
            cov = row.get("lifepro_coverage_id", "").strip()
            if plan in ISWL_MPLAN or cov in ISWL_COV:
                rows.append({
                    "lifepro_coverage_id": cov,
                    "qla_plan_code": plan,
                    "qla_plan_description": row.get("qla_plan_description", ""),
                    "nfo_interest_source": row.get("nfo_interest_source", ""),
                    "nfo_interest_code": row.get("nfo_interest_code", ""),
                })
    return {"path": str(path.relative_to(BASE)), "iswl_rows": rows}


def iswl_prem_evidence():
    path = BASE / "PFSA Rates/iswl-prem.csv"
    rows = 0
    segments = Counter()
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            rows += 1
            parts = row[0].strip().split()
            if len(parts) >= 2:
                segments[f"{parts[0]} {parts[1]}"] += 1
    return {
        "path": str(path.relative_to(BASE)),
        "data_rows": rows,
        "age_columns": len(header) - 1,
        "header_first_last_age": [header[1], header[-1]] if len(header) > 1 else [],
        "segment_row_counts": dict(segments),
        "sample_row_1": open(path, encoding="utf-8-sig").readline().strip(),
        "sample_row_2": open(path, encoding="utf-8-sig").readlines()[1].strip()[:200],
    }


def pfsa_exclude_evidence():
    path = BASE / "PFSA Rates/reconciliation/plan_csv_mapping_DRAFT.csv"
    hits = []
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            if "iswl" in str(row).lower():
                hits.append(dict(row))
    return {"path": str(path.relative_to(BASE)), "iswl_related_rows": hits}


def negative_search_type_codes():
    """Scan both rate files for surrender/expense-like TYPE_CODE on ISWL coverages."""
    results = {"rate_table": {}, "paagerat": {}}
    terms = ["SC", "SUR", "ISSC", "EXP", "GCOI", "COI", "GP"]
    for label, rel in [("rate_table", "plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv"),
                       ("paagerat", "plan_analysis/source_data/rates/PAAGERAT_AttainedAge_Rates_Extract_20260428.csv")]:
        path = BASE / rel
        counts = Counter()
        iswl_counts = Counter()
        with open(path, newline="", encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                tc = row.get("TYPE_CODE", row.get(list(row.keys())[1], "")).strip()
                cov = row.get("COVERAGE_ID", "").strip()
                if tc in terms:
                    counts[tc] += 1
                    if cov in ISWL_COV:
                        iswl_counts[tc] += 1
        results[label] = {"global_term_counts": dict(counts), "iswl_term_counts": dict(iswl_counts)}
    return results


def source_presence():
    checks = [
        "QLA_Migration/Source",
        "plan_analysis/source_data/reference_dbf",
    ]
    return {p: {"exists": (BASE / p).exists(), "is_dir": (BASE / p).is_dir() if (BASE / p).exists() else False} for p in checks}


def main():
    evidence = {
        "generated_at": "2026-06-28",
        "repo_root": str(BASE),
        "source_presence": source_presence(),
        "rate_table": rate_table_evidence(),
        "paagerat": paagerat_evidence(),
        "cso_crosswalk": cso_evidence(),
        "iswl_prem": iswl_prem_evidence(),
        "pfsa_exclude": pfsa_exclude_evidence(),
        "negative_search_type_codes": negative_search_type_codes(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
