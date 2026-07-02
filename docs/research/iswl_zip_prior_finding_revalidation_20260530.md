# ISWL ZIP Prior Finding Revalidation — 20260530

Evidence source: streamed analysis of `LifePRO_Extracts_20260530 (1).zip` (125 files, 50.24 GB uncompressed). No full extract performed.

### 1. QUIKCVS from Rate_Table CV proven
- **Status:** Strengthened
- **Note:** `Rate_Table_Extract` is **not** in the May ZIP. Alternate source **`PDAGE_AgeDuration_Rates_Extract_20260530.csv`** contains **12,084 ISWL rows** with `TYPE_CODE=CV` across all eight fleet coverage IDs (41,083 total ISWL rows in PDAGE). Repo `Rate_Table_Extract_20260427.csv` remains the converter-proven route; PDAGE is a strong May-dated parallel.

### 2. Rate_Table PR zero ISWL rows
- **Status:** Confirmed
- **Note:** `PAAGERAT_AttainedAge_Rates_Extract_20260530.csv` ISWL `PR` rows = **0**. `PDAGE` ISWL `PR` rows = **0** (3,000 global PR rows exist but none match ISWL coverages).

### 3. PAAGERAT NC may be COI
- **Status:** Still unknown (inference only)
- **Note:** **690 ISWL NC rows** in May PAAGERAT (unchanged vs April). PDDIC dictionary mentions COI/NC text but **no authoritative TYPE_CODE lookup table** found. **Unable to verify from available ZIP source data.**

### 4. PAAGERAT U6 may be GCOI
- **Status:** Still unknown (inference only)
- **Note:** **800 ISWL U6 rows** (658 CEN I + 659 CEN II only). PDDIC has 8–14 U6/GCOI text hits; no code-definition rows. **Unable to verify from available ZIP source data.**

### 5. PAAGERAT BP may be GP
- **Status:** Still unknown (inference only)
- **Note:** **1,164 ISWL BP rows** in May PAAGERAT. No dictionary proof that BP = gross premium. **Unable to verify from available ZIP source data.**

### 6. iswl-prem.csv not LifePRO authority
- **Status:** Confirmed
- **Note:** File not present in ZIP. Remains PFSA artifact only.

### 7. PPBEN FV_GUAR_RATE 4.50
- **Status:** Confirmed
- **Note:** **2,159** ISWL benefit rows with `FV_GUAR_RATE=4.50`; **2,391** with `.00`. Source: `PPBEN_PolicyBenefit_Extract_20260530.csv` (4,550 ISWL rows on `PLAN_CODE`).

### 8. UV_CURR_COI_RATE zero all ISWL
- **Status:** Confirmed
- **Note:** All **4,550** ISWL PPBEN rows have `UV_GUAR_COI_RATE=.00000` and `UV_CURR_COI_RATE=.00000`. Not usable for credited-rate mapping.

### 9. QUIKISSC unknown
- **Status:** Still unknown (new candidate — inference only)
- **Note:** `PDAGE` has **2,128 ISWL rows** each for `TYPE_CODE=TP` and `TYPE_CODE=TX` (duration-indexed VALUE fields). **No dictionary proof these are surrender charges.** Mark as candidate only.

### 10. Expenses unknown
- **Status:** Still unknown
- **Note:** No expense TYPE_CODE in rate files. `PCOVR` has `POLICY_FEE` (plan-level, 8 ISWL coverage rows). PDDIC EXPENSE line hits = 0. **Unable to verify from available ZIP source data.**

### 11. Senior plans weak PAAGERAT support
- **Status:** Strengthened (via PDAGE)
- **Note:** PAAGERAT ISWL types: BP=1164, U6=800, NC=690, NF=432, U5=200, RD=1 — concentrated on 658/659 CEN I/II. Senior coverages (659 SR GD, 669 SR GD, 679 CEN SD) have minimal PAAGERAT but **3,238+ PDAGE line hits** for 659 SR GD alone.

### 12. QUIKUINT mapping unknown
- **Status:** Still unknown
- **Note:** Guaranteed rate evidence remains PPBEN `FV_GUAR_RATE` + CSO crosswalk 4.50%. `PRBENINT` / `PPRBNUL` profiled but no QUIKUINT schema mapping proven. `PLOAN` has `INTEREST_RATE` (policy-level, 49,270 ISWL plan hits) — loan credited rate candidate only.
