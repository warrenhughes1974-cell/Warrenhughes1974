# Issue #56 — Risk Review Report

**Issue:** #56 — PUA CV is incorrect  
**Framework stage:** Risk Agent  
**Status:** **Conditional Go (revised 2026-07-14)** — Option **A** under client plan-key decision `1960PA`  
**Fallback simulated:** Option B withdrawn; Option A selected with multi-product caveat; Option C rejected  
**Generated:** 2026-07-13 · **Revised:** 2026-07-14  
**Agent/script:** Risk Agent (Cursor Grok 4.5) · read-only fleet join `evidence/issue56_*.csv`  
**Scope decisions:** `Issue_56_Scope_Decisions.md` (SD-1: use `1960PA`; SD-2: PAAGERAT `960 PO PUA` CV)

**Status note:** Risk analysis only — no production code changes unless later approved.

---

## Go / No-Go Recommendation

**CONDITIONAL GO (Option A — revised)** — **Keep** rider `MPLAN=1960PA` (client SD-1). Emit **QuikCvs/QuikPlCv for `1960PA`** from LifePRO attained-age **`960 PO PUA` / CV** (PAAGERAT; screenshot confirmed). Do **not** remap to catalog `1POPUA` (Option B **withdrawn**). Reject Option C (base CV alias).

**Hard caveat:** `1960PA` today also holds `960 OL/65/LP PUA` riders (49 rows) with **different** CV tables. Loading PO rates onto `1960PA` fixes Eric’s family (**22** rows) but can mis-rate the other three unless SD-3 chooses a split later. Default scope for this issue: **A1 — PO family first**.

Still blocked for Development until: (1) LifePRO correct PUA CV $ on `010310404C`, (2) SD-3 A1 vs A2 confirmed if needed, (3) user **Approved for Development** on Composer 2.5.

---

## 1. Current vs Proposed Mapping

| Field / object | Current | Proposed (Option B) | Change? |
|----------------|---------|---------------------|---------|
| `quikridr.MPLAN` for PUA | Synthetic `*PA` (e.g. `1960PA`, `1708PA`) | Catalog crosswalk plan (`1POPUA`, `170PUA`, …) | **Yes — 493 rows** |
| `_apply_pua_rider_inheritance` MPLAN rewrite | `base[:4]+"PA"` | **Remove MPLAN overwrite** (may still inherit `MEXPRY`/`MPAYUP` if required) | **Yes — surgical** |
| `QuikCvs` / `QuikPlCv` for catalog PUA plans | Missing for most (`1POPUA`=0, `170PUA`=0, …) | Emit from PAAGERAT attained-age CV | **Yes — rate emit** |
| Base `1960PO` / peer base QuikCvs | Present; client says CV OK | Unchanged | **No** |
| `quikridr.MUNIT` / `MVPU` / `MPREM` | Existing | Unchanged | **No** |
| Traditional `MCV0/1/2` | Blank | Remain blank | **No** |

### Why Option A fails (quantified)

Synthetic **`1960PA` is not one product** — it currently holds riders from **four** LifePRO PUA coverages with **separate** PAAGERAT CV tables:

| Current MPLAN | LifePRO PLAN | Catalog | Ridr rows | PAAGERAT CV rows |
|---------------|--------------|---------|----------:|-----------------:|
| `1960PA` | `960 OL PUA` | `1OLPUA` | 32 | 100 |
| `1960PA` | `960 PO PUA` | `1POPUA` | **22** | **200** |
| `1960PA` | `960 65 PUA` | `165PUA` | 16 | 66 |
| `1960PA` | `960 LP PUA` | `185PUA` | 1 | 175 |

Emitting a single QuikCvs under `1960PA` would attach the **wrong** CV table to at least 3 of 4 populations. **Option A = No-Go.**

### Why Option C fails

Pointing `*PA` at base plan CV (duration / issue-age) contradicts client finding (PUA attained-age rates) and would keep the multi-product collision under `1960PA`. **Option C = No-Go.**

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| `quikmstr.MMODPREM` | MODE_PREMIUM | **No** |
| `quikridr.MPREM` | #26 ANN_PREM_PER_UNIT | **No** |
| MPOLICY / MEMOKEY padding | #25 | **No** |
| Base plan QuikCvs (`1960PO`, etc.) | Rate pipeline | **No** |
| UL `MCV0` / FV_BALANCE2 | #21E UL | **No** |
| PUA non-CV (NP/RV/DV) inheritance | Deferred actuarial | **No** |
| #21F premium history on `010310404C` | quikprmh | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `QLA_Migration/app.py` `PAID_UP_ADDITION_PRODUCTS` | Identifies PUA products for rewrite |
| `QLA_Migration/app.py` `_apply_pua_rider_inheritance` | **`new_mplan = base_mplan[:4] + "PA"`** — primary defect for plan identity |
| `Configs/Sync_Rulebook_quikridr.csv` `PLAN_CODE→MPLAN` | Crosswalk path before rewrite |
| `Mapping/Master_Crosswalk.csv` | `960 PO PUA`→`1POPUA`, `670 PUA`→`170PUA`, … |
| `Output/quikplan.csv` | Catalog PUA plans present; synthetic `*PA` absent |
| `Output/rates/QuikCvs.csv` / `QuikPlCv.csv` | CV grids — PUA catalog mostly empty |
| `Source/PAAGERAT_…_20260630.csv` | Authority for PUA CV (PRIMARY_ONLY per #48) |
| Issue #40 QuikCvs for `261PUA`/`265PUA`/`280PUA` | Already present — do not regress |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| PUA-like `quikridr` rows analyzed | **495** |
| Rows Option B changes `MPLAN` | **493** |
| Rows already on catalog-style key (`261PUA`, `1970PA`) | 2 |
| Distinct policies with synthetic `*PA` | **492** |
| Unique synthetic `*PA` plan codes | **7** |
| Catalog plans needing **new** QuikCvs (0 today, PAAGERAT CV > 0) | **7** plan keys / **490** ridr rows |

### Breakdown — Option B MPLAN rewrite impact

| MPLAN before | LifePRO plan | MPLAN after (B) | Ridr rows | Catalog QuikCvs today |
|--------------|--------------|-----------------|----------:|----------------------:|
| `1708PA` | `670 PUA` | `170PUA` | 415 | 0 |
| `1705PA` | `670 PUA` | `170PUA` | 2 | 0 |
| `1960PA` | `960 OL PUA` | `1OLPUA` | 32 | 0 |
| `1960PA` | `960 PO PUA` | `1POPUA` | **22** | **0** |
| `1960PA` | `960 65 PUA` | `165PUA` | 16 | 0 |
| `1960PA` | `960 LP PUA` | `185PUA` | 1 | 0 |
| `280EPA` | `980 PUA` | `280PUA` | 3 | **496** (keep) |
| `221EPA` | `621 PUA` | `121PUA` | 1 | 0 |
| `2665PA` | `665 PUA` | `265PUA` | 1 | **383** (keep) |
| `261PUA` | `961 PUA` | `261PUA` | 1 | **486** (keep) |
| `1970PA` | `970 PUA` | `1970PA` | 1 | 0 |

### Rate emit workload (Option B)

| Catalog plan | Ridr rows needing CV | PAAGERAT CV source rows | QuikCvs today |
|--------------|---------------------:|------------------------:|--------------:|
| `170PUA` | 417 | 175 (`670 PUA`) | 0 |
| `1OLPUA` | 32 | 100 | 0 |
| `1POPUA` | 22 | 200 | 0 |
| `165PUA` | 16 | 66 | 0 |
| `121PUA` | 1 | 71 | 0 |
| `185PUA` | 1 | 175 | 0 |
| `1970PA` | 1 | 86 (`970 PUA`) | 0 |
| `280PUA` / `265PUA` / `261PUA` | 5 | already have QuikCvs | keep |

Evidence: `Issue_Log_Items/Issue_56/evidence/issue56_pua_fleet_impact.csv`, `issue56_option_ab_summary.csv`

---

## 5. Fallback Recommendation

| Option | Rows / plans impacted | Assessment |
|--------|----------------------:|------------|
| **B — Catalog MPLAN + PAAGERAT QuikCvs** | 493 MPLAN + ~7 new QuikCvs plans | **Recommended** |
| **A — QuikCvs under synthetic `*PA`** | 7 synth plans; `1960PA` multi-product collision | **Reject** |
| **C — Alias `*PA` → base CV** | Smaller emit; wrong rate semantics | **Reject** |
| **B-narrow — `960 PO PUA` / `1POPUA` only** | 22 ridr + 1 QuikCvs plan | Acceptable **interim** if client forces phased UAT; still remove rewrite for those rows only |

**Recommended fallback:** Full Option B. If New Era cannot accept catalog keys immediately, **do not** implement A; escalate product-setup decision instead.

**Phased interim (only if approved):** Fix rewrite + rates for `1POPUA` class first (Eric’s sample), then fleet remaining catalog PUA plans in same release if possible.

---

## 6. Trace Policies

| Policy | Before | Proposed (B) | Pass criteria |
|--------|--------|--------------|---------------|
| `010310404C` | PUA `MPLAN=1960PA`; no QuikCvs; client CV **$6,628.32** (> face **$5,942.78**) | `MPLAN=1POPUA`; QuikCvs from `960 PO PUA` CV; CV ≤ face and ≈ LifePRO | Pending OBQ-1 dollar |
| `010331768C` | `1960PA` / `960 PO PUA` | `1POPUA` + same QuikCvs | Peer |
| `010350577C` | `1960PA` / `960 PO PUA` | `1POPUA` | Peer |
| Base phase `010310404C` | `1960PO` CV OK | **Unchanged** | Control — must not drift |

Simulated LifePRO-scale check (not client-confirmed): PAAGERAT M CV @ age ~83 × 5.94278 ≈ **$4,928** (&lt; face). Exact acceptance wait on Eric.

---

## 7. Top Changes (by population)

| Rank | Change class | Magnitude |
|-----:|--------------|----------:|
| 1 | `1708PA`→`170PUA` | **415** ridr |
| 2 | `1960PA`→`1OLPUA` | 32 |
| 3 | `1960PA`→`1POPUA` | 22 (includes client sample) |
| 4 | `1960PA`→`165PUA` | 16 |
| 5 | New QuikCvs plans with 0→N rows | 7 plans |

*(Numeric CV deltas unknown until rates emitted and QLAdmin compute re-run; face/units unchanged.)*

---

## 8. Material Calculation Impact

| Impact | Intentional? |
|--------|--------------|
| PUA `MPLAN` realignment to catalog | **Yes** — restores rate-key identity |
| New PUA QuikCvs from attained-age PAAGERAT | **Yes** — addresses missing/wrong CV |
| Base traditional CV | **Must be zero drift** |
| PUA face (`MUNIT×MVPU`) | **No change** |
| Collapse of four PUA products under `1960PA` | **Removed** under B |

**Residual risk:** Attained-age → QuikCvs grid placement (AGE/CNTL/duration semantics) can reintroduce #37/#41-class errors. Development must document mapping rules and validate against LifePRO CV dollars, not only “table exists.”

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserve** — out of scope |
| Issue #26 MPREM / MMODPREM | **Preserve** — out of scope |
| Issue #40 PUA QuikCvs (`261/265/280PUA`) | **Preserve** — do not regenerate/overwrite incorrectly |
| Issue #21E UL MCV0 | **Preserve** |
| Issue #21F history on sample policy | **Preserve** |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] Trace `010310404C`: PUA `MPLAN=1POPUA`; QuikPlCv/QuikCvs present; face still $5,942.78  
- [ ] PUA computed CV ≤ face; matches LifePRO within agreed tolerance (OBQ-1)  
- [ ] Base phase `1960PO` QuikCvs bytes / sample base CV unchanged  
- [ ] Fleet: no remaining synthetic `1960PA`/`1708PA`/… on PUA riders (or documented exceptions)  
- [ ] `261PUA`/`265PUA`/`280PUA` QuikCvs row counts stable vs pre-change  
- [ ] `MUNIT`/`MVPU`/`MPREM`/`MPOLICY` unchanged on sample set  
- [ ] Row counts: `quikridr` total stable; only `MPLAN` (and rate tables) change  
- [ ] Peers: at least one `170PUA` (`670 PUA`) and one `1OLPUA` policy  
- [ ] Publish modified tables to `Output/Test_Validation/` on PASS  

---

## 11. Recommended Development Agent Task

**Model:** Composer 2.5 — only after user says Issue #56 is approved for Development **and** OBQ-1 answered (or waiver).

1. **Keep** `_apply_pua_rider_inheritance` MPLAN rewrite to `1960PA` (SD-1) — do **not** switch ridr to `1POPUA`.  
2. **Ensure** `1960PA` exists in product/rate setup as needed (`quikplan` / QuikPlCv pointer).  
3. **Rate emit:** PAAGERAT `960 PO PUA` + `TYPE_CODE=CV` → **QuikCvs under plan `1960PA`** (attained-age placement rules documented).  
4. **Do NOT change:** base `1960PO` QuikCvs, #25/#26, UL MCV0, `MUNIT`/`MVPU`, catalog `1POPUA` ridr remap.  
5. Version bump **both** root and `QLA_Migration/app.py` if engine/rate path touched.  
6. Validator: `QLA_Migration/_validate_issue56_pua_cv.py` — `010310404C` still `MPLAN=1960PA`; QuikCvs present; CV≤face smoke; LifePRO $ when known.  
7. Document residual risk: non-PO rows still on `1960PA` if scope A1.  
8. UAT: rate CSVs (+ quikplan if added) → `Output/Test_Validation/`.

---

## 12. Client gates before Development (carry forward)

| ID | Question | Blocks | Status |
|----|----------|--------|--------|
| OBQ-1 | LifePRO correct PUA CV $ for `010310404C` | Validation acceptance | **Open** |
| OBQ-2 | Catalog vs `1960PA` | Plan key | **Answered — use `1960PA`** (SD-1) |
| OBQ-3 | Screenshot of $6,628.32 | Optional debug | Open |
| SD-3 | A1 (PO rates on shared `1960PA`) vs A2 (split codes) | Fleet correctness | **Default A1** until overridden |

---

## Appendix

- Fleet impact: `Issue_Log_Items/Issue_56/evidence/issue56_pua_fleet_impact.csv`  
- Option summary: `Issue_Log_Items/Issue_56/evidence/issue56_option_ab_summary.csv`  
- Planning: `Issue_56_Planning_Report.md`  
- Dependency Gate: `Issue_56_Dependency_Gate.md` (Conditional Pass)  
- Related: #21E, #37, #40, #41, #48  

### G3 checklist

- [x] Risk report published with Go/No-Go  
- [x] Impact quantified (493 MPLAN; 7 QuikCvs plans; `1960PA` collision proven)  
- [x] Unrelated fields marked untouched  
- [x] #25 / #26 preservation confirmed  
- [ ] User acknowledged recommendation *(awaiting)*  
