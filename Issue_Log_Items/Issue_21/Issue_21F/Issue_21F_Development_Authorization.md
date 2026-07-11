# Issue 21F — Development Authorization

**Issue:** #21F — Truncated Premium History (conversion premium adjustment)  
**Framework stage:** Development Authorization (post G3)  
**Date:** 2026-07-11  
**Authority:** User **APPROVED** for Development  
**Assigned Development model (locked):** **Composer 2.5**  
**Prior gates:** Intake ✅ · Planning ✅ · Dependency Gate **PASS** · Risk **CONDITIONAL GO**

---

## Authorization

| Item | Value |
|------|--------|
| Development authorized? | **YES** |
| Scope | Phase-1 **non-ISWL** conversion premium adjustment only |
| Engine baseline | v57.63 (bump both `app.py` files on change) |
| Risk binding limits | See `Issue_21F_Risk_Review_Report.md` § Go / No-Go |

---

## Binding scope (do not expand)

1. **Additive only** — never modify/delete existing `quikprmh` payment rows.  
2. **ISWL hard-exclude** — PPBENTYP `TYPE_CODE=BF` / FV book — no adjustment.  
3. **Positive only** — negatives → `Reports/` exception file; do not load.  
4. **Idempotent** — skip if Conversion Adjustment marker already present for `MPOLICY`.  
5. **Date** — `DATEPAID` = **2017-12-31** (engine date format).  
6. **LifePRO total** — `PREMIUMS_PAID + PU_PREMIUMS_PAID + SU_PREMIUMS_PAID + SL_PREMIUMS_PAID`.  
7. **Reports** — `QLA_Migration/Reports/` only (not Output).  
8. **Schema** — no new `quikprmh` columns; marker via `MSOURCE` / `MBATCH` / `USER_ID`.  
9. Preserve **#25** MPOLICY padding and **#26** MPREM.

---

## Required Development tasks (Composer 2.5)

1. Helper in `qla_core/` (extend `issue21_open_item_decisions.py` or new `issue21f_*.py`): totals cache, eligibility, synthetic row, reports.  
2. Thin wire in **both** `app.py` and `QLA_Migration/app.py` after `quikprmh` materialization.  
3. Bump `APP_VERSION` in both app files.  
4. Validator: `tools/validators/validate_issue21f_premium_adjustment.py`  
   - Golden **010310404C** adjustment = **15,193.85** @ 2017-12-31  
   - ISWL / negatives / schema / idempotency / non-candidate history guards  
5. On validator PASS: copy modified `quikprmh.csv` to `Output/Test_Validation/`.  
6. Document exact Conversion Adjustment marker literals in Implementation Notes.

**Do not:** rewrite PACTG conversion wholesale; include ISWL; load negatives; redesign schema.

---

## Canonical references

| Doc | Path |
|-----|------|
| Business decisions | `Issue_21F_Business_Decisions.md` |
| Planning | `Issue_21F_Planning_Report.md` |
| Dependency Gate | `Issue_21F_Dependency_Gate.md` |
| Risk Review | `Issue_21F_Risk_Review_Report.md` |
| Risk simulation | `evidence/issue21f_risk_impact_summary.json` |

---

## Next step for operator

1. **Switch Cursor model to Composer 2.5.**  
2. Prompt: *“Issue 21F is approved for Development. Read `Issue_21F_Development_Authorization.md` and implement surgically.”*  
3. After Dev completes → Validation + Regression on **Cursor Grok 4.5** → Closure on **Composer 2.5**.
