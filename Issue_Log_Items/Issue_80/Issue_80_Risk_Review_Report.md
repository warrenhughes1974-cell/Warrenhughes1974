# Issue #80 — Risk Review Report

**Issue:** #80 — CSO Valuation Setup → exact QuikPlCv / QuikPlTv (plan + rate keys)  
**Framework stage:** Risk Agent  
**Status:** Conditional Go — Ready for Development (pending explicit user approval)  
**Fallback simulated:** N/A (authority overwrite; blank = does not apply)  
**Generated:** 2026-07-17  
**Model:** Cursor Grok 4.5 (locked)  
**Simulation:** `QLA_Migration/_risk_review_issue80_valuation_setup.py`  
**Evidence:** `evidence/issue80_risk_impact_summary.csv`, `issue80_risk_anchor_plans.csv`, `issue80_risk_sample_diffs.csv`

**Status note:** Risk analysis only — no production code changes.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Load Valuation_Setup for the **51 non-PUA** in-scope plans using the locked Help code map; exclude all PUA plans (#81/#82); apply plan-level MORT/ETIMORT to every key row for that PLAN (including gender/UW segments); update quikplan NFOINT/INTMETHCV for the same 51 plans; do not invent QuikPlCv/Tv key rows for the three L17 plans that currently have none.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| QuikPlCv.MORT | CSO crosswalk / gender variants (A1/A4/B1/P1…) | Valuation_Setup plan code (e.g. A1, O1, N1) | **Yes** |
| QuikPlCv.ETIMORT | Crosswalk / gender variants | Valuation_Setup (C1/Q1/N1 or blank) | **Yes** |
| QuikPlCv.NFOINT | Old crosswalk letters (often C/F/G) or blank | Help §6.10 code from workbook rate | **Yes** |
| QuikPlCv.INTMETHCV | Mostly `0` | `0` (Curtate) | Rare |
| QuikPlTv.RSVINT / RSVMETH / INTMETHTV / STOREMEANS / CALCMIDS | Almost all blank | Coded from workbook + Help | **Yes** (fill) |
| QuikPlTv.MORT | Same as CV pattern | Same as QuikPlCv.MORT | **Yes** |
| quikplan.NFOINT / INTMETHCV | Partial old crosswalk | Same as QuikPlCv for in-scope plans | **Yes** |
| PUA plans | — | **Out of scope** (#81/#82) | **No** |
| Citizens folder | — | Untouched | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| quikridr.MPREM / MMODPREM (#26) | **No** |
| MPOLICY padding (#25) | **No** |
| QuikCvs / QuikTvs / QuikNps factor grids | **No** |
| quikplan fields other than NFOINT / INTMETHCV | **No** |
| PUA QuikPl* keys | **No** (#82) |
| Citizens_Product_Rate_Conversion | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `docs/Valuation_Setup.xlsx` | CSO authority |
| `qla_core/cso_mortality_crosswalk.py` | Current CV assume path (supersede on conflict) |
| `qla_core/rate_key_setup.CSOAssumptionProvider` | QuikPlCv only today; QuikPlTv reserve fields blank |
| `qla_core/rate_dbf_schema.py` | Field lengths |
| `QLA_Migration/Output/rates/QuikPlCv.csv` / `QuikPlTv.csv` | Before-state |
| `QLA_Migration/Output/quikplan.csv` | Before-state |
| `evidence/cso_valuation_setup_coded_expected.csv` | After-state authority |

---

## 4. Population Analysis

**Universe:** 51 in-scope QLA plans (`scope_issue80=IN_SCOPE`).

| Table | Key/plan rows | Rows that would change | Cells that would change | Plans with keys | Plans missing keys |
|-------|-------------:|-----------------------:|------------------------:|----------------:|-------------------:|
| QuikPlCv | 96 | 89 | 173 | 48 | 3 |
| QuikPlTv | 127 | 127 | 709 | 48 | 3 |
| quikplan | 51 | 36 | 36 | 51 | 0 |

### QuikPlCv cell mix

| Type | Cells |
|------|------:|
| Blank → value | 45 |
| Value → value (overwrite) | 127 |
| Value → blank | 1 |

### QuikPlTv cell mix

| Type | Cells |
|------|------:|
| Blank → value | 651 |
| Value → value | 58 |
| Value → blank | 0 |

### QuikPlTv by field (all 127 rows get reserve fills)

RSVINT 127 · RSVMETH 127 · INTMETHTV 127 · STOREMEANS 127 · CALCMIDS 127 · MORT 74

### NFOINT overwrite pattern (QuikPlCv cells)

| Before → After | Cells | Meaning |
|----------------|------:|---------|
| C → A | 30 | 5.00% → 4.50% (Valuation_Setup) |
| blank → 2 | 12 | fill 2.50% |
| F → A | 8 | 5.75% → 4.50% (CSI family) |
| blank → 6 | 7 | fill 3.50% (incl. 1960PO) |
| G → E | 2 | 6.00% → 5.50% (1668SP) |
| 2 → blank | 1 | workbook blank = does not apply |

### Plans missing QuikPlCv / QuikPlTv keys today

`10L171`, `10L172`, `117JPO` — present on quikplan; **no** QuikCvs/QuikTvs factor rows for these three.  
**Conditional rule:** update quikplan NFOINT/INTMETHCV only; do **not** create new QuikPlCv/Tv key rows in #80.

---

## 5. Fallback Recommendation

| Option | Assessment |
|--------|------------|
| A. Apply Valuation_Setup plan-level codes to all key rows for in-scope PLANs | **Recommended** |
| B. Preserve gender-specific MORT/ETIMORT from old crosswalk when present | **Reject** — conflicts with single-code Valuation_Setup authority |
| C. Only fill blanks; never overwrite existing NFOINT/MORT | **Reject** — leaves wrong CSI/L10/L17 rates in place |
| D. Include PUA plans now | **Reject** — parked on #81/#82 |

**Recommended fallback:** none beyond scope limits in the Conditional Go.

---

## 6. Trace Plans (anchors)

| PLAN | Material before → after | Pass intent? |
|------|-------------------------|--------------|
| **1960PO** | QuikPlCv NFOINT blank→`6`; QuikPlTv RSVINT/RSVMETH blank→`6`/`3`; MORT P1→O1 | Yes — unblocks #60 Track B |
| **1658C1** | NFOINT already `A`; QuikPlTv reserve five fields blank→ filled | Yes |
| **17CSI3** | NFOINT `F`→`A`; MORT B1→A1 | Yes — Valuation_Setup rate win |
| **1L1095** | NFOINT `C`→`A` | Yes |
| **221END** | ETIMORT→`N1`; NFOINT stays/`2` as coded | Yes |
| **1668SP** | NFOINT `G`→`E` | Yes |

Full cell-level anchors: `evidence/issue80_risk_anchor_plans.csv`.

---

## 7. Top Material Overwrites

Not a numeric premium field — largest business impact is **interest letter changes**:

| PLAN family | NFOINT before | After | Rate meaning |
|-------------|---------------|-------|--------------|
| L10 / L14 / related | C | A | 5.00% → 4.50% |
| CSI (17CSI*) | F | A | 5.75% → 4.50% |
| 1668SP | G | E | 6.00% → 5.50% |
| 1960PO / peers | blank | 6 | → 3.50% |

**MORT collapse:** Female/SM variants (B4, A4, P1, B1, …) on key rows overwrite to the workbook’s single plan MORT (A1/O1). This is intentional under SD-80-6 / plan-level authority, but it is the main actuarial regression surface for UAT.

---

## 8. Material Calculation Impact

| Impact | Intentional? |
|--------|--------------|
| Non-zero NFOINT / RSVINT on base plans (esp. 1960PO) | **Yes** — enables CV/PUA calc path Chris required |
| QuikPlTv reserve method/interest finally populated | **Yes** — #77 OBQ-5 |
| CSI/L10 interest letters change vs old crosswalk | **Yes** — Valuation_Setup wins |
| Gender-specific MORT codes → plan default | **Yes** under workbook (single MORT column) — confirm in UAT |
| Factor grid values unchanged | **Yes** — assumptions only |

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserved** — not in touch list |
| Issue #26 MPREM / MMODPREM | **Preserved** — not in touch list |
| Issue #60 Track A PUA phase | **Preserved** — #80 does not edit quikridr |
| Issue #60 Track B interest | **Advanced** by 1960PO (and peers) assumption fill |
| Issue #77 key/PVO structure | **Preserved** — do not delete keys; only fill assumption columns |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] For every `scope_issue80=IN_SCOPE` plan with QuikPlCv rows: MORT/ETIMORT/NFOINT/INTMETHCV match `cso_valuation_setup_coded_expected.csv`
- [ ] Same plans’ QuikPlTv: MORT + RSVINT/RSVMETH/INTMETHTV/STOREMEANS/CALCMIDS match expected
- [ ] Same plans’ quikplan NFOINT/INTMETHCV match expected
- [ ] Blank expected → blank actual (no invention)
- [ ] No PUA plan codes from #81/#82 lists changed
- [ ] No QuikCvs/QuikTvs/QuikNps/QuikGps factor cell drift for non-assumption columns
- [ ] Plans outside the 51-plan set: QuikPlCv/Tv assumption cells unchanged
- [ ] Anchors: `1960PO`, `1658C1`, `17CSI3`, `1L1095`, `221END`, `1668SP`
- [ ] Still no QuikPlCv/Tv keys invented for `10L171`, `10L172`, `117JPO` unless separately approved
- [ ] Citizens folder untouched
- [ ] #25 / #26 spot checks unchanged

---

## 11. Recommended Development Agent Task

**Requires:** explicit user “Approved for Development” + Composer 2.5.

1. Treat `docs/Valuation_Setup.xlsx` + `evidence/cso_valuation_setup_coded_expected.csv` (IN_SCOPE only) as emit authority.  
2. Extend assumption provider (or sibling loader) so QuikPlTv reserve fields populate; keep QuikPlCv fields in sync; Valuation_Setup wins over `CSO_Mortiality_Crosswalk.csv` for in-scope plans.  
3. Apply plan-level MORT/ETIMORT/NFOINT/INTMETHCV to **all** key rows for that PLAN (every GENDER/UWCLASS/BAND…).  
4. Apply quikplan NFOINT/INTMETHCV for the same 51 plans.  
5. Skip PUA plans (#81/#82). Skip creating new QuikPlCv/Tv rows for `10L171`/`10L172`/`117JPO`.  
6. Add validator comparing Output to coded expected for IN_SCOPE.  
7. Version-bump `app.py` and `QLA_Migration/app.py` (currently **v57.99** → next).  
8. On validator PASS, publish modified `quikplan.csv` + `rates/QuikPlCv.csv` + `rates/QuikPlTv.csv` to `Output/Test_Validation/`.  
9. **Do NOT** change Citizens folder, factor grids, quikridr, or unrelated quikplan columns.

---

## Appendix

| Artifact | Path |
|----------|------|
| Impact summary | `evidence/issue80_risk_impact_summary.csv` |
| Anchor before/after | `evidence/issue80_risk_anchor_plans.csv` |
| Sample diffs | `evidence/issue80_risk_sample_diffs.csv` |
| Coded expected | `evidence/cso_valuation_setup_coded_expected.csv` |
| Simulation script | `QLA_Migration/_risk_review_issue80_valuation_setup.py` |
| Scope decisions | `Issue_80_Scope_Decisions.md` |

---

## Gate Criteria (G3)

- [x] Risk report published with Conditional Go  
- [x] Impact quantified from Output vs coded expected  
- [x] Unrelated fields marked untouched  
- [x] #25 / #26 preservation confirmed  
- [ ] User acknowledgment / “Approved for Development” (required before Dev)
