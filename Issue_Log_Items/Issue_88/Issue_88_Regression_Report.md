# Issue #88 — Regression Report

**Issue:** #88 — Blank `ANN_PREM_PER_UNIT` fallback loads full `MODE_PREMIUM` into Prem/Unit  
**Framework stage:** Regression Agent (G6)  
**Engine version:** v58.23  
**Baseline:** Risk sim change set (`evidence/issue88_mprem_simulated_changes.csv`) + source reconstruction of pre-#88 rule (blank ANN → full `MODE_PREMIUM`); schema vs `Archive/Output_midyear_20260715_pre_YE_meeting/quikridr.csv`  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-07-21  
**Model:** Cursor Grok 4.5 (locked)  
**Evidence:** `Issue_Log_Items/Issue_88/evidence/issue88_mprem_regression_summary.json`  
**Verdict:** **PASS**

> Note: An earlier draft in this folder addressed a different #88 topic (ISWL rate package Issc/Uint). This report is for the current tracking-sheet #88 (MPREM unit fallback). Rate-package evidence remains under `evidence/issue88_regression_summary.json` and is out of scope for this verdict.

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|-----------|-----------------|
| `quikridr.MPREM` | Blank-ANN rows: full MODE → annualized MODE ÷ units (~1,850 intentional) |
| Populated ANN → MPREM (#26) | **No change** |
| `quikmstr.MMODEPREM` / Mode Prem | **No change** |
| Other `quikridr` columns | **No intentional change** |
| Other policy tables | **No change** from #88 logic (row counts stable) |

---

## 2. Row Count Comparison

| Table | After | Archive midyear ref | Delta vs archive | OK? |
|-------|------:|--------------------:|-----------------:|:---:|
| quikridr | 6,934 | 6,934 | 0 | **Yes** |
| quikmstr | 5,083 | — | — | Stable (not #88 target) |
| quikprmh | 209,470 | — | — | Untouched by #88 rebatch (mtime earlier) |
| quikplan | 141 | — | — | Untouched |
| quikclid | 32,285 | — | — | Untouched |
| quikclnt | 13,597 | — | — | Untouched |

No pre-#88 Output snapshot existed (rebatch overwrote Output). Row identity: 6,934 joined PPBEN↔quikridr keys unchanged vs Validation.

---

## 3. Non-Target / Change-Set Diff

Source reconstruction (pre-#88 = ANN if populated else full `MODE_PREMIUM`):

| Cohort | Count | Result |
|--------|------:|--------|
| Joined rows | 6,934 | — |
| Populated ANN — MPREM unchanged | **3,775** | **PASS** (0 bad changes) |
| Blank ANN — MPREM changed (intentional) | **1,845** | **PASS** |
| Blank ANN — MPREM unchanged (units/mode already ≈ per-unit) | 1,314 | OK |
| Rule mismatches vs annualized formula | **0** | **PASS** |

Risk sim CSV (1,850 candidate rows):

| Check | Result |
|-------|--------|
| Missing from Output | 0 |
| Match Output using **raw** proposed (pre-annualize draft) | 837 (expected shortfall) |
| Match Output using **annualized** proposed (Risk Conditional Go) | **1,850 / 1,850** |

`MMODEPREM` spot samples still hold **policy modal** totals (not per-unit):  
`010779727C`=2930.75, `010826903C`=5000.00, `010897303C`=6887.88, `010718309C`=12.25.

---

## 4. Prior Issue Fix Regression

### Issue #25 — MPOLICY padding

| Check | Result |
|-------|--------|
| `tools/validators/validate_mpolicy_width.py` | **PASS** (all MPOLICY exactly 10 chars on checked tables) |
| Sample consistency mstr/clid/ridr | PASS |

### Issue #26 — MPREM mapping

| Check | Result |
|-------|--------|
| `validate_issue26_mprem.py` | **N/A / blocked** — hard-coded dated extracts `*_20260530.csv` missing (environmental) |
| Equivalent #26 traces via #88 validator / Output | **PASS** — 13.20 / 10.96 / 9.12 |
| Populated ANN cohort unchanged | **PASS** — 3,775 / 0 drift |
| `MMODEPREM` unchanged (anchor + samples) | **PASS** |

---

## 5. Schema Integrity (AGENTS.md)

| Check | Result |
|-------|--------|
| Field order vs midyear archive quikridr | **PASS** (40 cols identical) |
| Row count vs archive | **PASS** (6,934) |
| New blank MRIDRID | **PASS** — 0 blank |
| QLA formatting (Prem/Unit decimals) | Preserved (e.g. 5.8615) |

---

## 6. Batch / Fleet Checks

| Check | Result |
|-------|--------|
| Full fleet rebatch | Partial — `quikridr` rebatched under v58.23; other tables from same-day Output |
| Issue #88 validator | PASS (G5) |
| `validate_mpolicy_width.py` | PASS |
| Audit anomalies | None for #88 scope |

---

## 7. Failures (if any)

None for G6 scope.

---

## 8. Recommendation

- [x] Advance to **Closure Agent** / **Ready for Client UAT**
- [ ] Return to **Development Agent**

**Status:** **G6 PASS — Ready for Closure** (client UAT already exercised via 2026-07-21 QLA valuation re-run)

**Closure reminder (G7):** Wire Issue #88 into `validate_issue_log_accountability.py` (or document IN_DATA via #88 validator) before Closed — accountability script does not yet list #88.

---

## Appendix

- `evidence/issue88_mprem_regression_summary.json`
- `evidence/issue88_mprem_simulated_changes.csv` (Risk; annualize proposed before comparing)
- `evidence/issue88_mprem_validator_stdout.txt`
