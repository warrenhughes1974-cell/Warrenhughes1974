# Issue 21F — Risk Review Report

**Issue:** #21F — Truncated Premium History (conversion premium adjustment)  
**Framework stage:** Risk Agent (G3)  
**Status:** **CONDITIONAL GO** — Ready for Development (await explicit Development approval on **Composer 2.5**)  
**Generated:** 2026-07-11  
**Agent / model:** Risk · **Cursor Grok 4.5** (locked) — read-only; no production code  
**Prior stages:** Intake ✅ · Planning ✅ · Dependency Gate ✅ (`Issue_21F_Dependency_Gate.md`)  
**Simulation:** `evidence/issue21f_risk_*.csv` / `issue21f_risk_impact_summary.json`  
**Script:** `Issue_Log_Items/Issue_21/Issue_21F/_risk_review_issue21f_premium_adjustment.py`

---

## Go / No-Go Recommendation

**CONDITIONAL GO** for phase-1 non-ISWL conversion adjustment only, with these binding limits:

1. **Additive only** — never modify/delete existing `quikprmh` payment rows.  
2. **ISWL hard-exclude** — `TYPE_CODE=BF` / FV book (2,348 policies) get no adjustment.  
3. **Positive adjustments only** — negatives → exception report, not load (**1** policy in current sim).  
4. **Idempotent** — skip if Conversion Adjustment row already present for `MPOLICY`.  
5. **Reports in `QLA_Migration/Reports/`** — never park audits in Output.  
6. **Schema unchanged** — no new `quikprmh` columns; marker via existing `MSOURCE`/`MBATCH`/`USER_ID`.  
7. Dev must document exact marker literals and prove golden **010310404C → $15,193.85**.

Fleet impact is large (**~2,622** new rows / **~$20.0M** adjustment dollars) but **mechanically bounded** (one row per policy, fixed date, no history rewrite). Acceptable given Eric’s confirmed approach.

---

## 1. Current vs Proposed Mapping

| Concern | Current | Proposed | Change? |
|---------|---------|----------|---------|
| Detail payment history | PACTG → `quikprmh` from ~2017-01-01 | Unchanged | **No** |
| Lifetime premiums paid vs history sum | Gap (truncation) | One Conversion Adjustment row @ **2017-12-31** | **Yes** |
| LifePRO total | Not loaded to `quikprmh` | Base+PUA+SU+SL from PPBENTYP | **Yes** (calc) |
| ISWL | History may exist | **No** adjustment phase 1 | **Guard** |
| Negatives | N/A | Exception report only | **Guard** |
| 21G tax basis / target field | Staged report | Untouched | **No** |

---

## 2. Population / impact (read-only simulation)

Source: PPBENTYP 20260630 + Output `quikprmh.csv` + Master_Crosswalk.

| Metric | Count / amount |
|--------|----------------:|
| PPBENTYP policies | 5,084 |
| ISWL excluded (BF) | **2,348** |
| **Load candidates** (adj > 0) | **2,622** |
| Sum of positive adjustments | **$19,993,849.73** |
| Median adjustment | **$5,969.02** |
| Max adjustment | **$159,295.36** (011196134C) |
| Negative exceptions | **1** (−$97.00) |
| Already matched (NO_GAP) | 10 |
| No premium data | 102 |
| No crosswalk | 1 |
| `quikprmh` rows today | 206,861 |
| Projected rows after | **209,483** (+2,622) |
| ISWL policies that already have hist rows (untouched) | 1,475 |

### Golden trace (must hold in Development)

| Policy | LifePRO total | Current hist | Adjustment | Status |
|--------|-------------:|-------------:|-----------:|--------|
| **010310404C** | $17,040.05 | $1,846.20 | **$15,193.85** | LOAD_CANDIDATE |

Matches Eric’s planning example exactly.

### Candidates without existing history (370)

These get an opening-balance adjustment with `History_Total = 0`. Consistent with A4 in Dependency Gate — flag in validation report as `OPENING_BALANCE` subtype for UAT visibility.

Evidence files:

- `evidence/issue21f_risk_adjustment_simulation.csv`  
- `evidence/issue21f_risk_load_candidates.csv`  
- `evidence/issue21f_risk_negative_exceptions.csv`  
- `evidence/issue21f_risk_impact_summary.json`

---

## 3. Premium / related fields untouched

| Target | Touched? |
|--------|----------|
| Existing `quikprmh` payment rows (non-candidates & candidates’ history) | **No** (additive only) |
| ISWL `quikprmh` rows | **No** adjustment |
| `quikmstr` / `quikridr` / `quikplan` | **No** |
| #25 MPOLICY padding | **No** redesign |
| #26 `MPREM` | **No** |
| 21G staged premium/basis report | **No** (may later align component math; out of this Dev slice) |
| `quikactg` / PACTG source | **No** |

---

## 4. Repo touch surfaces (Development)

| Location | Role |
|----------|------|
| `qla_core/` helper (prefer extend `issue21_open_item_decisions.py` or new `issue21f_*.py`) | Totals cache, eligibility, row build, reports |
| `app.py` + `QLA_Migration/app.py` | Thin wire after `quikprmh` materialization; version bump |
| `Sync_Rulebook_quikprmh.csv` | Prefer **no** change unless defaults needed for synthetic row |
| `tools/validators/validate_issue21f_*.py` | Golden + schema + non-candidate unchanged |

---

## 5. Fallback options

| Option | Assessment |
|--------|------------|
| **A. Full non-ISWL fleet adjustment (Eric-approved)** | **Recommended** — CONDITIONAL GO |
| B. Pilot subset (workbook policies only) | Safer UAT first; delays fleet reconcile — optional if user wants staged ship |
| C. Accept floor only (v57.63 prior) | **Rejected** — superseded by Eric 2026-07-11 |
| D. Full PACTG re-extract to issue | Out of scope; source team; not required |
| E. Include ISWL now | **Rejected** — Eric deferred |

---

## 6. Regression surfaces & checklist

| Risk | Severity | Mitigation |
|------|----------|------------|
| Double adjustment on re-run | High | Idempotent Conversion Adjustment marker |
| ISWL incorrectly adjusted | High | BF/FV exclude + regression count of ISWL hist unchanged |
| Negative loads | Med | Exception path only (sim: 1 policy) |
| Schema / field-order drift | High | Schema assert in validator |
| Non-candidate history bytes change | High | Diff existing rows for non-candidate MPOLICYs |
| Output folder pollution | Med | Reports only under `Reports/` |
| Marker looks like real payment | Med | Fixed date 2017-12-31 + explicit classification |

**Validation Agent checklist (post-Dev):**

- [ ] 010310404C adjustment = 15,193.85 @ 2017-12-31  
- [ ] `quikprmh` row count = prior + loaded candidates (idempotent re-run adds 0)  
- [ ] Field order matches schema manifest  
- [ ] ISWL sample policies: no new Conversion Adjustment row  
- [ ] Negative exception file contains the −$97 policy; not in Output  
- [ ] Non-candidate existing rows byte-identical (or PREMIUM sum unchanged per row)  
- [ ] #25 / #26 untouched  

---

## 7. Recommended Development Agent task (Composer 2.5)

**Exact surgical ask:**

1. After `quikprmh` rows are built from PACTG, compute non-ISWL LifePRO four-component totals from PPBENTYP.  
2. For each eligible policy with `ADJ > 0` and no existing Conversion Adjustment marker, append one synthetic row: `DATEPAID=20171231` (or engine’s date format equivalent), `PREMIUM`/`MLIFE` = ADJ, other money fields 0.00, marker fields set.  
3. Write `Reports/issue21f_premium_adjustment_validation.csv` and `…_exceptions.csv`.  
4. Bump `APP_VERSION` in **both** `app.py` files.  
5. Add `tools/validators/validate_issue21f_premium_adjustment.py` covering golden + guards above.  
6. On validator PASS, copy modified `quikprmh.csv` to `Output/Test_Validation/`.

**Do not:** rewrite PACTG conversion; touch ISWL; load negatives; change unrelated tables.

---

## 8. Gate Criteria (G3)

| Criterion | Result |
|-----------|--------|
| Risk report with Go/No-Go | **CONDITIONAL GO** |
| Impact quantified | **Yes** (2,622 / $19.99M; golden matched) |
| Unrelated fields marked untouched | **Yes** |
| #25 / #26 preservation | **Yes** |
| User acknowledgment | **Pending** — approve Development to proceed on Composer 2.5 |

---

## Status

**Ready for Development** (conditional) after your explicit approval.

**Next model:** switch to **Composer 2.5** for Development Agent only.
