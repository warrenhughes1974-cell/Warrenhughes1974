# Issue 174 — Regression Report

**Issue:** 174 — Pending Death Benefit Policies
**Framework stage:** Regression Agent
**Engine version:** v59.26
**Baseline:** `Issue_Log_Items/Issue_174/evidence/quikridr_issue174_before_rows.csv` and the 2026-09-28 line compare (6,957 lines, 17 differed)
**Output directory:** `QLA_Migration/Output/`
**Generated:** 2026-09-28
**Verdict:** **PASS**

No full rebatch. The current package is the 6/30 cut. Only `quikridr.csv` was rewritten, and only on the 17 pending-death rows.

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|---|---|
| `quikridr.MPHSTAT` and `MSAVESTAT` on status-50 policies | 50 → 22. 17 rows. |
| `quikmstr.MSTATUS` | No change. Stays 50. |
| Other tables | Not rewritten. |
| Other `quikridr` columns | No change. |

---

## 2. Row Count Comparison

Untouched tables were last written 2026-09-27, before this fix. `quikridr.csv` was written 2026-09-28. Its row count did not change.

| Table | Before | After | Delta | OK? |
|---|---:|---:|---:|---|
| quikmstr | 5,083 | 5,083 | 0 | Yes. File not rewritten. |
| quikridr | 6,956 | 6,956 | 0 | Yes. |
| quikprmh | 211,709 | 211,709 | 0 | Yes. File not rewritten. |
| quikplan | 142 | 142 | 0 | Yes. File not rewritten. |
| quikclid | 32,285 | 32,285 | 0 | Yes. File not rewritten. |
| quikclnt | 13,598 | 13,598 | 0 | Yes. File not rewritten. |

---

## 3. Non-Target Field Diff

The 17 before-rows were compared to the current file on all 40 columns.

| Table | Column | Rows changed | OK? |
|---|---|---:|---|
| quikridr | MPHSTAT | 17 | Yes. 50 → 22. |
| quikridr | MSAVESTAT | 17 | Yes. 50 → 22. |
| quikridr | every other column | 0 | Yes. |
| quikmstr | all | 0 | Yes. |

The line compare at patch time found 17 differing lines out of 6,957 and no others. `9011085655C` phase 1 is status 22, premium 52.656708, units 5.00000, plan 1659CR.

---

## 4. Prior Issue Fix Regression

### Issue #25 / #2 — Policy key width

| Check | Result |
|---|---|
| Every `quikridr.MPOLICY` | PASS. All 6,956 keys are 11 characters (source number plus C). |
| Blank `MRIDRID` | PASS. 0 blank. |

### Issue #26 — MPREM

| Check | Result |
|---|---|
| `validate_issue26_mprem.py` | Not runnable. It still looks for the 20260530 extracts, which are not in Source. |
| MPREM on the 17 touched rows | PASS. `MPREM` is not in the diff. Gold `9011085655C` remains 52.656708. |

### Other Closed rows that share `quikridr`

| Issue | Validator | Result |
|---|---|---|
| 174 | `validate_issue174_pending_death_phase.py` | PASS. 16 `S`/`DP` policies, header 50, phases 22. A `T`/`DC` control is still 53/53. |
| 49 | `validate_issue49_mstatus.py --simulate-only` | PASS. 35 overrides, all to 22. |
| 133 | `validate_issue133_pua_header_status.py` | PASS. Header for `9010439999` stays 50 in the source check. Output WARN only: that policy is still Active on the 6/30 package. |
| 139 | `validate_issue139_policy_fee_suppression.py` | PASS. ISWL fees 0. Gold `9010713704C` premium 41.71. |
| 152 | `validate_issue152_mprem_rider.py` | PASS. 33 in-scope rows. |
| 159 | `validate_issue159_muwclass_plan_aware.py` | PASS. |
| 59 | `validate_issue59_mstatus.py` | FAIL, and it is not from this change. `quikmstr.csv` was not rewritten (timestamp 2026-09-27). The validator reads the 8/31 extract and expects `9010521213C` = 53 and `901ML8250C` = 53. This Output is the 6/30 package, where `9010521213C` is still Suspended/Death Pending, so 50 is the correct status for this cut. `901ML8250C` is still 22. An 8/31 batch is what moves the death-claim policy to 53. |
| 160 | `validate_issue160_pua_terminal_status.py` | Not run to completion. The pre-remap archive file is not in this workspace. |

---

## 5. Schema Integrity

| Check | Result |
|---|---|
| Field order | Same 40 `quikridr` columns as the before snapshot. |
| Field types/lengths | Unchanged. No schema edit. |
| Blank MRIDRID | 0. |
| Formatting | The 6,939 untouched lines were byte-identical at patch time. |

---

## 6. Batch / Fleet Checks

| Check | Result |
|---|---|
| Full batch | No. Targeted `quikridr` correction of the 17 rows only. |
| `validate_output.py` | Not run. |
| Audit anomalies | None on the touched rows. |

---

## 7. Failures

None that this issue caused.

The Issue 59 failure is a 6/30 Output versus 8/31 extract mismatch. It was already true before `quikridr` was patched. Do not change those policy statuses in this issue.

---

## 8. Recommendation

- [x] Advance to Closure / Ready for Client UAT
- [ ] Return to Development

Brianna can reload `QLA_Migration/Output/Test_Validation/quikridr.csv` and confirm `9011085655C` edits the beneficiary with the policy at 50 and the phase at 22. Return of premium is still a QLAdmin calculation, not a loaded amount.
