# Issue #156 — Resolution Summary

**Issue:** #156 — Add Source Policy Number to User Defined  
**Framework stage:** Closure Agent  
**Final status:** **Closed**  
**Engine version:** v59.02  
**Closed date:** 2026-08-26  
**Owner:** Conversion  
**Validation:** **PASS** (client UAT 2026-08-26)  
**Regression:** **PASS**  
**Accountability:** **IN_DATA** (issue validator PASS on full `QLA_Migration/Output/`)  
**Release smoke:** **PASS** / **RELEASE_OK** (`python tools/validators/validate_release_closed_issues.py --smoke-only`; `#156 quikspec SOR_POL` PASS)

---

## Resolution (issue log — paste-ready)

08/26/2026 Resolution: The original LifePRO policy number now loads on the policy User Defined field, while QLAdmin still uses the number with C. Examples: 9011050114C source 9011050114; 9010143726C source 9010143726; 901122D991C source 901122D991.

---

## Problem Statement

Eric asked that the original LifePRO policy number be stored as a QLAdmin User Defined value. Conversion only had the Issue #2 key (`source + C`) on `MPOLICY`.

---

## Root Cause

**Category:** [x] Scope gap  [ ] Mapping error  [ ] Source extract defect  [ ] Client definition

`SOR_POL` exists on the client QuikSpec template but was not on the converter schema. A Rule Book row alone could not emit it. The original `POLICY_NUMBER` was still on the PPOLC source row at map time.

---

## Resolution

Added `SOR_POL` to the QuikSpec emit schema and mapped `PPOLC.POLICY_NUMBER` with `SKIP_TRANSLATION`. The `C` suffix is applied only to `MPOLICY`. Template field is Character 10 so ML/D/FG keys load.

### Files changed

| File | Change |
|------|--------|
| `app.py` / `QLA_Migration/app.py` | v59.02 schema |
| `validation_config/schema_manifest.json` | `SOR_POL` |
| `QLA_Migration/Configs/Sync_Rulebook_quikspec.csv` | `POLICY_NUMBER → SOR_POL` |
| `QLA_Migration/_validate_issue156_sor_pol.py` | Fail-closed validator |
| `tools/validators/validate_release_closed_issues.py` | `SMOKE_JOBS` |
| `tools/validators/validate_issue_log_accountability.py` | `#156` job |
| `Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md` | Closed row + high-risk smoke |

### Rulebook changes

| Rulebook | Before | After |
|----------|--------|-------|
| `Sync_Rulebook_quikspec.csv` | No `SOR_POL` | `POLICY_NUMBER,SOR_POL,,SKIP_TRANSLATION` |

---

## Evidence

| Artifact | Path |
|----------|------|
| Implementation notes | `Issue_156_Implementation_Notes.md` |
| Validation report | `Issue_156_Validation_Report.md` PASS |
| Regression report | `Issue_156_Regression_Report.md` PASS |
| Validation script | `QLA_Migration/_validate_issue156_sor_pol.py` |
| Completed Issues guide | row 156 |

### Output accountability gate (G7)

| Gate | Result |
|------|--------|
| Issue validator PASS on full `QLA_Migration/Output/` | **PASS** |
| Accountability IN_DATA for #156 | **IN_DATA** (validator job) |
| Published to `Output/Test_Validation/` | `quikspec.csv` |
| Always-on smoke in `SMOKE_JOBS` | `#156 quikspec SOR_POL` |

---

## Trace Policy Confirmation

| Policy | Client expected | Emitted | Match |
|--------|-----------------|---------|-------|
| 9011050114C | 9011050114 | 9011050114 | Yes |
| 9010143726C | 9010143726 | 9010143726 | Yes |
| 901122D991C | 901122D991 | 901122D991 | Yes |
| 901ML8487C | 901ML8487 | 901ML8487 | Yes |

---

## Explicitly Not Changed

- Issue #2 `MPOLICY` (source + C, width 11)
- `VANISH` / `VANISHDT` / `RESSTATE` / `RESRVCAT`
- Other conversion tables

---

## Residual risks

None for Character `SOR_POL` C(10). All current source values are 10 characters or less.

---

## Rollback

1. Remove `SOR_POL` from `TABLE_SCHEMAS` and the QuikSpec rulebook.
2. Re-emit `quikspec.csv` without the column.
3. Keep the client template field if they still want it blank.
