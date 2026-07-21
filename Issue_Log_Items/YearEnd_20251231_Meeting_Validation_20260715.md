# YE 12/31 Meeting Package — Validation Snapshot

**Generated:** 2026-07-15  
**Engine:** v57.93  
**Source zip:** `QLA_Migration/Source/1231_Conversion_data.zip`  
**PPOLC:** `PPOLC_PolicyMaster_Extract_20260102.csv`  
**Valuation:** `QLA_VALUATION_DATE=20251231`  
**Batch:** exit 0 (~30 min)

---

## Counts

| Table | Rows |
|-------|-----:|
| quikmstr | 5,084 |
| quikridr | 6,936 |
| quikplan | 141 |

Midyear archive (pre this YE run): `QLA_Migration/Archive/Output_midyear_20260715_pre_YE_meeting/`

---

## Closed-issue business rules (YE)

| Issue | Rule | Result |
|-------|------|--------|
| **#72** | 44→NFO 2 / 45→NFO 3 | **PASS** (0 violations; 284 forced in batch log) |
| **#73** | MISSCNTRY=`0000` | **PASS** (0 ≠ 0000) |
| **#74** | VARDB `4`→`0` only | **PASS** (121×`0`; structure `1`/`2`/`3` kept) |
| **#75** | MBANKNO QLA-safe | **PASS** (0 invalid filled) |
| **#76** | phase-1 @44/45: MPAYUP=MPAIDTO; MLASTANN=run year−payup year | **PASS** (407 candidates, 0 formula fails) |

Hardcoded midyear row-count checks in some validators (expect 5083 / 400) will FAIL on YE — expected population drift. Use business-rule results above.

---

## Sample `010407670C`

| Field | Value |
|-------|-------|
| MSTATUS / MNFOPT | 45 / 3 |
| MISSCNTRY | 0000 |
| MPAIDTO | 20121001 |
| Phase-1 MPAYUP / MLASTANN | 20121001 / **14** |
| Phase-2 PUA MPAYUP | 19720201 (#60 preserved) |

---

## Client load for meeting

**Partial UAT:** `QLA_Migration/Output/Test_Validation/` (`quikmstr`, `quikridr`, `quikplan`)  
**Full package:** `QLA_Migration/Output/` + `Output/rates/`  
**Batch log:** `QLA_Migration/Logs/_full_batch_test_log.txt`
