# Issue #119 — Risk Review Report

**Issue:** #119 — PUA coverage MPAR must be 0 (non-participating)  
**Date:** 2026-07-27  
**Framework stage:** Risk complete (G3)  
**Code changes:** none (prohibited)  
**Dependency Gate:** PASS

---

## Go / No-Go

### **GO**

Robert’s rule is clear, blast radius is a single field on ~493 PUA rows, and the emit hook (`_apply_pua_rider_inheritance`) already isolates PUA riders. The main residual risk is **validator / accountability drift** if `#105` v1.1 and the briefing §10 check are not updated in the same release.

---

## 1. Does the defect exist?

**Yes.** Current Output:

| Metric | Value |
|--------|------:|
| Synthetic `*PA` PUA rows | 494 |
| `MPAR = 1` | **493** |
| `MPAR = 0` | 1 |
| PUA `MPAR` == phase-1 base `MPAR` | **494 / 494** |

Mechanism:

1. `#105` sets `MPAR` from `quikplan.PAR` while `MPLAN` is still the catalog PUA code (`170PUA`, `1POPUA`, …) — those plans are mostly `PAR=1`.  
2. Inheritance rewrites `MPLAN` → `xxxxPA` and does **not** clear `MPAR`.  
3. `#111` taught validators that matching the base is correct — that assertion must reverse.

Robert / briefing §7.2: PUA is non-participating; QL sets PAR/`MPAR` to **0** on the PA coverage.

---

## 2. Before / after impact

| Population | Before | After |
|------------|--------|-------|
| PUA `MPAR=1` | 493 | **0** |
| PUA `MPAR=0` | 1 | **494** |
| Non-PUA `MPAR` | unchanged | unchanged |
| `quikplan` rows | unchanged | unchanged |
| Other `quikridr` columns | unchanged | unchanged |

Largest plan buckets flipping 1→0 (approx.): `1708PA` ~415, `1960PA` ~71, plus small `280EPA` / `221EPA` / `1705PA` / `2665PA`.

Control: base `9010143726C` / `221END` stays `MPAR=1`.

---

## 3. Fallback options

| Option | Impact | Recommendation |
|--------|--------|----------------|
| **A. Force `MPAR=0` in `_apply_pua_rider_inheritance`** | 493 flips; surgical | **Prefer** |
| B. Force after emit via post-pass on `*PA` only | Same rows; misses if detection drifts | Reject vs A |
| C. Change catalog `quikplan.PAR` for `*PUA` plans to 0 | Touches product setup; does not fix synthetic path alone | Reject |
| D. Do nothing / keep base-match | Conflicts with Robert | Reject |

---

## 4. Regression surfaces

| Surface | Risk | Mitigation |
|---------|------|------------|
| Non-PUA `#105` product PAR | Medium if coded broadly | Touch only PUA inheritance path |
| `#105` / accountability validators | High if left on base-match | Update in same Development package |
| Briefing §10 vs §7.2 contradiction | Medium (client confusion) | Fix builder bullet + regenerate docx |
| `#111` closed summary | Low (docs history) | New issue supersedes participation claim only |
| Dividend / QuikBenh type 4 | Low | No field overlap with `MPAR` |
| `#2` / `#26` | None | Untouched |

---

## 5. Unrelated fields — must remain unchanged

`MPLAN` synthesis, `MEFFDATE` / `MPAYUP` / `MAGE` / `MPHSTAT` inheritance, `MUNIT`/`MVPU`, `MPREM`, fees, MPOLICY width, `quikplan` membership (no PA plan emit).

---

## 6. Trace (simulated after)

| MPOLICY | MPHASE | MPLAN | MPAR after |
|---------|--------|-------|------------|
| 9010310404C | 2 | 1960PA | **0** |
| 9010150910C | 3 | 221EPA | **0** |
| 9010360290C | 2 | 1708PA | **0** |
| 9010391228C | 2 | 1970PA | **0** |
| 9010143726C | 1 | 221END | **1** |

---

## 7. Recommended Development task (surgical)

1. In `app.py` / `QLA_Migration/app.py` `_apply_pua_rider_inheritance`: after PUA confirmed, `row_data["MPAR"] = "0"`.  
2. Bump `APP_VERSION` both copies.  
3. `tools/validators/validate_issue105_mpar.py`: for PUA codes / PUA products, expect `MPAR=="0"` (stop resolving expected PAR through base). Keep non-PUA product-PAR checks.  
4. Mirror in `validate_issue_log_accountability.py` `#105` spot-check.  
5. `tools/_build_pua_omaha_briefing.py` §10: replace “matches its base coverage” with “PUA participating flag is 0”; regenerate `PUA_CSO_Conversion_Briefing.docx` if delivering.  
6. Rebatch `quikridr`; run `#105` validator + accountability; publish `Output/Test_Validation/quikridr.csv` on PASS.

---

## 8. Validation / Regression checklist

- [ ] All PUA rows `MPAR=0` (expect 494 / 494 on current book)  
- [ ] Zero non-PUA rows with plan `PAR=1` and `MPAR≠1` (`#105` preserved)  
- [ ] Zero non-PUA rows with plan `PAR=0` and `MPAR=1`  
- [ ] Trace policies above  
- [ ] Header / column order unchanged  
- [ ] Accountability `#105` / `#119` IN_DATA after Output refresh  

---

## 9. Recommendation to project lead

**GO for Development** after explicit user approval (“Approved for Development”).

Do **not** treat `#111` as blocking — that closure accepted the wrong participation rule; this issue corrects it without reopening PA plan-file design.
