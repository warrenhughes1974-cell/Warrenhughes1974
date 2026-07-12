# Issue #45 — Validation Report

**Issue:** #45 — PPPAC `E_ACCOUNT_NUMBER` fallback for bank-draft `MBANKNO`  
**Framework stage:** Validation Agent  
**Engine version:** v57.77  
**Validation scripts:**  
- `QLA_Migration/_validate_issue45_output.py`  
- `QLA_Migration/_validate_issue45_pppac_fallback.py`  
**Output directory:** `QLA_Migration/Output/`  
**Before snapshot:** `Issue_Log_Items/Issue_45/evidence/before_batch_v57.77/`  
**Generated:** 2026-07-12  
**Verdict:** **PASS**  
**Model:** Cursor Grok 4.5 (locked Validation stage)

---

## Commands Run

```bash
# Before snapshot (763 exceptions / blank MBANKNO for candidates)
# Headless batch at v57.77 (rates skipped for speed; governance audit skipped)
$env:QLA_SKIP_GOVERNANCE_AUDIT='1'
$env:QLA_BATCH_INCLUDE_RATE_TABLES='0'
python tools/batch_tests/run_full_batch_test.py

python QLA_Migration/_validate_issue45_output.py
python QLA_Migration/_validate_issue45_pppac_fallback.py

python tools/publish_test_validation.py quikmstr --issue Issue_45
```

**Note:** Full batch process was still running other tables when quikmstr Validation completed. `quikmstr.csv` and `bank_draft_account_exceptions.csv` were rewritten at ~15:50–15:51 local time by the v57.77 engine and are the evidence base for this report.

---

## 1. Trace Policy Results

| Policy | Field | Expected | Actual (masked) | Result |
|--------|-------|----------|-----------------|--------|
| 010157076C | MBILLFRM | 2 | 2 | PASS |
| 010157076C | MBANKNO | filled ABA/ACCOUNT | *****1013/****2919 | PASS |
| 010161748C | MBILLFRM | 2 | 2 | PASS |
| 010161748C | MBANKNO | filled | *****0385/****0581 | PASS |
| 010348734C | MBILLFRM | 2 | 2 | PASS |
| 010348734C | MBANKNO | filled | *****1811/****8787 | PASS |
| 9015000043 | exception | still missing account | in exception CSV (`MISSING_BANK_ACCOUNT`) | PASS |

---

## 2. Acceptance Criteria (from Risk checklist)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Trace policies populate `MBANKNO` only with both halves | **PASS** |
| 2 | ≥10 PPACH-banked sample `MBANKNO` byte-identical | **PASS** (50/50 unchanged) |
| 3 | Exception CSV drops from 763 toward ~15–24 | **PASS** (24) |
| 4 | Remaining exceptions still `MBILLFRM=2`; policies in quikmstr | **PASS** |
| 5 | No change to sample `MMODEPREM` / `MACCTNO` | **PASS** (0 changed) |
| 6 | `MBILLFRM` unchanged for prior blank bank-draft set | **PASS** (763/763 still 2) |
| 7 | Log / engine shows PPPAC path (v57.77 batch) | **PASS** (APP_VERSION=v57.77; fallback applied in output) |
| 8 | Publish `quikmstr.csv` to `Output/Test_Validation/` | **PASS** |

---

## 3. Source Alignment

| Check | Result |
|-------|--------|
| PPPAC account + ABA → emitted `MBANKNO` | **739** previously blank policies now filled |
| PPPAC account, ABA unresolved → blank + `MISSING_ROUTING` | **11** |
| No account in PPACH or PPPAC → `MISSING_BANK_ACCOUNT` | **13** |
| PPACH-primary policies | Untouched (sample 50) |

---

## 4. Untouched Fields Confirmed

| Field / table | Check | Result |
|---------------|-------|--------|
| quikmstr.MBILLFRM | prior blank set still 2 | PASS |
| quikmstr.MMODEPREM | 50 PPACH sample | PASS (0 changed) |
| quikmstr.MACCTNO | 50 PPACH sample | PASS (0 changed) |
| quikmstr.MBANKNO (PPACH-banked) | 50 sample | PASS (0 changed) |
| quikmstr row count | before/after | PASS (5083 = 5083) |
| #25 MPOLICY / #26 MPREM | out of scope; not touched in code | N/A (code-level) |

---

## 5. Row Counts

| Table / artifact | Before | After | Match? |
|------------------|-------:|------:|--------|
| quikmstr.csv | 5083 | 5083 | Yes |
| PAC (`MBILLFRM=2`) | 2132 | 2132 | Yes |
| PAC with `MBANKNO` filled | 1369 | **2108** | Intentional (+739) |
| PAC with blank `MBANKNO` | 763 | **24** | Intentional |
| bank_draft_account_exceptions.csv | 763 | **24** | Intentional |

---

## 6. Impact Summary

| Metric | Value |
|--------|------:|
| Previously blank bank-draft policies now filled | **739** |
| Remaining exceptions | **24** (13 no account + 11 missing routing) |
| PPACH-banked sample unchanged | **50 / 50** |
| Target table for UAT reload | `quikmstr.csv` |

### Remaining exception mix

| EXCEPTION_REASON | Count |
|------------------|------:|
| MISSING_BANK_ACCOUNT | 13 |
| MISSING_ROUTING | 11 |

---

## 7. Failures

None.

---

## 8. Recommendation

- [x] Advance to **Regression Agent**
- [ ] Return to Development — N/A

**UAT partial reload:** `QLA_Migration/Output/Test_Validation/quikmstr.csv` (published Issue_45).

---

## Appendix

### Validator stdout (output)

```text
quikmstr rows: 5083 (before 5083)
exception rows: 24
reasons: {'MISSING_BANK_ACCOUNT': 13, 'MISSING_ROUTING': 11}
Trace 010157076C: MBILLFRM=2 MBANKNO=*****1013/****2919
Trace 010161748C: MBILLFRM=2 MBANKNO=*****0385/****0581
Trace 010348734C: MBILLFRM=2 MBANKNO=*****1811/****8787
PAC rows: 2132 filled=2108 blank=24
PPACH sample: checked=50 MBANKNO_changed=0 MMODEPREM_chg=0 MACCTNO_chg=0
prev blank=763 still MBILLFRM=2=763 now filled=739
PASS
```

### Evidence paths

- `Issue_Log_Items/Issue_45/evidence/before_batch_v57.77/`
- `Issue_Log_Items/Issue_45/evidence/issue45_validation_trace_masked.csv`
- `Issue_Log_Items/Issue_45/evidence/issue45_exceptions_after.csv`
- `QLA_Migration/Output/Test_Validation/manifest.txt`

### Gate G5 checklist

- [x] Trace policies pass
- [x] Output validator exits 0
- [x] Untouched fields confirmed for issue scope
- [x] Validation report published
- [x] Status: **Ready for Regression**
