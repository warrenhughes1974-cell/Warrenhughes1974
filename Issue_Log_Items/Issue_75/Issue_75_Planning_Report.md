# Issue #75 — Planning Report

**Issue:** #75 — Bank Acct / `MBANKNO` QLA validation  
**Framework stage:** Planning Agent  
**Status:** Ready for Dependency Gate  
**Generated:** 2026-07-15  
**Model:** Cursor Grok 4.5 (locked)  
**Scope decisions:** `Issue_75_Scope_Decisions.md`  
**Intake:** `Issue_75_Intake_Summary.md`  
**Evidence:** `evidence/issue75_mbankno_format_defects.csv`

---

## 1. Executive Finding

Client cannot save a policy change in QLAdmin because Bank Acct fails routing validation (`Invalid routing number (//)` on **010161748C**).

Conversion already maps bank draft into `quikmstr.MBANKNO` as `ABA/ACCOUNT` (Issues **#21H** / **#45**). Current Output for the example is:

`09130385/000000200-058-1`

That value is **not QLA-safe**: ABA is **8 digits** (must be 9), and the account contains **hyphens**. Fleet-wide, **~986** filled `MBANKNO` rows have ABA ≠ 9 digits; **15** have multiple slashes (literal `//` or `/…/…`); **165** have account punctuation.

**Direction:** Tighten emit rules so `MBANKNO` is only written as a QLA-valid `9digitABA/accountDigits` (optional `/S`/`/A` later if client confirms). Re-apply #21H full-ABA recovery where possible; strip punctuation; reject/blank + exception when ABA cannot be recovered to 9 digits. Ready for Dependency Gate / Risk.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source | Role | In this workspace Source/? | Notes |
|--------|------|:--------------------------:|-------|
| PPACH | Primary ABA + account | Not present locally | Existing `#21H` path → `_ppach_bank_map` |
| PPPAC | Fallback account (#45) | Not present locally | Used when PPACH account missing |
| `aba_routing_lookup.csv` | Full 9-digit ABA by account digits | Not present locally | Issue #21H recovery |
| RelationshipNameAddress | Fallback ABA (#45) | Not present locally | Single distinct ABA only |

Sources are documented and used on the batch path (Issue #45 closed on same example policy). Local `QLA_Migration/Source/` is empty in this workspace; **before-state is measurable from `Output/quikmstr.csv`**.

### Available source fields (from prior #21H/#45)

| Field | Column | Notes |
|-------|--------|-------|
| Policy | `POLICY_NUMBER` | Crosswalk → MPOLICY |
| ABA (history) | PPACH `E_ABA_NUM` | Often truncated |
| Account (history) | PPACH `E_ACCOUNT_NUMBER` | |
| Account (current PAC) | PPPAC `E_ACCOUNT_NUMBER` | No ABA column |
| Full ABA | lookup `FULL_ABA` / RNA `ELEC_ABA_NUMBER` | Prefer 9-digit |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Semantics (QLAdmin Help) |
|-------|-------|--------------------------|
| quikmstr | `MBANKNO` | **Bank Acct** — “Bank Routing Number plus the payor's account number for policies on bank draft.” |
| | | Savings: end with `/S`. Advance draft: end with `/A`. Both: `/A/S` or `/S/A` after routing/account. |
| | | Routing is **validated** by the system (matches client error). |
| quikmstr | `MBILLFRM` | Bill form `2` = bank draft (governance: needs bank value) |
| quikmstr | `MACCTNO` | Bill Acct — **different field**; blank on example |

**Repo emit path:**

| Location | Role |
|----------|------|
| `app.py` PPACH/PPPAC cache | Builds `_ppach_bank_map[pol] = f"{use_aba}/{acct}"` |
| Rulebook `MBANKNO` blank | Overridden from map when present |
| `_apply_issue45_bank_draft_gate` | Blanks incomplete bank-draft rows + exception CSV |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PPACH (primary) | `E_ABA_NUM` + `E_ACCOUNT_NUMBER` | `MBANKNO` | Recover full **9-digit** ABA via lookup; strip acct punct; single `/` | **Yes — tighten** |
| PPPAC (fallback) | `E_ACCOUNT_NUMBER` | `MBANKNO` account half | Same as #45 + strip `/` and punctuation from account | **Yes — tighten** |
| aba_routing_lookup / RNA | full ABA | `MBANKNO` ABA half | Emit only if digit-length **== 9** | **Yes — gate** |

### Fields that must remain unchanged

| Target | Touch this issue? |
|--------|-------------------|
| `MBILLFRM` | **No** |
| `MACCTNO` | **No** |
| `MMODPREM` / `MPREM` (#26) | **No** |
| MPOLICY padding (#25) | **No** |
| PPACH-primary path when already valid 9-digit | Prefer **byte-stable** where already good |

---

## 5. Open Client Questions

1. **OBQ-75-1:** When a usable account exists but ABA **cannot** be recovered to exactly 9 digits, confirm: **blank `MBANKNO` + exception** (keep converting), same as #45 incomplete cases?  
   - **Assumption for Risk:** **Yes.**

2. **OBQ-75-2:** Strip hyphens/spaces from account numbers before emit (e.g. `000000200-058-1` → `0000002000581`)?  
   - **Assumption for Risk:** **Yes** (digits-only account half).

3. **OBQ-75-3:** Do we need LifePRO checking vs savings → append `/S`?  
   - **Assumption:** **No for this issue** unless client provides type mapping; leave suffix out until confirmed.

4. **OBQ-75-4:** Screenshot shows `//` and a slightly different account digit string than current Output. Confirm UAT load is from latest `quikmstr` / Test_Validation, or note possible local edit in QLA.  
   - **Does not block** format hardening.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Separator | Exactly one `/` between ABA and account (suffixes `/S` `/A` only if client later confirms) |
| ABA | Digits only; **length == 9**; else do not emit |
| Account | Digits only (strip spaces, hyphens, leading `/`); reject if account itself contains `/` |
| Incomplete | Blank `MBANKNO` + `bank_draft_account_exceptions.csv` when `MBILLFRM=2` |
| Policy key | Crosswalk + #25 padding unchanged |

---

## 7. Policy key handling

Unchanged — `format_qladmin_mpolicy()` / crosswalk.

---

## 8. Estimated Record Counts (current Output)

| Population | Count |
|------------|------:|
| quikmstr rows | 5,083 |
| `MBANKNO` filled | 2,736 |
| `MBILLFRM=2` with filled bank | 2,108 |
| ABA digit length = 9 (all filled) | 1,750 |
| ABA ≠ 9 (all filled) | **986** |
| Multi-slash (`/` count ≥ 2) | **15** |
| Account punctuation (hyphen/space) | **165** |
| PAC (`MBILLFRM=2`) rows with ≥1 format flag | **961** |

Detail file: `evidence/issue75_mbankno_format_defects.csv` (1,074 rows).

---

## 9. Sample Trace

| Policy | MBILLFRM | Current `MBANKNO` | Defect | Notes |
|--------|:--------:|-------------------|--------|-------|
| **010161748C** | 2 | `09130385/000000200-058-1` | ABA_LEN=8; hyphen acct | Client screenshot / #45 rescue sample |
| 010157076C | 2 | `10491013/212919` | ABA_LEN=8 | #45 sample |
| 010348734C | 2 | `08151811/208787` | ABA_LEN=8 | #45 sample |
| 010464590C | 2 | `09140068//7562700387` | MULTI_SLASH | Literal `//` in Output |
| 010713704C | (prior #21H) | Expect 9-digit when lookup works | Regression guard | Classic #21H example |

---

## 10. Risks and Unknowns

| Risk | Mitigation |
|------|------------|
| Large intentional `MBANKNO` churn (~900+ PAC) | Risk Agent quantify; validate non-candidates / already-valid 9-digit stable |
| Blanking truncated ABA may increase exceptions | Prefer recover-to-9 via lookup/RNA before blank |
| Account digit strip changes ACH identity | Confirm OBQ-75-2 with client if hyphens are significant |
| Screenshot ≠ CSV byte-for-byte | Harden format anyway; re-UAT after reload |

---

## 11. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue #75.

Read AI_Agents/Risk_Agent.md and Issue_75_Planning_Report.md.
Model: Cursor Grok 4.5. Do not code.

Quantify before/after impact on quikmstr.MBANKNO:
- how many gain valid 9-digit ABA via recovery
- how many blank (exception) because ABA unrecovered
- punctuation/multi-slash cleanups
- prove already-valid 9-digit ABA/ACCOUNT rows unchanged where possible
GO/NO-GO for Development.
```

---

## 12. Recommended Development Task (do not implement)

1. When building `_ppach_bank_map` / PPPAC fallback:
   - Normalize ABA to digits; accept only length **9** (or recover via lookup/RNA to 9).
   - Normalize account: strip spaces/hyphens; reject if `/` remains in account.
   - Emit `f"{aba9}/{acct_digits}"` only when both pass.
2. Extend Issue #45 gate / exception reasons for `ABA_NOT_9` / `ACCT_INVALID_CHARS`.
3. Validator: assert no filled `MBANKNO` with ABA≠9, multi-slash, or hyphen/space in account; trace **010161748C**.
4. Version-bump both `app.py` files; publish `Test_Validation/quikmstr.csv` on PASS.
5. Do **not** touch #25/#26 or `MBILLFRM`.
