# Issue #27 — Proposed Fix (Planning Revision)

**Issue:** SL Phase of Insurance  
**Date:** 2026-06-28 (revised)  
**Version:** v57.38  
**Status:** Planning complete — **Development authorized pending this revision**

---

## 1. Updated business rule (client-confirmed)

QLAdmin handles **Substandard Life through its rating structure**, not as a separate coverage phase.

Therefore:

| Rule | Requirement |
|------|-------------|
| SL is not coverage | `BENEFIT_TYPE = SL` must **not** emit to `quikridr` |
| No duplicate face | SL must **not** duplicate base face amount |
| Base is sole death benefit | Only BA/BF (and legitimate riders such as PU/PUA) remain as coverage phases |
| Rating structure | Substandard handled by QLAdmin product/rate architecture — **not** by an SL quikridr row |

---

## 2. Investigation conclusions (pre-Development)

### 2.1 Is `SL_TABLE_CODE` required for QLAdmin substandard rates?

**No — not in current conversion scope.**

| Evidence | Finding |
|----------|---------|
| Rulebooks / crosswalks | **Zero** mappings for `SL_TABLE_CODE` |
| Fleet quikridr output | `MSPCODE` blank on **169/169** rows across all 67 SL policies |
| quikridr `MUWCLASS` | Mapped from PPBEN `UNDERWRITING_CLASS` — **not** from `SL_TABLE_CODE` |
| QLAdmin rate resolution | Uses `PLAN + Gender + UWCLASS + Band + State` via `QuikPlUw` / `UWVARY*` flags — product setup, not LifePRO table code |
| Current v57.38 batch | Substandard policies already run with **no** `SL_TABLE_CODE` conversion |

**Conclusion:** QLAdmin substandard rating calculations do **not** depend on converting `SL_TABLE_CODE`. Suppressing SL rows will **not** break rate selection.

### 2.2 Premium impact of suppression

| Check | Result |
|-------|--------|
| `quikmstr.MMODEPREM` vs PPOLC (28 premium-bearing SL policies) | **28/28 match** (±$0.10) |
| SL premium pattern | 21/28 additive extra; 7 partial edge cases — total already on policy master |
| Example `010448806C` | SL premium = $0; `MMODEPREM` = $62.40 unchanged |

**Conclusion:** Suppressing SL quikridr rows does **not** remove total policy premium.

### 2.3 Duplicate face elimination (67-policy validation)

Simulated removal of all 68 SL quikridr phases:

| Metric | Before | After SL suppression |
|--------|-------:|---------------------:|
| Policies with duplicate face (same MPLAN + amount) | **46** | **0** |
| Remaining duplicate death benefits | 68 SL phases | **0** |
| quikridr rows removed | — | **68** (7,002 → 6,934) |

**Validation artifact:** `Issue_27_SL_Suppression_Validation.json`

**Note:** 8 SL rows have face amounts that do **not** exactly match base (GL85-M unit scaling, partial paid-up context). These are **not** independent death benefits — removing them eliminates misleading coverage display without creating new duplicates.

---

## 3. Recommended fix (single phase — no table-code mapping)

### Option A — **Suppress SL from quikridr emit** (ONLY authorized approach)

**Mechanism:**

1. Extend existing UV/FV filter in `app.py` quikridr batch to exclude `BENEFIT_TYPE = 'SL'`.
2. Before filter: capture SL row audit data (`policy`, `seq`, `SL_TABLE_CODE`, `MODE_PREMIUM`, `amount`) → `Issue_27_SL_Suppression_Audit.csv`.
3. **Do not** merge SL premium into base `MPREM` — `MMODEPREM` already holds total.
4. **Do not** map `SL_TABLE_CODE` in Phase 1 — deferred (see §4).

**Why this is sufficient:**

- Fixes all 46 duplicate-face policies and 0 remaining duplicates fleet-wide
- Aligns with client business rule (rating structure handles substandard)
- Mirrors proven UV/FV non-coverage filter pattern
- No rulebook or crosswalk changes required

### Options B–D — Rejected

| Option | Reason rejected |
|--------|-----------------|
| B — Zero-face SL row | Still shows phantom SL phase |
| C — Non-product governance only | Over-engineered; filter is sufficient |
| D — QLAdmin-side fix | Defect is in converted `quikridr.csv` |

---

## 4. `SL_TABLE_CODE` recommendation

| Decision | **DEFER** to future enhancement |
|----------|--------------------------------|
| Phase 1 (this fix) | Suppress SL only — **no** `SL_TABLE_CODE` conversion |
| Rationale | Not required for rate calculations or premium integrity; never mapped today |
| Future (optional) | If client wants table rating visible in QLAdmin UI, map `SL_TABLE_CODE` to client-approved field (`MSPCODE`, `MISSCLASS`, or other) in a separate issue |
| Audit | Suppression audit CSV preserves LifePRO table codes for traceability |

---

## 5. Implementation sketch (Development — Phase 1 only)

```
PPBEN load
  → capture SL rows + PPBENTYP SL_TABLE_CODE for audit CSV
  → filter BENEFIT_TYPE = 'SL' from quikridr source (extend UV/FV filter)
  → existing quikridr conversion for remaining rows
```

| File | Change |
|------|--------|
| `app.py` / `QLA_Migration/app.py` | SL filter + audit hook (~30–40 lines) |
| `qla_core/sl_benefit_governance.py` | Optional — audit helper |
| `tools/validators/validate_issue27_sl_quikridr.py` | New validator |

**Not in scope:** Rulebooks, crosswalks, `SL_TABLE_CODE` mapping, premium merge, quikmemo.

---

## 6. Acceptance criteria

1. `010448806C`: quikridr **2 phases** (BA + PUA), not 3; no duplicate 5,778 face.
2. Fleet: **0** quikridr rows from PPBEN `BENEFIT_TYPE = SL`.
3. Fleet: **0** duplicate face pairs (same MPLAN + MUNIT×MVPU) on SL-policy population.
4. `010448806C`: `MMODEPREM` unchanged ($62.40).
5. Protected issues #21M, #21M-FU, #21K, #25, #26, #28, #21D, #21J rollback — PASS.

---

## 7. Planning recommendation

**Authorize Development (Phase 1)** — SL suppression only.

Business rule clarified; investigation confirms suppression is safe for QLAdmin rating calculations and premium integrity. `SL_TABLE_CODE` conversion deferred.

---

**Proposed fix status:** ✅ COMPLETE (planning revision)
