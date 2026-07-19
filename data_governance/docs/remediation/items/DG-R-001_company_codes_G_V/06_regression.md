# DG-R-001 — Regression

**Date:** 2026-07-18  
**Result:** **PASS** (non-candidates unchanged; no QuikPlan/QuikDate edits)

---

## Guards checked

### 1. QuikComp other codes unchanged

| Check | Result |
|-------|--------|
| Codes before | `C` only |
| Codes after | `C` only |
| G/V inserted? | **No** |
| File SHA vs backup | **Identical** |

### 2. QuikList rows outside delete set

| Check | Result |
|-------|--------|
| Keep-set before apply | Empty (only the three named groups existed) |
| Unexpected deletes | **None** — deleted exactly TEST1, GTEST01, TERMG |
| Rows after | 0 |

### 3. QuikAgts / QuikActg non-G/V rows

| Table | G/V before | Writes | SHA vs backup |
|-------|-----------:|--------|---------------|
| QuikAgts | 0 | None | **Identical** |
| QuikActg | 0 | None | **Identical** |

### 4. QuikPlan / QuikDate / plan-value tables

| Check | Result |
|-------|--------|
| In approved write list? | No |
| Opened for mutation by apply? | **No** |
| Post SHA (evidence of presence only) | QuikPlan `eb0f889239aaa13c1bbccb2d4ef8a9229ba13b89444d20e3431664563be77fae`; QuikDate `3e7be7e055e7e565666c517946caa85a381433b36606b85c674d1c9830b26528` |

No plan-value tables were modified under this item.

### 5. QuikChrt rows already coded C

| Check | Result |
|-------|--------|
| Pre-count already C | 22 |
| Remap applied only when MCOMP byte was G or V | Yes (37 + 34) |
| Post all active rows C | Yes (93) |

### 6. Prior CLOSED DG-R items

None yet — N/A.

---

## Changed vs backup (expected)

| File | Changed vs backup |
|------|-------------------|
| `quiklist.dbf` | Yes (3 deletes → empty) |
| `QUIKCHRT.DBF` | Yes (71 MCOMP remaps) |
| `quikagts.dbf` | No |
| `quikactg.dbf` | No |
| `QUIKCOMP.dbf` | No |

---

## DG-R-002 implication

The three QuikList groups that also failed billing-default rules under DG-R-002 (`GTEST01`, `TERMG`, `TEST1`) are **deleted**. DG-R-002 should be treated as **N/A / close or defer** at control-tower close of DG-R-001 (no List rows left to fix defaults on).

Residual: `quikgrpimp` still references `TERMG` — separate from QuikList defaults; not part of DG-R-002 as scoped to List billing defaults unless control tower expands it.
