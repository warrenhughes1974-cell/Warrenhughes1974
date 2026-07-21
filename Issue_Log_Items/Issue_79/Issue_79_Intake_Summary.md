# Issue #79 — Intake Summary

**Issue:** #79 — Align `quikclms.CLAIMSTAT` to real Policy-book conventions  
**Framework stage:** Intake Agent (G0)  
**Status:** Intake Complete → Planning (Pre-Risk Auto-Chain)  
**Generated:** 2026-07-17  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Conversion (Warren)  
**Priority:** High (claims UAT / open-work queue risk)  
**Code changes:** None  

---

## 1. Client / business symptom (verbatim + normalized)

**Verbatim (2026-07-17):**

> Okay thats what we want. Lets move forward with our framework.

**Normalized:**

Align converted claim statuses to the real `docs/Policy/quikclms.dbf` pattern so historical claims do not land in QLAdmin as Pending when they are already paid/closed. User locked the Policy-book convention as the consistency target.

---

## 2. Example policies

| QLA MPOLICY | Family (memo) | Current CLAIMSTAT | Proposed (Policy book) | Notes |
|-------------|----------------|-------------------:|------------------------:|-------|
| `010397318C` | DEATH_CLAIM | 3 | **2** | Settled death → Paid in Full |
| `010391359C` | DEATH_CLAIM | 1 | **2** | FUNDED death with payment → Paid in Full |
| `010469081C` | SURRENDER_CLAIM | 1 | **99** | Pending surrender → Surrender |
| `010154425C` | DISBURSEMENT_CLAIM | 99 | **99** | Already matches |

Fleet evidence (current Output, 2026-07-17):

| Metric | Count |
|--------|------:|
| CLAIMSTAT = 1 (Pending) | 494 |
| Of those with payments | 492 |
| CLAIMSTAT = 3 (Settled deaths) | 1,275 |
| CLAIMSTAT = 99 | 3,855 |
| CLAIMSTAT = 2 / 98 | 0 / 0 |
| Headers that would change under locked rule | ~1,769 |

---

## 3. Suspected domain

**Claims — `quikclms.CLAIMSTAT` (and linked `ORIGSTTUS` only if it currently mirrors claim status incorrectly).**

Authority for target convention: `docs/Policy/quikclms.dbf` (7,691 rows).

---

## 4. In scope / out of scope (first pass)

### In scope

- Remap `quikclms.CLAIMSTAT` to Policy-book family rules (death→2, surrender/partial/disbursement→99, maturity→98, true unpaid open→1)
- Close the 494 FUNDED/Pending historical claims that already have payments
- Change settled deaths from 3 → 2 for consistency with real data
- Validation + audit of before/after status counts
- Preserve Issue #78 recovered payments (do not delete `quikclmp` rows)

### Out of scope

- Re-deriving cause-of-death (`CAUSE`) medical codes (companion)
- `ORIGSTATUS` / pre-death policy status carry-forward (companion unless Risk folds a safe mirror)
- Payment recovery (#78 already done)
- `quikmstr` / `quikridr` / rates / premiums

---

## 5. Related issues

| Item | Relationship |
|------|----------------|
| #78 | Recovered missing payments — many Pending rows now have payments; strengthens need to close status |
| Claims Item 15 | Earlier recommended CLAIMSTAT=3 for standalone orphans; **superseded for deaths by Policy-book rule → 2** (user locked 2026-07-17) |
| Phase 10B lifecycle mapping | Current FUNDED→1 / SETTLED→3 source of mismatch |

---

## 6. Immediate blockers visible at intake

- None for framing — user approved Policy-book convention.
- Development still blocked until G1 + G2 + G3 + explicit Development approval.

---

## Gate Criteria (G0)

- [x] Issue folder created
- [x] Intake summary written
- [x] Example policies listed
- [x] Owner and priority assigned
- [x] No code or rulebook changes

**Recommended status:** Ready for Planning → Dependency Gate (auto-chain).
