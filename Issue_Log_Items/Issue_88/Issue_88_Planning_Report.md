# Issue #88 — Planning Report

**Issue:** #88 — Blank ANN_PREM_PER_UNIT fallback → Prem/Unit × units valuation blow-up  
**Framework stage:** Planning Agent  
**Status:** Planning Complete  
**Generated:** 2026-07-21  
**Agent:** Cursor Grok 4.5 (Planning)

---

## 1. Executive Finding

Issue #26 correctly maps LifePRO `ANN_PREM_PER_UNIT` → `quikridr.MPREM` (QLAdmin Prem/Unit). When that source is blank/zero, `app.py` falls back to phase `MODE_PREMIUM`, which is a **total** modal premium. QLAdmin treats `MPREM` as **per unit** and valuation multiplies by units — e.g. `010779727C`: 2,930.75 × 500 ≈ 1,465,400 in QuikValf/QLR while Policy Mode Prem stays 2,930.75.

**Direction:** Keep #26 primary mapping. Change blank fallback to **modal/annual total ÷ units** (with mode/zero-unit rules below). Do **not** change `quikmstr.MMODEPREM`. Go for Risk after Dependency Gate PASS.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Notes |
|--------------|--------------|---------------------|-------|
| PPBEN (benefit/coverage) | `PPBEN*` / policy master benefit extract used by quikridr | Yes (batch Source) | `ANN_PREM_PER_UNIT`, `MODE_PREMIUM`, units, BENEFIT_SEQ |
| PPOLC | Policy master | Yes | Policy-level `MODE_PREMIUM` → `quikmstr.MMODEPREM` only |

### Available source fields

| Field | Role | Notes |
|-------|------|-------|
| `ANN_PREM_PER_UNIT` | Preferred MPREM source | Blank/zero on this ISWL example and ~2.4k+ base rows historically (#26) |
| `MODE_PREMIUM` (PPBEN) | Phase modal premium total | Wrong as Prem/Unit; OK as numerator for ÷ units |
| Units (`NUMBER_OF_UNITS` / mapped MUNIT source) | Divisor | Must be > 0 for divide fallback |
| Mode | Annualization check | This conversion uses Mode **12** = annual on the example |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Semantics | Source |
|-------|-------|-----------|--------|
| `quikridr` | `MPREM` | **Annual premium per unit** (Coverage Prem/Unit) | QLAdmin Help / Issue #26 Field Definition |
| `quikmstr` | `MMODEPREM` | Policy modal premium | Unchanged |
| `quikridr` | `MUNIT`, `MVPU` | Units / value per unit | Unchanged |

**Repo references**

| Location | Role |
|----------|------|
| `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv` | `ANN_PREM_PER_UNIT` → `MPREM` |
| `QLA_Migration/app.py` (~7483–7490) | Issue #26 blank → `MODE_PREMIUM` interceptor |
| `Issue_Log_Items/Issue_26/` | Prior research + blank inventory |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PPBEN | `ANN_PREM_PER_UNIT` | `quikridr.MPREM` | Use when non-zero (existing #26) | **No** (preserve) |
| PPBEN | `MODE_PREMIUM` + units | `quikridr.MPREM` | If ANN blank/zero **and** units > 0: emit `MODE_PREMIUM / units` (see §6 for mode) | **Yes** |
| PPBEN | `MODE_PREMIUM` | `quikridr.MPREM` | Remove raw total fallback | **Yes** |
| PPOLC | `MODE_PREMIUM` | `quikmstr.MMODEPREM` | Existing | **No** |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| `quikmstr.MMODEPREM` | PPOLC.MODE_PREMIUM | **No** |
| MPOLICY padding | `#25` | **No** |
| `MUNIT` / `MVPU` / fees (#58) | Existing | **No** |
| Populated ANN → MPREM | `#26` primary | **No** |

---

## 5. Open Client Questions

1. For **non-annual** modes, should blank fallback annualize before ÷ units (e.g. monthly × 12), or is phase `MODE_PREMIUM` already on a basis QLA expects as “annual PPU” after ÷ units?  
   - *Working assumption for Risk:* Mode **12** = annual in this book (proven on `010779727C`); Risk must quantify non-12 blank-ANN population before Dev.
2. Confirm UAT acceptance: Coverage Prem/Unit ≈ LifePRO ANN_PPU when present; when blank, Prem/Unit ≈ ModePrem/Units; Policy Mode Prem unchanged; valuation Mode Prem no longer ≈ ModePrem×Units.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Primary | If `ANN_PREM_PER_UNIT` ≠ 0 → `MPREM` = that value (#26) |
| Blank fallback | If units > 0 → `MPREM` = `MODE_PREMIUM / units` (round consistent with existing money emit) |
| Units ≤ 0 | Do **not** divide; leave blank/zero or retain safe non-multiplying behavior (Risk to choose; avoid inventing rate) |
| Mode | Document annual (12) first; Risk flags other modes |
| Policy key | Crosswalk + #25 padding |
| Money | Preserve existing quikridr decimal emit (#55) |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

1. LifePRO → Master_Crosswalk → QLA  
2. `format_qladmin_mpolicy()` (#25)  
3. No orphan-policy change

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| Historical blank ANN base rows (#26) | ~2,469–2,994 | Issue #26 reports |
| ISWL Compare prem×units suspects | ~512 | `docs/Valuation/analysis/iswl_premium_times_units_iswl_only.csv` |
| All unit-scale suspects | ~544 | Same analysis |
| Anchor policy | 1 | `010779727C` |

Exact post-fix delta count = Risk/Dev simulation on current Source.

---

## 10. Sample Trace

| Policy (QLA) | Before MPREM | Units | After (proposed) | Mode Prem (unchanged) |
|--------------|-------------:|------:|-----------------:|----------------------:|
| `010779727C` ph1 | 2,930.75 | 500 | ~5.8615 | 2,930.75 |
| `010779727C` ph4 `9DIS90` | -169.50 | 1 | -169.50 (ANN or mode; units=1) | n/a phase |
| Typical 1-unit blank ANN | = MODE_PREMIUM | 1 | unchanged numerically | unchanged |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Non-annual mode: MODE÷units ≠ annual PPU | Medium | Risk population by mode; annualize if needed |
| Zero / tiny units | Medium | Align with #55 floor; no divide-by-zero |
| Rider phases with blank ANN and odd MODE_PREMIUM | Medium | Per-benefit-row logic only; validate discount/ADB |
| Changes MPREM for many blank-ANN rows vs #26 UAT baseline | High | Diff-only validation; 1-unit rows should be no-ops |
| Plan VarGP=4 / max units 99 | Low for this fix | Out of scope; Issue A |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | Yes |
| Field definitions confirmed (#26 + Help) | Yes |
| Client scope clear (user: fix load fallback; no commit; validate) | Yes |
| Example policies available | Yes |

---

## 13. Recommended Risk Agent Prompt

```
Proceed to Risk Agent — Issue #88.

Read Issue_88_Intake_Summary.md, Issue_88_Planning_Report.md, Issue_88_Dependency_Gate.md.
Quantify blank-ANN rows by mode and units; simulate MODE_PREMIUM/units vs current MPREM.
Flag non-annual modes and zero-unit rows. No code. Publish Issue_88_Risk_Review_Report.md.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. Surgical edit in `app.py` Issue #26 interceptor: when ANN=0 and units>0, set `val = MODE_PREMIUM / units` (apply agreed annualization if Risk requires).  
2. Update rulebook comment on `Sync_Rulebook_quikridr.csv` MPREM row.  
3. Bump `APP_VERSION` in root `app.py` **and** `QLA_Migration/app.py`.  
4. Add `tools/validators/validate_issue88_mprem_unit_fallback.py` (or `QLA_Migration/_validate_issue88_*.py`).  
5. Re-batch `quikridr` only for user Validation; publish `Output/Test_Validation/quikridr.csv` on PASS.  
6. **Do not commit** until user requests.

---

## Appendix

- Related: Issue #26 (released), valuation analysis under `docs/Valuation/analysis/`
- Anchor: `010779727C` / `9010779727` / plan `1658C1`
