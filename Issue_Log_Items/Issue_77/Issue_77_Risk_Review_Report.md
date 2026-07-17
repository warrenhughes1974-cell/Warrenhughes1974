# Issue #77 — Risk Review Report

**Issue:** #77 — Fleet rate setup: Plan Values Options + default keys vs loaded rates  
**Framework stage:** Risk Agent  
**Status:** Conditional Go — Ready for Development after user approval  
**Generated:** 2026-07-17  
**Model:** Cursor Grok 4.5 (locked)  
**Code changes:** None (Risk only)

**Compare basis:** `QLA_Migration/Output/rates` vs `docs/EX_Rate_Tables` (setup guide)  
**Evidence:** `Issue_Log_Items/Issue_77/evidence/`

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Safe to develop with the locked rules below. Touches rate setup + `quikplan` PVO flags only. Does **not** invent factor values. Does **not** touch policy tables.

User locked (2026-07-17): move forward; **every rate family (GP/DB/CV/TV/DV) that has no factor rates still gets one default key record** for plans that already have other rates loaded.

---

## Locked decisions (from user)

| # | Decision |
|---|----------|
| D1 | Truth = rates we load in `Output/rates` |
| D2 | Guide = `docs/EX_Rate_Tables` for setup shape/defaults |
| D3 | Recompute Plan Values Options from loaded keys (after stubs) |
| D4 | **Default key stub:** if a plan has any factor rates, and a family (GP/DB/CV/TV/DV) has **zero** factor rows, emit **one** default QuikPl* key for that family |
| D5 | QuikPlSt.MLOANINT blank → `0.00` |
| D6 | PLANVALOPT only `Y`/`N` (fix invalid `F`) |
| D7 | Do **not** invent factor grid values; do **not** copy foreign EX plan codes |
| D8 | QuikPlTv assumption fill (RSVINT etc.) stays **out** unless later expanded (#60) |

---

## 1. Current vs Proposed

| Area | Current | Proposed | Change? |
|------|---------|----------|---------|
| QuikPlGp/Db/Cv/Tv/Dv | Keys only where factors exist | + default key when family has no factors | **Yes** |
| Default key tuple | N/A | `GENDER=0`, `UWCLASS=00`, `BAND=00`, `ISSCNTRY=0000`, `ISSUEST=00`, `EFFDATE=19000101`; CV/TV assumption fields blank | **Yes** |
| `quikplan` *VARY* / PLANVALOPT | R7 count>1 (stale/wrong) | Recompute from keys after stubs: GD/UW if ≥2 values; BD if family has key; STVARYGP if GP key exists | **Yes** |
| QuikPlSt.MLOANINT | blank | `0.00` | **Yes** |
| Factor grids (Gps/Dbs/…) | LifePRO values | Unchanged | **No** |
| Orphan key `910RWP` TV | Key w/o matching factor tuple | Drop orphan or align — Dev validates | **Yes** (surgical) |

---

## 2. Premium / unrelated fields untouched

| Target | Touched? |
|--------|----------|
| quikmstr / quikridr / MPREM / MPOLICY (#25/#26) | **No** |
| Factor cell values in QuikGps/Dbs/Cvs/Tvs/Dvs/Nps | **No** |
| BAND=`00` policy/rate rule (#71) | **No** (stubs also use `00`) |
| Sync rulebooks (unless Dev needs a tiny PVO post-step only in rate pipeline) | Prefer rate-pipeline only |

---

## 3. Repo references

| Location | Role |
|----------|------|
| `qla_core/rate_key_setup.py` | Build QuikPl* keys from factor grids |
| `qla_core/rate_member_setup.py` | Members; MLOANINT placeholder |
| `qla_core/quikplan_rate_variation_flags.py` | PLANVALOPT / *VARY* |
| `qla_core/rate_pipeline.py` / `rate_emit.py` | Emit orchestration |
| `docs/EX_Rate_Tables/` | Setup guide |
| `QLA_Migration/Output/rates/` | Loaded rates under test |

---

## 4. Population impact (before → after)

### 4a. Default key stubs to add

Plans with any factor rates: **126**  
Families with no factors and no key today → add 1 default key:

| Family | Plans needing default key |
|--------|--------------------------:|
| GP | 17 |
| DB | **103** |
| CV | 80 |
| TV | 46 |
| DV | **106** |
| **Total stub key rows** | **352** |

Example `1658CS`: GP/CV/TV OK; **add default QuikPlDb + QuikPlDv** (matches screenshot checking DB with no DB factors).

Evidence: `evidence/issue77_default_key_stub_needs.csv`

### 4b. Plan Values Options

| Metric | Count |
|--------|------:|
| Rated plans | 126 |
| Currently M2-imperfect (pre-stub) | 114 |
| Expected after stubs + recompute | Aim **126/126** match locked PVO rule |
| PLANVALOPT invalid / inconsistent today | 11 |

### 4c. QuikPlSt.MLOANINT

| Metric | Count |
|--------|------:|
| Rows blank today | 126 |
| Set to `0.00` | 126 |

### 4d. Factor values

| Metric | Count |
|--------|------:|
| Factor rows changed | **0** |

---

## 5. Fallback options

| Option | Assessment |
|--------|------------|
| A — Stub all missing GP/DB/CV/TV/DV keys (user request) | **Recommended** |
| B — Stub only DB/DV (screenshot families) | Reject — user asked every variable without rates |
| C — PVO-only, no stub keys | Reject — user required default keys |
| D — Copy EX plan rows | Reject — wrong book |

**Recommended:** Option A.

---

## 6. Trace examples (plan-level)

| Plan | Before | After (proposed) |
|------|--------|------------------|
| `1658CS` | No QuikPlDb/Dv; STVARYGP=N; GDVARYDB/BDVARYDB=N | Default DB+DV keys; PVO includes Band/State GP + DB Gender/Band as keys allow |
| `1666WL` | Already M2-ish OK | Add stubs only for families with zero factors; PVO refresh |
| `960ADB` | Has rates, PLANVALOPT≠Y | PLANVALOPT=Y + stubs for missing families |
| `910RWP` | TV key orphan risk | Fix orphan; keep/add stubs per rule |

---

## 7. Material impact

| Intentional | Not in scope |
|-------------|----------------|
| 352 default key headers | New factor numbers |
| ~114+ plans PVO flag fixes | Policy premium/status |
| 126 MLOANINT defaults | QuikPlTv RSVINT fill (#60) |

**UI note:** Default DB/DV keys may enable Death Benefit / Dividend buttons in QLAdmin even with empty factor grids. That is intentional per user (default key when no rates).

---

## 8. Prior fix preservation

| Check | Result |
|-------|--------|
| #25 MPOLICY | Preserved — no policy emit change |
| #26 MPREM | Preserved |
| #71 BAND=`00` | Preserved — stubs use `00` |

---

## 9. Regression surfaces

1. `quikplan` *VARY* / PLANVALOPT columns only (other quikplan fields frozen in validator)  
2. New QuikPlDb/Dv/Gp/Cv/Tv stub rows (352)  
3. QuikPlSt.MLOANINT  
4. Rate factor CSV row counts/values must be **unchanged**  
5. Non-rated quikplan plans (15 without members) — do **not** invent full rate packages unless they already have factors  

---

## 10. Recommended Development task (surgical)

1. In rate key emit (`rate_key_setup` / pipeline): after building keys from factors, for each plan with ≥1 factor family, for each of GP/DB/CV/TV/DV with zero factors → append **one** default key (`0`/`00`/`00`/`0000`/`00`/`19000101`; assumptions blank).  
2. Set QuikPlSt.MLOANINT default `0.00` when blank.  
3. Recompute `quikplan` PLANVALOPT/*VARY* from **final** keys (post-stub) using locked rule; coerce alphabet to Y/N.  
4. Remove/fix `910RWP` orphan key if still present.  
5. Validator:  
   - every rated plan: members present  
   - every rated plan: each of GP/DB/CV/TV/DV has ≥1 key  
   - zero factor value drift  
   - PVO matches keys  
6. Version-bump both `app.py`; publish changed `quikplan` + touched `rates/QuikPl*.csv` (+ QuikPlSt) to `Output/Test_Validation/`.  

**Do not:** invent QuikDbs/Gps/… factor rows; copy EX plan codes; fill QuikPlTv RSVINT from foreign EX plans.

---

## 11. Validation / regression checklist

- [ ] `1658CS`: QuikPlDb + QuikPlDv default keys exist; factor counts unchanged  
- [ ] Stub count ≈ 352 (± document if pipeline differs)  
- [ ] All 126 rated plans: 5 family keys present  
- [ ] PLANVALOPT ∈ {Y,N} only; no `F`  
- [ ] STVARYGP=Y for all plans with GP key  
- [ ] QuikGps/Dbs/Cvs/Tvs/Dvs row counts + checksums unchanged  
- [ ] Spot-check 5 non-candidate plans: unrelated quikplan columns unchanged  
- [ ] #25/#26 smoke unchanged  

---

## Gate G3

- [x] Go/No-Go published (Conditional Go)  
- [x] Impact quantified (352 stubs; 126 MLOANINT; PVO fleet)  
- [x] Unrelated fields marked untouched  
- [x] #25/#26 preserved  
- [ ] User acknowledges → then **Approved for Development** (Composer 2.5)
