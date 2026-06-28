# Issue #21J — Planning Correction Report

**Issue:** Modal Premium Factors — Governance vs. Policy Quote Factors  
**Date:** 2026-06-28  
**Project version under review:** v57.37  
**Stage:** Planning / Research Correction Agent ✅  
**Constraint:** No code changes in this stage. Validation **on hold** pending this report.

---

## 1. Executive Summary

Issue #21J was originally logged as a **modal premium amount mismatch** (QLAdmin Coverage Detail grossing monthly as Annl÷12 vs LifePRO draft premium). Development at **v57.37** implemented a **QUIKMEMO governance memo** documenting **QLAdmin standard plan-level modal factors** (100 / 51 / 26.5 / 9.25 / 9.25) — not LifePRO policy-level Premium Quote effective factors.

**Research conclusion:** LifePRO monthly source extracts **do not contain** policy-level modal quote factors (e.g. 0.525 / 0.27 / 0.088) or a modal premium quote grid. They **do contain** the policy’s **actual billed modal premium** (`MODE_PREMIUM = 43.91` for `010713704C`), which the converter already loads to `quikmstr.MMODEPREM`.

| Question | Answer |
|----------|--------|
| Are LifePRO policy-level quote factors in source data? | **No** — not in any loaded extract |
| Does v57.37 memo document plan factors only? | **Yes** — QLAdmin standard values only |
| Does v57.37 memo document imported `MODE_PREMIUM`? | **No** — gap |
| Does memo incorrectly imply quote factors were imported? | **Partial risk** — wording says factors “used during conversion” without clarifying policy premium came from `MODE_PREMIUM` |
| Is current implementation sufficient for governance scope? | **Mostly yes**, with **recommended memo wording revision** |
| Is Development rework required? | **Minor wording only** — not premium/rating rework |

**Recommendation:** **Revise memo wording only** (Development Rework Agent), then proceed to Validation. Do **not** attempt to add LifePRO policy-level quote factors unless a new LifePRO extract is delivered.

---

## 2. Source Data Inventory

### 2.1 LifePRO extracts in `QLA_Migration/Source/` (May 2026 load)

| Extract | LifePRO table | Used for | Modal / premium relevance |
|---------|---------------|----------|---------------------------|
| `PPOLC_PolicyMaster_Extract_20260530.csv` | PPOLC | quikmstr | **`MODE_PREMIUM`**, `ANNUAL_PREMIUM`, `BILLING_MODE`, billing fields |
| `PPBEN_PolicyBenefit_Extract_20260530.csv` | PPBEN | quikridr | **`ANN_PREM_PER_UNIT`**, **`MODE_PREMIUM`** (per benefit row) |
| `PCOVR_Coverage_Extract_20260530.csv` | PCOVR | quikplan (via crosswalk) | Product/plan setup — **no modal factor % columns** in extract |
| `PACTG_Accounting_Extract20260530.csv` | PACTG | quikprmh | Historical **paid premium** amounts (e.g. 43.91) |
| Other extracts | PPBENTYP, RNA, PNOTE, PENSE, etc. | Various | No modal quote factors |

**Not present in source package:** Premium Quote table, modal factor override extract, policy-level effective factor columns, semi/quarterly/monthly quote amount fields.

### 2.2 Modal / premium columns found (PPOLC — 22 columns matching MODE/PREM/BILL patterns)

Relevant populated fields for conversion:

| Column | In extract? | Mapped to QLAdmin? |
|--------|-------------|-------------------|
| `MODE_PREMIUM` | ✅ | ✅ `quikmstr.MMODEPREM` |
| `ANNUAL_PREMIUM` | ✅ | ❌ Not mapped |
| `BILLING_MODE` | ✅ | ✅ `quikmstr.MMODE` |
| `BILLING_FORM` | ✅ | ✅ `quikmstr.MBILLFRM` |
| Semi / Qtr / Mth **quote amounts** | ❌ | — |
| Effective modal **factor %** (0.525, 0.27, 0.088) | ❌ | — |

### 2.3 Modal / premium columns found (PPBEN)

| Column | Mapped? | Target |
|--------|---------|--------|
| `ANN_PREM_PER_UNIT` | ✅ | `quikridr.MPREM` (Issue #26) |
| `MODE_PREMIUM` | ❌ (policy level uses PPOLC) | — |
| Modal factor / quote columns | ❌ None present | — |

### 2.4 QUIKPLAN modal factors (conversion output)

From `Sync_Rulebook_quikplan.csv` defaults — **not read from LifePRO extract fields**:

| Field | Value (plan 1659C2 confirmed in output) |
|-------|-------------------------------------------|
| ANNL | 100.0000 |
| SEMI | 51.0000 |
| QTRL | 26.5000 |
| MTHD | 9.2500 |
| MTHB | 9.2500 |

### 2.5 What is NOT available in source data

The following **cannot** be sourced from current LifePRO extracts without invention or a new extract:

- Policy-level Premium Quote **effective modal factors** (~0.525 / 0.27 / 0.088 cited from LifePRO UI screenshots)
- Modal quote grid: semi-annual quote ($498.99), quarterly quote, monthly quote (distinct from `MODE_PREMIUM`)
- Per-policy modal factor overrides

These values appear in **LifePRO runtime Premium Quotes / Coverage Detail UI**, not in the May 2026 conversion extract set documented in `docs/LIFEPRO_SOURCE_FILES.txt`.

---

## 3. Policy `010713704C` Evidence Review

**Legacy LifePRO key:** `9010713704`  
**QLAdmin MPOLICY:** `010713704C`  
**Phase-1 MPLAN:** `1659C2` (659 CEN II)

### 3.1 LifePRO source (PPOLC)

| Field | Value | Notes |
|-------|-------|-------|
| `BILLING_MODE` | `1` | Monthly draft (PAC) |
| `MODE_PREMIUM` | **43.91** | **Authoritative billed modal premium** |
| `ANNUAL_PREMIUM` | 526.92 | Present in extract; **not mapped**; equals 43.91 × 12 (1/12 relationship) |
| Modal quote factors | *absent* | — |

### 3.2 LifePRO source (PPBEN — base benefit, BENEFIT_SEQ = 1)

| Field | Value |
|-------|-------|
| `PLAN_CODE` | 659 CEN II |
| `NUMBER_OF_UNITS` | 25.00000 |
| `ANN_PREM_PER_UNIT` | 20.07680 |
| `MODE_PREMIUM` | 43.91 |
| `VALUE_PER_UNIT` | 1000.00 |

### 3.3 QLAdmin conversion output

| Table / field | Value | Source |
|---------------|-------|--------|
| `quikmstr.MMODEPREM` | **43.91** | PPOLC `MODE_PREMIUM` ✅ |
| `quikmstr.MMODE` | 01 | PPOLC `BILLING_MODE` |
| `quikmstr.MSEMI/MQTRL/MMTHD/MMTHB` | blank | Not mapped |
| `quikridr.MPREM` | 20.07680 | PPBEN `ANN_PREM_PER_UNIT` (#26) |
| `quikridr.MUNIT` | 25.00000 | PPBEN units |
| `quikplan` 1659C2 ANNL/SEMI/QTRL/MTHD/MTHB | 100 / 51 / 26.5 / 9.25 / 9.25 | Rulebook defaults |
| `quikprmh.PREMIUM` | 43.91 (all sampled rows) | PACTG payment history |

### 3.4 Issue log / screenshot values (NOT in extract)

From Issue #21 analysis (LifePRO / QLAdmin UI screenshots):

| Display item | Value | Available in extract? |
|--------------|-------|----------------------|
| QLAdmin Coverage Annl | $1,095.44 | ❌ (QLAdmin **derived display**) |
| QLAdmin Coverage Mthly | $91.29 (= Annl ÷ 12) | ❌ |
| LifePRO draft premium | **$43.91** | ✅ `MODE_PREMIUM` |
| LifePRO SA factor (screenshot) | ~0.525 | ❌ UI/runtime only |
| LifePRO Q factor (screenshot) | ~0.27 | ❌ UI/runtime only |
| LifePRO M factor (screenshot) | ~0.088 | ❌ UI/runtime only |
| LifePRO semi quote (screenshot) | $498.99 | ❌ |

**Draft premium $43.91 trace:** `PPOLC.MODE_PREMIUM` → `quikmstr.MMODEPREM` → `quikprmh.PREMIUM`. **Correctly converted.**

**Annual $1,095.44 / monthly $91.29:** QLAdmin appears to derive Coverage Detail modal breakdown from **plan factors × coverage rate × units** (or similar runtime path), not from LifePRO Premium Quotes extract. This is the **display mismatch** that originated Issue #21J — it is **not** a missing conversion field for draft premium.

---

## 4. Current v57.37 Memo Behavior

### 4.1 Implementation review

| Component | Behavior |
|-----------|----------|
| `append_issue21j_conversion_memos()` | Adds one `[CONVERSION]` segment per `quikmstr` policy |
| MPLAN resolution | Phase-1 `quikridr.csv`; key = `format_qladmin_mpolicy(MPOLICY)` |
| Memo content | Hardcoded QLAdmin standard factors via `ISSUE21J_MODAL_FACTORS` |
| PNOTE/PENSE | Preserved after `\n---\n` (#21M-FU grain intact) |
| Premium fields | **Not read** for memo text |

### 4.2 Sample memo — `010713704C` (actual v57.37 output)

```
[CONVERSION]
Conversion Version: v57.37
Product Plan: 1659C2
Plan-level modal premium factors used during conversion:
  Annual = 100
  Semi-Annual = 51
  Quarterly = 26.5
  Monthly Draft = 9.25
  Monthly Billing = 9.25
These are QLAdmin standard product modal factors.
Policy premium quotes may differ because runtime premium quote calculations are separate from product setup.
WARNING: If plan-level modal factors are modified after conversion, all affected policy premiums should be recalculated.
```

### 4.3 What the memo documents vs. omits

| Content | Documented? |
|---------|-------------|
| QLAdmin plan-level modal factors (100 / 51 / 26.5 / 9.25 / 9.25) | ✅ |
| Product plan (1659C2) | ✅ |
| Runtime quote disclaimer | ✅ |
| Post-conversion recalculation warning | ✅ |
| Imported `MODE_PREMIUM` (43.91) | ❌ |
| LifePRO policy-level effective quote factors (0.525 / 0.27 / 0.088) | ❌ (not in source) |
| Distinction: plan setup vs. policy billed premium | ⚠️ Implicit only |

### 4.4 Wording accuracy concern

The phrase **“Plan-level modal premium factors used during conversion”** may be read as “these factors determined this policy’s premium.” In fact:

- **Plan factors** were applied to **quikplan product setup** (rulebook defaults), not read from LifePRO.
- **This policy’s billed modal premium** came from **`MODE_PREMIUM`**, not from applying plan factors to coverage.

The disclaimer partially addresses this but does **not** name `MODE_PREMIUM` or state that LifePRO quote factors are **unavailable in extract**.

---

## 5. Gap Analysis

| Gap | Severity | Notes |
|-----|----------|-------|
| Original Issue #21J defect = modal **amount** mismatch in QLAdmin UI | **Out of scope** for v57.37 (no rating changes authorized) | Documented as runtime/display behavior |
| Memo does not record imported `MODE_PREMIUM` | **Medium** | Business may expect “what was converted” for modal premium |
| Memo could imply plan factors drove policy premium | **Medium** | Wording ambiguity |
| LifePRO policy quote factors not in memo | **Low** (if unavailable) | Cannot add without source; should **explicitly state unavailable** |
| `quikmstr.MSEMI/MQTRL/MMTHD/MMTHB` unmapped | **Informational** | Schema slots exist; not part of #21J memo scope |
| Issue tracking sheet still “AWAITING CLIENT” for factor table | **Process** | Superseded by governance-only Development authorization — needs status alignment |

### Business requirement interpretation

| Option | Feasible with current source? | v57.37 status |
|--------|------------------------------|---------------|
| Memo showing **only QLAdmin standard plan factors** | ✅ | **Implemented** |
| Memo showing **LifePRO policy-level effective quote factors** | ❌ Not in extract | **Not implemented — cannot without new source** |
| **Both** plan factors + policy quote factors | ❌ Partial | Plan only |
| Memo + research report explaining quote factors unavailable | ✅ | **Partially** — disclaimer exists; should be strengthened |

**Conclusion:** The v57.37 implementation matches the **authorized governance scope** and the issue-log technical finding that plan factors already align and draft premium converts correctly. It does **not** fully close the **original client confusion** unless memo wording explicitly documents **`MODE_PREMIUM` import** and **quote-factor unavailability**.

---

## 6. Ownership Decision

| Data element | Owner | Conversion action | Memo should reference? |
|--------------|-------|-------------------|------------------------|
| QLAdmin plan modal factors (100/51/26.5/9.25/9.25) | Product setup / quikplan rulebook | Defaults applied at quikplan conversion | ✅ Yes — current |
| Policy billed modal premium (`MODE_PREMIUM`) | LifePRO PPOLC | Mapped to `quikmstr.MMODEPREM` | ✅ **Recommended add** |
| LifePRO Premium Quote effective factors | LifePRO runtime engine | **Not convertible** — not in extract | ✅ **State unavailable** |
| QLAdmin Coverage Detail modal breakdown | QLAdmin runtime | **Not conversion output** | Disclaimer only |
| Modal amount mismatch (1095.44 vs 43.91) | QLAdmin display / runtime | **Not a conversion defect** | Document in memo or ops note |

**Ownership verdict:** Issue #21J **closure as governance** is **Conversion-owned**. Policy-level LifePRO quote factors are **LifePRO-runtime-owned / extract-gap** — defer unless client provides a new extract.

---

## 7. Recommendation

### Primary: **Revise memo wording only** (minor Development Rework)

Before Validation, update `[CONVERSION]` memo text to:

1. Rename section to **“QLAdmin plan-level product modal factors (quikplan setup)”** — avoid “used during conversion” ambiguity.
2. Add **“Policy modal premium loaded from LifePRO: MMODEPREM = {MODE_PREMIUM} (PPOLC.MODE_PREMIUM)”** — sourced from conversion output / PPOLC, not calculated.
3. Add explicit line: **“LifePRO policy-level Premium Quote effective modal factors are not present in the LifePRO source extracts and were not converted.”**
4. Retain existing runtime disclaimer and recalculation WARNING.

**Do not:**
- Change premium calculations, rulebooks, crosswalks, or quikplan values
- Derive or invent 0.525 / 0.27 / 0.088 factors
- Map new LifePRO fields without client extract approval

### Alternative: **Accept v57.37 as-is**

Acceptable only if business explicitly signs off that plan-factor documentation + generic disclaimer is sufficient without naming `MODE_PREMIUM` or extract limitation.

### Not recommended

- Adding LifePRO policy-level quote factors to memo **without source** (would violate “do not invent” constraint)
- Reopening premium/rating engine work under #21J (explicitly excluded)

---

## 8. Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| Operators assume memo lists all modal data converted | Medium | Wording revision + `MODE_PREMIUM` line |
| Client expects 0.525/0.27/0.088 in memo | Medium | Explicit “not in extract” statement |
| Validation proceeds on ambiguous memo | Medium | **Hold Validation** until wording decision |
| #21M row count change (4380→5083) | Low | Update baseline after memo wording finalized |
| Protected issues (#25/#26/#28/#21D) | Low | No premium/schema changes proposed |

---

## 9. Whether Development Rework Is Required

| Category | Required? |
|----------|-----------|
| Premium / rating / rulebook changes | **No** |
| Memo wording enhancement | **Yes — recommended** |
| New LifePRO extract integration | **No** (unless client delivers quote-factor extract) |
| #21M validator baseline update | **Defer** until memo wording finalized |

**Verdict:** **Minor Development Rework** (memo text only in `format_conversion_modal_factor_memo()` + optional pass of `MMODEPREM` from quikmstr). Estimated blast radius: QUIKMEMO MEMOTEXT only — preserves all protected issues.

---

## 10. Next-Stage Cursor Prompt

### If memo wording revision approved → **Development Rework Agent**

```
# Issue #21J — Development Rework Agent (Memo Wording Only)

**Version:** v57.37 → v57.38 (patch)
**Authority:** Issue_21J_Planning_Correction_Report.md §7

## Scope
Surgical memo text revision ONLY. No premium, rating, rulebook, crosswalk, or quikplan changes.

## Required memo changes (format_conversion_modal_factor_memo / append_issue21j_conversion_memos)
1. Clarify section title: QLAdmin plan-level product modal factors (quikplan setup) — not "used during conversion" in ambiguous sense.
2. Add policy modal premium loaded: MMODEPREM from PPOLC.MODE_PREMIUM (read from quikmstr.csv or PPOLC during memo build).
3. Add explicit statement: LifePRO policy-level Premium Quote effective modal factors are NOT in LifePRO source extracts and were NOT converted.
4. Retain: standard factors 100/51/26.5/9.25/9.25, runtime disclaimer, recalculation WARNING.

## Files
- qla_core/quikmemo_converter.py
- app.py / QLA_Migration/app.py (version bump, pass MMODEPREM if needed)
- Update Issue_21J deliverables under Issue_Log_Items/Issue_21/Issue_21J/

## Validation prerequisites after rework
- Regenerate quikmemo only or full batch
- Confirm 5083 rows, [CONVERSION] prefix, PNOTE/PENSE preserved
- Sample 010713704C memo shows MMODEPREM=43.91 and extract-unavailable statement

## Protected issues (must not regress)
#21M, #21M-FU, #21K, #25, #26, #28, #21D

Stop after Development Rework — hand off to Validation Agent.
```

### If business accepts v57.37 memo as-is → **Validation Agent**

```
# Issue #21J — Validation Agent

**Version:** v57.37
**Prerequisite:** Business sign-off on Planning Correction Report §7 Alternative (accept as-is).

## Hold lifted conditions
- Planning Correction Report reviewed and accepted
- Confirmed: no LifePRO policy-level quote factors in source extracts
- Confirmed: governance memo documents plan factors only by design

## Validate
- quikmemo.csv = 5083 rows; unique MEMOKEY; [CONVERSION] on all rows
- Memo contains plan factors 100/51/26.5/9.25/9.25 and runtime disclaimer
- 010713704C: MMODEPREM=43.91 unchanged in quikmstr; memo MPLAN=1659C2
- Update validate_issue21m_quikmemo.py expected emitted_rows: 4380 → 5083
- Protected issues #21M, #21M-FU, #21K, #25, #26, #28, #21D: PASS

Stop after Validation — do not proceed to Client UAT without sign-off.
```

---

## Appendix — Converter modal-field read summary

| LifePRO field | QLAdmin target | Read today? |
|---------------|----------------|-------------|
| PPOLC `MODE_PREMIUM` | quikmstr.MMODEPREM | ✅ |
| PPOLC `BILLING_MODE` | quikmstr.MMODE | ✅ |
| PPBEN `ANN_PREM_PER_UNIT` | quikridr.MPREM | ✅ |
| Rulebook defaults | quikplan ANNL/SEMI/QTRL/MTHD/MTHB | ✅ (not from LifePRO) |
| Modal quote factors | — | ❌ Not in extract |
| Semi/Qtr/Mth quote amounts | — | ❌ Not in extract |
| PPOLC `ANNUAL_PREMIUM` | — | ❌ Not mapped |

---

**Planning Correction Agent status:** ✅ COMPLETE  
**Validation status:** ⛔ **ON HOLD** — pending memo wording decision (recommended: minor rework before Validation)
