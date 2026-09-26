# Issue #137 — Risk Review Report

**Issue:** #137 — Names-tab Modalized Annual Premium  
**Framework stage:** Risk Agent  
**Status:** **CONDITIONAL GO — Ready for Development** (after user approval)  
**Generated:** 2026-08-05  
**Agent/script:** Cursor Grok 4.5 · read-only Output/Source join (summary: `evidence/issue137_risk_impact_summary.json`)

**Status note:** Risk analysis only — no production code changes.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Implement surgical replacement of Issue #88 blank-ANN `ann_factor` (payments-per-year) with **modal-factor reverse-engineer**, mode- and bill-form-aware.

**Conditions:**

1. **Blank-ANN path only** — populated `ANN_PREM_PER_UNIT` (#26) must not change.  
2. **UAT** Names-tab on gold `9010722550C` (premium base ≈436; Mode Prem 40.11 unchanged).  
3. **Accept** Coverage Prem/Unit and QuikVal movement on ~1,257 blank-ANN rows (same `MPREM` field).  
4. Missing plan factor → keep today’s crude annualization + audit.

---

## 1. Current vs Proposed Mapping

| Field / path | Current | Proposed | Change? |
|--------------|---------|----------|---------|
| `MPREM` when ANN > 0 | ANN_PREM_PER_UNIT (#26) | unchanged | **No** |
| `MPREM` when ANN blank, units > 0 | `(MODE × {12,4,2,1}) / units` | `(MODE ÷ (factor%/100)) / units` | **Yes** |
| `MMODEPREM` | MODE_PREMIUM | unchanged | **No** |
| Factors / fees | #36 / #58 | unchanged | **No** |

---

## 2. Fields Untouched

| Target | Touch? |
|--------|--------|
| `quikmstr.MMODEPREM` | **No** |
| #26 ANN→MPREM | **No** |
| `MSEMI`/`MQTRL`/`MMTHD`/`MMTHB` | **No** (read) |
| `MANNLFEE` / modal fees | **No** |
| MPOLICY padding | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `app.py` / `QLA_Migration/app.py` ~8815–8844 | Blank-ANN interceptor (`ann_factor`) |
| `QLA_Migration/Mapping/Modal_Premium_Factors_By_Plan.csv` | Factor % by plan |
| `qla_core/modal_premium_factors.py` | Existing factor helpers (#21J/#36) |
| Issue #88 / #58 / #26 folders | Prior semantics |

---

## 4. Population / Impact (read-only)

Phase-1 `quikridr` ⋈ `quikmstr` ⋈ PPBEN ANN (20260731 Output):

| Metric | Count |
|--------|------:|
| Phase-1 rows | 5,083 |
| Populated ANN (must not change) | 2,613 |
| Blank ANN in scope | 2,077 |
| Blank ANN where proposed MPREM ≠ current | **1,257** |
| Blank ANN unchanged under new formula | 820 |

### Blank-ANN changes by `MMODE`

| Mode | Meaning | Rows |
|-----:|---------|-----:|
| 01 | Monthly | 824 |
| 03 | Quarterly | 228 |
| 06 | Semiannual | 110 |
| 12 | Annual | 95 |

Median |Δ annual base| among changers ≈ **$16.88**; max ≈ **$2,646** (large-face / large mode prem).

### Gold after-state (simulated)

| | Current | Proposed |
|--|--------:|---------:|
| MPREM | 9.6264 | ~8.7197 |
| MPREM×MUNIT | 481.32 | **435.98** |
| + MANNLFEE 25 | 506.32 | **~460.98** (if Names adds fee) |
| MMODEPREM | 40.11 | 40.11 |

Eric `9010367131C`: ANN populated → **out of scope / unchanged**.

---

## 5. Fallback Options

| Option | Pros | Cons | Recommend? |
|--------|------|------|------------|
| A. Blank-ANN modal-factor (fleet) | One rule; fixes Nancy; aligns LifePRO screen | Moves Prem/Unit + QuikVal on ~1.3k rows | **Yes** |
| B. ISWL-only blank-ANN | Smaller blast | Two rules; non-ISWL still wrong | No |
| C. Do nothing | No regression | Names Annl stays wrong | No |

---

## 6. Regression Surfaces

| Surface | Guard |
|---------|--------|
| #26 ANN path | Assert Eric / populated ANN MPREM byte-stable |
| #88 annual blank (×1) | Annual mode modal 100% ≈ crude ×1 |
| #36 factors | No writes to factor columns |
| #58 fees | No writes to M*FEE |
| MMODEPREM / #26 Mode Prem | Assert unchanged fleet-wide |
| QuikVal | Spot-check #88 anchor + Nancy after re-batch |

---

## 7. Recommended Development Task (surgical)

1. Twin bump `APP_VERSION` (`app.py` + `QLA_Migration/app.py`).  
2. In blank-ANN block only: resolve factor% from plan mapping + `BILLING_MODE` + `BILLING_FORM` (MTHD vs MTHB);  
   `annual_ppu = MODE_PREMIUM / (factor/100) / units` (annual factor=100).  
3. If factor missing/zero: keep existing crude `ann_factor` dict; count in convert log.  
4. Do not alter ANN>0 branch.  
5. Validator + re-batch Output; publish `Test_Validation/quikridr.csv`.

---

## 8. Validation / Regression Checklist

- [ ] Gold `9010722550C`: `MPREM × MUNIT` ≈ 435.98–436.00; `MMODEPREM` = 40.11  
- [ ] Eric `9010367131C` MPREM unchanged  
- [ ] Sample monthly PAC uses MMTHB  
- [ ] Sample quarterly / semi blank-ANN  
- [ ] Populated ANN cohort: 0 MPREM diffs vs pre-change snapshot  
- [ ] Factors / fees / MMODEPREM non-regression  
- [ ] Names-tab UAT (Annl / current mode)  
- [ ] QuikVal spot-check after reload  

---

## Tracking status recommendation

**Ready for Development** — awaiting explicit **Approved for Development**.
