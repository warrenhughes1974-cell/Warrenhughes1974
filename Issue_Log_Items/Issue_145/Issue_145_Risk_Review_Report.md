# Issue #145 — Risk Review Report

**Issue:** #145 — Vanish Flag (VB)  
**Framework stage:** Risk Agent  
**Status:** **GO — Ready for Development** (after user approval)  
**Fallback simulated:** none required  
**Generated:** 2026-08-19  
**Agent/script:** Cursor Grok 4.5 · read-only PPOLC join to `QLA_Migration/Output/quikspec.csv`

**Status note:** Risk analysis only — no production code changes unless later approved.

---

## Go / No-Go Recommendation

**GO** — Set `quikspec.VANISH` to **T** when LifePRO `PPOLC.BILLING_REASON` is **VB**, else leave **F**. On the current 6/30 Output that is **636** rows F→T and **4,447** unchanged. `VANISHDT`, `RESSTATE`, and `RESRVCAT` stay as they are.

**Conditions:**

1. Do **not** set vanish from 659-plan lists, “eligible to vanish,” or `BA_OR_VANISH_FLAG`.  
2. Do **not** populate `VANISHDT`.  
3. Do **not** turn on #146 leftovers (9010761639C / 9010760840C).  
4. Do **not** overwrite #141 `RESRVCAT` or #132 `RESSTATE`.  
5. Count against the **same PPOLC extract** as the batch (636 on 6/30; 635 on 7/31).

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| quikspec.VANISH | Default F (all 5,083) | T iff PPOLC BILLING_REASON=VB | **Yes** |
| quikspec.VANISHDT | Blank | Blank | **No** |
| quikspec.RESSTATE | PPOLC.RES_STATE | Unchanged | **No** |
| quikspec.RESRVCAT | PCOVR.PRODUCT_TYPE via seq-1 | Unchanged | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| quikridr.MPREM | #26 / #88 / #137 | **No** |
| quikmstr.MMODPREM | PPOLC.MODE_PREMIUM | **No** |
| MPOLICY padding | #25 / #2 | **No** |
| quikplan PRODUCT/HLOB/MKTG | #99 ISWLFE | **No** |
| QuikIsrr | #34 | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `Sync_Rulebook_quikspec.csv` | VANISH default F until this mapping |
| `qla_core/quikspec_resrvcat.py` | #141 post-hook — leave behavior |
| `app.py` quikspec write | Chain vanish enrich; bump v58.99 |
| `QLA_Migration/_validate_issue141_resrvcat.py` | Must still PASS after #145 |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| Total QuikSpec rows | 5,083 |
| Rows that would change (F→T, 6/30) | 636 |
| Rows unchanged | 4,447 |
| VB missing from QuikSpec | 0 |
| VANISHDT that would populate | 0 |

### Breakdown (6/30 VB)

| Dimension | rows | would_change |
|-----------|-----:|-------------:|
| BILLING_REASON=VB | 636 | 636 |
| 659 CEN II | 387 | 387 |
| 659 CEN SR | 242 | 242 |
| Other 659/669 | 7 | 7 |
| BILLING_CODE=A | 341 | 341 |
| BILLING_CODE blank | 295 | 295 |
| CONTRACT_CODE A / T / S | 340 / 295 / 1 | all |

7/31: 635 VB; **9011085421** moved VB→PC (would stay F on a 7/31 convert).

---

## 5. Fallback Recommendation (if applicable)

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| VB only → T (recommended) | 636 | **recommended** |
| All 659 / eligible | ~659+ | **reject** — Issue 22 trap |
| VB + #146 leftovers | 638 | **reject** |
| Flag + invented VANISHDT | 636 + dates | **reject** — no date source |

**Recommended fallback:** none. If PPOLC is missing, fail the enrich (do not silently leave all F).

---

## 6. Trace Policies

| Policy | Before | Proposed | Pass? |
|--------|--------|----------|-------|
| 9010815236C | F | T | Yes |
| 9011050114C | F | T | Yes |
| 9011069610C | F | T | Yes |
| 9010761639C | F | F | Yes |
| 9010760840C | F | F | Yes |
| 9010143726C RESRVCAT | 03 | 03 | Yes (#141) |
| 9010713704C RESRVCAT | 05 | 05 | Yes (#141) |

---

## 7. Top [N] Largest Changes

Logical flag only — no numeric delta. All 636 changes are F→T.

Sample of VB keys (first three gold traces plus vintage edge): 9010815236C; 9011050114C; 9011069610C; 9011085421C (T on 6/30 Output only).

---

## 8. Material Calculation Impact

Intentional: User Defined Vanish on for policies already coded VB in LifePRO. QLAdmin vanish billing uses this flag (#22 research: UTUIA-style flag-only). No premium, unit, or reserve-category rewrite in this issue.

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | Untouched |
| Issue #26 MPREM / MMODPREM | Untouched |
| Issue #132 RESSTATE | Untouched |
| Issue #141 RESRVCAT | Untouched (must remain 5,083 filled) |
| Issue #75 Bank Acct | Untouched (different table) |
| Issue #22 | Stays research; not closed by this flag |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] Traces T: 9010815236C; 9011050114C; 9011069610C  
- [ ] Traces F: 9010761639C; 9010760840C  
- [ ] VANISH T count = VB count on the extract used  
- [ ] VANISHDT all blank  
- [ ] RESSTATE unchanged vs pre-change Output  
- [ ] RESRVCAT still filled; #141 traces 03/03/05; Issue 141 validator PASS  
- [ ] quikspec row count 5,083; column order MPOLICY, VANISH, VANISHDT, RESSTATE, RESRVCAT  
- [ ] Non-candidate VANISH stays F  
- [ ] QuikIsrr / quikmstr / quikridr not in the change set  

---

## 11. Recommended Development Agent Task

1. New module `qla_core/quikspec_vanish.py` — surgical VANISH overlay from resolved PPOLC; emit `T`/`F` only.  
2. Hook in both `app.py` copies on quikspec write; do not change `apply_quikspec_resrvcat` internals.  
3. Do **not** change: RESSTATE, RESRVCAT, VANISHDT, QuikIsrr, QuikPlan, premiums.  
4. Version bump: **v58.99** both `app.py` files.  
5. Validator `QLA_Migration/_validate_issue145_vanish.py` (fail-closed). Register in `SMOKE_JOBS` at **Close**, not before.  
6. On validator PASS, publish `Output/Test_Validation/quikspec.csv` only.

---

## Appendix

- Simulation: read-only join 2026-08-19 (636 VB in current Output; 0 misses)  
- Related: `Issue_145_Discovery_Notes.md`, `Issue_145_Planning_Report.md`
