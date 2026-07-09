# Issue #40 — Validation Report

**Issue:** Inherited Cash Value Rate Load  
**Date:** 2026-07-06  
**Validation result:** PASS — 100% source-to-QLA parity for all 10 approved inherited plans  
**Generated evidence:** `Issue_Log_Items/Issue_40/evidence/`

---

## 1. Validation summary

| Check | Result |
|-------|--------|
| V40-01 Issuing plan row count | **PASS** — all 10 plans > 0 QuikCvs keys (was 0 at intake) |
| V40-02 Rate-owner plan unchanged | **PASS** — all rate-owner plans retain QuikCvs keys |
| V40-03 Source row coverage | **PASS** — **0** mismatches across **101,793** inherited source rows |
| V40-04 Plan code on emit | **PASS** — all inherited cells under issuing plan code |
| V40-05/06/07 Anchor points | **PASS** — 30 / 30 (first / mid / age-100 per plan) |
| V40-08 Emitted CSV = grid | **PASS** — `QuikCvs.csv` matches grid at anchor keys |
| V40-09 QuikPlCv key | **PASS** — pipeline generates QuikPlCv keys for issuing plans |
| V40-10 No duplicate cells | **PASS** — 0 inherited-plan grid collisions |
| P-GL85-02 Inherited vs owner | **PASS** — 100 / 100 comparisons: `17085M` = `170858` values at same QL duration |
| Issue #37 regression | **PASS** |
| Issue #41 regression | **PASS** — 5 / 5 endpoint examples |

---

## 2. Fleet results (post-fix)

| Plan | QuikCvs keys | Source rows checked | Mismatches |
|------|-------------:|--------------------:|-----------:|
| `17085M` | 1,002 | 9,028 | 0 |
| `1L10SO` | 3,285 | 29,018 | 0 |
| `1L10SR` | 3,246 | 28,479 | 0 |
| `1668SP` | 1,081 | 9,625 | 0 |
| `1SALMI` | 516 | 4,572 | 0 |
| `1SALML` | 516 | 4,572 | 0 |
| `1666AI` | 541 | 4,805 | 0 |
| `280PUA` | 496 | 4,143 | 0 |
| `265PUA` | 383 | 3,479 | 0 |
| `261PUA` | 486 | 4,069 | 0 |

**Total QuikCvs factor rows:** 38,047 (includes direct + inherited fleet)

---

## 3. GL85 anchor proof

| Proof | Result |
|-------|--------|
| P-GL85-01 `17085M` key count | **1,002** keys (was 0) |
| P-GL85-02 `17085M` vs `170858` values | **Identical** at same QL duration index; different PLAN |
| P-GL85-03 Rate owner | **`670 GL85-8`** per manifest |
| P-GL85-04 Client UAT | **Pending** — policies `010367438C`, `010615191C`, `010464869C` |

Evidence: `evidence/issue40_gl85_inherited_vs_owner.csv`, `evidence/issue40_inherited_cv_anchor_points.csv`

---

## 4. Validation commands

```powershell
python "QLA_Migration\_validate_issue40_inherited_cv_source_parity.py"
python "QLA_Migration\_validate_issue37_quikcvs_placement.py"
python "QLA_Migration\_validate_issue41_quikcvs_endpoint.py"
```

---

## 5. Closure status

**Development / G5 validation:** PASS  
**Client UAT (G7):** Pending reload of `QuikCvs.csv` + `QuikPlCv.csv` and CV calc on ≥ 2 policies from `Issue_40_Population.csv`
