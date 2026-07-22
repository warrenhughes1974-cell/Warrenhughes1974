# Issue #89 — Resolution Summary

**Issue:** #89 — Policy fee wipe after `quikridr`-only rebatch (`MANNLFEE` / modal fees)  
**Framework stage:** Closure Agent (G7)  
**Final status:** **Closed ✓**  
**Engine version:** v58.24  
**Closed date:** 2026-07-22  
**Owner:** Conversion (Warren)

---

## Resolution (issue log — paste-ready)

**Resolution:** Policy fees now load from LifePRO on every `quikridr` emit (including ridr-only rebatches), with a fail-closed guard so a blank fleet fee wipe cannot ship again; annual and modal fees are restored on fee-bearing policies.

> Copy the line above into tracking sheets and client readouts. Long-form detail follows.

---

## Problem Statement

Eric reported a policy fee issue on `010310404C`. LifePRO still had `POLICY_FEE` = $10.00, but QLAdmin Coverage Pol Fee was $0. Investigation found fleet-wide blank `MANNLFEE` / modal fees after the Issue #88 `quikridr`-only rebatch.

---

## Root Cause

**Category:** Mapping / emit-path gap (regression of #21C/#58)

Issue #21C loaded `_policy_fee_map` only on the `quikmstr` table path. Issue #58 derives modal fees from `MANNLFEE`. A `quikridr`-only rebatch never built the fee cache → blank annual fees → `#58` skipped all modal fees (`updated=0, zero_fee=5083`).

---

## Resolution (long-form)

In v58.24, the existing `quikridr` PPOLC read (Issue #88 billing mode) also builds the `#21C` policy-fee cache. After `#58` modal-fee apply, if the fee cache has ≥1,000 policies and base `MANNLFEE` populated count is 0, the run raises `RuntimeError` and does not write a wiped Output. Fee formulas unchanged.

### Files changed

| File | Change |
|------|--------|
| `app.py` / `QLA_Migration/app.py` | v58.24 — ridr fee cache + fail-closed guard |
| `tools/validators/validate_issue58_quikridr_modal_fees.py` | Numeric fee compare (10.44 vs 10.4400) |
| `QLA_Migration/_risk_review_issue89_policy_fee_cache.py` | Risk simulation (read-only) |
| `Issue_Log_Items/Issue_89/*` | Framework artifacts |

### Rulebook changes

None.

---

## Evidence

| Artifact | Path | Result |
|----------|------|--------|
| Intake | `Issue_89_Intake_Summary.md` | — |
| Planning | `Issue_89_Planning_Report.md` | — |
| Dependency Gate | `Issue_89_Dependency_Gate.md` | PASS |
| Risk | `Issue_89_Risk_Review_Report.md` | GO |
| Implementation | `Issue_89_Implementation_Notes.md` | v58.24 |
| Validation | `Issue_89_Validation_Report.md` | **PASS** |
| Regression | `Issue_89_Regression_Report.md` | **PASS** |

### Output accountability gate (G7)

| Check | Evidence | Status |
|-------|----------|--------|
| Issue validator on full Output | `validate_issue58_quikridr_modal_fees.py` | **PASS** |
| Fees in data | Base MANNLFEE>0 = **4,457**; Eric `010310404C`=10.0000 | **IN_DATA** |
| #88 preserved | `validate_issue88_mprem_unit_fallback.py` | **PASS** |
| Test_Validation | `Output/Test_Validation/quikridr.csv` | Published |

---

## Trace Policy Confirmation

| Policy | Expected | Emitted | Match |
|--------|----------|---------|-------|
| `010310404C` | MANNLFEE 10.00; MMTHBFEE 0.8702 | 10.0000 / 0.8702 | Yes |
| `010367131C` | MANNLFEE 10.44 + #58 modals | 10.4400 + goldens | Yes |
| `010779727C` | MPREM 5.8615 (#88) | 5.8615 | Yes |

Client UAT note: Coverage **Policy Fee** on a monthly bank-draft policy shows **0.8702** (modal), not annual 10.00 — correct QLAdmin display.

---

## Explicitly Not Changed

- Issue #26 / #88 MPREM mapping
- Issue #25 MPOLICY padding
- `#21C` / `#58` fee formulas (restore + harden only)
- `quikmstr.MMODEPREM` / plan *FEE columns

---

## Residual risks / follow-ups

None for this issue. Future ridr-only rebatches are safe for fees.

---

## Rollback

Revert `app.py` / `QLA_Migration/app.py` to v58.23 and re-emit `quikridr` (with `quikmstr` first if on old code).

---

## Git release

| Item | Value |
|------|-------|
| Commit | `cb0fb43` |
| Branch | `issue-34-pr7-quikisrr` |
| Push | Required for network batch machines |
| Output | gitignored — reload `Test_Validation/quikridr.csv` or rebatch after pull |
