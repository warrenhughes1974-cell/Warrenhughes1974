# Issue #2 — Resolution Summary

**Issue:** #2 — 11 Character Policy Number  
**Framework stage:** Closure Agent (G7)  
**Final status:** **Closed ✓**  
**Engine version:** v58.29  
**Closed date:** 2026-07-23  
**Owner:** Conversion (Warren)

---

## Resolution (issue log — paste-ready)

**Resolution:** QLAdmin policy numbers now keep the LifePRO source policy number with a trailing C and are right-justified to 11 characters (replacing the old strip-9 crosswalk and 10-character pad).

> Copy the line above into tracking sheets and client readouts. Long-form detail follows.

---

## Problem Statement

Active-QLA Testing required 11-character policy numbers. QLA tables were widened to 11, but conversion still emitted crosswalked 10-character keys (strip leading `9` + `C`, Issue #25 pad).

---

## Root Cause

**Category:** Mapping / key identity

Legacy Master_Crosswalk policy remap (`9010…` → `010…C`) plus Issue #25 width-10 formatting did not match the approved QLA identity (source + trailing `C`, width 11, right-justified).

---

## Resolution (long-form)

In v58.29, emit uses `format_qladmin_mpolicy`: normalize source `POLICY_NUMBER`, append `C`, right-justify to 11. Policy crosswalk Old→New is bypassed for `MPOLICY`/`MEMOKEY`. Parallel paths (claims, prmh, loan, benh, isrr, memo DBF C(11)) aligned. Full batch Validation + Regression PASS.

### Files changed

| File | Change |
|------|--------|
| `qla_core/normalize_utils.py` | Issue #2 formatter (width 11, source+`C`) |
| `app.py` / `QLA_Migration/app.py` | Skip policy CW on MPOLICY; v58.29 |
| `qla_core/quikplan_converter.py` | Skip MPOLICY CW (+ #99 ISWL tags in same tree) |
| `qla_core/quikmemo_converter.py` / `quikmemo_dbf_generator.py` | Source+`C`; MEMOKEY C(11) |
| `qla_core/quikloan_converter.py` / `quikbenh_loan_history_converter.py` | Source+`C` |
| `qla_core/quikisrr_loader.py` / `reinsurance_lookups.py` / `balancing.py` | Shared identity |
| `qla_core/issue78_quikclmp_recovery.py` | Reverse = strip trailing `C` |
| `tools/validators/validate_mpolicy_width.py` | Width 11 |
| `QLA_Migration/_validate_issue2_mpolicy.py` | Issue validator |
| `tools/validators/validate_issue_log_accountability.py` | `#2` IN_DATA; `#25` superseded WARN |
| `Issue_Log_Items/Issue_2/*` | Framework package |

### Rulebook changes

None (engine identity path).

---

## Evidence

| Artifact | Path | Result |
|----------|------|--------|
| Intake | `Issue_2_Intake_Summary.md` | — |
| Planning | `Issue_2_Planning_Report.md` | — |
| Dependency Gate | `Issue_2_Dependency_Gate.md` | **PASS** |
| Risk | `Issue_2_Risk_Review_Report.md` | **GO** |
| Implementation | `Issue_2_Implementation_Notes.md` | v58.29 |
| Validation | `Issue_2_Validation_Report.md` | **PASS** (full batch) |
| Regression | `Issue_2_Regression_Report.md` | **PASS** |

### Output accountability gate (G7)

| Check | Evidence | Status |
|-------|----------|--------|
| Issue validator on full Output | `python QLA_Migration/_validate_issue2_mpolicy.py` | **PASS** |
| Width validator | `tools/validators/validate_mpolicy_width.py` | **PASS** (322,084 fields) |
| Accountability | `validate_issue_log_accountability.py` → `#2` | **IN_DATA** (post-update) |
| Test_Validation | 15 policy-keyed tables published | Done |

---

## Trace Policy Confirmation

| LifePRO | Expected QLA | Match |
|---------|--------------|-------|
| `9010143726` | `9010143726C` | Yes |
| `9010148272` | `9010148272C` | Yes |
| `901222DC` | `  901222DCC` | Yes |
| `9014059` | `   9014059C` | Yes |
| `9014100C` | `  9014100CC` | Yes |

---

## Explicitly Not Changed

- Issue #26 MPREM / MMODPREM mapping logic  
- Product/entity crosswalk (non-policy)  
- Premium amounts, statuses, plan codes (aside from key rewrite)  
- Issue #25 width-10 contract — **superseded** (documented)

---

## Residual risks / follow-ups

- UAT bookmarks must use new keys (`901…C`, not `010…C`).  
- Stock Issue #26 validator still hardcodes old `010…C` samples / dated extracts — remapped checks PASS; script retarget optional follow-up.  
- quikbenh row count −556 vs pre-#2 merge baseline explained in Regression (old-key merge).  
- Network machines: pull + full batch (Output is gitignored).

---

## Rollback

Revert v58.29 Issue #2 commits; restore prior `format_qladmin_mpolicy` width-10 + policy crosswalk apply; re-batch.

---

## Git release

| Item | Value |
|------|-------|
| Branch | `issue-34-pr7-quikisrr` |
| Commit | `1c7fc0a39507966e64c8c71ae5cf7aa34feb24d4` |
| Remote | `origin` |
| Engine | **v58.29** |

**Network rollout:** `git pull` → run full batch / `run_converter.bat` at v58.29 → load `QLA_Migration/Output/` (or `Test_Validation/` for partial UAT).
