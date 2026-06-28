# Issue #27 — Impact Analysis (Planning Revision)

**Issue:** SL Phase of Insurance  
**Date:** 2026-06-28 (revised)  
**Version:** v57.38  
**Detail population:** `Issue_27_SL_Impact_Population.csv`  
**Suppression validation:** `Issue_27_SL_Suppression_Validation.json`

---

## 1. Fleet summary

| Metric | Count |
|--------|------:|
| **Total SL rows in PPBEN** | 68 |
| **Policies with at least one SL row** | 67 |
| **SL rows duplicating base face amount** (±$0.02) | **47** |
| **Policies with duplicate SL face** | **46** |
| **SL rows with premium > 0** | 28 |
| **SL rows emitted to quikridr (current)** | **68** (100%) |
| **SL rows with PPBENTYP `SL_TABLE_CODE` populated** | 66 |
| **quikridr rows if SL suppressed** | 7,002 → **6,934** (−68) |

**Fleet penetration:** 67 / 5,083 policies = **1.32%**

---

## 2. Post-suppression validation (67 policies — all validated)

Simulated removal of all 68 SL quikridr phases against v57.38 batch output:

| Validation check | Result |
|------------------|--------|
| Duplicate face pairs after suppression (same MPLAN + face) | **0** |
| Policies with remaining duplicate death benefit | **0 / 67** |
| Premium-bearing SL policies: MMODEPREM vs PPOLC | **28 / 28 match** |
| SL policies missing quikmstr row | **0** |
| quikridr MSPCODE populated (SL_TABLE_CODE proxy) | **0 / 169 rows** |

**Conclusion:** Suppressing all SL rows eliminates **every** duplicate death benefit in the SL population with **no** premium regression at policy master level.

---

## 3. Impact categories (revised)

### Category A — Duplicate face amount (primary defect) — **FIXED by suppression**

**46 policies** where SL row amount insured equals base benefit face.

Includes **`010448806C`**: BA seq 1 and SL seq 3 both 5,778.00 → quikridr phases 1 and 3 both duplicate.

**After suppression:** 0 duplicate face pairs fleet-wide in SL population.

### Category B — SL with premium (28 rows) — **NO policy-level impact**

SL row premium is substandard extra mortality charge stored on the SL benefit row in LifePRO. **`quikmstr.MMODEPREM` already holds PPOLC total** for all 28 premium-bearing policies (validated).

| Pattern | Count | Suppression impact |
|---------|------:|-------------------|
| Additive (base + SL ≈ PPOLC) | 21 | None on MMODEPREM |
| Partial / edge | 7 | None on MMODEPREM (PPOLC = MMODEPREM) |
| Zero-face premium only | 2 | None — rating metadata |

**Per-phase `MPREM` on SL row removed** — acceptable; SL is not coverage.

### Category C — SL rating-only (zero face, zero premium)

**40 rows** — table code may be populated but no face/premium on SL row.

**After suppression:** No coverage row loss; table code preserved in audit CSV only.

### Category D — SL face differs from base (8 rows) — **NOT duplicate, still suppress**

| Policy | SL face | Base face | Notes |
|--------|--------:|----------:|-------|
| 010373918C | 11,557 | 17,657 | GL85-M unit scaling |
| 010397318C | 7,304 | 3,626 | GL85-M unit scaling |
| 010505481C | 12,338 | 16,510 | GL85-M unit scaling |
| 010549966C | 1,500 | 5,205 | Partial / PUA context |
| 011104570C | 5,000 | 4,145 | Paid-up context |
| 011182954C | 5,000 | 2,612 | Paid-up context |
| 011208333C | 25,000 | 3,172 | CEN II family |
| 011208334C | 50,000 | 7,399 | CEN II family |

These rows do **not** create duplicate face pairs after suppression (validated: **0** remaining duplicates). Per business rule, SL face is substandard rating context — **not** additive death benefit. Suppression is correct.

---

## 4. `SL_TABLE_CODE` impact assessment

| Question | Answer |
|----------|--------|
| Currently converted? | **No** — zero rulebook mappings |
| Required for QLAdmin rates? | **No** — rating via `MUWCLASS`/`MBAND` + product `QuikPlUw` keys |
| Impact if not converted? | **None** on premium or duplicate-face fix |
| Recommendation | **Defer** — capture in suppression audit CSV; optional future enhancement |

---

## 5. QLAdmin rating structure (client business rule)

Client confirmed: **Substandard Life is handled through QLAdmin's rating structure**, not as a separate coverage phase.

| Layer | Role | SL suppression impact |
|-------|------|----------------------|
| `quikplan` + `QuikPlUw` | Product UW class rate segmentation | **None** |
| `quikridr.MUWCLASS` / `MBAND` | Policy phase rate lookup keys (base phase) | **None** — base phase unchanged |
| `quikmstr.MMODEPREM` | Total modal premium (PPOLC) | **None** — unchanged |
| SL quikridr row (current) | Incorrect duplicate coverage display | **Removed** — correct behavior |

---

## 6. Converter output confirmation (current defect)

All **68** SL source rows produce matching **quikridr** rows with:

- `MUNIT` / `MVPU` copied from PPBEN (duplicate face)
- `MPLAN` same as base for 65/68 rows
- `MUWCLASS` from `UNDERWRITING_CLASS` — **not** `SL_TABLE_CODE`
- `MSPCODE` blank — **`SL_TABLE_CODE` never transferred**

---

## 7. Business impact assessment (revised)

| Severity | Area | Post-fix state |
|----------|------|----------------|
| **High** | Duplicate face display (46 policies) | **Resolved** — 0 duplicates |
| **None** | Policy premium integrity | MMODEPREM preserved |
| **None** | QLAdmin rate calculations | Rating structure unchanged |
| **Low** | Table rating visibility | Deferred — audit CSV only |

---

## 8. Validation sample set

| Policy | Reason |
|--------|--------|
| 010448806C | Client example — BA + PU + SL duplicate |
| 010799083C | High SL premium — additive pattern |
| 010770580C | Zero-face SL premium |
| 010373918C | SL face ≠ base (exception — still suppress) |
| 010497264C | Two SL rows on one policy |

---

**Impact analysis status:** ✅ COMPLETE (planning revision)
