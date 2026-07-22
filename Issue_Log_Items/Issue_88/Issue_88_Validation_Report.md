# Issue #88 — Validation Report

**Issue:** #88 — Blank `ANN_PREM_PER_UNIT` fallback loads full `MODE_PREMIUM` into Prem/Unit  
**Framework stage:** Validation Agent (G5)  
**Engine version:** v58.23  
**Validation script:** `tools/validators/validate_issue88_mprem_unit_fallback.py`  
**Output directory:** `QLA_Migration/Output/`  
**Before snapshot:** N/A (rebatch applied to full Output; Risk sim CSV used for expected deltas)  
**Generated:** 2026-07-21  
**Model:** Cursor Grok 4.5 (locked)  
**Verdict:** **PASS**

> Note: An earlier draft in this folder addressed a different #88 topic (ISWL QuikIssc/Uint rates). This report is for the current tracking-sheet #88 (MPREM unit fallback). Rate-package evidence remains under `evidence/issue88_validation_checks.json` / related rate files and is out of scope for this verdict.

---

## Commands Run

```text
python tools/validators/validate_issue88_mprem_unit_fallback.py
# EXIT=0 — PASS Issue #88 MPREM unit fallback

# Spot checks (phases, billing modes, row counts, Test_Validation)
# stdout saved: Issue_Log_Items/Issue_88/evidence/issue88_mprem_validator_stdout.txt
```

---

## 1. Trace Policy Results

| Policy | Phase | Field | Expected | Actual | Result |
|--------|------:|-------|----------|--------|--------|
| `010779727C` | 1 | MPREM | ≈ 5.8615 | 5.8615 | **PASS** |
| `010779727C` | 1 | quikmstr.MMODEPREM | 2930.75 | 2930.75 | **PASS** |
| `010779727C` | 2 | MPREM (ANN path) | 0.25 | 0.25000 | **PASS** |
| `010779727C` | 3 | MPREM (ANN path) | 1.20 | 1.20000 | **PASS** |
| `010779727C` | 4 | MPREM (ANN path) | -169.5 | -169.50000 | **PASS** |
| `010310404C` | 1 | MPREM (#26) | 13.20 | 13.2 | **PASS** |
| `010331768C` | 1 | MPREM (#26) | 10.96 | 10.96 | **PASS** |
| `010367131C` | 1 | MPREM (#26) | 9.12 | 9.12 | **PASS** |
| `010736035C` | 1 | MPREM (monthly blank ANN) | ≈ 20.30 (MODE×12/units) | 20.30304 | **PASS** |
| `010718309C` | 1 | MPREM (mode 1) | 5.88 | 5.88 | **PASS** |
| `010732078C` | 1 | MPREM (mode 6) | 4.7352 | 4.7352 | **PASS** |
| `010725643C` | 1 | MPREM (mode 3) | 4.8704 | 4.8704 | **PASS** |
| `010390251C` | 1 | MPREM (mode 12) | 5.0 | 5.0 | **PASS** |

Joined population: **6,934** rows checked; **0** MPREM mismatches (>0.02).

---

## 2. Acceptance Criteria (from Risk §10)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | `010779727C` ph1 MPREM ≈ 5.8615; Mode Prem still 2,930.75 | **PASS** |
| 2 | `010779727C` ph2/ph3/ph4 ANN-driven MPREM unchanged | **PASS** |
| 3 | #26 traces `010310404C` / `010331768C` / `010367131C` unchanged | **PASS** |
| 4 | Monthly blank-ANN: MPREM ≈ (MODE×12)/units, not MODE/units | **PASS** (`010718309C`: 5.88 vs raw 0.49; `010736035C` ≈ 20.30) |
| 5 | Semi (mode 6): MPREM ≈ (MODE×2)/units | **PASS** (`010732078C`) |
| 6 | 1-unit blank ANN: MPREM ≈ annualized total / 1 | **N/A** — no joined blank-ANN row with units=1 in current extracts; covered by general 0-mismatch rule |
| 7 | Row count `quikridr` stable; no MPOLICY width regression on padded rows | **PASS** — 6,934 rows; 6,669 of 10-char MPOLICY (pre-existing shorter keys unchanged pattern) |
| 8 | After reload: valuation Mode Prem not Prem/Unit × units for anchor | **PASS** (user QLA re-run 2026-07-21 ~20:17) — Compare: Valx 3,085 / QLA 2,930 (was 1,465,400) |
| 9 | Publish `Output/Test_Validation/quikridr.csv` on PASS | **PASS** — TV present and byte-identical to full Output |

---

## 3. Source Alignment

| Check | Result |
|-------|--------|
| Populated ANN → MPREM | **PASS** (#26 traces + anchor ph2–4) |
| Blank/zero ANN → annualized MODE / units | **PASS** (0 mismatches / 6934) |
| Units ≤ 0 → not full MODE as Prem/Unit | **PASS** (validator allows blank; 0 mismatches) |

---

## 4. Untouched Fields Confirmed

| Field / table | Check | Result |
|---------------|-------|--------|
| `quikmstr.MMODEPREM` | Anchor still 2930.75 | **PASS** |
| Issue #26 populated ANN | Trace policies unchanged | **PASS** |
| MPOLICY width (#25) | 10-char majority preserved | **PASS** (no new blank/shortening introduced by this fix) |

---

## 5. Row Counts

| Table | Count | Notes |
|-------|------:|-------|
| `quikridr` (Output) | 6,934 | Joined check universe = 6,934 |
| `quikridr` (Test_Validation) | same file | Identical to Output |
| `quikmstr` | not modified by #88 | Anchor Mode Prem spot-checked |

---

## 6. Impact Summary

| Metric | Value |
|--------|------:|
| Joined MPREM mismatches vs rule | **0** |
| Anchor Prem/Unit correction | 2,930.75 → **5.8615** |
| Valuation overstatement (prior Compare analysis) | ~$6.97M → ~$0.14M residual (non-#88 / Valx zero-prem residuals) |

---

## 7. Failures (if any)

None for G5 scope.

**Accountability note (G7, not blocking G5):** `validate_issue_log_accountability.py` does not yet register Issue #88 as a spot-check. Closure Agent should wire #88 (or confirm IN_DATA via this validator) before Closed. Existing GAPs (#60, #58, #59) are unrelated.

---

## 8. Recommendation

- [x] Advance to **Regression Agent**
- [ ] Return to **Development Agent**

**Status:** **Ready for Regression**

---

## Appendix

- Validator stdout: `Issue_Log_Items/Issue_88/evidence/issue88_mprem_validator_stdout.txt`
- Risk sim (pre-dev): `Issue_Log_Items/Issue_88/evidence/issue88_mprem_simulated_changes.csv`
- QLA valuation confirm: `docs/Valuation/QLReports/QLAdmin-ValxLife 6-2026 from QLR 06-30-26 (rerun).xlsx`
