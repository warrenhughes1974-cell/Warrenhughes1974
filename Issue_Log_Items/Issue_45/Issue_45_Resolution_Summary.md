# Issue #45 — Resolution Summary

**Issue:** #45 — Bank Draft Account Validation / PPPAC Account Fallback  
**Framework stage:** Closure Agent  
**Final status:** **Closed**  
**Engine version:** v57.77  
**Closed date:** 2026-07-12  
**Owner:** Conversion  
**Git:** commit pending record below · branch `issue-34-pr7-quikisrr`

---

## Resolution (issue log — paste-ready)

**Resolution:** Bank-draft policies missing PPACH account numbers now fall back to PPPAC `E_ACCOUNT_NUMBER`, with ABA from routing lookup or RelationshipNameAddress, and emit `MBANKNO` only when both account and routing resolve.

> Copy the line above into tracking sheets and client readouts. Long-form detail follows.

---

## Problem Statement

Eric asked whether `PPPAC_PACDetail_Extract_20260630` could be incorporated because it held `E_ACCOUNT_NUMBER` values not imported by the conversion. Bank-draft policies (`MBILLFRM=2`) used PPACH only; **763** policies had blank `MBANKNO` and were listed on `bank_draft_account_exceptions.csv`.

---

## Root Cause

**Category:** [x] Scope gap  [ ] Mapping error  [ ] Source extract defect  [ ] Client definition  [ ] QLAdmin behavior

PPACH history did not contain accounts for that exception fleet. PPPAC (current PAC detail) had usable accounts for **750** of **763** exceptions but no ABA column. Conversion never loaded PPPAC as a banking fallback.

---

## Resolution

PPACH remains the primary ABA+account source (Issue #21H). After the PPACH cache loads, PPPAC supplies account numbers only when PPACH has no usable account. ABA is recovered via `aba_routing_lookup.csv`, then RelationshipNameAddress (single distinct ABA only). `MBANKNO` emits as `ABA/ACCOUNT` only when both halves resolve; otherwise the policy still converts with blank `MBANKNO` and a refined exception (`MISSING_BANK_ACCOUNT` or `MISSING_ROUTING`).

### Files changed

| File | Change |
|------|--------|
| `app.py` / `QLA_Migration/app.py` | v57.77 — PPPAC fallback + Issue #45 gate |
| `QLA_Migration/_validate_issue45_pppac_fallback.py` | Source simulation validator |
| `QLA_Migration/_validate_issue45_output.py` | Output-level validator |
| `QLA_Migration/_regress_issue45.py` | Before/after regression |
| `Issue_Log_Items/Issue_45/*` | Framework artifacts G0–G7 |

### Rulebook changes

None.

### Engine changes

- PPPAC load via `find_extract('pppac')` after PPACH cache
- Usable-account rules (≥4 digits; reject masked/zero)
- ABA: lookup → RNA (reject multi-ABA ambiguity)
- Exception CSV columns: `PPPAC_ACCOUNT`, `ABA_SOURCE`, `BANK_SOURCE`

---

## Evidence

| Artifact | Path |
|----------|------|
| Source investigation | `Issue_45_Source_Investigation_Report.md` |
| Intake / Planning / Dependency / Risk | `Issue_45_*` in same folder |
| Implementation notes | `Issue_45_Implementation_Notes.md` |
| Validation report | **PASS** — `Issue_45_Validation_Report.md` |
| Regression report | **PASS** — `Issue_45_Regression_Report.md` |
| Batch log | `QLA_Migration/Logs/_full_batch_test_log.txt` |
| UAT partial reload | `QLA_Migration/Output/Test_Validation/quikmstr.csv` |

---

## Trace Policy Confirmation

| Policy | Before | After (masked) | Match |
|--------|--------|----------------|-------|
| 010157076C | blank + exception | *****1013/****2919 | Yes |
| 010161748C | blank + exception | *****0385/****0581 | Yes |
| 010348734C | blank + exception | *****1811/****8787 | Yes |
| 9015000043 | blank + exception | still exception | Yes |

**Fleet:** 739 newly filled; exceptions 763 → 24 (13 no account + 11 missing routing).

---

## Explicitly Not Changed

- [x] `MBILLFRM` / PAC detection
- [x] PPACH-primary banked policies (~1,369) — sample 50 byte-identical
- [x] Issue #25 MPOLICY padding (no new short-key drift)
- [x] Issue #26 MPREM mapping
- [x] Issue #21H PPACH ABA path for policies with PPACH accounts
- [x] Premium / rider / client tables (Issue #45 scope = banking cache only)

---

## Fleet Impact

| Metric | Value |
|--------|------:|
| `MBANKNO` newly filled | 739 |
| Exception rows remaining | 24 |
| quikmstr row count delta | 0 |
| Non-candidate field changes | 0 |

---

## Production Readiness + Git Release (G7)

| Check | Status |
|-------|--------|
| Validators PASS (G5 + G6) | Yes |
| `app.py` version bumped | **v57.77** (both copies) |
| Issue-scoped git commit | _(recorded after push)_ |
| **`git push` to remote** | branch `issue-34-pr7-quikisrr` |
| Network batch note | `Output/` gitignored — pull code, run full batch or reload `Test_Validation/quikmstr.csv`; ensure `PPPAC_PACDetail_Extract_*.csv` is in `Source/` |

---

## Client UAT

| Item | Status |
|------|--------|
| QLAdmin banking on sample policies (010157076C, 010161748C, 010348734C) | Pending client verify |
| Client sign-off | Pending |

---

## Residual Risks / Follow-ups

| Item | Owner | Notes |
|------|-------|-------|
| 11 `MISSING_ROUTING` (PPPAC account, no unique ABA) | Conversion / client | May need PPCOM re-pull or manual ABA |
| 13 still no account in PPACH or PPPAC | Client | Includes several `9015000xxx` PAC policies |
| RNA ABA may be truncated | Known #21H | Lookup preferred; 40 used lookup, 699 RNA |

---

## Rollback

1. Revert Issue #45 commit(s) on `app.py` / `QLA_Migration/app.py`
2. Re-run batch without PPPAC fallback (or remove PPPAC extract)
3. Confirm exceptions return toward 763 and validators for prior version

---

## Issue Log Entry (paste-ready)

> **Issue #45 — Bank Draft / PPPAC Account Fallback — CLOSED (2026-07-12).**  
> **Resolution:** Bank-draft policies missing PPACH account numbers now fall back to PPPAC `E_ACCOUNT_NUMBER`, with ABA from routing lookup or RelationshipNameAddress, and emit `MBANKNO` only when both account and routing resolve.  
> **Evidence:** Validation and regression PASS; 739 fills; traces 010157076C / 010161748C / 010348734C confirmed. **Preserved:** PPACH-primary banking (#21H), MPOLICY (#25), MPREM (#26). **Follow-ups:** 24 remaining exceptions (13 no account, 11 missing routing).

---

## Framework Checklist

- [x] Intake
- [x] Planning
- [x] Dependency Gate PASS
- [x] Risk Conditional Go
- [x] Development (v57.77)
- [x] Validation PASS
- [x] Regression PASS
- [x] Closure — **`Resolution:`** one-line + long-form summary
- [x] Git commit + push (G7 release gate)
