# Issue #143 — Regression Report

**Issue:** #143 — Units Incorrect (RPU)  
**Framework stage:** Regression Agent  
**Engine version:** v58.96  
**Baseline:** `Issue_Log_Items/Issue_143/evidence/quikridr_pre_issue143_20260818T130527Z.csv` (pre-#143 `quikridr.csv`)  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-08-18  
**Verdict:** **PASS**

No production code was changed during Regression. Formal Closure was not started.

---

## 1. Executive regression verdict

**PASS — READY FOR CLOSURE.**

Issue #143 is contained to **23** `quikridr` phase-1 `MUNIT` values. Every other QuikRidr field is identical to the pre-#143 baseline. Protected issues #2 / #25 (width via #2) / #26 (baseline identity + traces) / #55 / #108A hold. Issue #124’s stored `MDB` still reflects pre-correction units because `QuikIswl.csv` was not reseeded — that is an **EXPECTED DOWNSTREAM CONSEQUENCE**, not a regression.

There are **no unexplained differences**.

---

## 2. Baseline used

| Item | Path / value |
|------|----------------|
| Pre-#143 QuikRidr | `evidence/quikridr_pre_issue143_20260818T130527Z.csv` |
| Post-#143 QuikRidr | `QLA_Migration/Output/quikridr.csv` |
| Independent candidate list | `evidence/issue143_independent_candidates.csv` (Validation) |
| Other tables | Current Output inventory only — #143 apply did not rewrite them |
| Engine | `APP_VERSION = v58.96` in both `app.py` files |

Regression compare: `Issue_Log_Items/Issue_143/_regress_issue143.py`  
Evidence: `evidence/issue143_regression_summary.json`

---

## 3. Output row-count comparison

Issue #143 does not create or remove records.

| Table | Baseline / prior known | After | Delta | Class |
|-------|-----------------------:|------:|------:|-------|
| quikridr | 6,934 | 6,934 | 0 | Unchanged count |
| quikmstr | (current) 5,083 | 5,083 | 0 | Not rewritten by #143 |
| quikprmh | (current) 211,709 | 211,709 | 0 | Not rewritten |
| quikplan | (current) 141 | 141 | 0 | Not rewritten |
| quikclid | (current) 32,285 | 32,285 | 0 | Not rewritten |
| quikclnt | (current) 13,598 | 13,598 | 0 | Not rewritten |
| QuikIswl | (current) 2,268 | 2,268 | 0 | Not reseeded |
| QuikIsrr | (current) 3,657 | 3,657 | 0 | Not rewritten |

QuikRidr `MPOLICY+MPHASE` key set: **identical** (6,934 / 6,934). Schema: **40 columns, same order**.

---

## 4. Field-level comparison

### quikridr (full file vs pre-#143 baseline)

| Check | Result | Class |
|-------|--------|-------|
| Rows that differ | **23** | EXPECTED ISSUE #143 |
| Fields that differ | **`MUNIT` only** (23 hits) | EXPECTED ISSUE #143 |
| `MPREM` diffs | **0** | — |
| `MVPU` diffs | **0** | — |
| `MSAVEUNIT` diffs | **0** | — |
| `MPOLICY` diffs | **0** | — |
| All other QuikRidr fields | **0** diffs | — |
| Non-candidate rows changed | **0** | — |

Gold `9010757606C`: `25.00000` → `19.10196`; `MVPU` 1000.00; Amount Ins 19101.96; `MPREM` 9.77037 unchanged.

### Other tables

`QuikIswl.csv` row count and stored `MDB` values are unchanged (file not regenerated). Stored `MDB` on the 23 ISWL candidates no longer equals current `MUNIT × 1000`. Class: **EXPECTED DOWNSTREAM CONSEQUENCE** (see §7).

No other target table was part of the #143 apply. No #143-induced create/delete.

---

## 5. Protected-issue validator results

| Issue | Check | Result | Classification |
|-------|-------|--------|----------------|
| **#2** | `QLA_Migration/_validate_issue2_mpolicy.py` | **PASS** — 331,647 MPOLICY values width 11; traces include `901222DC` → `  901222DCC` and `9014100C` → `  9014100CC` | Intact. Extra-C behavior **not** modified. |
| **#25** | Historical width-10; superseded by #2 | Covered by #2 width PASS | Intact |
| **#26** | Script `validate_issue26_mprem.py` | Script **FAIL** — hardcoded `*_Extract_20260530.csv` missing (environment) | **PRE-EXISTING** validator/extract gap |
| **#26** | Baseline + traces | **PASS** — fleet `MPREM` diffs = 0; `9010310404C` 13.20000; `9010331768C` 10.96000; `9010367131C` 9.12000 unchanged | Intact |
| **#55** | `validate_issue55_munit_floor.py` | **PASS** — 6,934 rows; 0 sub-floor; traces `9018495BC` / `9018499CC` / `9018510C` / PUA floor | Intact |
| **#108A** | Baseline `MSAVEUNIT` on 23 + status-45 blanks | **PASS** — 0 `MSAVEUNIT` diffs; gold blank | Intact |
| **#124 formula** | `MDB = MUNIT × 1000` in `qla_core/quikiswl_loader.py` | **Unchanged** (not edited) | Intact |
| **#124 stored file** | `validate_issue124_quikiswl.py` | Reports **23 rows MDB != MUNIT×1000** because seed was not regenerated | **EXPECTED DOWNSTREAM CONSEQUENCE** — not a #143 regression |
| **#143** | `validate_issue143_rpu_munit.py` | **PASS** | Expected |
| **#105** | `validate_issue105_mpar.py` | **PASS** | Intact |
| **#119** | `validate_issue119_pua_mpar.py` | **PASS** | Intact |
| **#21K** | `validate_issue21k_munit.py` | Script **FAIL** — missing `qladmin_issue21k/QUIKRIDR.DBF`; looks for legacy `010448806C` | **PRE-EXISTING** packaging/key check; not introduced by #143 |

#26 / #21K script FAILs are **not** unexplained #143 diffs. QuikRidr field identity already proves `MPREM` and 5-decimal `MUNIT` emit on the 23.

---

## 6. Issue #143 population containment

Independent Validation population, re-proven against the baseline diff:

| Population | Expected | Regression proof |
|------------|---------:|------------------|
| BF RPU mismatch | 23 remapped | 23 `MUNIT`-only diffs; all in the independent candidate set |
| BF RPU already aligned | 82 unchanged | 0 of these keys in the 23-row diff |
| BA RPU | 0 remapped | 0 BA keys in the 23-row diff |
| Non-RPU / other benefit types | 0 remapped | 6,911 non-candidate rows byte-identical |
| 15 BA extra-C keys (`9018166C` → `9018166CC`) | Unchanged | Confirmed in Validation; #2 validator still emits extra C; **do not change #2** |

---

## 7. Issue #124 downstream-impact classification

All 23 candidates are ISWL (`1658C1` / `1659C2` / `1659CR`). `QuikIswl.csv` was **not** reseeded (authorized: do not regenerate solely to match current `MUNIT`).

| | Current stored MDB | Expected MDB after authorized reseed | Class |
|--|-------------------:|-------------------------------------:|-------|
| Formula | — | `MDB = corrected MUNIT × 1000` | Unchanged #124 logic |
| Gold `9010757606C` | **25000.00** | **19101.96** | EXPECTED DOWNSTREAM CONSEQUENCE |
| All 23 ISWL candidates | original face (`MUNIT_old × 1000`) | `MUNIT_new × 1000` | EXPECTED DOWNSTREAM CONSEQUENCE |

`validate_issue124_quikiswl.py` FAIL (`23 rows with MDB != MUNIT*1000`) is that same unreseeded gap. **Do not treat as a regression.** Next authorized #124 seed will pick up corrected units.

---

## 8. Unexpected differences

**None.**

| Difference | Class |
|------------|-------|
| 23 `quikridr.MUNIT` values | EXPECTED ISSUE #143 |
| 23 stored QuikIswl `MDB` still at old face | EXPECTED DOWNSTREAM CONSEQUENCE |
| #26 script missing 20260530 extracts | PRE-EXISTING |
| #21K missing DBF / legacy key | PRE-EXISTING |
| `Sync_Rulebook_quikridr.csv` MPREM comment (#137) | PRE-EXISTING comment-only; `NUMBER_OF_UNITS,MUNIT` default unchanged |

---

## 9. Exceptions / observations

1. **15 BA “absent” keys** remain a Validation lookup artifact vs Issue #2 extra-C. #2 validator PASS on those exact traces. Out of scope.
2. **No full-fleet Output snapshot** exists for tables other than `quikridr`. Containment for those tables is: #143 apply did not write them; current row counts are stable; no #143 create/delete.
3. Extra overlapping QuikRidr validators (#76 / #118 / #137) were not required for blast-radius proof: every non-`MUNIT` field is identical to baseline.
4. Working-tree #137 rulebook **comment** is unrelated to #143.

---

## 10. Version / architecture

| Check | Result |
|-------|--------|
| `app.py` | **v58.96** |
| `QLA_Migration/app.py` | **v58.96** |
| #143 production files | `qla_core/issue143_rpu_munit.py` + isolated hook in both `app.py` files |
| #55 emit / #124 loader | Not modified |
| Default rulebook map `NUMBER_OF_UNITS → MUNIT` | Unchanged |
| Unrelated architecture / mapping rewrite | **None** |

---

## 11. Final gate recommendation

- [x] **READY FOR CLOSURE**
- [ ] Return to Development

Formal Closure was **not** started.

### Commands run

```text
python Issue_Log_Items/Issue_143/_regress_issue143.py
python QLA_Migration/_validate_issue2_mpolicy.py
python tools/validators/validate_issue26_mprem.py
python tools/validators/validate_issue55_munit_floor.py
python tools/validators/validate_issue143_rpu_munit.py
python tools/validators/validate_issue124_quikiswl.py
python tools/validators/validate_issue105_mpar.py
python tools/validators/validate_issue119_pua_mpar.py
python tools/validators/validate_issue21k_munit.py
```
