# Issue #33 — Forensic Pointer Resolution (QUIKISSC)

**Issue:** #33 — ISWL QUIKISSC (Surrender Charges)  
**Date:** 2026-06-30  
**Mode:** Research-only forensic pass (no code changes)

---

## A. Pointer Resolution

### A1) PSEGT SL payload decode (byte-level)

**Source:** `QLA_Migration/Source/PSEGT_Segment_Extract_20260629.csv`  
**Rows decoded:** `(SEGMENT_ID=659 CEN II, SEGT_TYPE=SL)` and `(SEGMENT_ID=668 SPWL, SEGT_TYPE=SL)`

Decoded `SEGT_DATA` (659 CEN II / SL), 128 bytes:

- Offset `0x00`: `659 CEN IISLD000`
- Offset `0x20`: `0C` length marker + ASCII token `OSLNS00XT`
- Offset `0x40+`: flags/markers including `PN`, `I`, `F`, `NN`

Decoded `SEGT_KEY0`:

- `659 CEN IISL`

Decoded `ROW_COLUMN`:

- Same payload as `SEGT_DATA`, plus modifier tail `MB01...`

### A2) SR linkage decode

Decoded `SEGT_DATA` (659 CEN II / SR), 128 bytes:

- Prefix `659 CEN IISR`
- Embedded segment reference `Y659 CEN II`
- Multiple Y/N flag blocks

Interpretation: SR row carries parent/child control flags and references hub segment linkage; SL row carries pointer token(s) for surrender load schedule lookup.

### A3) Pointer token chain resolved

```text
PSEGT(SEGT_TYPE=SL)
  -> SEGT_DATA token: SLD000
  -> SEGT_DATA token: OSLNS00XT
  -> runtime schedule source lookup
```

**Forensic resolution outcome:** `OSLNS00XT` is confirmed as a runtime pointer token in PSEGT SL payload.  
`SLD000` behaves as the SL schedule code attached to that pointer context.

---

## B. Runtime Lookup Proof

### B1) Lookups performed

1. **Global token scan across `QLA_Migration/Source/*.csv` (raw + hex-decoded fields):**
   - `OSLNS00XT` appears only in PSEGT hex payloads.
2. **Global SL-bearing segment decode in PSEGT:**
   - Only two SL segments: `659 CEN II`, `668 SPWL`.
   - Both carry `OSLNS00XT` pointer token.
3. **Candidate table comparison for `TYPE_CODE=SL`:**
   - `Rate_Table_Extract_20260427.csv`:  
     - `659 CEN II`: 14 rows  
     - `668 SPWL`: 10 rows  
     - Non-zero surrender-like duration ladder.
   - `PDAGE_AgeDuration_Rates_Extract_20260530.csv`:  
     - `659 CEN II`: 12 rows  
     - `668 SPWL`: 12 rows  
     - Values are zero (`VALUE1_FLOAT=0.0`) and do not represent a usable surrender schedule.

### B2) Hierarchy proof (not name-similarity-only)

```text
PCOVRSGT (ISWL active slot -> SEGT_ID=659 CEN II)
  -> PSEGT (SEGMENT_ID=659 CEN II, SEGT_TYPE=SL)
  -> SEGT_DATA contains runtime pointer OSLNS00XT + SLD000
  -> candidate schedule rows exist in Rate_Table TYPE_CODE=SL for same segment coverage
  -> schedule shape is valid duration ladder (non-zero, descending)
```

### B3) Conclusion on source table

**Result:** `Rate_Table TYPE_CODE=SL` is the runtime-referenced schedule source with **strong forensic evidence**.  
`PDAGE TYPE_CODE=SL` is not runtime-authoritative for QUIKISSC in this extract set (zero payload).

---

## C. Exact Expected Row Count (8 ISWL MPLANs)

### C1) Determined dimensionality of SL schedule (`659 CEN II`)

From `Rate_Table TYPE_CODE=SL` rows:

- `SEX`: only `M`
- `UNDERWRITING_CLASS`: only `S`
- `BAND`: only `1`
- `AGE`: only `0`
- `DURATION`: `1..14`

No issue-country/state columns exist in source; established conversion defaults are `ISSCNTRY=0000`, `ISSUEST=00`.

### C2) Dimensions that vary

- **Varies:** `DURATION` only.
- **Does not vary:** `SEX`, `UWCLASS`, `BAND`, `AGE`, `ISSCNTRY`, `ISSUEST`.

### C3) Exact row count

Because durations are pivoted into SCHG columns, one dimension tuple yields one QuikIssc row per plan.

- Dimension tuples per plan: **1**
- ISWL MPLANs: **8**

**Exact expected QuikIssc rows for ISWL:** **8**

---

## D. SCHG01–SCHG20 Mapping

### D1) Proven duration mapping

`Rate_Table` SL provides durations `1..14`, so:

- `SCHG01 <- DURATION 1`
- `SCHG02 <- DURATION 2`
- ...
- `SCHG14 <- DURATION 14`

### D2) SCHG15–SCHG20 population

No source rows exist for durations 15–20 for `659 CEN II` SL.

Evidence from current CSV emission conventions in repo:

- `qla_core/rate_factor_loader.py` sets missing duration cells to empty string:
  - `row[field] = ""  # unpopulated duration cell`

Therefore for CSV-level emission, **SCHG15–SCHG20 should be blank (empty)**, not carry-forward and not synthetic zero-fill.

---

## E. Percentage Representation

### E1) Source evidence

`Rate_Table` SL values for `659 CEN II`:

`100, 100, 70, 60, 50, 40, 30, 20, 15, 10, 8, 6, 4, 2`

`668 SPWL` SL control schedule:

`10, 9, 8, ..., 1`

These are canonical percentage ladders; they are not decimal fractions (`1.0000`, `0.7000`, etc.).

### E2) QLAdmin schema consistency

`QuikIssc` fields `SCHG01..SCHG20` are numeric `N(8.4)` duration charge values.  
Current project convention for percent-style rate values (e.g., QUIKUINT) uses percent literals, not decimal fractions.

### E3) Representation conclusion

**`100` means `100%` (emit as `100.0000`)**, not `1.0000`.

---

## F. Remaining SME Questions (reduced set)

The forensic pass closes most discovery uncertainty; remaining SME items are narrowed to policy decisions:

1. **Formal sign-off:** Confirm `OSLNS00XT/SLD000 -> Rate_Table TYPE=SL` as production authority.
2. **UW code normalization:** Confirm mapping from source `S` to QLAdmin `UWCLASS` target code.
3. **AGE field semantics:** Confirm `AGE=0` means single all-age schedule row (no age expansion).
4. **Blank vs zero in SCHG15–20 at DBF handoff:** CSV blank is recommended; confirm if downstream DBF loader requires explicit `0.0000`.

---

## Final Recommendation

**READY FOR SME**

Runtime pointer chain is now forensically resolved to a concrete schedule source with hierarchy proof.  
Development should wait only for final SME sign-off on the narrowed policy-format questions above.

