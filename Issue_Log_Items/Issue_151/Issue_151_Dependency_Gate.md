# Issue #151 — Dependency Gate

**Issue:** #151 — Val X Modal Prem Outlier (9010969231C former-vanish 0561 leftover)  
**Framework stage:** Dependency Gate (G2)  
**Generated:** 2026-09-22  
**Stage model:** Cursor Grok 4.6 (Warren override 2026-09-22; Grok 4.5 unavailable)  
**Status:** **PASS (MET)**

---

## Checklist

### Source data

| Check | Met? |
|-------|------|
| Required LifePRO extract(s) present in `QLA_Migration/Source/` | **Met** — `PPOLC_PolicyMaster_Extract_20260831.csv`, `PPBEN_PolicyBenefit_Extract_20260831.csv`, `PACTG_Accounting_Extract20260831.csv` |
| Extract row count > 0 | **Met** — PPOLC 5,084; this policy has 8 unreversed 0561s at $188.10 |
| Column headers documented | **Met** — `BILLING_CODE`, `BILLING_REASON`, `MODE_PREMIUM`, `ANNUAL_PREMIUM`, `POLICY_FEE`, `DEBIT_CODE`, `REVERSAL_CODE`, `TRANS_AMOUNT`, `NUMBER_OF_UNITS` |
| Extract date/version matches batch under test | **Met** — 20260831 source vs current Output for this policy |
| Re-extract required? | **N/A** |

### Field definitions

| Check | Met? |
|-------|------|
| QLAdmin target table confirmed | **Met** — QuikIsrr §7.143; companions are the same #34 PR-7 package as #146 |
| QLAdmin target field semantics confirmed | **Met** — `MSURRAMT` is the dollar anniversary subtracts; QuikValf `MPREM1`/`MANNLZD` 2899.79 is valuation output, not load premium |
| LifePRO source field semantics confirmed | **Met** — 0561 amount = annual premium on anniversary; billing reason PC; fee $25 is #139, not this emit |
| Transformation notes identified | **Met** — exclude / strip; no amount rewrite |

### Client clarification

| Check | Met? |
|-------|------|
| Scope boundary agreed | **Met** — one policy `9010969231C`. Warren written approval **2026-09-22** to expand Closed #146 allowlist 20 → 21. Not all 0561s. Not all PC. Not VANISH=T. Not undo #139 |
| Business rule for edge cases | **Met** — keep 9010761639 / 9010760840; preserve rider 5.00000 / 37.62 / -812.49 |
| Retention / filtering | **Met** — do not delete PACTG; exclude from emit only |
| UAT acceptance criteria stated | **Met** — conversion: 0 QuikIsrr/companions on 9010969231C; load premium/units unchanged. **Fresh QLAdmin valuation** (MUNIT 5.0000 and $2,899.79 gone; compare controls MEXTCODE 1 / normal premium) is a **UAT criterion after Development**, not a gate blocker. Current `docs/Valuation/QuikValf.dbf` is dated **2026-06-30** and is **not** a passed fresh valuation |

### Evidence

| Check | Met? |
|-------|------|
| Example policies identified | **Met** — 9010969231C; controls 9010817956C / 9010943849C; keep golds 9010761639C / 9010760840C |
| Screenshots or docx | **N/A** — 8/18 client symptom + 09/22 Warren allowlist approval + current Output / QuikValf / #145B join |
| Before-state measurable | **Met** — 8 rows on each of four tables; QuikValf MUNIT 3.4952 / MPREM1 2899.79; load MMODEPREM 163.10 |

### Regression guards

| Check | Met? |
|-------|------|
| Plan preserves Issue #25 MPOLICY padding | **Met** |
| Plan preserves Issue #26 MPREM mapping | **Met** — rider MPREM 37.62 stays |
| Plan does not alter unrelated rulebooks | **Met** — no Sync rulebook change |
| Plan does not undo Closed #139 | **Met** — MMODEPREM stays 163.10; fees stay 0 |
| Plan does not undo Closed #145B / #34 | **Met** — VB exclude and leftover source rule unchanged; membership add only |
| Plan does not silently contradict Closed #146 guide “20 policies” | **Met for this gate** — Warren approved 20→21 on 2026-09-22; #146 docs/guide update is a Development/Closure obligation, not a missing input |

---

## Gate result

**PASS (MET)** — Framework auto-chain continues to Risk in this session.

Accepted assumptions:

1. Identity is the one new key `9010969231` plus the existing 20, not `BILLING_REASON=PC`.  
2. Warren authorized this **allowlist expansion** of Closed #146 on **2026-09-22**.  
3. Companions come out with QuikIsrr because they are the same event.  
4. `$2,899.79` is valuation after false 0561 processing, not a conversion premium to map.  
5. A **fresh** QLAdmin valuation has **not** been run and is **not** claimed PASS. It is a Validation/UAT criterion.  
6. Stage-model override to Cursor Grok 4.6 is Warren-approved **2026-09-22**.

## Blockers

None.

## Recommended tracking status

**Dependency Gate PASS → Risk Complete (pending separate Development approval)**
