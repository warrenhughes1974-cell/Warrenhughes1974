# Issue #118 — Regression Report

**Issue:** #118 — Active UW classes by form remap  
**Framework stage:** Regression Agent  
**Engine version:** v58.84 (v58.83 + L10 family correction)  
**Baseline:** `QLA_Migration/Archive/issue118_pre_remap/quikridr_pre_issue118.csv` (pre-remap Output snapshot)  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-08-09  
**Verdict:** **PASS**

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|-----------|-----------------|
| `quikridr.MUWCLASS` | Form-aware remap per Eric spreadsheet; no orphan codes |
| Rate tables (`QuikGps`, `QuikCvs`, …) | UWCLASS key remap; L14 T/Q/R premiums appended to `QuikGps` |
| `QuikPlUw` / `QuikUwpo` | Membership + labels; drop `NS`; trim stale dropdown rows |
| All other `quikridr` fields | **No change** |
| All other policy tables | **No change** (this fix was surgical to UW class paths only) |

---

## 2. Issue Validators

| Validator | Result | Notes |
|-----------|--------|-------|
| `validate_issue118_uwclass.py` | **PASS** | 6,934 rows; domain `{00,BL,NT,PQ,PR,SM,ST}`; QuikUwpo has no `NS`; UAT anchors OK; L10 family covers all 15 crosswalk plans |
| `validate_issue59_muwclass.py` | **PASS** | Updated samples (901…C; L14 Q→PQ); no 55/41/56 on MUWCLASS |

---

## 3. quikridr Before / After (non-candidate proof)

| Check | Before | After | OK? |
|-------|-------:|------:|-----|
| Row count | 6,934 | 6,934 | Yes |
| Key set (MPOLICY + MPHASE) | 6,934 | 6,934 identical | Yes |
| Field order | 40 columns | 40 columns identical | Yes |
| Rows with MUWCLASS change | — | 2,597 | Expected |
| Rows with MUWCLASS unchanged | — | 4,337 | Expected |
| Non-MUWCLASS field changes | — | **0** | **Yes** |

Evidence: `evidence/issue118_regression_muwclass_diff.csv` (2,597 changed rows)

### L10 family correction (v58.84)

Implementation review found `L10_PLANS` covered only 11 of the 15 `L10*` coverages in the Policy Form
Crosswalk. QLAdmin plan codes do not carry the family name consistently (`L10 SPSWP` → `910SWP`,
`L10 WP CDT` → `9CDTWP`), so four were missed when the set was enumerated by hand.

This mattered because the two halves of the conversion detect L10 differently: rate loaders pass
`coverage_id` (prefix match succeeds → `S` = `SM`), while `app.py` passes only `plan` (set lookup
failed → `S` = `ST`). On a full batch `9JPO10` rate rows would have been keyed `SM` while its policies
carried `ST`, producing exactly the orphan condition this issue exists to prevent. The surgical apply
masked it by keying both sides off the plan set.

| Plan | Coverage | Policies moved ST → SM |
|------|----------|-----------------------:|
| `9JPO10` | L10 JPO | 92 |
| `9GPO10` | L10 GPO | 3 |
| `910SWP` | L10 SPSWP | 0 (no S letters) |
| `9CDTWP` | L10 WP CDT | 0 (no S letters) |

All 15 L10 plans now return the same class from both code paths (verified). A guard was added to
`validate_issue118_uwclass.py` that fails when `L10_PLANS` does not cover every `L10*` crosswalk plan.

### MUWCLASS transition counts (old → new)

| Transition | Rows | Rule |
|------------|-----:|------|
| SM → ST | 1,516 | LifePRO S on non-L10 forms → Standard |
| ST → BL | 840 | LifePRO B → Blended (was wrongly ST) |
| NS → PQ | 111 | L14 LifePRO Q |
| NS → NT | 101 | L14 LifePRO N |
| NS → 00 | 9 | Residual N/Q off L14 → Standard code 00 |
| R → PR | 13 | L14 LifePRO R |
| T → ST | 7 | L14 LifePRO T |

**Unexplained transitions:** 0 (every changed row matches `map_rider_uwclass` against PPBEN letter + plan)

### L14 (`1L14SC`) distribution after

| MUWCLASS | Rows |
|----------|-----:|
| PQ | 111 |
| NT | 101 |
| PR | 13 |
| ST | 7 |

---

## 4. Source Spot-Checks (PPBEN → Output)

| Policy | Plan | Letter | Old | New | Expected | OK |
|--------|------|--------|-----|-----|----------|----|
| 9011107879C | 1L10SO | B | ST | BL | BL | Yes |
| 9010787560C | 1659CR | S | SM | ST | ST | Yes |
| 9011261602C | 1L14SC | Q | NS | PQ | PQ | Yes |
| 9011253007C | 1L14SC | N | NS | NT | NT | Yes |
| 9011185537C | 5L0110 | S | SM | ST | ST | Yes |
| 9011227609C | 982JPO | S | SM | ST | ST | Yes |
| 9011194191C | 9JPO10 | S | SM | ST | ST | Yes |
| 9010785099C | 980JPO | S | SM | ST | ST | Yes |

---

## 5. Plan Membership Integrity (QuikPlUw cleanup)

After moving rollback copies to `Archive/issue118_pre_remap/` and rebuilding membership from live rate keys + policy MUWCLASS only:

| Check | Count | OK? |
|-------|------:|-----|
| A — dropdown entry with no rates and no policies | **0** | Yes |
| B — policy MUWCLASS missing from plan dropdown | **0** | Yes |
| C — rate row UWCLASS missing from plan dropdown | **0** | Yes |
| D — plan has policies but empty dropdown | **0** | Yes |

| Metric | Before cleanup | After cleanup |
|--------|---------------:|--------------:|
| QuikPlUw rows | 300 | **239** |
| Plans | 147 | 147 |
| Stale entries removed | — | 61 (all SM/ST with zero policies and zero rate rows) |

Published to `Output/Test_Validation/rates/`: `QuikPlUw.csv`, `QuikUwpo.csv`

---

## 6. Prior Closed-Issue Regression

| Issue | Check | Result | Related to #118? |
|-------|-------|--------|------------------|
| #59 | `validate_issue59_muwclass.py` | **PASS** | Yes — MUWCLASS path updated intentionally |
| #59 | MSTATUS allowlist (release gate) | FAIL (23 unexpected MSTATUS changes) | **No** — pre-existing; not caused by MUWCLASS remap |
| #106 | QuikTvs duration | FAIL | **No** — pre-existing rate duration gap |
| L14 | QuikCvs duration | FAIL | **No** — pre-existing; separate from UW class remap |
| Release gate overall | `validate_release_closed_issues.py` | RELEASE_BLOCKED | **No** — blocked by pre-existing Closed-issue GAPs, not #118 |

**Closed-row conflict check:** No Closed row in `Completed_Issues_Release_Validation_Guide.md` conflicts with the #118 UW remap. Issue #59 MUWCLASS validator was updated and passes with the new domain.

---

## 7. Output Folder & Rollback

| Check | Result |
|-------|--------|
| `*_pre_issue118*` under `Output/` | **None** (moved to Archive) |
| Rollback archive | 18 files in `QLA_Migration/Archive/issue118_pre_remap/` |
| Pre-remap baseline has NS on quikridr | 221 rows (confirms rollback is pre-change) |
| Current quikridr NS | 0 |
| APP_VERSION root `app.py` | v58.84 |
| APP_VERSION `QLA_Migration/app.py` | v58.84 |

---

## 8. Residual Items (not regression failures)

These are documented gaps or follow-ups for Closure / client reporting — not blockers to #118 regression PASS:

1. **L14 cash value gap** — ST/PQ/PR have premiums only; LifePRO CV/reserve grids exist for NT only. Approved; note on client report.
2. **`5L01MA`** — Eric's spreadsheet lists Preferred + Standard; LifePRO supplies Standard only (1 policy). On Exceptions tab of plan report.
3. **Eight plans** — dropdown still lists classes with LifePRO rate tables but zero policies (`1668SP` PR, `1679CS` 00/PR, `1L10SO`/`1L10SR` PR/SM). Eric decision if those rate grids should stay or be dropped.
4. **Closure still pending** — Completed Issues guide row for #118 not yet written; accountability catalog does not include #118 until Closed.
5. **Output provenance** — Current Output was surgically remapped via `apply_issue118_output_remap.py`; a full production batch on the release machine remains the handoff standard before client UAT reload. Rate-content equivalence was proven for this cut: PDAGE contains only `0/S/P/N/B`, PAAGERAT `T/Q/R` occur only on L14 (appended), and `M` occurs only on coverage `8034 J15MT`, which has no plan in the crosswalk.
6. **`QuikIssc` default class** — `quikissc_loader.DEFAULT_UWCLASS = "S"` resolves to `ST` (was `SM` pre-#118) because no plan/coverage is supplied. All 8 rows sit on `1658*`/`1659*`/`166*`/`1679CS` plans, whose client sheet target is `ST`, so the new value is the better fit. The `or "SM"` fallback on that line is now unreachable.

---

## 9. Verdict

**PASS** for Issue #118 regression.

- Intended policies remapped correctly (2,597 MUWCLASS changes, 0 unexplained).
- Non-candidate rows unchanged except MUWCLASS (4,337 unchanged; 0 other field diffs).
- L10 family gap found in implementation review, fixed, and guarded against recurrence.
- No orphan MUWCLASS; membership join integrity clean after QuikPlUw cleanup.
- Issue #118 and #59 MUWCLASS validators pass.
- Rollback path intact; Output folder policy restored.

**Ready for Closure discussion** (G7 gate + Completed Issues guide row + resolution handoff).

---

## Evidence

| File | Purpose |
|------|---------|
| `evidence/issue118_regression_muwclass_diff.csv` | Every changed quikridr row |
| `evidence/issue118_regression_summary.json` | Machine-readable counts |
| `evidence/Issue_118_Plan_Underwriting_Classes.xlsx` | Client-facing plan × class report |
| `QLA_Migration/Archive/issue118_pre_remap/` | Pre-remap rollback copies |
