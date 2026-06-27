# Issue 21M — Deployment Packaging Fix (v57.33)

**Stage:** 4B — Deployment Packaging Correction  
**Engine version:** v57.33  
**Generated:** 2026-06-26  
**Verdict:** **PASS**

---

## Problem (Regression finding)

`write_quikmemo_dbf()` generated a valid `quikmemo.dbf` + `quikmemo.dbt` pair, but `_run_output_hygiene()` routed:

| File | Destination |
|------|-------------|
| `quikmemo.dbf` | `plan_analysis/phase_r5_rate_loader/emitted_dbf/` |
| `quikmemo.dbt` | `QLA_Migration/Reports/` |

Result: `BadDataError: memo fields exist without memo file` — DBF unusable for QLAdmin load.

**Not a conversion logic defect.** CSV output was always correct.

---

## Fix (smallest safe change)

Two surgical edits — no converter, rulebook, or memo formatting changes:

### 1. Write DBF to dedicated UAT folder (`QLA_Migration/app.py`, `app.py`)

```
Output/quikmemo_uat_dbf/quikmemo.dbf
Output/quikmemo_uat_dbf/quikmemo.dbt   (sidecar, same directory)
```

### 2. Skip `*_uat_dbf/` in output hygiene (`qla_core/run_logging.py`)

`scan_non_csv()` skips directories whose basename ends with `_uat_dbf` (includes `quikmemo_uat_dbf` and `claims_uat_dbf`).

---

## Before / After

| Aspect | Before (v57.32) | After (v57.33) |
|--------|-----------------|----------------|
| CSV output | `Output/quikmemo.csv` (29,279 rows) | **Unchanged** |
| DBF write path | `Output/quikmemo.dbf` | `Output/quikmemo_uat_dbf/quikmemo.dbf` |
| After batch hygiene | DBF/DBT **split** to different folders | DBF/DBT **remain together** |
| DBF open test | FAIL (missing memo file) | **PASS** |
| Conversion logic | — | **Unchanged** |

---

## Files Changed

| File | Change |
|------|--------|
| `qla_core/run_logging.py` | Skip `*_uat_dbf` dirs in `scan_non_csv()` |
| `QLA_Migration/app.py` | v57.33; DBF path → `quikmemo_uat_dbf/` |
| `app.py` | Mirror of QLA_Migration/app.py |
| `QLA_Migration/_validate_issue21m_dbf_packaging.py` | New packaging validator |

**Not changed:** `quikmemo_converter.py`, rulebooks, source resolver mappings, memo templates.

---

## Packaging Validation

```bash
python QLA_Migration/_validate_issue21m_dbf_packaging.py
python QLA_Migration/_validate_issue21m_quikmemo.py --before-dir QLA_Migration/Output/_issue21m_before
python QLA_Migration/_validate_issue26_mprem.py
```

| Check | Result |
|-------|--------|
| `quikmemo.dbf` exists in `quikmemo_uat_dbf/` | ✓ (614,957 bytes) |
| `quikmemo.dbt` sidecar same directory | ✓ (14,990,916 bytes) |
| DBF opens (`dbf.Table`) | ✓ 29,279 rows |
| MEMOTEXT readable (`[ENS]`/`[PNOTE]`) | ✓ |
| Survives `relocate_non_csv()` simulation | ✓ pair intact |
| `quikmemo.csv` unchanged | ✓ 29,279 rows |
| Regression tables unchanged | ✓ |
| Issue #25 MEMOKEY width | ✓ (via issue21m validator) |
| Issue #26 MPREM | ✓ PASS |

**Packaging validator:** `RESULT: PASS`

---

## Recommendation for Closure Agent

| Gate | Status |
|------|--------|
| CSV conversion regression | PASS |
| DBF/FPT UAT load packaging | **PASS** (v57.33) |
| Client UAT — memo content review (CSV) | Ready |
| Client UAT — QLAdmin DBF load | **Ready** — deploy from `Output/quikmemo_uat_dbf/` |

**Closure Agent may proceed** to finalize Issue 21M documentation and client handoff. UAT load path:

```
QLA_Migration/Output/quikmemo_uat_dbf/quikmemo.dbf
QLA_Migration/Output/quikmemo_uat_dbf/quikmemo.dbt   (must stay with DBF)
```

---

## Note for next full batch

Re-run `_run_full_batch_test.py` at v57.33 to confirm end-to-end batch writes the UAT folder (Development validation used direct DBF write + hygiene simulation; full batch not re-run in this packaging fix).
