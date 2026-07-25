# Issue #75 — Intake Summary (REOPEN)

**Issue:** #75 — Bank Acct / `MBANKNO` QLA validation + PPCOM bank recovery  
**Framework stage:** Intake Agent (G0)  
**Status after intake:** Planning  
**Generated:** 2026-07-25  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Warren / Conversion  
**Priority:** Go-No Go  
**Reopen reason:** New LifePRO extract `PPCOM_PACAccountInformation_Extract_20260630.csv` available; prior v57.92 fix blanked invalid `MBANKNO` but left ~910 bank-draft policies without a loadable Bank Acct. Client also reports leading zeros on 8-digit account numbers.

---

## Client symptom (verbatim)

> Lets reopen this issue: 75 … There is a new file in source data called PPCOM. This should have much more complete bank information. Can you look at this table and analyze what we need to do to get the bank account numbers into QLA. There also seems to be leading zeros added to account numbers that have 8 digits.

Original symptom (still in force from first intake):

> QL error on policy change: Invalid routing number (//) / bank account not correct. Example 010161748C.

---

## Normalized symptom

1. **Format gate (already shipped v57.92):** QLA rejects non–9-digit ABA, punctuation in account, or multi-slash `MBANKNO`. Converter now blanks unsafe values — correct, but incomplete.
2. **Fill gap (reopen):** Bank-draft policies (`MBILLFRM=2`) with usable PPPAC/PPACH accounts still emit blank `MBANKNO` because full 9-digit ABA is not resolved from the stale `aba_routing_lookup.csv` path.
3. **Account padding:** Some emitted account halves carry leading zeros that make an 8-digit account look longer (source-driven and/or join-variant); needs an explicit emit rule against PPCOM’s account form.

---

## Example policies

| Client # | Output `MPOLICY` | Current `MBANKNO` | Notes |
|----------|------------------|-------------------|--------|
| 010161748C | 9010161748C | blank | PPPAC acct `000000  200-058-1`; PPCOM ABA **091303855** (unique, checksum OK) |
| 010157076C | 9010157076C | blank | PPCOM ABA **104910135** |
| 010348734C | 9010348734C | blank | PPCOM ABA **081518113** |
| 010713704C | 9010713704C | `104000016/47374579` | Already good; regression guard |
| 9010857359C | same | `082900872/0059281456` | Leading zeros on account vs PPCOM form `59281456` |

---

## Suspected domain

- **Primary target:** `quikmstr.MBANKNO` (`ABA/ACCOUNT`)
- **New source:** `PPCOM` — `E_TRAN_ABA_NUMBER`, `E_ACCOUNT_NUMBER` (no `POLICY_NUMBER`; join by account digits)
- **Existing sources:** PPACH (history), PPPAC (detail fallback #45), `aba_routing_lookup.csv` (#21H precompute)
- **Not:** `MACCTNO` (Bill Acct), claims `quikclmp.MBANKNO`

---

## In scope / out of scope (first pass)

**In scope:**

- Profile PPCOM and quantify recovery for blank bank-draft `MBANKNO`
- Rebuild or live-load ABA resolution from current PPCOM (join PPPAC + PPACH accounts)
- Preserve v57.92 QLA-safe emit rules (9-digit ABA, digits-only account, single `/`)
- Define leading-zero account emit rule (prefer PPCOM form vs preserve PPACH/PPPAC padding)
- Ambiguous account→ABA cases (multiple routing numbers)

**Out of scope (unless expanded):**

- Inventing ABA when PPCOM has no match
- Changing `MBILLFRM`
- Bank-name mapping / Credit Card ID UI labeling (#21H open product question)
- Claims banking fields

---

## Related issues

| ID | Relationship |
|----|----------------|
| **#21H** | Original PPCOM→`aba_routing_lookup` ABA recovery pattern |
| **#45** | PPPAC account fallback when PPACH missing |
| **#75 v57.92** | QLA-safe blanking of bad `MBANKNO` (still required) |

---

## Artifact inventory

| Provided | Status |
|----------|--------|
| `Source/PPCOM_PACAccountInformation_Extract_20260630.csv` (~5.3 GB, 2.6M rows) | Present |
| PPACH / PPPAC 20260630 extracts | Present |
| `Source/aba_routing_lookup.csv` (May-era, 2,692 keys) | Stale vs current blanks |
| Current `Output/quikmstr.csv` | Present (1,222 filled / 910 blank among 2,132 drafts) |
| Intake evidence | `evidence/issue75_ppcom_blank_draft_recovery.csv` |

---

## Immediate blockers

None for research/planning. Development should not start until Risk Go/No-Go and explicit Development approval (PPCOM is large; prefer rebuild lookup over in-batch full scan unless streaming is accepted).

---

## Tracking

Copy/paste row: `Issue_75_Tracking_Sheet_Row.tsv`
