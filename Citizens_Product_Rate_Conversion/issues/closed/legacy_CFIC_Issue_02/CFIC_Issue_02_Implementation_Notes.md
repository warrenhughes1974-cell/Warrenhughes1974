# CFIC Issue #02 — PDF Rate Sheet Extract → QLAdmin

**Track:** Standalone CFIC pipeline (not Warren `app.py`)  
**Source:** `CFIC_Rates/docs/*.pdf` (scanned rate sheets)  
**Pilot:** PermaLife 7 `P7MN` adult from `CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf`

## Pipeline

```
docs PDF  →  extract_cfic_pdf_rates.py  →  extracted_pdf_rates/staging/
                                        →  validate_cfic_pdf_permalife7.py  (vs Access CSV)
                                        →  emit_cfic_pdf_rates.py  →  output/rates/quikgps.csv + quikplgp.csv
```

## Setup

```powershell
pip install -r CFIC_Rates/Issue_Log/CFIC_Issue_02/requirements-cfic-pdf.txt
```

## Run (pilot)

```powershell
# 1. Extract P7MN adult sheet (page 4)
python CFIC_Rates/Issue_Log/CFIC_Issue_02/scripts/extract_cfic_pdf_rates.py --plans P7MN

# 2. Validate vs Access PermaLife7AdultBefore.csv
python CFIC_Rates/Issue_Log/CFIC_Issue_02/scripts/validate_cfic_pdf_permalife7.py --plan P7MN

# 3. Emit QLAdmin gross premium tables
python CFIC_Rates/Issue_Log/CFIC_Issue_02/scripts/emit_cfic_pdf_rates.py --plan P7MN
```

## All PermaLife 7 single-table sheets

```powershell
python CFIC_Rates/Issue_Log/CFIC_Issue_02/scripts/extract_cfic_pdf_rates.py --all-permalife7
```

## Output locations

| Stage | Path |
|-------|------|
| Staging | `CFIC_Rates/extracted_pdf_rates/staging/{PLAN}/` |
| QLAdmin CSV | `CFIC_Rates/output/rates/quikgps.csv`, `quikplgp.csv` |
| Validation | `CFIC_Rates/Issue_Log/CFIC_Issue_02/evidence/cfic_issue02_pdf_validation.csv` |

## Phase 2 (not built yet)

- Juvenile dual-table layout (pages 1–2)
- Quest I / term sheets from same PDF
- `QuikCvs` / `QuikNps` emit from illustration columns
- QuikPlGp assumption values (OBQ-2)

## Related

- Plan inventory: `CFIC_Rates/docs/plan_rate_inventory.csv`
- CFIC Issue #01: green-sheet full-duration extract
- Scope: `CFIC_Issue_01_Scope_Decisions.md` (SD-1 standalone)
