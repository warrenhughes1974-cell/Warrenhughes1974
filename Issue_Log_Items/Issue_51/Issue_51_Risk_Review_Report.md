# Issue #51 — Risk Review Report

**Issue:** #51 — Missing Interest Table (A60MIR / A96DAR) — Projected Values Crash Loop  
**Framework stage:** Risk Agent  
**Status:** **Conditional Go** — Ready for Development pending user approval  
**Fallback simulated:** QuikAint 0.0000 stubs (PPBEN authority)  
**Generated:** 2026-07-11  
**Agent/script:** Risk Agent (Cursor Grok 4.5) · `scripts/research_issue51_quikaint_gap.py`

**Status note:** Risk analysis only — no production code changes unless later approved.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Add exactly two QuikAint rows (`A60MIR`, `A96DAR`) at `MINTRATE/MINTRATE1=0.0000` / `MEFFDATE=19000101`, wire into `Output/rates/` load package; do not touch QuikUint, quikridr status filter, #21D, #25, or #26. Proceed to Development on **Composer 2.5** after user approval. If UAT still errors, emit matching QuikAing/QuikAinf stubs as same-issue follow-on.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| QuikAint A60MIR | Absent | `19000101 / 0.0000 / 0.0000` | **Yes — insert** |
| QuikAint A96DAR | Absent | `19000101 / 0.0000 / 0.0000` | **Yes — insert** |
| Output/rates QuikAint.csv | Missing from package | Present in manifest + folder | **Yes** |
| QuikUint MIR/DAR | Absent (correct) | Remain absent | **No** |
| quikridr MPHSTAT=56 rows | Present (6) | Unchanged | **No** |
| quikdvdp.MDEPINT | #21D rules | Unchanged | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| quikmstr.MMODPREM | MODE_PREMIUM | **No** |
| quikridr.MPREM | #26 ANN_PREM_PER_UNIT | **No** |
| MPOLICY / MEMOKEY padding | #25 | **No** |
| QuikGps/Dbs/Nps/Cvs/Tvs factors | Rate_Table / PAAGERAT | **No** |
| QuikUint ISWL | #32 PDINT | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `data_governance/rules/chk_quikplan.py` PLAN-023 | Flags missing QuikAint for A* plans |
| `QLA_Migration/Data_Goverence.txt` L155 | A-plan annuity table rule |
| `plan_analysis/phase_r6_quikaint_rates/build_quikaint.py` | PFSA builder (extend or parallel stub emit) |
| `qla_core/rate_emit.py` / `rate_dbf_schema.py` | Rate package writers — surgical QuikAint add |
| `qla_core/quikuint_loader.py` | Must remain ISWL-only |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| quikplan A* plans | 2 |
| quikridr target rows | 6 |
| Rows that would change (QuikAint) | **+2** (new) |
| Target policies for UAT | 6 |
| Active MIR/DAR riders | 0 |
| PPBEN FV_GUAR_RATE nonzero | 0 |

### Breakdown

| Dimension | rows | would_change |
|-----------|-----:|-------------:|
| A60MIR ridr | 2 | 0 (ridr untouched); QuikAint +1 plan |
| A96DAR ridr | 4 | 0; QuikAint +1 plan |
| MPHSTAT=56 | 6 | 0 |

Evidence: `evidence/issue51_gap_summary.csv`, `issue51_quikridr_population.csv`, `issue51_ppben_fv_guar_rate.csv`

---

## 5. Fallback Recommendation

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| **A — QuikAint 0% stubs** | +2 | **Recommended** — matches PPBEN; stops missing-table |
| B — QuikUint MIR/DAR | +N | **Reject** — wrong table / product class |
| C — DEPINT scalar only | 2 plan cells | **Reject** — insufficient for interest table SEEK |
| D — Drop status-56 from quikridr | 6 | **Reject** — destroys history; wrong layer |
| E — QuikAint + QuikAing/QuikAinf 0% | +2..6 | **Fallback if UAT fails** after A |

**Recommended fallback:** Option A; authorize E without new Risk if needed.

---

## 6. Trace Policies

| Policy | Before | Proposed | Pass? |
|--------|--------|----------|-------|
| 010348734C / A60MIR | Interest table not found | QuikAint row present @ 0% | Expected Pass (UAT) |
| 010510671C / A96DAR | Same class of error | QuikAint row present @ 0% | Expected Pass |
| Unrelated ISWL policy | QuikUint / MDEPINT as today | Unchanged | Must Pass |

---

## 7. Top Changes

| Change | Before | After | Delta |
|--------|--------|-------|------:|
| QuikAint row count (targets) | 0 | 2 | +2 |
| Rate package file count | QuikAint absent | QuikAint present | +1 file |

No numeric policy-field deltas expected.

---

## 8. Material Calculation Impact

- **Intentional:** Projected Values can resolve interest table SEEK for MIR/DAR; crash loop should stop.
- **Balance calc at 0% on $0 FV:** Materially zero — matches LifePRO terminated state.
- **Not a claim** that historical active-period crediting is reconstructed (no active riders remain).

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserved** — no policy-key touch |
| Issue #26 MPREM / MMODPREM | **Preserved** |
| Issue #21D MDEPINT | **Preserved** |
| Issue #32 QuikUint ISWL | **Preserved** — no allowlist expansion |

---

## 10. Regression Surfaces

| Surface | Risk | Guard |
|---------|------|-------|
| Rate package load order / manifest | Medium | Update manifest; validate QuikAint listed |
| Accidental overwrite of PFSA QuikAint if merged | Medium | Prefer additive stub file or append-only for MIR/DAR codes |
| Schema mismatch vs Help §7.31 | High if wrong | Clone field order from `quikaint_append.csv` |
| DBF vs CSV UAT path | Medium | Emit both if package uses DBF |
| Data governance PLAN-023 noise | Low | Should clear for these two plans |

---

## 11. Recommended Development Agent Task (exact)

**Model required:** Composer 2.5 (locked Development stage)

1. Add QuikAint to rate schema/writer if not present (`MPLAN`, `MEFFDATE`, `MINTRATE`, `MINTRATE1` per Help §7.31).
2. Emit surgical rows from `evidence/issue51_proposed_quikaint_stubs.csv` into `QLA_Migration/Output/rates/QuikAint.csv` (+ DBF if applicable).
3. Ensure rate load manifest includes QuikAint.
4. Forbid MIR/DAR on QuikUint path.
5. Bump `APP_VERSION` in root `app.py` and `QLA_Migration/app.py` if engine/rate emit path changes.
6. Add `tools/validators/validate_issue51_quikaint.py`.
7. Self-check: ridr row counts unchanged; #25/#26/#21D/#32 untouched.

---

## 12. Validation / Regression Checklist (for later stages)

- [ ] QuikAint contains A60MIR and A96DAR @ 0.0000
- [ ] QuikUint does not contain A60MIR/A96DAR
- [ ] quikridr still has 6 MPHSTAT=56 MIR/DAR rows
- [ ] PLAN-023 no longer flags these two plans for missing QuikAint (if governance run)
- [ ] Client UAT: 010348734C Projected Values — no endless interest-table error
- [ ] Spot-check unrelated policy Projected Values unchanged
- [ ] #21D MDEPINT sample unchanged
- [ ] Publish modified rate artifacts to `Output/Test_Validation/` on PASS

---

## G3 checklist

- [x] Risk report published with Conditional Go  
- [x] Impact quantified (+2 QuikAint rows; 6 UAT policies)  
- [x] Unrelated fields marked untouched  
- [x] #25 / #26 preservation confirmed  
- [ ] User acknowledged recommendation *(awaiting)*  

**Next status after user approval:** **Ready for Development**  
**Next agent:** Development Agent — **switch to Composer 2.5**
