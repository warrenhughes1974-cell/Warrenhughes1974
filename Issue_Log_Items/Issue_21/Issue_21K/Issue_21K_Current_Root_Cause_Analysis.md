# Issue #21K — Current Root Cause Analysis (Reopened)

**Issue:** #21K — PUA Amount Precision  
**Engine:** v57.39  
**Generated:** 2026-06-28  
**Status:** Root cause isolated — **downstream of converter CSV**

---

## Executive Conclusion

**Where precision is lost:** **QLAdmin runtime path** (DBF deployment, stored values, and/or Coverage tab display calculation) — **not** LifePRO source and **not** v57.39 converter CSV.

| Stage | `010448806C` PUA (MPHASE 2 / `1708PA`) | Status |
|-------|----------------------------------------|--------|
| LifePRO PPBEN | `NUMBER_OF_UNITS = 5.75296`, `VALUE_PER_UNIT = 1000.00` | **CORRECT** |
| v57.39 `quikridr.csv` | `MUNIT = 5.75296`, `MVPU = 1000.00`, face = **$5,752.96** | **CORRECT** |
| Staging `QUIKRIDR.DBF` (`--reload-quikridr`) | `MUNIT N(10,5)`, stored `5.75296`, face = **$5,752.96** | **CORRECT** |
| Client QLAdmin Coverage tab | **$5,753.00** | **INCORRECT** |

**Converter remains correct at v57.39.** Issue #21K is a **deployment / QLAdmin data-path defect**, not a regression from Issue #27 (SL suppression removed the duplicate phase-3 row; PUA row unchanged).

---

## Symptom Evolution

| Display | Implied calculation | Matches? |
|---------|---------------------|:--------:|
| **$5,752.00** (original) | `trunc(5.75296, 3) × 1000 = 5.752 × 1000` | Original intake |
| **$5,753.00** (reopened) | `round(5.75296, 3) × 1000 = 5.753 × 1000` | **Yes** |
| **$5,753.00** (reopened) | `round(5752.96) = 5753` (whole-dollar display) | **Yes** |

The reopened screenshot value **`$5,753.00`** is **inconsistent with simple N(10,3) truncation** (which yields **$5,752.00**) and **inconsistent with a successful CSV reload into N(10,5)** (which yields **$5,752.96**).

This indicates the client environment is **not yet reading five-decimal stored units with a five-decimal display path**, or is applying an **additional rounding rule** on top of stored data.

---

## Hypothesis Test Results

| # | Hypothesis | Result | Evidence |
|---|------------|--------|----------|
| 1 | CSV still correct; active DBF structure not actually N(10,5) | **PLAUSIBLE — unverified in production** | Staging reload proves tooling works; **no client production DBF supplied** |
| 2 | Structure updated in wrong / unused table | **PLAUSIBLE** | Coverage tab reads **`QUIKRIDR`** per Help; five valuation tables also carry `MUNIT` — any remaining N(*,3) table could affect reports |
| 3 | DBFs updated but indexes/cache not rebuilt | **PLAUSIBLE** | Client UAT gate documented reindex **PENDING**; stale `QuikRdr.ntx` could serve old rows |
| 4 | QLAdmin display rounds Amount Ins despite N(10,5) storage | **PLAUSIBLE — best fit for $5,753.00** | `$5,753.00 = round(5.75296,3)×1000`; no repo source code, but math matches reopened screenshot |
| 5 | Load process recreates DBFs at N(10,3) | **PLAUSIBLE** | v57.39 batch emits **CSV only**; client import tooling not in repo — unknown path may still truncate |
| 6 | Screenshot uses stale / wrong data folder | **PLAUSIBLE — high priority** | Production migration gate **never PASS** in repo record; client may not be on `qladmin_issue21k` reload package |
| 7 | Another field drives displayed value (not `MUNIT`) | **UNLIKELY for Coverage tab** | Help / Issue #26: Amount Ins = **`MUNIT × MVPU`**; no `MAMTINS` field in quikridr layout |

---

## Confirmed Root Cause Mechanism (Repo-Proven)

### A. Converter is not the failure point

Rulebook maps `NUMBER_OF_UNITS → MUNIT` without precision transform. v57.39 output verified by:

- Direct CSV read
- `validate_issue21k_munit.py` — **PASS**
- `validate_issue21k_fleet.py` — **PASS** (1,065/1,065 sub-mill rows preserved)

### B. Structure-only migration is insufficient

`migrate_dbf_widen_units()` **copies existing row values** from old DBF to widened structure. Simulation:

- Seed N(10,3) with truncated `MUNIT = 5.752`
- Widen to N(10,5) **without CSV reload**
- Stored value remains **`5.752`**, face **`$5,752.00`**

**Conclusion:** Client must run **`--reload-quikridr`** (or equivalent CSV import) **after** widen. Field-size change alone cannot recover lost decimals.

### C. CSV reload path works when executed

2026-06-28 run:

```text
python qladmin_core/issue21k_units_migration.py --reload-quikridr
→ 6934 rows, MUNIT N(10,5), 010448806C PUA MUNIT=5.75296 face=$5752.96
```

Validators: **OVERALL PASS**.

---

## Most Likely Production Failure (Ranked)

1. **QUIKRIDR not reloaded from v57.39 CSV** after schema widen (truncated values remain, or wrong import path used).
2. **Active QLAdmin data folder is not the migrated/reloaded set** (stale DBF, wrong directory, pre-migration copy).
3. **QLAdmin Coverage display applies 3-decimal rounding** (or whole-dollar rounding) even when DBF stores 5 decimals — explains **$5,753.00** specifically.
4. **Indexes not rebuilt** after DBF replace — QLAdmin may read cached/indexed stale values.
5. **Five non-QUIKRIDR tables** still at N(*,3) — affects valuation/report paths; less likely for primary Coverage tab but required for full closure.

---

## What Is Ruled Out

| Ruled out | Evidence |
|-----------|----------|
| LifePRO source error | PPBEN `5.75296` / `1000.00` |
| v57.39 converter rounding | CSV `5.75296`; validator PASS |
| Issue #27 SL regression on PUA row | PUA row intact; SL source row suppressed from quikridr only |
| Repo staging DBF writer defect | Reload DBF stores `5.75296` correctly |

---

## Required Client Evidence (Not Yet Received)

To move from **inferred** to **proven** on production:

1. Path QLAdmin is using for live data (e.g. `C:\QLAdmin\Data`).
2. Production `QUIKRIDR.DBF` structure line for `MUNIT` (expect `N(10,5)` if migration applied).
3. Stored values for `010448806C`, MPHASE 2, plan `1708PA`: `MUNIT`, `MVPU`.
4. Confirmation whether `--reload-quikridr` was run **after** widen, or only `--migrate-dir`.
5. Reindex log (`QuikRdr.ntx` timestamp vs DBF timestamp).

---

## Recommendation

**Issue remains No-Go.** Route to **Dependency Gate → Deployment/DBF Remediation Agent**. Do **not** change converter logic unless client production DBF proves CSV wrong.

---

## Related Documents

- `Issue_21K_End_to_End_Trace_010448806C.md`
- `Issue_21K_Field_Metadata_Audit.md`
- `Issue_21K_Fleet_Impact_Analysis.md`
- `Issue_21K_Proposed_Fix.md`
