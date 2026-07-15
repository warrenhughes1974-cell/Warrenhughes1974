# Issue #75 — Intake Summary

**Issue:** #75 — Bank Account Number / `MBANKNO` QLA validation error  
**Framework stage:** Intake Agent (G0)  
**Status after intake:** Planning  
**Generated:** 2026-07-15  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Conversion  
**Priority:** Go-No Go  

---

## Client symptom (verbatim)

> Issue 75 I am getting an error in QL when I make a policy change stating the Bank account number is not correct. I need to look into this issue. Can you look at how the bank account number is coming over into QLA. how that needs to be formatted in QLA and see what we are doing on our side.

**Screenshot evidence (Editing Policy 010161748C — Base Data):**

- Bank Acct field displays: `09130385//00000200-058-1`
- Error popup: **Invalid routing number (//)**

---

## Normalized symptom

QLAdmin rejects the Bank Acct (`quikmstr.MBANKNO`) value on policy edit because the **routing (ABA) portion fails validation**. Conversion is emitting `MBANKNO` values that do not meet QLA’s expected bank-draft format (valid routing + `/` + account).

| Item | Value |
|------|--------|
| Example policy | **010161748C** (Active / status 22; EDWIN ARNDT) |
| Current Output `MBANKNO` | `09130385/000000200-058-1` |
| UI display (screenshot) | `09130385//00000200-058-1` (close; double-slash / slight acct digit difference vs current CSV) |
| Bill form | `MBILLFRM=2` (bank draft) |

---

## Suspected domain

- **Primary:** `quikmstr.MBANKNO` (Bank Acct on Base Data / Coverage)
- **Sources:** PPACH + PPPAC fallback + `aba_routing_lookup` / RNA (Issues **#21H**, **#45**)
- **Not:** `MACCTNO` (Bill Acct) — blank on this policy

---

## In scope / out of scope (first pass)

**In scope:**

- Confirm QLA Bank Acct formatting rules (Help PDF)
- Trace how conversion builds `MBANKNO` (`ABA/ACCOUNT`)
- Quantify format defects (truncated ABA, extra `/`, punctuation in account)
- Recommend surgical emit/cleanup rules so QLA accepts bank-draft values on edit

**Out of scope (unless client expands):**

- Credit-card ID labeling / Bill Acct vs Bank Acct product question still open on **#21H**
- Inventing ABA when no recoverable 9-digit routing exists
- Changing `MBILLFRM`

---

## Related issues

| ID | Relationship |
|----|----------------|
| **#21H** | ABA recovery to 9 digits; target-field placement still partly open |
| **#45** | PPPAC account fallback; **010161748C was a rescue sample** (`*****0385/****0581`) |
| Data governance | `MBANKNO` required when bill form is 2 |

---

## Artifact inventory

| Provided | Missing |
|----------|---------|
| Symptom + screenshot | Full LifePRO screen for same policy (optional) |
| Example policy 010161748C | Client confirmation of account-type suffix rules (`/S`, `/A`) if needed |
| Current `Output/quikmstr.csv` | Local `Source/` extracts in this workspace (batch path may hold them) |

---

## Immediate blockers

None for research. Format defect is measurable from current Output + QLAdmin Help.

---

## Tracking

Copy/paste row: `Issue_75_Tracking_Sheet_Row.tsv`
