# Citizens / CFIC — Target Platform Decision

**Status:** DECIDED  
**Date decided:** 2026-07-08  
**Source:** `CFIProposalMakerRev2.mdb` (proposal / illustration rate tool)

---

## Decision

| Field | Answer |
|-------|--------|
| **Chosen option** | **A — QLAdmin rate tables** |
| **Decided by** | Warren (business owner) |
| **Date** | 2026-07-08 |
| **Notes** | Rates from CFI Proposal Maker will be loaded into QLAdmin. All products are active. |

---

## What this means (plain language)

These Access rate tables will be converted into **QLAdmin rate / plan tables** (QuikPl* style structures and related rate DBFs), not left only in a proposal tool and not mapped to LifePRO.

Illustration columns (cash value, paid-up) may still need a separate decision: load into QLAdmin CV tables, keep for proposals only, or both.

---

## Options (for reference)

| Option | Description | Status |
|--------|-------------|--------|
| **A. QLAdmin rate tables** | Load into QuikPl* / QuikCvs-style rate structures | **SELECTED** |
| **B. LifePRO product rates** | Map into LifePRO product / segment / rate hierarchy | Not selected |
| **C. Proposal / illustration only** | Keep as a rate source for a new proposal tool | Not selected |
| **D. Hybrid** | Premium rates → admin; illustration → proposal tool | Not selected (may revisit for CV columns) |

---

## Immediate implication

Next work is a **product → QLAdmin plan/rate-key crosswalk** and column mapping for QuikPlan / rate tables.
