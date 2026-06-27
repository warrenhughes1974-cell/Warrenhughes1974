# Issue [ID] — Validation Report

**Issue:** [ID] — [Title]  
**Framework stage:** Validation Agent  
**Engine version:** v[xx.xx]  
**Validation script:** `QLA_Migration/_validate_issue[id]_*.py` v[x.x]  
**Output directory:** `QLA_Migration/Output/`  
**Before snapshot:** [path or N/A]  
**Generated:** [YYYY-MM-DD]  
**Verdict:** **PASS | FAIL**

---

## Commands Run

```bash
python QLA_Migration/_validate_issue[id]_*.py [--flags]
```

---

## 1. Trace Policy Results

| Policy | Phase | Field | Expected | Actual | Result |
|--------|------:|-------|----------|--------|--------|
| | | | | | PASS / FAIL |

---

## 2. Acceptance Criteria (from Risk checklist)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | | PASS / FAIL |
| 2 | | PASS / FAIL |

---

## 3. Source Alignment

| Check | Result |
|-------|--------|
| Populated source → emitted target | / |
| Fallback rows (blank/zero) | / |
| Orphan policies skipped | |

---

## 4. Untouched Fields Confirmed

| Field / table | Check | Result |
|---------------|-------|--------|
| quikmstr.MMODPREM | vs PPOLC | |
| quikprmh | vs before | |
| MVPU / MUNIT | vs PPBEN | |
| MPOLICY width (#25) | 10 char | |
| MPREM (#26) on non-scope rows | | |

---

## 5. Row Counts

| Table | Count | Before | Match? |
|-------|------:|-------:|--------|
| quikridr | | | |
| quikmstr | | | |
| quikprmh | | | |

---

## 6. Impact Summary

| Metric | Value |
|--------|------:|
| Target field rows changed | |
| Rows unchanged | |

---

## 7. Failures (if any)

| # | Description | Severity | Return to Dev? |
|---|-------------|----------|----------------|
| | | | Yes / No |

---

## 8. Recommendation

- [ ] Advance to **Regression Agent**
- [ ] Return to **Development Agent** with fixes: [list]

---

## Appendix

- Full validator stdout: [optional path or snippet]
- Before/after trace CSV: [path]
