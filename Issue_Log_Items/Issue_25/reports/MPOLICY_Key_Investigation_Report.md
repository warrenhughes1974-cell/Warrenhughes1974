# MPOLICY Key Investigation Report

**Generated:** 2026-06-26 09:58:13
**Script:** `_investigate_mpolicy_keys.py` v1.0
**Output directory:** `C:\Users\warren\Documents\GitHub\Warrenhughes1974\QLA_Migration\Output`

## Executive Summary

- **quikmstr policies:** 5083 unique visible MPOLICY values
- **Policies with visible length < 10:** 258 (length distribution: {7: 29, 8: 57, 9: 43, 10: 4954})
- **quikmstr raw length exactly 10:** 5083 / 5083
- **Child-table raw MPOLICY mismatches vs quikmstr:** 0
- **CSV file preserves leading-space MPOLICY bytes:** True
- **Good policy `010143726C` raw len:** 10
- **Bad example `018499DC` raw len:** 10

## Hypothesis Test: Locate vs Display Key Split

Child tables match quikmstr **raw** CSV values (including leading spaces). CSV output **does** preserve leading spaces on disk.

However, every in-repo DBF generation path tested uses **`strip()` before writing** character fields. After strip, short policies become **7–9 characters** in a **C(10)** field, not left-padded to 10.

**Likely QLAdmin behavior:**
- **Locate/list** may scan/display using **trimmed** visible policy text → user sees `018499DC`.
- **Display/open** may use the **indexed primary key** (`MPOLICY` as stored in quikmstr index) which may require **fixed-width 10** or exact padded match.
- If load strips spaces, index key = `018499DC` (8 chars) but child FK lookups may still fail if mixed padded/unpadded values exist across tables from prior loads.

**Leading-space padding in CSV alone does not survive DBF load** if the client's import uses the same strip pattern as this repo's DBF utilities.

## Trace Policies (quikmstr + child tables)

### `018510C`
- **quikmstr raw:** '   018510C' (len=10, leading spaces=3)
- **visible:** `018510C` (len=7)
- **hex:** `20 20 20 30 31 38 35 31 30 43`
- **DBF after strip+truncate C(10):** '018510C' (len=7)
- **Child table hits:**
  - `quikclid.csv`: 7 rows, raw values=["'   018510C'"] [MATCH]
  - `quikdvdp.csv`: 1 rows, raw values=["'   018510C'"] [MATCH]
  - `quikridr.csv`: 2 rows, raw values=["'   018510C'"] [MATCH]

### `018495BC`
- **quikmstr raw:** '  018495BC' (len=10, leading spaces=2)
- **visible:** `018495BC` (len=8)
- **hex:** `20 20 30 31 38 34 39 35 42 43`
- **DBF after strip+truncate C(10):** '018495BC' (len=8)
- **Child table hits:**
  - `quikclid.csv`: 7 rows, raw values=["'  018495BC'"] [MATCH]
  - `quikdvdp.csv`: 1 rows, raw values=["'  018495BC'"] [MATCH]
  - `quikridr.csv`: 2 rows, raw values=["'  018495BC'"] [MATCH]

### `018499CC`
- **quikmstr raw:** '  018499CC' (len=10, leading spaces=2)
- **visible:** `018499CC` (len=8)
- **hex:** `20 20 30 31 38 34 39 39 43 43`
- **DBF after strip+truncate C(10):** '018499CC' (len=8)
- **Child table hits:**
  - `quikbenf.csv`: 1 rows, raw values=["'  018499CC'"] [MATCH]
  - `quikclid.csv`: 8 rows, raw values=["'  018499CC'"] [MATCH]
  - `quikdvdp.csv`: 1 rows, raw values=["'  018499CC'"] [MATCH]
  - `quikprmh.csv`: 18 rows, raw values=["'  018499CC'"] [MATCH]
  - `quikridr.csv`: 2 rows, raw values=["'  018499CC'"] [MATCH]

### `018499DC`
- **quikmstr raw:** '  018499DC' (len=10, leading spaces=2)
- **visible:** `018499DC` (len=8)
- **hex:** `20 20 30 31 38 34 39 39 44 43`
- **DBF after strip+truncate C(10):** '018499DC' (len=8)
- **Child table hits:**
  - `quikclid.csv`: 7 rows, raw values=["'  018499DC'"] [MATCH]
  - `quikdvdp.csv`: 1 rows, raw values=["'  018499DC'"] [MATCH]
  - `quikridr.csv`: 2 rows, raw values=["'  018499DC'"] [MATCH]

### `010143726C`
- **quikmstr raw:** '010143726C' (len=10, leading spaces=0)
- **visible:** `010143726C` (len=10)
- **hex:** `30 31 30 31 34 33 37 32 36 43`
- **DBF after strip+truncate C(10):** '010143726C' (len=10)
- **Child table hits:**
  - `quikbenf.csv`: 3 rows, raw values=["'010143726C'"] [MATCH]
  - `quikclid.csv`: 7 rows, raw values=["'010143726C'"] [MATCH]
  - `quikdvdp.csv`: 1 rows, raw values=["'010143726C'"] [MATCH]
  - `quikprmh.csv`: 9 rows, raw values=["'010143726C'"] [MATCH]
  - `quikridr.csv`: 2 rows, raw values=["'010143726C'"] [MATCH]

## Per-Table Scan Summary

| Table | Rows | Raw!=10 | Visible<10 | Leading spaces | Mismatch vs quikmstr raw | Mismatch after DBF strip sim |
|-------|------|---------|------------|----------------|--------------------------|------------------------------|
| Output\claims_review_hold_manifest.csv | 3851 | 0 | 0 | 0 | 0 | 0 |
| Output\quikbenf.csv | 5870 | 0 | 65 | 65 | 0 | 0 |
| Output\quikclid.csv | 46753 | 0 | 1093 | 1093 | 0 | 0 |
| Output\quikclmp.csv | 1709 | 0 | 31 | 31 | 0 | 0 |
| Output\quikclms.csv | 2114 | 0 | 29 | 29 | 0 | 0 |
| Output\quikdvdp.csv | 5083 | 0 | 129 | 129 | 0 | 0 |
| Output\quikdvpr.csv | 31 | 0 | 0 | 0 | 0 | 0 |
| Output\quikmstr.csv | 5083 | 0 | 129 | 129 | 0 | 0 |
| Output\quikprmh.csv | 205577 | 0 | 779 | 779 | 0 | 0 |
| Output\quikridr.csv | 7002 | 0 | 265 | 265 | 0 | 0 |

## DBF Load Simulation (trace policies)

Simulates known in-repo DBF writers that call `.strip()` before append (e.g. `phase19_uat_emitted_csv_dbf_generator.truncate_char`, `phase_p2f_validation_runner.write_quikplan_dbf`).

```json
{
  "018510C": {
    "csv_raw": "'   018510C'",
    "csv_raw_len": 10,
    "dbf_after_strip": "'018510C'",
    "dbf_after_strip_len": 7,
    "left_pad_would_be": "'   018510C'",
    "right_pad_would_be": "'018510C   '",
    "display_key_hypothesis_trimmed": "018510C",
    "index_key_hypothesis_fixed10_left": "   018510C"
  },
  "018495BC": {
    "csv_raw": "'  018495BC'",
    "csv_raw_len": 10,
    "dbf_after_strip": "'018495BC'",
    "dbf_after_strip_len": 8,
    "left_pad_would_be": "'  018495BC'",
    "right_pad_would_be": "'018495BC  '",
    "display_key_hypothesis_trimmed": "018495BC",
    "index_key_hypothesis_fixed10_left": "  018495BC"
  },
  "018499CC": {
    "csv_raw": "'  018499CC'",
    "csv_raw_len": 10,
    "dbf_after_strip": "'018499CC'",
    "dbf_after_strip_len": 8,
    "left_pad_would_be": "'  018499CC'",
    "right_pad_would_be": "'018499CC  '",
    "display_key_hypothesis_trimmed": "018499CC",
    "index_key_hypothesis_fixed10_left": "  018499CC"
  },
  "018499DC": {
    "csv_raw": "'  018499DC'",
    "csv_raw_len": 10,
    "dbf_after_strip": "'018499DC'",
    "dbf_after_strip_len": 8,
    "left_pad_would_be": "'  018499DC'",
    "right_pad_would_be": "'018499DC  '",
    "display_key_hypothesis_trimmed": "018499DC",
    "index_key_hypothesis_fixed10_left": "  018499DC"
  },
  "010143726C": {
    "csv_raw": "'010143726C'",
    "csv_raw_len": 10,
    "dbf_after_strip": "'010143726C'",
    "dbf_after_strip_len": 10,
    "left_pad_would_be": "'010143726C'",
    "right_pad_would_be": "'010143726C'",
    "display_key_hypothesis_trimmed": "010143726C",
    "index_key_hypothesis_fixed10_left": "010143726C"
  }
}
```

## Root Cause Assessment

**Primary (proven in-repo):** DBF load utilities strip leading/trailing spaces from MPOLICY before append (`truncate_char` / `strip_val` in claims UAT DBF generator and quikplan DBF writer). This removes the v57.30 leading-space padding benefit at DBF boundary.

**Secondary (consistent with symptom):** Short crosswalked policies (7–9 visible chars) are stored in QLAdmin as **unpadded** values in C(10) fields after load. QLAdmin locate may trim for display while policy open uses a different key resolution path, producing **Policy Not Found**.

**Not the cause:** Crosswalk identity mismatch for traced policies — all five trace policies exist in quikmstr with expected crosswalk targets. Child-table raw values match quikmstr when v57.30 padding is present.

**Not proven in this repo:** Loyal2QL / QLAdmin native FieldPut behavior (external to this codebase) — must confirm on client load workstation whether FieldPut strips character fields.

## Recommended Next Step (no code applied)

1. **Confirm client DBF load path** — capture actual quikmstr.dbf MPOLICY bytes for `018499DC` after QLAdmin import (hex dump of 10-char field).
2. **Compare good vs bad** — `010143726C` is already 10 visible chars; short policies are 7–9.
3. **If DBF stores trimmed 8-char value:** test whether QLAdmin expects **right-padding with spaces** within C(10) (FoxPro PADR/left-aligned storage) vs **left-padding** vs **no padding**.
4. **Surgical fix candidate (after proof):** apply padding at **DBF write boundary** without strip, OR use QLAdmin-native padding (PADR/LEFT alignment) — **not** CSV-only padding that gets stripped.
5. Do **not** zero-pad or change crosswalk identity.
