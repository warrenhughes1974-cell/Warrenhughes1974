# Issue #160 — Risk Review Report

**Issue:** #160 — PUA phase stays Expired (56) instead of Surrendered (55) when base surrenders
**Framework stage:** Risk Agent (G3)
**Status:** **CONDITIONAL GO — Ready for Development approval, contingent on Warren's SD-60-12 carve-out sign-off**
**Fallback simulated:** N/A — additive branch mirroring existing #108D pattern; no new business rule invented
**Generated:** 2026-09-07
**Agent/script:** read-only counts on current `QLA_Migration/Output/quikridr.csv`

**Status note:** Risk analysis only — no production code changes unless later approved.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — add a new `elif base_status == 55: row_data["MPHSTAT"] = "55"` branch inside `_apply_pua_rider_inheritance` (both `app.py` copies) and re-emit `quikridr`. Blast radius is exactly **71 rows** (PUA `MPHSTAT` 56→55); base status, dates, age, MPAR, and every other field on those rows are untouched. This is the smallest possible surgical change — same function, same pattern already proven safe by #108D.

**The only reason this is not an unconditional GO:** it directly narrows the locked **SD-60-12** decision ("terminated-base PUA keep current status"). That decision was made deliberately at Issue #60's Risk stage. Per the workspace's Closed/locked-row conflict rule, Development must not start until **Warren explicitly approves the carve-out** (same precedent as how #108D itself carved 44/45 out of the "<50" window without repealing SD-60-12 wholesale).

**Conditions (surgical, not blockers once approved):**

1. New branch only fires when `base_status == 55`. Does not touch `< 50` (→41, SD-60-3) or `44/45` (→54, #108D).
2. Do not generalize to base 53 (Terminated/Death, 163 rows), 57 (Matured, 4 rows), or 50 (Suspended/#133, 1 row) in this pass — separate Warren decision.
3. Do not change PUA MPAR, MEFFDATE, MAGE, MPAYUP, MLASTANN, or MPLAN — untouched by this branch.
4. Do not change base phase 1 status logic, non-PUA rider logic, or any rulebook.
5. Bump **both** `APP_VERSION` files (AGENTS.md requirement).

---

## 1. Current vs Proposed Mapping

| Base MPHSTAT | Current PUA MPHSTAT | Proposed PUA MPHSTAT | Change? |
|---|---|---|---|
| < 50 (active) | 41 (SD-60-3) | 41 | **No** |
| 44 / 45 (ETI/RPU) | 54 (#108D) | 54 | **No** |
| **55 (Surrendered)** | **56 (own PPBEN status)** | **55** | **Yes** |
| 53 (Terminated/Death) | 56 (own PPBEN status) | 56 (unchanged) | **No — out of scope this pass** |
| 57 (Matured) | 56 (own PPBEN status) | 56 (unchanged) | **No — out of scope this pass** |
| 50 (Suspended) | 22 (own PPBEN status, #133) | 22 (unchanged) | **No — separate issue #133** |

---

## 2. Fields Untouched

| Target | Source | Touched? |
|---|---|---|
| quikridr.MPAR (PUA) | 0 always (#119) | **No** |
| quikridr.MEFFDATE/MAGE/MPAYUP/MLASTANN (PUA) | Base inheritance (#60 SD-60-4/5/6) | **No** |
| quikridr.MPLAN (PUA synthetic) | `base[:4]+"PA"` | **No** |
| Base phase 1 MPHSTAT | Terminal sync (already 55) | **No** |
| Non-PUA riders (ADB, WP, term) | SD-60-11 gate | **No** |
| Rate tables, PVO, premiums, MPOLICY | N/A to this fix | **No** |

---

## 3. Repo References

| Location | Role |
|---|---|
| `app.py` + `QLA_Migration/app.py` `_apply_pua_rider_inheritance` (~3608–3644) | Insertion point for new branch |
| `app.py` `_cache_quikridr_base_phase` (~3595–3606) | Confirms cache carries terminal MPHSTAT (55) correctly by the time PUA branch runs |
| `app.py` PUA deferral (~9758–9765, 9827–9838) | Confirms processing order: base phase-1 cached (with terminal sync applied) **before** any PUA row is resolved |
| `Issue_Log_Items/Issue_60/Issue_60_Scope_Decisions.md` (SD-60-12) | Locked decision this change carves out an exception to |
| `Issue_Log_Items/Issue_133/Issue_133_Discovery_Notes_Policy_Status.md` | Same defect class, base=50 variant — not bundled into this fix |

---

## 4. Population Analysis

| Metric | Count |
|---|---:|
| Total quikridr rows | 6,956 |
| Total PUA rows (any base status) | 494 |
| Base=55 policies | 692 |
| Base=55 policies with a PUA phase | 71 |
| **Rows that would change** | **71** (100% of base=55 PUA rows; currently 0 already correct) |
| Rows unchanged | 6,885 |

### Breakdown by PUA plan code (all 71 affected)

| PUA MPLAN | Rows |
|---|---:|
| 1708PA | 58 |
| 1960PA | 11 |
| 1970PA | 1 |
| 1705PA | 1 |

### Related terminal-base gap, NOT in this pass (context only)

| Base MPHSTAT | Meaning | PUA rows currently wrong | This issue? |
|---|---|---:|---|
| 53 | Terminated/Death | 163 | No |
| 57 | Matured | 4 | No |
| 50 | Suspended (#133) | 1 | No |

---

## 5. Fallback Recommendation (if applicable)

| Option | Rows changed | Assessment |
|---|---:|---|
| **A. Add `base_status == 55` branch to `_apply_pua_rider_inheritance`** | 71 | **Recommended** — mirrors proven #108D pattern, smallest surgical change |
| B. Generalize to all terminal codes ≥50 in one pass | 239 (71+163+4+1) | Reject for now — exceeds client's stated scope (surrenders only); would need separate Warren sign-off and would also absorb #133 |
| C. Change the rulebook `STATUS_CODE→MPHSTAT` mapping instead | Fleet-wide, all phases | Reject — would affect non-PUA riders and base phases too; far too broad |
| D. Post-process Output CSV only, no `app.py` change | 71 | Reject — next full batch regresses again (same lesson as #159) |

**Recommended fallback:** none needed. Kill switch is reverting the one added `elif` branch.

---

## 6. Trace Policies

| Policy | Base MPHSTAT | Before (PUA) | Proposed (PUA) | Pass? |
|---|---|---|---|---|
| 9010360289C | 55 | 56 | 55 | Yes |
| 9010367705C | 55 | 56 | 55 | Yes |
| 9010376522C | 55 | 56 | 55 | Yes |
| 9010379405C | 55 | 56 | 55 | Yes |
| 9010391228C | 55 | 56 | 55 | Yes |
| (any base<50 sample) | <50 | 41 | 41 | Yes — must not flip |
| (any base 44/45 sample) | 44/45 | 54 | 54 | Yes — must not flip |

---

## 7. Top Largest Changes

Not a dollar field. Count concentration: `1708PA` 58 of 71 rows (82%), `1960PA` 11 rows, `1970PA`/`1705PA` 1 row each.

---

## 8. Material Calculation Impact

Status-only change — no premium, cash value, or reserve field is touched by this fix. Downstream QLAdmin behavior (e.g., whether Surrendered vs Expired coverages appear differently in valuation or reporting) is a QLAdmin-side consequence of the status code, not something this conversion fix calculates directly.

---

## 9. Prior Fix Preservation

| Check | Result |
|---|---|
| Issue #60 SD-60-3 (PUA=41 when base active) | Untouched |
| Issue #60 SD-60-4/5/6/7 (date/age inheritance) | Untouched |
| Issue #60 SD-60-11 (PUA-only gate) | Untouched — new branch stays inside the same gated function |
| Issue #60 SD-60-12 | **Narrowed** (base=55 carved out) — requires Warren approval |
| Issue #108D (base 44/45 → 54) | Untouched — new branch placed after it, does not intercept |
| Issue #119 (PUA MPAR=0) | Untouched |
| Issue #133 (base=50 discovery) | Not bundled — remains open/separate |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] All 71 current base=55/PUA=56 policies now show PUA MPHSTAT=55
- [ ] Zero remaining base=55 policies with PUA still at 56
- [ ] Base<50 PUA population still forced to 41 (count unchanged)
- [ ] Base 44/45 PUA population still forced to 54 (count unchanged, #108D)
- [ ] Base 53/57/50 PUA populations **unchanged** (163 / 4 / 1 respectively) — confirms no scope creep
- [ ] quikridr row count still 6,956; MPAR/MEFFDATE/MAGE/MPLAN unchanged on a sample join
- [ ] New #160 validator PASS
- [ ] Publish Test_Validation/quikridr.csv

---

## 11. Recommended Development Agent Task

1. Both `app.py` files, inside `_apply_pua_rider_inheritance`, after the existing `elif base_status < 50: row_data["MPHSTAT"] = "41"` branch, add:
   ```python
   elif base_status == 55:
       # Issue #160: base Surrendered — PUA follows base to Surrendered.
       row_data["MPHSTAT"] = "55"
   ```
2. Do NOT change: the 44/45→54 branch, the <50→41 branch, any rulebook, any other rider logic, base 53/57/50 handling.
3. Version bump: both `app.py` files (AGENTS.md requirement).
4. Re-emit `quikridr` (full batch preferred).
5. Add `tools/validators/validate_issue160_pua_surrender_status.py` (fail-closed). Register in `SMOKE_JOBS` only at Closure.
6. Publish `Output/Test_Validation/quikridr.csv`.

**Gate before starting: Warren must approve the SD-60-12 carve-out in writing.**

---

## Appendix

- Before-state: current Output `quikridr.csv`
- Conflict reference: `Issue_Log_Items/Issue_60/Issue_60_Scope_Decisions.md` SD-60-12
- Related, not bundled: `Issue_Log_Items/Issue_133/Issue_133_Discovery_Notes_Policy_Status.md`
