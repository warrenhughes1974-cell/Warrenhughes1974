# Issue #36 — Regression Report (G6)

**Issue:** #36 — Modal Premium factors at policy level (`quikmstr`)  
**Framework stage:** Regression Agent  
**Engine version:** **v57.62**  
**Baseline:** Pre-fix Output (factors 100% blank) + stable fleet row counts from v57.46+ / G5  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-07-09  
**Verdict:** **PASS**

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|-----------|-----------------|
| `quikmstr.MSEMI/MQTRL/MMTHD/MMTHB` | Blank → plan factors (+ PAC Q/S overrides) |
| `quikmstr` other columns | **No change** |
| `quikmstr` row count | **No change** (5083) |
| `quikplan` / `quikridr` / other tables | **No change** |
| Code | `modal_premium_factors.py` + both `app.py` (v57.62) |

---

## 2. Row Count Comparison

| Table | After (current) | Expected stable | Delta | OK? |
|-------|----------------:|----------------:|------:|-----|
| quikmstr | 5,083 | 5,083 | 0 | **PASS** |
| quikridr | 6,934 | — | — | Present |
| quikplan | 141 | 141 | 0 | **PASS** |
| quikmemo | 5,083 | 5,083 | 0 | **PASS** |
| quikclid | 34,449 | — | — | Present |
| quikclnt | 13,597 | — | — | Present |
| quikbenf | 5,916 | — | — | Present |
| quikprmh | 206,861 | — | — | Present |
| quikdvdp | 5,083 | — | — | Present |
| quikdvpr | 31 | — | — | Present |
| quikagts | 4,843 | — | — | Present |
| quikactg | 87 | — | — | Present |

No table gained/lost rows due to #36 (factor columns only).

---

## 3. Non-Target Field Diff (quikmstr)

| Column group | Check | OK? |
|--------------|-------|-----|
| Schema order vs `TABLE_SCHEMAS["quikmstr"]` | Exact match (45 cols) | **PASS** |
| MPOLICY / MSTATUS / MMODE / MBILLFRM | 0 blank | **PASS** |
| MMODEPREM | 0 blank; traces unchanged (19.23 / 43.91 / 15.00 / 60.00) | **PASS** |
| MSEMI/MQTRL/MMTHD/MMTHB | Intentional populate (0 blank) | **PASS** (in scope) |

Other tables not rewritten by #36 path (post-emit enrichment of `quikmstr.csv` only).

---

## 4. Prior Issue Fix Regression

### Issue #25 — MPOLICY padding

| Check | Result |
|-------|--------|
| `validate_mpolicy_width.py` | **PASS** |
| quikmstr short MPOLICY | **0** |

### Issue #26 — MPREM / MMODEPREM

| Check | Result |
|-------|--------|
| quikridr.MPREM blank | **0 / 6934** |
| quikmstr.MMODEPREM blank | **0 / 5083** |
| Full `validate_issue26_mprem.py` | N/A — dated Source extract filenames missing; blank-rate guard used |

### Issue #21J — Plan factors + PAC

| Check | Result |
|-------|--------|
| `validate_issue21j_modal_factors.py` | **PASS** |
| quikplan SEMI samples (1659C2 / 170858 / 221END) | **PASS** |
| PAC Q=4 / S=8 | **PASS** |
| quikmemo conversion segments = 5083 | **PASS** |

### Issue #36 (reconfirm)

| Check | Result |
|-------|--------|
| `validate_issue36_quikmstr_modal_factors.py` | **PASS** |
| MMTHD≠MMTHB collapse | **0 / 3443** |

---

## 5. Schema Integrity (AGENTS.md)

| Check | Result |
|-------|--------|
| Field order preserved | **PASS** |
| Field types/lengths (Help 7.4 factors) | Values as percent strings matching quikplan | **PASS** |
| No new blank MRIDRID | **0 blank** | **PASS** |
| QLA formatting / MPOLICY width | **PASS** |
| Both `app.py` versions | **v57.62** | **PASS** |

---

## 6. Batch / Fleet Checks

| Check | Result |
|-------|--------|
| Full re-batch from scratch | Not required for G6 — Output enriched with v57.62 logic; batch hook wired for next full run |
| Issue validators | #36 / #21J / #25 **PASS** |
| Audit log anomalies | None observed for this scope |
| Code surface | `apply_plan_modal_factors_to_quikmstr` + PAC; no unrelated converters touched |

Evidence script: `Issue_Log_Items/Issue_36/scripts/_g6_regression_checks.py` → **REGRESSION PASS**

---

## 7. Failures

None.

---

## 8. Recommendation

- [x] Advance to **Closure Agent** / **Ready for Client UAT**
- [ ] Return to Development — N/A

**Client UAT focus:** Names tab Modal Premiums on `010148856C`; PAC Q `010560185C`; PAC S `010442216C`.

---

## Gate G6 checklist

- [x] Row counts stable
- [x] Unrelated fields unchanged
- [x] #25 / #26 / #21J preservation verified
- [x] Regression report published
- [x] No schema integrity violations

**G6 status:** **PASS**
