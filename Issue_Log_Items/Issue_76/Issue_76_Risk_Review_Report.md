# Issue #76 — Risk Review Report

**Issue:** #76 — ETI/RPU phase-1 pay-up + duration for Policy Display cash values  
**Framework stage:** Risk Agent  
**Status:** **Conditional Go → Ready for Development** (pending explicit user approval)  
**Generated:** 2026-07-15  
**Model:** Cursor Grok 4.5 (locked)  
**Status note:** Risk analysis only — no production code changes.  
**Evidence:** `evidence/issue76_risk_phase1_simulation.csv` · `scripts/risk_review_issue76_payup_mlastann.py`

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Blast radius is quantified and matches UAT; Development may proceed under the locks below.

| Factor | Assessment |
|--------|------------|
| Scope | Phase-1 `quikridr` only when master `MSTATUS` ∈ {44, 45} |
| Impact | **223** `MPAYUP` changes; **400** `MLASTANN` changes; **0** blank `MPAIDTO` |
| #60 PUA | **0** phase-1 PUA plans on 44/45; **173** later-phase rows on 44/45 must stay untouched (sample phase-2 `1708PA` already `MPAYUP=MEFFDATE`) |
| #72 NFO / #25 / #26 | Untouched |
| OBQ-76-1 | Lock **SD-76-8**: duration year = **run-date year** (2026 → sample `t=14`). Valuation-year (2025) would yield `t=13` on every candidate — document for YE UAT |

Development may proceed after user says **Approved for Development** and switches to **Composer 2.5**.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| Phase-1 `MPAYUP` when status ∈ {44,45} | LifePRO `PAY_UP_DATE` | `quikmstr.MPAIDTO` | **Yes** (223 ≠ today) |
| Phase-1 `MLASTANN` when status ∈ {44,45} | `val_year − MEFFDATE year` | `sys_year − MPAYUP year` | **Yes** (400) |
| Phase-1 `MPAYUP` / `MLASTANN` when status ∉ {44,45} | Existing paths | Unchanged | **No** |
| Phase > 1 (incl. #60 PUA) | Existing (#60 inherit) | Unchanged | **No** |
| `MNFOPT` / `MEFFDATE` / `MPREM` / rates | — | Unchanged | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| MPOLICY padding (#25) | **No** |
| quikridr.MPREM (#26) | **No** |
| MEFFDATE / MAGE / MEXPRY / MUNIT | **No** |
| MNFOPT (#72) | **No** |
| PUA phase `MPAYUP` (#60) | **No** (phase ≠ 1) |
| MCV0/1/2 amounts | **No** (rebuild remains UAT) |
| Rates / BAND / NFOINT / MRRULE | **No** |
| MISSCNTRY (#73 CLOSED) | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `Sync_Rulebook_quikridr.csv` | `PAY_UP_DATE→MPAYUP` — keep for non-candidates |
| `app.py` `_compute_quikridr_mlastann` / `_apply_quikridr_mlastann` | Today: duration from **MEFFDATE** — #76 overrides after for 44/45 phase 1 |
| `app.py` `_apply_pua_rider_inheritance` | #60 — must run without #76 overwrite on PUA rows |
| Status / paid-to caches (PPOLC / quikmstr emit) | Join source for gate + `MPAIDTO` |

---

## 4. Population Analysis (simulated on current Output)

| Metric | Count |
|--------|------:|
| quikmstr / quikridr rows | 5,083 / 6,934 |
| MSTATUS 44 / 45 | 206 / 194 |
| Phase-1 candidates (44/45) | **400** |
| Blank `MPAIDTO` (fallback leave) | **0** |
| `MPAYUP` would change | **223** |
| `MLASTANN` would change (sys year 2026) | **400** |
| Phase > 1 on 44/45 (must not change) | **173** |
| Phase-1 PUA plans on 44/45 | **0** |
| PUA-plan rows on 44/45 policies (later phases) | 27 |
| Non-44/45 phase-1 rows | 4,683 (untouched) |
| Mean `MLASTANN` delta (after − before) | **−24.4** (range −54 … −3) |

### Status split (candidates)

| Status | Candidates | Pay-up change | Duration change |
|--------|----------:|--------------:|----------------:|
| 44 | 206 | (subset of 223) | 206 |
| 45 | 194 | (subset of 223) | 194 |

### OBQ-76-1 — year source

| Year source | Sample `010407670C` `MLASTANN` | Fleet note |
|-------------|--------------------------------:|------------|
| **Run date 2026 (SD-76-8)** | **14** | Matches YE screenshot `t=14` |
| Valuation 2025 | 13 | Would differ on **all 400** candidates by −1 |

**Risk lock:** implement run-date year; optional later env override only if client demands YE freeze.

---

## 5. Fallback Recommendation

| Option | Assessment |
|--------|------------|
| **A. Phase-1 override for 44/45: MPAYUP=MPAIDTO; MLASTANN=sys_year−payup_year (recommended)** | Matches UAT; quantified; preserves #60/#72 |
| B. Set MPAYUP=MEFFDATE (issue date) for 44/45 | **Reject** — contradicts screenshot (paid-to, not issue) |
| C. Change only MLASTANN, leave contractual MPAYUP | **Reject** — still dates from 2027+duration |
| D. Blank MPAIDTO → leave source | **Adopt** (0 rows today) |
| E. Do nothing | Reject — Policy Display remains in 2080s |

**Recommended:** Option A + D under SD-76-*.

---

## 6. Trace Policies

| Policy | Status | MPAIDTO | MPAYUP before → after | MLASTANN before → after (2026) | Notes |
|--------|--------|---------|------------------------|--------------------------------:|-------|
| **010407670C** | 45 | 20121001 | 20270201 → **20121001** | 53 → **14** | Phase-2 `1708PA` stays 19720201 / 53 |
| 010374099C | 44 | 20090921 | 20730921 → **20090921** | 55 → **17** | |
| 010149295C | 44 | 19921201 | 19921201 → same | 64 → **34** | Pay-up already = paid-to |
| 010367131C | 22 | 20260801 | unchanged | unchanged | Active control |

---

## 7. Largest Duration Reductions (illustrative)

| Policy | Status | MLASTANN before → after | MPAYUP before → after |
|--------|--------|-------------------------|------------------------|
| 018313AC | 45 | 73 → 19 | same (already = paid-to) |
| 01ML8314BC | 45 | 73 → 22 | same |
| 010448375C | 44 | 51 → 3 | 20280215 → 20230915 |
| 010466471C | 44 | 50 → 4 | 20450915 → 20220115 |
| 010505481C | 45 | 47 → 2 | 20630401 → 20240601 |

Large reductions are expected: issue-year duration → paid-to-year duration.

---

## 8. Regression Surfaces

| Surface | Risk | Guard |
|---------|------|-------|
| #60 PUA `MPAYUP=MEFFDATE` | High if phase gate wrong | Apply **only** `MPHASE==1`; never rewrite `*PA` later phases |
| Hook order vs `_apply_quikridr_mlastann` | Med | Override **after** first mlastann pass |
| Status not final yet | Med | Use same final-status cache as #72 / #49 path |
| Active policies (status 22 etc.) | Low | Status gate excludes |
| YE duration off-by-one | Med | SD-76-8 + Validation note |
| CV $ still blank | Info | UAT: Data Admin + Rebuild CV after reload |

---

## 9. Recommended Development Task (surgical)

1. In `app.py` + `QLA_Migration/app.py`, after phase-1 `MPAYUP`/`MLASTANN` set and status/`MPAIDTO` available:  
   if `MSTATUS ∈ {44,45}` and `MPHASE==1` and `MPAIDTO` valid → set `MPAYUP=MPAIDTO`, `MLASTANN=str(datetime.now().year - int(MPAYUP[:4]))`.  
2. Do **not** apply to phase > 1 or when `MPAIDTO` blank.  
3. Do **not** alter `_apply_pua_rider_inheritance` logic.  
4. Bump `APP_VERSION` both copies.  
5. Rebatch; publish `Output/Test_Validation/quikridr.csv`.  
6. Validator: sample + fleet formula + #60 phase-2 control + non-44/45 unchanged + #25/#26 smoke.

**Model:** Composer 2.5 only after **Approved for Development**.

---

## 10. Validation / Regression Checklist

- [ ] `010407670C` phase 1: `MPAYUP=20121001`, `MLASTANN=14` (run year 2026)
- [ ] `010407670C` phase 2 `1708PA`: `MPAYUP` still = `MEFFDATE` (19720201)
- [ ] All 400 phase-1 @44/45: `MPAYUP==MPAIDTO` and `MLASTANN==sys_year−payup_year`
- [ ] Non-44/45 phase-1: `MPAYUP`/`MLASTANN` unchanged vs pre-fix baseline
- [ ] #72 `MNFOPT` still 44→2 / 45→3 on sample
- [ ] #25 / #26 smoke
- [ ] UAT: reload ridr → Data Admin → Rebuild CV → CV dates ~ paid-to anniversary years

---

## Gate Criteria (G3 — Risk Approved)

- [x] Risk report published with Go/No-Go  
- [x] Impact quantified (not guessed)  
- [x] Unrelated fields explicitly marked untouched  
- [x] #25 / #26 preservation confirmed  
- [ ] User acknowledged recommendation (**Approved for Development**)

---

## Next step

Say **Approved for Development** and switch chat model to **Composer 2.5**.
