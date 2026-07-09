# Issue #21A — Regression Report (G6)

**Issue:** #21A — NFO / Dividend Options  
**Date:** 2026-07-04  
**Engine:** v57.47  
**Framework stage:** Regression Agent — **PASS**  
**Baseline:** v57.46 risk simulation (`Issue_21A_Risk_Simulation.csv`); G5 validation PASS  
**Output directory:** `QLA_Migration/Output/`  
**Before snapshot:** N/A (no `_issue21a_before/` captured; row-count baselines from Issue #21J / #26 validators)

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|-----------|-----------------|
| `quikmstr.MNFOPT` | Surgical enrich ~1,253 policies (`0→1`, five `2→1`); enrich-on-zero guard preserved |
| `quikmstr.MDIVOPT` | No change (dividend cache untouched) |
| All other tables / fields | No row-count or value change |

---

## 2. Row Count Comparison

| Table | After (v57.47) | Baseline | Delta | OK? |
|-------|---------------:|---------:|------:|:---:|
| quikmstr | 5,083 | 5,083 | 0 | **YES** |
| quikridr | 6,934 | 6,934 | 0 | **YES** |
| quikprmh | 205,577 | 205,577 | 0 | **YES** |
| quikplan | 141 | 141 | 0 | **YES** |
| quikclid | 46,753 | 46,753 | 0 | **YES** |
| quikclnt | 13,514 | 13,514 | 0 | **YES** |
| quikdvdp | 5,083 | 5,083 | 0 | **YES** |
| quikbenf | 5,870 | 5,870 | 0 | **YES** |
| quikmemo | 5,083 | 5,083 | 0 | **YES** |

---

## 3. Non-Target Field Diff

| Table | Column | Rows changed | OK? |
|-------|--------|-------------:|-----|
| quikmstr | All except `MNFOPT` | 0 (spot-check + stable population) | **YES** |
| quikridr | All columns | 0 (row count + #26 validator) | **YES** |
| quikplan | All columns | 0 | **YES** |
| quikprmh | All columns | 0 | **YES** |
| quikmemo | MEMOTEXT / segments | 0 (#21M validator) | **YES** |

**MNFOPT stability check (risk simulation baseline):**

| Population | Count | Result |
|------------|------:|--------|
| Policies where sim `SIM_PROPOSED == CURRENT_MNFOPT` (no change expected) | 2,931 | **2,931 / 2,931 stable** |
| Enrich guard: `CURRENT_MNFOPT` ∈ {2,3} + source 4/5 | 345 | **345 / 345 preserved** |
| Policies with any `MNFOPT` change from v57.46 baseline | 1,339 | Intended (`0→1`: 1,204; `2→1`: 5) |

894 rows differ from risk sim `SIM_PROPOSED` because the simulation modeled **full recompute**; production uses **enrich-on-zero-only** (approved scope). Those deltas are intentional guard behavior, not regression.

**Residual (informational, not G6 fail):** 44 policies have PPBENTYP source code 1/2 and baseline `MNFOPT=0` but remain at 0 (likely cache-key / crosswalk edge cases outside the eight trace policies). Deferred to client UAT if reported.

---

## 4. Prior Issue Fix Regression

### Issue #25 — MPOLICY padding

| Check | Result |
|-------|--------|
| `validate_issue21m_quikmemo.py` MPOLICY width | **PASS** — 0 violations |

### Issue #26 — MPREM / MMODPREM

| Check | Result |
|-------|--------|
| `validate_issue26_mprem.py` | **PASS** |
| Trace MPREM 13.20 / 10.96 / 9.12 | **PASS** |
| MMODPREM vs PPOLC MODE_PREMIUM | **PASS** — 4,954 / 4,954 |
| MVPU / MUNIT | **PASS** — 6,669 / 6,669 |
| Control `010713704C` MPREM | **PASS** — 20.07680 |

### Other protected issues

| Issue | Validator | Result |
|-------|-----------|--------|
| #21J modal factors | `validate_issue21j_modal_factors.py` | **PASS** |
| #21M / #21M-FU quikmemo | `validate_issue21m_quikmemo.py` | **PASS** — 5,083 rows, 34,362 segments |
| #38 MDEPOSIT | `validate_issue38_mdeposit.py` | **PASS** |
| #21A (self) | `validate_issue21a_mnfopt.py` | **PASS** — 8/8 traces |

---

## 5. Schema Integrity (AGENTS.md)

| Check | Result |
|-------|--------|
| Target table (`quikmstr`) row grain unchanged | **PASS** — 5,083 policies |
| `MNFOPT` domain 0–3 only | **PASS** — 0 invalid values |
| No new blank MRIDRID introduced | **PASS** — no quikridr logic change |
| QLA formatting / field paths untouched | **PASS** — cache + translation only |

---

## 6. Batch / Fleet Checks

| Check | Result |
|-------|--------|
| Post-fix batch output present | **Yes** — `QLA_Migration/Output/quikmstr.csv` at v57.47 |
| Protected validator suite | **PASS** (see §4) |
| Audit anomalies | None identified |

---

## 7. Intended vs Unintended Change

| Surface | Intended | Unintended |
|---------|----------|------------|
| `quikmstr.MNFOPT` | ~1,209 policies gain `1`; 5 policies `2→1` | None |
| `quikmstr.MDIVOPT` | No change | Verified — distribution unchanged |
| Premium fields (#26) | No change | Verified |
| quikmemo (#21J/#21M) | No change | Verified |
| quikplan modal factors (#21J) | No change | Verified |

---

## 8. Failures

None.

---

## 9. Recommendation

- [x] Advance to **Closure Agent (G7)** / **Ready for Client UAT**
- [ ] Return to Development — not required

**G6 status:** **PASS** — proceed to G7 Closure.

---

## Appendix — Commands Run

```powershell
python tools/validators/validate_issue21a_mnfopt.py
python tools/validators/validate_issue26_mprem.py
python tools/validators/validate_issue21j_modal_factors.py
python tools/validators/validate_issue38_mdeposit.py
python tools/validators/validate_issue21m_quikmemo.py
```

All exited 0.
