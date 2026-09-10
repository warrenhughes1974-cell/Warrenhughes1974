# Issue #167 — Regression Report

**Issue:** #167 — Dividend Premium Payment
**Framework stage:** Regression Agent
**Engine version:** v59.12
**Baseline:** `Issue_Log_Items/Issue_167/evidence/quikridr_pre_issue167_20260910T081723Z.csv`
**Output directory:** `QLA_Migration/Output/`
**Valuation date:** 20260831
**Generated:** 2026-09-10
**Verdict:** **PASS**

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|---|---|
| Target table/field | `quikridr.MLASTANN` only — 2,142 rows, all −1 |
| ETI/RPU phase 1 | Untouched (Issue #76 / #108B paid-to math) |
| Other tables | No row-count change |
| Other fields | No change |

---

## 2. Row Count Comparison

| Table | Before | After | Delta | OK? |
|---|---:|---:|-----|-----|
| quikmstr | 5,083 | 5,083 | 0 | Yes |
| quikridr | 6,956 | 6,956 | 0 | Yes |
| quikprmh | 211,709 | 211,709 | 0 | Yes |
| quikplan | 142 | 142 | 0 | Yes |
| quikclid | 32,285 | 32,285 | 0 | Yes |
| quikclnt | 13,598 | 13,598 | 0 | Yes |
| quikbenh | 41,465 | 41,465 | 0 | Yes |

---

## 3. Non-Target Field Diff (quikridr)

| Check | Result |
|---|---|
| Column count / header | 40 columns identical to snapshot |
| Keys (MPOLICY + MPHASE) | Same 6,956 keys |
| Columns other than MLASTANN | 0 rows changed |
| MLASTANN | 2,142 rows changed, all −1 |
| ETI/RPU phase-1 MLASTANN | 314 rows identical to snapshot |

---

## 4. Prior Issue Fix Regression

Catalog: `Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md`

### Issue #167 (this fix)

| Check | Result |
|---|---|
| `tools/validators/validate_issue167_mlastann.py` | **PASS** — gold 9010397528C 54/54; July 56; April 54; ETI traces 33 / 16 |

### Issue #2 — Policy key width

| Check | Result |
|---|---|
| `#2 MPOLICY width-11` | **PASS** |

### Issue #55 — MUNIT floor

| Check | Result |
|---|---|
| `tools/validators/validate_issue55_munit_floor.py` | **PASS** |

### Issue #119 — PUA MPAR=0

| Check | Result |
|---|---|
| `tools/validators/validate_issue119_pua_mpar.py` | **PASS** |

### Issue #139 — ISWL fees withheld

| Check | Result |
|---|---|
| `tools/validators/validate_issue139_policy_fee_suppression.py` | **PASS** |

### Issue #160 — PUA terminal status (same table, different column)

| Check | Result |
|---|---|
| `tools/validators/validate_issue160_pua_terminal_status.py` | Environmental **FAIL** — missing archive `QLA_Migration/Archive/issue160_pre_remap/quikridr_pre_issue160.csv`. MPHSTAT was not in the #167 diff (MLASTANN only). |

### Pre-existing, unrelated FAIL (not a #167 regression)

| Check | Result |
|---|---|
| `tools/validators/validate_issue76_eti_rpu_payup.py` | **FAIL** — 77 MLASTANN mismatches vs paid-to anniversary math. Snapshot proves those 314 ETI/RPU phase-1 values are **unchanged**. Accountability already records #76 as GAP on this 8/31 cut. |
| `tools/validators/validate_issue160_pua_terminal_status.py` archive path | Environmental FAIL only if `QLA_Migration/Archive/issue160_pre_remap/quikridr_pre_issue160.csv` is missing. MPHSTAT was not rewritten by #167. |

---

## 5. Schema Integrity (AGENTS.md)

| Check | Result |
|---|---|
| Field order preserved | PASS — header identical to snapshot |
| Field types/lengths preserved | PASS |
| No new blank MRIDRID | PASS — field not touched |
| QLA formatting rules preserved | PASS |

---

## 6. Batch / Fleet Checks

| Check | Result |
|---|---|
| Full policy batch | No — scoped `MLASTANN`-only remap of `quikridr`; `app.py` wired for next full batch |
| `validate_release_closed_issues.py --smoke-only` | **#167 PASS** (always-on job). Suite may still be RELEASE_BLOCKED on pre-existing #59 MSTATUS (`9010521213C` / `901ML8250C`) — same gap documented since Issue #159 Regression (2026-09-02). Not caused by this fix. |
| Audit log anomalies | None |

---

## 7. Failures

None attributable to #167. #76 MLASTANN gaps and any #59 smoke FAIL are pre-existing on this 8/31 cut.

---

## 8. Recommendation

- [x] Advance to **Closure Agent**
- [ ] Return to **Development Agent**

---

## Appendix

- Before snapshot: `Issue_Log_Items/Issue_167/evidence/quikridr_pre_issue167_20260910T081723Z.csv`
- Independent Validation: `Issue_Log_Items/Issue_167/Issue_167_Validation_Report.md`
