# Issue #45 — Resolution Summary

**Issue:** #45 — Bank Draft Account Validation / PPPAC Account Fallback  
**Framework stage:** Closure Agent  
**Final status:** **Closed**  
**Engine version:** v57.77  
**Closed date:** 2026-07-12  
**Owner:** Conversion  
**Git:** `c3a4e26f34bff1ba1ccad81cc2b6c834811062f4` · branch `issue-34-pr7-quikisrr`

---

## Resolution (issue log — paste-ready)

Copy everything in the box below:

```text
Resolution: Bank-draft policies missing PPACH account numbers now fall back to PPPAC E_ACCOUNT_NUMBER, with ABA from routing lookup or RelationshipNameAddress, and emit MBANKNO only when both account and routing resolve. 739 policies newly filled; 24 remain incomplete (policy still converts; MBILLFRM=2; MBANKNO blank).

Still incomplete — no account in PPACH or PPPAC (13):
010772298C — Active (22)
010827081C — Active (22)
010847481C — Active (22)
011047403C — Death / death-terminated (53)
011192032C — Death / death-terminated (53)
015000043C — Surrender (55)
015000078C — Death / death-terminated (53)
015000080C — Surrender (55)
015000117C — Surrender (55)
015000138C — Surrender (55)
015000148C — Active (22)
015000211C — Death / death-terminated (53)
015000261C — Death / death-terminated (53)

Still incomplete — PPPAC account present but routing/ABA unresolved (11):
010408371C — Paid-up (41)
010785310C — Surrender (55)
010936709C — ETI (44)
011017289C — ETI (44)
011064372C — Death / death-terminated (53)
011090462C — Active (22)
011090463C — Active (22)
011090464C — Active (22)
011210337C — Death / death-terminated (53)
015000462C — Active (22)
015000581C — Death / death-terminated (53)
```

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
| Exception rows remaining | **24** (listed below) |
| quikmstr row count delta | 0 |
| Non-candidate field changes | 0 |

### Remaining policies without complete banking (`MBANKNO` blank)

All **24** remain `MBILLFRM=2` (bank draft) and still convert; only banking is incomplete.  
`MSTATUS` labels below follow the project translation (22=Active, 41=Paid-up, 44=ETI, 53=Death/terminated-death, 55=Surrender).

#### A. No usable account in PPACH or PPPAC — `MISSING_BANK_ACCOUNT` (13)

| MPOLICY | LifePRO POLICY | MSTATUS | Status meaning |
|---------|----------------|---------|----------------|
| 010772298C | 9010772298 | 22 | Active |
| 010827081C | 9010827081 | 22 | Active |
| 010847481C | 9010847481 | 22 | Active |
| 011047403C | 9011047403 | 53 | Death / death-terminated |
| 011192032C | 9011192032 | 53 | Death / death-terminated |
| 015000043C | 9015000043 | 55 | Surrender |
| 015000078C | 9015000078 | 53 | Death / death-terminated |
| 015000080C | 9015000080 | 55 | Surrender |
| 015000117C | 9015000117 | 55 | Surrender |
| 015000138C | 9015000138 | 55 | Surrender |
| 015000148C | 9015000148 | 22 | Active |
| 015000211C | 9015000211 | 53 | Death / death-terminated |
| 015000261C | 9015000261 | 53 | Death / death-terminated |

#### B. PPPAC account present but ABA unresolved — `MISSING_ROUTING` (11)

| MPOLICY | LifePRO POLICY | MSTATUS | Status meaning | PPPAC account (masked) |
|---------|----------------|---------|----------------|------------------------|
| 010408371C | 9010408371 | 41 | Paid-up | ****7294 |
| 010785310C | 9010785310 | 55 | Surrender | ****5282 |
| 010936709C | 9010936709 | 44 | ETI | ****3747 |
| 011017289C | 9011017289 | 44 | ETI | ****0830 |
| 011064372C | 9011064372 | 53 | Death / death-terminated | ****4018 |
| 011090462C | 9011090462 | 22 | Active | ****7678 |
| 011090463C | 9011090463 | 22 | Active | ****7678 |
| 011090464C | 9011090464 | 22 | Active | ****7678 |
| 011210337C | 9011210337 | 53 | Death / death-terminated | ****9071 |
| 015000462C | 9015000462 | 22 | Active | ****1475 |
| 015000581C | 9015000581 | 53 | Death / death-terminated | ****8859 |

#### Status mix (all 24 remaining)

| MSTATUS | Meaning | Count |
|---------|---------|------:|
| 22 | Active | 8 |
| 53 | Death / death-terminated | 8 |
| 55 | Surrender | 5 |
| 44 | ETI | 2 |
| 41 | Paid-up | 1 |

Source file: `QLA_Migration/Reports/bank_draft_account_exceptions.csv` (post–v57.77 batch).

---

## Production Readiness + Git Release (G7)

| Check | Status |
|-------|--------|
| Validators PASS (G5 + G6) | Yes |
| `app.py` version bumped | **v57.77** (both copies) |
| Issue-scoped git commit | `c3a4e26f34bff1ba1ccad81cc2b6c834811062f4` |
| **`git push` to remote** | `origin/issue-34-pr7-quikisrr` |
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
| 13 `MISSING_BANK_ACCOUNT` | Client | Full list in Fleet Impact §A — no account in PPACH or PPPAC |
| 11 `MISSING_ROUTING` | Conversion / client | Full list in Fleet Impact §B — PPPAC account present; need unique ABA |
| RNA ABA may be truncated | Known #21H | Lookup preferred; 40 used lookup, 699 RNA |

---

## Rollback

1. Revert Issue #45 commit(s) on `app.py` / `QLA_Migration/app.py`
2. Re-run batch without PPPAC fallback (or remove PPPAC extract)
3. Confirm exceptions return toward 763 and validators for prior version

---

## Issue Log Entry (paste-ready)

```text
Issue #45 — Bank Draft / PPPAC Account Fallback — CLOSED (2026-07-12).
Resolution: Bank-draft policies missing PPACH account numbers now fall back to PPPAC E_ACCOUNT_NUMBER, with ABA from routing lookup or RelationshipNameAddress, and emit MBANKNO only when both account and routing resolve. 739 policies newly filled; 24 remain incomplete (policy still converts; MBILLFRM=2; MBANKNO blank).
Evidence: Validation and regression PASS; traces 010157076C / 010161748C / 010348734C confirmed. Preserved: PPACH-primary banking (#21H), MPOLICY (#25), MPREM (#26).

Still incomplete — no account in PPACH or PPPAC (13):
010772298C — Active (22); 010827081C — Active (22); 010847481C — Active (22); 011047403C — Death / death-terminated (53); 011192032C — Death / death-terminated (53); 015000043C — Surrender (55); 015000078C — Death / death-terminated (53); 015000080C — Surrender (55); 015000117C — Surrender (55); 015000138C — Surrender (55); 015000148C — Active (22); 015000211C — Death / death-terminated (53); 015000261C — Death / death-terminated (53).

Still incomplete — PPPAC account present but routing/ABA unresolved (11):
010408371C — Paid-up (41); 010785310C — Surrender (55); 010936709C — ETI (44); 011017289C — ETI (44); 011064372C — Death / death-terminated (53); 011090462C — Active (22); 011090463C — Active (22); 011090464C — Active (22); 011210337C — Death / death-terminated (53); 015000462C — Active (22); 015000581C — Death / death-terminated (53).
```

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
