# Issue #36 — Risk Review Report

**Issue:** #36 — Modal Premium factors at policy level (`quikmstr`)  
**Framework stage:** Risk Agent (G3)  
**Status:** **CONDITIONAL GO** — Ready for Development after project-lead acknowledgment  
**Fallback simulated:** Leave blank if phase-1 plan missing (0 policies today)  
**Generated:** 2026-07-09  
**Agent:** Risk Agent (read-only simulation; no production code changes)

**Status note:** Risk analysis only — no production code changes unless later approved.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Safe surgical enrichment of four blank `quikmstr` columns from existing `#21J` plan factors, with the **two PAC special modes** (Q→`MQTRL=25`, S→`MSEMI=50`) applied after, and **MMTHD ≠ MMTHB** preserved independently; proceed only if Development (1) does not touch `MMODEPREM`/`MPREM`, (2) runs plan-copy before PAC, (3) never collapses MTHD/MTHB into one value, and (4) adds a fleet validator covering both PAC modes.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| quikmstr.MSEMI | Always blank (rulebook unmapped) | Copy quikplan.SEMI via phase-1 MPLAN; PAC may set 50.0000 | **Yes** |
| quikmstr.MQTRL | Always blank | Copy quikplan.QTRL; PAC may set 25.0000 | **Yes** |
| quikmstr.MMTHD | Always blank | Copy quikplan.MTHD | **Yes** |
| quikmstr.MMTHB | Always blank | Copy quikplan.MTHB | **Yes** |
| quikmstr.MMODEPREM | PPOLC.MODE_PREMIUM | Unchanged | **No** |
| quikplan SEMI/QTRL/MTHD/MTHB | #21J mapping | Unchanged (read source) | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| quikmstr.MMODEPREM | PPOLC.MODE_PREMIUM | **No** |
| quikmstr.MMODE / MBILLFRM / MBILLDAY | PPOLC | **No** |
| quikridr.MPREM | #26 | **No** |
| quikridr.M*FEE | Existing | **No** |
| quikplan modal columns | #21J | **No** (read only) |
| MPOLICY width | #25 | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `qla_core/modal_premium_factors.py` | Add plan→mstr copy; keep PAC function |
| `app.py` / `QLA_Migration/app.py` | Call copy then PAC after quikridr emit |
| `Sync_Rulebook_quikmstr.csv` | No new rows required (post-emit pattern) |
| `tools/validators/validate_issue21j_modal_factors.py` | Preserve; add #36 validator |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| Total quikmstr rows | 5,083 |
| Currently non-blank MSEMI/MQTRL/MMTHD/MMTHB | **0** |
| Rows that would gain factors (simulation) | **5,083** |
| Rows unchanged (factor columns) | 0 |
| Phase-1 plan missing / not in quikplan | **0** |
| PAC quarterly overrides (MQTRL=25) — special mode 1 | **4** |
| PAC semiannual overrides (MSEMI=50) — special mode 2 | **8** |
| Plans where MTHD ≠ MTHB (must stay distinct on mstr) | **91** of 141 |
| MMODEPREM blank | 0 (must stay populated) |

### Breakdown

| Dimension | rows | would_change |
|-----------|-----:|-------------:|
| All policies | 5,083 | 5,083 (blank → plan factors) |
| PAC GL85 Q/S subset | 12 | 12 (plan copy + override on S/Q field) |

**Blast radius:** Four columns on `quikmstr` only. No row-count change. No other tables written by this fix.

---

## 5. Fallback Recommendation

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| **A. Fleet copy from quikplan + PAC after** | 5,083 | **Recommended** |
| B. Populate only current billing mode’s factor | Partial | Reject — Names tab shows full grid |
| C. Hardcode generic 51/26.5/9.25 | 5,083 | Reject — ignores #21J per-plan mapping |
| D. Wait for LifePRO quote-factor extract | 0 | Reject — extract does not exist; blocks Names tab |

**Recommended fallback:** If `MPLAN` missing from `quikplan`, leave that policy’s four fields blank and increment a log counter (expected 0).

---

## 6. Trace Policies

| Policy | Before | Proposed | Pass? |
|--------|--------|----------|-------|
| 010148856C | all blank | 51.0140 / 26.0010 / 8.9964 / 8.9989 | Yes |
| 010713704C | all blank | 52.5000 / 27.0000 / 9.1999 / 8.8018 | Yes |
| 010560185C | all blank | SEMI=52.0000, **MQTRL=25.0000**, MMTHD=9.0000, MMTHB=8.3333 | Yes (PAC Q) |
| 010442216C | all blank | **MSEMI=50.0000**, QTRL=26.5000, MMTHD=9.0000, MMTHB=8.3333 | Yes (PAC S) |

---

## 7. Top Changes

Not a numeric delta on premiums — categorical blank→factor. Largest “semantic” change is fleet-wide enablement of Names-tab factor math. `MMODEPREM` must show **zero** diffs in validation.

---

## 8. Regression Surfaces

| Surface | Risk | Guard |
|---------|------|-------|
| #26 MMODEPREM / MPREM | High if overwritten | Validator equality vs pre-change snapshot / source |
| #21J quikplan factors | Medium if rewrite | Do not call plan overlay from this path |
| #21J PAC overrides | Medium if order wrong | **Copy then PAC** |
| #25 MPOLICY | Low | Reuse format_qladmin_mpolicy only for joins |
| quikridr fees | Low | Out of write set |
| Row counts quikmstr | Low | Assert same row count |

---

## 9. Recommended Development Task (Surgical)

1. In `qla_core/modal_premium_factors.py`, add `apply_plan_modal_factors_to_quikmstr(...)`.
2. Wire in both `app.py` files: after quikridr CSV written, load quikmstr → apply plan copy → apply PAC → rewrite quikmstr.
3. Bump `APP_VERSION` both apps.
4. Add `tools/validators/validate_issue36_quikmstr_modal_factors.py`.
5. No rulebook schema reorder; no wholesale app rewrite.

---

## 10. Validation / Regression Checklist (for G5/G6)

- [ ] ≥99.9% policies have non-blank MSEMI/MQTRL/MMTHD/MMTHB (expect 100%)
- [ ] Trace policies match proposed factors
- [ ] PAC special mode 1 (Q): 4× MQTRL=25.0000 on PAC+mode3+170858/17085M
- [ ] PAC special mode 2 (S): 8× MSEMI=50.0000 on PAC+mode6+170858/17085M
- [ ] Client workbook samples: 010560185C MQTRL=25; 010442216C MSEMI=50
- [ ] Where quikplan MTHD≠MTHB, quikmstr MMTHD≠MMTHB (no collapse)
- [ ] MMODEPREM identical to pre-fix for all policies (or vs PPOLC)
- [ ] quikplan factor columns unchanged vs #21J validator
- [ ] quikmstr row count unchanged
- [ ] #25 MPOLICY width still 10
- [ ] #26 MPREM validator PASS

---

## Gate G3 checklist

- [x] Risk report published with Go/No-Go
- [x] Impact quantified (5,083 / PAC 4+8)
- [x] Unrelated fields explicitly marked untouched
- [x] #25 / #26 preservation confirmed
- [ ] **User (or project lead) acknowledged recommendation** ← required before Development

---

## Appendix — Simulation method

Read-only join: `quikmstr` ⋈ phase-1 `quikridr.MPLAN` ⋈ `quikplan` factors; then PAC rules from `apply_pac_gl85_modal_overrides`. No files modified.
