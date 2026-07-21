"""Build CFIC docs plan/rate inventory with QLAdmin plan mapping."""
from __future__ import annotations

import csv
import re
from pathlib import Path

try:
    import openpyxl
except ImportError as exc:  # pragma: no cover
    raise SystemExit("pip install openpyxl") from exc

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CROSSWALK = ROOT / "Citizens_Plan_Crosswak.xlsx"
OUT_CSV = DOCS / "plan_rate_inventory.csv"
OUT_MD = DOCS / "plan_rate_source_index.md"

# source_pdf, page, cfic_plan, product_family, rate_types, segment, notes
ROWS = [
    # Current New Business
    ("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 1, "P7FN", "PermaLife 7 Juvenile", "Gross Premium;Cash Value;Paid-Up", "Female Nonsmoker ages 0-17", "Also HPFN (2017 CSO)"),
    ("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 1, "P7MN", "PermaLife 7 Juvenile", "Gross Premium;Cash Value;Paid-Up", "Male Nonsmoker ages 0-17", "Also HPMN"),
    ("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 2, "P7FS", "PermaLife 7 Juvenile", "Gross Premium;Cash Value;Paid-Up", "Female Smoker ages 0-17", "Also HPFS"),
    ("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 2, "P7MS", "PermaLife 7 Juvenile", "Gross Premium;Cash Value;Paid-Up", "Male Smoker ages 0-17", "Also HPMS"),
    ("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 3, "P7FN", "PermaLife 7 Adult", "Gross Premium;Cash Value;Paid-Up", "Female Nonsmoker ages 18-70", "Also HPFN"),
    ("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 4, "P7MN", "PermaLife 7 Adult", "Gross Premium;Cash Value;Paid-Up", "Male Nonsmoker ages 18-70", "Also HPMN"),
    ("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 5, "P7FS", "PermaLife 7 Adult", "Gross Premium;Cash Value;Paid-Up", "Female Smoker ages 18-70", "Also HPFS"),
    ("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 5, "P7MS", "PermaLife 7 Adult", "Gross Premium;Cash Value;Paid-Up", "Male Smoker ages 18-70", "Also HPMS"),
    ("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 6, "HRWG", "Quest I", "Gross Premium", "Whole Life column ages 0-75", "Maps from RW8G; HR 2017 CSO"),
    ("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 6, "HR2G", "Quest I", "Gross Premium", "Paid-up at 65 column ages 0-55", "Maps from R28G"),
    ("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 6, "HR6G", "Quest I", "Gross Premium", "20-pay column ages 0-65", "Maps from R68G"),
    ("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 7, "QIII", "Quest II & III", "Gross Premium", "Whole life ages 0-75", "Graded death benefit plan"),
    ("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 8, "X58F", "5-Year Term", "Gross Premium", "Female base ages 15-64", "Renewable/convertible to 65"),
    ("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 9, "X58M", "5-Year Term", "Gross Premium", "Male base ages 15-64", ""),
    ("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 10, "X18M", "10-Year Term", "Gross Premium", "Male base ages 15-64", ""),
    ("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 11, "X18F", "10-Year Term", "Gross Premium", "Female base ages 15-64", "Verify page — likely female 10yr"),
    ("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 12, "XR1F", "10-Year Term Rider", "Gross Premium", "Female rider ages 15-64", "Renewal only ages 56-64"),
    ("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 12, "XR1M", "10-Year Term Rider", "Gross Premium", "Male rider ages 15-64", ""),
    ("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 13, "XR5F", "5-Year Term Rider", "Gross Premium", "Female rider ages 15-64", ""),
    ("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 13, "XR5M", "5-Year Term Rider", "Gross Premium", "Male rider ages 15-64", ""),
    # Quest / PermaLife index + Quest I sheet
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "RW8", "Whole Life", "Plan definition", "80 CSO whole life cash plan", "QL: 100RW8"),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "RW8G", "Whole Life", "Plan definition", "80 CSO; CV/loan/ETI; 8% loan", "QL: 10RW8G"),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "RW8A", "Whole Life", "Plan definition", "2006-2009 issue reserve adjustment", "QL: 10RW8A"),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "R28", "20-Pay Life", "Plan definition", "Premium payable 20 years", ""),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "R28G", "20-Pay Life", "Plan definition", "80 CSO; CV/loan/ETI", ""),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "R29G", "20-Pay Life", "Plan definition", "2001 CSO", ""),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "R68", "Pay to 65", "Plan definition", "Premium payable to age 65", ""),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "R68G", "Pay to 65", "Plan definition", "80 CSO", ""),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "R69G", "Pay to 65", "Plan definition", "2001 CSO", ""),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "HR2G", "Quest / 20-Pay", "Plan definition", "2017 CSO 20-pay", ""),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "HR6G", "Quest / Pay to 65", "Plan definition", "2017 CSO pay to 65", ""),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "HRWG", "Quest / Whole Life", "Plan definition", "2017 CSO whole life", ""),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "HPFN", "PermaLife / HP 2017", "Plan definition", "Female nonsmoker whole life", "QL: 10HPFN"),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "HPFS", "PermaLife / HP 2017", "Plan definition", "Female smoker", "QL: 10HPFS"),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "HPMN", "PermaLife / HP 2017", "Plan definition", "Male nonsmoker", "QL: 10HPMN"),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "HPMS", "PermaLife / HP 2017", "Plan definition", "Male smoker", "QL: 10HPMS"),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "P7FN", "PermaLife 7", "Plan definition", "Female nonsmoker; 80 CSO", "QL: 10P7FN"),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "P7FS", "PermaLife 7", "Plan definition", "Female smoker", "QL: 10P7FS"),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "P7MN", "PermaLife 7", "Plan definition", "Male nonsmoker", "QL: 10P7MN"),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "P7MS", "PermaLife 7", "Plan definition", "Male smoker", "QL: 10P7MS"),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "P8FN", "PermaLife 8", "Plan definition", "Female nonsmoker; 80 CSO", ""),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "P8FS", "PermaLife 8", "Plan definition", "Female smoker", ""),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "P8MN", "PermaLife 8", "Plan definition", "Male nonsmoker", ""),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "P8MS", "PermaLife 8", "Plan definition", "Male smoker", ""),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "P8FJ", "PermaLife 8 Juvenile", "Plan definition", "Female juvenile 0-17", ""),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "P8MJ", "PermaLife 8 Juvenile", "Plan definition", "Male juvenile 0-17", ""),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "P9FN", "PermaLife 9", "Plan definition", "Female nonsmoker; 2001 CSO", ""),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "P9FS", "PermaLife 9", "Plan definition", "Female smoker", ""),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "P9MN", "PermaLife 9", "Plan definition", "Male nonsmoker", ""),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 1, "P9MS", "PermaLife 9", "Plan definition", "Male smoker", ""),
    ("Quest_PermaLife_PlanCode_Rates.pdf", 2, "HRWG", "Quest I", "Gross Premium;Waiver", "WL / PdUp65 / 20-pay / WP", "Duplicate of CNB p6"),
    # Life plan codes
    ("Life_PlanCodes_Rates.pdf", 1, "RW8", "Whole Life", "Plan definition", "Whole life cash plan", ""),
    ("Life_PlanCodes_Rates.pdf", 1, "RW8G", "Whole Life", "Plan definition", "80 CSO", "QL: 10RW8G"),
    ("Life_PlanCodes_Rates.pdf", 1, "RW8A", "Whole Life", "Plan definition", "2006-2009 adjustment", "QL: 10RW8A"),
    ("Life_PlanCodes_Rates.pdf", 1, "R28", "20-Pay Life", "Plan definition", "", ""),
    ("Life_PlanCodes_Rates.pdf", 1, "R28G", "20-Pay Life", "Plan definition", "80 CSO", ""),
    ("Life_PlanCodes_Rates.pdf", 1, "RW1", "Family Whole Life", "Plan definition", "Single parent; 58 CSO", ""),
    ("Life_PlanCodes_Rates.pdf", 1, "RW18", "Family Whole Life", "Plan definition", "Single parent; 80 CSO", ""),
    ("Life_PlanCodes_Rates.pdf", 1, "RW2", "Family Whole Life", "Plan definition", "Both parents; 58 CSO", ""),
    ("Life_PlanCodes_Rates.pdf", 1, "RW28", "Family Whole Life", "Plan definition", "Both parents; 80 CSO", ""),
    ("Life_PlanCodes_Rates.pdf", 1, "RJ", "Joint Life", "Plan definition", "58 CSO; 4.8% loan", ""),
    ("Life_PlanCodes_Rates.pdf", 1, "T58F", "5-Year Term", "Plan definition", "Female; no CV/loan", ""),
    ("Life_PlanCodes_Rates.pdf", 1, "T58M", "5-Year Term", "Plan definition", "Male", ""),
    ("Life_PlanCodes_Rates.pdf", 1, "T18F", "10-Year Term", "Plan definition", "Female", ""),
    ("Life_PlanCodes_Rates.pdf", 1, "T18M", "10-Year Term", "Plan definition", "Male", ""),
    ("Life_PlanCodes_Rates.pdf", 1, "TR5F", "5-Year Term Rider", "Plan definition", "Female rider", ""),
    ("Life_PlanCodes_Rates.pdf", 1, "TR5M", "5-Year Term Rider", "Plan definition", "Male rider", ""),
    ("Life_PlanCodes_Rates.pdf", 1, "TR1F", "10-Year Term Rider", "Plan definition", "Female rider", ""),
    ("Life_PlanCodes_Rates.pdf", 1, "TR1M", "10-Year Term Rider", "Plan definition", "Male rider", ""),
    ("Life_PlanCodes_Rates.pdf", 1, "X58F", "5-Year Term", "Plan definition", "Female; 2000 CSO", ""),
    ("Life_PlanCodes_Rates.pdf", 1, "X58M", "5-Year Term", "Plan definition", "Male; 2000 CSO", ""),
    ("Life_PlanCodes_Rates.pdf", 1, "X18F", "10-Year Term", "Plan definition", "Female; 2000 CSO", ""),
    ("Life_PlanCodes_Rates.pdf", 1, "X18M", "10-Year Term", "Plan definition", "Male; 2000 CSO", ""),
    ("Life_PlanCodes_Rates.pdf", 2, "RW8", "Ordinary Life", "Gross Premium;Cash Value;Paid-Up", "Individual ages 0-65", "Handwritten RW8 IND"),
    ("Life_PlanCodes_Rates.pdf", 2, "RW8G", "Ordinary Life", "Gross Premium;Cash Value;Paid-Up", "Family ages 0-65", "Handwritten RW8G Family"),
    # Term Q-series
    ("Term_PlanCodes_Rates.pdf", 1, "Q1FN", "Term Life", "Plan definition", "10-year female nonsmoker", ""),
    ("Term_PlanCodes_Rates.pdf", 1, "Q1FS", "Term Life", "Plan definition", "10-year female smoker", ""),
    ("Term_PlanCodes_Rates.pdf", 1, "Q1MN", "Term Life", "Plan definition", "10-year male nonsmoker", ""),
    ("Term_PlanCodes_Rates.pdf", 1, "Q1MS", "Term Life", "Plan definition", "10-year male smoker", ""),
    ("Term_PlanCodes_Rates.pdf", 1, "Q2FN", "Term Life", "Plan definition", "20-year female nonsmoker", ""),
    ("Term_PlanCodes_Rates.pdf", 1, "Q2FS", "Term Life", "Plan definition", "20-year female smoker", ""),
    ("Term_PlanCodes_Rates.pdf", 1, "Q2MN", "Term Life", "Plan definition", "20-year male nonsmoker", ""),
    ("Term_PlanCodes_Rates.pdf", 1, "Q2MS", "Term Life", "Plan definition", "20-year male smoker", ""),
    ("Term_PlanCodes_Rates.pdf", 1, "Q3FN", "Term Life", "Plan definition", "30-year female nonsmoker", ""),
    ("Term_PlanCodes_Rates.pdf", 1, "Q3FS", "Term Life", "Plan definition", "30-year female smoker", ""),
    ("Term_PlanCodes_Rates.pdf", 1, "Q3MN", "Term Life", "Plan definition", "30-year male nonsmoker", ""),
    ("Term_PlanCodes_Rates.pdf", 1, "Q3MS", "Term Life", "Plan definition", "30-year male smoker", ""),
    # Drummond legacy
    ("Drummond_CFI_PlanCodes_Rates.pdf", 1, "FW5", "Merchandise/Service", "Plan definition", "58 CSO; pay to 100", "No QL crosswalk"),
    ("Drummond_CFI_PlanCodes_Rates.pdf", 1, "FW5C", "Merchandise/Service", "Plan definition", "", ""),
    ("Drummond_CFI_PlanCodes_Rates.pdf", 1, "F25", "Merchandise/Service", "Plan definition", "20-pay", ""),
    ("Drummond_CFI_PlanCodes_Rates.pdf", 1, "RW", "Whole Life", "Plan definition", "58 CSO legacy", "QL: 100RW8 family?"),
    ("Drummond_CFI_PlanCodes_Rates.pdf", 1, "RWC", "Whole Life", "Plan definition", "", ""),
    ("Drummond_CFI_PlanCodes_Rates.pdf", 1, "R2", "20-Pay Life", "Plan definition", "58 CSO", ""),
    ("Drummond_CFI_PlanCodes_Rates.pdf", 1, "R2G", "20-Pay Life", "Plan definition", "", ""),
    ("Drummond_CFI_PlanCodes_Rates.pdf", 1, "RJ", "Joint Life", "Plan definition", "4.8% loan", ""),
    ("Drummond_CFI_PlanCodes_Rates.pdf", 1, "RE1", "Endowment 65", "Plan definition", "", ""),
    ("Drummond_CFI_PlanCodes_Rates.pdf", 1, "RE2", "Youth Estate", "Plan definition", "", ""),
    ("Drummond_CFI_PlanCodes_Rates.pdf", 2, "ALL", "General", "Present value factors", "4.5% discount table", "Not plan-specific rates"),
    # Burial / merchandise
    ("BW_PlanCode_Rates.pdf", 1, "BW", "Burial / Merchandise", "Gross Premium", "Age-banded burial rates", "Non-reserve; no CV/loan"),
    ("BWB_971_PlanCode_Rates.pdf", 1, "971", "Burial / Merchandise", "Gross Premium", "Plan 971 modal factors", "BWB office 10; no QL crosswalk"),
]


def load_crosswalk() -> dict[str, dict]:
    wb = openpyxl.load_workbook(CROSSWALK, data_only=True)
    ws = wb.active
    lookup: dict[str, dict] = {}
    for lob, plan, suffix, ql in ws.iter_rows(min_row=2, values_only=True):
        if plan is None:
            continue
        group = str(plan).strip()
        ql_raw = "" if ql is None else str(ql).strip()
        lob_s = "" if lob is None else str(lob).strip()
        suffix_s = "" if suffix is None else str(suffix)
        for token in re.split(r",\s*", group):
            token = token.strip().upper()
            if token:
                lookup[token] = {
                    "cfic_plan_group": group,
                    "ql_plan_all": ql_raw,
                    "lob": lob_s,
                    "suffix": suffix_s,
                }
    return lookup


def resolve_ql_plan(code: str, lookup: dict[str, dict]) -> tuple[str, str]:
    code_u = code.upper()
    hit = lookup.get(code_u)
    if not hit:
        return "", "N"
    ql_all = hit["ql_plan_all"]
    if not ql_all:
        return "", "Y"
    parts = [p.strip() for p in ql_all.split(",") if p.strip()]
    # Prefer exact token match e.g. 10P7MN for P7MN
    for part in parts:
        if part.upper().endswith(code_u) or part.upper() == f"10{code_u}" or part.upper() == f"100{code_u}":
            return part, "Y"
    if len(parts) == 1:
        return parts[0], "Y"
    return ql_all, "Y"


def main() -> None:
    lookup = load_crosswalk()
    fields = [
        "source_pdf",
        "page",
        "cfic_plan_code",
        "ql_plan",
        "in_plan_crosswalk",
        "product_family",
        "rate_types_in_pdf",
        "segment",
        "notes",
        "source_path",
    ]
    out_rows = []
    for pdf, page, code, family, rates, segment, notes in ROWS:
        ql, in_xw = resolve_ql_plan(code, lookup)
        out_rows.append(
            {
                "source_pdf": pdf,
                "page": page,
                "cfic_plan_code": code,
                "ql_plan": ql,
                "in_plan_crosswalk": in_xw,
                "product_family": family,
                "rate_types_in_pdf": rates,
                "segment": segment,
                "notes": notes,
                "source_path": f"CFIC_Rates/docs/{pdf}",
            }
        )

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)

    # Markdown index grouped by PDF
    from collections import defaultdict

    by_pdf: dict[str, list] = defaultdict(list)
    for row in out_rows:
        by_pdf[row["source_pdf"]].append(row)

    lines = [
        "# CFIC Plan / Rate PDF Inventory",
        "",
        "Scanned rate sheets in `CFIC_Rates/docs/`. Mapped to QLAdmin plan codes via `Citizens_Plan_Crosswak.xlsx`.",
        "",
        "**Google Sheets:** import `plan_rate_inventory.csv`",
        "",
        "## PDF summary",
        "",
        "| PDF | Pages | Purpose |",
        "|-----|------:|---------|",
        "| CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf | 13 | **Active rate sheets** — PermaLife 7, Quest, term base + riders |",
        "| Quest_PermaLife_PlanCode_Rates.pdf | 6 | Plan code index + Quest I rates |",
        "| Life_PlanCodes_Rates.pdf | 7 | Plan definitions + RW8 ordinary life rates |",
        "| Term_PlanCodes_Rates.pdf | 2 | Q1/Q2/Q3 term plan code definitions |",
        "| Drummond_CFI_PlanCodes_Rates.pdf | 11 | Legacy Drummond plans (pre-1988) |",
        "| BW_PlanCode_Rates.pdf | 2 | Burial/merchandise BW plan |",
        "| BWB_971_PlanCode_Rates.pdf | 3 | Burial plan 971 (BWB office) |",
        "",
        "## QL plan mapping (in crosswalk)",
        "",
    ]
    mapped = [r for r in out_rows if r["ql_plan"]]
    unmapped = sorted({r["cfic_plan_code"] for r in out_rows if not r["ql_plan"]})
    lines.append(f"**{len(mapped)}** inventory rows with QL plan · **{len(unmapped)}** CFIC codes without crosswalk match")
    lines.append("")
    lines.append("### Mapped highlights")
    lines.append("")
    lines.append("| CFIC | QL Plan | Product | Source PDF |")
    lines.append("|------|---------|---------|------------|")
    seen = set()
    for r in out_rows:
        if not r["ql_plan"]:
            continue
        key = (r["cfic_plan_code"], r["ql_plan"])
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"| {r['cfic_plan_code']} | {r['ql_plan']} | {r['product_family']} | {r['source_pdf']} |")

    lines.extend(["", "### Not in crosswalk (legacy / burial / new codes)", ""])
    for code in unmapped:
        lines.append(f"- `{code}`")

    lines.extend(["", "## By source PDF", ""])
    for pdf, items in sorted(by_pdf.items()):
        lines.append(f"### {pdf}")
        lines.append("")
        for r in items:
            ql = r["ql_plan"] or "—"
            lines.append(
                f"- **p{r['page']}** `{r['cfic_plan_code']}` → **{ql}** — {r['segment']} ({r['rate_types_in_pdf']})"
            )
        lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(out_rows)} rows -> {OUT_CSV}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
