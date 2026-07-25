# Issue #75 — Planning Report (REOPEN — PPCOM recovery)

**Issue:** #75 — Bank Acct / `MBANKNO` via PPCOM  
**Framework stage:** Planning Agent (G1)  
**Date:** 2026-07-25  
**Model:** Cursor Grok 4.5 (locked)  
**Code changes:** None (planning only)

---

## 1. Executive finding

v57.92 correctly stopped emitting QLA-invalid `MBANKNO`, but **~910 bank-draft policies remain blank** even though PPPAC has an account on every one of them. The missing piece is a **current PPCOM-backed 9-digit ABA**. The May `aba_routing_lookup.csv` (built from PPACH accounts only) hits almost none of these PPPAC-only blanks.

**Plan:** Keep the QLA-safe emit gate; rebuild ABA resolution from `PPCOM_PACAccountInformation_Extract_20260630.csv` joined by account digits (PPACH primary, PPPAC fallback); emit `9digitABA/accountDigits`; decide leading-zero account form explicitly.

---

## 2. Confirmed LifePRO sources

| Source | File | Grain | Bank fields |
|--------|------|-------|-------------|
| **PPCOM** (authoritative ABA) | `PPCOM_PACAccountInformation_Extract_20260630.csv` | PAC account history (~2.62M rows, 37 cols) | `E_ACCOUNT_NUMBER`, `E_TRAN_ABA_NUMBER`, `EFFECTIVE_DATE`, `DRAFT_TYPE`; **no POLICY_NUMBER** |
| PPACH | `PPACH_PACHistory_Extract_20260630.csv` | Policy PAC history | `POLICY_NUMBER`, `E_ACCOUNT_NUMBER`, `E_ABA_NUM` (often truncated) |
| PPPAC | `PPPAC_PACDetail_Extract_20260630.csv` | Policy PAC detail | `POLICY_NUMBER`, `E_ACCOUNT_NUMBER`, `PAC_ID` (PAC_ID does **not** join cleanly to PPCOM) |
| Lookup (current engine) | `aba_routing_lookup.csv` | Account→ABA | Stale; rebuild from PPCOM |

PPCOM join key = **bank account digits** (exact, then strip-leading-zeros match). Do not rely on `PAC_ID`.

---

## 3. Confirmed QLAdmin target

| Table | Field | Format |
|-------|-------|--------|
| `quikmstr` | `MBANKNO` | `AAAAAAAAA/ACCT…` — exactly one `/`, ABA **exactly 9 digits**, account **digits only** |

Governance: bank value expected when `MBILLFRM=2`; blank + exception is allowed when ABA cannot be recovered safely.

---

## 4. Proposed source-to-target mapping

```text
Policy account  := PPACH.E_ACCOUNT_NUMBER (latest) else PPPAC.E_ACCOUNT_NUMBER
Account digits  := digits-only(account); usable if len>=4 (#45/#75 rules)
ABA             := PPCOM.E_TRAN_ABA_NUMBER for matching account digits
                     prefer native 9-digit; if only 8-digit, accept zfill(9) ONLY when ABA checksum passes
                     if multiple distinct 9-digit ABAs → latest EFFECTIVE_DATE (flag AMBIGUOUS)
MBANKNO         := f"{aba9}/{account_digits_emit}" if both present else blank + exception
```

**Account emit (leading zeros) — recommended default for Risk:**

- Prefer **PPCOM’s latest/most-common `E_ACCOUNT_NUMBER` digit form** for the matched account (strip punctuation/spaces only).
- Do **not** invent padding (no `zfill` on accounts).
- If PPCOM form absent, use PPACH/PPPAC digits-only as today.
- Open question: if LifePRO UI shows 8 digits but extract stores leading zeros, confirm with client whether zeros are significant.

---

## 5. Open client questions

1. For ambiguous account→ABA (205 blank-draft accounts map to >1 routing): OK to take latest `EFFECTIVE_DATE`, or leave blank for client list?
2. Leading zeros on accounts: emit PPCOM form, strip insignificant zeros, or keep PPACH/PPPAC literal digits?
3. Reload previously blanked bank-draft policies into UAT after recovery?

---

## 6. Formatting / fallback rules

| Rule | Action |
|------|--------|
| ABA not 9 after PPCOM + checksum pad | Blank; `ABA_NOT_9` / `MISSING_ROUTING` |
| Account unusable / punctuation-only | Blank; `ACCT_INVALID` / `MISSING_BANK_ACCOUNT` |
| Multi-slash / punct in emit | Forbidden (keep v57.92 gate) |
| No PPCOM match | Blank; do not invent |
| Already QLA-safe filled | Unchanged unless ABA/account intentionally corrected |

---

## 7. Policy key handling

Output keys are Issue #2 form (`9010…C`). Source `POLICY_NUMBER` may be without `C` — normalize with existing `normalize()` / append-`C` used on PPACH/PPPAC paths. PPCOM has no policy key.

---

## 8. Estimated record counts (current Output)

| Metric | Count |
|--------|------:|
| `MBILLFRM=2` | 2,132 |
| Filled QLA-safe `MBANKNO` | 1,222 |
| Blank bank-draft | 910 |
| Blank with PPPAC account | 910 (100%) |
| Blank recoverable via PPCOM (unique ABA) | **656** |
| Blank recoverable but ambiguous ABA | **205** |
| Blank still not in PPCOM | **49** |
| Filled emits with leading-zero-padded 8-digit-looking accounts | ~55–91 |

Evidence: `evidence/issue75_ppcom_blank_draft_recovery.csv`

---

## 9. Sample traces

| MPOLICY | PPPAC account (raw) | PPCOM ABA | Proposed `MBANKNO` |
|---------|---------------------|-----------|--------------------|
| 9010161748C | `000000  200-058-1` | 091303855 | `091303855/0000002000581` (or PPCOM form if different) |
| 9010157076C | `212919` | 104910135 | `104910135/212919` |
| 9010348734C | `208787` | 081518113 | `081518113/208787` |
| 9010713704C | `47374579` | 104000016 | **unchanged** `104000016/47374579` |

---

## 10. Risks and unknowns

- PPCOM file size (~5.3 GB): prefer **offline rebuild** of `aba_routing_lookup.csv` (+ optional account-form map) over full in-batch scan every run.
- Ambiguous ABAs (205): wrong routing if latest-date rule is wrong.
- Account leading zeros: stripping vs preserving can both be wrong for ACH; need clear rule.
- Stale lookup in Source today means even PPACH recoveries may be underfilled vs June PPCOM.

---

## 11. Recommended Risk Agent focus

Simulate fill of 910 blanks under (A) unique-only vs (B) unique+latest-ambiguous; measure `MBANKNO` changes on the 1,222 already filled; quantify leading-zero account diffs vs current emit; confirm non-`MBANKNO` columns untouched.
