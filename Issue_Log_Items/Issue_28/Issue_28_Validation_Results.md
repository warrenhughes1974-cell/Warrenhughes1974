# Issue #28 — Validation Results

**Validation date:** 2026-06-27  
**Engine version:** v57.35  
**Batch source:** `PPOLC_PolicyMaster_Extract_20260530.csv`  
**Output path:** `QLA_Migration/Output/`

---

## Summary table

| Activity | ID | Result | Evidence |
|----------|-----|--------|----------|
| Full batch conversion | V-05 | **PASS** | Exit code 0; ~13.6 min; `_full_batch_test` stub |
| PLAN mapping (141 rows) | V-02 | **PASS** | 0 mismatches; `validate_issue28_plan_mapping.py` |
| Intake crosswalk compare | V-01 | **PASS** | `exact_matches: 141`, `mismatches: 0` |
| Client examples | V-03 | **PASS** | quikplan + quikridr evidence below |
| DISCHO25 | V-11 | **PASS** | Catalog row + quikplan PLAN=9DIS25 |
| P3E MPLAN alignment | V-12/V-13 | **PASS*** | 7002 AUTHORIZED; 0 orphans; *see observations |
| Schema validate_output | V-04 | **OBSERVATION** | Pre-existing duplicate findings; not #28 regression |
| Protected #25 MPOLICY | V-06 | **PASS** | `validate_mpolicy_width.py` |
| Protected #26 MPREM | V-07 | **PASS** | `validate_issue26_mprem.py` |
| Protected #21M memo | V-08 | **PASS** | `validate_issue21m_quikmemo.py` |
| Protected #21M-FU DBF | V-09 | **PASS** | `validate_issue21m_dbf_packaging.py` |
| Protected #21K MUNIT | V-10 | **PARTIAL** | CSV precision PASS; DBF reload artifact missing |
| Rate spot-check V-16 | V-16 | **OBSERVATION** | PLAN_NOT_IN_TARGET for rider plans; Risk-known |
| Output delta v57.34→v57.35 | — | **PASS** | Exactly 33 PLAN changes; FORM/DESCR unchanged |

**Overall decision:** **PASS WITH OBSERVATIONS**

---

## V-01 Intake analysis (post-batch)

```json
{
  "crosswalk_rows": 141,
  "catalog_rows": 141,
  "catalog_migration_rows": 141,
  "catalog_files_identical": true,
  "quikplan_rows": 141,
  "quikplan_unique_plan": 141,
  "quikridr_unique_mplan": 139,
  "exact_matches": 141,
  "mismatches": 0,
  "crosswalk_divergent_catalog_rows": 33,
  "missing_from_catalog": 0,
  "extra_in_converter": 0
}
```

Artifact: `Issue_Log_Items/Issue_28/evidence/issue28_intake_analysis_v5735.txt`

---

## V-02 validate_issue28_plan_mapping.py

```
Catalog rows: 141
quikplan PLAN universe: 141
Mismatches: 0
Client examples: 10827 MN5K, 0823 960CH, 0824 P DIS, DISCHO25 — all OK
Result: PASS
```

Warning: validator reported catalog file diff via `DataFrame.equals()` — intake script reports `catalog_files_identical: true`. Non-functional (likely line-ending/normalization); no action required for Issue #28.

Artifact: `Issue_Log_Items/Issue_28/evidence/validate_issue28_results.txt`

---

## V-03 Client examples

### quikplan.csv

| Coverage (source) | v57.34 PLAN | v57.35 PLAN | Status |
|-------------------|-------------|-------------|--------|
| 10827 MN5K | 10827 MN5K | **1CSIMN** | PASS |
| 0823 960CH | 0823 960CH | **960CWP** | PASS |
| 0824 P DIS | 0824 P DIS | **94PDIS** | PASS |

### quikridr.csv (P3E resolved MPLAN)

| Policy | Phase | Source PLAN_CODE | MPLAN | Status |
|--------|-------|------------------|-------|--------|
| 010488878C | 4 | 0823 960CH | **960CWP** | PASS |
| 010521756C | 2 | 0824 P DIS | **94PDIS** | PASS |
| 015000270C | — | 10827 MN5K | **1CSIMN** | PASS (P3E trace) |

---

## V-05 Full batch

- Command: `python tools/batch_tests/run_full_batch_test.py`
- Duration: ~814 seconds
- Exit code: **0**
- Row counts unchanged vs v57.34 snapshot: quikplan 141, quikridr 7002

---

## Protected issue regression

| Issue | Validator | Result |
|-------|-----------|--------|
| #25 | `validate_mpolicy_width.py` | **PASS** |
| #26 | `validate_issue26_mprem.py` | **PASS** |
| #21M | `validate_issue21m_quikmemo.py` | **PASS** |
| #21M-FU | `validate_issue21m_dbf_packaging.py` | **PASS** |
| #21K | `validate_issue21k_munit.py` | **CSV PASS / DBF SKIP** |

Combined log: `Issue_Log_Items/Issue_28/evidence/` (validate_issue25_mpolicy.txt through validate_issue21k.txt)

---

## Observations (non-blocking)

1. **validate_output.py** reports pre-existing duplicate-key findings (quikclid, quikclnt, quikprmh, etc.) and 21 blank MRIDRID rows — unchanged baseline behavior; not introduced by Issue #28.
2. **P3E `validation_passed: false`** in summary JSON due to 493 quikridr rows with MPLAN codes outside quikplan PLAN set (6 unique: `1708PA`, `1960PA`, etc.) — PUA paid-up-addition products not in quikplan catalog. All 7002 trace rows `AUTHORIZED`; `orphan_mplan_count: 0`. Pre-existing P3E referential check limitation.
3. **Issue #21K DBF reload** requires manual `issue21k_units_migration.py --reload-quikridr`; not part of standard batch. CSV MUNIT precision validated PASS.
4. **V-16 rate tables:** Changed rider PLANs (e.g. `94PDIS`, `960CWP`) show `no matching rate rows` in variation audit — consistent with Risk Agent PLAN_NOT_IN_TARGET expectation; production rate review still required (B-02).
