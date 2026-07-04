# Issue #38 — Regression Report (G6)

**Issue:** Dividend Accumulations  
**Date:** 2026-07-04  
**Engine:** v57.44 (post-fix batch output)  
**Status:** **PASS**

---

## Protected-issue validators

| Issue | Validator | Result |
|-------|-----------|--------|
| #25 MPOLICY padding | `validate_mpolicy_width.py` | **PASS** — 279,538 fields, 0 short |
| #26 MPREM mapping | `validate_issue26_mprem.py` | **PASS** — trace policies; MMODPREM unchanged |
| #21D MDEPINT | `validate_issue21d_mdepint.py` | **PASS** — ISWL 4.50; non-ISWL 4.00 |

---

## Scope isolation

| Check | Result |
|-------|--------|
| quikdvdp row count | 5,083 — unchanged |
| quikridr row count | 6,934 — unchanged |
| quikmstr row count | 5,083 — unchanged |
| Rulebook `Sync_Rulebook_quikdvdp.csv` | **Unchanged** |
| Columns changed | MDEPOSIT, MINTYTD, MINTDATE on expected rows only |

---

## G6 gate: **PASS**
