# Issue #85 — Intake Summary

**Issue:** #85 — Duplicate claim headers sharing the same policy + phase  
**Framework stage:** Intake Agent (G0)  
**Status:** Intake Complete → Planning (Pre-Risk Auto-Chain)  
**Generated:** 2026-07-17  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Conversion (Warren)  
**Priority:** High (blocks Issue #84 Track B money reconciliation)  
**Code changes:** None  

**Opened as:** Companion to Issue #84 Risk addendum (duplicate `MPOLICY`+`MPHASE` header structure).

---

## 1. Symptom in plain English

In QLAdmin, each claim on a policy should have **one claim header** (the top “Claim Information” row) and then one or more **payee / check** rows under it.

In the **real** QLAdmin Policy book we use as the model, that pattern holds: there is **never** more than one claim header for the same policy number and phase.

In **our converted claims file**, about **3,054** claim-header rows share a policy + phase with another header. So one policy/phase can show multiple claim “tops” fighting over the same slot.

That makes the money not add up:

- The checks (payees) can’t be cleanly attached to “the” claim header.
- Net Payment on the header often doesn’t match the check total.
- Issue #84 Track B (fixing Dividends / Loan / Interest / etc., and balancing Net Payment to payees) **cannot finish safely** until we decide how to treat these duplicates.

**Why it matters in the UI:** You see confusing Claims screens — multiple headers, Net Payment that doesn’t match the payee amount, and money fields that can’t be trusted.

---

## 2. Evidence (counts)

| Measure | Real Policy book | Our Output |
|---------|-----------------:|-----------:|
| Duplicate claim headers on same policy + phase | **0** | **3,054** |
| Policies with more than one claim header | — | **735** |
| Policies where sum of header Net Payment ≠ sum of payee checks | 14 (~$35K) | **898 (~$2.46M)** |

Example of the structural mess: `010914301C` has more than one header on the same phase, so payee totals cannot be attributed cleanly.

Related money symptoms (owned by #84, not this issue’s code fix): `010360289C`, `010391359C`.

---

## 3. Suspected domain

**Claims emit structure — `quikclms` header identity / cardinality**

Likely cause area: claim reconstruction creates multiple reconstructed claim events (or claim numbers) that still emit under the same `MPOLICY` + `MPHASE`, whereas real QLAdmin uses a unique policy+phase (or unique claim key) per header.

---

## 4. In scope / out of scope

### In scope

- Decide the business rule for “one claim header” identity in QLAdmin
- Plan how to collapse, renumber, or re-phase duplicate headers
- Keep payee rows (`quikclmp`) attached correctly after the header rule is chosen
- Document impact on Issue #84 Track B sequencing

### Out of scope (this issue)

- Filling Dividends / Loan / Premium / Interest components (#84 Track B)
- Changing CLAIMSTAT (#79)
- Inventing new payee rows (#78)
- `quikmstr` / `quikridr` / rates

---

## 5. Related issues

| Issue | Relationship |
|-------|----------------|
| **#84** | Parent money-field work; Track B blocked/high-risk until this structure is decided |
| **#78** | Payee recovery — payees must still attach after header consolidation |
| **#79** | CLAIMSTAT remap — must not be undone |

---

## 6. Gate Criteria (G0)

- [x] Issue folder created
- [x] Intake summary written (lay language)
- [x] Decisions needed listed (see Scope Decisions)
- [x] Owner / priority assigned
- [x] No code changes

**Recommended status:** Ready for Planning → Dependency Gate (auto-chain).
