# Issue 21M — QUIKMEMO Regression Report

**Issue:** 21M — Policy Notes / ENS → QUIKMEMO  
**Framework stage:** Regression Agent (Stage 6)  
**Engine version:** v57.32  
**Baseline:** `QLA_Migration/Output/_issue21m_before/` (pre-21M batch snapshot)  
**Output directory:** `QLA_Migration/Output/`  
**Batch log:** `QLA_Migration/Output/_full_batch_test_log.txt` (2026-06-26, exit 0)  
**Generated:** 2026-06-26  
**Verdict:** **PASS** (fleet regression) / **CONDITIONAL GO** (Client UAT — CSV ready; DBF load blocked)

---

## Executive Summary

The greenfield `quikmemo` pipeline **does not regress** any existing conversion output. All six baseline regression tables are **byte-identical** before and after the v57.32 full batch. Issues **#25** and **#26** remain preserved.

The Validation Agent DBF/FPT warning is **resolved**: DBF generation succeeds, but **`_run_output_hygiene()` splits `quikmemo.dbf` and `quikmemo.dbt` into different folders**, rendering the memo table unusable for QLAdmin load until a surgical fix is applied.

| Surface | Verdict |
|---------|---------|
| Existing table regression | **PASS** |
| quikmemo.csv correctness | **PASS** |
| Issue #25 / #26 preservation | **PASS** |
| DBF/FPT pair for UAT load | **FAIL** (split by output hygiene) |
| **Client UAT (CSV review)** | **GO** |
| **Client UAT (DBF load)** | **NO-GO** until Dev fix |

---

## 1. Scope of Change (expected)

| Component | Expected impact | Actual |
|-----------|-----------------|--------|
| `quikmemo` (new) | +29,279 rows | ✓ |
| quikmstr / quikridr / quikprmh / quikplan / quikclid / quikclnt | No change | ✓ byte-identical |
| MPOLICY / MEMOKEY padding (#25) | Preserved | ✓ |
| MPREM / MMODPREM / MVPU / MUNIT (#26) | Preserved | ✓ |

---

## 2. Row Count Comparison

| Table | Before | After | Delta | Byte-identical | OK? |
|-------|-------:|------:|------:|:--------------:|:---:|
| quikmstr | 5,083 | 5,083 | 0 | Yes | ✓ |
| quikridr | 7,002 | 7,002 | 0 | Yes | ✓ |
| quikprmh | 205,577 | 205,577 | 0 | Yes | ✓ |
| quikplan | 141 | 141 | 0 | Yes | ✓ |
| quikclid | 46,753 | 46,753 | 0 | Yes | ✓ |
| quikclnt | 13,846 | 13,846 | 0 | Yes | ✓ |
| quikactg | — | 87 | — | n/a | ✓ (same batch) |
| quikagts | — | 4,843 | — | n/a | ✓ (same batch) |
| quikbenf | — | 5,870 | — | n/a | ✓ (same batch) |
| quikdvdp | — | 5,083 | — | n/a | ✓ (same batch) |
| quikdvpr | — | 31 | — | n/a | ✓ (same batch) |
| **quikmemo** | **0** | **29,279** | **+29,279** | n/a | ✓ (intentional) |

CSV: `Issue_Log_Items/Issue_21M/Issue_21M_Regression_Row_Counts.csv`

---

## 3. quikmemo.csv Correctness

| Check | Expected | Actual | OK? |
|-------|----------|--------|:---:|
| Total rows | 29,279 | 29,279 | ✓ |
| PNOTE (`[PNOTE]`) | 6,003 | 6,003 | ✓ |
| PENSE (`[ENS]`) | 23,276 | 23,276 | ✓ |
| Skipped blank PNOTE | 30 | 30 | ✓ |
| Orphan policies | 0 | 0 | ✓ |
| MEMOKEY width ≠ 10 | 0 | 0 | ✓ |
| Text-only deduplication | None | None (emit = 6,003 + 23,276) | ✓ |
| ENS_KEY_TYPE filter | P only | 0 non-P in source | ✓ |

Validators re-run: `_validate_issue21m_quikmemo.py` → **PASS**

---

## 4. Prior Issue Fix Regression

### Issue #25 — MPOLICY / MEMOKEY padding

| Check | Result |
|-------|--------|
| quikmstr.MPOLICY width = 10 | PASS (0 violations) |
| quikmemo.MEMOKEY width = 10 | PASS (0 violations) |
| MEMOKEY ⊆ quikmstr.MPOLICY | PASS (0 orphan keys) |
| Regression tables byte-identical | PASS (MPOLICY unchanged) |

### Issue #26 — MPREM mapping

`_validate_issue26_mprem.py` → **PASS**

| Check | Result |
|-------|--------|
| Trace 010310404C MPREM | 13.20 ✓ |
| Trace 010331768C MPREM | 10.96 ✓ |
| Trace 010367131C MPREM | 9.12 ✓ |
| Edge 010718276C phase 4 | 1641.30 ✓ |
| MMODPREM vs PPOLC MODE_PREMIUM | 4,954/4,954 |
| MVPU vs VALUE_PER_UNIT | 6,737/6,737 |
| MUNIT vs NUMBER_OF_UNITS | 6,737/6,737 |
| quikprmh row count | 205,577 (unchanged) |

---

## 5. DBF/FPT Persistence Investigation

### Finding: **Not a generator failure — output hygiene splits DBF pair**

| Step | Timestamp | Event |
|------|-----------|-------|
| 1 | 13:23:17 | `quikmemo.csv` written (29,279 rows) |
| 2 | 13:23:26 | `write_quikmemo_dbf()` succeeds — log reports 29,279 rows, FPT=yes |
| 3 | 13:24:31 | `_run_output_hygiene()` moves 14 non-CSV files out of Output |

### Post-hygiene file locations

| File | Location | Size |
|------|----------|-----:|
| `quikmemo.csv` | `QLA_Migration/Output/` | 4.6 MB |
| `quikmemo.dbf` | `plan_analysis/phase_r5_rate_loader/emitted_dbf/` | 615 KB |
| `quikmemo.dbt` | `QLA_Migration/Reports/` | 15.0 MB |

### Root cause

```4133:4145:QLA_Migration/app.py
    def _run_output_hygiene(self, error_log=None):
        """Keep QLA_Migration/Output CSV-only. Moves (never deletes) non-CSV files
        to Reports / rate sandbox / Error_Logs and reports the result in the log."""
        ...
            res = RL.relocate_non_csv(out_dir, reports, sandbox, error_log)
```

```188:212:qla_core/run_logging.py
def relocate_non_csv(output_dir, reports_dir, sandbox_dbf_dir, error_log=None):
    ...
            if lower.endswith(".dbf"):
                dest_dir = sandbox_dbf_dir
            ...
            else:
                dest_dir = reports_dir
            ...
            shutil.move(src, dest)
```

**Routing mismatch:** `*.dbf` → rate sandbox; `*.dbt` (memo sidecar) → Reports. The pair is **physically separated**.

### Integrity test

```
dbf.Table('.../emitted_dbf/quikmemo.dbf')
→ BadDataError: memo fields exist without memo file
```

CSV artifact: `Issue_Log_Items/Issue_21M/Issue_21M_DBF_Persistence_Finding.csv`

### Is DBF/FPT required for UAT?

**Yes.** QLAdmin Help §7.151 defines `QUIKMEMO` with `MEMOTEXT` as type **MEMO** (DBF + blob sidecar). CSV batch output alone is sufficient for row-count and content review; **QLAdmin load requires an intact DBF+DBT pair** in the same directory.

This matches the Risk Agent **CONDITIONAL GO** gate: CSV first; DBF prototype before production load.

---

## 6. Smallest Safe Correction (Development Agent — not applied in Regression)

Regression Agent is **read-only**. Recommended **surgical fix** (smallest blast radius):

**Option A (recommended):** Mirror claims UAT pattern — write `quikmemo.dbf` + sidecar to `Output/quikmemo_uat_dbf/` and extend `relocate_non_csv()` to **skip** `*_uat_dbf/` subdirectories (or move `.dbf` + co-located `.dbt`/`.fpt` together).

**Option B:** In `relocate_non_csv()`, when moving a `.dbf`, also move same-stem `.dbt`/`.fpt` from the same source directory to the **same destination**.

**Option C:** Invoke `write_quikmemo_dbf()` **after** `_run_output_hygiene()` into a dedicated UAT folder.

**Do not:** Change memo conversion logic, rulebooks, or unrelated table batch paths.

---

## 7. Development Agent Follow-Up Prompt (if DBF UAT required)

```
Development Agent — Issue 21M DBF hygiene fix (v57.33)

Problem: _run_output_hygiene splits quikmemo.dbf (-> emitted_dbf/) from quikmemo.dbt (-> Reports/), corrupting memo table.

Surgical fix only:
1. Write quikmemo DBF+DBT to Output/quikmemo_uat_dbf/ (mirror claims_uat_dbf pattern), OR
2. Update qla_core/run_logging.relocate_non_csv to move .dbf and same-stem .dbt/.fpt together.

Do NOT change quikmemo converter, filters, or existing table batch branches.
Version bump v57.33. Re-run _validate_issue21m + confirm dbf.Table opens with memotext.
```

---

## 8. Batch / Fleet Checks

| Check | Result |
|-------|--------|
| Full batch v57.32 | PASS (exit 0, ~13 min) |
| `_validate_issue21m_quikmemo.py` | PASS |
| `_validate_issue26_mprem.py` | PASS |
| Post-batch OUTPUT VALIDATION | FAIL (11,641 errors — **pre-existing fleet rules**, not quikmemo) |
| Output hygiene | Moved 14 non-CSV files (includes quikmemo DBF split) |

---

## 9. Recommendation

### Regression verdict: **PASS**

No regression to existing conversion outputs. Greenfield `quikmemo` CSV pipeline is correct and isolated.

### Client UAT readiness

| UAT mode | Recommendation |
|----------|----------------|
| **CSV content review** (counts, trace policies, memo text) | **GO** |
| **QLAdmin DBF load** (Memo tab) | **NO-GO** — fix DBF/DBT co-location first |

### Overall: **CONDITIONAL GO for Client UAT**

Proceed to **Closure Agent** for CSV-phase UAT sign-off. Schedule a **v57.33 surgical Dev fix** before DBF load UAT.

---

## Appendix

| Artifact | Path |
|----------|------|
| Regression report | `Issue_Log_Items/Issue_21M/Issue_21M_Regression_Report.md` |
| Row-count comparison | `Issue_Log_Items/Issue_21M/Issue_21M_Regression_Row_Counts.csv` |
| DBF persistence finding | `Issue_Log_Items/Issue_21M/Issue_21M_DBF_Persistence_Finding.csv` |
| Validation report | `Issue_Log_Items/Issue_21M/Issue_21M_Validation_Report.md` |
| Relocated DBF | `plan_analysis/phase_r5_rate_loader/emitted_dbf/quikmemo.dbf` |
| Relocated DBT | `QLA_Migration/Reports/quikmemo.dbt` |
| Batch log | `QLA_Migration/Output/_full_batch_test_log.txt` |
