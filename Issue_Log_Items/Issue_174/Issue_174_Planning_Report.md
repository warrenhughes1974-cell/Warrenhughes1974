# Issue 174 — Planning Report

**Issue:** 174 — Pending Death Benefit Policies
**Framework stage:** Planning Agent
**Status:** Planning
**Generated:** 2026-09-28
**Agent:** Cursor Grok 4.5 (Intake through Risk chain)

---

## 1. Executive Finding

Brianna is right about the load. On a Suspended / Death Pending contract, LifePRO leaves the benefit Active. Conversion translates the contract to policy status 50, then copies that 50 onto the coverage. QLAdmin wants the policy at 50 and the coverage at 22. The copy is the defect.

The current Output is the 6/30 package. All 16 policies at status 50 on that package are `S`/`DP`, and every benefit is still `A`/`DP`. Sixteen phase-1 rows and one paid-up-addition row are status 50. Proposed result: header stays 50, those 17 phase rows become 22.

Do not apply this to real deaths. On the 8/31 extract, 10 of those 16 have already moved to `T`/`DC` (status 53). They must keep a terminal phase. The rule is "do not copy status 50," not "every policy that was 50 on 6/30 stays Active."

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File | In Source/? | Row grain |
|---|---|---|---|
| PPOLC | `QLA_Migration/Source/PPOLC_PolicyMaster_Extract_20260630.csv` | Yes | One row per policy. This is the extract behind current Output. |
| PPOLC | `QLA_Migration/Source/PPOLC_PolicyMaster_Extract_20260831.csv` | Yes | Same layout. Later cut. Not what Output was built from. |
| PPBEN | `PPBEN_PolicyBenefit_Extract_20260630.csv` and `_20260831.csv` | Yes | One row per benefit. |

### Fields that decide this issue

| Field | Meaning on these policies |
|---|---|
| `CONTRACT_CODE` + `CONTRACT_REASON` | `S` + `DP` → translation `ST_S_DP` → **50**. `T` + `DC` → `ST_T_DC` → **53**. |
| `PPBEN.STATUS_CODE` | `A` on every pending-death benefit in both extracts. Bare map `A` → **22**. |
| `PPBEN.STATUS_REASON` | `DP`. The rider rulebook does not read it. |
| `BENEFIT_TYPE` | `BA` or `BF` on the base. `PU` on one paid-up addition per cut. |

`D` / `PND` (`ST_D_PND` → 50) does not occur on either extract.

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | What it is | Change? |
|---|---|---|---|
| `quikmstr` | `MSTATUS` | Policy status. 50 = Death Claim Pending. | **No.** Stays 50. |
| `quikridr` | `MPHSTAT` | Coverage phase status. | **Yes.** 50 → 22 on these phases. |
| `quikridr` | `MSAVESTAT` | Saved status. Blank save fields copy `MPHSTAT`. | **Yes,** because it mirrors `MPHSTAT`. |

Schema order is already in `app.py` (`quikridr` header list). No new field.

**Where 50 is written onto the phase** (`QLA_Migration/app.py` and root `app.py`, same block):

Phase 1 copies the policy status when that status is not blank, 11, 22, or the word ACTIVE. Status 50 is copied. The same idea is in `qla_core/quikmstr_active_phase_status.py` (`PHASE1_INHERIT_BLOCK`) and drives whether Issue #49 rewrites the header.

`MSAVESTAT` is filled from `MPHSTAT` in `_apply_quikridr_v5796_defaults` when the save field is blank. Fixing `MPHSTAT` before that mirror fixes `MSAVESTAT`. Do not write `MSAVESTAT` on its own.

---

## 4. Required Source-to-Target Field Mapping

| LifePRO | Field | QLAdmin | Transformation | Change? |
|---|---|---|---|---|
| PPOLC | `S` / `DP` | `quikmstr.MSTATUS` | `ST_S_DP` → 50 | **No** |
| PPBEN | `STATUS_CODE=A` | `quikridr.MPHSTAT` phase 1 | Bare `A` → 22. Stop the later copy of policy status 50. | **Yes** |
| PPBEN | `STATUS_CODE=A` on `PU` | `quikridr.MPHSTAT` PUA | Keep 22. Do not let #60 force 41 or #160 force 50 while the policy is 50. | **Yes** |
| (mirror) | | `MSAVESTAT` | Copy final `MPHSTAT` when blank | Follows `MPHSTAT` |

### Proposed rule

1. When the policy status to inherit is **50**, do not copy it onto phase 1. Leave the benefit translation (22).
2. When the policy status is **50**, do not rewrite the paid-up addition to 41 (#60) or to the base's terminal status (#160). Leave its own Active translation (22).
3. Put **50** in `PHASE1_INHERIT_BLOCK` so the header simulation matches. Phase 1 then displays as Active, and `select_mstatus_from_active_phase` keeps the provisional header of 50. It does not promote the header to 22.
4. Status **53, 54, 55, 56, 57**, and the rest of the terminal list still copy onto phase 1. #160 still runs when the base phase is actually one of those.

### Fields that must remain unchanged

| Target | Current source | Touch? |
|---|---|---|
| `quikmstr.MSTATUS` for `S`/`DP` | `ST_S_DP` | **No** — stays 50 |
| `quikmstr.MSTATUS` for `T`/`DC` | `ST_T_DC` | **No** — stays 53, phase still inherits 53 |
| `quikmstr.MMODPREM` / mode premium | #26 / #139 | **No** |
| `quikridr.MPREM`, units, plan, dates | existing | **No** |
| `MPOLICY` padding | #25 | **No** |
| Non-50 terminal phases | existing inherit | **No** |

---

## 5. Open Client Questions

1. Return of premium is not a load field. After the phase is 22, Brianna confirms whether QLAdmin calculates it. No conversion work either way.
2. The paid-up-addition default in this plan is 22, matching her "phases stay 22." One policy on each extract. Development approval accepts that this carves #60 and #160 for status 50 only.

No other client question blocks the blueprint.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|---|---|
| Policy key | Unchanged. #25 padding. |
| Status values | Character codes already used: `50` and `22`. No new code. |
| Money / dates | Not in this change. |

---

## 7. Memo / Text / Special Handling

Not applicable.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` matches the Output key with a trailing `C` (`9011085655` → `9011085655C`).
2. No crosswalk change. No orphan handling.

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|---|---:|---|
| `S`/`DP` policies on 6/30 (current Output) | 16 | PPOLC. Matches the 16 `MSTATUS=50` rows exactly. |
| `quikridr` rows that change on that package | 17 | 16 phase-1 rows plus `9010521213C` phase 2. `MPHSTAT` and `MSAVESTAT` 50 → 22. |
| `S`/`DP` policies on 8/31 | 11 | Five new, ten of the 6/30 sixteen have become `T`/`DC`. |
| `quikridr` rows that would change on an 8/31 batch | 12 | 11 phase-1 rows plus `9010439999C` phase 2. |
| Policies that must not change | All non-50 statuses | Terminal inherit stays. |

---

## 10. Sample Trace

| Policy | Extract | Before | Proposed |
|---|---|---|---|
| `9011085655C` | 6/30 and 8/31, `S`/`DP`, benefit `A` | Header 50, phase 1 `1659CR` status 50 | Header 50, phase 1 status 22 |
| `9010521213C` | 6/30 `S`/`DP`, base and PUA both `A`. 8/31 this policy is `T`/`DC`. | Header 50, phase 1 and PUA both 50 | On a 6/30 rerun: header 50, both phases 22. On 8/31: header 53, phases follow 53. Do not freeze 50. |
| `9010439999C` | 8/31 `S`/`DP`, base and PUA both `A`. 6/30 Output is still Active 22 / PUA 41. | Not status 50 in current Output | On an 8/31 batch: header 50, both phases 22 |
| `9010741334C` | 6/30 `S`/`DP`. 8/31 `T`/`DC`, benefit `T`. | Header 50, phase 50 in the 6/30 Output | 6/30 rerun: phase 22. 8/31 batch: status 53 on the policy and the phase. |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|---|---|---|
| Leaving the phase Active makes #49 set the header back to 22 | High if the simulator is not updated | Add 50 to `PHASE1_INHERIT_BLOCK`. Active first phase keeps the provisional header. |
| #60 turns the PUA into Paid Up (41) once the base is 22 | Medium, one row | Skip that rewrite when the policy status is 50. |
| A blanket "status 50 policies in Output become 22" applied to a later cut | High | Key off the status being inherited (50), not off a frozen policy list. `T`/`DC` is 53 and still inherits. |
| Closed #160 / #108 treated 50 like every other terminal status | Approval | Named in Risk. Do not code until Development is approved with that exception. |
| #133 unit test uses a synthetic phase status of `50` | Low | That test still passes. Add a #174 case for provisional 50 plus benefit `A`. |

---

## 12. Recommended Risk Agent Prompt

Quantify the 17-row 6/30 change and the 12-row 8/31 change. Prove `T`/`DC` still inherits. Prove the header stays 50 when phase 1 is simulated as 22. Recommend Conditional Go pending acceptance of the #160 / #60 / #108 exception for status 50 only.

---

## 13. Recommended Development Task (do not implement)

1. In both `app.py` copies, stop phase-1 inherit when the policy status is 50.
2. In `_apply_pua_rider_inheritance`, when the provisional policy status is 50, leave the PUA's own `MPHSTAT`.
3. Add `50` to `PHASE1_INHERIT_BLOCK` in `qla_core/quikmstr_active_phase_status.py`.
4. Bump `APP_VERSION` in both `app.py` files (now `v59.25`).
5. Do not change `MSTATUS` translation, premium, units, or non-50 inherit.
6. Validator: the 16 current-package policies stay header 50 and phase 22; a `T`/`DC` control stays terminal; `9010439999C` header stays 50 with phases 22 once an 8/31 batch exists.

---

## Gate G1

- [x] Planning report published
- [x] Source and target documented
- [x] Trace table included
- [x] Open questions enumerated
- [x] Development task outlined, not executed
- [x] No code, rulebook, or Output changes
