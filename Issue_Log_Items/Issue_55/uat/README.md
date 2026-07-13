# Issue #55 — QUIKRIDR UAT package

**Generated:** 2026-07-13  
**Scope:** Sample policies only (`018495BC`, `018499CC`, `018510C`) — **6 rows**  
**MUNIT:** N(10,5) — verified PASS vs PPBEN / client expected units  

## Files

| File | Path |
|------|------|
| QUIKRIDR.DBF | `QLA_Migration/Staging/issue55_quikridr_uat/QUIKRIDR.DBF` |
| Same copy | `Issue_Log_Items/Issue_55/uat/QUIKRIDR.DBF` |
| Sample CSV | `…/quikridr_issue55_samples.csv` (Staging, Issue_55/uat, Test_Validation) |
| Source of truth (full fleet CSV) | `QLA_Migration/Output/quikridr.csv` |

## Verified stored units in DBF

| Policy | Phase | MUNIT | Face (×1000) |
|--------|------:|------:|-------------:|
| 018495BC | 1 | 0.00001 | $0.01 |
| 018495BC | 2 | 0.53 | **$530** |
| 018499CC | 1 | 0.00001 | $0.01 |
| 018499CC | 2 | 1.05 | $1,050 |
| 018510C | 1 | 0.00001 | $0.01 |
| 018510C | 2 | 0.647 | **$647** |

## Load caution

This DBF has **only these 6 rows**. Do **not** replace the entire production/UAT `QUIKRIDR.DBF` with it (that would drop all other policies). Use your normal update/append path for these three policies, or merge into the existing table.

Rebuild:

```bat
python Issue_Log_Items\Issue_55\scripts\build_issue55_quikridr_uat.py
```

**Note:** Full-fleet `write_quikridr_dbf` currently fails on unrelated `MCV0` overflow for some UL rows; Issue #55 package avoids that by sampling only these policies.
