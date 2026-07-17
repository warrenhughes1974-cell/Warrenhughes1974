# Issue #77 — Planning Report (fleet-wide)

**Issue:** #77 — Fleet rate-table setup validation (members, keys, factors, Plan Values Options)  
**Framework stage:** Planning Agent  
**Status:** Planning Complete → Dependency Gate  
**Generated:** 2026-07-17 (reframed)  
**Agent:** Planning Agent (Cursor Grok 4.5)  
**Code changes:** None  

**Evidence:** `Issue_Log_Items/Issue_77/evidence/`  
**Audit script:** `QLA_Migration/_research_issue77_fleet_rate_setup_audit.py`

---

## 1. Executive Finding

This is a **fleet setup accuracy** issue. Using `docs/EX_Rate_Tables` as the structural guide and our current `Output/rates` + `quikplan` as before-state:

1. **Factor↔key linkage is nearly perfect** (1 orphan). Member tables cover all 126 rated plans.  
2. **Plan Values Options is not fleet-correct** — under the UI-inferred rule (Band/State participate even when single-valued; Gender/UW when multi-valued), **114 of 126** rated plans have checkbox gaps. Worst gap: **STVARYGP = N on 109 plans** (should be Y whenever GP rates exist).  
3. **Defaults/assumptions lag the EX guide** — QuikPlTv interest/method fields are **100% blank**; QuikPlSt.MLOANINT all blank; QuikAint only 2 plans vs EX 181.  
4. EX cannot be copied plan-by-plan (wrong book). Target = **EX conventions + our LifePRO factor content + consistent PVO flags for every plan we load.**

**Go path:** Risk sizes blast radius after OBQs lock the PVO rule and assumption scope.

---

## 2. Confirmed sources / guide

| Source | Role |
|--------|------|
| `docs/EX_Rate_Tables/*.dbf` | Guide for table presence, member/key shape, default conventions |
| LifePRO Rate_Table / PAAGERAT / PDAGE | Factor **values** authority |
| `Output/quikplan.csv` + `Output/rates/*.csv` | Before-state |
| `1658CS` Plan Values Options screenshot | Checkbox semantics sample (not sole scope) |

### Package inventory (EX guide vs our load)

| Table | EX rows | OUR rows | EX plans | OUR plans | Setup note |
|-------|--------:|---------:|---------:|----------:|------------|
| QuikPlGd | 1,906 | 210 | 1,798 | 126 | Members OK for rated plans |
| QuikPlUw | 1,830 | 186 | 1,798 | 126 | OK |
| QuikPlBd | 2,261 | 126 | 1,762 | 126 | All `00` (#71) — matches Citizens policy band |
| QuikPlSt | 1,798 | 126 | 1,798 | 126 | ISSCNTRY/ISSUEST OK; MLOANINT blank |
| QuikPlNb | 1 | 126 | 0 | 126 | We emit per plan; EX unused — likely OK |
| QuikPlGp | 3,139 | 225 | 1,760 | 109 | |
| QuikPlDb | 4 | 25 | 4 | 23 | EX rarely uses DB keys |
| QuikPlCv | 487 | 94 | 297 | 46 | |
| QuikPlTv | 944 | 220 | 529 | 80 | Assumptions blank vs EX |
| QuikPlDv | 0 | 29 | 0 | 20 | We have DV; EX file absent/empty |
| QuikGps | 62,900* | 11,983 | 1,759 | 109 | *active EX rows |
| QuikDbs | 208 | 2,513 | 3 | 23 | |
| QuikCvs | 232,555* | 38,047 | 279 | 46 | |
| QuikTvs | 456,072 | 53,818 | 530 | 80 | |
| QuikDvs | 145,673* | 6,452 | 276 | 20 | |
| QuikNps | 284,424* | 52,647 | 520 | 76 | No PVO NP flags in schema |
| QuikCoi | 0 | 792 | 0 | 2 | Empty OK in EX |
| QuikNff | 0 | 20,217 | 0 | 23 | We have NFF; EX empty |
| QuikAint | 919 | 2 | 181 | 2 | **Large coverage gap vs EX pattern** |
| QuikUint | 0 | 0 | 0 | 0 | Empty both sides |
| QuikIssc | 0 | 0 | 0 | 0 | Empty both sides |

---

## 3. QLAdmin targets under review

| Layer | Tables | Accuracy goal |
|-------|--------|----------------|
| Plan Values Options | `quikplan` PLANVALOPT + GD/UW/BD/ST × GP/DB/CV/TV/DV | Checkboxes match rate keys for **every** loaded plan |
| Members | QuikPlGd/Uw/Bd/St/Nb | Every rated plan has complete member lists |
| Keys | QuikPlGp/Db/Cv/Tv/Dv | Every factor key has a header; no orphans |
| Factors | QuikGps/Dbs/Cvs/Tvs/Dvs/Nps/Coi/Nff/… | Content from LifePRO; no silent drops |
| Defaults | QuikPlSt.MLOANINT, QuikPlCv/Tv assumptions, QuikAint | Match EX conventions where Citizens authority exists |

---

## 4. What is wrong / missing (fleet)

### 4a. Plan Values Options — primary defect

**Current engine rule (R7):** *VARY* = Y only if distinct dimension count **> 1**.  
**UI/guide rule (M2, from screenshot + EX key shape):**

| Dimension | Flag Y when |
|-----------|-------------|
| Gender (GD) | Family has rates **and** ≥2 genders |
| UW Class (UW) | Family has rates **and** ≥2 UW classes |
| Band (BD) | Family has rates (**even if** only `00`) |
| Country/State (ST) | **GP** family has rates (**even if** only ALL/`0000`) — screenshot pattern |
| PLANVALOPT | Y if any *VARY* is Y |

**Fleet result (M2 vs current emit):**

| Metric | Count |
|--------|------:|
| Rated plans | 126 |
| Rated plans with any M2 checkbox gap | **114** |
| Rated plans M2-perfect | **12** |
| STVARYGP under-set (need Y) | **109** |
| BDVARYTV under-set | 30 |
| BDVARYGP under-set | 20 |
| BDVARYDB under-set | 13 |
| False Y (over-set) | rare (GDVARYCV/TV a few) |

Evidence: `evidence/issue77_pvo_flag_audit.csv`

### 4b. PLANVALOPT ↔ rates consistency (11 plans)

| Status | Plans |
|--------|-------|
| Has factor rates but PLANVALOPT ≠ Y | `960ADB`, `9896WP`, `90POWP`, `976659`, `996ADB`, `7647SP`, `9ADB10`, `9GPO10` (several show `F` — invalid flag char) |
| PLANVALOPT=Y but no factor rates | `170PUA`, `185PUA`, `1POPUA` |

Evidence: `evidence/issue77_planvalopt_rate_consistency.csv`

### 4c. Key / factor integrity

| Finding | Detail |
|---------|--------|
| Member gaps for rated plans | **0** |
| Key without factor | **1** — `910RWP` QuikPlTv key (F/NS/00) |
| Factor without key | **0** in audit sample |

Evidence: `evidence/issue77_key_factor_orphans.csv`, `issue77_member_coverage_gaps.csv`

### 4d. Defaults vs EX guide

| Field | EX guide | Our emit | Gap |
|-------|----------|----------|-----|
| QuikPlSt.ISSCNTRY/ISSUEST | `0000`/`00` | `0000`/`00` | OK |
| QuikPlSt CNTRYTXT/STATETXT | ALL (OTHER) / N/A | ALL (OTHER) | OK |
| QuikPlSt.MLOANINT | `0.00` on 830 plans; blank on 968 | **all blank** | Default missing |
| QuikPlBd | Multi-band + BDLOWVAL breakpoints | All `00` / 0.0 | Intentional (#71) |
| QuikPlCv NFOINT/MORT/… | ~3% blank | 12–32% blank | Partial |
| QuikPlTv RSVINT/RSVMETH/INTMETHTV | **0% blank** | **100% blank** | Major |
| QuikPlTv STOREMEANS/CALCMIDS | mostly filled | **100% blank** | Major |
| QuikAint | 181 plans | 2 plans | Coverage gap vs EX pattern |

Evidence: `evidence/issue77_assumption_blank_rates.csv`, `issue77_default_value_distributions.csv`

### 4e. Already correct (do not “fix”)

- Member coverage for all 126 rated plans  
- Band=`00` / policy MBAND alignment (#71)  
- ISSCNTRY=`0000` (#73)  
- Near-perfect key↔factor join  
- Empty QuikUint / QuikIssc (matches EX emptiness)  
- DV/NFF/COI presence where LifePRO supplies them (EX may be empty — not a defect by itself)

---

## 5. Proposed source-to-target rules (blueprint)

| ID | Rule |
|----|------|
| PVO-FLEET-1 | Recompute all *VARY* from **emitted** keys/factors using locked M2 (or client-chosen) semantics — not stale R7 count>1 alone |
| PVO-FLEET-2 | PLANVALOPT = Y iff any *VARY* = Y; never `F` or other non Y/N |
| PVO-FLEET-3 | Plans with factor rates must have PLANVALOPT=Y after recompute; PUA-only flag-without-rates plans need explicit decision |
| MEM-1 | Keep member derivation from rate keys; ensure 100% rated-plan coverage (already met) |
| KEY-1 | Remove or complete orphan keys (e.g. `910RWP` TV) |
| DEF-1 | QuikPlSt.MLOANINT default `0.00` when blank (EX convention) |
| DEF-2 | QuikPlTv/Cv assumptions: **only** with CSO/LifePRO authority (#60 Track B unless OBQ expands) |
| AINT-1 | QuikAint expansion is separate decision — EX shows interest stubs are normal; do not invent rates |

### Must not change

| Item | Touch? |
|------|--------|
| #25 MPOLICY padding | **No** |
| #26 MPREM mapping | **No** |
| #71 BAND=`00` | **No** unless client reverses |
| Validated factor cell values (#37/#40/#41/#42) | **No** (flags/defaults only unless orphan fix) |
| Unrelated quikplan columns | **No** |

---

## 6. Open client questions (fleet)

1. **OBQ-1 — PVO rule:** Lock M2 (Band Y if family present; STVARYGP Y if GP present; GD/UW if count>1) as fleet standard? Or another rule?  
2. **OBQ-2 — Invalid PLANVALOPT:** Treat `F` as defect → force Y/N from rates?  
3. **OBQ-3 — PUA plans** (`170PUA`, `185PUA`, `1POPUA`): Keep PLANVALOPT=Y with no factors, or set N?  
4. **OBQ-4 — MLOANINT:** Default all blank QuikPlSt to `0.00`?  
5. **OBQ-5 — QuikPlTv assumptions:** In #77 or remain #60 Track B / CSO?  
6. **OBQ-6 — QuikAint:** Expand beyond 2 stub plans toward EX-style coverage, or leave to #51-style casework only?  
7. **OBQ-7 — UAT bar:** “100% accuracy” = (a) PVO+members+key join only, or (b) also every QuikPlTv/Cv assumption field non-blank like EX?

---

## 7. Formatting / fallback

| Rule | Recommendation |
|------|----------------|
| Flag alphabet | Only `Y` / `N` |
| ISSCNTRY/ISSUEST | `0000` / `00` |
| BAND | `00` (#71) |
| MLOANINT blank | → `0.00` if OBQ-4 accepted |
| Missing assumptions | Blank until CSO — do not copy EX foreign plan codes |

---

## 8. Estimated impact

| Object | Likely touch |
|--------|----------------|
| `quikplan` PVO columns | Up to **114+** plans |
| `QuikPlSt.MLOANINT` | Up to 126 rows |
| Orphan key cleanup | 1 known (`910RWP`) |
| QuikPlTv assumptions | 220 rows **if** OBQ-5 includes |
| QuikAint | 2 → many **if** OBQ-6 expands |
| Policy CSVs | **0** under recommended scope |

---

## 9. Sample traces

| Plan | Role |
|------|------|
| `1658CS` | Screenshot: missing GDVARYDB, BDVARYDB, STVARYGP |
| `1666WL` | M2-perfect control (one of 12) |
| `960ADB` / `9896WP` | Rates present, PLANVALOPT not Y (`N`/`F`) |
| `170PUA` | PVO=Y, no factor rates |
| `910RWP` | TV key without factor |
| EX `11720L` | Structural guide: members + GP/CV/TV keys + populated TV assumptions |

---

## 10. Risks

| Risk | Level | Mitigation |
|------|-------|------------|
| Broad PVO churn | Medium | Validator: only *VARY*/PLANVALOPT; freeze other quikplan cols |
| Wrong PVO rule | High | Lock OBQ-1 before Dev |
| Inventing TV/Aint from EX | High | Keep CSO authority; foreign plans out |
| Touching factor values | High | Out of scope unless orphan repair |

---

## 11. Recommended Risk prompt

```
Proceed to Risk Agent for Issue #77 (fleet-wide).

Read Issue_77_Planning_Report.md and evidence/*.csv.
Model: Cursor Grok 4.5. Do not code.

Size impact of: PVO M2 recompute fleet-wide; PLANVALOPT Y/N cleanup;
MLOANINT 0.00 default; orphan 910RWP; optional QuikPlTv / QuikAint if OBQs include.
Preserve #25/#26/#71. No factor-value rewrites.
```

---

## 12. Recommended Development task (do not implement)

1. Lock OBQs.  
2. Recompute fleet PVO from emitted rates (M2 or approved rule); coerce PLANVALOPT to Y/N.  
3. Default QuikPlSt.MLOANINT → `0.00` if approved.  
4. Fix `910RWP` orphan key.  
5. Add fleet validator: member coverage, key↔factor, PVO matrix, PLANVALOPT alphabet, MLOANINT.  
6. Version-bump both `app.py`; publish changed `quikplan` (+ rates CSVs touched) to `Output/Test_Validation/`.  
7. QuikPlTv / QuikAint only if OBQ-5/6 expand scope.

---

## Gate G1

- [x] Fleet sources/targets confirmed  
- [x] Gap inventory with evidence  
- [x] Open questions listed  
- [x] Unrelated fields protected  
- [x] No code/rulebook changes  
