# PSUBSSEG Rate Substitution — Dependency Gate

**Date:** 2026-08-31
**Framework stage:** Dependency Gate
**Status:** **PASS for Tranche 1** (Tranche 2 dependency documented, not blocking)

---

## 1. Checklist

### Source data

| Check | Met? |
|---|---|
| PSUBS/PSUBSSEG extracts present and parsed | **Met** — `docs/New_Segments/` (3,048 / 170,688 rows); copy into `QLA_Migration/Source/` planned at Development |
| Tranche 1 source segments present with rates | **Met** — `L10 LP9595` (12,384 PDAGE pages), `L10 LP95SR`/`L10SR 95` (2,064 each), `L17` CV/NP (360/624), `667 ART` NP (288 PAAGERAT), premium owners (~2,850 PAAGERAT) |
| Tranche 2 source segments | **NOT HELD** — 13 segment IDs; blocks Tranche 2 only; request drafted |
| Extract dates align with valuation batch | **Met** — PDAGE/PAAGERAT 20260714/20260731 dated twins; PPBEN 20260630 |

### Field definitions

| Check | Met? |
|---|---|
| QLAdmin target tables/keys confirmed | **Met** — Help 7.183/7.217 (QuikPlTv/QuikTvs), EFFDATE in key |
| EFFDATE band selection semantics | **Met** — confirmed by Warren 2026-08-31 (latest EFFDATE ≤ issue date) |
| SEQ slot → segment type map | **Met** — New Era SQL (`PSSUBSSEG_SegtFlag_Query.sql`): 1=PR, 2=CV, 12=RV, 13=NP |
| Duration conventions | **Met** — reuse shipped #106 RV identity / CV native-first / NP−1 |
| 19950101 QuikPlTv basis fields | **Assumed** (OI-1) — crosswalk first, copy-forward fallback flagged to Eric |

### Client clarification

| Check | Met? |
|---|---|
| Substitution rule meaning | **Met** — New Era readme + data dictionary in package |
| Scope boundary (Tranche 1 vs 2) | **Met** — internal decision, documented in Intake |
| `5667AT` zero-RV handling | **Assumed** (OI-2) — leave absent; flagged for Warren at Dev approval |
| UAT acceptance | **Met** — anchor policies per band + full-grid value compare |

### Evidence

| Check | Met? |
|---|---|
| Example policies per era band | **Met** — Intake table (active policies, both bands) |
| Before-state measurable | **Met** — 213-row reconciliation CSV with value-overlap scores |
| Wrong-value proof | **Met** — `1L10SO` overlap 0.08–0.37; `1L10OD` post-95 policies on pre-95 values |

### Regression guards

| Check | Met? |
|---|---|
| #106 RV identity duration preserved | **Met** — conventions reused, not modified |
| #96 L17 full annual RV untouched | **Met** — loader skips already-emitted keys |
| #40/#42 inheritance/miss-fill untouched | **Met** — additive step; collision gate active |
| Unaffected plans byte-identical | **Met** — hard regression requirement in plan |
| DBF append-only flow | **Met** — CSV emit only; packaging via Desktop DBF Append Tool unchanged |

---

## 2. Gate status

**PASS** — proceed to Risk for Tranche 1.

Tranche 2 is **BLOCKED on New Era data** (13 segment IDs) and is explicitly out of
this Development scope; it does not gate Tranche 1.

## 3. Documented assumptions (non-blocking)

| ID | Assumption | Confirm |
|---|---|---|
| A1 | TYPE_FLAG 0 records govern base-coverage rate slots (2/4 variants not rate-bearing for our four types) | Development probe re-verifies before emit |
| A2 | 19950101 is the correct band cut for all Tranche 1 era plans (from PSUBS record dates; `1L10SO` first band 1994 emits as 19000101 base) | Validator asserts band dates == PSUBS dates |
| A3 | Premium-fill plans accept attained-age PR emit under their VarGP config | OI-3 skip-and-report guard |

## Gate criteria (G2)

- [x] Dependency gate published
- [x] Status PASS (scoped)
- [x] No code changes
