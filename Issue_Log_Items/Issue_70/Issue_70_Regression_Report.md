# Issue #70 — Regression Report

**Issue:** #70 — QuikPlan `LOANINTX` from `PCOVR.LOAN_ADV_ARREARS` (`0`/`N`→`A`, `1`→`R`)  
**Framework stage:** Regression Agent (Stage 7 / G6)  
**Engine version:** **v58.50**  
**Baseline:** `Issue_Log_Items/Issue_70/evidence/quikplan_before_v5850_rebatch.csv` + `quikloan_before_v5850_rebatch.csv` (captured 2026-08-02 ~10:41, pre v58.50 re-batch; fleet was still 141×`LOANINTX=A`)  
**Output directory:** `QLA_Migration/Output/` (post v58.50 full batch 2026-08-02 ~11:14–11:17)  
**Validation prerequisite:** `Issue_70_Validation_Report.md` — **PASS**  
**Generated:** 2026-08-02  
**Verdict:** **PASS** (Issue #70 intended delta clean; seven `PLANVALOPT` flips **explained** as Issue A3 / R7B default-only PVO clear correcting stale before-snapshot inconsistency — **not** caused by #70)

**Status note:** Regression only — no production-code changes; issue tracking status **not** updated; **not** Closed. Closure / G7 git release remain separate.

---

## Commands Run

```text
# 1) Focused unit tests (includes A3 default-only PVO clear regression)
python Issue_Log_Items/Issue_70/test_issue70_loanintx_map.py -v
# Result: OK — 6 tests

# 2) Full Output Issue #70 validator (reconfirm after Validation)
python QLA_Migration/_validate_issue70_loanintx.py
# Result: PASS — A=137 R=4; SAL traces OK; PCOVR mismatches=0

# 3) Before/after field-level diff (read-only Python)
# Baseline: evidence/quikplan_before_v5850_rebatch.csv vs Output/quikplan.csv
#           evidence/quikloan_before_v5850_rebatch.csv vs Output/quikloan.csv
# Result: 11 plans differ — 4 LOANINTX only + 7 PLANVALOPT only; QuikLoan identical

# 4) Prior-fix validators
python tools/validators/validate_mpolicy_width.py
# Result: PASS — MPOLICY exactly 11 chars (Issue #2 successor to #25 width gate)

python tools/validators/validate_issue26_mprem.py
# Result: FAIL (environmental) — missing dated Source extracts
#   PPBEN_PolicyBenefit_Extract_20260530.csv / PPOLC_PolicyMaster_Extract_20260530.csv
# Not attributable to Issue #70; batch used PPOLC_…_20260630.csv

# 5) Fleet accountability (registry does not yet include #70)
python tools/validators/validate_issue_log_accountability.py
# Result: exit 1 — unrelated GAPs (#76 candidate count, #58/#21F trace keys, etc.)
# #70 not in validator_jobs; see §8 G7 spot-check instead

# 6) Batch log evidence
# QLA_Migration/Logs/_full_batch_test_log.txt
#   [11:14:02] Initializing QUIKConvert v58.50
#   [11:17:14] Issue #70 LOANINTX emit: A=137 R=4
```

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|-----------|-----------------|
| QuikPlan `LOANINTX` | Exactly 4 plans A→R: `1SALOL`, `1SALML`, `1SALMI`, `9SLADB` |
| QuikPlan other fields | No Issue #70-driven change |
| QuikLoan | Row count / `MLOANINTX` unchanged (356×A; no current R-plan loans) |
| Other tables | No #70-driven row/schema change |

---

## 2. Row Count Comparison

| Table | Before snapshot | After (v58.50 Output) | Delta | OK? |
|-------|----------------:|----------------------:|------:|-----|
| quikplan | 141 | 141 | 0 | Yes |
| quikloan | 356 | 356 | 0 | Yes |
| quikmstr | (not in #70 baseline) | 5083 | — | N/A (fleet intact) |
| quikridr | — | 6934 | — | N/A |
| quikprmh | — | 209480 | — | N/A |
| quikclid | — | 32285 | — | N/A |
| quikclnt | — | 13597 | — | N/A |

Schema: quikplan 79 columns, identical order before/after.

---

## 3. Intended vs Non-Intended Deltas

### 3.1 Intended — Issue #70 `LOANINTX` (PASS)

| Plan | Before | After | PCOVR / expected | OK? |
|------|--------|-------|------------------|-----|
| `1SALOL` | A | **R** | Arrears | Yes |
| `1SALML` | A | **R** | Arrears | Yes |
| `1SALMI` | A | **R** | Arrears | Yes |
| `9SLADB` | A | **R** | Arrears | Yes |
| Control `1960PO` | A | A | Advance | Yes |

| Control | Result |
|---------|--------|
| Fleet distribution | **137 A / 4 R** |
| Non-candidate `LOANINTX` changes | **0** (all other 137 plans unchanged vs before) |
| PCOVR fidelity mismatches | **0** (validator) |
| Rulebook | `Source_Field=LOAN_ADV_ARREARS`, `Default_Value=A`, `SKIP_TRANSLATION` retained |

### 3.2 QuikLoan / R-plan loan controls (PASS)

| Check | Before | After | OK? |
|-------|-------:|------:|-----|
| Row count | 356 | 356 | Yes |
| `MLOANINTX` distribution | 356×A | 356×A | Yes |
| Any loan field diffs (row-aligned) | — | **0** | Yes |
| Loan rows on R-base `MPLAN` (`1SAL*`, `9SLADB`) | 0 | 0 | Yes |

### 3.3 Non-intended — seven `PLANVALOPT` Y→N (**EXPLAINED — not #70**)

| Plan | Before | After | Only field changed? |
|------|--------|-------|---------------------|
| `121PUA` | Y | N | Yes |
| `165PUA` | Y | N | Yes |
| `170PUA` | Y | N | Yes |
| `185PUA` | Y | N | Yes |
| `1970PA` | Y | N | Yes |
| `1OLPUA` | Y | N | Yes |
| `1POPUA` | Y | N | Yes |

**Attribution (root cause):** Issue **A3** default-only PVO clear in `qla_core/quikplan_rate_variation_flags.py`, applied on every full product/rate rebuild via R7B enrichment — **not** Issue #70 `LOANINTX` mapping.

Evidence:

1. **Exact set match** — these seven plans are the entire `DEFAULT_ONLY_PLAN_CODES` frozenset:

```text
DEFAULT_ONLY_PLAN_CODES = frozenset({
    "121PUA", "170PUA", "165PUA", "185PUA", "1OLPUA", "1POPUA", "1970PA",
})
```

2. **Before-snapshot was already R7B-inconsistent** — all seven had `PLANVALOPT=Y` with **every** `*VARY*` flag `N` (violates R7B rule: `PLANVALOPT=Y` iff any `*VARY*` is Y). After re-batch: `PLANVALOPT=N` and all `*VARY*=N` (consistent). No other columns changed on those plans.

3. **No real factor rates** — `Output/variation_code_audit.csv`: `Source_Table=NONE`, evidence `no matching rate rows` for all seven. They appear only as **default stub keys** in `Output/rates/QuikPl*.csv` (e.g. `GENDER=0`, `UWCLASS=00`, `BAND=00`, `EFFDATE=19000101`) and are **absent** from factor tables (`QuikGps` / `QuikCvs` / `QuikTvs`).

4. **Code path** — `enrich_quikplan_rows` ends with `apply_default_only_pvo_clear` so factor-table enablement cannot reactivate these plans. Rulebook `PLANVALOPT` default is `Y` with `RATE_DERIVED_R7B_OVERRIDES`; R7B/A3 overrides that default when there is no real rate segmentation.

5. **Rated PUA controls preserved** — `261PUA`, `265PUA`, `280PUA`, `1960OL` remain `PLANVALOPT=Y` with real `*VARY*` evidence (e.g. `GDVARYCV`/`GDVARYTV=Y`). Unit test `test_default_only_pvo_clear_preserves_rated_control` covers this.

6. **Not caused by #70** — `#70` only maps `LOAN_ADV_ARREARS`→`LOANINTX` and normalizes invalid→`A` (preserving `R`). No `PLANVALOPT` writes in the #70 path. Collateral appears because Validation required a **full** v58.50 re-batch (product + rates + R7B), which re-applied A3.

7. **Stale Output drift corrected** — before snapshot (pre-rebatch Output) carried rulebook-default / stale `PLANVALOPT=Y` on default-only PUA plans; v58.50 rebuild corrected them. This is concurrent product/rate (Issue A / R7B) behavior, not unexplained drift and not a #70 defect.

**Fleet PLANVALOPT counts:** before 134 Y / 7 N → after 127 Y / 14 N (+7 N exactly the default-only set).

---

## 4. Prior Issue Fix Regression

### Issue #25 / #2 — MPOLICY width

| Check | Result |
|-------|--------|
| `validate_mpolicy_width.py` | **PASS** (exactly 11 characters — Issue #2 convention) |
| Sample keys present | `9010143726C`, `901222DCC`, etc. FOUND |

### Issue #26 — MPREM mapping

| Check | Result |
|-------|--------|
| `validate_issue26_mprem.py` | **FAIL (environmental)** — hardcoded 20260530 Source extracts missing; current batch uses 20260630 |
| Attribution to #70 | **No** — #70 did not touch premium mapping |

### QuikLoan (#32 inherit)

| Check | Result |
|-------|--------|
| Algorithm untouched; emit identical to before snapshot | **PASS** |

---

## 5. Schema Integrity (AGENTS.md)

| Check | Result |
|-------|--------|
| Field order preserved (quikplan 79 cols) | **PASS** |
| Field types/lengths preserved | **PASS** (A/R alphabet for `LOANINTX`; Y/N for `PLANVALOPT`) |
| No new blank MRIDRID | N/A (plan catalog) |
| QLA formatting / `SKIP_TRANSLATION` | **PASS** (no A→22 mistranslation) |

---

## 6. Batch / Fleet Checks

| Check | Result |
|-------|--------|
| Full batch completed (v58.50) | **Yes** — `QLA_Migration/Logs/_full_batch_test_log.txt` |
| Batch emit line | `Issue #70 LOANINTX emit: A=137 R=4` |
| `validate_issue70_loanintx.py` on full Output | **PASS** |
| `Output/Test_Validation/quikplan.csv` | Present (published at Validation) |
| Unit tests | **PASS** (6) |

---

## 7. Output-root hygiene (`qla-output-folder.mdc`)

**Limitation — documented, not cleaned this session** (broad relocation not required for #70 proof; Validation already noted Auto-review block).

Non-load artifacts still under `QLA_Migration/Output/` root:

| Artifact | Should relocate to |
|----------|--------------------|
| `claims_*validation*.csv`, `claims_review_hold_manifest.csv`, `cso_mortality_crosswalk_qa.csv`, `variation_code_audit.csv` | `QLA_Migration/Reports/` |
| `claims_uat_dbf/`, `claims_uat_staging/` | `QLA_Migration/Staging/` |

Load tables (`quik*.csv`), `rates/`, and `Test_Validation/` are present.

| Question | Answer |
|----------|--------|
| Blocks Issue #70 Regression verdict? | **No** — #70 proof is on `quikplan.csv` / `quikloan.csv` |
| Blocks Closure G7 Output accountability for #70? | **No** for field proof; **Yes** for clean client load-package handoff until hygiene cleanup |
| Action taken | Document only (no broad move) |

---

## 8. G7 Accountability Spot-Check (Issue #70)

`validate_issue_log_accountability.py` **does not yet register `#70`** in `validator_jobs`. Full run completed with unrelated fleet GAPs (not #70-scoped). Per framework, Issue #70 G7 uses the dedicated Output validator + spot-check:

| Check | Result |
|-------|--------|
| `validate_issue70_loanintx.py` on full `Output/` | **PASS** → treat as **IN_DATA** for #70 |
| Fleet `LOANINTX` | 137 A / 4 R; arrears set exact |
| QuikLoan `MLOANINTX` | 356×A; 0 R-plan loan rows |
| `Test_Validation/quikplan.csv` | Published |
| Mark Closed? | **No** — status untouched; Closure still owns tracking + git release + registry add |

**Closure follow-ups (not done here):**

1. Add `#70` → `QLA_Migration/_validate_issue70_loanintx.py` to accountability `validator_jobs`.
2. Optional Output-root hygiene before client package.
3. User approval before Closed / git push.

---

## 9. Failures

| # | Description | Blast radius | Action |
|---|-------------|--------------|--------|
| — | None for Issue #70 regression controls | — | — |
| env | #26 validator missing 20260530 extracts | Prior-fix script only | Use current extracts / update validator paths outside #70 |
| fleet | Accountability unrelated GAPs (#76, #58, #21F, …) | Other issues | Out of #70 scope |

---

## 10. Recommendation

- [x] **G6 Regression PASS** for Issue #70 — intended 4×`LOANINTX` A→R only among #70 candidates; non-candidates unchanged; QuikLoan stable
- [x] Seven `PLANVALOPT` Y→N flips **explained** (Issue A3 `DEFAULT_ONLY_PLAN_CODES` / R7B on full rebuild; before snapshot was inconsistent) — **do not** treat as unexplained → no CONDITIONAL/BLOCKED for #70
- [ ] Advance to **Closure Agent** when user requests (still requires G7: accountability registry entry for #70, status/Notes update, commit/push rules) — **do not auto-close**
- [ ] Return to Development — **not required** for #70

**Verdict line:** Issue #70 Regression **PASS**. Collateral `PLANVALOPT` changes are concurrent Issue A3 correction of stale Output, not a #70 regression failure.

---

## Appendix — Diff inventory (quikplan before → after)

| Plans changed | Fields |
|--------------:|--------|
| 4 | `LOANINTX` only (`1SALOL`,`1SALML`,`1SALMI`,`9SLADB`) |
| 7 | `PLANVALOPT` only (default-only PUA set) |
| 0 | Any other field |
| 0 | QuikLoan any field |

Evidence paths:

- `Issue_Log_Items/Issue_70/evidence/quikplan_before_v5850_rebatch.csv`
- `Issue_Log_Items/Issue_70/evidence/quikloan_before_v5850_rebatch.csv`
- `Issue_Log_Items/Issue_70/evidence/issue70_validation_summary.json`
- `QLA_Migration/Logs/_full_batch_test_log.txt`
- `QLA_Migration/Output/variation_code_audit.csv`
- `qla_core/quikplan_rate_variation_flags.py` (`DEFAULT_ONLY_PLAN_CODES`, `apply_default_only_pvo_clear`)
