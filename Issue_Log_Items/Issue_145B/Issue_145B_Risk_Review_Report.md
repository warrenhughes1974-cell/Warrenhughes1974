# Issue #145B — Risk Review Report

**Issue:** #145B — Vanish 0561s Out of ISRR  
**Framework stage:** Risk Agent  
**Status:** **GO — Ready for Development** (after user approval)  
**Fallback simulated:** VB-only exclude vs “all 0561s” (rejected) vs QuikIsrr-only (rejected)  
**Generated:** 2026-08-23  
**Agent/script:** Cursor Grok 4.5 · read-only `quikspec.VANISH` join to current Output

**Status note:** Risk analysis only — no production code changes unless later approved.

---

## Go / No-Go Recommendation

**GO** — Exclude vanishing (VB) policies from the #34 0561 emit and strip the already-written rows from current Output. On the 6/30 package that removes **3,452** QuikIsrr rows ($1,157,482.66) and the matching **3,452** companions on each of `quikclms` / `quikclmp` / `quikbenh` type 8. Leftover QuikIsrr is **205** rows / **50** policies ($75,119.87), including #146.

**Conditions:**

1. VB only. Do **not** strip #146 (9010761639C / 9010760840C).  
2. Do **not** delete LifePRO PACTG.  
3. Do **not** rewrite `quikridr.MUNIT` — units are already LifePRO original.  
4. Do **not** change `quikspec.VANISH` (#145).  
5. Strip companions with QuikIsrr (same event). Keep `quikbenh` types 10/11/12 (#54).  
6. Restate `quikisrr_pr7_emit.py` `EXPECTED` to the leftover book. Do not keep 3657.  
7. Do not blindly re-run PR-7 emit against already-loaded Output (clms/clmp **append**).

**Closed #34 notice:** this is a Warren-authorized **exclusion** on that emit, not a reopen of the 0561 source rule. Non-VB 0561s still load.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| QuikIsrr (VB 0561) | Emitted (#34) | Not emitted / stripped | **Yes** |
| quikclms PS- (VB) | Appended by PR-7 | Not emitted / stripped | **Yes** |
| quikclmp phase 0 (VB) | Appended by PR-7 | Not emitted / stripped | **Yes** |
| quikbenh type 8 (VB) | Replaced by PR-7 | Not emitted / stripped | **Yes** |
| Same four tables, non-VB | Emitted | Unchanged | **No** |
| quikspec.VANISH | T on 636 | Unchanged | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| quikridr.MPREM | #26 / #88 / #137 | **No** |
| quikmstr.MMODPREM | PPOLC.MODE_PREMIUM | **No** |
| quikridr.MUNIT | LifePRO / #143 | **No** |
| MPOLICY padding | #25 / #2 | **No** |
| quikspec.VANISH / RESSTATE / RESRVCAT | #145 / #132 / #141 | **No** |
| quikbenh 10/11/12 | #54 | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `qla_core/quikisrr_loader.py` | Add VB skip after #34 eligibility |
| `Issue_Log_Items/Issue_34/tools/quikisrr_pr7_emit.py` | Restate EXPECTED; do not append-duplicate |
| `app.py` `_execute_batch_quikisrr_finale` | Existing call site — bump version only |
| `qla_core/quikspec_vanish.py` | Reuse VB list |
| `Issue_Log_Items/Issue_145B/evidence/issue145b_risk_impact_summary.json` | This count |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| QuikIsrr rows now | 3,657 |
| Rows that would be removed | 3,452 |
| Rows unchanged | 205 |
| VB policies with no 0561 | 49 (no Output change) |
| Companion rows removed (each table) | 3,452 |

### Breakdown

| Dimension | rows | would_change |
|-----------|-----:|-------------:|
| QuikIsrr VANISH=T | 3,452 | 3,452 |
| QuikIsrr VANISH=F | 205 | 0 |
| quikclms PS- VANISH=T | 3,452 | 3,452 |
| quikclms PS- VANISH=F | 205 | 0 |
| quikbenh type 8 VANISH=T | 3,452 | 3,452 |
| quikbenh type 8 VANISH=F | 205 | 0 |

---

## 5. Fallback Recommendation

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| A. VB exclude on all four #34 tables | 3,452 × 4 | **Recommended** — matches “completely” and the 1:1 companions |
| B. QuikIsrr only | 3,452 | Reject — Claims / UL still show fake surrenders |
| C. All 0561s (VB + #146) | 3,657 | Reject — Warren 08/23: vanishing only |
| D. Amount = today’s premium only | ~3,324 | Reject — Warren: all 0561s on VB |

**Recommended fallback:** Option A. If a later batch uses a different PPOLC, VB count follows that extract, not a frozen 636.

---

## 6. Trace Policies

| Policy | Before QuikIsrr | Proposed | MUNIT now | Pass? |
|--------|----------------:|----------|-----------|-------|
| 9010815236C | 8 / $1,402.56 | 0 | 25.00000 | Yes |
| 9011050114C | 1 / $136.00 | 0 | 25.00000 | Yes |
| 9011069610C | 1 / $406.00 | 0 | 50.00000 | Yes |
| 9010761639C | 1 / $271.00 | 1 / $271.00 | 25.00000 | Yes — keep |
| 9010760840C | 2 / $716.40 | 2 / $716.40 | 35.00000 | Yes — keep |

---

## 7. Top Changes (by 0561 dollars removed)

Anniversary unit recovery on the golds (formula already proven 08/20):

| Policy | Σ 0561 | Live QLA if history stays | After exclude |
|--------|-------:|--------------------------:|--------------:|
| 9010815236C | 1,402.56 | 23.597 | 25 |
| 9011069610C | 406.00 | 49.594 | 50 |
| 9011050114C | 136.00 | 24.864 | 25 |

Largest single-policy removals are the long anniversary 0561 strings on the vanish book (example gold 9010815236C, eight years). Fleet dollars removed: **$1,157,482.66**.

---

## 8. Material Calculation Impact

**Intentional.** We are not changing converted units. We are removing history that QLAdmin treats as a face cut. Residual #146 policies will still drop units after anniversary — that is out of scope.

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | Preserved — no key rewrite |
| Issue #26 MPREM / MMODPREM | Preserved — not in this emit |
| Issue #34 0561 source (non-VB) | Preserved — leftover 205 stay |
| Issue #54 quikbenh loans | Preserved — type 8 VB only |
| Issue #145 VANISH | Preserved — 636 T stays |
| Issue #143 RPU units | Preserved — `MUNIT` not rewritten |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] 9010815236C / 9011050114C / 9011069610C have **0** QuikIsrr rows  
- [ ] Same three have **0** PS- clms / phase-0 clmp / type-8 benh  
- [ ] 9010761639C still 1 QuikIsrr ($271); 9010760840C still 2 ($716.40)  
- [ ] QuikIsrr leftover = 205 rows / 50 policies on 6/30  
- [ ] `quikspec.VANISH` still T=636  
- [ ] Gold `quikridr.MUNIT` unchanged (25 / 25 / 50)  
- [ ] `quikbenh` types 10/11/12 row count unchanged  
- [ ] #25 / #26 sample keys unchanged  

---

## 11. Recommended Development Agent Task

1. Skip VB events in `qla_core/quikisrr_loader.py` using `load_ppolc_billing_reason`.  
2. Restate `EXPECTED` in `quikisrr_pr7_emit.py` to 205 / 50 / 75119.87 for the 6/30 book (or compute from leftover, not a stale 3657).  
3. Strip current Output VB rows on QuikIsrr + PS- clms + phase-0 clmp + type-8 benh.  
4. Bump **both** `APP_VERSION` to **v59.01**.  
5. Add fail-closed validator `tools/validators/validate_issue145b_vb_isrr_exclude.py`.  
6. Do **not** change `quikridr`, `quikmstr`, `quikspec`, PACTG, or #146 rows.

---

## Appendix

- Impact JSON: `Issue_Log_Items/Issue_145B/evidence/issue145b_risk_impact_summary.json`  
- Prior proof: `Issue_145B_Analysis_Report.md`  
