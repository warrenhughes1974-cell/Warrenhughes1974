# Issue #72 — Risk Review Report

**Issue:** #72 — NFO must match ETI/RPU status (`MSTATUS` 44→`MNFOPT` 2; 45→3)  
**Framework stage:** Risk Agent  
**Status:** **Go → Ready for Development** (pending explicit user approval)  
**Generated:** 2026-07-15  
**Model:** Cursor Grok 4.5 (locked)  
**Status note:** Risk analysis only — no production code changes.  
**Evidence:** `evidence/issue72_risk_mnfopt_deltas.csv` · `scripts/risk_review_issue72_mnfopt.py`

---

## Go / No-Go Recommendation

**GO** — Blast radius is narrow, fully quantified, and aligned with Robert’s rule + SD-72-*.

| Factor | Assessment |
|--------|------------|
| Scope | Only `quikmstr.MNFOPT` when final `MSTATUS` ∈ {44, 45} |
| Impact | **277** MNFOPT changes; **0** changes outside 44/45 |
| #57 conflict | Resolved by design: election kept for non-44/45; status wins for exercised ETI/RPU |
| #25 / #26 | Untouched |
| Fallback | Not needed — rule is binary and client-authored |

Development may proceed after user says **Approved for Development** and switches to **Composer 2.5**.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| `MSTATUS` | PUT/contract/#49 path | Unchanged | **No** |
| `MNFOPT` when status ∉ {44,45} | #57 PPBENTYP + `NF_*` | Unchanged | **No** |
| `MNFOPT` when status = **44** | Mix 0/1/2 | Force **2** | **Yes** (98 rows) |
| `MNFOPT` when status = **45** | Mix 0/1/2/3 | Force **3** | **Yes** (179 rows) |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| MPOLICY padding (#25) | **No** |
| quikridr.MPREM (#26) | **No** |
| MSTATUS / MPHSTAT | **No** |
| MDIVOPT | **No** |
| `Master_Value_Translation` NF_* / PUT_* | **No** |
| Rulebook PUT→MNFOPT restore | **No** (must not) |
| Rates / MCV / RRULE | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `app.py` / `QLA_Migration/app.py` MNFOPT enrich + `NF_` translate | Current election path (#57) — keep |
| Same file MSTATUS interceptor + #49 override | Produces final status — NFO force must run **after** |
| `Sync_Rulebook_quikmstr.csv` `NFO_OPT→MNFOPT` | Default 0 only — no change |
| Issue #57 artifacts | Election semantics for non-44/45 |

---

## 4. Population Analysis (simulated on current Output)

| Metric | Count |
|--------|------:|
| quikmstr rows | 5,083 |
| MSTATUS=44 | 206 |
| MSTATUS=45 | 194 |
| **MNFOPT deltas (total)** | **277** |
| 44: MNFOPT → 2 | 98 |
| 45: MNFOPT → 3 | 179 |
| Already correct (44+2 / 45+3) | 123 |
| Non-44/45 MNFOPT deltas | **0** |

### Before → after transitions (delta rows only)

| Status | MNFOPT before | After | Rows |
|--------|---------------|-------|-----:|
| 44 | 0 | 2 | 86 |
| 44 | 1 | 2 | 12 |
| 45 | 0 | 3 | 80 |
| 45 | 1 | 3 | 55 |
| 45 | 2 | 3 | 44 |

After fix: **100%** of status-44 have MNFOPT=2; **100%** of status-45 have MNFOPT=3.

---

## 5. Fallback Recommendation

| Option | Assessment |
|--------|------------|
| **A. Force MNFOPT from final MSTATUS 44/45 (recommended)** | Matches Robert; quantified; preserves #57 elsewhere |
| B. Restore fleet PUT→MNFOPT in rulebook | **Reject** — undoes #57 for non-exercised policies |
| C. Manual client edit of 277 policies | Reject — not conversion-grade |
| D. Do nothing | Reject — fails Robert validation / YE display |

**Recommended:** Option A.

---

## 6. Trace Policies

| Policy | MSTATUS | MNFOPT before | After | Pass criteria |
|--------|---------|---------------|-------|---------------|
| **010407670C** | 45 | 2 | **3** | Robert / YE sample |
| 010165095C | 45 | 2 | **3** | Peer |
| 010374099C | 44 | 1 | **2** | Peer |
| 010149295C | 44 | 2 | 2 | No-op correct |
| 010403916C | 45 | 3 | 3 | No-op correct |
| 010367131C | 22 | 2 | **2** | #57 Eric control — unchanged |
| 010148272C | 22 | 2 | **2** | #57 control |
| 011221309C | 53 | 1 | **1** | #57 APL control |

---

## 7. Top Changes

Not a numeric magnitude field — categorical overwrite only.

Largest semantic flip class: **45 with MNFOPT=2 (ETI election while on RPU)** → **3** (**44** policies), including `010407670C`.

---

## 8. Regression Surfaces

| Surface | Risk | Check |
|---------|------|-------|
| #57 election on active/other statuses | Low | Controls above unchanged |
| #49 MSTATUS override | Med | Force uses **final** status only (post-#49) |
| Accidental rulebook PUT→MNFOPT | High | Explicitly forbidden |
| MDIVOPT / fees / rates | None | Out of scope |
| CV dates / blank MCV | Unchanged | Still needs Data Admin + rebuild CV after UAT reload |
| #25 / #26 | None | No MPOLICY/MPREM edits |

---

## 9. Recommended Development Agent Task (exact)

**Switch to Composer 2.5.** Then:

1. Surgical post-map on completed `quikmstr` `row_data` (after #13/#59/`ST_`/#49; before `output.append`):  
   - if `MSTATUS == "44"` → `MNFOPT = "2"`  
   - if `MSTATUS == "45"` → `MNFOPT = "3"`  
2. Mirror in **both** `app.py` and `QLA_Migration/app.py`; bump `APP_VERSION` both.  
3. Log forced count (`Issue #72: forced MNFOPT…`).  
4. Do **not** edit `Master_Value_Translation.csv` NF_* keys; do **not** re-add PUT→MNFOPT to rulebook.  
5. Re-batch; publish `Output/quikmstr.csv` + `Output/Test_Validation/quikmstr.csv` only (modified table).  
6. Add `tools/validators/validate_issue72_mnfopt_status.py` asserting:  
   - every 44 → 2; every 45 → 3  
   - `010407670C` = 3  
   - `010367131C` still 2 @ status 22  
   - delta count ≈ 277 vs pre-fix baseline (or exact from evidence CSV)  

---

## 10. Validation / Regression Checklist

- [ ] All `MSTATUS=44` → `MNFOPT=2` (206)  
- [ ] All `MSTATUS=45` → `MNFOPT=3` (194)  
- [ ] `010407670C` MNFOPT=3  
- [ ] #57 controls unchanged (`010367131C`, `010148272C`, `011221309C`)  
- [ ] Non-44/45 MNFOPT distribution unchanged vs pre-fix (4,683 rows)  
- [ ] MDIVOPT / MSTATUS / MPOLICY unchanged on delta set  
- [ ] #25 / #26 smoke PASS  
- [ ] Only `quikmstr` published to `Test_Validation/` for this issue  

---

## Gate Criteria (G3)

- [x] Go issued  
- [x] Impact quantified (277 deltas; evidence CSV)  
- [x] Unrelated fields marked untouched  
- [x] #25 / #26 preservation confirmed  
- [x] No code in this stage  
- [ ] User acknowledges Go and approves Development (next)
