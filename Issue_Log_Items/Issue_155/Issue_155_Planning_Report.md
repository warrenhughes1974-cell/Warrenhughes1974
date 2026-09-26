# Issue #155 — Planning Report

**Date:** 2026-09-24  
**Stage:** Planning (G1). No code, rulebook, or Output changes.  
**Scripts (read-only):** `tools/_pfndrdet_rollforward_probe.py`, `tools/_pfndrdet_population_probe.py`, `tools/_ql_seed_proof_test.py`

---

## 1. Executive finding

Loading the LifePRO balance makes QLAdmin's account **exact at the conversion date**. It does **not** keep QLAdmin in step with LifePRO afterwards, because QLAdmin's ISWL monthly calculation on these plans uses different interest, mortality and expense than LifePRO, and none of the three is driven by the tables conversion loads.

Proof test (seed the 6/19/2026 LifePRO balance, apply QLAdmin's own monthly formula taken from Warren's 9/23 anniversary run):

| Policy | Seed 6/19 | QL 7/19 | LifePRO 7/19 | QL 8/19 | LifePRO 8/19 | Drift/month |
|---|---:|---:|---:|---:|---:|---:|
| 9010713704 | 45,551.94 | 45,842.55 | 45,729.12 | 46,143.32 | 45,906.83 | ≈ +$113 |
| 9010713705 | 26,251.74 | 26,417.26 | 26,365.18 | 26,588.63 | 26,479.01 | ≈ +$52 |
| 9010713707 | 8,146.88 | 8,187.28 | 8,170.16 | 8,229.43 | 8,193.53 | ≈ +$17 |

9010713704, July, component split (ties to the penny, +113.43):

| Component | QLAdmin | LifePRO | QL − LifePRO |
|---|---:|---:|---:|
| Interest | 7.0% → 253.90 | 4.5% → 167.41 | +86.49 |
| Mortality / COI | 0.00 | MT 30.39 | +30.39 |
| Expense | $5 + 5% prem = 7.20 | PF 2.08 + load 1.67 = 3.75 | −3.45 |

## 2. Confirmed LifePRO sources

| Source | Grain | Use |
|---|---|---|
| `PFNDR_FundHistory_Extract_20260630.csv` | 1 row/policy, latest monthiversary ≤ cut | Seed balance (`FUND_BALANCE`), date (`VALUATION_DATE`), `GROSS_DEPOSITS`, `LOAN_BALANCE` |
| `PFNDRDET_FundHistoryDET_ISWL_Extract_20260831.csv` | Monthiversary transactions 2002/2003 → 8/2026 | Proof and validation only |
| `PPBEN` FV benefit | 1 row/policy | Cross-check `FV_BALANCE2` (2,170/2,245 equal PFNDR at 8/31) |

PFNDRDET rolls forward to PFNDR `FUND_BALANCE` for 2,139 of 2,268 QL ISWL policies at both cuts. Every interest record 2003–2026 is 4.50%.

## 3. Confirmed QLAdmin target structure

**QuikIswl** (Help §7.146; index `MPOLICY + descending MLASTANNV` — the latest row is the policy's current state). QL's own 6/19/2026 row for 9010713704C: `MMONTH=506`, `MLASTANNV=2026-06-19`, `MACCTBAL=31469.97`, `MSUMPREM=22292.52`, `MUNALLOC=0`.

**quikprmh.MISWL / QuikIsrr.MISWL** — "monthiversary the premium was added to the UL/ISWL account". QL stamps it during anniversary (9010713704C: paid 6/15/2026 → MISWL 6/19/2026). Conversion CSV does not carry `MISWL`, so every converted premium is treated as unapplied.

**QLAdmin ISWL engine (observed, 9/23 run):**

| Driver | Table we load | QL behavior |
|---|---|---|
| Interest | QuikUint 1659C2: 11/9/5/**4.5 from 2002** | Credits **7.0%** every month 2018–2026 |
| COI | QuikCoi rows only for 1658CS, 1679CS | **COI = 0** on all ISWL plans, including 1658CS |
| Expense | QuikIsxp empty | **$5.00** monthly + 5% of premium on all plans |

QLAdmin Help §5.7.9: QuikUint applies to plans with LOB `UNVLFE`; "existing UL plans that have interest rates hardcoded in QLAdmin … are not subject to this UL rate table." Our ISWL plans are `ISWLFE`. Help also says premium expense and surrender charge rate tables "are not yet available".

## 4. Proposed source-to-target mapping (conversion part)

One additional QuikIswl row per ISWL base policy, **kept alongside** the #124 month-0 row:

| QuikIswl field | Value |
|---|---|
| MPOLICY, MLOB | As #124 (`I`) |
| MLASTANNV | PFNDR `VALUATION_DATE` (last LifePRO monthiversary ≤ `QLA_VALUATION_DATE`) |
| MMONTH | Whole months issue → MLASTANNV (9010713704C → 506, matches QL) |
| MACCTBAL, MCASHVAL | max(PFNDR `FUND_BALANCE`, 0.00) |
| MLOANBAL | PFNDR `LOAN_BALANCE` |
| MSUMPREM | PFNDR `GROSS_DEPOSITS` |
| MDB | As #124 (units × 1,000) |
| Others | 0.00 / blank |

Plus: stamp `quikprmh.MISWL` (and `QuikIsrr.MISWL`) for every converted premium/withdrawal dated on or before the seed MLASTANNV, so QLAdmin does not apply them again.

## 5. Open questions

1. **Scope (Warren):** Is the target (a) account exact at the conversion date, or (b) QLAdmin tracks LifePRO monthly after go-live? (a) is conversion-only. (b) needs item 2.
2. **QLAdmin:** Can the ISWLFE plans' interest (4.5%), COI and expense be table-driven, or are they hardcoded? Where does the 7% come from?
3. **QLAdmin:** Does the valuation reserve project the account forward with the same engine (earlier back-solve suggested start- and end-of-year AV)? If yes, reserves stay off even with a correct seed.
4. **QLAdmin:** Confirm anniversary resumes from the latest QuikIswl row and skips premiums with `MISWL` populated.

## 6. Formatting / fallback rules

Money 10.2; dates YYYYMMDD in CSV. Negative LifePRO fund → 0.00 (Warren 2026-09-24; 248 policies, `evidence/issue155_negative_fund_review_list_20260831.csv`). 23 policies with no PFNDR row → keep #124 month-0 only and list.

## 7. Policy key handling

`MPOLICY` from existing QuikIswl/quikridr keys (C-suffix, #25 padding unchanged).

## 8. Estimated record counts

QuikIswl: 2,268 month-0 rows (unchanged) + ~2,245 seed rows. quikprmh: MISWL populated on ISWL-policy rows only. Non-ISWL rows unchanged.

## 9. Sample trace

| Policy | Current QuikIswl | Proposed seed row | quikprmh |
|---|---|---|---|
| 9010713704C | month 0, 0.00 | 2026-06-19, month 506, 45,551.94, MSUMPREM 22,292.52 | 105 rows get MISWL ≤ 2026-06-19 |
| 9010713705C | month 0, 0.00 | 2026-06-19, month 506, 26,251.74 | same pattern |
| 9010713707C | month 0, 0.00 | 2026-06-19, month 506, 8,146.88 | same pattern |
| 9010779727C | month 0, 0.00 | −180,012.63 → **0.00**, listed for review | same pattern |

## 10. Risks and unknowns

| Risk | Level |
|---|---|
| Without `MISWL`, QL re-applies all historical premium on the next monthiversary (≈ +$22k on 9010713704) | **High** — must ship together |
| Post-conversion drift ≈ 3% a year of account until QLAdmin engine matches LifePRO | High (scope question 1) |
| Conflicts with Closed #124 (premise: anniversary rebuilds history) and #21F (quikprmh) | Needs Warren's written OK |
| Adding `MISWL` column to quikprmh CSV — DBF template already has the field; Append tool field mapping to confirm | Medium |
| QuikIssc surrender charges (durations 1–14) could reduce MCASHVAL on young policies | Low — check in Risk |

## 11. Recommended Risk prompt

Simulate the seed + MISWL change on full 6/30 Output: counts, blank checks, non-ISWL quikprmh rows unchanged, #124 month-0 rows unchanged, and QuikIswl seed balance = PFNDR for every seeded policy.

## 12. Recommended Development task (not implemented)

1. `qla_core/quikiswl_loader.py`: add seed-row builder from PFNDR (cut matching `QLA_VALUATION_DATE`), floor at 0.00.
2. quikprmh / QuikIsrr emit: populate `MISWL` for ISWL policies on rows ≤ seed date.
3. Validator `validate_issue155_iswl_seed.py` (fail-closed) + smoke.
4. Full 6/30 batch (`QLA_VALUATION_DATE=20260630`), DBF Append, Warren runs anniversary + valuation in Q, compare QuikValf MACCTBAL to LifePRO.
