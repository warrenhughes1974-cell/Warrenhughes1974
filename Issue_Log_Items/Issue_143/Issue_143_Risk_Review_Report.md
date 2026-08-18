# Issue #143 — Risk Review Report

**Issue:** #143 — Units Incorrect (RPU)  
**Framework stage:** Risk Agent  
**Status:** **CONDITIONAL GO — Ready for Development** (after user approval)  
**Generated:** 2026-08-18  
**Agent/script:** Cursor Grok 4.5 · `Issue_143/_risk_sim_issue143.py`  
**Evidence:** `evidence/issue143_risk_impact_summary.json`

**Status note:** Risk analysis only — no production code changes.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Remap phase-1 `MUNIT` on the **23** BF RPU policies where LifePRO units ≠ `BF_CURRENT_DB / VALUE_PER_UNIT`, so Amount Ins equals LifePRO Column DD.

**Conditions:**

1. **Mismatch-only.** Do not touch 199 BA RPU or 82 already-aligned BF RPU.  
2. **Do not write `MSAVEUNIT`.** Issue #108A leaves save fields blank on ETI/RPU phase 1.  
3. **Do not change `MPREM`, `MVPU`, `MMODEPREM`, or MPOLICY.**  
4. **#55 emit stays after the remap** (floor + leading-zero format).  
5. **UAT** Amount Ins on `9010757606C` = **$19,101.96** (units 19.10196), not $25,000.

Closed-row note for Warren: Issue **#124** `MDB = MUNIT × 1000` will follow the new units on the next QuikIswl seed for these ISWL plans (`1658C1` / `1659C2` / `1659CR`). That is the #124 formula applied to corrected units, not an override of #124. Issue **#55** is not in conflict (proposed units are all well above 0.001).

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|---|---|---|---|
| `MUNIT` default | `NUMBER_OF_UNITS` | unchanged | **No** |
| `MUNIT` BF RPU mismatch | same (copies 25.00000) | `BF_CURRENT_DB / VALUE_PER_UNIT` | **Yes — 23 rows** |
| `MVPU` | `VALUE_PER_UNIT` | unchanged | **No** |
| `MPREM` | #26 / #88 / #137 | unchanged | **No** |
| `MSAVEUNIT` on 44/45 | blank (#108A) | still blank | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|---|---|---|
| `quikridr.MPREM` | ANN / modalized fallback | **No** |
| `quikmstr.MMODEPREM` | PPOLC `MODE_PREMIUM` | **No** |
| `quikridr.MVPU` | `VALUE_PER_UNIT` | **No** |
| MPOLICY (#2) | source + `C` | **No** |
| #55 floor / emit | post-map hook | **No** (order: remap then emit) |

Side effect (not a mapping change): Names-tab annual display `MPREM × MUNIT` will fall on the 23 because `MUNIT` falls. Leave `MPREM`. Flag for UAT.

---

## 3. Repo References

| Location | Role |
|---|---|
| `Sync_Rulebook_quikridr.csv` | Default `NUMBER_OF_UNITS → MUNIT` |
| `qla_core/quikridr_decimal_emit.py` | #55 floor + format |
| `app.py` ~6168–6186 | #108A `MSAVE*` blank on NFO phase 1 |
| `app.py` PPBENTYP cache (~8004) | Pattern for `BF_CURRENT_DB` lookup |
| `qla_core/quikiswl_loader.py` | #124 `MDB = MUNIT × 1000` |

---

## 4. Population Analysis

Read-only join: PPOLC RU × PPBEN seq-1 × PPBENTYP seq-1 × current `Output/quikridr.csv` (20260630 cut).

| Metric | Count |
|---|---:|
| RPU policies | 304 |
| BA / no DD — **no change** | 199 |
| BF aligned — **no change** | 82 |
| BF unaligned — **would change** | **23** |
| Candidates missing from Output | 0 |
| Unaligned Output still = source units | 23 |
| Aligned Output already = source units | 82 |

### Unaligned by `MSTATUS`

| MSTATUS | Meaning | Rows |
|---:|---|---:|
| 45 | RPU in force | 13 |
| 53 | Death (typical) | 7 |
| 55 | Surrender / lapse-class | 3 |

Recommend remapping all 23. Same LifePRO defect.

---

## 5. Fallback Recommendation

| Option | Rows changed | Assessment |
|---|---:|---|
| A. Remap 23 BF mismatches only | 23 | **Recommended** |
| B. Remap in-force 45 only | 13 | Reject — 10 terminated still show original face |
| C. Remap all 304 RPU | 304 | **Reject** — damages BA and 82 aligned BF |
| D. No change (reload / display) | 0 | Reject — Output already equals unreduced source units |

**Recommended fallback:** Option A. If `BF_CURRENT_DB` missing or VPU ≤ 0, keep `NUMBER_OF_UNITS`.

---

## 6. Trace Policies

| Policy | Before MUNIT | Proposed MUNIT | Amount Ins after | Pass? |
|---|---:|---:|---:|:---:|
| `9010757606C` | 25.00000 | **19.10196** | $19,101.96 | Yes (SME) |
| `9010766847C` | 25.00000 | **5.16341** | $5,163.41 | Yes |
| `9010826422C` | 50.00000 | **9.65590** | $9,655.90 | Yes |
| `9010732975C` | 14.08377 | 14.08377 | $14,083.77 | Control |
| `9010165095C` | 1.69072 | 1.69072 | $1,690.72 | BA control |

---

## 7. Top Largest Unit Decreases

| Policy | Before | After | Delta (units) |
|---|---:|---:|---:|
| `9010826422C` | 50.00000 | 9.65590 | −40.34410 |
| `9011001627C` | 30.00000 | 3.04464 | −26.95536 |
| `9010766847C` | 25.00000 | 5.16341 | −19.83659 |
| `9010757606C` | 25.00000 | 19.10196 | −5.89804 |

All proposed `MUNIT × 1000` equal Column DD within $0.02.

---

## 8. Material Calculation Impact

**Intentional:** Amount Ins / valuation face on 23 policies drops from original issue face to LifePRO RPU death benefit.

**Not accidental drift:** 82 aligned BF and 199 BA stay on `NUMBER_OF_UNITS`.

**Valuation:** cash-value rebuild uses units × VPU as face. Leaving 25 on `9010757606C` overstates RPU face by $5,898.04.

---

## 9. Prior Fix Preservation

| Check | Result |
|---|---|
| Issue #2 MPOLICY width-11 + C | **No touch** |
| Issue #26 / #88 / #137 MPREM | **No touch** |
| Issue #55 MUNIT floor + emit | **Keep; run after remap** |
| Issue #108A MSAVE blank on 44/45 | **Keep; do not populate** |
| Issue #124 QuikIswl MDB | **Follows MUNIT** — notify only, not a Closed-row override |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] `9010757606C` MUNIT = 19.10196; Amount Ins = 19101.96
- [ ] `9010766847C` / `9010826422C` remapped to DD/VPU
- [ ] `9010732975C` unchanged 14.08377
- [ ] BA RPU sample `9010165095C` unchanged
- [ ] #55 traces `9018495BC` / `9018499CC` / `9018510C` still floored / leading-zero
- [ ] `MPREM` / `MVPU` / `MPOLICY` unchanged on the 23
- [ ] `MSAVEUNIT` still blank on status-45 candidates
- [ ] quikridr row count unchanged
- [ ] Non-RPU policies: MUNIT unchanged

---

## 11. Recommended Development Agent Task

1. Surgical post-map hook (or tight branch beside the existing PPBENTYP cache):  
   `if PUT=RU and TYPE_CODE=BF and DD>0 and |units − DD/VPU| > 0.01: MUNIT = DD/VPU`  
   then existing `apply_quikridr_decimal_emit()`.
2. Do **NOT** change: rulebook `NUMBER_OF_UNITS→MUNIT` default, `MPREM`, `MVPU`, `MSAVEUNIT`, status, #55 threshold, MPOLICY.
3. Version bump both `app.py` files (next after v58.95).
4. Validator `tools/validators/validate_issue143_rpu_munit.py` — 23 PASS, 82+BA controls, #55 traces.

---

## Appendix

- Simulation: `Issue_Log_Items/Issue_143/_risk_sim_issue143.py`
- Summary: `Issue_Log_Items/Issue_143/evidence/issue143_risk_impact_summary.json`
- Research: `Issue_143_Research_Report.md`
