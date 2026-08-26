# Issue #146 — Dependency Gate

**Issue:** #146 — Non-VB Unit Reductions (PC / former-vanish 0561 exclude)  
**Framework stage:** Dependency Gate (G2)  
**Generated:** 2026-08-26  
**Status:** **PASS**

---

## Checklist

### Source data

| Check | Met? |
|-------|------|
| Required LifePRO extract(s) present in `QLA_Migration/Source/` | **Met** — PPOLC 20260630; leftover QuikIsrr is current Output after #145B |
| Extract row count > 0 | **Met** — 20/20 allowlist policies have QuikIsrr (104 rows) |
| Column headers documented | **Met** — `BILLING_REASON`, `DEBIT_CODE`, `REVERSAL_CODE`, `TRANS_AMOUNT` |
| Extract date/version matches batch under test | **Met** — 6/30 leftover book; later batch follows that extract’s allowlist matches |
| Re-extract required? | **N/A** |

### Field definitions

| Check | Met? |
|-------|------|
| QLAdmin target table confirmed | **Met** — QuikIsrr §7.143; companions are the same #34 PR-7 package |
| QLAdmin target field semantics confirmed | **Met** — `MSURRAMT` is the dollar anniversary subtracts |
| LifePRO source field semantics confirmed | **Met** — 0561 on the allowlist = vanish-premium fingerprint (amount = annual premium, anniversary). PC is the current billing label, not the emit key |
| Transformation notes identified | **Met** — exclude / strip; no amount rewrite |

### Client clarification

| Check | Met? |
|-------|------|
| Scope boundary agreed | **Met** — 20-policy allowlist (Warren 08/26). Not all 0561s. Not all PC. Not VANISH=T |
| Business rule for edge cases | **Met** — keep 9010761639 / 9010760840; 9010808831 included though billing reason blank |
| Retention / filtering | **Met** — do not delete PACTG; exclude from emit only |
| UAT acceptance criteria stated | **Met** — allowlist golds 0 QuikIsrr; units stay 5 / 5 / 25; keep golds unchanged |

### Evidence

| Check | Met? |
|-------|------|
| Example policies identified | **Met** |
| Screenshots or docx | **N/A** — Eric 08/23 VPU write-up + 08/26 New Era PC note + current Output |
| Before-state measurable | **Met** — 104 allowlist rows on each of four tables |

### Regression guards

| Check | Met? |
|-------|------|
| Plan preserves Issue #25 MPOLICY padding | **Met** |
| Plan preserves Issue #26 MPREM mapping | **Met** |
| Plan does not alter unrelated rulebooks | **Met** — no Sync rulebook change |
| Plan does not undo Closed #145B | **Met** — VB golds stay 0; $271 / $716.40 keep golds stay |

---

## Gate result

**PASS** — Framework auto-chain continues to Risk in this session.

Accepted assumptions:

1. Identity is the locked 20 keys, not `BILLING_REASON=PC`.  
2. Warren authorized an **allowlist exclusion** on Closed #34 / leftover after Closed #145B.  
3. Companions come out with QuikIsrr because they are the same event.  
4. Eric’s 08/26 PC / former-vanish note is confirmation of the 08/23 fingerprint, not a fleet-PC rule.

## Blockers

None.

## Recommended tracking status

**Dependency Gate PASS → Risk Complete (pending Dev approval)**
