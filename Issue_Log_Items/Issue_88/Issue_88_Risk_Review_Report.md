# Issue #88 — Risk Review Report

**Issue:** #88 — Blank `ANN_PREM_PER_UNIT` fallback loads full `MODE_PREMIUM` into Prem/Unit  
**Framework stage:** Risk Agent  
**Status:** **Conditional Go — Ready for Development** (after user approval)  
**Fallback simulated:** `MODE_PREMIUM / units` (raw) + mode semantics analysis  
**Generated:** 2026-07-21  
**Agent/script:** Cursor Grok 4.5 · `QLA_Migration/_risk_review_issue88_mprem_unit_fallback.py`

**Status note:** Risk analysis only — no production code changes.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Fix the blank-ANN fallback so Prem/Unit is never the full phase modal premium when units > 1; Development must **annualize by billing mode before ÷ units** (not raw `MODE_PREMIUM / units` for all modes).

Rationale: Anchor and ISWL valuation blow-ups are real and fixed by ÷ units on annual (mode 12). Raw ÷ units alone is **wrong for monthly/quarterly/semi** because `MPREM` is defined as **annual** premium per unit.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| `quikridr.MPREM` when ANN ≠ 0 | `ANN_PREM_PER_UNIT` (#26) | unchanged | **No** |
| `quikridr.MPREM` when ANN blank/zero | raw `MODE_PREMIUM` (total) | `(MODE_PREMIUM × annualize(mode)) / NUMBER_OF_UNITS` | **Yes** |
| `quikridr.MPREM` when units ≤ 0 | today: MODE_PREMIUM | leave blank/zero (do not divide) | **Yes** (edge) |
| `quikmstr.MMODEPREM` | PPOLC.MODE_PREMIUM | unchanged | **No** |

### Annualize(mode) for LifePRO `BILLING_MODE`

| BILLING_MODE | Meaning (this book) | Factor |
|-------------:|---------------------|-------:|
| 12 | Annual | ×1 |
| 6 | Semi-annual | ×2 |
| 3 | Quarterly | ×4 |
| 1 | Monthly | ×12 |

Evidence: PPOLC samples — mode 12 MODE≈ANNUAL; mode 1 MODE×12≈ANNUAL; mode 6 MODE×2≈ANNUAL.

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| `quikmstr.MMODEPREM` | PPOLC.MODE_PREMIUM | **No** |
| `quikridr.MUNIT` / `MVPU` | existing | **No** |
| `quikridr` M*FEE (#58) | existing | **No** |
| MPOLICY padding (#25) | existing | **No** |
| Populated ANN→MPREM (#26 primary) | existing | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `QLA_Migration/app.py` ~7483–7490 | Issue #26 blank → MODE_PREMIUM interceptor |
| `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv` | ANN_PREM_PER_UNIT → MPREM |
| `Issue_Log_Items/Issue_26/` | Prior field definition + mode_prem fallback choice |
| `docs/Valuation/analysis/iswl_premium_times_units_*.csv` | Valuation symptom population |

---

## 4. Population Analysis

Source: `PPBEN_PolicyBenefit_Extract_20260630` ⋈ crosswalk ⋈ `Output/quikridr.csv`  
Script: `_risk_review_issue88_mprem_unit_fallback.py`  
Simulation compared **current Output MPREM** vs **ANN if present else MODE_PREMIUM/units** (raw ÷ units).

| Metric | Count |
|--------|------:|
| Joined PPBEN↔quikridr rows | 6,934 |
| ANN_PREM_PER_UNIT populated | 3,775 |
| ANN blank/zero | 3,159 |
| Rows that would change under raw ÷ units | **1,850** |
| Rows unchanged | 5,084 |
| Blank ANN with units ≤ 0 | 0 (among joined blank rows with mode prem path) |
| No quikridr match (non-emit / UV etc.) | 4,764 |

### Changes by BILLING_MODE (raw ÷ units sim)

| Mode | Meaning | Rows that would change |
|-----:|---------|-----------------------:|
| 12 | Annual | 837 |
| 1 | Monthly | 714 |
| 3 | Quarterly | 203 |
| 6 | Semi | 96 |

### Blank ANN unit buckets (joined blanks)

| Units | Count |
|-------|------:|
| 1 | 58 |
| 1–25 | 2,798 |
| 25–100 | 299 |
| >100 | 4 |

---

## 5. Fallback Recommendation

| Option | Assessment |
|--------|------------|
| A. Keep MODE_PREMIUM total (#26 today) | **Reject** — causes Prem/Unit × units in valuation |
| B. Raw MODE_PREMIUM / units (all modes) | **Reject as sole rule** — understates annual PPU for mode 1/3/6 |
| C. `(MODE_PREMIUM × 12/mode) / units` | **Recommended** |
| D. Mode-12-only ÷ units | Acceptable phased scope; leaves monthly/Q/S wrong until follow-up |

**Recommended fallback:** Option **C**.  
When ANN blank/zero and `NUMBER_OF_UNITS` > 0:  
`MPREM = MODE_PREMIUM * (12 / BILLING_MODE) / NUMBER_OF_UNITS`  
with BILLING_MODE from PPOLC (cache lookup during quikridr emit).  
If BILLING_MODE missing/invalid: Risk default = treat as annual (factor 1) and log count.

**Note:** Quarterly may not match PPOLC `ANNUAL_PREMIUM` exactly (modal factors). Frequency annualization (×4) is still the correct semantic for “annual per unit” vs leaving full modal total in Prem/Unit.

---

## 6. Trace Policies

| Policy | Phase | ANN | Units | Mode | Current MPREM | Proposed (raw ÷u) | Proposed (ann. ÷u) | Pass? |
|--------|------:|----:|------:|-----:|--------------:|------------------:|-------------------:|-------|
| `010779727C` | 1 | 0 | 500 | 12 | 2,930.75 | **5.8615** | **5.8615** | Yes — fixes 1,465,400 val |
| `010779727C` | 2 | 0.25 | 500 | 12 | 0.25 | 0.25 | 0.25 | Yes — ANN path |
| `010779727C` | 4 | -169.5 | 1 | 12 | -169.5 | -169.5 | -169.5 | Yes — ANN path |
| `010310404C` | 1 | 13.20 | 15 | — | 13.20 | 13.20 | 13.20 | Yes — #26 primary |
| `010331768C` | 1 | 10.96 | 15 | — | 10.96 | 10.96 | 10.96 | Yes |
| `010367131C` | 1 | 9.12 | 5.434 | — | 9.12 | 9.12 | 9.12 | Yes |
| `010736035C` | 1 | 0 | 125 | 1 | 211.49 | 1.6919 | **~20.30** (×12) | Need ann. rule |

---

## 7. Top Largest Changes (raw ÷ units vs current)

| Policy | Units | Mode | Before | After (raw) | Delta |
|--------|------:|-----:|-------:|------------:|------:|
| `010897303C` | 14.16 | 12 | 6887.88 | 486.38 | -6401.50 |
| `010826903C` | 21.93 | 12 | 5000.00 | 228.05 | -4771.95 |
| `010779727C` | 500 | 12 | 2930.75 | 5.86 | -2924.89 |
| `011072813C` | 100 | 12 | 2794.00 | 27.94 | -2766.06 |

Full list: `Issue_Log_Items/Issue_88/evidence/issue88_mprem_simulated_changes.csv` (1,850 rows).

These large drops are **intentional corrections** (total → per-unit), not collateral drift.

---

## 8. Material Calculation Impact

| Impact | Intentional? |
|--------|--------------|
| Coverage Prem/Unit drops from full modal to per-unit rate | **Yes** — semantic fix |
| Valuation Mode Prem stops ≈ ModePrem × units | **Yes** — symptom fix |
| Policy header Mode Prem / `MMODEPREM` | **No change** |
| #26 rows with populated ANN | **No change** |
| Monthly blank-ANN if Dev uses raw ÷ units only | **Bad** — blocked by Conditional Go annualize rule |

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserve** — untouched |
| Issue #26 ANN→MPREM when populated | **Preserve** |
| Issue #26 blank fallback | **Replace** (this issue) |
| `MMODEPREM` | **Preserve** |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] `010779727C` ph1: MPREM ≈ 5.8615; MMODEPREM/Mode Prem still 2,930.75
- [ ] `010779727C` ph2/ph3/ph4: ANN-driven MPREM unchanged
- [ ] #26 traces `010310404C` / `010331768C` / `010367131C` ph1 unchanged
- [ ] Sample monthly blank-ANN (mode 1): MPREM ≈ (MODE_PREMIUM×12)/units, not MODE/units
- [ ] Sample semi (mode 6): MPREM ≈ (MODE×2)/units
- [ ] 1-unit blank ANN: numeric MPREM ≈ prior (annualized total / 1)
- [ ] Row count `quikridr` stable; no MPOLICY width change
- [ ] After reload: valuation Mode Prem not equal to prior Prem/Unit × units for anchor
- [ ] Publish `Output/Test_Validation/quikridr.csv` on PASS; **no commit** unless user asks

---

## 11. Recommended Development Agent Task

**Model:** Composer 2.5 (locked). User must say `Approved for Development`.

1. In `app.py` Issue #26 interceptor (`quikridr`/`MPREM`):  
   - If ANN ≠ 0 → keep current (#26).  
   - If ANN blank/zero and units > 0:  
     `val = MODE_PREMIUM * ann_factor(BILLING_MODE) / NUMBER_OF_UNITS`  
     with `ann_factor` = `{12:1, 6:2, 3:4, 1:12}` default 1 if unknown.  
   - BILLING_MODE via PPOLC cache (mirror `_policy_fee_map` pattern) — not on PPBEN row.  
   - If units ≤ 0: do not emit full MODE_PREMIUM as Prem/Unit; emit blank/zero.  
2. Update comment on `Sync_Rulebook_quikridr.csv` MPREM row.  
3. Bump `APP_VERSION` in **both** root `app.py` and `QLA_Migration/app.py`.  
4. Add validator `tools/validators/validate_issue88_mprem_unit_fallback.py`.  
5. Re-batch `quikridr` for user Validation; **do not commit**.

**Do NOT change:** `MMODEPREM`, fees, units, #25 padding, plan VarGP.

---

## Appendix

- Simulation changes: `Issue_Log_Items/Issue_88/evidence/issue88_mprem_simulated_changes.csv`
- Summary: `Issue_Log_Items/Issue_88/evidence/issue88_risk_sim_summary.txt`
- Scripts: `QLA_Migration/_risk_review_issue88_mprem_unit_fallback.py`, `_risk_issue88_mode_check.py`
- Planning: `Issue_88_Planning_Report.md`
- Gate: `Issue_88_Dependency_Gate.md` PASS
