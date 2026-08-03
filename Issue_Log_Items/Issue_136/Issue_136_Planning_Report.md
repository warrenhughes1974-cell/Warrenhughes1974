# Issue #136 — Planning Report

**Issue ID:** #136  
**Framework stage:** Planning  
**Date:** 2026-08-02  
**Track:** Internal only  
**Coding:** Not started

---

## Objective

Make QuikPlan Plan Values Options (category checkboxes / `*VARY*` / `PLANVALOPT`) report **only real loaded-rate variation**, fleet-wide, while preserving TESTRD-style default keys for structure.

---

## Proposed approach (surgical)

### 1. Redefine dimension enablement in `derive_plan_flags()`

File: `qla_core/quikplan_rate_variation_flags.py`

| Flag group | New rule |
|------------|----------|
| `GDVARY{family}` | `Y` iff real rows for that family have **>1** distinct gender (unchanged intent; ensure defaults/`0` alone do not count as multi) |
| `UWVARY{family}` | `Y` iff real rows have **>1** distinct UW class |
| `BDVARY{family}` | `Y` iff real rows have **>1** distinct band **or** a band other than default `00` with real differentiation — **not** merely because any real row exists |
| `STVARY{family}` | `Y` iff real rows have **>1** distinct state/country tuple **excluding** sole default `0000\|00` — **remove** special-case `STVARYGP=Y` on any GP presence |
| Family absent | Skip family entirely when `real_row_count == 0` for that family (already present; verify DB/DV do not inherit from other families) |

Default key markers (`real=False`, Values=N companions) continue to be ignored.

### 2. Soften / retarget Issue #96 `apply_factor_table_pvo_enablement()`

Current: any QuikCvs/QuikTvs rows ⇒ force `PLANVALOPT`, `GDVARYCV/TV`, `BDVARYCV/TV`.

Planned:
- Do **not** force `BDVARY*` from mere factor presence
- Do **not** force `GDVARY*` unless Gender multi-value is true for that family
- Prefer relying on post-`derive_plan_flags` results; if Issue #96 must remain for QLAdmin usability, limit it to setting `PLANVALOPT=Y` only when that family’s legitimate VARY flags already include at least one `Y`, or document that factor tables + Gender/UW-only is sufficient

### 3. Preserve unchanged (regression fence)

- A3 default keys still emitted
- Default-only plans: `PLANVALOPT=N`, all VARY `N`
- Independent CV/TV UW collapse
- `PAR=0` without real `QuikDvs`; `DEFICIENCY=N`
- LOANINTX / QuikLoan
- Schema / field order
- Claims tables

### 4. Tests to add (before / with Development)

| Test | Assert |
|------|--------|
| Real GP rows, Band=`00` only | `BDVARYGP=N`, `STVARYGP=N` |
| Real GP Gender F/M + UW multi, Band/State default | `GDVARYGP=Y`, `UWVARYGP=Y`, Band/State `N` |
| No QuikDvs | all `*VARYDV=N` |
| No QuikDbs | all `*VARYDB=N` |
| Multi-band real factors (synthetic) | `BDVARY*=Y` for that family only |
| Multi-state real factors (synthetic) | `STVARY*=Y` for that family only |
| Issue #96 path | does not re-force Band from QuikCvs/QuikTvs presence alone |

### 5. Validation gold (Output + UAT)

Primary: **1658C1** — Band all N; DV all N; State all N; no DB flags without QuikDbs; Gender/UW for GP/CV/TV only if factor values support.

Fleet scan: count of plans with `BDVARY*=Y` or `STVARY*=Y` must equal plans with genuine multi-band / multi-state factor evidence (expected near-zero unless extracts prove otherwise).

Publish corrected `quikplan.csv` to `Output/Test_Validation/` and redeploy via DBF Append Tool to Q after Validation PASS.

---

## Blast radius

| Touched | Risk |
|---------|------|
| `quikplan.csv` VARY / PLANVALOPT columns | Primary — all 141 plans |
| Rate CSVs / keys | **No change intended** |
| Issue #77 historical expectations / audits | Docs + validators must be updated to #136 |
| Issue #96 behavior | Must not regress QLAdmin’s ability to open CV/TV when Gender/UW legitimately vary |

---

## Work estimate

Surgical flag-logic + tests + rebatch/validate/redeploy. No architecture redesign.

---

## Open decisions for Dependency Gate / Risk

1. Exact Band rule: `>1` distinct band codes **vs** any band ≠ `00`? (Recommend: enable only if set of bands after removing sole-default case has real multi-value differentiation — i.e. more than `{00}` or multiple non-default bands with differing rates.)
2. Exact State rule: same for `{0000|00}` only.
3. Issue #96: confirm with Validation that Gender/UW-driven `PLANVALOPT=Y` is enough for QLAdmin to use QuikCvs/QuikTvs without Band forced on.
4. Gender/UW for 1658C1: confirm factor **values** differ across Sex/UW (keys already show multi codes — Luna: verify values).