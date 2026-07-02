# Issue #21K — End-to-End Trace: Policy 010448806C

**Policy:** `010448806C` (LifePRO `9010448806`)  
**Focus row:** MPHASE **2**, MPLAN **`1708PA`** (PUA)  
**Engine:** v57.39  
**Generated:** 2026-06-28

---

## Trace Summary

| Stage | MUNIT | MVPU | Face (MUNIT × MVPU) | Match LifePRO? |
|-------|------:|-----:|--------------------:|:--------------:|
| LifePRO PPBEN (BENEFIT_SEQ 2, PU) | **5.75296** | **1000.00** | **$5,752.96** | — |
| v57.39 `quikridr.csv` | **5.75296** | **1000.00** | **$5,752.96** | **YES** |
| Staging `QUIKRIDR.DBF` (reload) | **5.75296** | **1000.00** | **$5,752.96** | **YES** |
| QLAdmin Coverage (client screenshot) | *unknown stored* | *unknown* | **$5,753.00** | **NO** |

**Precision loss location:** **After CSV** — client QLAdmin path (unverified production DBF).

---

## Stage 1 — LifePRO Source

**File:** `QLA_Migration/Source/PPBEN_PolicyBenefit_Extract_20260530.csv`  
**Rulebook source alias:** PPBEN / benefit extract  
**Crosswalk:** `9010448806` → `010448806C`

### PPBEN rows for `9010448806`

| BENEFIT_SEQ | BENEFIT_TYPE | NUMBER_OF_UNITS | VALUE_PER_UNIT | Notes |
|------------:|:-------------|----------------:|---------------:|-------|
| 1 | BA | 5.77800 | 1000.00 | Base coverage |
| **2** | **PU** | **5.75296** | **1000.00** | **PUA — trace target** |
| 3 | SL | 5.77800 | 1000.00 | Substandard (suppressed from quikridr in v57.39 #27) |

**PUA expected face:** `5.75296 × 1000.00 = **$5,752.96**`

**Source columns (rulebook):**

| LifePRO field | QLAdmin target |
|---------------|----------------|
| `NUMBER_OF_UNITS` | `MUNIT` |
| `VALUE_PER_UNIT` | `MVPU` |
| `BENEFIT_SEQ` | `MPHASE` (via mapping) |

---

## Stage 2 — Converter CSV (v57.39)

**File:** `QLA_Migration/Output/quikridr.csv`  
**Verified:** 2026-06-28 (post–Issue #27 batch)

### All quikridr rows for `010448806C`

| MPHASE | MPLAN | MUNIT | MVPU | MPREM | MRIDRID | Face |
|-------:|-------|------:|-----:|------:|---------|-----:|
| 1 | 170858 | 5.77800 | 1000.00 | 18.96000 | 588929 | $5,778.00 |
| **2** | **1708PA** | **5.75296** | **1000.00** | .00 | 588929 | **$5,752.96** |

**Note:** v57.39 emits **2 rows** (SL phase suppressed). Prior v57.38 snapshots showed 3 rows including duplicate SL coverage.

### Display simulation from CSV values

| Display rule | Computed Amount Ins |
|--------------|--------------------:|
| Exact (CSV) | **$5,752.96** |
| 3 dp truncate | $5,752.00 |
| 3 dp round | **$5,753.00** |
| Whole-dollar round | **$5,753.00** |

**CSV verdict:** **CORRECT** — full five-decimal `MUNIT` preserved.

**Converter function path:** Generic rulebook loop (`NUMBER_OF_UNITS → MUNIT`); PUA plan rewrite via `_apply_pua_rider_inheritance()` — **does not alter MUNIT/MVPU**.

---

## Stage 3 — DBF Generation (Repo Staging)

**Command run:**

```text
python qladmin_core/issue21k_units_migration.py --reload-quikridr
```

**Output:** `QLA_Migration/Output/qladmin_issue21k/QUIKRIDR.DBF`

| Check | Result |
|-------|--------|
| Row count | 6934 |
| Structure | `MUNIT N(10,5)` |
| `010448806C` / ph2 / `1708PA` MUNIT | **5.75296** |
| MVPU | **1000.0** |
| Face | **5752.96** |

**Validator:** `validate_issue21k_munit.py` — **OVERALL PASS**

### Structure-only migration trap (documented)

If client ran **`--migrate-dir` only** on an existing N(10,3) DBF containing truncated `5.752`:

- Widened structure = N(10,5)
- Stored value remains **5.752**
- Face = **$5,752.00** (still wrong; not $5,753.00)

**CSV reload is mandatory** to restore `5.75296`.

---

## Stage 4 — Production QLAdmin (Client — Not Verified)

**Not available in repo.** Client UAT gate (2026-06-27) documented:

- Production path `C:\QLAdmin\Data` — not validated here
- Six-table migration — **PENDING**
- QUIKRIDR production reload — **PENDING**
- Reindex — **PENDING**

### Client screenshot analysis

| Displayed | Expected | Delta |
|----------:|---------:|------:|
| **$5,753.00** | **$5,752.96** | **+$0.04** (round-up) |

**Best mathematical fit:** `round(5.75296, 3) × 1000 = 5753.00` or `round(5752.96) = 5753`.

This is **not** explainable by successful five-decimal storage + exact multiply display.

---

## Stage 5 — Runtime Display (QLAdmin)

**Authoritative repo reference:** `Issue_26_Field_Definition_Report.md`

| QLAdmin label | Source |
|---------------|--------|
| Units | `QUIKRIDR.MUNIT` |
| Val/U | `QUIKRIDR.MVPU` |
| **Amount Ins** (Coverage tab) | **Derived: MUNIT × MVPU** |

No `MAMTINS` stored field exists in `QUIKRIDR` layout.

**Reopened failure** therefore implies one of:

1. Stored `MUNIT` in **active** production DBF is not `5.75296`, **or**
2. QLAdmin applies **rounding/truncation in the display expression**, **or**
3. QLAdmin reads **stale/wrong DBF/index** not matching v57.39 reload package.

---

## Stage 6 — Environment Verification Checklist

| Check | Repo status | Client action required |
|-------|-------------|------------------------|
| QLAdmin data folder = v57.39 output path | Unknown | Confirm path |
| `QUIKRIDR.DBF` timestamp post-migration | Staging only | Compare production file date |
| `MUNIT` field = N(10,5) in **active** DBF | Staging PASS | Export production structure |
| CSV reload executed after widen | Staging PASS | Confirm client ran reload |
| `QuikRdr.ntx` rebuilt | PENDING | Reindex and verify timestamp |
| Other five MUNIT tables migrated | PENDING | Run full six-table migrate |

---

## Conclusion

For policy **`010448806C`**, the v57.39 conversion pipeline delivers **correct PUA precision through CSV and staging DBF reload**. The client-reported **`$5,753.00`** display confirms the defect persists **downstream** — in production DBF deployment, index/cache, or QLAdmin display rounding — **not** in LifePRO source or converter CSV.

**Next:** Dependency Gate for production DBF evidence → Deployment/DBF Remediation Agent.
