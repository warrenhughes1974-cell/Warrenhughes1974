# Issue #159 — Regression Report

**Issue:** #159 — L10/L14 traditional-life reserves at $0 (UW key mismatch)  
**Framework stage:** Regression Agent  
**Engine version:** v59.08  
**Baseline:** `QLA_Migration/Archive/issue159_pre_remap/quikridr_pre_issue159.csv`  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-09-02  
**Verdict:** **PASS**

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|---|---|
| Target table/field | `quikridr.MUWCLASS` only — 616 letter-sourced remaps |
| Other tables | No row count change |
| Other fields | No change |

---

## 2. Row Count Comparison

| Table | Before | After | Delta | OK? |
|---|---:|---:|---:|-----|
| quikmstr | 5083 | 5083 | 0 | Yes |
| quikridr | 6956 | 6956 | 0 | Yes |
| quikprmh | 211709 | 211709 | 0 | Yes |
| quikplan | 142 | 142 | 0 | Yes |
| quikclid | 32285 | 32285 | 0 | Yes |
| quikclnt | 13598 | 13598 | 0 | Yes |
| quikspec | 5083 | 5083 | 0 | Yes |

---

## 3. Non-Target Field Diff (affected tables)

| Table | Column | Rows changed | OK? |
|---|---|---:|-----|
| quikridr | all except MUWCLASS | 0 | Yes |
| quikridr | MPOLICY + MPREM + MBAND + MUNIT | 0 of 6956 | Yes |

---

## 4. Prior Issue Fix Regression

Catalog: `Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md`

### Issue #25 / #2 — Policy key width

| Check | Result |
|---|---|
| `QLA_Migration/_validate_issue2_mpolicy.py` | **PASS** (316,753 keys width 11) |
| Sample policies | 9010143726C / 901222DCC / 9014059C present |

### Issue #26 — MPREM mapping

| Check | Result |
|---|---|
| `validate_issue26_mprem.py` | **WARN** — script still points at retired `_20260530` extracts (pre-existing #112 class). Not caused by #159. |
| MPREM leading-dot (#55 spot) | 0 |
| MPREM identity vs before snapshot | 6956/6956 identical |

### Other Closed rows overlapping this change

| Issue ID | Guide check / validator | Result |
|---|---|---|
| #55 MUNIT floor | `validate_issue55_munit_floor.py` | PASS |
| #59 MSTATUS allowlist | `validate_issue59_mstatus.py` | Pre-existing 8/31 cut FAIL (9010521213C / 901ML8250C now T/DC→53). Not a #159 change — MUWCLASS only. |
| #105 / #119 MPAR | `validate_issue105_mpar.py` | PASS |
| #139 ISWL fee withhold | `validate_issue139_policy_fee_suppression.py` | PASS |
| #142 9SUBLF | `validate_issue142_sl_rider.py` | PASS |
| #118 form-aware UW | `validate_issue118_uwclass.py` | PASS (WARN: 95 L10 rider SM not yet on QuikPlUw — membership only) |
| #96 / #136 PVO | flags not edited | N/A — no quikplan write |
| #71 BAND | MBAND unchanged | PASS (identity) |
| #107 / #157 / #158 | rates not edited | N/A |

---

## 5. Schema Integrity (AGENTS.md)

| Check | Result |
|---|---|
| Field order preserved | PASS (backup vs current headers identical) |
| Field types/lengths preserved | PASS |
| No new blank MRIDRID | N/A — field not touched |
| QLA formatting rules preserved | PASS |

---

## 6. Batch / Fleet Checks

| Check | Result |
|---|---|
| Full policy batch | No — letter-sourced `quikridr` remap only; `app.py` wired for next batch |
| `validate_output.py` | N/A |
| Audit log anomalies | None |

---

## 7. Failures

None for #159. #26 extract-path WARN is environmental (stale 20260530 filenames). Full `--smoke-only` is RELEASE_BLOCKED on pre-existing #59 MSTATUS cut drift (8/31 PPOLC T/DC), not on #159 (that job PASS).

---

## 8. Recommendation

- [x] Advance to **Closure Agent**
- [ ] Return to **Development Agent**

---

## Appendix

- Before snapshot: `QLA_Migration/Archive/issue159_pre_remap/quikridr_pre_issue159.csv`
- UAT trace: `Issue_Log_Items/Issue_159/evidence/issue159_uat_before_after.csv`
