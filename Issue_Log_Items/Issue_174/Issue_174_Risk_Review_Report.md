# Issue 174 — Risk Review Report

**Issue:** 174 — Pending Death Benefit Policies
**Framework stage:** Risk Agent
**Status:** Conditional Go
**Fallback simulated:** Skip inherit of status 50 only. Paid-up addition on a status-50 policy keeps its own Active status.
**Generated:** 2026-09-28
**Agent:** Cursor Grok 4.5

**Status note:** Risk analysis only. No production code, rulebook, or Output change.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — The change is 17 coverage rows on the current package, header stays 50, and real deaths stay terminal. Development is approved only if status 50 is accepted as an exception to Closed #160, #60's paid-up-addition rule, and #108's "every status 50-and-above ends the coverage" guidance. That acceptance is the Development approval.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|---|---|---|---|
| `quikmstr.MSTATUS` when contract is `S`/`DP` | 50 | 50 | **No** |
| `quikridr.MPHSTAT` phase 1 when that policy status is 50 | Copied 50 | Benefit `A` → 22 | **Yes** |
| `quikridr.MSAVESTAT` on those rows | 50 (mirror) | 22 (mirror) | **Yes** |
| Paid-up addition on a status-50 policy | 50, via #160 after the base was forced to 50 | Own `A` → 22 | **Yes** |
| `quikmstr.MSTATUS` and phase when contract is `T`/`DC` | 53, phase inherits 53 | Same | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|---|---|---|
| `MPOLICY` padding | #25 | **No** |
| `quikridr.MPREM` | #26 | **No** |
| `quikmstr` mode premium | #26 / #139 | **No** |
| Plan, units, dates, beneficiary rows | existing | **No** |
| Statuses other than 50 | existing inherit | **No** |

---

## 3. Repo References

| Location | Role |
|---|---|
| `app.py` and `QLA_Migration/app.py`, phase-1 inherit | Copies policy status onto phase 1 unless it is blank, 11, 22, or ACTIVE |
| Same files, `_apply_pua_rider_inheritance` | #60 sets PUA to 41 when base < 50. #160 copies the base when base ≥ 50 |
| Same files, `_apply_quikridr_v5796_defaults` | Blank `MSAVESTAT` copies `MPHSTAT` |
| `qla_core/quikmstr_active_phase_status.py` | Same inherit list. Decides whether #49 rewrites the header |
| `Master_Value_Translation.csv` | `ST_S_DP` → 50, `A` → 22, `ST_T_DC` → 53. No row change |

---

## 4. Population Analysis

Current Output is the 6/30 package. Every `MSTATUS=50` policy is `S`/`DP` on that extract, and every convertible benefit is `A`/`DP`.

| Metric | Count |
|---|---:|
| Policies in current Output | 5,083 |
| Policies with header 50 | 16 |
| `quikridr` rows on those policies | 17 |
| Rows whose `MPHSTAT` / `MSAVESTAT` would change 50 → 22 | 17 |
| Headers that would change | 0 |
| `S`/`DP` policies on the 8/31 extract | 11 |
| Phase rows that would change on an 8/31 batch | 12 |
| Of the 6/30 sixteen, already `T`/`DC` on 8/31 | 10 |

### 6/30 rows that change (all of them)

Phase 1 unless noted. Plan is the current Output plan. Both `MPHSTAT` and `MSAVESTAT` go from 50 to 22. Header stays 50.

| Policy | Plan | Phase |
|---|---|---|
| 9011085655C | 1659CR | 1 — Brianna's example |
| 9010521213C | 17085M | 1 |
| 9010521213C | 1708PA | 2 paid-up addition |
| 9010741334C | 1659C2 | 1 |
| 9010772919C | 1659C2 | 1 |
| 9010797197C | 1658C1 | 1 |
| 9010835310C | 1659CR | 1 |
| 9010841124C | 1659CR | 1 |
| 9011085270C | 5L0110 | 1 |
| 9011112998C | 1L10SO | 1 |
| 9011176240C | 1L10SO | 1 |
| 9011177866C | 1L10SO | 1 |
| 9011190416C | 1L10SR | 1 |
| 9011194146C | 1L10SO | 1 |
| 9011248017C | 1L14SC | 1 |
| 9011262791C | 1L14SC | 1 |
| 9015000239C | 17CSI5 | 1 |

8/31 pending-death set (header 50, phases 22 on a future batch): `9010439999C` (base and paid-up addition), `9010772919C`, `9010797197C`, `9010803420C`, `9010969653C`, `9011085655C`, `9011142296C`, `9011177866C`, `9011214229C`, `9011248017C`, `9015000239C`.

---

## 5. Fallback Recommendation

| Option | Rows | Assessment |
|---|---:|---|
| A. Do not copy status 50 onto any phase. PUA on that policy keeps its own Active status. Header stays 50. | 17 now, 12 on 8/31 | **Recommended** |
| B. Change phase 1 only, and let #60 set the paid-up addition to 41 | 16 phase-1 rows, plus one PUA 50 → 41 | Reject. Brianna's working case is phase 22. Paid Up is a different status and can fail the same sync check. |
| C. Force every current Output status-50 policy to phase 22 forever, including after it becomes a real death | 16 policies stuck | Reject. Ten of them are already `T`/`DC` on 8/31 and must go to 53. |

**Recommended fallback:** Option A.

Header proof for Option A: if phase 1 is simulated as 22, `select_mstatus_from_active_phase` sees an active first phase and returns the provisional status unchanged. Provisional `S`/`DP` is 50, so the header stays 50. That holds for the single-phase policies and for `9010439999C` / `9010521213C`, whose paid-up addition is also Active. #49 does not get a chance to replace 50.

---

## 6. Trace Policies

| Policy | Before | Proposed | Pass? |
|---|---|---|---|
| 9011085655C | Header 50, phase 50. LifePRO benefit Active. | Header 50, phase 22 | Yes — Brianna's shape |
| 9010521213C on 6/30 | Header 50, base 50, PUA 50 | Header 50, base 22, PUA 22 | Yes — on this cut only |
| 9010521213C on 8/31 | Contract is now `T`/`DC` | Header 53, phases inherit 53 | Yes — must not stay 22 |
| 9010439999C on 6/30 Output | Header 22, phase 22, PUA 41 | Unchanged until an 8/31 batch | Yes |
| 9010439999C on 8/31 | `S`/`DP`, both benefits Active | Header 50, both phases 22 | Yes |
| 9010741334C on 8/31 | `T`/`DC`, benefit `T` | Status 53 inherited onto the phase | Yes — control |

---

## 7. Largest Changes

Not a money field. The status move is the same on every affected row: 50 → 22. No row moves further than that.

---

## 8. Material Calculation Impact

Intentional. Beneficiary edit and, per Eric, return of premium depend on QLAdmin seeing an active coverage under a pending-death policy. We are not loading a new premium or a return-of-premium amount. Surrender, death, lapse, and maturity calculations are outside the status-50 exception.

---

## 9. Prior Fix Preservation

| Check | Result |
|---|---|
| Issue #25 MPOLICY padding | Preserved |
| Issue #26 MPREM | Preserved |
| Issue #13 / #59 status translation | Preserved. `S`/`DP` stays 50. `T`/`DC` stays 53. `9010521213C` is allowed to move from 50 to 53 when the extract does. |
| Issue #49 header override | Preserved for real terminal bases. For status 50, the first phase is Active, so the override does not fire and the header stays 50. |
| Closed #160 | **Exception, status 50 only.** A pending-death PUA stays 22 instead of copying a base that we will no longer set to 50. Surrendered, death, matured, and lapsed bases still copy onto the PUA. |
| #60 PUA → 41 | **Exception, status 50 only.** Does not run when the policy is 50. |
| #108 terminate all coverages at ≥50 | **Exception, status 50 only.** |
| #133-PS header stays 50 | Preserved. `9010439999C` header remains 50. Its phases become 22 instead of 50. The existing unit test feeds a synthetic phase status of `50` and still passes. |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] `9011085655C`: `MSTATUS` 50, phase 1 `MPHSTAT` 22, `MSAVESTAT` 22. `MPREM` unchanged.
- [ ] The other fifteen 6/30 status-50 policies: header still 50, every phase 22.
- [ ] A `T`/`DC` policy (8/31 `9010741334C`, or any current status 53): header and phase stay terminal. Not 22.
- [ ] A surrendered policy (status 55) and a lapsed policy (54): phases unchanged.
- [ ] `9010439999C` after an 8/31 batch: header 50, both phases 22. On the current 6/30 Output it stays 22 / 41 until that batch.
- [ ] `9010521213C`: 50 and phases 22 on a 6/30 rerun; 53 and terminal phases on an 8/31 batch.
- [ ] Issue #49 and #59 validators still pass.
- [ ] #133 unit check (synthetic base status 50) still passes. New check: provisional 50 plus benefit `A` keeps header 50 and simulated phase 22.
- [ ] No `MPREM`, unit, plan, or `MPOLICY` diffs on the 17 rows.

---

## 11. Recommended Development Agent Task

1. Both `app.py` copies: do not copy policy status 50 onto phase 1.
2. Both copies: when provisional policy status is 50, `_apply_pua_rider_inheritance` does not change `MPHSTAT`.
3. `qla_core/quikmstr_active_phase_status.py`: add `50` to `PHASE1_INHERIT_BLOCK`.
4. Bump `APP_VERSION` from `v59.25` in both `app.py` files.
5. Do not edit `Master_Value_Translation.csv`, premium logic, or Output by hand.
6. After approval and a batch, the validator in section 10 is the proof. Update the Closed #160 guide row in the same change so it no longer says a pending-death PUA follows status 50.

---

## Appendix

- Population: `Issue_Log_Items/Issue_174/evidence/issue174_pending_death_population.csv`
- Before-state: current `QLA_Migration/Output/quikmstr.csv` and `quikridr.csv` (valuation 20260630)
