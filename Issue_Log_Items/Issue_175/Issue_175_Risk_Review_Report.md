# Issue 175 — Risk Review Report

**Issue:** 175 — Res Cat Unique Field
**Framework stage:** Risk Agent
**Status:** Conditional Go
**Fallback simulated:** Coverage-id exception, read-only, against current Output
**Generated:** 2026-09-28
**Agent:** Cursor Grok

**Status note:** Risk analysis only. No production code was changed.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Change 33 reserve categories from `L` to 13 or 12. Development waits on Warren’s written OK to make that exception to Closed Issue 141.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|---|---|---|---|
| quikspec.RESRVCAT for L15 (`1L15GD`) | L | 13 | Yes. 11 policies. |
| quikspec.RESRVCAT for L16 (`1L16GD`) | L | 13 | Yes. 2 policies. |
| quikspec.RESRVCAT for L17 BASE (`1L17SP`) | L | 12 | Yes. 20 policies. |
| quikspec.RESRVCAT for every other coverage | LifePRO product type | Same | No. 5,050 policies. |
| quikplan.PRODUCT on the three plans | 13 / 13 / 12 | Same | No. |
| Other quikspec columns | Current values | Same | No. |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|---|---|---|
| quikmstr modal premium | PPOLC | **No** |
| quikridr.MPREM | Issue 26 | **No** |
| MPOLICY | Issue 2 / 25 | **No** |
| quikplan | Plan setup | **No** |
| quikspec VANISH, VANISHDT, RESSTATE, SOR_POL | Existing spec row | **No** |

---

## 3. Repo References

| Location | Role |
|---|---|
| `qla_core/quikspec_resrvcat.py` | The only writer of `RESRVCAT` |
| `QLA_Migration/_validate_issue141_resrvcat.py` | Fails today if these 33 rows leave `L` |
| `tools/validators/validate_release_closed_issues.py` | Runs the Issue 141 smoke |
| `app.py`, `QLA_Migration/app.py` | Call the filler during batch |

---

## 4. Population Analysis

Read from current `QLA_Migration/Output/quikspec.csv` joined to phase-1 plan and 6/30 PPBEN seq 1.

| Metric | Count |
|---|---:|
| quikspec rows | 5,083 |
| Rows that would change | 33 |
| Rows unchanged | 5,050 |
| Blank reserve categories | 0 |
| Reserve category `L` today | 33 |
| Reserve category `L` after | 0 |

| Plan | LifePRO coverage | Rows | Now | After |
|---|---|---:|---|---|
| 1L15GD | L15 | 11 | L | 13 |
| 1L16GD | L16 | 2 | L | 13 |
| 1L17SP | L17 BASE | 20 | L | 12 |

Seq-1 counts for `DISCHO20 B`, `DISCHO25`, `DISCHO80`, and `L16POLFEE` are 0. Those product-type `L` coverages are not in this change.

---

## 5. Fallback Recommendation

| Option | Rows changed | Assessment |
|---|---:|---|
| A. Map L15 and L16 to 13, and L17 BASE to 12, inside the existing filler | 33 | Recommended |
| B. Copy `quikplan.PRODUCT` onto every policy | 2,268 would become `ISWLFE` | Reject |
| C. Replace every product type `L` with the plan product | 33 today, and any future discount base would move too | Reject. The three coverage ids are the client list. |

**Recommended rule:** Option A.

---

## 6. Trace Policies

| Policy | Before | Proposed | Pass? |
|---|---|---|---|
| 9011210337C | L | 13 | Yes, if approved |
| 9011216680C | L | 13 | Yes, if approved |
| 9011217014C | L | 12 | Yes, if approved |
| 9010143726C | 03 | 03 | Must stay |
| 9010148272C | 03 | 03 | Must stay |
| 9010713704C | 05 | 05 | Must stay |

On the three target traces, vanish stays `F`, resident state stays KY / IN / LA, and `SOR_POL` stays the source number.

---

## 7. Largest Changes

This is a category code, not an amount. Every change is the same size: one character `L` becomes `13` or `12`. No premium delta.

---

## 8. Material Calculation Impact

QLAdmin uses this code as the policy reserve category. The plan product code is already 13 or 12, so the policy field is being brought in line with the plan. No rate, reserve factor, or premium table changes.

---

## 9. Prior Fix Preservation

| Check | Result |
|---|---|
| Issue 25 / Issue 2 policy key | Preserved. Width 11 on all 5,083 rows. No key edit. |
| Issue 26 premium | Preserved. `quikridr` not edited. |
| Issue 99 ISWL tags | Preserved. Plan product is not copied. |
| Issue 141 other categories | Preserved for 5,050 rows. The 33-row exception conflicts with the closed “keep L” sentence and must be approved before code. |
| Issue 156 / 145 / 132 | Preserved. Same row, other columns unchanged. |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] 9011210337C reserve category 13. Vanish F. State KY. Source policy 9011210337.
- [ ] 9011216680C reserve category 13. State IN.
- [ ] 9011217014C reserve category 12. State LA.
- [ ] All 11 `1L15GD` and both `1L16GD` are 13. All 20 `1L17SP` are 12.
- [ ] Reserve category `L` count is 0. No other category count moves except 13 (+13) and 12 (+20).
- [ ] 9010143726C and 9010148272C stay 03. 9010713704C stays 05. No `ISWLFE` on `RESRVCAT`.
- [ ] `quikspec` stays 5,083 rows and the same six columns. `quikplan` product on the three plans stays 13 / 13 / 12.
- [ ] Issue 141 validator passes with the exception. Issue 175 validator fails if any of the 33 revert to `L`.

---

## 11. Recommended Development Agent Task

1. Add the three-coverage map in `qla_core/quikspec_resrvcat.py`.
2. Set those 33 `RESRVCAT` values in current Output. Do not rewrite the rest of the file’s columns.
3. Teach the Issue 141 validator the exception. Add `tools/validators/validate_issue175_resrvcat.py`. Do not register the smoke until closure.
4. If `app.py` changes, bump both copies from v59.26 to v59.27.
5. Do not change rulebooks, `quikplan`, premium, or any reserve category outside L15, L16, and L17 BASE.

---

## Appendix

- Population: `Issue_Log_Items/Issue_175/evidence/issue175_resrvcat_population.csv`
- Planning: `Issue_175_Planning_Report.md`
- Gate: `Issue_175_Dependency_Gate.md` — PASS
