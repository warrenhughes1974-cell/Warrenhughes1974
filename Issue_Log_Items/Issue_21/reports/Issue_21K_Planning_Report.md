# Issue 21K — PUA Amount Precision — Planning Report

**Issue:** 21K — PUA Amount Precision  
**Framework stage:** Planning Agent (Stage 2)  
**Status:** **HOLD — Dependency Gate** (awaiting client QLAdmin `MUNIT` precision confirmation)  
**Generated:** 2026-06-24  
**Engine version at review:** v57.33  
**Agent/script:** `_research_issue21k_munit.py` v1.0 (read-only)  
**Code changes:** None

---

## 1. Planning Summary

Paid-Up Addition (PUA) face amounts lose cents in QLAdmin (example policy **010448806C**: LifePRO **$5,752.96** vs QLAdmin **$5,752.00**). Planning confirms the **Intake finding**: conversion **`quikridr.csv` is correct** — `MUNIT = 5.75296`, `MVPU = 1000.00`, implied face **$5,752.96**. The cent loss aligns with **downstream truncation of `MUNIT` to three decimal places** (5.75296 → 5.752 → $5,752.00), not with conversion CSV emission.

The conversion engine emits **`quikridr.csv` only** — it does **not** generate `QUIKRIDR.DBF`. QLAdmin Help confirms **`MUNIT` semantics** (“number of units of coverage”) but the repo does **not** contain the **`N(length, decimals)` DBF definition** for `QUIKRIDR.MUNIT`. Without a post-load DBF sample or vendor schema extract, the failure point cannot be proven to the bit — only strongly inferred from client UAT.

**Recommended direction:** **Option A — no converter change** until Dependency Gate clears. If QLAdmin/load supports five decimal `MUNIT`, remediation belongs to the **client load path** (CSV→DBF import configuration), not the conversion rulebook. If QLAdmin hard-limits `MUNIT` to three decimals, escalate to **New Era / client** for schema or display change — **not** a PUA-only rounding hack in the converter.

**Dependency Gate:** **HOLD** — proceed to Risk Agent only after client supplies `MUNIT` field definition and post-load `QUIKRIDR.DBF` row for **010448806C** MPHASE 2 / plan **1708PA**.

---

## 2. Confirmed Facts

| # | Fact | Evidence |
|---|------|----------|
| F1 | LifePRO PUA face for **010448806C** is **$5,752.96** | `Issue_Log_Items/Issue_21/010448806C - LifePRO.docx`; Issue #21 Final Analysis C11 |
| F2 | QLAdmin displays **$5,752.00** (implied `MUNIT ≈ 5.752` at `MVPU = 1000`) | Client UAT; tracking sheet |
| F3 | Converted **`quikridr.csv`** PUA row (MPHASE 2, `1708PA`) has **`MUNIT = 5.75296`**, **`MVPU = 1000.00`** | `QLA_Migration/Output/quikridr.csv` (verified 2026-06-24) |
| F4 | Rulebook maps **`NUMBER_OF_UNITS → MUNIT`** with no precision transform | `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv` line 14 |
| F5 | Crosswalk maps LifePRO **`9010448806` → `010448806C`** | `QLA_Migration/Mapping/Master_Crosswalk.csv` row 356 |
| F6 | Conversion batch emits **`quikridr.csv` only** — **no `QUIKRIDR.DBF`** from engine | `QLA_Migration/RUN_GUIDE.md`; `app.py` has `write_quikmemo_dbf` for memos only; no quikridr DBF writer |
| F7 | QLAdmin Help defines **`MUNIT`** = “Number of units of coverage”; **`MVPU`** = “Value per unit”; face = **`MUNIT × MVPU`** | `Issue_Log_Items/Issue_26/Issue_26_Field_Definition_Report.md` (Help §QuikRidr ~p. 887–901) |
| F8 | Issue **not PUA-only** in conversion output — **1,068** rider rows carry sub-mill `MUNIT` precision; **488** PUA-style (`MPLAN` ends `PA`) rows would lose ≥ $0.01 face under 3 dp truncate | `_research_issue21k_munit.py` on current `quikridr.csv` (7,002 rows) |
| F9 | **`PPBEN_PolicyBenefit_Extract_20260530.csv` does not contain policy `9010448806`** in the current Source package | Grep 2026-06-24; batch output nonetheless includes `010448806C` (prior/full batch source) |

**Hypothesis (not yet proven in repo):** QLAdmin or the client CSV→DBF load path stores `MUNIT` as **`N(?,3)`** (truncate), while LifePRO and conversion CSV carry up to **five** significant decimal places.

---

## 3. Failure-Point Matrix

| Stage | Component | Cent loss observed? | Control | Assessment |
|-------|-----------|:-------------------:|---------|------------|
| 1 | LifePRO PPBEN `NUMBER_OF_UNITS` | No | LifePRO | Source carries **5.75296** (client screenshot + intake) |
| 2 | Crosswalk / rulebook | No | Conversion | Direct map; no precision rule |
| 3 | **`quikridr.csv` emission** | **No** | Conversion | **`5.75296` preserved** — **cleared** |
| 4 | CSV numeric formatting | No | Conversion | All rows formatted `X.XXXXX` (5 char decimal width); values with only 3 sig dp (e.g. `5.77800`) are padding, not loss |
| 5 | **Conversion DBF writer** | N/A | Conversion | **No quikridr DBF path exists** — not in scope |
| 6 | **Conversion DBF schema** | N/A | Conversion | `validation_config/schema_manifest.json` lists columns only — **no `N(?,?)` types** |
| 7 | **Client CSV → DBF build** | **Likely** | Client / New Era | Unknown load tooling; tracking sheet cites ~3 dp truncation |
| 8 | **QLAdmin `QUIKRIDR` table definition** | **Likely** | New Era | **`MUNIT` decimal count not in repo** |
| 9 | **QLAdmin display** (`MUNIT × MVPU`) | **Likely** | QLAdmin UI | $5,752.00 matches truncated units |
| 10 | Prior reload / re-import path | Unknown | Client | Same table — would inherit same `MUNIT` precision cap |

**Primary suspect:** stages **7–9** (client load + QLAdmin storage/display).  
**Cleared:** stages **1–4** (source through conversion CSV).

---

## 4. Population Impact

Analysis: read-only on `QLA_Migration/Output/quikridr.csv` (7,002 rows, engine v57.33 batch).  
Script: `QLA_Migration/_research_issue21k_munit.py`  
Trace sample: `Issue_Log_Items/Issue_21/Issue_21K_MUNIT_Precision_Trace.csv`

| Metric | Count | Notes |
|--------|------:|-------|
| Total `quikridr` rows | **7,002** | Full batch |
| Rows with **sub-mill** `MUNIT` (4th–5th decimal significant) | **1,068** | Meaningful precision beyond 3 dp |
| Rows where **`MUNIT × MVPU`** has **non-zero cents** | **1,070** | Fractional-dollar face |
| PUA-style rows (`MPLAN` ends **`PA`**) | **494** | Includes `1708PA` |
| PUA-style rows with sub-mill `MUNIT` | **488** | Nearly all PA rows |
| Rows where **3 dp `MUNIT` truncate** changes face by **≥ $0.01** | **1,067** | Fleet-wide, not PUA-only |
| Same, **PA rows only** | **488** | Client-visible PUA cohort |
| Unique policies with face delta **≥ $0.01** (3 dp hypothesis) | **949** | |
| Unique policies — **PA only** | **487** | |
| Maximum face delta under 3 dp truncate | **$5.02** | Policy `010510671C` ph1 (`MVPU = 5234`) |

**Intake note on “89% rows >3 dp”:** that figure counts **CSV string width** (all rows emit five decimal places, e.g. `5.77800`). Planning uses **significant precision** (1,068 rows) for impact sizing — the correct metric for truncation risk.

**Scope conclusion:** Any remediation must treat **`MUNIT` as a fleet-wide precision field**, not a PUA-only formatter change.

---

## 5. External Dependencies

| Dependency | Owner | Status | Required for |
|------------|-------|--------|--------------|
| QLAdmin Help or schema extract: **`QUIKRIDR.MUNIT` `N(?,?)`** | New Era / Client | **Missing from repo** | Confirm 3 vs 5 decimal storage |
| Post-load **`QUIKRIDR.DBF`** for **010448806C** MPHASE 2 / `1708PA` | Client | **Not supplied** | Prove stored `MUNIT` value |
| Client **load method** documentation (CSV import vs external DBF rebuild) | Client | **Unknown** | Locate truncation stage |
| Working/production **`QUIKRIDR.DBF`** sample (non-converted) for precision comparison | Client | **Not in repo** | Baseline QLAdmin behavior |
| New Era confirmation: can **`MUNIT`** be **`N(10,5)`** or equivalent? | New Era | **Open** (tracking sheet Q) | Option A vs B vs C |
| Business rule if 3 dp is immovable | Client | **Open** | Accept loss vs vendor change |

**In-repo gaps (not blockers for Planning, blockers for Risk/Development):**

- No `quikridr.dbf` under `QLA_Migration/Output/` or `docs/`
- `validation_config/schema_manifest.json` — column names only, no FoxPro types
- Current Source package missing PPBEN row for trace policy (output from prior batch still valid)

---

## 6. Decision-Path Evaluation

### Option A — No converter change (**RECOMMENDED pending confirmation**)

| Criterion | Assessment |
|-----------|------------|
| Fit | **Strong** — CSV already correct |
| Action | Document that remediation belongs to **client load / QLAdmin `MUNIT` definition** if truncation confirmed |
| Converter work | **None** |
| Risk | **Low** — avoids corrupting correct CSV to match a defective downstream cap |

**Planning recommendation:** Default path. Do **not** alter `NUMBER_OF_UNITS → MUNIT` mapping or add PUA-specific formatting until Dependency Gate clears.

### Option B — DBF schema precision change

| Criterion | Assessment |
|-----------|------------|
| Fit | **Not applicable to current conversion pipeline** — engine does not emit `QUIKRIDR.DBF` |
| Local control | Only if project **adds** a quikridr DBF writer (out of scope; no precedent except `quikmemo_uat_dbf`) |
| Client path | If client rebuilds DBF with `N(10,3)`, client must change to **`N(?,5)`** aligned with QLAdmin vendor spec |
| Converter role | **None today** |

**Planning recommendation:** Defer unless client confirms they load from a **project-generated DBF** and QLAdmin accepts wider precision.

### Option C — Alternate face storage

| Candidate field | Role | Viable for exact PUA face? |
|-----------------|------|:--------------------------:|
| **`MUNIT × MVPU`** | Canonical QLAdmin face | **Yes** — if `MUNIT` precision fixed |
| **`MSAVEUNIT`** | Original units (Help) | **No** — unmapped; semantic is historical, not current face |
| **`MSAVEVPU`** | Original value per unit | **No** — unmapped; not current face |
| **`MCV0`/`MCV1`/`MCV2`** | Cash values | **No** — different domain (Issue 21E) |
| **`quikactg.MDIVPUA`** | Dividend accounting | **No** — not issued rider face |
| Policy memo / extension table | Ad hoc | **Not confirmed** — would need client approval |

**Planning recommendation:** **Do not implement** unless New Era confirms QLAdmin **cannot** widen `MUNIT` and names an approved alternate field. No such field identified in Help review to date.

### Option D — Rounding workaround (**REJECT**)

| Approach | Why reject |
|----------|------------|
| Truncate CSV `MUNIT` to 3 dp | Destroys correct data; matches bad downstream instead of fixing it |
| PUA-only 2 dp face rounding | Wrong grain — 949 policies affected; violates fleet precision |
| Scale units (×1000 into integer field) | No approved target field; high regression risk |

**Planning recommendation:** **Reject** unless Dependency Gate proves structural fix impossible **and** client accepts systematic cent loss in writing.

---

## 7. Recommended Remediation Path

```text
Step 1  HOLD — Client/New Era answers open MUNIT precision question (tracking sheet 21K)
Step 2  Client supplies post-load QUIKRIDR.DBF row for 010448806C / 1708PA / MPHASE 2
Step 3  Compare stored MUNIT to quikridr.csv (expect 5.75296 vs 5.752)
Step 4a IF stored value matches CSV → investigate QLAdmin display calculation (UI rounding)
Step 4b IF stored value truncated → fix client CSV→DBF import or QLAdmin field width (Option A/B client-side)
Step 4c IF QLAdmin cannot hold 5 dp → Option C only with written client/vendor approval; else accept or defer
Step 5  Risk Agent → Development ONLY if converter change proven necessary (currently NOT expected)
```

**Converter guardrails (unchanged regardless of path):**

- **Issue #25:** `format_qladmin_mpolicy()` — do not alter
- **Issue #26:** `ANN_PREM_PER_UNIT → MPREM` — do not alter
- **Issue #21C:** fee fields — do not alter

---

## 8. Options Rejected

| Option | Reason |
|--------|--------|
| **D — Rounding / PUA-only truncate in converter** | CSV is correct; would institutionalize precision loss across 949+ policies |
| **B — Local DBF schema change now** | No quikridr DBF generation path; premature |
| **C — Alternate field without client sign-off** | No confirmed QLAdmin target; `MSAVE*` fields wrong semantics |
| **Issue #21 Final Analysis “preserve 2 decimals on PUA path”** | Superseded by intake: loss is **downstream**, not CSV formatting; PUA-only code change would miss 581 non-PA affected rows |

---

## 9. Required Evidence Before Risk Agent

| # | Evidence | Purpose | Owner |
|---|----------|---------|-------|
| E1 | QLAdmin Help or data dictionary: **`MUNIT` numeric type** (`N length, decimals) | Confirm 3 vs 5 dp cap | New Era / Client |
| E2 | Post-load **`QUIKRIDR.DBF`** extract: **010448806C**, MPHASE **2**, MPLAN **1708PA** | Prove where truncation occurs | Client |
| E3 | Description of **CSV import / DBF rebuild** toolchain for `quikridr` | Identify stage 7 vs 8 vs 9 | Client |
| E4 | Optional: production **`QUIKRIDR.DBF`** row with known fractional PUA for baseline | Compare native QLAdmin precision | Client |
| E5 | Written answer: if 3 dp is fixed, **accept cent loss** vs **vendor change** vs **alternate field** | Business decision for Option C/D | Client |

**Risk Agent may proceed when E1 + E2 + E3 are satisfied** (or documented client sign-off on assumptions).

---

## 10. Dependency Gate Recommendation

| Gate check | Met? | Notes |
|------------|:----:|-------|
| Source file present | **Partial** | Output CSV present; PPBEN extract missing trace policy in current Source |
| QLAdmin target field definition confirmed | **No** | Semantics only; **`N(?,?)` unknown** |
| Client scope clear | **Yes** | Fix cent accuracy on PUA face display; fleet-wide `MUNIT` implication understood |
| Example policies available | **Yes** | **010448806C** + trace CSV samples |
| Failure point localized to conversion | **No** | **Cleared conversion** — downstream unproven |

### **Recommendation: HOLD**

Do **not** proceed to Risk Agent or Development until **E1** and **E2** are delivered. Planning is complete; the blocker is **external confirmation**, not missing internal analysis.

If client returns proof that QLAdmin stores **5.75296** correctly but UI shows **$5,752.00**, re-scope to **QLAdmin display** (vendor ticket) — still **no converter change**.

---

## 11. Confirmed LifePRO Source

| Source | File | Grain | Mapping |
|--------|------|-------|---------|
| PPBEN | `PPBEN_PolicyBenefit_Extract_*.csv` / batch `PPBEN.csv` | One row per benefit (`BENEFIT_SEQ`) | `NUMBER_OF_UNITS → MUNIT` |
| PUA identification | `BENEFIT_TYPE = PU` and/or crosswalk plan **`1708PA`** | MPHASE > 1 typical | Engine PUA inheritance (MPHASE 2+) |

---

## 12. Confirmed QLAdmin Target Structure

| Table | Field | Semantic definition | DBF type in repo |
|-------|-------|---------------------|------------------|
| **QUIKRIDR** | **MUNIT** | Number of units of coverage | **Unknown** |
| **QUIKRIDR** | **MVPU** | Value per unit ($ face per unit) | Unknown (emitted `1000.00`) |
| Derived | **`MUNIT × MVPU`** | Phase face amount (Coverage tab) | Display-layer |

---

## 13. Required Source-to-Target Mapping

| LifePRO field | QLAdmin field | Transformation | Change for 21K? |
|---------------|---------------|----------------|-----------------|
| `NUMBER_OF_UNITS` | `MUNIT` | Direct copy | **No** (keep) |
| `VALUE_PER_UNIT` | `MVPU` | Direct copy | **No** |

### Fields that must remain unchanged

| Target | Current behavior | Touch? |
|--------|------------------|--------|
| `quikridr.MPREM` | `ANN_PREM_PER_UNIT` + fallback (#26) | **No** |
| `quikmstr.MMODEPREM` | PPOLC `MODE_PREMIUM` | **No** |
| `MPOLICY` | 10-char left-pad (#25) | **No** |
| PUA phase/plan logic | MPHASE 2 / `1708PA` inheritance | **No** |

---

## 14. Sample Trace (4 policies)

| Policy | Phase | Plan | CSV `MUNIT` | `MVPU` | Face | Face if 3 dp `MUNIT` | Δ | Status |
|--------|------:|------|------------:|-------:|-----:|---------------------:|------:|--------|
| **010448806C** | 2 | **1708PA** | **5.75296** | 1000.00 | **5752.96** | 5752.00 | **0.96** | Client example — PUA |
| 010615191C | 2 | 1708PA | 3.74599 | 1000.00 | 3745.99 | 3745.00 | 0.99 | PUA cohort |
| 010367438C | 2 | 1708PA | 2.46499 | 1000.00 | 2464.99 | 2464.00 | 0.99 | PUA cohort |
| 010510671C | 1 | 2665ST | 1.15296 | 5234.00 | 6034.59 | 6029.57 | 5.02 | Non-PUA; high `MVPU` amplifies loss |

Full trace rows: `Issue_21K_MUNIT_Precision_Trace.csv`

---

## 15. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Fix converter when CSV is already correct | **High** | HOLD until E1/E2 |
| PUA-only patch leaves 581 non-PA rows wrong | **High** | Fleet-wide `MUNIT` policy |
| QLAdmin immovable 3 dp cap | **Medium** | Option C/D only with client sign-off |
| Remediation Plan lists 21K “ready without client” vs tracking **AWAITING CLIENT** | **Medium** | Planning follows **tracking sheet / intake** reclassification — client gate first |
| Missing PPBEN row for 010448806C in current Source | **Low** | Re-extract for Validation; output CSV sufficient for Planning |

---

## 16. Recommended Risk Agent Prompt

```text
Risk Agent — Issue 21K: PUA Amount Precision

Read:
- Issue_Log_Items/Issue_21/Issue_21K_Intake_Report.md
- Issue_Log_Items/Issue_21/Issue_21K_Planning_Report.md

Prerequisite: Dependency Gate cleared — client supplied QUIKRIDR.MUNIT N(?,?) definition
and post-load QUIKRIDR.DBF row for 010448806C MPHASE 2 / 1708PA.

Assess:
1. Whether any converter change is warranted (expect NO if CSV matches DBF input).
2. Regression scope if client-side load fix only.
3. Fleet impact: 949 policies / 1067 rows under 3 dp truncate hypothesis.

Do NOT change quikridr rulebook, MUNIT mapping, MPREM (#26), or MPOLICY padding (#25)
unless Risk explicitly approves after E1/E2 proof.

Deliver: Issue_21K_Risk_Review_Report.md
```

---

## 17. Recommended Development Task (Do Not Implement)

**Expected outcome after Dependency Gate:** **No converter development** (Option A).

If E2 proves client load truncates a **correct CSV**:

1. Document client load fix — **outside** `app.py` scope.
2. Add read-only validator `QLA_Migration/_validate_issue21k_munit.py` to assert `MUNIT` significant precision preserved in CSV and (optional) client DBF ≥ 5 dp when sample provided.
3. **Do not** bump engine version for client-only fixes.

If E1 proves QLAdmin accepts 5 dp but converter somehow regressed (unlikely):

1. Surgical verify `NUMBER_OF_UNITS` passthrough only — no new formatters.
2. Version bump only if `app.py` touched.
3. Full-batch regression: row counts, `MUNIT`/`MVPU`/`MPREM` unchanged except traced policies.

---

## Appendix A — Pipeline: CSV vs DBF

| Table | Conversion output | DBF in repo |
|-------|-------------------|-------------|
| `quikridr` | **`quikridr.csv`** | **None** |
| `quikmemo` | `quikmemo.csv` + optional UAT DBF | `write_quikmemo_dbf` only |
| Claims UAT | CSV + phase19 DBF generator | `QUIKCLMS`/`QUIKCLMP` only |
| Rate sandbox | CSV + `rate_dbf_writer` | Rate tables only |

Reference: `QLA_Migration/RUN_GUIDE.md` — “writes CSV files that QLAdmin can load.”

---

## Appendix B — Related References

- `Issue_Log_Items/Issue_21/Issue_21K_Intake_Report.md`
- `Issue_Log_Items/Issue_21/Issue_21_Tracking_Sheet.md` — row 21K **AWAITING CLIENT (New Era)**
- `Issue_Log_Items/Issue_21/Issue_21_Final_Analysis.md` — Issue K (CONFIRMED symptom; root cause layer revised by intake)
- `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv`
- `QLA_Migration/_research_issue21k_munit.py`
- `Issue_Log_Items/Issue_21/Issue_21K_MUNIT_Precision_Trace.csv`

---

**Stop point:** Planning Agent complete. **Do not proceed to Dependency Gate review / Risk Agent** until this report is reviewed and client evidence **E1–E2** is requested.
