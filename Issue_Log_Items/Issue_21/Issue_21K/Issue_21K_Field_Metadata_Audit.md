# Issue #21K — Field Metadata Audit

**Issue:** #21K — MUNIT precision  
**Generated:** 2026-06-28  
**Engine:** v57.39

---

## Purpose

Confirm current **field definitions** and **stored values** for `MUNIT` across the six authorized QLAdmin tables, distinguishing **template/spec** from **active DBF files**.

---

## Six-Table Schema Registry

**Source:** `qladmin_core/qladmin_units_schema.py`

| Table | MUNIT before (Issue 21K baseline) | MUNIT after (target) | Width |
|-------|-----------------------------------|----------------------|------:|
| **QUIKPOLX** | N(11,3) | **N(11,5)** | 11 |
| **QUIKRIDR** | N(10,3) | **N(10,5)** | 10 |
| **QUIKRVAL** | N(10,3) | **N(10,5)** | 10 |
| **QUIKVALF** | N(10,3) | **N(10,5)** | 10 |
| **QUIKVERR** | N(7,3) | **N(7,5)** | 7 |
| **QUIKTVAL** | N(10,3) | **N(10,5)** | 10 |

**Field changed:** `MUNIT` only.  
**Not changed by 21K:** `MSAVEUNIT N(10,3)`, `MVPU N(8,2)`, `MPREM N(10,2)`, etc.

---

## QUIKRIDR Full Layout (Post-21K)

**Source:** `qladmin_core/qladmin_units_schema.py` → `QUIKRIDR_DBF_LAYOUT`  
**Help reference:** QLAdmin Help §7.203 (QuikRidr)

| Field | Type | Notes |
|-------|------|-------|
| MPOLICY | C(10) | Policy key |
| MPHASE | N(2,0) | Phase / benefit seq |
| MPLAN | C(6) | Plan code (PUA → `{base}PA`) |
| **MUNIT** | **N(10,5)** | **Issue #21K target** |
| **MVPU** | N(8,2) | Value per unit — unchanged |
| MPREM | N(10,2) | Premium per unit |
| MSAVEUNIT | N(10,3) | Save units — **still 3 dp** |
| MRIDRID | C(12) | Rider id |
| … | … | 40 fields total |

---

## Active DBF Verification (Repo Staging — 2026-06-28)

**File:** `QLA_Migration/Output/qladmin_issue21k/QUIKRIDR.DBF`  
**Manifest:** `QLA_Migration/Output/qladmin_issue21k/issue21k_schema_migration_manifest.json`

### Structure excerpt (manifest)

```text
MUNIT N(10,5)
MVPU N(8,2)
MSAVEUNIT N(10,3)
```

### Stored value — policy 010448806C PUA

| Field | Value |
|-------|------:|
| MPOLICY | 010448806C |
| MPHASE | 2 |
| MPLAN | 1708PA |
| **MUNIT** | **5.75296** |
| MVPU | 1000.0 |
| Implied face | **5752.96** |

**Staging verdict:** Structure and stored value **both correct** when `--reload-quikridr` is used.

---

## Production DBF Verification

| Table | Production structure verified? | Production stored MUNIT verified? |
|-------|:------------------------------:|:---------------------------------:|
| QUIKPOLX | **NO** | **NO** |
| QUIKRIDR | **NO** | **NO** |
| QUIKRVAL | **NO** | **NO** |
| QUIKVALF | **NO** | **NO** |
| QUIKVERR | **NO** | **NO** |
| QUIKTVAL | **NO** | **NO** |

**Client claim:** field sizes "reportedly increased."  
**Repo cannot confirm** without production DBF export. Staging proves tooling **can** produce N(10,5); it does **not** prove client applied reload to **active** QLAdmin data folder.

---

## Widen-Only vs Reload Comparison

| Operation | Structure | Stored MUNIT (from 5.752 seed) | Face @ MVPU=1000 |
|-----------|-----------|-------------------------------:|-----------------:|
| N(10,3) original | N(10,3) | 5.752 | $5,752.00 |
| **Widen only** (`migrate_dbf_widen_units`) | N(10,5) | **5.752** (unchanged value) | **$5,752.00** |
| **CSV reload** (`write_quikridr_dbf`) | N(10,5) | **5.75296** | **$5,752.96** |

**Critical finding:** Metadata audit must verify **both** field definition **and** post-reload stored values. Structure change without reload leaves truncated numeric content.

---

## Related CSV Tables (Conversion Output)

v57.39 batch emits **CSV only** for quikridr — no automatic production DBF.

| File | In repo output? | MUNIT precision |
|------|:-----------------:|-----------------|
| `quikridr.csv` | Yes | Full (5 dp observed) |
| `quikpolx.csv` | **No** | N/A — not in batch output |
| Valuation CSVs | **No** | N/A — QLAdmin-native tables |

**Implication:** `QUIKPOLX`, `QUIKRVAL`, `QUIKVALF`, `QUIKVERR`, `QUIKTVAL` must be migrated in place on client DBF folder; conversion does not regenerate them.

---

## Index / Sidecar Files

QLAdmin typically uses index sidecars (e.g. `QuikRdr.ntx`). Client UAT gate documented reindex as **PENDING**.

| Risk | If index not rebuilt after DBF replace |
|------|----------------------------------------|
| Stale lookup | Policy row may resolve to old truncated values |
| Display mismatch | UI shows cached/indexed face inconsistent with DBF body |

**Audit requirement:** Compare DBF vs `.ntx` file timestamps after migration.

---

## Display Field Mapping (No Stored Amount Ins)

| UI label | DBF source | Stored? |
|----------|------------|:-------:|
| Units | MUNIT | Yes |
| Val/U | MVPU | Yes |
| **Amount Ins** | **MUNIT × MVPU** | **No — calculated** |

There is **no** `MAMTINS` column in QUIKRIDR. Display rounding/truncation in QLAdmin runtime is a **valid remaining failure point** even when DBF stores `5.75296`.

---

## Audit Conclusion

| Layer | N(10,5) confirmed? |
|-------|:------------------:|
| Schema registry (repo) | **YES** |
| Staging QUIKRIDR.DBF (reload) | **YES** |
| Client production DBFs | **NOT VERIFIED** |
| QLAdmin display formatter | **NOT VERIFIED** |

**Metadata audit status:** **INCOMPLETE for production** — Dependency Gate required.

---

## Client Export Request

Please supply for active QLAdmin data directory:

1. `DBSTRUCT QUIKRIDR` or equivalent structure dump showing `MUNIT` line
2. Row dump: `010448806C`, MPHASE 2, MPLAN `1708PA` — `MUNIT`, `MVPU`
3. File timestamps: `QUIKRIDR.DBF`, `QuikRdr.ntx`
4. Migration manifest if `--migrate-dir` was run
