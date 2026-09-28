# Issue 175 — Regression Report

**Issue:** 175 — Res Cat Unique Field
**Framework stage:** Regression Agent
**Engine version:** v59.26. `app.py` was not changed.
**Baseline:** `Issue_Log_Items/Issue_175/evidence/issue175_resrvcat_population.csv` (the 33 rows before the patch)
**Output directory:** `QLA_Migration/Output/`
**Generated:** 2026-09-28
**Verdict:** **PASS**

No full rebatch. Only `quikspec.csv` was rewritten, and only `RESRVCAT` on 33 rows.

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|---|---|
| `quikspec.RESRVCAT` on L15, L16, and L17 BASE | `L` → 13 or 12. 33 rows. |
| Other `quikspec` columns | No change. |
| `quikplan` | No change. Product was already 13, 13, and 12. |
| Other tables | Not rewritten. |

---

## 2. Row Count Comparison

`quikspec.csv` was written 2026-09-28 14:53. The other core tables were last written on 2026-09-27, or `quikridr.csv` at 13:26 for Issue 174, before this patch.

| Table | Before | After | Delta | OK? |
|---|---:|---:|---:|---|
| quikspec | 5,083 | 5,083 | 0 | Yes. |
| quikmstr | 5,083 | 5,083 | 0 | Yes. File not rewritten. |
| quikridr | 6,956 | 6,956 | 0 | Yes. File not rewritten by this issue. |
| quikprmh | 211,709 | 211,709 | 0 | Yes. File not rewritten. |
| quikplan | 142 | 142 | 0 | Yes. File not rewritten. |
| quikclid | 32,285 | 32,285 | 0 | Yes. File not rewritten. |
| quikclnt | 13,598 | 13,598 | 0 | Yes. File not rewritten. |

---

## 3. Non-Target Field Diff

The 33 before-rows were compared to the current file.

| Column | Rows changed | OK? |
|---|---:|---|
| RESRVCAT | 33 | Yes. `L` to 13 or 12. |
| VANISH | 0 | Yes. |
| VANISHDT | Not in the before snapshot as a changed field. Gold rows are still blank. | Yes. |
| RESSTATE | 0 | Yes. |
| SOR_POL | 0 | Yes. |
| MPOLICY | 0 | Yes. |

Category `L` is 0. Category 13 is 845. Category 12 is 541. Blank `SOR_POL` is 0. Every policy key is 11 characters.

---

## 4. Prior Issue Fix Regression

| Issue | Validator | Result |
|---|---|---|
| 175 | `validate_issue175_resrvcat.py` | PASS. L15=11, L16=2, L17 BASE=20. |
| 141 | `_validate_issue141_resrvcat.py` | PASS. 5,083 filled, 0 mismatches, 0 `ISWLFE`. Golds 03, 03, and 05. |
| 156 | `_validate_issue156_sor_pol.py` | PASS. 5,083 filled, 0 mismatches, 0 converted-key copies. |
| 2 / 25 | Policy key width on `quikspec` | PASS. All 5,083 keys are 11 characters. |
| 26 | `quikridr` premium | Not rewritten by this issue. File timestamp is the Issue 174 patch. |
| 145 | `_validate_issue145_vanish.py` | FAIL, and it is not from this change. The validator reads the 8/31 extract. Output is the 6/30 package. One policy, `9011085421C`, is vanish T because 6/30 billing reason is VB. On 8/31 that reason is PC. Vanish on the 33 Issue 175 rows did not change. |
| Resident state | `validate_quikspec_resident_state.py` | FAIL, same cut mismatch. Five policies match 6/30 and differ on 8/31: `9010441082C` ND vs MN, `9010790287C` KS vs NE, `9010806873C` SD vs SC, `9010815524C` FL vs IN, `9010933370C` IL vs NE. None of them is in the 33. |

---

## 5. Schema Integrity

| Check | Result |
|---|---|
| Field order | Same six columns. |
| Field types/lengths | Unchanged. `13` and `12` fit the two-character category. |
| Blank keys | No blank policy key. No blank source policy number. |

---

## 6. Batch / Fleet Checks

| Check | Result |
|---|---|
| Full batch | No. Targeted correction of 33 cells. |
| Plan product | `1L15GD` 13, `1L16GD` 13, `1L17SP` 12. Unchanged. |

---

## 7. Failures

None that this issue caused.

The vanish and resident-state failures compare this 6/30 package to the 8/31 extract. Do not change those six policies in this issue.

---

## 8. Recommendation

- [x] Advance to Closure / Ready for Client UAT
- [ ] Return to Development

Reload `QLA_Migration/Output/Test_Validation/quikspec.csv` and confirm the three products show reserve category 13, 13, and 12.
