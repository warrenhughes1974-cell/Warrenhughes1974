# Issue #96 — Risk Review Report

**Issue:** #96 — CSO valuation cannot use SAL MULTPL / L17 RV rates (PVO + QuikPl* wiring)  
**Framework stage:** Risk Agent (G3)  
**Status:** **GO — Ready for Development** (awaiting user approval)  
**Generated:** 2026-07-22  
**Agent:** Cursor Grok 4.5 (Risk)  
**Model override (user 2026-07-22):** Grok 4.5 allowed through Development; stop only for Dev approval; after Dev → Validation then stop; after Validation → Closure chain

**Status note:** Risk analysis only — no production code changes in this stage.

---

## Go / No-Go Recommendation

**GO** — Scope is small, sources and targets are confirmed, QuikTvs inheritance already PASSes, and the only durable work is wiring `quikplan` PVO + `1SALMI` QuikPlTv/QuikPlCv so CSO valuation can use rates already in Output.

Rationale: ~**103** ValxLife gap rows on focus plans are `QLA_ZERO` (~**$94.9k** Valx reserve) while TV grids exist. Temporary Output patch proves desired end-state; Development must bake it into emit so full batch does not regress.

---

## 1. Current vs Proposed Mapping

| Target | Current (pre-patch batch / durable emit) | Proposed | Change? |
|--------|------------------------------------------|----------|---------|
| `QuikTvs` SAL/L17 Track 1 | Already inherited (508 / 38) | Unchanged | **No** |
| `quikplan` `10L171`/`10L172`/`117JPO` | `PLANVALOPT=N`, TV vary blank/`0` | `PLANVALOPT=Y`, `GDVARYTV=Y` (+ #77 BDVARYTV etc.) | **Yes** |
| `quikplan` `1SALMI` | `GDVARYTV/CV=N` | `GDVARYTV/CV/GP/DB=Y` (match SAL OL family) | **Yes** |
| `QuikPlTv` `1SALMI` | Blank / incomplete | Copy codes from `1SALOL` (O1/4/1 …) M+F | **Yes** |
| `QuikPlCv` `1SALMI` | 1 blank M stub | Copy codes from `1SALOL` (O1/Q1/4/0) M+F | **Yes** |
| L17 `QuikPlTv`/`QuikPlCv` | Already coded (#80) | Keep | **No** (unless batch order regresses PVO) |
| Track 2 RV (L01/L05/L07/667 ART) | Held / LifePRO zeros | Held | **No** |

### Desired end-state (already mirrored in patched Output / load package)

| Plan | PLANVALOPT | GDVARYTV | QuikTvs | QuikPlTv | QuikPlCv |
|------|:----------:|:--------:|--------:|---------:|---------:|
| `1SALOL` | Y | Y | 508 | 2 | 2 |
| `1SALMI` | Y | Y | 508 | 2 (O1/4/1) | 2 (O1/Q1/4) |
| `1SALML` | Y | Y | 508 | 2 | 2 |
| `1L17SP` + 4 children | Y | Y | 38 each | 2 each | 2 each |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| Issue #25 MPOLICY padding | **No** |
| Issue #26 / #88 `quikridr.MPREM` | **No** |
| `quikmstr` / claims / memo | **No** |
| QuikTvs factor values (SAL OL / L17 grids) | **No** |
| Annuity A* `PLANVALOPT=N` (Issue A A8e) | **No** — guard required |
| Issue #95 QuikUint / PDINTTBL | **No** |
| Track 2 zero-RV plans | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `qla_core/rate_pipeline.py` | non_cv inheritance + CSO setup emit order |
| `qla_core/rate_inheritance_loader.py` | Manifest RV → QuikTvs |
| `qla_core/quikplan_rate_variation_flags.py` | R7A/R7B PLANVALOPT / *VARY* |
| `qla_core/quikplan_converter.py` | `apply_rate_variation_flag_enrichment` |
| `qla_core/cso_valuation_setup.py` | QuikPlCv / QuikPlTv assumption codes |
| `qla_core/issue_a_plan_setup.py` | Annuity PVO clear — must not break |
| `approved_first_pass_scope.csv` | SAL/L17 RV Yes rows |
| `docs/Valuation/load_package_SAL_L17_RV_20260722/` | UAT target package (patched) |
| `validate_l17_rv_inheritance_v5825.py` | QuikTvs inheritance PASS |

---

## 4. Population Analysis

### Valuation symptom (pre-wiring effectiveness)

Source: `docs/Valuation/analysis/reserve_gap_population.csv`

| Metric | Count |
|--------|------:|
| Focus-plan gap rows (`ql_code` in SAL/L17 set) | 142 |
| Of which `QLA_ZERO` | **103** |
| Valx reserve on those QLA_ZERO rows | **~$94,868** |

| ql_code | Gap rows | QLA_ZERO |
|---------|----------:|---------:|
| `1SALMI` | 116 | **78** |
| `10L171` | 7 | 7 |
| `17MJPO` | 6 | 6 |
| `1SALOL` | 6 | 5 |
| `117JPO` | 4 | 4 |
| `10L172` | 3 | 3 |

### Conversion blast radius (durable emit)

| Artifact | Rows / plans touched |
|----------|---------------------:|
| `quikplan` PVO flags | **4–5 plans** (`1SALMI`, `10L171`, `10L172`, `117JPO`; confirm `17MJPO` already Y) |
| `QuikPlTv` `1SALMI` | 1→**2** rows (codes filled) |
| `QuikPlCv` `1SALMI` | 1→**2** rows (codes filled) |
| `QuikTvs` | **0** value changes |
| Annuity A* PLANVALOPT=Y today | **0** (must stay 0) |

---

## 5. Fallback Recommendation

| Option | Assessment |
|--------|------------|
| A. Durable emit: PVO after rates + `1SALMI` Pl* inherit from `1SALOL` | **Recommended** |
| B. Keep Output-only CSV patch (no engine change) | **Reject** — full batch regresses |
| C. Invent Track 2 RV factors | **Reject** — Eric hold |

**Recommended fallback:** Option A only. If R7B gender rule alone cannot set `GDVARYTV=Y` for single-gender TV keys, add explicit rule: **QuikTvs rows > 0 ⇒ `GDVARYTV=Y` and `PLANVALOPT=Y`** for that plan (life plans only; skip A-prefix / Issue A annuity clear).

---

## 6. Trace Policies

| Policy (Valx) | Plan | Before (unwired) | After (desired) |
|---------------|------|------------------|-----------------|
| `901ML8307` | `1SALMI` | TV present; PlCv blank; GDVARYTV=N; QLA resv 0 | Pl* = SAL OL; GDVARYTV=Y; valuation path open |
| `9011258158` | `10L171` | TV=38; PLANVALOPT=N | PLANVALOPT=Y; GDVARYTV=Y |
| `9011227611` | `117JPO` | TV=38; PLANVALOPT=N | PLANVALOPT=Y; GDVARYTV=Y |

---

## 7. Top Changes

Not a money-field remap. Largest impact is enabling reserves on **`1SALMI` (78 QLA_ZERO)** plus L17 children (**20 QLA_ZERO**).

---

## 8. Regression Surfaces

| Surface | Guard |
|---------|-------|
| Issue #77 fleet PVO | Limit force-Y to plans with QuikTvs / focus set; re-scan after inheritance |
| Issue #80 CSO codes | Copy from `1SALOL` only for `1SALMI`; do not invent |
| Issue A A8e annuities | Assert A-prefix stay `PLANVALOPT=N` |
| QuikTvs grids | Assert SAL/L17 inheritance validator still PASS |
| Emit order | Inherit → Pl* keys → R7B PVO (document in Dev notes) |
| #25 / #26 / #88 | Untouched |

---

## 9. Recommended Development Agent Task (surgical)

1. In rate/quikplan pipeline: after non-CV inheritance and CSO Pl* emit, ensure PVO enrichment sees final `Output/rates` (or in-memory equivalents).
2. For plans with QuikTvs > 0 (Track 1 focus minimum): set `PLANVALOPT=Y`, `GDVARYTV=Y`, and appropriate `GDVARYCV=Y` when QuikCvs present (`1SALMI`).
3. When emitting/inheriting for `1SALMI`, copy QuikPlTv + QuikPlCv assumption fields from `1SALOL` (M+F).
4. Bump `APP_VERSION` in **both** `app.py` and `QLA_Migration/app.py`.
5. Add/extend validator: eight-plan QuikTvs + PVO + PlTv/PlCv codes.
6. Re-emit rates + quikplan (or full batch if required); publish `Test_Validation`; do **not** leave Output-only manual patches as the only fix.

**Model for Development (user override):** Cursor Grok 4.5 (normally Composer 2.5).

---

## 10. Validation / Regression Checklist

- [ ] `validate_l17_rv_inheritance_v5825.py` PASS  
- [ ] Focus plans: `PLANVALOPT=Y`, `GDVARYTV=Y`  
- [ ] `1SALMI` QuikPlTv/PlCv == `1SALOL` codes (M+F)  
- [ ] Annuity A* still `PLANVALOPT=N`  
- [ ] QuikTvs row counts unchanged for non-focus plans (spot)  
- [ ] `Test_Validation/` updated with modified `quikplan` + rate tables  
- [ ] User: reload QLAdmin from load package / Test_Validation → re-run Life Reserve Valuation → rebuild ValxLife compare  

---

## 11. Gate Criteria (G3)

- [x] Go/No-Go published (**GO**)  
- [x] Impact quantified (103 QLA_ZERO; ~$94.9k Valx; 4–5 plans PVO; 1SALMI Pl*)  
- [x] Untouched fields listed  
- [x] #25 / #26 preservation confirmed  
- [ ] **User acknowledges and approves Development**

---

## Recommended next prompt

```
Approved for Development — Issue #96
```

(Use Grok 4.5 per your override. After Dev completes, proceed to Validation and **stop**. After Validation PASS, continue through Closure.)
