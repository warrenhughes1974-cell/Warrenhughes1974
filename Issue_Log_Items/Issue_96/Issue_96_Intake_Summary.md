# Issue #96 — Intake Summary

**Issue:** #96 — CSO valuation cannot use SAL MULTPL / L17 RV rates (PVO + QuikPl* wiring)  
**Framework stage:** Intake Agent (G0)  
**Status recommendation:** Intake Complete → Planning  
**Generated:** 2026-07-22  
**Owner:** Conversion  
**Reporter / UAT:** Eric (LifePRO segment pointing) + internal valuation compare  
**Priority:** High (CSO reserve valuation / ValxLife gaps)  
**Model:** Cursor Grok 4.5 (locked Intake stage)

---

## Client symptom (verbatim / paraphrased)

> The SAL MULTPL is set up to point at the RVs for SAL OL in LifePRO and the L17 items point to the RVs for L17 in LifePRO. There do appear to RV factors for the SAL OL and L17 policy forms.

Normalized from Eric 2026-07-22 Track 1 note + valuation reload attempt:

- LifePRO: **SAL MULTPL → SAL OL** RVs; **L17 children → L17** RVs; factors exist.
- After loading rates and re-running Life Reserve Valuation (06/30/2026), the ValxLife / QLR compare **did not move** on SAL MULTPL / L17 reserve gaps (`QLA_ZERO` population still present).

## Client symptom (normalized)

Conversion already emits inherited **`QuikTvs`** for:

| QLA plan | Source | QuikTvs rows (current Output) |
|----------|--------|-------------------------------:|
| `1SALMI`, `1SALML` | `1SALOL` / SAL OL | 508 each |
| `10L171`, `10L172`, `117JPO`, `17MJPO` | `1L17SP` / L17 | 38 each |

But CSO valuation still shows **QLA reserve = 0** for many of those plans because **plan wiring blocks use of the TV tables**:

1. `10L171` / `10L172` / `117JPO` had `PLANVALOPT=N` and blank/`0` `GDVARYTV` (and related *VARY*).
2. `1SALMI` had `GDVARYTV/CV=N` despite QuikTvs/QuikCvs present.
3. `1SALMI` `QuikPlTv` / `QuikPlCv` assumption codes were blank (or M-only stub) vs populated `1SALOL` (`O1`/`4`/`1` TV; `O1`/`Q1`/`4` CV).

**Note:** A temporary Output/load-package patch was applied 2026-07-22 for UAT reload. This issue exists to **implement the durable conversion emit** so a full batch does not wipe those fixes.

## Example policies

From `docs/Valuation/analysis/reserve_gap_population.csv` (`QLA_ZERO` examples):

| LifePRO / Valx | QLA plan | Symptom |
|----------------|----------|---------|
| `901ML8307` | `1SALMI` | Valx reserve present; QLA 0 |
| `901ML8246` | `1SALMI` | same |
| `9011258158` | `10L171` | same |
| `9011217014` | `10L171` | same |
| `9011227611` | `117JPO` | same |
| `9011227610` | `17MJPO` | same |

Full SAL/L17 `QLA_ZERO` population: ~111 matching rows in reserve-gap CSV (includes anchors above).

## Suspected domain

**Rates / plan setup for CSO valuation** — not annuity QuikAint; not PDINTTBL/#95.

Targets:

- `quikplan` — `PLANVALOPT`, `GDVARYTV` / related *VARY*
- `QuikPlTv` / `QuikPlCv` — assumption codes on inherited plans
- Preserve existing `QuikTvs` inheritance (manifest / non-CV inheritance)

## In scope (first pass)

- Durable emit so SAL MULTPL (`1SALMI`) and L17 children can use inherited RV (and SAL CV) tables in QLAdmin CSO valuation.
- Fix ordering / logic so PVO flags reflect emitted QuikPlTv/Cv/Tvs after inheritance.
- Ensure `1SALMI` QuikPlTv + QuikPlCv assumption codes match `1SALOL` (CSO / parent inheritance).
- Validator(s) for the eight-plan set; publish `Test_Validation` on PASS.
- Do not invent RV factors for Track 2 hold plans (`5L0110` / `5L0510` / `5L075Y` / `5667AT` — LifePRO zeros per Eric).

## Out of scope (first pass)

- Track 2 actuarial zero-RV plans (L01 10Y, L05, L07, 667 ART).
- Issue #95 declared interest / QuikUint.
- Annuity QuikAint promotional rates.
- Changing ValxLife actuarial extract itself.
- Broad redesign of Issue #77 / #80 beyond what’s required for these plans.

## Related issues

| ID | Relationship |
|----|----------------|
| **Rates Inheritance / Eric 7/22** | Track 1 QuikTvs for L17 children + SAL already in manifest (`approved_first_pass_scope.csv`) |
| **#42** | Loaded `1L17SP` NP/RV parent from PDAGE |
| **#40** | SAL CV inheritance; SAL MULTPL fleet context |
| **#77** | Fleet PVO + default keys when rates present |
| **#80** | CSO Valuation_Setup → QuikPlCv/Tv codes (closed; `1SALMI` not fully coded like OL/ML) |
| **Issue A** | Plan-setup checklist; do not regress A1/A8 annuity rules |

## Immediate blockers at intake

None for framing. Planning must confirm whether PVO gap is **order-of-emit** (flags before inheritance) vs **#77 gender rule** (`GDVARYTV` only when >1 gender) vs post-process wipe.

## Artifact inventory

| Artifact | Status |
|----------|--------|
| Eric 2026-07-22 L17/SAL RV note | `Issue_Rates_Inheritance_Validation/.../Eric_20260722_L17_RV_Inheritance_Note.md` |
| Manifest rows for SAL/L17 RV | `approved_first_pass_scope.csv` |
| Validator | `validate_l17_rv_inheritance_v5825.py` → PASS on QuikTvs |
| Current Output QuikTvs / QuikPl* / quikplan | Present; UAT patch applied 2026-07-22 |
| Load package | `docs/Valuation/load_package_SAL_L17_RV_20260722/` |
| Reserve gap population | `docs/Valuation/analysis/reserve_gap_population.csv` |
| Latest QLR (pre-final wiring) | `docs/Valuation/QLReports/* 06-30-26.QLR` @ 15:50 |

## Severity / owner

- **Severity:** High — client-visible CSO reserve zeros for plans with known LifePRO RV factors.
- **Owner:** Conversion (`rate_pipeline` / `quikplan_rate_variation_flags` / CSO PlCv-Tv emit).
- **Client:** Eric for UAT after reload + valuation rerun.
