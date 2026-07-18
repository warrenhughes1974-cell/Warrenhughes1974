# Issue #83 — Planning Report

**Issue:** #83 — Fleet gender companion rate keys (Values=N when no factors)  
**Framework stage:** Planning Agent  
**Status:** Planning complete → Dependency Gate  
**Generated:** 2026-07-17  
**Agent/script:** Cursor Grok 4.5 · `QLA_Migration/_research_issue83_gender_companion_keys.py`

---

## 1. Executive Finding

Issue #77 ensures each rated plan has **at least one** GP/DB/CV/TV/DV key, but when factor extracts only supply one sex (usually `M` or `F`), the other gender key is never built — even though QuikPlGd already lists both members. Anchor `221END` Cash Values shows Sex=`M` Values=`Y` and no Female key; Plan Information already has Gender F+M.

**Direction:** After default key stubs (#77), add a fleet **gender companion** step: for each family that already has an F or M key on a plan that declares both F and M members, emit the missing gender key with the same non-gender segmentation and assumptions, **without** inventing factor rows (QLAdmin Values=`N`). Wire via `rate_pipeline` / `app.py` rate emit. Safe to advance Dependency Gate / Risk.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|--------------|--------------|---------------------|----------:|
| Rate factor extracts (PDAGE / PAAGERAT / etc.) | Existing R5 rate package | Yes (via rate loader) | (unchanged) |
| Derived gender members | Union of factor genders → QuikPlGd | Emit path | — |

Companion keys are **not** new LifePRO cells — they are **QLAdmin key headers** for member variances that already exist when only one sex has factors.

### Available source fields

| Field | Column / source | Notes |
|-------|-----------------|-------|
| PLAN / GENDER on factors | Rate grid keys | Drives which gender currently gets a key |
| QuikPlGd GDCODE | Member emit | Declares F/M variances that must be keyed |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Role |
|-------|-------|------|
| QuikPlGp / Db / Cv / Tv / Dv | PLAN, GENDER, UWCLASS, BAND, ISSCNTRY, ISSUEST, EFFDATE | Rate-key identity |
| QuikPlCv | MORT, ETIMORT, NFOINT, INTMETHCV | Assumptions (#80 authority) |
| QuikPlTv | MORT, RSVINT, RSVMETH, INTMETHTV, STOREMEANS, CALCMIDS | Assumptions (#80) |
| QuikGps / Dbs / Cvs / Tvs / Dvs | Factor grids | **Do not invent** → Values=`N` |
| quikplan | GDVARY* / PLANVALOPT | Recompute after companions (#77 rule) |

**UI:** Plan Rate File Options Keys **Values** column = Y when factor rows exist for that key, else N. Not a stored CSV column in our emit.

**Repo references:**

| Location | Role |
|----------|------|
| `qla_core/rate_key_setup.py` | `build_key_rows`, `ensure_default_key_stubs` (#77) |
| `qla_core/rate_pipeline.py` | Calls stub ensure + members |
| `qla_core/rate_member_setup.py` | QuikPlGd F/M members |
| `qla_core/quikplan_rate_variation_flags.py` | PVO from keys |
| `app.py` / `QLA_Migration/app.py` | GENERATE RATE TABLES entry |

---

## 4. Required Source-to-Target Field Mapping

| Source / rule | Target | Transformation | Change? |
|---------------|--------|----------------|---------|
| Plan has QuikPlGd ∈ {F,M} both; family has key for one | Missing QuikPl* key row | Clone sibling key seg + assumptions; set GENDER to missing | **Yes** |
| Factor grid for missing gender | Quik*vs | Leave absent | **No invent** |
| #80 Valuation_Setup | Assumption cols on new keys | Same plan-level codes as sibling | **Yes** (fill via existing provider) |
| #77 PVO | GDVARY* / PLANVALOPT | Recompute after companions | **Yes** (derived) |

### Fields that must remain unchanged

| Target | Touch this issue? |
|--------|-------------------|
| Factor cell values / row counts (except none added) | **No invent** — counts stay same |
| quikmstr / quikridr / quikprmh | **No** |
| MPOLICY padding (#25) | **No** |
| MPREM mapping (#26) | **No** |
| BAND=`00` (#71) | **Preserve** on companions |
| #80 assumption codes on existing keys | **No overwrite drift** — only fill new companion rows |

---

## 5. Open Client Questions

1. **UW companions:** 37 plans have ≥2 real UW members. Should this issue also emit missing UWCLASS companion keys within a family, or **gender-only** for #83?  
   **Recommendation default:** gender F/M only (matches screenshots); park UW as follow-up unless user expands.
2. **Gender `0` / Joint `J`:** Companions only for F↔M when both are members? (Recommend: yes — only F/M pairing; leave `0`/`J` alone.)
3. **PVO GDVARYCV:** Adding F to QuikPlCv when only M existed will flip Gender-CV checkbox to Y under #77 multi-value rules. Confirm that is desired (Plan Information currently shows CV unchecked for Gender on `221END` because only one CV gender key exists).

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Companion identity | Same UW/Band/Cntry/State/EFFDATE as preferred existing F/M key on that family (or first sorted sibling) |
| Assumptions | `assumptions.get(plan, key_table, fld, gender=new, uwclass=…)` — plan-level #80 codes |
| Factors | Never fabricate |
| Values UI | Expect `N` when `FACTOR_ROWS_FOR_MISSING=N` (fleet audit: 259/259) |
| Members | Already have F/M; `ensure_members_for_keys` remains idempotent |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

N/A — plan/rate keys only. Preserve #25/#26 if any batch path touched.

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| Companion keys to add | **259** | Current Output rates audit |
| Unique plans | **83** | Same |
| QuikPlCv companions | **53** | Includes `221END` F, `222END` F |
| QuikPlTv companions | **13** | Smaller residual |
| QuikPlGp / Db / Dv | 39 / 81 / 73 | Same audit |
| Factor rows with missing gender | **0** | All gaps Values=`N` safe |
| Unexpected invent risk | **0** | No orphaned factors for missing gender |

Detail: `evidence/issue83_gender_companion_key_gaps.csv`

---

## 10. Sample Trace

| Plan | Family | Today | After #83 | Values |
|------|--------|-------|-----------|--------|
| `221END` | QuikPlCv | M only | M + **F** | M=`Y`, F=`N` |
| `221END` | QuikPlTv | F + M | unchanged | both as today |
| `221END` | QuikPlGp | F only | F + **M** | F as today, M=`N` |
| `222END` | QuikPlCv | M only | M + **F** | F=`N` |
| `1960PO` | (if F+M members + gap) | per CSV | companion added | `N` if no factors |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| GDVARY* flips to Y when second gender key appears | Medium (UI) | Document as intentional; confirm OBQ-3 |
| Duplicate key signatures | Low | Dedupe on KEY_FIELDS before append |
| Assumption blank on new F key | Low | Reuse AssumptionProvider / #80 composite |
| EX sample incomplete F/M coverage | Info | User requirement supersedes EX incomplete pattern |
| Preferred stub gender picks only one sex (#77) | Medium | Companion step **after** stubs fixes within-family gaps |

---

## 12. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue #83.

Scope: fleet gender companion keys (F/M) on QuikPlGp/Db/Cv/Tv/Dv when
QuikPlGd has both members and a family already has one gender key.
Values=N (no factor invent). Anchor 221END QuikPlCv F.

Confirm: gender-only vs UW expansion; PVO GDVARY flip acceptable;
exact Development touch list (rate_key_setup + rate_pipeline + APP_VERSION).
Do not code.
```

---

## 13. Recommended Development Task (do not implement)

1. Add `ensure_gender_companion_keys(key_rows, member_rows, assumptions=…)` in `qla_core/rate_key_setup.py`.
2. Call it from `rate_pipeline.py` **after** `ensure_default_key_stubs` and **before/with** `ensure_members_for_keys` + PVO recompute.
3. Logic: for each plan with QuikPlGd containing both F and M; for each FAMILY_KEY_TABLE with ≥1 F/M key for that plan; for each missing F/M member → append cloned key (Values=N path).
4. Bump `APP_VERSION` in root `app.py` and `QLA_Migration/app.py`; changelog note Issue #83.
5. Validator: 221END QuikPlCv has F+M; 0 new factor rows for companions; non-candidate plans without F+M members unchanged; #80 assumption cells on new keys match sibling/plan authority.
6. Publish modified rate key CSVs (+ quikplan if PVO changes) to `Output/Test_Validation/` on PASS.

---

## Gate Criteria (G1 — Planning Complete)

- [x] LifePRO/QLA targets identified
- [x] Mapping + do-not-touch listed
- [x] Counts + sample traces
- [x] Open questions listed
- [x] No production code changed
