# Issue 21F — Validation Report

**Issue:** #21F — Truncated Premium History (conversion premium adjustment)  
**Framework stage:** Validation Agent (G5)  
**Date:** 2026-07-11  
**Agent / model:** Validation · **Cursor Grok 4.5** (locked)  
**Engine:** v57.73 (fix pass after v57.72 FAIL)  
**Verdict:** **PASS**

---

## Commands run

```powershell
python Issue_Log_Items/Issue_21/Issue_21F/_rebatch_quikprmh_21f.py
python Issue_Log_Items/Issue_21/Issue_21F/_rebatch_quikprmh_21f.py   # idempotency
python tools/validators/validate_issue21f_premium_adjustment.py --before QLA_Migration/Archive/quikprmh_pre_21f_v57.72.csv --publish-test-validation
python Issue_Log_Items/Issue_21/Issue_21F/_validate_issue21f_deep_audit.py
```

| Script | Exit |
|--------|------|
| Official validator | **0 (PASS)** |
| Deep audit | **0 (PASS)** — no findings |

Evidence: `evidence/issue21f_validation_deep_audit.json`, `QLA_Migration/Reports/issue21f_validation_deep_audit.json`

---

## v57.73 fixes verified

| Defect (v57.72) | Fix | Result |
|-----------------|-----|--------|
| UAT report blank ADJ / full variance on rebatch | Strip-rebuild CONV_ADJ each run; report shows ADJUSTMENT, FINAL_TOTAL = LifePRO, VARIANCE = 0 for LOADED/OPENING | **PASS** |
| OR `PREMIUMS_PAID` bleed into base | Base from **BA/BF only**; PU/SU/SL summed on typed rows | **PASS** — 13 fewer policies loaded (2,622 → **2,609**) |
| SU multi-row / negatives via max() | **Sum** `SU_PREMIUMS_PAID` on SU rows (negatives included) | **PASS** |
| No OPENING_BALANCE status | `OPENING_BALANCE` when hist ≤ 0 and positive adj (**359** policies) | **PASS** |
| Validator gap | Fail if report variance ≠ 0 for LOADED/OPENING | **PASS** |

---

## Load package results

| Check | Result |
|-------|--------|
| Schema field order | PASS |
| `quikprmh` rows | **209,470** (206,861 history + 2,609 CONV_ADJ) |
| Golden **010310404C** CONV_ADJ = **$15,193.85** @ `20171231` | PASS |
| Golden LifePRO reconcile ($17,040.05) | PASS |
| ISWL excluded (2,348 BF policies; samples 010713704C, 010818663C, 010765930C) | PASS |
| Negative exceptions (3 policies; e.g. 01FG8217A/C/D) not loaded | PASS |
| Duplicate CONV_ADJ per policy | PASS |
| Idempotent rebatch (strip 2,609 → reload 2,609; row count unchanged) | PASS |
| Existing payment history vs archive | PASS (206,861 rows byte-identical) |
| Marker literals `CONV_ADJ` / `QLA21F` / `21F-ADJ` / `20171231` | PASS |
| PREMIUM = MLIFE; money splits 0.00 | PASS |
| MPOLICY width on all CONV_ADJ | PASS (all len 10) |
| Report LOADED+OPENING = CONV_ADJ count; variance ≈ 0 | PASS |
| Report ADJUSTMENT sum = CONV_ADJ PREMIUM sum ($19,970,810.97) | PASS |
| Test_Validation publish | PASS — `Output/Test_Validation/quikprmh.csv` |

### Validation report STATUS counts

| STATUS | Count |
|--------|------:|
| LOADED | 2,250 |
| OPENING_BALANCE | 359 |
| ISWL_EXCLUDED | 2,348 |
| NEGATIVE_EXCEPTION | 3 |
| NO_GAP | 10 |
| NO_PREMIUM_DATA | 114 |

---

## Trace policy table

| Policy | Expectation | quikprmh | Validation report |
|--------|-------------|----------|-----------------|
| 010310404C | Adj $15,193.85 | **PASS** | **PASS** — LOADED, variance 0 |
| 010713704C (ISWL) | No adj | **PASS** | ISWL_EXCLUDED |
| 01FG8217A/C/D | Negative exception | **PASS** (not loaded) | NEGATIVE_EXCEPTION |

---

## Gate Criteria (G5)

| Criterion | Result |
|-----------|--------|
| Trace policies pass | **PASS** |
| Validation script exits 0 | **PASS** (official + deep audit) |
| Untouched fields confirmed | History / schema yes |
| Validation report published | This document |
| Status | **PASS** — proceed to Regression (re-confirm) or Closure |
