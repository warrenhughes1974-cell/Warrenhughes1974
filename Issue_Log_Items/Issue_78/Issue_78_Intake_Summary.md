# Issue #78 — Intake Summary

**Issue:** #78 — Recover missing `quikclmp` claim payments with approved payee fallback  
**Framework stage:** Intake Agent (G0)  
**Status:** Intake Complete → Planning (Pre-Risk Auto-Chain)  
**Generated:** 2026-07-17  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Conversion (Warren)  
**Priority:** High (claims financial completeness / UAT)  
**Code changes:** None  

---

## 1. Client / business symptom (verbatim + normalized)

**Business ask (normalized from 2026-07-17 claims book analysis + user approval):**

> 744 claim policies in `quikclms` have no matching `quikclmp` payment rows. Source accounting (PACTG) proves live payouts exist for ~729 of those policies (~$7.37M). Payee names are blank on PACTG payout rows; existing emitted payments resolved payees from relationship records. User approved a three-tier payee fallback so those historical payments can be emitted.

**Verbatim approval (2026-07-17):**

> Okay this is approved. Lets use our framework and make it happen

---

## 2. Example policies

| Tier | QLA MPOLICY | LifePRO | CLAIMSTAT | MPAID (header) | Notes |
|------|-------------|---------|-----------|----------------|-------|
| 1 (single PE) | `010150740C` | 9010150740 | 3 | 3213.59 | Death claim — 1 PE on file |
| 1 (single PE) | `010154425C` | 9010154425 | 99 | 0.00 | Disbursement — 1 PE on file |
| 2 (multi PE) | `010331157C` | 9010331157 | 3 | 19636.31 | Death claim — 2+ PE |
| 3 (no PE) | `015000341C` | 9015000341 | 3 | 5217.64 | Death — no PE; beneficiary/estate fallback |
| 3 (no PE) | `010469081C` | 9010469081 | 1 | 9722.80 | Surrender — no PE |

Fleet evidence (read-only, 2026-07-17):

| Metric | Count |
|--------|------:|
| Claim policies with zero `quikclmp` rows | 744 |
| Of those, with live non-reversed PACTG payouts (90/92/94/567/1900) | 729 |
| Payout txn rows available | 932 |
| Dollar total of those payouts | ~$7.37M |
| Policies with exactly 1 PE relationship | 646 |
| Policies with 2+ PE relationships | 85 |
| Policies with no PE record | 13 |

---

## 3. Suspected domain

**Claims — payment staging (`quikclmp`) + payee resolution from LifePRO relationships.**

| Layer | Path / table | Role |
|-------|--------------|------|
| Source (payouts) | `PACTG_Accounting_Extract_*.csv` | Amounts, dates, check-like txn codes |
| Source (payee) | `RelationshipNameAddress_Extract_*.csv` | `RELATE_CODE=PE` (+ B1 / insured fallback) |
| Target header | `quikclms` | Already present; not inventing new claims |
| Target payment | `quikclmp` | Missing rows to recover |
| Governance hold | Phase 17 deferred orphan payments | Why many were withheld |

---

## 4. In scope / out of scope (first pass)

### In scope

- Emit `quikclmp` rows for claim policies that currently have none, when live PACTG payout evidence exists
- Apply **approved three-tier payee rule** (see Scope Decisions)
- Preserve existing emitted `quikclmp` rows (non-candidates unchanged)
- Audit / lineage tagging for Tier 2 and Tier 3 recoveries
- Validation: recovered count, dollar reconciliation, tier distribution, #25/#26 guards

### Out of scope (companion items — separate issues unless explicitly folded later)

- `ORIGSTTUS` / `ORIGSTATUS` field-name and pre-death policy status fix
- Settling the 494 `CLAIMSTAT=1` funded claims (Pending → Settled)
- Blank `CAUSE` convention defaults (999 / SRR / MAT)
- Rebalancing still-unbalanced claim headers beyond payment emit
- Changing `quikmstr` / `quikridr` / rates / premiums

---

## 5. Related issues / prior claims work

| Item | Relationship |
|------|----------------|
| Claims log #15 | Orphan payments — prior promotion of 374 deferred payments |
| Claims log #16 | Unbalanced claims — still blocked population overlaps this gap |
| Claims log #19 | Payee override precedent (`010807842C`) |
| Phase 8 / 10A | Payee distribution + `quikclmp` derivation engines |
| Phase 17 | `deferred_governance_payments.csv` — PRODUCTION_BLOCKED orphans |

---

## 6. Immediate blockers visible at intake

- None for framing — user approved Tier 1–3 payee rule.
- Development still blocked until G1 + G2 + G3 + explicit “Approved for Development.”
- Risk must quantify multi-payee pairing ambiguity (Tier 2) and estate fallback (Tier 3).

---

## 7. Artifact inventory

| Artifact | Status |
|----------|--------|
| Symptom / approval | Present (chat 2026-07-17) |
| `Output/quikclms.csv` + `quikclmp.csv` before-state | Present |
| PACTG 20260630 | Present in Source |
| RelationshipNameAddress 20260630 | Present in Source |
| Reference `docs/Policy/quikclmp.dbf` | Present |
| Screenshots | Not required (fleet financial gap) |

---

## Gate Criteria (G0)

- [x] Issue folder created
- [x] Intake summary written
- [x] Example policies listed
- [x] Owner and priority assigned
- [x] No code or rulebook changes

**Recommended status:** Ready for Planning → Dependency Gate (auto-chain).
