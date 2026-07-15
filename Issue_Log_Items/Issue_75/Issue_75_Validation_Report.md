# Issue #75 — Validation Report

**Issue:** #75 — Bank Acct / `MBANKNO` QLA validation  
**Framework stage:** Validation Agent  
**Engine version:** v57.92  
**Validation script:** `Issue_Log_Items/Issue_75/scripts/validate_issue75_mbankno.py`  
**Output directory:** `QLA_Migration/Output/`  
**Before snapshot:** `Issue_Log_Items/Issue_75/evidence/before_batch_v57.92/`  
**Generated:** 2026-07-15  
**Model:** Cursor Grok 4.5 (locked)  
**Verdict:** **PASS**

---

## Commands Run

```bash
python tools/batch_tests/run_full_batch_test.py
python Issue_Log_Items/Issue_75/scripts/validate_issue75_mbankno.py
```

Batch: **exit 0** (~30 min). Validator: **exit 0 / PASS**.

---

## 1. Trace Policy Results

| Policy | MBILLFRM | Field | Expected | Actual (masked) | Result |
|--------|:--------:|-------|----------|-----------------|--------|
| **010161748C** | 2 | MBANKNO | blank or QL-safe | blank | **PASS** (no invalid routing) |
| 010157076C | 2 | MBANKNO | blank or QL-safe | blank | PASS |
| 010348734C | 2 | MBANKNO | blank or QL-safe | blank | PASS |
| 010464590C | 2 | MBANKNO | blank or QL-safe (was `//`) | blank | PASS |
| **010713704C** | 2 | MBANKNO | unchanged valid 9-digit | `*****0016/****4579` | **PASS** |

Detail: `evidence/issue75_validation_trace_masked.csv`

---

## 2. Acceptance Criteria (Risk checklist §10)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | No filled `MBANKNO` with ABA ≠ 9 digits | **PASS** (0 invalid) |
| 2 | No multi-slash or hyphen/space in account half | **PASS** |
| 3 | Trace 010161748C no invalid routing emit | **PASS** (blank) |
| 4 | 010713704C regression unchanged | **PASS** |
| 5 | `MBILLFRM`, `MACCTNO`, `MMODEPREM`, `MSTATUS` unchanged | **PASS** (0 side changes) |
| 6 | quikmstr row count stable | **PASS** (5,083) |
| 7 | Exception CSV lists blanked bank-draft rows | **PASS** (910 rows) |
| 8 | `Test_Validation/quikmstr.csv` published | **PASS** |

---

## 3. Source Alignment

| Check | Result |
|-------|--------|
| PPACH + lookup + PPPAC/RNA path used | PASS (batch log v57.92) |
| Truncated ABA not emitted | PASS |
| Account digits-only when emitted | PASS |
| Unrecoverable → blank + exception | PASS (`ABA_NOT_9` 185; `MISSING_ROUTING` 710) |

---

## 4. Untouched Fields Confirmed

| Field / table | Check | Result |
|---------------|-------|--------|
| `MBILLFRM` | 0 changes on trace + fleet compare | **PASS** |
| `MACCTNO` | 0 side changes | **PASS** |
| `MMODE` / `MMODEPREM` | 0 side changes | **PASS** |
| `MSTATUS` / `MBILLDAY` | 0 side changes | **PASS** |
| MPOLICY width (#25) | all 10-char | **PASS** |
| quikridr.MPREM (#26) | not re-scoped | **PASS** (row count stable) |

---

## 5. Row Counts

| Table | After | Before | Match? |
|-------|------:|-------:|:------:|
| quikmstr | 5,083 | 5,083 | Yes |
| quikridr | 6,934 | 6,934 | Yes |
| MBANKNO filled | 1,824 | 2,736 | Intentional (-912) |
| PAC filled MBANKNO | 1,222 | 2,108 | Intentional |
| PAC blank MBANKNO | 910 | 24 | Intentional (+886) |

---

## 6. Impact Summary

| Metric | Value |
|--------|------:|
| `MBANKNO` value changes | 1,074 |
| Invalid filled after fix | **0** |
| Already-valid unchanged (e.g. 010713704C) | confirmed |
| Bank-draft exceptions after | 910 |
| Exception reasons added | `ABA_NOT_9` (185) |

Before exceptions: 24 → After: 910 (expected tradeoff for QLA-safe emit).

---

## 7. Failures

None.

---

## 8. Recommendation

- [x] Advance to **Regression Agent**
- [ ] Return to Development — not required

**Client UAT:** Reload `Output/Test_Validation/quikmstr.csv` and retest policy edit on **010161748C** — Bank Acct should no longer show `Invalid routing number (//)`; field may be blank until full 9-digit ABA is sourced.

---

## Appendix

Validator stdout:

```text
helpers: PASS
output: PASS {'rows': 5083, 'filled': 1824, 'invalid_filled': 0, 'pac_filled': 1222, 'pac_invalid': 0, 'pac_blank': 910}
```

Evidence:
- `evidence/issue75_validation_summary.csv`
- `evidence/issue75_validation_trace_masked.csv`
- `evidence/before_batch_v57.92/`
- `QLA_Migration/Logs/_full_batch_test_log.txt`
- `QLA_Migration/Reports/bank_draft_account_exceptions.csv`
