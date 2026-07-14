# Issue #54 — QuikBenh vs Loan History UI (14560K)

**Date:** 2026-07-11  
**Source:** `docs/QUIKBENH.DBF`  
**UI:** Loan History - [14560K]

## Verdict

**YES — QuikBenh is the multi-line Loan History grid source.**

| UI column | QuikBenh field |
|-----------|----------------|
| Transaction | `MBENTYP` (code → label) |
| Date | `MDATE` |
| Amount | `MBEN` |
| Balance | **Not stored** — UI running total |
| Footer Accrued / Current / Paid To | **QuikLoan** (`MLOANACCR` / `MLOANBAL` / `MLOANIDT`) |

## Policy 14560K

- **221** QuikBenh rows  
- Schema: `MPOLICY`, `MBENTYP`, `MDATE`, `MBEN`

### Inferred MBENTYP map (from screenshot match)

| MBENTYP | Loan History label | Evidence |
|---------|-------------------|----------|
| **10** | Loans Granted | 92 rows @ 0.71; matches 10/31/1991, 11/29/1991, 12/31/1991… |
| **11** | Interest Added | 45 rows; 12/31/1991 amount **0.65** exact |
| **12** | Loan Payments | 3 rows; 12/31/1991 amount **2.69** exact |
| **20** | Loan Payments - Div | 7 rows; 02/22/1993 amount **2.95** exact |

Other types on this policy (2, 3, 6, 7, 16, 18, 19) — need Help/New Era labels (may be non-loan benefit history mixed in same table).

## Screenshot match

Exact date+amount matches on visible window: **19 / 40**.  
Unmatched lines are mostly **date drift of 1–3 days** (e.g. UI 01/31/1992 vs Benh 02/03/1992; UI 04/30 vs Benh 04/29) with the same 0.71 type-10 amount still present nearby — not missing history.

## Implication for Issue #54

| Layer | Table |
|-------|-------|
| Loan History **grid** | **`quikbenh`** (multi-row; loan types 10/11/12/20+) |
| Loan History **footer** / coverage loan summary | **`quikloan`** (one current row) |
| Not the grid | QuikActg (GL chart), QuikPrmh (premiums; partial APL echo only) |

**Conversion direction:** emit LifePRO loan history events into `quikbenh` with correct `MBENTYP`, plus keep `#32` QuikLoan for current balance footer.

Evidence: `issue54_quikbenh_14560K.csv`
