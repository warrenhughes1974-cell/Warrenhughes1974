# Issue #60 — Planning Report

**Issue:** #60 — PUA phase fields + base plan interest (Chris plan)  
**Framework stage:** Planning Agent (G1)  
**Status:** Ready for Risk Review on **Track A**; Track B **Blocked — Awaiting Actuarial Rates**  
**Generated:** 2026-07-14  
**Intake:** `Issue_60_Intake_Summary.md`  
**Scope lock:** `Issue_60_Scope_Decisions.md` (Chris authority)  
**Code changes:** None (planning is read-only)  
**Model:** Cursor Grok 4.5 (locked Planning)

---

## 1. Executive Finding

Chris (actuary) diagnosed incorrect PUA values on `010310404C` as **wrong PUA phase setup** plus **zero interest on base plan `1960PO`**, not as a missing PA product in the plan file. User locked **Chris’s plan** over Robert’s earlier “add `1960PA` + own CV/TV” guidance (**#56 withdrawn**).

**Track A (ready):** Expand `_apply_pua_rider_inheritance` so every PUA `quikridr` row gets `MPHSTAT=41`, `MEFFDATE`/`MAGE`/`MLASTANN` from base phase 1, and `MPAYUP = MEFFDATE` (eff). Today’s code only copies `MPLAN`/`MEXPRY`/`MPAYUP` (and currently copies **base payup/expiry**, which Chris rejects for payup). Fleet: **494** PUA rows / **492** policies — **100%** mismatch on status, eff, age, mlastann.

**Track B (blocked):** `1960PO` `QuikPlCv.NFOINT` and `QuikPlTv` RSVINT/RSVMETH/INTMETHTV are blank; CSO crosswalk says interest is “Computed on CRVM” with **no code**. Chris must supply the non-zero interest (and reserve methods) before rate emit can be fixed. Do **not** invent rates.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/? | Role for #60 |
|--------------|--------------|-------------|--------------|
| PPBEN | `PPBEN_PolicyBenefit_Extract_20260630.csv` | Yes | Base + PUA benefit rows (issue date/age/status) — **Chris overrides PUA issue/age for QLA** |
| PPOLC | `PPOLC_PolicyMaster_Extract_20260630.csv` | Yes | Context only; not primary for phase fields |
| CSO Mortality Crosswalk | `plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv` | Yes | Confirms `960 PO` → `1960PO` NFOINT **blank** (CRVM) |

### Sample — `9010310404` / `010310404C` PPBEN

| Seq | PLAN_CODE | ISSUE_DATE | ISSUE_AGE | STATUS | PAY_UP_DATE |
|-----|-----------|------------|-----------|--------|-------------|
| 1 | 960 PO | 19690128 | 26 | A | 20460128 |
| 2 | 960 PO PUA | **20110128** | **68** | A | **99999999** |

LifePRO stores PUA at **attained** issue date/age. Chris requires QLA PUA phase to use **base** issue date/age for calculation. PUA `PAY_UP_DATE=99999999` is not a usable QLA date — supports Chris’s eff / eff+1 rule over copying base 2046 payup.

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Role |
|-------|-------|------|
| `quikridr` | `MPHSTAT` | PUA → **41** |
| `quikridr` | `MEFFDATE` | PUA → base phase 1 |
| `quikridr` | `MAGE` | PUA → base phase 1 |
| `quikridr` | `MPAYUP` | PUA → **MEFFDATE** (SD-60-6) |
| `quikridr` | `MLASTANN` | PUA → base (or recompute from inherited MEFFDATE) |
| `quikridr` | `MPLAN` | Keep `base[:4]+"PA"` — **do not** add to `quikplan` |
| `quikridr` | `MEXPRY` | Keep inherit from base |
| `QuikPlCv` | `NFOINT` | Base `1960PO` — must be non-zero / non-blank (Track B) |
| `QuikPlTv` | `RSVINT`, `RSVMETH`, `INTMETHTV` (+ STOREMEANS/CALCMIDS if required) | Base `1960PO` — Track B |

**Code paths (population only — do not change yet):**

| Location | Role |
|----------|------|
| `QLA_Migration/app.py` `_cache_quikridr_base_phase` | Cache phase-1 fields for PUA |
| `QLA_Migration/app.py` `_apply_pua_rider_inheritance` | PUA rewrite (expand) |
| `QLA_Migration/app.py` `_apply_quikridr_mlastann` | Duration from MEFFDATE — will follow inherited date if order correct |
| Rate emit / CSO apply | `QuikPlCv`/`QuikPlTv` assumptions (Track B) |

**Plan file check:** `1960PA` **absent** from `quikplan` (desired under Chris). `1960PO` and catalog `1POPUA` present — do **not** add `1960PA`.

---

## 4. Required Source-to-Target Field Mapping

| Authority | Source | QLAdmin target | Transformation | Change? |
|-----------|--------|----------------|----------------|---------|
| Phase 1 cache | Base `MEFFDATE` | PUA `MEFFDATE` | Copy after base emit | **Yes** |
| Phase 1 cache | Base `MAGE` | PUA `MAGE` | Copy | **Yes** |
| Chris rule | Literal `41` | PUA `MPHSTAT` | Force Paid Up (see Risk for terminated cohort) | **Yes** |
| Chris + SD-60-6 | Inherited PUA `MEFFDATE` | PUA `MPAYUP` | Set equal to MEFFDATE (not base MPAYUP) | **Yes** |
| Phase 1 cache | Base `MLASTANN` **or** recompute | PUA `MLASTANN` | Prefer copy base after MEFFDATE set; else `_compute_quikridr_mlastann(MEFFDATE)` | **Yes** |
| Existing | Base `MEXPRY` / `MPLAN` prefix | PUA `MEXPRY` / `MPLAN` | Unchanged pattern | No (keep) |
| LifePRO PUA ISSUE_DATE/AGE | — | — | **Do not use** for these QLA fields | Override |
| CSO / Chris (Track B) | TBD interest codes | `QuikPlCv.NFOINT`, `QuikPlTv.*` for `1960PO` | Populate non-zero | **Yes** when rates delivered |

### Fields that must remain unchanged

| Target | Touch this issue? |
|--------|-------------------|
| `MPOLICY` padding (#25) | **No** |
| `quikridr.MPREM` (#26) | **No** |
| Base phase 1 `MEFFDATE`/`MAGE`/`MPHSTAT`/`MLASTANN` | **No** |
| Base `1960PO` QuikCvs **grid** values (#41) | **No** (assumptions only in Track B) |
| `quikmstr.MSTATUS` (#59) | **No** (phase PUA status only) |
| PUA `MUNIT` / face (#21K) | **No** |
| Adding `1960PA` to `quikplan` / QuikCvs (#56) | **No — withdrawn** |

---

## 5. Open Client Questions

| ID | Question | Blocks? |
|----|----------|---------|
| **OBQ-1** | Exact **NFOINT** code (or numeric rate) and **reserve** RSVINT / RSVMETH / INTMETHTV for **`1960PO`** (issue-year CRVM)? | **Yes — Track B** |
| **OBQ-2** | Track B scope: **`1960PO` only** (pilot) vs all CSO “Computed on CRVM” plans with blank NFOINT? | Track B scope |
| **OBQ-3** | Confirm **MPAYUP = MEFFDATE** (not eff+1) for UAT on `010310404C`. | Soft — Planning default locked; flip if Chris prefers +1 |
| **OBQ-4** | On **terminated** policies (base/master status ≥50), still force PUA `MPHSTAT=41`, or leave death/lapse phase status? | Soft — Risk recommendation: force 41 only when base `MPHSTAT` &lt; 50 |
| **OBQ-5** | After conversion fix: client runs Data Admin + rebuild CV — any conversion-side rebuild required? | UAT process only |

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Crosswalk + #25 10-char pad |
| Dates | `YYYYMMDD`; PUA `MEFFDATE`/`MPAYUP` = base issue date |
| `MPHSTAT` | `41` (zero-pad not required if current emit is unpadded `41`) |
| `MLASTANN` | Integer string duration matching base |
| Interest codes | 1-char QLA codes per existing QuikPlCv convention — **do not invent** |
| Factors | **Do not emit** new modal/CV factors for PA |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` → `Master_Crosswalk.csv` → QLA  
2. `format_qladmin_mpolicy()` (#25)  
3. PUA detection unchanged: `_is_paid_up_addition_product` + pending-row pass after base cache  

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| PUA `quikridr` rows (`MPLAN` ends with `PA`, len≥6) | **494** | Current Output |
| Policies with ≥1 PUA | **492** | Current Output |
| Rows with `MEFFDATE` ≠ base | **494** (100%) | Research |
| Rows with `MAGE` ≠ base | **494** | Research |
| Rows with `MLASTANN` ≠ base | **494** | Research |
| Rows with `MPHSTAT` ≠ 41 | **494** | Research |
| Rows with `MPAYUP` = base payup (wrong vs Chris) | **494** | Research |
| PUA on active base (`MPHSTAT`&lt;50) | **255** | Research |
| PUA on terminated base | **239** | Research — OBQ-4 |
| Top synthetic plans | `1708PA` 415; `1960PA` 71 | Research |
| `1960PO` QuikPlCv rows needing NFOINT | **2** (M/F) | Output/rates |
| `1960PO` QuikPlTv rows needing RSV* | **2** | Output/rates |

---

## 10. Sample Trace (4 policies)

| Policy (QLA) | Before PUA (stat / eff / age / mlastann / payup) | After proposed | Notes |
|--------------|--------------------------------------------------|----------------|-------|
| **010310404C** | 22 / 20110128 / 68 / 15 / 20460128 | **41** / **19690128** / **26** / **57** / **19690128** | Chris screenshot |
| 010331768C | 22 / 19710724 / 22 / 55 / 20520724 | 41 / 19690724 / 20 / 57 / 19690724 | `1960PA` peer |
| 010350577C | 22 / 19720128 / 02 / 54 / 20730128 | 41 / 19700128 / 00 / 56 / 19700128 | `1960PA` peer |
| 010363098C | 56 / 19720602 / 26 / 54 / 20310602 | **41?** / 19700602 / 24 / 56 / 19700602 | Terminated base — OBQ-4 |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Forcing `MPHSTAT=41` on terminated PUA (239 rows) | Medium | Risk: prefer only when base active (&lt;50) unless Chris overrides |
| Omitting PA plan while Eric said PA CV ≠ base forms | High product | Chris (actuary) wins per user; document; UAT rebuild CV on sample |
| Track B without rates → still bad PUA $ after Track A | High | Do not claim CV $ fixed until interest populated; Chris UAT path needs both |
| `MLASTANN` applied before MEFFDATE inherit today | Medium | Dev: set MEFFDATE then mlastann (or copy base mlastann) |
| MPHDOB derived from issue age | Low | Re-resolve DOB after MAGE/MEFFDATE inherit if needed |
| #56 residual expectations | Process | Tracker + Pause Checkpoint mark withdrawn |

---

## 12. Dependency Gate Preview

| Check | Track A | Track B |
|-------|---------|---------|
| Source present | Met | Met (crosswalk shows gap) |
| Field definitions | Met | Met (targets known) |
| Client scope | **Met** (Chris locked) | Partial — need rate values |
| Example policy | Met | Met |
| Interest values | N/A | **Missing** |

---

## 13. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue #60 Track A only (Chris plan).

Read AI_Agents/Risk_Agent.md, Issue_60_Planning_Report.md,
Issue_60_Scope_Decisions.md, Issue_60_Dependency_Gate.md.

Model: Cursor Grok 4.5. Do not code.

Quantify before/after for expanding PUA inheritance:
MPHSTAT=41, MEFFDATE/MAGE/MLASTANN from base, MPAYUP=MEFFDATE.
Recommend whether terminated-base PUA (239) get 41 or stay terminated.
Do not approve Track B interest inventing. Preserve #25/#26.
Issue #56 is withdrawn — confirm no dual Development.
```

---

## 14. Recommended Development Task (Do Not Implement)

### Track A (after Risk Go + user approval → Composer 2.5)

1. Expand `_cache_quikridr_base_phase` to store `MEFFDATE`, `MAGE`, `MLASTANN` (and existing MPLAN/MEXPRY/MPAYUP as needed).  
2. Expand `_apply_pua_rider_inheritance`:  
   - `MEFFDATE`, `MAGE` ← base  
   - `MPHSTAT` ← `41` (or Risk-scoped rule)  
   - `MPAYUP` ← inherited `MEFFDATE` (not base MPAYUP)  
   - `MLASTANN` ← base (or recompute after MEFFDATE)  
   - Keep `MPLAN` / `MEXPRY` behavior  
3. Ensure `MLASTANN` / MPHDOB run **after** inheritance.  
4. **Do not** add `1960PA` to plan/rate emit; **do not** add factors.  
5. Version bump both `app.py` copies.  
6. Validator: `QLA_Migration/_validate_issue60_pua_phase.py` — assert sample + fleet rules; #25/#26 guards.  
7. Publish modified `quikridr` to `Output/Test_Validation/` on PASS.

### Track B (after OBQ-1 rates from Chris)

1. Populate `QuikPlCv.NFOINT` (+ methods if required) and `QuikPlTv` interest/methods for `1960PO` (scope per OBQ-2).  
2. Re-emit rates; UAT: Data Admin + rebuild CV on `010310404C`.  
3. Separate version bump / validator for rates.

---

## Appendix

### #56 disposition

| Prior #56 decision | #60 disposition |
|--------------------|-----------------|
| SD-4 Add PA plan + CV/TV | **Withdrawn** (SD-60-1 / SD-60-9) |
| SD-1 Keep `1960PA` MPLAN | **Keep** synthetic MPLAN only |
| Ready for Development | **Cancelled** — use #60 |

### Related issues

#56 (withdrawn path), #40/#41 (base CV grids), #21K (MUNIT), #25/#26, rate gap grid (CRVM NFOINT).

### Evidence

- `evidence/chris_email_pua_screenshots_20260714.png`  
- Output `quikridr` / `rates/QuikPlCv.csv` / `QuikPlTv.csv` verified 2026-07-14  
