# Issue #60 — Risk Review Report

**Issue:** #60 — PUA phase fields + base plan interest (Chris plan) — **Track A**  
**Framework stage:** Risk Agent (G3)  
**Status:** **CONDITIONAL GO** — Ready for Development (await explicit Stage 5 approval)  
**Fallback simulated:** PUA-only gate; `MPHSTAT=41` only when base phase status &lt; 50  
**Generated:** 2026-07-14  
**Baseline engine:** `APP_VERSION` **v57.84**  
**Evidence:** `evidence/issue60_risk_summary.csv`, `evidence/issue60_risk_pua_deltas_active_status.csv`  
**Simulation script:** `QLA_Migration/_risk_review_issue60_pua_phase.py`  
**Code changes in this stage:** None (read-only)  
**Model:** Cursor Grok 4.5 (locked Risk)  
**User constraint (this turn):** **Do not change dates or ages on other (non-PUA) riders**

---

## Go / No-Go Recommendation

**CONDITIONAL GO (Track A)**

Expand existing `_apply_pua_rider_inheritance` only. Hard gate: changes apply **solely** to rows that already pass `_is_paid_up_addition_product` (same gate used today for synthetic `*PA` MPLAN). **Non-PUA riders and phase-1 base are untouched** for `MEFFDATE` / `MAGE` / `MPAYUP` / `MLASTANN` / `MPHSTAT`.

**Conditions:**

1. **PUA-only** — no date/age inheritance on ADB, WP, term riders, etc. (**SD-60-11**, user-locked).  
2. **`MPHSTAT=41` only when base `MPHSTAT` &lt; 50** — do not force Paid Up on terminated policies (239 PUA rows keep current status).  
3. **Track B (interest) out of scope** for this Development — still blocked pending Chris rates.  
4. Explicit user **Approved for Development** + switch to **Composer 2.5**.

---

## 1. Current vs Proposed Mapping

| Field | Current (PUA rows) | Proposed (PUA only) | Change? |
|-------|--------------------|---------------------|---------|
| `MPLAN` | `base[:4]+"PA"` | unchanged | No |
| `MEXPRY` | copy base | unchanged | No |
| `MPAYUP` | copy **base MPAYUP** | set to **inherited MEFFDATE** | **Yes** |
| `MEFFDATE` | LifePRO PUA issue date | **base MEFFDATE** | **Yes** |
| `MAGE` | LifePRO PUA issue age | **base MAGE** | **Yes** |
| `MLASTANN` | from PUA MEFFDATE | **base MLASTANN** (or recompute after MEFFDATE) | **Yes** |
| `MPHSTAT` | usually 22 or 56 | **41** if base &lt; 50; else leave | **Yes** (255 of 494) |

### Hard non-targets (user lock)

| Population | Rows | Date/age action |
|------------|-----:|-----------------|
| Phase-1 base | 5,083 | **No change** |
| Other non-PUA later phases (ADB, etc.) | **1,357** | **No change** — includes **201** with date/age already ≠ base |
| Policies with both PUA + other riders | **27** | Change **PUA row only** |

Example mixed policy **`010150910C`**:

| Ph | MPLAN | Current eff / age | After Track A |
|----|-------|-------------------|---------------|
| 1 | 221END | 19610901 / 21 | **unchanged** |
| 2 | **920ADB** | 19610901 / 21 | **unchanged** (other rider) |
| 3 | 221EPA (PUA) | 20070901 / 67 | → base eff/age; status left 56 (base terminated 53) |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| MPOLICY padding (#25) | **No** |
| `quikridr.MPREM` / MMODPREM (#26) | **No** |
| Non-PUA `MEFFDATE` / `MAGE` / `MPAYUP` / `MLASTANN` / `MPHSTAT` | **No** |
| Phase-1 base dates/ages/status | **No** |
| `quikmstr.MSTATUS` (#59) | **No** |
| `MUNIT` / face (#21K) | **No** |
| `quikplan` / QuikCvs / add `1960PA` (#56) | **No** |
| Track B NFOINT / QuikPlTv | **No** (this Dev) |
| Sync rulebooks | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `app.py` / `QLA_Migration/app.py` `_is_paid_up_addition_product` | **Gate** — PUA detection (do not widen) |
| `_cache_quikridr_base_phase` | Expand cache: +`MEFFDATE`, `MAGE`, `MLASTANN` |
| `_apply_pua_rider_inheritance` | **Only edit site** for Track A field writes |
| `_apply_quikridr_mlastann` | Runs after inheritance — ensure MEFFDATE already set, or copy base MLASTANN in inheritance |
| `_resolve_quikridr_mphdob` | May re-run after MAGE/MEFFDATE; PUA only (already in PUA pending loop) |
| Rate emit / QuikPlCv | Track B only — leave alone |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| Total `quikridr` rows | 6,934 |
| PUA rows (synthetic `*PA`) | **494** |
| PUA rows with any Track A field change | **494** (100%) |
| Other non-PUA rider rows (**must not change**) | **1,357** |
| Other riders with date/age ≠ base (**must stay**) | **201** |
| Policies with PUA + other riders | **27** |

### Field-level hits (PUA only, recommended status rule)

| Field | Rows changing |
|-------|-------------:|
| `MEFFDATE` | 494 |
| `MAGE` | 494 |
| `MLASTANN` | 494 |
| `MPAYUP` | 494 |
| `MPHSTAT` | **255** |

### Status transitions (recommended: 41 only if base &lt; 50)

| Before → After | Count |
|----------------|------:|
| 22 → 41 | 227 |
| 56 → 41 | 28 (PUA was 56 but base still active) |
| Unchanged status (terminated base) | **239** |

### Rejected alternate: force all PUA → 41

Would add **266** extra `56→41` on terminated bases — **reject** unless Chris overrides OBQ-4.

---

## 5. Fallback Recommendation

| Option | Rows date/age | Status→41 | Assessment |
|--------|--------------:|----------:|------------|
| **A — PUA-only + status if base active** | 494 | 255 | **Recommended** |
| B — PUA-only + all PUA status 41 | 494 | 494 | Reject (resurrects terminated) |
| C — All later phases inherit base dates | 494 + 1,357 | — | **Reject** — violates user constraint |
| D — Sample policy only (`010310404C`) | 1 | 1 | Reject — Chris rule is structural |

**Recommended:** Option **A**.

---

## 6. Trace Policies

| Policy | PUA before (stat/eff/age/mlast/payup) | Proposed | Other riders |
|--------|----------------------------------------|----------|--------------|
| **010310404C** | 22 / 20110128 / 68 / 15 / 20460128 | **41** / **19690128** / **26** / **57** / **19690128** | none — PASS |
| 010331768C | 22 / 19710724 / 22 / 55 / … | 41 / 19690724 / 20 / 57 / 19690724 | — PASS |
| **010150910C** | PUA 56 / 20070901 / 67 / … | dates→base; **stat stays 56** | **920ADB unchanged** — PASS |

---

## 7. Top Changes (nature)

Not a numeric magnitude sort — every PUA row replaces attained issue date/age with base issue date/age (Chris). Largest conceptual delta is sample `010310404C` (2011/68 → 1969/26).

---

## 8. Material Calculation Impact

| Intentional | Accidental drift to avoid |
|-------------|---------------------------|
| PUA phase metadata for QLAdmin PUA/value calc | Changing ADB/WP/term rider dates or ages |
| Aligning PUA `MLASTANN` to base duration | Changing phase-1 base |
| PUA status 41 on in-force | Forcing 41 on death/lapse bases |
| — | Adding PA plan file or inventing NFOINT |

Track A alone may not fully fix PUA **dollar** CV until Track B interest is loaded — Chris UAT still needs Data Admin + rebuild CV after both.

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Pass** — not touched |
| Issue #26 MPREM / MMODPREM | **Pass** — not touched |
| Issue #59 MSTATUS | **Pass** — `quikmstr` not touched |
| Issue #56 add-PA-plan | **Withdrawn** — must not reintroduce |
| Non-PUA rider dates/ages | **Pass** — gated; validator must assert |

---

## 10. Regression Testing Checklist (Validation Agent)

- [ ] `010310404C` PUA: status 41, eff/age/mlastann = base, payup = eff  
- [ ] `010150910C`: PUA dates/ages updated; **`920ADB` MEFFDATE/MAGE unchanged**  
- [ ] Fleet: **0** non-PUA later-phase rows with MEFFDATE/MAGE delta vs pre-batch baseline  
- [ ] Fleet: only rows passing PUA product gate change Track A fields  
- [ ] Terminated-base PUA: `MPHSTAT` not forced to 41 (239 cohort)  
- [ ] Phase-1 base dates/ages/status unchanged  
- [ ] MUNIT / MPREM / MPOLICY unchanged on sample + spot checks  
- [ ] No `1960PA` added to `quikplan` / QuikCvs  
- [ ] #25 / #26 guards PASS  

---

## 11. Recommended Development Agent Task

1. **Composer 2.5** after user: `Issue #60 Track A approved for Development`.  
2. Expand `_cache_quikridr_base_phase` to store `MEFFDATE`, `MAGE`, `MLASTANN` (keep existing MPLAN/MEXPRY).  
3. In `_apply_pua_rider_inheritance` **only** (still gated by `_is_paid_up_addition_product`):  
   - `MEFFDATE` ← base  
   - `MAGE` ← base  
   - `MPAYUP` ← that MEFFDATE (not base MPAYUP)  
   - `MLASTANN` ← base  
   - `MPHSTAT` ← `41` **iff** base `MPHSTAT` &lt; 50  
   - Keep `MPLAN` / `MEXPRY` behavior  
4. **Do not** add any loop that copies base dates/ages to non-PUA phases.  
5. **Do not** touch rate emit / QuikPlCv / add PA plan.  
6. Version bump both `app.py` copies (next after v57.84).  
7. Validator `QLA_Migration/_validate_issue60_pua_phase.py`: PUA rules + **assert zero MEFFDATE/MAGE deltas on non-PUA later phases** vs baseline.  
8. On PASS: copy modified `quikridr` to `Output/Test_Validation/`.

---

## Appendix

### Scope addendum (Risk)

| ID | Decision |
|----|----------|
| **SD-60-11** | Date/age/payup/mlastann/status overrides apply **only** to PUA product rows. **Other riders unchanged.** |
| **SD-60-12** | `MPHSTAT=41` only when base phase `MPHSTAT` &lt; 50. |

### Related

- Planning: `Issue_60_Planning_Report.md`  
- Gate: `Issue_60_Dependency_Gate.md` (Track A PASS)  
- #56 withdrawn  

### Next prompt

```
Issue #60 Track A is approved for Development.
Switch to Composer 2.5. Read Issue_60_Risk_Review_Report.md and
Issue_60_Scope_Decisions.md. PUA-only inheritance; do not change
dates/ages on other riders. Surgical only; version bump both app.py.
```
