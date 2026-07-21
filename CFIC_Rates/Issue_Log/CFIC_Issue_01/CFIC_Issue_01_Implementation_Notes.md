# CFIC Issue #01 — Implementation Notes (Wave 1)

**Issue:** CFIC #01 — Green-Sheet NF / Reserve Rate Extraction  
**Framework stage:** Development (Wave 1)  
**Date:** 2026-07-11  
**Scope:** Standalone one-time extract — **no `app.py` changes** (SD-1 locked)

---

## What was built

| Artifact | Path |
|----------|------|
| Extract script | `scripts/extract_cfic_green_sheets.py` |
| P7 layout template | `scripts/cfic_green_sheet_template.py` |
| Validation script | `scripts/validate_cfic_issue01_p7mn_pilot.py` |
| OCR dependencies | `requirements-cfic-ocr.txt` |
| Staging output | `CFIC_Rates/extracted_green_sheets/staging/P7MN/{age}.csv` |

### Process flow

```
P7MN_CV.zip → render PDF 4x → green-bar suppress → column OCR (EasyOCR)
            → wide staging CSV (all 9 body columns + metadata)
```

---

## How to run

```powershell
pip install -r CFIC_Rates/Issue_Log/CFIC_Issue_01/requirements-cfic-ocr.txt

python CFIC_Rates/Issue_Log/CFIC_Issue_01/scripts/extract_cfic_green_sheets.py --ages 18,30,50

python CFIC_Rates/Issue_Log/CFIC_Issue_01/scripts/validate_cfic_issue01_p7mn_pilot.py --ages 18,30,50
```

**Runtime:** ~20 min per PDF page on CPU (EasyOCR). First run downloads OCR models.

---

## Wave 1 results (2026-07-11)

| Deliverable | Status |
|-------------|--------|
| Standalone extract pipeline | **Complete** |
| P7MN age 18 staging CSV | **Produced** (`98` rows = 2 pages × 49 durations) |
| P7MN ages 30, 50 | **Not run** (pending OCR accuracy fix) |
| Warren `app.py` / `QLA_Migration/` | **Untouched** |
| Access parity validation | **FAIL** — OCR accuracy below 99.5% gate |

### Validation (age 18 vs Access `PermaLife7AdultBefore.csv`, Male NS)

Evidence: `evidence/cfic_issue01_p7mn_validation.csv`

Pilot checkpoints did **not** match illustration columns at durations 10 and 20. Root cause: EasyOCR cell reads on green-bar scans are misaligned/noisy without Tesseract or Azure Document Intelligence.

---

## Files changed (CFIC only)

- `CFIC_Rates/Issue_Log/CFIC_Issue_01/scripts/extract_cfic_green_sheets.py` (new)
- `CFIC_Rates/Issue_Log/CFIC_Issue_01/scripts/cfic_green_sheet_template.py` (new)
- `CFIC_Rates/Issue_Log/CFIC_Issue_01/scripts/validate_cfic_issue01_p7mn_pilot.py` (new)
- `CFIC_Rates/Issue_Log/CFIC_Issue_01/requirements-cfic-ocr.txt` (new)
- `CFIC_Rates/extracted_green_sheets/staging/P7MN/18.csv` (generated)

**No changes:** `app.py`, `QLA_Migration/`, rulebooks, Warren Output.

---

## Recommended next steps (Wave 1 completion)

1. **Install Tesseract OCR** on the extract workstation (blocked in this session) OR use **Azure Document Intelligence** for table OCR.
2. Re-calibrate `cfic_green_sheet_template.py` row grid using anchor row at duration 10 (`cash_value=21` at y≈828 on 4x render).
3. Re-run ages 18, 30, 50; validation must pass ≥99.5% spot-check before Wave 2.
4. Do **not** emit `QuikCvs` until OBQ-1 + OBQ-2 cleared.

---

## Regression

Warren conversion blast radius: **zero** — all artifacts under `CFIC_Rates/`.
