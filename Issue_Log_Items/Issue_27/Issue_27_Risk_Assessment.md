# Issue #27 — Risk Assessment (Planning Revision)

**Issue:** SL Phase of Insurance  
**Date:** 2026-06-28 (revised)  
**Version:** v57.38  
**Fix status:** Not implemented — Development authorized (Phase 1)

---

## 1. Overall risk if unfixed

| Risk | Level | Impact |
|------|-------|--------|
| Inflated amount insured on display | **High** | 46 policies with duplicate face |
| Client UAT No-Go persists | **High** | Blocks production sign-off |
| Misrepresentation of death benefit | **High** | SL shown as separate coverage |

---

## 2. Investigation risk clearance (pre-Development)

Planning revision validated suppression safety:

| Investigation question | Result | Residual risk |
|------------------------|--------|---------------|
| `SL_TABLE_CODE` required for QLAdmin rates? | **No** — never converted; MSPCODE blank fleet-wide | **None** for Phase 1 |
| Premium loss on suppression? | **No** — 28/28 premium SL policies: MMODEPREM = PPOLC | **Low** — per-phase MPREM display on SL phase removed |
| Duplicate face eliminated? | **Yes** — 46 → **0** across 67 policies | **None** |
| QLAdmin rating structure impact? | **None** — substandard via product rate keys, not SL row | **None** |

**Gate:** ✅ Suppression confirmed safe for QLAdmin substandard rating calculations.

---

## 3. Fix implementation risk (Phase 1 — suppress SL only)

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Loss of total policy premium | **Very Low** | High | Validated 28/28 MMODEPREM match; no premium merge needed |
| QLAdmin rate miscalculation | **Very Low** | High | SL_TABLE_CODE not used today; MUWCLASS/MBAND on base unchanged |
| MPHASE / quikclid breakage | Low | Medium | SL rarely referenced outside quikridr; spot-check sample |
| Over-suppression | Very Low | Low | Business rule confirms SL ≠ coverage for all 68 rows |
| quikridr row count change | Certain | Low | Document 7,002 → 6,934; update validators |
| Loss of table rating visibility | Medium | Low | Deferred — audit CSV preserves SL_TABLE_CODE |

---

## 4. Deferred risk (`SL_TABLE_CODE` — out of Phase 1 scope)

| Risk | Status |
|------|--------|
| Table rating not visible in QLAdmin UI | **Accepted / deferred** — client confirmed rating structure handles substandard |
| Future mapping to wrong field | N/A until enhancement authorized |

---

## 5. Protected issue regression matrix

| Issue | Exposure | Expected |
|-------|----------|----------|
| **#21M** QUIKMEMO | None | PASS |
| **#21M-FU** memo grain | None | PASS |
| **#21K** MRIDRID / field lengths | Low | PASS |
| **#25** MPOLICY width | Low | PASS |
| **#26** MPREM semantics | **Low** | No SL premium merge; base MPREM unchanged |
| **#28** MPLAN authority | Low | PASS |
| **#21D** quikclnt/MDEPINT | None | PASS |
| **#21J** rollback | None | PASS |

---

## 6. Blast radius (Phase 1)

| Component | Impact |
|-----------|--------|
| `quikridr.csv` | −68 rows; 46 policies lose duplicate phase |
| `quikmstr.csv` | **None** |
| `quikplan.csv` | **None** |
| Rulebooks / crosswalks | **None** |
| Rate tables / QuikPlUw | **None** |
| `quikclid.csv` | Verify MPHASE references |

---

## 7. Rollback safety

- Isolated SL filter alongside UV/FV (bounded ~10 lines)
- Suppression audit CSV for traceability
- Revert = remove SL from filter list

---

## 8. Planning-stage risk rating

| Dimension | Rating |
|-----------|--------|
| Root cause confidence | **High** |
| Fix complexity | **Low** (filter only — no UW/premium mapping) |
| Fleet blast radius | **Low** (1.32% of policies) |
| Client decision dependency | **Resolved** — business rule clarified |
| Investigation gate | **PASS** |

---

## 9. Recommendation

**Authorize Development (Phase 1)** — surgical SL suppression.

Risk of **not fixing** exceeds risk of **filter-only suppression**. Investigation confirms no impact on QLAdmin substandard rating calculations or policy-level premium.

---

**Risk assessment status:** ✅ COMPLETE (planning revision)
