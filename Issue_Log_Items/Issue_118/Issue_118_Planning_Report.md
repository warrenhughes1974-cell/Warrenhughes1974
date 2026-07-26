# Issue #118 — Planning Report

**Issue:** #118 — Align QLAdmin underwriting class codes/labels to client "Underwriting Classes by Form"
**Framework stage:** Planning Agent
**Status:** Blocked — Awaiting Client Clarification (see Dependency Gate)
**Generated:** 2026-07-26
**Agent:** Cursor Grok 4.5
**Code changes:** none (prohibited)

---

## 1. Executive Finding

The client spreadsheet is the target **plan membership + code/label catalog**. Today the conversion uses a **single global** LifePRO letter map in `qla_core/rate_dbf_schema.py` (`UWCLASS_MAP` / `RIDER_UWCLASS_MAP`) that is wrong for the client's meaning of `ST` (Standard) vs our current use of `ST` for LifePRO `B` (Blended), and wrong for LifePRO `S` on non-smoker products (we emit `SM` / SMOKER; client wants `ST` / Standard).

This is not a QuikPlUw-only cosmetic change. Every rate factor/key row, the UW master dropdown, and `quikridr.MUWCLASS` must stay on the same code set or rate lookup breaks in QLAdmin.

**Recommended direction:** introduce a **form/plan-aware** UWCLASS map driven by the spreadsheet (with a documented default for forms not listed), rebuild rate keys + member tables + rider MUWCLASS in one release, and expand validator / CSO UW domains for `BL` / `NT` / `PQ`.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source | File | In Source/? | Role |
|--------|------|-------------|------|
| Rate grids | `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv` (+ PAAGE/PDAGE/PAAGERAT families) | Yes (rate package) | `UNDERWRITING_CLASS` letters on factor rows |
| Policy benefits | `PPBEN_PolicyBenefit_Extract_20260630.csv` | Yes | Policy/rider `UNDERWRITING_CLASS` → `MUWCLASS` |
| Reinsurance | `PREIN_ReinsuranceDetail_Extract_20260630.csv` | Yes | `UNDERWRITING_CLASS` / `CONV_UWCLS` (Q/N heavy) |
| Client catalog | `docs/Underwriting Classes by Form.xlsx` | Yes (docs) | Authoritative form → allowed UW codes/labels |

### LifePRO letters observed (Rate_Table)

| Letter | Rows | Current map |
|--------|-----:|-------------|
| `0` | 514,793 | `00` |
| `S` | 314,644 | `SM` |
| `P` | 154,515 | `PR` |
| `B` | 118,887 | `ST` ← **must become `BL`** |
| `N` | 26,145 | `NS` ← **L14 → `NT`; others TBD** |

PPBEN also has `Q` (113), `T` (7), `R` (13). Rider map today: `Q→NS`; `T`/`R` pass through and remain on quikridr (7 + 13 rows).

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Role |
|-------|-------|------|------|
| All rate factor tables (`QuikGps`, `QuikCvs`, `QuikTvs`, `QuikNps`, `QuikNff`, `QuikDbs`, `QuikDvs`, `QuikCoi`, `QuikGcoi`, …) | `UWCLASS` | C(2) | Rate key dimension |
| Rate key tables (`QuikPlGp`, `QuikPlCv`, `QuikPlTv`, `QuikPlDb`, `QuikPlDv`, …) | `UWCLASS` | C(2) | Plan key setup |
| `QuikIssc` | `UWCLASS` | C(2) | Issue-age schedule key |
| `QuikPlUw` | `UWCODE`, `UWDESCR` | C(2), C(20) | Per-plan allowed classes |
| `QuikUwpo` | `UWCODE`, `UWDESCR` | C(2), C(20) | Company UW dropdown (A10) |
| `quikridr` | `MUWCLASS` | C(2) | Policy/rider UW for rate join |
| `quikplan` variation flags | `VARIES_BY_UWCLASS` / counts | derived | Must recompute after remap |

Help / schema refs: `qla_core/rate_dbf_schema.py` (UWCLASS C2; QuikUwpo §7.230; QuikPlUw member layout).

### Current Output footprint (must be remapped)

| Location | Codes today | Approx volume |
|----------|-------------|----------------:|
| Factor `UWCLASS` (Cvs/Gps/Tvs/Nps/Nff/…) | 00, NS, SM, PR, ST | ~200k+ rate rows |
| `QuikPlUw` | 00/NS/PR/SM/ST | 187 rows / 129 plans |
| `QuikUwpo` | 00/NS/PR/SM/ST | 5 rows |
| `quikridr.MUWCLASS` | 00/PR/SM/NS/ST (+T/R) | 6,914 rows |

---

## 4. Required Source-to-Target Field Mapping

### 4a. Proposed letter map (hypothesis — needs client confirm)

| LifePRO | Current QLA | Proposed QLA | When |
|---------|-------------|--------------|------|
| `0` / blank | `00` | `00` | Always |
| `B` | `ST` | **`BL`** | All forms (L10 blended family) |
| `S` | `SM` | **`SM`** | L10 smoker/blend family only (sheet: Standard Smoker) |
| `S` | `SM` | **`ST`** | Preferred/Standard forms (L01/L05/L07/667/658/659/… and ST-only forms) |
| `P` | `PR` | `PR` | All (labels may differ by form; QuikUwpo needs one fleet label) |
| `N` | `NS` | **`NT`** | L14 (Standard Non-Tobacco) |
| `N` | `NS` | `NS` or retire | Non-L14 (ISWL etc.) — **open** |
| `Q` | `NS` | **`PQ`** | L14 Preferred Non-Tobacco |
| `T` / `R` | pass-through | unchanged or map | Reinsurance — **open** |

### 4b. Plan membership (from spreadsheet)

Client form → codes (abridged; full list in Intake / spreadsheet):

| Form | Target UWCODEs |
|------|----------------|
| L10 LP95 / L10 OLD | PR, SM, BL |
| L10 SR OLD / L10 LP95SR | BL |
| L14 | NT, ST, PQ, PR |
| L01 / L05 / L07 / 667 / 658* / 659* | ST, PR |
| All other listed forms | ST only |

Implementation needs form → QL `PLAN` resolution (existing coverage_id / crosswalk), then `QuikPlUw` emit exactly those codes (plus `00` where annuity/default keys require it).

### Fields that must remain unchanged

| Target | Touch this issue? |
|--------|-------------------|
| `quikmstr.MMODPREM` / #26 `MPREM` | **No** |
| MPOLICY padding #25 | **No** |
| Rate factor numeric values (except UW key remap) | **No** (same source VALUE) |
| Gender / Band / State keys | **No** |
| Unrelated rulebooks | **No** |

---

## 5. Open Client Questions

1. **Confirm LifePRO letter → client code by form family** (especially `S→SM` vs `S→ST`, `B→BL`, `N→NT`, `Q→PQ`). Please validate or correct the §4a matrix.
2. **L14:** Rate_Table only has letter `N` today, but the sheet lists NT/ST/PQ/PR. Where do ST/PQ/PR rate rows come from (other extract, inherit, or membership-only with rates only on NT)?
3. **QuikUwpo labels:** One label per code fleet-wide. Approve labels, e.g. `BL=BLENDED`, `NT=STD NON-TOBACCO`, `PQ=PREF NON-TOBACCO`, `PR=PREFERRED`, `SM=STD SMOKER`, `ST=STANDARD` (even if L10 sheet says "Preferred Non-Smoker" for PR).
4. **Forms not on the sheet** (ISWL 1658/1659, riders, SAL annuities using `00`): keep current codes, force `ST`, or add rows to the spreadsheet?
5. **Retire `NS`?** If L14 moves to `NT` and other `N` usages are remapped, should `NS` disappear from QuikUwpo?
6. **UAT example policies** per L10 / L14 / Preferred-Standard form for screen proof.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| UWCODE / UWCLASS / MUWCLASS width | Keep C(2) |
| Unknown LifePRO letter | Do not invent; exception report + hold `00` only where blank default already applies |
| Plan not on sheet | Freeze current mapping until OQ-4 answered (no silent remap) |
| QuikUwpo | Distinct codes from QuikPlUw + always `00` (A10) |
| Policy/rate join | `quikridr.MUWCLASS` must equal rate-table `UWCLASS` for that plan’s class |

---

## 7. Policy key handling

- MPOLICY: unchanged (#25).
- Crosswalk: unchanged for policy numbers; plan-form linkage uses existing PLAN / COVERAGE_ID resolution.
- MUWCLASS: continue through `map_rider_uwclass()` but with new map (and plan context if form-aware).

---

## 8. Estimated record counts (before-state)

| Artifact | Rows | Would remapped keys touch? |
|----------|-----:|----------------------------|
| Rate factor UWCLASS ≠ remap-stable | large majority of non-`00` rows | **Yes** |
| `QuikPlUw` | 187 | **Yes** (codes + descr) |
| `QuikUwpo` | 5 → ~7+ | **Yes** (add BL/NT/PQ; maybe drop NS) |
| `quikridr` MUWCLASS in {NS,ST} and L10 ST(from B) | thousands | **Yes** |
| `quikridr` MUWCLASS already PR/SM/00 | many | Labels only / maybe unchanged codes |

Exact after-counts require the confirmed §4a matrix (Risk stage simulation).

---

## 9. Sample traces (current → hypothesized)

| Plan | LifePRO letter | Current QLA | Hypothesized QLA |
|------|----------------|-------------|------------------|
| `1L1095` (L10 LP95) | B / P / S | ST / PR / SM | **BL** / PR / SM |
| `5L0110` (L01) | S / P | SM / PR | **ST** / PR |
| `1L14SC` (L14) | N (rates); Q on policies | NS | **NT**; Q→**PQ** |
| `1L15GD` (L15) | S | SM | **ST** (sheet: ST only) |
| `1659C2` (ISWL) | N/P/S | NS/PR/SM | **blocked — not on sheet** |

---

## 10. Risks and unknowns

| Risk | Notes |
|------|-------|
| Form-aware map complexity | Global dict insufficient; need plan/form discriminator |
| L14 incomplete rate source | Membership without rates → QLAdmin lookup failures |
| CSO `_UWCLASS_KEY` only knows `00/NS/SM` | PR/ST/BL/NT/PQ MORT column resolution may fall back to default |
| Reinsurance T/R | 20 quikridr rows outside new catalog |
| Validator hard domain | `rate_validation.UWCLASS_DOMAIN` will BLOCKER on new codes until updated |
| Full rate re-batch required | Partial Test_Validation insufficient for Closure (G7) |

---

## 11. Touch-point inventory (everywhere UW classes are used)

### A. Canonical maps / labels (must change)

| Location | What |
|----------|------|
| `qla_core/rate_dbf_schema.py` | `UWCLASS_MAP`, `RIDER_UWCLASS_MAP`, `QLA_RIDER_UWCLASS_PASS`, `UWCLASS_LABEL`, `map_uwclass()`, `map_rider_uwclass()` |
| `QLA_Migration/app.py` (+ root `app.py`) | Calls `map_rider_uwclass` for `MUWCLASS`; version bump |
| `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv` | `UNDERWRITING_CLASS → MUWCLASS` default `00` note |

### B. Rate pipeline (re-emit keys)

| Location | What |
|----------|------|
| `qla_core/rate_factor_loader.py` | `map_uwclass` on every factor row |
| `qla_core/rate_key_setup.py` | Key rows `UWCLASS` |
| `qla_core/rate_member_setup.py` | `QuikPlUw` + `QuikUwpo` build |
| `qla_core/rate_emit.py` | Emits QuikUwpo / member / factor CSVs |
| `qla_core/rate_pipeline.py` | `KEY_FIELDS` includes UWCLASS |
| `qla_core/rate_inheritance_loader.py` | Inherited grids |
| `qla_core/shared_rate_candidate_loader.py` | Candidate UW map |
| `qla_core/cv_inheritance_loader.py` | CV UW map |
| `qla_core/paagerat_ul_coi_loader.py` / `paagerat_pr_loader.py` | COI/PR UW map |
| `qla_core/pdage_missfill.py` | Rejects unmapped UW letters |
| `qla_core/quikissc_loader.py` | Default UWCLASS `S`→SM today |
| `qla_core/quikplan_rate_variation_flags.py` | `VARIES_BY_UWCLASS` / distinct counts |

### C. Policy / reinsurance

| Location | What |
|----------|------|
| `qla_core/reinsurance_converter.py` | `MUWCLASS` from rider/parent UNDERWRITING_CLASS |
| `qla_core/reinsurance_lookups.py` | Pass-through MUWCLASS |
| `tools/validators/validate_issue59_muwclass.py` | Expected MUWCLASS literals |

### D. Downstream consumers / validation

| Location | What |
|----------|------|
| `qla_core/rate_validation.py` | `UWCLASS_DOMAIN = {00,NS,SM,PR,ST}` |
| `qla_core/cso_mortality_crosswalk.py` | `_UWCLASS_KEY` ns/sm only |
| `Issue_Log_Items/Issue_A/Issue_A_Conversion_Checklist.md` | A10 expects 00/NS/PR/SM/ST |
| Issue A verifiers / emit helpers under `Issue_Log_Items/Issue_A/scripts/` | QuikUwpo checks |
| Data governance rules (DG-PLANVALUES-005 etc.) | Valid UW class lists in governance packs |
| Load packages under `docs/Valuation/load_package_*` | Snapshot rates (regenerate, do not hand-edit) |

### E. Output artifacts rewritten on next full rate + policy batch

| Path | Field |
|------|-------|
| `QLA_Migration/Output/rates/Quik*.csv` (all keyed tables) | `UWCLASS` |
| `QLA_Migration/Output/rates/QuikPlUw.csv` | `UWCODE` / `UWDESCR` |
| `QLA_Migration/Output/rates/QuikUwpo.csv` | master codes |
| `QLA_Migration/Output/quikridr.csv` | `MUWCLASS` |
| `QLA_Migration/Output/quikplan.csv` | variation flags if emitted from rate stats |

### F. Explicitly not a change surface (unless new evidence)

| Path | Why |
|------|-----|
| Premium / mode / status rulebooks | No UW dimension |
| Claims (`quikclmp`/`quikclms`) | No UWCLASS key in conversion |
| Dividend / loan history tables | No UWCLASS |

---

## 12. Recommended Risk Agent prompt

```
Proceed to Risk Agent for Issue #118 after Dependency Gate PASS.

Simulate form-aware UWCLASS remap against current Output/rates and quikridr.
Quantify rows changing ST→BL (L10 B), SM→ST (non-L10 S), NS→NT / Q→PQ (L14).
Confirm rate↔MUWCLASS join integrity and CSO fallback behavior.
Go/No-Go for Development.
```

---

## 13. Recommended Development task (do not implement yet)

1. Add client spreadsheet-driven plan UW membership table under `QLA_Migration/Configs/` or `qla_core/` (surgical).
2. Replace global `UWCLASS_MAP` with form/plan-aware mapper; keep `00` default.
3. Update labels + `QuikUwpo` domain; expand `UWCLASS_DOMAIN` / CSO `_UWCLASS_KEY` as approved.
4. Re-run rate package + quikridr emit; publish validators for #118.
5. Bump `APP_VERSION` in root + `QLA_Migration/app.py`.
6. Update Issue A A10 expected code set after PASS.

**Do not start until Dependency Gate PASS and explicit “Approved for Development.”**
