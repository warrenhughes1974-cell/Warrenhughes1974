# Issue #70 — Risk Review Report

**Issue:** #70 — QuikPlan `LOANINTX` Advance/Arrears from `PCOVR.LOAN_ADV_ARREARS`  
**Framework stage:** Risk Agent (G3)  
**Status:** **CONDITIONAL GO** — Ready for Development **after** explicit user approval  
**Fallback simulated:** Keep fleet interim `A` (v57.89) vs source map `0`/`N`→`A`, `1`→`R`  
**Generated:** 2026-08-02  
**Agent/script:** Cursor Grok 4.5 — read-only Source/Output/code verification (no production changes)

**Status note:** Risk analysis only — no production code, Output, or tracking-status changes.  
**Dependency Gate:** `Issue_70_Dependency_Gate.md` — **G2 CONDITIONAL PASS** (accepted for Risk).

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Source field is present and joinable on the QuikPlan conversion row; plan-level codebook yields a measurable **137 A / 4 R** catalog with **zero** current QuikLoan `MLOANINTX` flips; #104 settlement remains out of scope. Proceed to Development only with user approval that locks Planning defaults D1–D3 (all four SAL `R`, zero-loan catalog fidelity, `0`/`N`→`A`). Written CSO email (D4) is **not** required before Development given extract authority + zero active SAL loans; elevate D4 only if the user wants a formal client line before coding.

| Gate | Result |
|------|--------|
| **G2 Dependency** | **CONDITIONAL PASS** |
| **G3 Risk** | **CONDITIONAL GO** |
| **Development start** | **Blocked until user says Approved for Development** |

---

## 1. Current vs Proposed Mapping

| Field | Current (v57.89 interim) | Proposed | Change? |
|-------|--------------------------|----------|---------|
| QuikPlan `LOANINTX` | Force/default **A** (141/141) via `_normalize_quikplan_loanintx` + rulebook default | Map `PCOVR.LOAN_ADV_ARREARS`: `0`/`N`→`A`, `1`→`R`; blank/other→`A` + audit | **Yes** |
| QuikLoan `MLOANINTX` | #32 QuikPlan lookup + fallback `A` | **Unchanged algorithm**; inherits plan value if plan is `R` | **No** (data inherit only) |
| PLOAN `INT_METHOD` / `INTEREST_TYPE` | Rejected for A/R | Still rejected | **No** |
| #104 claim/surrender interest | Separate SME options | Out of scope | **No** |

### Codebook locked for Dev (unless user overrides)

| `LOAN_ADV_ARREARS` | `LOANINTX` |
|--------------------|------------|
| `0` | A |
| `N` | A |
| `1` | R |
| blank / other | A (fail-safe) |

**Arrears plans (expected `R`):** `1SALOL`, `1SALML`, `1SALMI`, `9SLADB`.

---

## 2. Premium / Related Fields Untouched

| Target | Source / owner | Touched? |
|--------|----------------|----------|
| QuikPlan `LOANINT` | PLOAN modal enrichment | **No** |
| QuikLoan principal/balance/accrual/dates | #32 | **No** |
| QuikLoan `MLOANINTX` resolver | #32 lookup + A fallback | **No** (algorithm) |
| `quikmstr.MMODPREM` / `quikridr.MPREM` | #26 | **No** |
| MPOLICY padding / formatter | #25 / #2 | **No** |
| #104 settlement path | SME A/B/C | **No** |
| QuikPlSt `MLOANINTX` | State override | **No** |
| Unrelated QuikPlan columns | Rulebook | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `qla_core/quikplan_converter.py` | `_normalize_quikplan_loanintx` interim; Dev maps source then keeps safety net |
| `QLA_Migration/Configs/Sync_Rulebook_quikplan.csv` | `LOANINTX` default `A`, `SKIP_TRANSLATION` |
| `plan_governance/config/quikloan_derivation_rules.json` | `mloanintx_source=QUIKPLAN_LOANINTX` |
| `qla_core/quikloan_converter.py` | `resolve_mloanintx` / plan lookup |
| `QLA_Migration/Source/PCOVR_Coverage_Extract_20260630.csv` | Authority column |
| `plan_analysis/quikplan_source.csv` + `load_quikplan_source_csv` | Conversion ingest path |
| `QLA_Migration/Mapping/Master_Crosswalk.csv` | SAL → QuikPlan PLAN |
| `QLA_Migration/Output/quikplan.csv` | Before: 141×A |
| `QLA_Migration/Output/Test_Validation/quikplan.csv` | Before publish: 141×A |
| `QLA_Migration/Output/quikloan.csv` | 356×`MLOANINTX=A` |
| `Issue_Log_Items/Issue_32/*` | QuikPlan intended for `MLOANINTX`; PLOAN F/D rejected |
| `Issue_Log_Items/Issue_104/*` | Settlement UAT — coupled note only |
| `QLA_Migration/Data_Goverence.txt` / DG-QUIKPLAN-006 | A or R required |

---

## 4. Population Analysis (read-only, 2026-08-02)

| Metric | Count | Basis |
|--------|------:|-------|
| QuikPlan rows (Output / Test_Validation) | 141 | Current before-state |
| Raw PCOVR `LOAN_ADV_ARREARS=0` | 129 | Advance |
| Raw PCOVR `LOAN_ADV_ARREARS=N` | 8 | Advance family (DISCHO*/L15/L16/L17) |
| Raw PCOVR `LOAN_ADV_ARREARS=1` | 4 | Arrears SAL* |
| **Expected after `LOANINTX=A`** | **137** | 129+8 |
| **Expected after `LOANINTX=R`** | **4** | SAL OL/ML/MULTPL/ADB |
| QuikPlan rows that would change vs Output | **4** | `1SALOL`, `1SALML`, `1SALMI`, `9SLADB` A→R |
| QuikPlan rows unchanged | **137** | Stay A |
| PLOAN data rows | 94,151 | `INT_METHOD=D` all |
| PLOAN rows with SAL* `PLAN_CODE` | **0** | No in-force SAL loans |
| PPBEN distinct policies on SAL four forms | **163** | Context only |
| QuikLoan rows that would flip to `R` today | **0** | No SAL loans to inherit |
| QuikLoan `MLOANINTX` today | 356×A | Non-regression control |

### Breakdown — Arrears candidates

| COVERAGE_ID | QuikPlan PLAN | Before | After | PLOAN loans |
|-------------|----------------|--------|-------|------------:|
| SAL OL | `1SALOL` | A | **R** | 0 |
| SAL ML | `1SALML` | A | **R** | 0 |
| SAL MULTPL | `1SALMI` | A | **R** | 0 |
| SAL ADB | `9SLADB` | A | **R** | 0 (`LOANS_AVAILABLE=N`) |

### Loader caveat (emit-neutral under codebook)

`load_quikplan_source_csv` currently shows the eight raw-`N` rows as `LOAN_ADV_ARREARS=0` (field alignment / DESCRIPTION merge). Arrears `1` rows remain correct. Because **`0` and `N` both map to `A`**, simulated catalog counts stay **137 A / 4 R**. Risk does **not** BLOCK on this; Development should map after trim/casefold and keep validator fidelity notes aware of loader vs raw PCOVR for the eight `N` rows.

---

## 5. Fallback Recommendation

| Option | QuikPlan A/R | QuikLoan impact today | Assessment |
|--------|--------------|----------------------:|------------|
| **A. Source map all four `R`** (Planning default) | 137 A / 4 R | 0 row flips | **Recommended** — catalog fidelity; measurable; lowest ambiguity vs extract |
| B. Narrow `R` to SAL OL + SAL ML only | 139 A / 2 R | 0 | Reject unless CSO narrows — leaves MULTPL/ADB wrong vs extract |
| C. Keep fleet interim `A` forever | 141 A | 0 | Reject as product truth — only rollback / waiver posture |
| D. Wait for written CSO email before any Dev | unchanged until confirm | 0 | Optional hold — **not** required by Risk given extract + zero-loan impact |

**Recommended fallback if user rejects zero-loan `R` (D3 No):** Option **C** with documented CSO waiver that fleet Advance is accepted despite four extract `1` rows — do not invent a third codebook.

**Recommended if user wants written confirm (D4 elevated):** Hold coding until one-line CSO ack of codebook + four-plan `R` list; gate stays CONDITIONAL PASS (not extract FAIL).

---

## 6. Trace Policies / Plans

| Plan / policy | LifePRO evidence | Before | Proposed | Pass? |
|---------------|------------------|--------|----------|-------|
| `1SALOL` | PCOVR `LOAN_ADV_ARREARS=1` | A | **R** | Yes (candidate) |
| `1SALML` | `=1` | A | **R** | Yes |
| `1SALMI` | SAL MULTPL `=1` | A | **R** | Yes |
| `9SLADB` | SAL ADB `=1` | A | **R** | Yes (catalog; loans N/A) |
| `1960PO` / `9010331768` | #32 UI Advance; non-`1` | A (+ QuikLoan A) | **A** | Non-candidate control |
| Example `N` (e.g. L15) | raw `N` → Advance family | A | **A** | Non-candidate control |

---

## 7. Top Changes

Not numeric. Largest (only) catalog changes: four SAL plans **A→R**. No QuikLoan monetary fields change under this issue.

---

## 8. Material Calculation Impact

| Surface | Impact |
|---------|--------|
| QuikPlan catalog timing | **Intentional** — four plans flip to Arrears |
| Active loan interest / balances | **None today** — zero SAL PLOAN rows; QuikLoan stays 356×A |
| #104 payoff interest UAT | **None from #70 emit** — do not reopen #32/#104 math; settlement mismatch remains #104’s SME choice |
| Historical `22`/`2` mistranslation | Mitigated by retaining `SKIP_TRANSLATION` + A/R normalize safety net |

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 / #2 MPOLICY padding | **Preserved** — untouched |
| Issue #26 MPREM / MMODPREM | **Preserved** — untouched |
| Issue #32 QuikLoan mapping / PLOAN F/D rejection | **Preserved** — lookup only; no principal/ACCR change |
| Issue #104 settlement options | **Out of scope** — no converter path change |
| Issue #70 interim loadability (A or R only) | **Preserved** — still A/R-only emit; expands to include valid `R` |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] Universe: every QuikPlan `LOANINTX` ∈ {`A`,`R`}; zero blanks/invalids/`2`/`22`
- [ ] Arrears set exactly `{1SALOL,1SALML,1SALMI,9SLADB}` = `R`
- [ ] All other plans = `A` (137), including eight Advance-family `N` coverages and `1960PO`
- [ ] Source fidelity: PCOVR/`quikplan_source` codebook match (allow loader `N`→`0` note if comparing post-ingest)
- [ ] QuikLoan: #32 validator still PASS; sample `9010331768C` remains `MLOANINTX=A`
- [ ] QuikLoan principals/balances/rates/dates/`MLOANACCR` unchanged
- [ ] No #104 / claims / QuikBenh changes
- [ ] Non-candidate QuikPlan columns unchanged on sample plans
- [ ] On PASS: publish modified `quikplan.csv` to `Output/Test_Validation/` (and `quikloan.csv` only if any `MLOANINTX` actually changed — expect none)
- [ ] Before Closure: G7 — issue validator PASS on full Output + accountability **IN_DATA**

**Suggested validator:** `QLA_Migration/_validate_issue70_loanintx.py` (Dev/Validation; not created in Risk).

---

## 11. Recommended Development Agent Task (do not implement until approved)

1. In QuikPlan conversion, map same-row `LOAN_ADV_ARREARS` → `LOANINTX` with codebook `0`/`N`→`A`, `1`→`R` (trim/casefold) **before** `_normalize_quikplan_loanintx`.  
2. Keep `_normalize_quikplan_loanintx` as invalid→`A` safety net; **must preserve valid `R`**.  
3. Wire rulebook Source_Field / transform note for `LOAN_ADV_ARREARS` if needed; **retain `SKIP_TRANSLATION`**.  
4. Do **not** change QuikLoan resolver, PLOAN enrichment for `LOANINT`, or any #104 path.  
5. Bump `APP_VERSION` in **both** root `app.py` and `QLA_Migration/app.py`.  
6. Add `_validate_issue70_loanintx.py` per checklist; run on full `QLA_Migration/Output/`.  
7. On PASS: publish `quikplan.csv` to `Output/Test_Validation/`; update Implementation Notes (preserve interim history).  
8. Closure only after G7.

### Affected files (blast radius)

| Path | Change type |
|------|-------------|
| `qla_core/quikplan_converter.py` | Surgical LOANINTX source map |
| `QLA_Migration/Configs/Sync_Rulebook_quikplan.csv` | Source field / note; keep SKIP_TRANSLATION |
| `app.py` + `QLA_Migration/app.py` | Version bump only |
| `QLA_Migration/_validate_issue70_loanintx.py` | New read-only validator |
| `QLA_Migration/Output/quikplan.csv` | After approved batch — 4 plans A→R |
| `QLA_Migration/Output/quikloan.csv` | Re-batch optional; expect **no** `MLOANINTX` value change today |
| `Issue_Log_Items/Issue_70/*` | Notes / validation evidence |

**Blast radius:** Low — one QuikPlan C(1) field; four plan rows flip; no active-loan inheritance today.  
**Rollback:** Revert Dev commits → restore v57.89 normalize/default-`A` posture → re-batch QuikPlan to 141×A → re-publish Test_Validation.

---

## 12. Open decisions disposition (Risk)

| ID | Planning default | Risk disposition |
|----|------------------|------------------|
| D1 `0`/`N`→`A` | Yes | **Accept for Dev** |
| D2 all four `R` | Yes | **Accept for Dev** |
| D3 zero-loan `R` | Yes | **Accept for Dev** (catalog) |
| D4 written CSO | Optional | **Not required before Dev**; user may still request |
| D5 #104 | No reopen | **Confirm out of scope** |

---

## Appendix

- Planning: `Issue_70_Planning_Report.md`  
- Dependency Gate: `Issue_70_Dependency_Gate.md` (G2 CONDITIONAL PASS)  
- Intake: `Issue_70_Intake_Summary.md` (2026-08-02)  
- Interim emit: `Issue_70_Implementation_Notes.md` (v57.89)  
- Related: Issue #32 (MLOANINTX), Issue #104 (settlement — out of scope)

---

## Pre-Development approval required

**Stop here.** Do not start Development until the user explicitly approves (e.g. “Approved for Development”) with the Conditional Go conditions above accepted or overridden in writing.
