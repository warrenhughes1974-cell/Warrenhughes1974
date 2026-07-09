"""Prove specific client-screen rate rows are absent from delivered extracts."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = Path(__file__).resolve().parent

RATE_TABLE = ROOT / "plan_analysis" / "source_data" / "rates" / "Rate_Table_Extract_20260427.csv"
PAAGERAT = ROOT / "plan_analysis" / "source_data" / "rates" / "PAAGERAT_AttainedAge_Rates_Extract_20260428.csv"
PCOVR = ROOT / "plan_analysis" / "source_data" / "coverage" / "PCOVR.csv"
PCOVRSGT = ROOT / "plan_analysis" / "source_data" / "coverage" / "PCOVRSGT.csv"

CHECKS = [
    {
        "item": "L01 screenshot NP",
        "lifepro_id": "L01 10Y",
        "type_code": "NP",
        "expected_plan": "5L0110",
        "why_it_matters": "Screenshot shows L01 10Y NP under L01 10Y LT; converter needs Rate_Table rows to load QuikNps.",
    },
    {
        "item": "L01 LT direct NP",
        "lifepro_id": "L01 10Y LT",
        "type_code": "NP",
        "expected_plan": "5L0110",
        "why_it_matters": "If the NP rows were delivered directly under L01 10Y LT, they could load to 5L0110.",
    },
    {
        "item": "L10 LP9595 any rate rows",
        "lifepro_id": "L10 LP9595",
        "type_code": "",
        "expected_plan": "",
        "why_it_matters": "Eric referenced L10 LP9595 as limited to NP/RV; converter needs rows for that ID to load it.",
    },
]


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def _count_csv(path: Path, coverage: str, type_code: str = ""):
    exact_any_type = 0
    exact_type = 0
    contains_id = 0
    type_counts = {}
    samples = []
    with path.open(encoding="utf-8-sig", errors="replace", newline="") as f:
        for row in csv.DictReader(f):
            cov = (row.get("COVERAGE_ID") or "").strip()
            typ = (row.get("TYPE_CODE") or "").strip()
            if coverage.upper() in cov.upper():
                contains_id += 1
            if cov == coverage:
                exact_any_type += 1
                type_counts[typ] = type_counts.get(typ, 0) + 1
                if not type_code or typ == type_code:
                    exact_type += 1
                    if len(samples) < 5:
                        samples.append(dict(row))
    return exact_any_type, exact_type, contains_id, type_counts, samples


def _pcovr_exact(coverage: str):
    rows = []
    with PCOVR.open(encoding="utf-8-sig", errors="replace", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("COVERAGE_ID") or "").strip() == coverage:
                rows.append(row)
    return rows


def _pcovrsgt_refs(coverage: str):
    rows = []
    with PCOVRSGT.open(encoding="utf-8-sig", errors="replace", newline="") as f:
        for row in csv.DictReader(f):
            owner = (row.get("COVERAGE_ID") or "").strip()
            seg = (row.get("SEGT_ID   ") or "").strip()
            if owner == coverage or seg == coverage:
                rows.append({
                    "coverage_id": owner,
                    "seq": (row.get("SEQ   ") or "").strip(),
                    "segment_id": seg,
                    "segment_flag": (row.get("SEGT_FLAG") or "").strip(),
                })
    return rows


def _raw_byte_count(path: Path, needle: str):
    data = path.read_bytes().upper()
    return data.count(needle.upper().encode("utf-8"))


def main() -> int:
    proof_rows = []
    sample_rows = []
    pcovrsgt_rows = []

    for check in CHECKS:
        coverage = check["lifepro_id"]
        type_code = check["type_code"]
        for source_name, path in [("Rate_Table", RATE_TABLE), ("PAAGERAT", PAAGERAT)]:
            exact_any, exact_type, contains_id, type_counts, samples = _count_csv(path, coverage, type_code)
            proof_rows.append({
                "item": check["item"],
                "source": source_name,
                "source_file": _rel(path),
                "lifepro_id": coverage,
                "type_code_checked": type_code or "(any)",
                "exact_coverage_rows_any_type": exact_any,
                "exact_coverage_rows_for_type": exact_type if type_code else exact_any,
                "substring_rows_containing_lifepro_id": contains_id,
                "raw_byte_occurrences_of_id": _raw_byte_count(path, coverage),
                "type_counts_for_exact_coverage": "; ".join(f"{k}:{v}" for k, v in sorted(type_counts.items())),
                "conclusion": "MISSING" if (exact_type if type_code else exact_any) == 0 else "FOUND",
                "why_it_matters": check["why_it_matters"],
            })
            for sample in samples:
                sample_rows.append({
                    "item": check["item"],
                    "source": source_name,
                    **sample,
                })

        pcovr_rows = _pcovr_exact(coverage)
        proof_rows.append({
            "item": check["item"],
            "source": "PCOVR",
            "source_file": _rel(PCOVR),
            "lifepro_id": coverage,
            "type_code_checked": "(coverage setup)",
            "exact_coverage_rows_any_type": len(pcovr_rows),
            "exact_coverage_rows_for_type": len(pcovr_rows),
            "substring_rows_containing_lifepro_id": len(pcovr_rows),
            "raw_byte_occurrences_of_id": _raw_byte_count(PCOVR, coverage),
            "type_counts_for_exact_coverage": "",
            "conclusion": "MISSING" if not pcovr_rows else "FOUND",
            "why_it_matters": "Shows whether the ID exists as a delivered LifePRO coverage row.",
        })

        refs = _pcovrsgt_refs(coverage)
        for ref in refs:
            pcovrsgt_rows.append({"item": check["item"], "lifepro_id": coverage, **ref})

    proof_csv = OUT_DIR / "missing_source_proof.csv"
    sample_csv = OUT_DIR / "found_sample_rows_if_any.csv"
    pcovrsgt_csv = OUT_DIR / "pcovrsgt_references.csv"
    md = OUT_DIR / "missing_source_proof_summary.md"

    with proof_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(proof_rows[0].keys()))
        w.writeheader()
        w.writerows(proof_rows)

    if sample_rows:
        with sample_csv.open("w", newline="", encoding="utf-8") as f:
            fields = sorted({k for row in sample_rows for k in row})
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(sample_rows)

    with pcovrsgt_csv.open("w", newline="", encoding="utf-8") as f:
        fields = ["item", "lifepro_id", "coverage_id", "seq", "segment_id", "segment_flag"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(pcovrsgt_rows)

    lines = [
        "# Missing Source Proof Summary",
        "",
        "This proof searches the delivered source files for the exact IDs/rate types raised by the client.",
        "",
        "## What These Files Are",
        "",
        "- `Rate_Table_Extract_20260427.csv`: the LifePRO age/duration rate-value extract. "
        "This is where the converter expects rate rows such as CV, NP, RV, NF, DB, and similar duration-based factors.",
        "- `PAAGERAT_AttainedAge_Rates_Extract_20260428.csv`: the LifePRO attained-age rate-value extract. "
        "This is where the converter expects attained-age rows such as PR gross premiums and other scalar attained-age rates.",
        "- `PCOVR.csv`: the LifePRO coverage setup extract. This tells us whether a coverage ID exists as a delivered product/coverage row.",
        "- `PCOVRSGT.csv`: the LifePRO coverage-to-segment setup extract. This can show that one product points to another segment ID, "
        "but it does not contain the actual rate values.",
        "",
        "## Search Logic Used",
        "",
        "For each client-raised ID, the proof checks:",
        "",
        "1. Exact `COVERAGE_ID` match in `Rate_Table`.",
        "2. Exact `COVERAGE_ID` match and exact `TYPE_CODE` where a specific rate type is required.",
        "3. Exact `COVERAGE_ID` match in `PAAGERAT`.",
        "4. Exact coverage-row existence in `PCOVR`.",
        "5. Setup references in `PCOVRSGT` where the ID appears as either a coverage or segment.",
        "6. Raw byte occurrences of the ID in the delivered files, so the proof is not dependent on CSV parsing only.",
        "",
        "## Files Searched",
        "",
        f"- `{_rel(RATE_TABLE)}`",
        f"- `{_rel(PAAGERAT)}`",
        f"- `{_rel(PCOVR)}`",
        f"- `{_rel(PCOVRSGT)}`",
        "",
        "## Conclusions",
        "",
    ]
    for row in proof_rows:
        if row["source"] in {"Rate_Table", "PAAGERAT"}:
            lines.append(
                f"- `{row['lifepro_id']}` `{row['type_code_checked']}` in `{row['source_file']}`: "
                f"{row['conclusion']} (exact rows={row['exact_coverage_rows_for_type']}, "
                f"raw byte ID occurrences={row['raw_byte_occurrences_of_id']})."
            )
    lines.extend([
        "",
        "## Plain-English Explanation",
        "",
        "The converter can only load rows that are present in the delivered extract files. "
        "`PCOVRSGT` can show that a product points to a segment, but the actual rate values still "
        "must exist in `Rate_Table` or `PAAGERAT`. For the listed client gaps, those rate-value rows "
        "are not present in the delivered extracts.",
        "",
        "## Re-run Command",
        "",
        "```powershell",
        r'python "Issue_Log_Items\Issue_Rates_Inheritance_Validation\client_l10_l01_followup\source_gap_proof\prove_missing_l01_l10_rows.py"',
        "```",
    ])
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {proof_csv}")
    print(f"Wrote {pcovrsgt_csv}")
    print(f"Wrote {md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
