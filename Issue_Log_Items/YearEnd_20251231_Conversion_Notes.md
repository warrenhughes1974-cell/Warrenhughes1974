# Year-End Valuation Conversion — 12/31/2025

**Extract package:** `LifePRO_Extracts_20260102.zip` (Downloads)  
**Valuation as-of:** **2025-12-31** (`QLA_VALUATION_DATE=20251231`)  
**Engine:** **v57.86**  
**Batch:** Full UAT — exit 0 (~27 min)  
**Status:** **READY for client YE validation**

---

## Staging

| Action | Location |
|--------|----------|
| Midyear Source archived | `QLA_Migration/Archive/Source_midyear_20260630/` |
| Midyear Output archived | `QLA_Migration/Archive/Output_midyear_20260714_pre_YE/` |
| YE extracts in Source | `*_20260102.csv` (+ `aba_routing_lookup.csv`) |

Skipped multi-GB fund detail files from the zip (`PFNDRDET`, `PFNDS*`, etc.).  
**Not in YE zip:** `PDINT`/`PDINTTBL` → QuikUint remains empty (known).

---

## Exact YE controls

| Control | Value |
|---------|-------|
| Source PPOLC | `PPOLC_PolicyMaster_Extract_20260102.csv` |
| `QLA_VALUATION_DATE` | **20251231** → `quikridr.MLASTANN` |
| Engine | v57.86 (valuation-date override) |
| Emit paths | claims, QuikLoan, QuikBenh, rates, QuikIsrr, reinsurance |

### Golden `010310404C` (as-of YE)

| Ph | MPLAN | MPHSTAT | MEFFDATE | MAGE | MLASTANN | MPAYUP |
|----|-------|---------|----------|------|----------|--------|
| 1 | 1960PO | 22 | 19690128 | 26 | **56** | 20460128 |
| 2 | 1960PA | **41** | **19690128** | **26** | **56** | **19690128** |

`MLASTANN=56` = 2025 − 1969 (correct for YE; midyear run had used run-date → 57).

---

## Output counts (YE vs midyear archive)

| Table | YE 12/31/2025 | Midyear archive |
|-------|-------------:|----------------:|
| quikmstr | 5,084 | 5,083 |
| quikridr | 6,936 | 6,934 |
| quikprmh | 201,564 | 209,470 |
| quikmemo | 5,084 (MEMOKEY grain) | — |
| quikbenh | 39,112 | 41,066 |
| quikloan | 365 | 356 |
| quikclms | 5,624 | 5,771 |

Population deltas are expected (different extract date).

---

## Validation (YE-specific)

Script: `QLA_Migration/_validate_ye_20251231.py` → **PASS**

Confirmed: #60 PUA phase + other riders, #25, #57 NFO traces, #59 LP samples (where present), #13, #54 QuikBenh shape, #51 QuikAint, #55 MUNIT floor, no `1960PA` in plan file.

**Note:** Midyear hardcoded validators (#54/#55/#60 baseline) will FAIL on YE — use the YE script above.

### YE data note — #59 Death Claim Pending

On **20260102** extract, `9010521213` / `010521213C` is **Active + PU** (not Suspended/DP). Emitted `MSTATUS=41` is correct for YE. Midyear 6/30 had S+DP → 50.

---

## Client load package

**`QLA_Migration/Output/Test_Validation/`**  
(+ full `QLA_Migration/Output/` and `Output/rates/`)

---

## Re-run

```bat
set QLA_VALUATION_DATE=20251231
QLA_Migration\run_converter.bat
```

Or: `python tools/batch_tests/run_full_batch_test.py` (defaults valuation to 20251231).
