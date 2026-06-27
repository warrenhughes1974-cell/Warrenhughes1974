# Issue [ID] — Regression Report

**Issue:** [ID] — [Title]  
**Framework stage:** Regression Agent  
**Engine version:** v[xx.xx]  
**Baseline:** [git commit / `_issue*_before/` / date]  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** [YYYY-MM-DD]  
**Verdict:** **PASS | FAIL**

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|-----------|-----------------|
| Target table/field | [intentional change only] |
| Other tables | No row count change |
| Other fields | No change |

---

## 2. Row Count Comparison

| Table | Before | After | Delta | OK? |
|-------|-------:|------:|------:|-----|
| quikmstr | | | 0 | |
| quikridr | | | | |
| quikprmh | | | 0 | |
| quikplan | | | 0 | |
| quikclid | | | 0 | |
| quikclnt | | | 0 | |
| [issue table] | | | | |

---

## 3. Non-Target Field Diff (affected tables)

| Table | Column | Rows changed | OK? |
|-------|--------|-------------:|-----|
| | [all except target] | 0 | |

---

## 4. Prior Issue Fix Regression

### Issue #25 — MPOLICY padding

| Check | Result |
|-------|--------|
| `_validate_mpolicy_width.py` | PASS / FAIL |
| Sample policies width = 10 | |

### Issue #26 — MPREM mapping

| Check | Result |
|-------|--------|
| `_validate_issue26_mprem.py` | PASS / FAIL |
| MMODPREM unchanged | |

---

## 5. Schema Integrity (AGENTS.md)

| Check | Result |
|-------|--------|
| Field order preserved | |
| Field types/lengths preserved | |
| No new blank MRIDRID | |
| QLA formatting rules preserved | |

---

## 6. Batch / Fleet Checks

| Check | Result |
|-------|--------|
| Full batch completed | Yes / No |
| `validate_output.py` | PASS / FAIL / N/A |
| Audit log anomalies | None / [list] |

---

## 7. Failures (if any)

| # | Description | Blast radius | Action |
|---|-------------|--------------|--------|
| | | | Return to Dev |

---

## 8. Recommendation

- [ ] Advance to **Closure Agent** / **Ready for Client UAT**
- [ ] Return to **Development Agent**

---

## Appendix

- Batch log: `QLA_Migration/Output/_full_batch_test_log.txt`
- Diff artifacts: [paths]
