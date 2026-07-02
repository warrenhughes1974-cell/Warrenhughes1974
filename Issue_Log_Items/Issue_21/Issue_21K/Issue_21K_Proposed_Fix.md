# Issue #21K — Proposed Fix (Reopened)

**Issue:** #21K — PUA Amount Precision  
**Status:** Proposed — **not authorized for implementation**  
**Generated:** 2026-06-28  
**Engine:** v57.39

---

## Fix Classification

| Layer | Fix required? |
|-------|:-------------:|
| LifePRO source | No |
| v57.39 converter / rulebook | **No** |
| QLAdmin DBF deployment | **Yes** |
| QLAdmin display (possible) | **TBD — client/New Era** |

**Primary fix type:** **Deployment / DBF remediation** (environmental), not converter Development.

---

## Recommended Fix Path (Ordered)

### Step 1 — Dependency Gate (BLOCKING)

Client exports from **active QLAdmin data folder**:

1. `QUIKRIDR.DBF` structure — confirm `MUNIT N(10,5)`
2. Row values for `010448806C` MPHASE 2 / `1708PA`
3. DBF vs index timestamps
4. Confirmation of migration commands actually executed

**Do not proceed until stored production MUNIT is verified.**

---

### Step 2 — Full Six-Table Schema Migration

**Tool:** `qladmin_core/issue21k_units_migration.py --migrate-dir <QLAdmin_Data>`

| Table | Target MUNIT |
|-------|--------------|
| QUIKPOLX | N(11,5) |
| QUIKRIDR | N(10,5) |
| QUIKRVAL | N(10,5) |
| QUIKVALF | N(10,5) |
| QUIKVERR | N(7,5) |
| QUIKTVAL | N(10,5) |

**Prerequisite:** Full backup of all six DBFs + index sidecars.

**Warning:** Widen-only copies truncated values — **Step 3 is mandatory for QUIKRIDR.**

---

### Step 3 — QUIKRIDR CSV Reload (MANDATORY)

**Tool:**

```powershell
cd C:\Users\warren\Documents\GitHub\Warrenhughes1974
python qladmin_core\issue21k_units_migration.py --reload-quikridr
```

**Source CSV:** `QLA_Migration\Output\quikridr.csv` (v57.39 batch output)

**Deploy:** Copy staged `QLA_Migration\Output\qladmin_issue21k\QUIKRIDR.DBF` to active QLAdmin data directory (or run reload targeting production path once CLI supports `--out-dir` to production).

**Acceptance:** Stored `MUNIT = 5.75296` for `010448806C` PUA row.

---

### Step 4 — Reindex

Rebuild QUIKRIDR index (`QuikRdr.ntx`) and valuation table indexes per QLAdmin admin procedure.

**Acceptance:** Index timestamp ≥ DBF replace timestamp; policy search returns updated row.

---

### Step 5 — QLAdmin UI Validation

Open `010448806C` → Coverage tab → PUA row (`1708PA`):

| Check | Expected |
|-------|----------|
| Amount Ins | **$5,752.96** |

Spot-check: `010615191C` ($3,745.99), `010510671C` ($6,034.59).

---

### Step 6 — If DBF Correct but UI Still Wrong

Escalate to **New Era / QLAdmin vendor**:

- Coverage tab may apply `round(MUNIT, 3)` or whole-dollar rounding in display expression
- Request display fix to honor **N(10,5)** stored units for Amount Ins calculation
- Provide evidence: DBF stores `5.75296`, UI shows `$5,753.00`

**This is not fixable in converter CSV.**

---

## Options Explicitly Rejected

| Option | Reason |
|--------|--------|
| Truncate CSV MUNIT to 3 dp | Destroys correct data; masks defect |
| PUA-only converter rounding hack | 950 policies affected — fleet-wide field |
| Store face in new custom field | No approved alternate; violates schema |
| Re-open Issue #27 / SL logic | Unrelated — PUA row verified correct |

---

## Validation After Fix

```powershell
python tools\validators\validate_issue21k_munit.py
python tools\validators\validate_issue21k_fleet.py
```

Plus client UI sign-off on § Step 5.

---

## Rollback

1. Restore pre-migration DBF backups (six tables + indexes)
2. Reindex from restored files
3. Document rollback in Issue #21K closure record

---

## Converter Changes

**None recommended.** v57.39 CSV and staging DBF reload already PASS all validators.

Development Agent engagement is **only** required if Dependency Gate proves CSV wrong — currently **disproven**.

---

## Success Criteria

| Criterion | Target |
|-----------|--------|
| Production QUIKRIDR.MUNIT spec | N(10,5) |
| Stored MUNIT 010448806C PUA | 5.75296 |
| QLAdmin Amount Ins display | $5,752.96 |
| Fleet sub-mill preservation | 1065/1065 rows |
| Six-table migration complete | 6/6 |
