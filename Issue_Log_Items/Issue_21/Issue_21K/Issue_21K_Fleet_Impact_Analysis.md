# Issue #21K — Fleet Impact Analysis

**Source file:** `QLA_Migration/Output/quikridr.csv` (v57.39 batch)  
**Generated:** 2026-06-28  
**Machine summary:** `Issue_21K_Fleet_Impact_Summary.json`

---

## Fleet Overview

| Metric | Count |
|--------|------:|
| Total `quikridr` rows | **6,934** |
| Rows with sub-mill `MUNIT` (>3 dp significant) | **1,065** |
| Unique policies with sub-mill `MUNIT` | **950** |
| PUA-style plan rows (`*PA` / `*PUA`) | **495** |
| Unique policies with PUA-style rows | **493** |

---

## Cent-Loss Exposure (If Downstream Truncates/Rounds)

Simulated display loss on current **correct CSV** values:

| Downstream behavior | Rows losing ≥ $0.01 vs true face | Policies affected (approx.) |
|---------------------|--------------------------------:|----------------------------:|
| 3 dp **truncate** on MUNIT | **1,063** | ~950 |
| 3 dp **round** on MUNIT | **1,063** | ~950 |
| Whole-dollar **round** on face | **1,064** | ~950 |

**Scope:** Not limited to PUA — any rider/base row with fractional units is affected. PUA rows are the **most visible** because fractional PUA face amounts are common.

---

## PUA Subpopulation

| Metric | Count |
|--------|------:|
| PUA-style rows | 495 |
| PUA rows with sub-mill MUNIT | ~488 (prior research; pattern unchanged) |
| PUA rows that would show wrong cents under 3 dp | **488** |

---

## Trace Policy — 010448806C

| Field | CSV (v57.39) | If 3dp truncate | If 3dp round | If whole-$ round |
|-------|-------------:|----------------:|-------------:|-------------------:|
| MUNIT | 5.75296 | 5.752 | 5.753 | — |
| MVPU | 1000.00 | 1000.00 | 1000.00 | — |
| **Face** | **$5,752.96** | **$5,752.00** | **$5,753.00** | **$5,753.00** |

**Client reopened screenshot ($5,753.00)** aligns with **round-up** behavior, not truncate-down ($5,752.00).

---

## Sample High-Impact PUA Rows

| MPOLICY | MPLAN | MUNIT | True face | 3dp round face | Δ |
|---------|-------|------:|----------:|---------------:|--:|
| 010448806C | 1708PA | 5.75296 | $5,752.96 | $5,753.00 | +$0.04 |
| 010615191C | 1708PA | 3.74599 | $3,745.99 | $3,746.00 | +$0.01 |
| 010510671C | 2665ST | 1.15296 | $6,034.59 | $6,035.00 | +$0.41 |
| 010335095C | 261PUA | 0.83564 | $835.64 | $836.00 | +$0.36 |
| 010310404C | 1960PA | 5.94278 | $5,942.78 | $5,943.00 | +$0.22 |

Full historical trace sample: `Issue_Log_Items/Issue_21/reports/Issue_21K_MUNIT_Precision_Trace.csv`

---

## Validator Fleet Results (2026-06-28)

**Command:** `python tools/validators/validate_issue21k_fleet.py`

| Check | Result |
|-------|--------|
| CSV rows | 6934 |
| DBF rows (staging reload) | 6934 |
| Sub-mill preserved CSV→DBF | **1065/1065** |
| Fractional-cent faces OK | **1067/1067** |
| MUNIT mismatch | **0** |
| Primary trace 010448806C | MUNIT=5.75296 face=5752.96 **PASS** |

**Fleet conclusion at CSV/staging DBF layer:** **No precision loss.**

---

## Business Impact

| Dimension | Assessment |
|-----------|------------|
| Severity | Low–Medium per policy; cumulative on PUA-heavy block |
| Financial delta | Typically **$0.01–$1.00** per affected row; example 010448806C = **$0.04** round-up |
| Regulatory / client trust | **High** — visible Coverage tab mismatch vs LifePRO |
| Conversion rework required | **None** — CSV already correct |
| Deployment rework required | **Yes** — production DBF path + possible QLAdmin display |

---

## Isolation

| Question | Answer |
|----------|--------|
| Only 010448806C? | **No** — ~950 policies / 1,065 rows at risk |
| Only PUA? | **No** — PUA is ~495 rows; remainder are other riders/bases with fractional units |
| Caused by Issue #27? | **No** — #27 removed SL duplicate row; PUA MUNIT unchanged |

---

## Impact Conclusion

Fleet impact is **material but downstream-contained**: v57.39 CSV preserves precision for all 1,065 sub-mill rows. Failure manifests only when QLAdmin storage or display does not honor five-decimal `MUNIT`.

**Remediation scope:** Client production DBF deployment (six tables + reload + reindex) and/or QLAdmin display fix — **not** fleet-wide converter changes.
