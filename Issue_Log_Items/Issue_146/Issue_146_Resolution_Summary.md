# Issue #146 — Resolution Summary

**Issue:** #146 — Non-VB Unit Reductions  
**Framework stage:** Closure Agent  
**Final status:** **Closed**  
**Engine version:** v59.03  
**Closed date:** 2026-08-26  
**Owner:** Conversion  
**Validation:** **PASS**  
**Regression:** **PASS**  
**Accountability:** issue validator PASS on full `QLA_Migration/Output/`  
**Release smoke:** `#146 PC/former-vanish 0561s out of ISRR`

---

## Resolution (issue log — paste-ready)

08/26/2026 Resolution: For 20 former-vanish policies, old premium-from-fund withdrawals are no longer loaded as surrenders, so anniversary will not cut the units. Real partial surrenders stay. Examples: 9011077629 stays 5 units; 9010817956 stays 5 units; 9010808831 stays 25 units.

---

## Problem Statement

After the VB vanish book was fixed, QLAdmin still cut units on leftover policies whose 0561 history was annual premium taken on the anniversary. LifePRO never reduced those units.

---

## Root Cause

**Category:** [x] Scope gap  [ ] Mapping error  [ ] Source extract defect  [x] Client definition

#145B excluded 0561s only when `BILLING_REASON=VB`. These 20 policies carry the same vanish-premium fingerprint but are coded PC (or blank on 9010808831) after New Era moved them off vanish.

---

## Resolution

Exclude the locked 20-policy allowlist from the #34 0561 emit and strip the matching QuikIsrr / PS- / phase-0 / type-8 rows from current Output. Do not set VANISH. Keep 9010761639 ($271) and 9010760840 ($716.40).

### Files changed

| File | Change |
|------|--------|
| `qla_core/issue146_pc_isrr.py` | Allowlist |
| `qla_core/quikisrr_loader.py` | Filter after #145B |
| `app.py` / `QLA_Migration/app.py` | v59.03 |
| `tools/validators/validate_issue146_pc_isrr.py` | Fail-closed smoke |

---

## Evidence

| Artifact | Path |
|----------|------|
| Validation | `Issue_146_Validation_Report.md` PASS |
| Regression | `Issue_146_Regression_Report.md` PASS |
| Apply | `evidence/issue146_apply_summary.json` |
| Guide | row 146 |

### Output accountability gate (G7)

| Gate | Result |
|------|--------|
| Issue validator PASS on full Output | **PASS** |
| #145B still PASS | **PASS** |
| Published to Test_Validation | quikisrr / quikclms / quikclmp / quikbenh |
| Always-on smoke | `#146 PC/former-vanish 0561s out of ISRR` |

---

## Trace Policy Confirmation

| Policy | Expected | Result |
|--------|----------|--------|
| 9011077629C | 0 ISRR; MUNIT 5 | Yes |
| 9010817956C | 0 ISRR; MUNIT 5 | Yes |
| 9010808831C | 0 ISRR; MUNIT 25 | Yes |
| 9010761639C | 1 / $271 | Yes |
| 9010760840C | 2 / $716.40 | Yes |
