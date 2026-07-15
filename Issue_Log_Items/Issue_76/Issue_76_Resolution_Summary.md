# Issue #76 — Resolution Summary

**Issue:** #76 — ETI/RPU phase-1 pay-up + duration for Policy Display cash values  
**Framework stage:** Closure Agent  
**Final status:** **Closed**  
**Release:** **v57.93** (`app.py` + `QLA_Migration/app.py`)  
**Closed date:** 2026-07-15  
**Owner:** Conversion

---

## Resolution (issue log — paste-ready)

**Resolution:** For exercised ETI/RPU policies (`quikmstr.MSTATUS` 44/45), phase-1 `quikridr.MPAYUP` now equals `quikmstr.MPAIDTO` and `MLASTANN` equals run-year minus pay-up year, correcting Policy Display cash-value anniversary dates (e.g. `010407670C`: pay-up `20121001`, duration `14` → CV dates ~2026 instead of 2080). Fleet: 400 policies adjusted; #60 PUA and non-ETI/RPU rows unchanged.

> Copy the line above into tracking sheets and client readouts. Long-form detail follows.

---

## Problem Statement

On Policy Display for exercised ETI/RPU policies (e.g. **`010407670C`**, Status RPU), Cash Values showed far-future dates (**02/01/2080**) because phase-1 **`MPAYUP`** remained at contractual LifePRO pay-up age (**20270201**) while **`MLASTANN`** used issue-year duration (**53**). QLAdmin dated CV lines from pay-up + duration (**2027 + 53 = 2080**).

Manual UAT proved the fix: set phase-1 Payup = Paid To (**10/01/2012**) and duration **`t = 14`** (2026 − 2012) → CV dates moved to **2026/2027**.

---

## Root Cause

**Category:** Post-map business rule gap (ETI/RPU-specific)

Conversion mapped `PAY_UP_DATE → MPAYUP` and `_apply_quikridr_mlastann` from **issue date** for all policies. Exercised ETI/RPU policies require pay-up anchored to **paid-to** and duration from **current year − pay-up year**, not contractual pay-up age + issue-based duration.

---

## Resolution (long-form)

Added surgical post-map hook `_apply_issue76_eti_rpu_phase1_payup_mlastann` after `_apply_quikridr_mlastann` on phase-1 `quikridr` rows when master status ∈ {44, 45}. Uses `quikmstr.csv` status/paid-to cache (quikmstr must convert before quikridr in rebatch). Preserves Issue **#60** PUA inheritance (phase > 1) and Issue **#72** NFO on `quikmstr`.

### Files changed

| File | Change |
|------|--------|
| `app.py` | `APP_VERSION` v57.93; `_apply_issue76_eti_rpu_phase1_payup_mlastann`; `_qm_paidto_cache`; call + log |
| `QLA_Migration/app.py` | Mirror |
| `tools/validators/validate_issue76_eti_rpu_payup.py` | Issue validator (new) |
| `Issue_Log_Items/Issue_76/scripts/rebatch_issue76_quikridr.py` | Scoped rebatch (new) |
| `Issue_Log_Items/Issue_76/scripts/regression_issue76.py` | Regression checks (new) |
| `QLA_Migration/Output/quikridr.csv` | Re-emitted (6,934 rows) |
| `QLA_Migration/Output/Test_Validation/quikridr.csv` | UAT publish |

### Engine changes

| Behavior | Before | After |
|----------|--------|-------|
| Phase-1 `MPAYUP` @44/45 | `PAY_UP_DATE` (contractual) | **`MPAIDTO`** |
| Phase-1 `MLASTANN` @44/45 | valuation − issue year | **run-year − pay-up year** |
| Phase > 1 / PUA (#60) | Unchanged | Unchanged |
| Non-44/45 policies | Unchanged | Unchanged |

### Rulebook changes

None.

---

## Evidence

| Artifact | Path |
|----------|------|
| Intake | `Issue_Log_Items/Issue_76/Issue_76_Intake_Summary.md` |
| Planning | `Issue_Log_Items/Issue_76/Issue_76_Planning_Report.md` |
| Scope decisions | `Issue_Log_Items/Issue_76/Issue_76_Scope_Decisions.md` |
| Dependency Gate | `Issue_Log_Items/Issue_76/Issue_76_Dependency_Gate.md` |
| Risk review | `Issue_Log_Items/Issue_76/Issue_76_Risk_Review_Report.md` |
| Implementation | `Issue_Log_Items/Issue_76/Issue_76_Implementation_Notes.md` |
| Validation report | **PASS** — `Issue_Log_Items/Issue_76/Issue_76_Validation_Report.md` |
| Regression report | **PASS** — `Issue_Log_Items/Issue_76/Issue_76_Regression_Report.md` |
| Validation script | `tools/validators/validate_issue76_eti_rpu_payup.py` |

---

## Trace Policy Confirmation

| Policy | Phase | Field | Before | After | Match |
|--------|------:|-------|--------|-------|-------|
| **010407670C** | 1 | MPAYUP | 20270201 | **20121001** | Yes |
| **010407670C** | 1 | MLASTANN | 53 | **14** | Yes |
| **010407670C** | 2 | MPAYUP | 19720201 | 19720201 (#60 PUA) | Yes |
| 010374099C | 1 | MPAYUP | 20730921 | **20090921** | Yes |
| 010367131C | 1 | MPAYUP | 20520801 | 20520801 (active control) | Yes |

---

## Explicitly Not Changed

- `quikmstr` mapping logic (#76 hook is `quikridr` only)
- Issue **#60** PUA `MPAYUP=MEFFDATE` on later phases
- Issue **#72** `MNFOPT` 44→2 / 45→3
- `MEFFDATE`, `MAGE`, `MEXPRY`, `MUNIT`, `MPREM` (#26)
- `MCV0/1/2` amounts (rebuild CV remains UAT step)
- Rates / rulebooks / BAND
- Row counts on all core tables

---

## Fleet Impact

| Metric | Count |
|--------|------:|
| Phase-1 candidates @44/45 | 400 |
| `MPAYUP` changes | 223 |
| `MLASTANN` changes | 400 |
| Non-candidate false overrides | 0 |
| PUA regressions | 0 |

---

## Client UAT

1. Reload **`QLA_Migration/Output/Test_Validation/quikridr.csv`** into QLAdmin  
2. Run **Data Admin** on sample **`010407670C`**  
3. Run **Rebuild CV**  
4. Confirm Policy Display cash-value dates near **10/01/2026–2027**, not **2080**

---

## Rollback

1. Revert `app.py` and `QLA_Migration/app.py` to **v57.92** (remove `_apply_issue76_*` hook and `_qm_paidto_cache`)  
2. Rebatch `quikridr` (and `quikmstr` first for cache)  
3. Remove `Test_Validation/quikridr.csv` publish if rolled back

---

## Framework Gates

| Gate | Result |
|------|--------|
| G0 Intake | PASS |
| G1 Planning | PASS |
| G2 Dependency | PASS |
| G3 Risk | Conditional Go |
| G4 Development | PASS (v57.93) |
| G5 Validation | PASS |
| G6 Regression | PASS |
| **Closure** | **CLOSED** |

---

## Related Issues

| Issue | Relationship |
|-------|----------------|
| **#72** | NFO 44→2 / 45→3 on `quikmstr` — complementary; reload both tables for full UAT |
| **#60** | PUA pay-up on later phases — must not regress |
| **#73** | CLOSED MISSCNTRY — separate issue (ID collision avoided at intake) |

---

## Paste-ready tracking line

> **Resolution:** For exercised ETI/RPU policies (MSTATUS 44/45), phase-1 quikridr MPAYUP = MPAIDTO and MLASTANN = run-year − pay-up year (v57.93). Sample 010407670C: MPAYUP 20121001, MLASTANN 14. UAT: Test_Validation/quikridr.csv + Rebuild CV.
