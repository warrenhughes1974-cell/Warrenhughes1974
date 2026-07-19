# DG-R-001 — Change Log

**Status:** Applied  
**Date:** 2026-07-18  
**Data region:** `Q:\CSO\CSO_Test_6_30_2025`  
**Backup:** `Q:\CSO\CSO_Test_6_30_2025_backup_DG-R-001_20260718`  
**Decision:** Remap G/V → C; delete QuikList groups GTEST01 / TERMG / TEST1; do not create G/V in QuikComp

---

## Pre-flight inventory (before writes)

| Check | Result |
|-------|--------|
| QuikComp distinct MCOMP | `C` = 1 only (G/V absent) |
| C present exactly once | **Yes** (gate passed) |
| QuikList total rows | 3 |
| QuikList delete-set (trim MGROUP) | **3** — TEST1 (G), GTEST01 (V), TERMG (G) |
| QuikList MCOMP in (G,V) | 3 |
| QuikChrt MCOMP G / V | 37 / 34 (**71** total) |
| QuikAgts MCOMP G/V | 0 |
| QuikActg MCOMP G/V | 0 |
| QuikMstr policies last non-space char G/V | **0 / 0** (flag only; no auto-fix) |
| Unexpected QuikList delete count | No (exactly 3) |

### Dependent scan (informational)

| Table | Finding |
|-------|---------|
| QuikChrt | No `MGROUP` field |
| `quikgrpimp.dbf` | 3 rows with `MGROUP=TERMG` — **out of scope** for this item (not in approved write list); residual noted |

---

## Backup

Created folder `Q:\CSO\CSO_Test_6_30_2025_backup_DG-R-001_20260718` with copies of:

- `quiklist.dbf`, `quiklist.dbt`, `QUIKLIST.ntx`
- `QUIKCHRT.DBF`, `QUIKCHRT.ntx`
- `quikagts.dbf`, `quikagts.dbt`, `QUIKAGTS.ntx`
- `quikactg.dbf`, `QUIKACTG.ntx`
- `QUIKCOMP.dbf`, `QUIKCOMP.ntx`

**12 files.** Backup completed before mutations.

---

## Mutations applied

### 1. QuikList — DELETE (3 rows)

| MGROUP | Prior MCOMP | Action |
|--------|-------------|--------|
| TEST1 | G | Deleted |
| GTEST01 | V | Deleted |
| TERMG | G | Deleted |

- Method: `dbf` package — mark deleted + `pack()`
- Rows after: **0**
- No other QuikList rows existed (keep-set empty)

### 2. QuikChrt — UPDATE MCOMP G/V → C (71 rows)

| From | Count |
|------|------:|
| G → C | 37 |
| V → C | 34 |
| Already C (unchanged) | 22 |
| Deleted-flagged record (skipped) | 1 (header still shows 94 physical slots; dbfread active rows = 93) |

- Method: surgical binary update of MCOMP byte (field length 1 at record offset 1).  
  Reason: Python `dbf` library could not parse this file’s field-descriptor reserved bytes (`FieldMissingError` / empty structure); `dbfread` reads it correctly. Binary path preserves header/structure.
- Post: all 93 active rows `MCOMP=C`; residual G/V = **0**

### 3. QuikAgts / QuikActg

- Pre-flight G/V = 0 → **no writes**
- SHA-256 identical to backup (unchanged)

### 4. QuikComp

- **No insert** of G or V
- Still exactly one row: `MCOMP=C`
- SHA-256 identical to backup (unchanged)

---

## Post counts (live region)

| Table | Rows | MCOMP G/V remaining | Notes |
|-------|-----:|--------------------:|-------|
| QuikList | 0 | 0 | All three test groups removed |
| QuikChrt | 93 | 0 | All active rows C |
| QuikAgts | 4843 | 0 | Unchanged vs backup |
| QuikActg | 87 | 0 | Unchanged vs backup |
| QuikComp | 1 | n/a | C only |

---

## Index / memo notes

- **NTX indexes** (`QUIKLIST.ntx`, `QUIKCHRT.ntx`, etc.) were **not** rebuilt. QLAdmin may need **reindex** after DBF edits.
- QuikList `.dbt` memo sidecar retained; table is empty after pack.
- QuikChrt has no memo file.

---

## Helper scripts (item folder)

- `_preflight_inventory.py` — read-only inventory
- `_apply_dgr001.py` — backup + QuikList delete (QuikChrt remap completed via follow-up binary write after `dbf` parse failure)

---

## Forbidden actions (confirmed not done)

- Did not create company codes G or V in QuikComp
- Did not edit QuikPlan / QuikDate / plan-value tables
- Did not delete QuikList rows outside the three named groups
- Did not change data_governance rule logic or conversion `app.py`
