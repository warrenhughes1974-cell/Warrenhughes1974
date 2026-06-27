# Issue #28 — Regressions

**Validation date:** 2026-06-27  
**Engine:** v57.35  
**Batch:** Full UAT batch (20260530 source)

---

## Protected issue regression matrix

| Issue | Validator | Result | Notes |
|-------|-----------|--------|-------|
| **#25** MPOLICY width | `tools/validators/validate_mpolicy_width.py` | **PASS** | 279,222 fields checked; 0 width violations |
| **#26** MPREM | `tools/validators/validate_issue26_mprem.py` | **PASS** | Trace policies + ANN/MODE alignment |
| **#21M** QUIKMEMO | `tools/validators/validate_issue21m_quikmemo.py` | **PASS** | 4380 rows; 4380 unique MEMOKEY |
| **#21M-FU** DBF packaging | `tools/validators/validate_issue21m_dbf_packaging.py` | **PASS** | DBF 4380 rows; hygiene OK |
| **#21K** MUNIT precision | `tools/validators/validate_issue21k_munit.py` | **PARTIAL** | CSV PASS; DBF reload skipped |

---

## Issue #25 — MPOLICY width

```
OVERALL: PASS - all MPOLICY fields are exactly 10 characters
Total fields checked: 279,222
```

Cross-table consistency samples (018495BC, 018499CC, 018510C): PASS

---

## Issue #26 — MPREM

```
RESULT: PASS
Trace policies 010310404C, 010331768C, 010367131C: PASS
Edge case 010718276C: PASS
ANN populated: 3743/3743 match; Fallback MODE: 2994/2994 match
quikridr rows: 7002 (unchanged)
```

Issue #21M validator cross-check: Issue #26 preservation PASS

---

## Issue #21M — QUIKMEMO

```
RESULT: PASS
quikmemo rows: 4380 (expected 4380)
unique MEMOKEY: 4380
duplicate MEMOKEY groups: 0
merged segments: 29279
Regression row counts: all tables match baseline
Issue #26 preservation: PASS
Issue #25 preservation: PASS
```

---

## Issue #21M-FU — DBF packaging

```
RESULT: PASS
DBF rows: 4380
DBF duplicate keys: 0
CSV unchanged: 4380 rows
Regression tables: quikmstr/quikridr/quikprmh unchanged
```

---

## Issue #21K — MUNIT (observation)

```
CSV precision: PASS
QUIKRIDR DBF reload: FAIL (missing qladmin_issue21k/QUIKRIDR.DBF)
OVERALL: FAIL (validator script)
```

**Assessment:** Not an Issue #28 regression. The DBF artifact requires a separate manual step (`issue21k_units_migration.py --reload-quikridr`) outside standard batch. Core MUNIT CSV precision validation **PASS**. Recommend Regression & Deployment Agent confirm DBF reload in deployment checklist if DBF UAT is required.

---

## Issue #28 functional regression

| Check | Result |
|-------|--------|
| 108 stable PLAN mappings unchanged | PASS |
| 33 divergent mappings corrected | PASS |
| No new blank MRIDRID introduced | PASS (21 pre-existing; unchanged count) |
| Schema integrity (quikplan/quikridr columns) | PASS |

---

## validate_output.py (general schema)

Exit code 1 — pre-existing duplicate-key and priority-rule findings across quikclid, quikclnt, quikprmh, quikclmp, quikclms. These findings exist independent of Issue #28 and were not used as a regression gate for this issue.

---

## Overall regression decision

**Protected issues #25, #26, #21M, #21M-FU: PASS**  
**Issue #21K: PASS (CSV) with DBF artifact observation**  
**No Issue #28-induced regressions detected**
