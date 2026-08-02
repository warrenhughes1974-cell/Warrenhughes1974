# Issue #70 — Dependency Gate

**Issue:** #70 — QuikPlan `LOANINTX` Advance/Arrears authority  
**Framework stage:** Dependency Gate (G2)  
**Generated:** 2026-08-02  
**Re-verified:** 2026-08-02 (pre-Development gate + Risk handoff)  
**Status:** **CONDITIONAL PASS**  
**Basis:** `Issue_70_Planning_Report.md`, `Issue_70_Intake_Summary.md` (2026-08-02), independent Source/Output/code read-only checks  

**G2 — Dependencies Satisfied:** **CONDITIONAL PASS** (source + join + target Met; residual CSO choices are Risk/approval items, not extract gaps).  
**Tracking sheet:** not updated this session (docs only).

---

## 1. Checklist

### Source data

| Check | Met? |
|-------|------|
| Required LifePRO extract(s) present in `QLA_Migration/Source/` | **Met** — `PCOVR_Coverage_Extract_20260630.csv` column `LOAN_ADV_ARREARS` (index 87 / Excel CJ); working copy also on `plan_analysis/quikplan_source.csv` |
| Extract row count > 0 | **Met** — 141 coverage data rows; raw PCOVR value counts **`0`=129, `N`=8, `1`=4** |
| Column headers documented (not just Excel letters) | **Met** — `LOAN_ADV_ARREARS` named header |
| Extract date/version matches batch under test | **Met** — 20260630 package (same family as current Output evidence) |
| Re-extract required? | **N/A** — not required for planned map |

### Field definitions

| Check | Met? |
|-------|------|
| QLAdmin target table confirmed (Help PDF / schema) | **Met** — QuikPlan `LOANINTX` C(1) in `schema_manifest.json` / `QUIKPLAN_SCHEMA` |
| QLAdmin target field semantics confirmed | **Met** — `A`=Advance, `R`=Arrears (governance + #32 Help alignment) |
| LifePRO source field semantics confirmed | **Partial** — CSO/Intake reading (`0`/`N`→Advance, `1`→Arrears) accepted for Planning; formal LifePRO field-help text not in repo |
| Transformation notes identified | **Met** — codebook + invalid→`A` safety net; keep `SKIP_TRANSLATION` |

### Client clarification

| Check | Met? |
|-------|------|
| Scope boundary agreed (in / out) | **Met** — QuikPlan `LOANINTX` + inherit via #32; not PLOAN A/R invent; **#104 settlement out of scope** |
| Business rule for edge cases (fallback, blank, zero) | **Partial** — Planning defaults D1–D3 documented; CSO may still narrow D2 or reject zero-loan `R` (D3) |
| Retention / filtering rules | **Met** — all QuikPlan rows get A/R; do not suppress `R` via `LOANS_AVAILABLE` |
| UAT acceptance criteria stated | **Met** — Planning §13 (4×`R`, 137×`A`, #32 non-regression) |

### Evidence

| Check | Met? |
|-------|------|
| Example policies / plans identified | **Met** — Arrears plans `1SALOL` / `1SALML` / `1SALMI` / `9SLADB`; Advance control `1960PO` / `9010331768` |
| Screenshots or docx support client claim | **Met (partial)** — #32 Advance UI on `9010331768`; Chris invalid-`2` history in Intake |
| Before-state measurable from current output | **Met** — `Output/quikplan.csv` and `Output/Test_Validation/quikplan.csv` both **141/141 = A** (incl. all four SAL plans) |

### Regression guards

| Check | Met? |
|-------|------|
| Plan preserves Issue #25 MPOLICY padding | **Met** — plan-grain field only |
| Plan preserves Issue #26 MPREM mapping | **Met** — no ridr/premium touch |
| Plan does not alter unrelated rulebooks | **Met** — QuikPlan `LOANINTX` only; QuikLoan derivation rules unchanged |

### Issue-specific dependencies (re-verified 2026-08-02)

| Check | Met? | Evidence |
|-------|------|----------|
| PCOVR `LOAN_ADV_ARREARS=1` set | **Met** | SAL OL, SAL ML, SAL MULTPL, SAL ADB only |
| Master_Crosswalk covers SAL → QuikPlan plans | **Met** | `SAL OL→1SALOL`, `SAL ML→1SALML`, `SAL MULTPL→1SALMI`, `SAL ADB→9SLADB` |
| Same-row join path in converter | **Met** | `convert_quikplan_row` iterates `src_row` (has `COVERAGE_ID` + `LOAN_ADV_ARREARS`); PLAN via existing crosswalk/overlay — no policy-number join |
| PLOAN rejected as A/R source | **Met** | `INT_METHOD=D` on 94,151 data rows; **0** SAL `PLAN_CODE` rows |
| Zero loans on Arrears forms | **Met** | PPBEN: **163** distinct policies on SAL OL/ML/MULTPL/ADB; **0** of those plan codes in PLOAN |
| #32 QuikLoan lookup remains `MLOANINTX` authority | **Met** | `mloanintx_source=QUIKPLAN_LOANINTX`; Output QuikLoan **356×A** today |
| Written CSO email confirming codebook | **Missing (optional)** | Planning D4; not a Source-folder FAIL |

### Loader note (not a gate FAIL)

`load_quikplan_source_csv` (DESCRIPTION comma-merge) currently surfaces the eight raw-`N` coverages as `LOAN_ADV_ARREARS=0` with `LOANS_AVAILABLE=N`, while raw PCOVR/`csv.DictReader` show `LOAN_ADV_ARREARS=N`. The four `1` (Arrears) rows remain correct under the loader. Under the proposed codebook **`0` and `N` both → `A`**, expected emit remains **137 A / 4 R**. Development must not treat raw-`N` fidelity as a second A/R code without an explicit codebook change; validator may compare after codebook or against raw PCOVR.

---

## 2. Gate status

**CONDITIONAL PASS** — Development design is unblocked on **source + target + join**. Residual CSO choices (D1–D4) are **Risk / approval** items, not missing extracts.

| Gate | Result |
|------|--------|
| **G2** | **CONDITIONAL PASS** |
| Hard extract/join blocker? | **No** |
| Advance to Risk? | **Yes** |

Do **not** start Development until:

1. Risk Agent returns Go or Conditional Go, **and**  
2. User gives explicit Development approval.

If Risk elevates D4 (written CSO confirm) to mandatory, treat that as a soft client clarification hold before coding — **not** a Source-folder FAIL / BLOCKED.

---

## 3. Exact residual decisions (not extract blockers)

| ID | Item | Owner | Blocks Dev? |
|----|------|-------|-------------|
| D1 | Confirm `0` and `N` both → `A` | CSO / Risk | Only if Risk rejects Planning default |
| D2 | All four SAL `R` vs OL/ML only | CSO / Risk | Only if Risk requires narrow set before code |
| D3 | Emit `R` with zero loans | CSO / Risk | Planning default Yes |
| D4 | Written CSO confirm vs extract authority | Risk | Optional unless Risk elevates |
| D5 | #104 coupling | Risk | Planning: no #70 reopen |

---

## 4. Recommended issue status (tracking — **not** applied this session)

Per user instruction, **do not** change the tracking sheet this session. Suggested later wording after Risk + Dev approval:

`Ready for Development` (or retain interim “Implemented v57.89 — Awaiting CSO” only if D4 is elevated to a hard written-confirm hold).

---

## 5. Next step

Risk Agent — Issue #70 (same session / parent chain).

**Stop after Risk readout** — do not start Development without explicit user approval.
