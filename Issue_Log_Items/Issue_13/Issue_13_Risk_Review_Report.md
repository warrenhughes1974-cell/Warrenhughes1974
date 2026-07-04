# Issue #13 — Risk Review Report

**Issue:** #13 — Incorrect QL Status  
**Date:** 2026-07-04  
**Converter version (baseline):** v57.47  
**Prior stages:** Intake ✅ · Planning ✅ · Dependency Gate ✅  
**Framework stage:** Risk Agent (G3)  
**Next stage:** Development Agent (awaiting explicit authorization)

**Status note:** Risk analysis only — no production code changes in this stage.

---

## Go / No-Go Recommendation

```text
GO
```

Proceed with **surgical MSTATUS interceptor change** in `app.py` / `QLA_Migration/app.py` per Option A. Fleet impact is **bounded, intentional, and aligned with approved business rule**. No rulebook or translation-table changes required.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed (Option A) | Rows changing |
|-------|---------|---------------------|--------------:|
| **`quikmstr.MSTATUS`** | `PAID_UP_TYPE` wins when PU/RU/ET/LE/LP/SP | When `CONTRACT_CODE=T`, use `CONTRACT_CODE`+`CONTRACT_REASON` only | **607** |
| **`quikmstr.MSTATDATE`** | `CONTRACT_DATE` | Unchanged | **0** |
| **`quikridr.MPHSTAT`** (phase 1) | Inherits terminal `quikmstr.MSTATUS` | Follows new master status | **subset of 607** |
| All other fields | — | Unchanged | **0** |

---

## 2. Premium / Related Fields Untouched

| Target | Source / behavior | Touched? |
|--------|-------------------|----------|
| `quikmstr.MMODPREM` | PPOLC modal premium | **No** |
| `quikridr.MPREM` | ANN_PREM_PER_UNIT + fallback (#26) | **No** |
| `MPOLICY` width | `format_qladmin_mpolicy()` (#25) | **No** |
| `MNFOPT` / `MDIVOPT` | #21A PPBENTYP cache | **No** |
| `Master_Value_Translation.csv` | ST_* keys | **No** |
| `quikclms.CLAIMSTAT` | Phase 10B lifecycle | **No** |
| Row count `quikmstr` | 5,084 | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `app.py` ~5870–5878 | **MSTATUS interceptor — change target** |
| `app.py` ~6035–6037 | ST_ translation lookup |
| `app.py` ~6170–6185 | quikridr MPHSTAT inherit |
| `Master_Value_Translation.csv` | `ST_T_DC`→53, `ST_T_LP`→54, `ST_T_SR`→55, `ST_T_EX`→56, `ST_T_MA`→57 |
| `Issue_Log_Items/Issue_13/Issue_13_Risk_Simulation.csv` | Fleet simulation output |
| `Issue_Log_Items/Issue_13/_risk_review_issue13_mstatus.py` | Simulation script |

---

## 4. Population Analysis (simulated)

| Metric | Count |
|--------|------:|
| Total PPOLC / quikmstr policies | 5,084 |
| **MSTATUS would change** | **607** |
| Unchanged | 4,477 |
| T + non-blank PAID_UP_TYPE (trigger set) | 611 |
| Proposed unmapped keys | 2 (pre-existing: header row + `ST_S_PC`) |

### Breakdown by transition (top)

| From | To | Policies |
|------|-----|--------:|
| 41 Paid Up | 53 Terminated/Death | 174 |
| 44 Extended Term | 57 Matured | 86 |
| 45 RPU | 53 Terminated/Death | 78 |
| 44 Extended Term | 54 Lapsed | 69 |
| 44 Extended Term | 55 Surrendered | 63 |
| 44 Extended Term | 53 Terminated/Death | 40 |
| 45 RPU | 55 Surrendered | 31 |
| 41 Paid Up | 55 Surrendered | 29 |

---

## 5. Fallback Recommendation

| Scenario | Recommendation |
|----------|----------------|
| `CONTRACT_CODE=T`, blank `CONTRACT_REASON` | Use key `ST_T_`; if unmapped, existing `trans_map.get` fallback (no new behavior) |
| Translation miss on valid T + reason | **Reject** adding new keys without client request — all T reasons in fleet map today |
| Non-T contracts with PUT | **Keep current** PAID_UP_TYPE-first logic |

---

## 6. Trace Policies

| Policy | Before | Proposed | Pass? |
|--------|-------:|---------:|-------|
| 010516211C (Eric) | 44 | **54** | ✅ Lapsed |
| 011101663C (Eric) | 41 | **56** | ✅ Expired |
| 010397318C | 45 | **53** | ✅ Death |
| 010464590C | 45 | **53** | ✅ Death |
| 010784054C | 56 | **56** | ✅ No change |

---

## 7. Downstream Impact Notes

- **Issue #34 / governance joins** on `quikmstr.MSTATUS` may reclassify policies (e.g., more Terminated/Death, fewer Extended Term). Expected and intentional.
- **Status analysis runner** should be updated in Development or Validation to mirror new precedence for future diffs.

---

## 8. Material Calculation Impact

**None.** MSTATUS is display/governance metadata — no premium, CV, or rate calculations depend on this field in the conversion engine.

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Not in scope** — PASS |
| Issue #26 MPREM / MMODPREM | **Not in scope** — PASS |
| Issue #21A MNFOPT cache | **Not in scope** — PASS |

---

## 10. Regression Testing Checklist (Validation Agent)

- [ ] Trace: 010516211C → MSTATUS **54**; 011101663C → **56**
- [ ] Fleet change count ≈ **607** (±0)
- [ ] quikmstr row count **5,084** unchanged
- [ ] MPREM / MMODPREM unchanged on sample policies
- [ ] MPOLICY width unchanged (#25 validator)
- [ ] quikridr phase-1 MPHSTAT inherits new terminal code on 010516211C

---

## 11. Recommended Development Agent Task

1. Update MSTATUS interceptor in **`app.py`** and **`QLA_Migration/app.py`** per Planning §4 pseudocode.
2. Version bump: **v57.48** — Issue #13 MSTATUS termination precedence.
3. Add **`tools/validators/validate_issue13_mstatus.py`**.
4. Mirror logic in **`plan_analysis/status_analysis/status_analysis_runner.py`** `derive_mstatus_from_source_fields()`.
5. Re-run full batch; attach validation report.

**Do NOT change:** rulebooks, Master_Value_Translation, claims derivation, premium paths.

---

## Appendix

- Simulation CSV: `Issue_Log_Items/Issue_13/Issue_13_Risk_Simulation.csv`
- Summary: `Issue_Log_Items/Issue_13/Issue_13_Risk_Simulation_Summary.txt`
