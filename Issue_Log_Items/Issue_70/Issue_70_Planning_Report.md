# Issue #70 — Planning Report

**Issue:** #70 — QuikPlan `LOANINTX` Advance/Arrears authority (CSO guidance)  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning complete — Dependency Gate next  
**Generated:** 2026-08-02  
**Agent/script:** Cursor Grok 4.5 — research only, no code / no Output / no status change  
**Inputs:** `Issue_70_Intake_Summary.md` (2026-08-02 refresh), `Issue_70_Implementation_Notes.md`, Issue #32 / #104 docs, Source 20260630, current Output

---

## 1. Executive Finding

Chris’s invalid QuikPlan `LOANINTX` (`2`/`22`) was made loadable by v57.89 interim fleet **`A`** (141/141). That interim is **not** product-sourced Advance/Arrears truth.

**Confirmed authority (Intake + Planning re-verify):** LifePRO coverage field `PCOVR.LOAN_ADV_ARREARS` (Excel CJ / column index 87) on the 20260630 extract and on `plan_analysis/quikplan_source.csv`:

| Value | Count | Proposed QuikPlan `LOANINTX` |
|-------|------:|------------------------------|
| `0` | 129 | **A** (Advance) |
| `N` | 8 | **A** (Advance family) |
| `1` | 4 | **R** (Arrears) |

The four Arrears coverages are **SAL OL, SAL ML, SAL MULTPL, SAL ADB** → QuikPlan `1SALOL`, `1SALML`, `1SALMI`, `9SLADB`. PLOAN remains unusable for A/R (`INT_METHOD=D` fleet-wide). SAL has **163** PPBEN policies and **0** PLOAN rows — so flipping those four plans to `R` changes **plan catalog only**; current QuikLoan emit would not inherit `R` for any in-force loan row.

**Recommended direction:** Replace the hard interim “force A” posture with a **source-driven** map from `LOAN_ADV_ARREARS` on the same QuikPlan source row (`COVERAGE_ID` → Master_Crosswalk → `PLAN`), emit `R` for all four SAL Arrears plans (catalog fidelity even with zero loans), keep `A` for `0`/`N`/blank/unknown, preserve #32 QuikLoan lookup + `A` fallback, and do **not** reopen #104 settlement math in this issue.

**Planning verdict:** **G1 Planning Complete** — proceed to Dependency Gate. Do not start Development until Dependency Gate clears and Risk Go + user Development approval.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/? | Row count (data) |
|--------------|--------------|-------------|-----------------:|
| PCOVR | `PCOVR_Coverage_Extract_20260630.csv` | Yes | 141 coverages (`LOAN_ADV_ARREARS`: 0=129, N=8, 1=4; 0 blank/other) |
| QuikPlan source (PCOVR-shaped) | `plan_analysis/quikplan_source.csv` | Yes | Same grain; **includes** `LOAN_ADV_ARREARS` |
| PLOAN | `PLOAN_LoanInformation_Extract_20260630.csv` | Yes | 94,151; `INT_METHOD=D` all; **0** SAL `PLAN_CODE` |
| PPBEN (context only) | `PPBEN_PolicyBenefit_Extract_20260630.csv` | Yes | 163 distinct policies on SAL OL/ML/MULTPL/ADB; **0** of those in PLOAN |

### Available source fields

| Field | Column / source | Populated % | Notes |
|-------|-----------------|------------:|-------|
| Coverage key | `COVERAGE_ID` | 100% | Join to Master_Crosswalk → QuikPlan `PLAN` |
| Advance/Arrears | `LOAN_ADV_ARREARS` | 100% (`0`/`N`/`1` only) | **Authority for #70** |
| Loans available | `LOANS_AVAILABLE` | Partial | SAL ADB = `N`; others Y/blank — informational only |
| Policy form | `POLICY_FORM_NUM` | Partial | Form family note; not the join key |
| PLOAN method | `INT_METHOD` / `INTEREST_TYPE` | 100% D / F | **Rejected** as A/R (#32) |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source (Help / schema) |
|-------|-------|------|--------|------------------------|
| QuikPlan | `LOANINTX` | C | 1 | `schema_manifest.json` / `QUIKPLAN_SCHEMA`; governance: **A or R**, default A |
| QuikLoan | `MLOANINTX` | C | 1 | Help §7.150; **inherits** QuikPlan via #32 — not re-derived from PLOAN |

**Governance / rulebook today**

| Location | Role |
|----------|------|
| `QLA_Migration/Data_Goverence.txt` | `LOANINTX` must be A or R; default A |
| DG-QUIKPLAN-006 | Same A/R rule in data-governance validators |
| `Sync_Rulebook_quikplan.csv` | `LOANINTX` default `A`, `SKIP_TRANSLATION` (empty Source_Field) |
| `qla_core/quikplan_converter.py` | `_normalize_quikplan_loanintx` — invalid/missing → `A` (preserves existing `R` if present) |
| `plan_governance/config/quikloan_derivation_rules.json` | `mloanintx_source=QUIKPLAN_LOANINTX`, default `A` |
| `qla_core/quikloan_converter.py` | `resolve_mloanintx` — plan lookup + A fallback |

**Current Output before-state**

| File | `LOANINTX` |
|------|------------|
| `QLA_Migration/Output/quikplan.csv` | **141 / 141 = A** (incl. all four SAL plans) |
| SAL rows | `1SALOL`, `1SALML`, `1SALMI`, `9SLADB` all `LOANINTX=A`, `LOANINT=0.00` |
| Trace Advance loan plan | `1960PO`: `LOANINT=5.00`, `LOANINTX=A` (aligned with #32 UI Advance) |

---

## 4. Required Source-to-Target Field Mapping

### Recommended mapping (lock for Development unless Risk/CSO overrides)

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PCOVR / `quikplan_source` | `LOAN_ADV_ARREARS` | QuikPlan `LOANINTX` | See codebook below | **Yes** |
| — (derived) | QuikPlan `LOANINTX` | QuikLoan `MLOANINTX` | Existing #32 lookup; no algorithm change | **No** (inherits if plan flips) |
| PLOAN | `INT_METHOD` / `INTEREST_TYPE` | *(none)* | Do not map | **No** |

### Codebook (proposed)

| `LOAN_ADV_ARREARS` (trimmed, casefold) | `LOANINTX` | Rationale |
|----------------------------------------|------------|-----------|
| `0` | **A** | CSO / Intake: In Advance |
| `N` | **A** | CSO / Intake: same Advance family as `0` |
| `1` | **R** | CSO / Intake: In Arrears |
| blank / null | **A** | Governance default; audit warn |
| any other / unknown | **A** | Fail-safe loadable default; audit warn + fail validator if unexpected in Source package |

### Plan-level join / key strategy

1. **Grain:** One QuikPlan row per `COVERAGE_ID` (existing `prepare_quikplan_source` dedupe).  
2. **Same-row map:** Read `LOAN_ADV_ARREARS` from the **same source row** used to emit `PLAN` (prefer `plan_analysis/quikplan_source.csv` / batch QuikPlan source — already carries the column).  
3. **Plan identity:** `COVERAGE_ID` → `Master_Crosswalk` product-plan map → QuikPlan `PLAN` (existing engine path). No policy-number join.  
4. **Confirmed crosswalk for Arrears candidates:**

| `COVERAGE_ID` | QuikPlan `PLAN` |
|---------------|-----------------|
| SAL OL | `1SALOL` |
| SAL ML | `1SALML` |
| SAL MULTPL | `1SALMI` |
| SAL ADB | `9SLADB` |

5. **Optional hardening:** After emit, assert PCOVR 20260630 `LOAN_ADV_ARREARS=1` set equals the four plans above; drift → validator FAIL.  
6. **Do not** join PLOAN for A/R. Do not use `LOANS_AVAILABLE` to suppress `R`.

### SAL / zero-loan handling (Planning recommendation)

| Decision | Recommendation |
|----------|----------------|
| Emit `R` on Arrears plans with **zero** PLOAN rows? | **Yes** — QuikPlan is product catalog; timing belongs on the plan even if no loans exist today |
| Limit `R` to SAL OL + SAL ML only? | **No (default)** — extract marks four coverages; emit all four unless CSO narrows |
| Keep fleet interim `A` forever? | **No** — replace with source map once Risk/Dev approved |

### Fields / surfaces that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| QuikPlan `LOANINT` | PLOAN modal rate enrichment | **No** (only `LOANINTX`) |
| QuikLoan principal/balance/accrual/dates | #32 approved mapping | **No** |
| QuikLoan `MLOANINTX` algorithm | QuikPlan lookup + A fallback | **No** (data may inherit `R` only if a loan’s plan is `R`) |
| #104 claim/surrender settlement | SME options A/B/C | **No** — keep coupled note only |
| `quikmstr.MMODPREM` / `quikridr.MPREM` / MPOLICY | #26 / #25 / #2 | **No** |
| QuikPlSt `MLOANINTX` | State override (future) | **No** |
| Unrelated QuikPlan columns | Rulebook | **No** |

---

## 5. Open Client / CSO Questions (explicit decisions still needed)

| ID | Decision | Planning default if waived into Risk |
|----|----------|--------------------------------------|
| D1 | Confirm codebook: `0` and `N` both Advance (`A`)? Any third meaning? | Treat `0`/`N` → `A`; blank/other → `A` + audit |
| D2 | Emit `R` for **all four** SAL coverages, or only SAL OL / SAL ML forms? | **All four** (`1SALOL`, `1SALML`, `1SALMI`, `9SLADB`) |
| D3 | Keep `R` on zero-loan Arrears plans for catalog fidelity? | **Yes** |
| D4 | Is extract reading final authority, or is a one-line written CSO confirm still required before Development/Closure? | **Extract sufficient for Dev design**; written confirm optional unless Risk elevates |
| D5 | Any #104 UAT interaction if only SAL flips to `R` (zero active SAL loans)? | **No operational QuikLoan impact expected**; do not reopen #104 under #70 |

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Allowed values | Uppercase `A` or `R` only (C(1)) |
| Normalization | Trim + upper; map codebook **before** `_normalize_quikplan_loanintx` |
| Post-normalize | Keep safety net: invalid → `A`; **must not** overwrite a valid mapped `R` (current helper already preserves `R`) |
| Rulebook | Prefer mapping `LOAN_ADV_ARREARS` → `LOANINTX` with transform note; retain `SKIP_TRANSLATION` so status maps cannot turn `A`→`22` again |
| Policy key | N/A for QuikPlan `LOANINTX` (plan grain). QuikLoan continues Issue #2 `format_qladmin_mpolicy` |
| Blanks | Never emit blank `LOANINTX` |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

Not applicable to QuikPlan `LOANINTX` (plan catalog).  
Downstream QuikLoan remains: LifePRO `POLICY_NUMBER` → `format_qladmin_mpolicy()` → `MLOANINTX` from QuikPlan by resolved plan — unchanged by #70 except if a future SAL loan appears under an `R` plan.

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| QuikPlan rows (current Output) | 141 | `quikplan.csv` |
| Expected `LOANINTX=A` after rule | **137** | 129×`0` + 8×`N` |
| Expected `LOANINTX=R` after rule | **4** | SAL OL/ML/MULTPL/ADB |
| QuikLoan rows that would flip to `R` today | **0** | No SAL loans in PLOAN |
| Non-candidate QuikPlan rows (must stay `A`) | 137 | All non-`1` coverages |
| SAL policies in PPBEN (context) | 163 | No loan activity |

---

## 10. Sample Trace (≥3)

| Plan / policy | LifePRO evidence | Before (Output) | After (proposed) | Status |
|---------------|------------------|-----------------|------------------|--------|
| `1SALOL` | PCOVR SAL OL `LOAN_ADV_ARREARS=1` | `LOANINTX=A` | **`R`** | Candidate |
| `1SALML` | PCOVR SAL ML `=1` | `A` | **`R`** | Candidate |
| `1SALMI` | PCOVR SAL MULTPL `=1` | `A` | **`R`** | Candidate |
| `9SLADB` | PCOVR SAL ADB `=1`, `LOANS_AVAILABLE=N` | `A` | **`R`** | Candidate (catalog) |
| `1960PO` / policy `9010331768` | UI Advance (#32); PCOVR non-`1` | `LOANINTX=A`, QuikLoan `MLOANINTX=A` | **`A` unchanged** | Non-candidate control |
| Example `N` plan (e.g. `L15`) | PCOVR `LOAN_ADV_ARREARS=N` | `A` | **`A`** | Non-candidate control |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| `N` means something other than Advance | Medium | D1; default A + CSO confirm if Risk requires |
| Emitting `R` on SAL ADB (`LOANS_AVAILABLE=N`) undesired | Low–Med | D2/D3; can carve out only if CSO says so |
| Over-narrowing to OL/ML only leaves MULTPL/ADB wrong | Medium | Prefer all four from extract |
| Touching #32 QuikLoan math while fixing INTX | High | Out of scope — lookup only |
| Silent #104 reopen | Medium | Explicit non-touch; note zero SAL loan impact |
| Rulebook mistranslation `A`→`22` regression | High | Keep `SKIP_TRANSLATION` / no status map on LOANINTX |
| Source package without column on future extract | Medium | Validator requires column + codebook coverage |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present (`PCOVR` + `quikplan_source` column) | **Yes** |
| QLAdmin target A/R defined | **Yes** |
| Join path clear (same-row `COVERAGE_ID`) | **Yes** |
| Client scope (QuikPlan timing; not #104) | **Yes** |
| Codebook formally signed by CSO email | **Partial** — extract reading accepted for Planning; Risk may still want D4 |
| Example plans available | **Yes** (SAL four + `1960PO`) |

---

## 13. Acceptance Tests (for Validation after Dev)

1. **Universe:** Every QuikPlan row `LOANINTX ∈ {A,R}`; zero blanks/invalids (DG-QUIKPLAN-006).  
2. **Arrears set:** Exactly `{1SALOL,1SALML,1SALMI,9SLADB}` = `R` (unless D2 narrows — then assert the approved set).  
3. **Advance set:** All other plans = `A` (including eight `N` coverages and `1960PO`).  
4. **Source fidelity:** For each QuikPlan `PLAN`, mapped `LOAN_ADV_ARREARS` from PCOVR/`quikplan_source` matches codebook.  
5. **QuikLoan non-regression:** `#32` validator still PASS; `MLOANINTX` still from QuikPlan; no PLOAN A/R invent; active-loan sample `9010331768C` remains `A`.  
6. **Zero-loan SAL:** No requirement that QuikLoan contain SAL rows; absence is expected.  
7. **Accountability:** Issue #70 spot-check **IN_DATA** on full Output before Closure (G7).  
8. **Publish:** On PASS, copy modified `quikplan.csv` (and `quikloan.csv` only if any `MLOANINTX` changed) to `Output/Test_Validation/`.

---

## 14. Regression / Non-Candidate Controls

| Control | Expectation |
|---------|-------------|
| Non-SAL QuikPlan rows | `LOANINTX` unchanged at `A` |
| QuikPlan columns other than `LOANINTX` | Byte-stable / equal on non-touched fields for sample plans |
| QuikLoan principals, balances, rates, dates, `MLOANACCR` | Unchanged (#32) |
| Active loan fleet `MLOANINTX` | Remains `A` (no SAL loans) |
| #104 | No converter changes; no claim/surrender emit changes |
| #25 / #26 / #2 | Untouched |
| Historical mistranslation | No reintroduction of `22`/`2` |

**Suggested validator:** `QLA_Migration/_validate_issue70_loanintx.py` (read-only against Output + PCOVR/`quikplan_source`).

---

## 15. Rollback Plan

1. Revert Development commit(s) touching `quikplan_converter` / rulebook LOANINTX source mapping.  
2. Restore interim behavior: `_normalize_quikplan_loanintx` + rulebook default `A` (v57.89 posture).  
3. Re-batch QuikPlan (and QuikLoan if needed) → Output 141×`A`.  
4. Re-publish `Output/Test_Validation/quikplan.csv`.  
5. Keep Intake/Planning docs; mark Dev notes as rolled back — do not delete history.

---

## 16. Affected Tables / Files (Development scope — do not implement now)

| Path | Role |
|------|------|
| `qla_core/quikplan_converter.py` | Map `LOAN_ADV_ARREARS` → `LOANINTX`; keep normalize safety net |
| `QLA_Migration/Configs/Sync_Rulebook_quikplan.csv` | Wire source field + transform note; keep `SKIP_TRANSLATION` |
| `app.py` + `QLA_Migration/app.py` | `APP_VERSION` bump when code changes |
| `QLA_Migration/Output/quikplan.csv` | Emit result (after approved batch) |
| `QLA_Migration/Output/quikloan.csv` | Only if re-batch inherits plan INTX (expect **no** row value change today) |
| `QLA_Migration/_validate_issue70_loanintx.py` | New validator (Dev/Validation) |
| `Issue_Log_Items/Issue_70/*` | Notes / validation evidence |

**Do not modify for #70:** QuikLoan derivation rules (unless fallback policy changes — not recommended), #104 paths, PLOAN enrichment for `LOANINT`, QuikPlSt.

---

## 17. Recommended Risk Agent Prompt

```
Risk Agent — Issue #70: QuikPlan LOANINTX Advance/Arrears from PCOVR.LOAN_ADV_ARREARS.

Read Issue_70_Planning_Report.md, Issue_70_Intake_Summary.md, Issue_70_Dependency_Gate.md.
Quantify: codebook 0/N→A and 1→R; emit R on four SAL plans with zero loans; QuikLoan inherit (#32) with zero expected MLOANINTX flips; #104 coupling (expect none operational).
Decide whether written CSO confirm (D4) is required before Development.
No code. Recommend Go / Conditional Go / No-Go.
Preserve #2 MPOLICY, #26 MPREM, #32 QuikLoan math, #104 out of scope.
```

---

## 18. Recommended Development Task (Do Not Implement)

1. Add codebook transform: `LOAN_ADV_ARREARS` → `LOANINTX` during QuikPlan conversion (same source row as `COVERAGE_ID`).  
2. Keep `SKIP_TRANSLATION` and `_normalize_quikplan_loanintx` as invalid→`A` safety net (**preserve valid `R`**).  
3. Do **not** change QuikLoan resolver, PLOAN F/D rejection, or #104.  
4. Bump `APP_VERSION` in root `app.py` and `QLA_Migration/app.py`.  
5. Add `_validate_issue70_loanintx.py` per §13; run on full Output.  
6. On PASS: publish `quikplan.csv` to `Output/Test_Validation/`; update Implementation Notes (preserve interim history).  
7. Closure only after G7 (validator PASS + accountability IN_DATA).

---

## Appendix

- Intake: `Issue_70_Intake_Summary.md` (2026-08-02 addendum)  
- Interim emit: `Issue_70_Implementation_Notes.md` (v57.89)  
- Related: `Issue_Log_Items/Issue_32/` (esp. `Issue_32_MLOANINTX_Source_Review.md`), `Issue_104/`  
- Sources: `QLA_Migration/Source/PCOVR_Coverage_Extract_20260630.csv`, `PLOAN_*_20260630.csv`, `PPBEN_*_20260630.csv`  
- Working QuikPlan source: `plan_analysis/quikplan_source.csv` (column present)  
- Crosswalk: `QLA_Migration/Mapping/Master_Crosswalk.csv`  
- Governance: `QLA_Migration/Data_Goverence.txt` LOANINTX line; DG-QUIKPLAN-006  
