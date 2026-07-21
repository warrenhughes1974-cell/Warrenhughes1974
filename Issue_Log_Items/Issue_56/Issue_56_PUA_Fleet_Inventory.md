# Issue #56 — Full PUA fleet inventory (not just 1960PA / 960 PO PUA)

**Generated:** 2026-07-14  
**Question:** Is `960 PO PUA` / `1960PA` the only PUA plan to resolve?  
**Answer:** **No.**

---

## Summary

| Metric | Count |
|--------|------:|
| LifePRO PUA products (`PPBEN` PU) | **10** |
| QLA synthetic/catalog PUA `MPLAN` codes in use | **8** |
| PUA rider rows | **495** |
| Groups with LifePRO own CV in PAAGERAT but **no** QuikCvs on the QLA `MPLAN` | **9 of 10** LifePRO products |
| Already has QuikCvs on ridr plan key | **1** (`261PUA` only) |

Eric’s sample (`960 PO PUA` → `1960PA`) is **22 of 495** rows (~4%). Largest gap is **`670 PUA` → `1708PA`** (415 rows).

---

## All PUA groups (current Output)

| QLA MPLAN | LifePRO PUA | Policies | In quikplan? | QuikCvs on MPLAN | PAAGERAT CV | Needs plan + own rates? |
|-----------|-------------|---------:|:------------:|-----------------:|------------:|:-----------------------:|
| `1708PA` | `670 PUA` | 413 | No | 0 | 175 | **Yes** |
| `1705PA` | `670 PUA` | 2 | No | 0 | 175 | **Yes** |
| `1960PA` | `960 OL PUA` | 32 | No | 0 | 100 | **Yes** |
| `1960PA` | **`960 PO PUA`** | **22** | No | 0 | 200 | **Yes (Eric)** |
| `1960PA` | `960 65 PUA` | 16 | No | 0 | 66 | **Yes** |
| `1960PA` | `960 LP PUA` | 1 | No | 0 | 175 | **Yes** |
| `280EPA` | `980 PUA` | 3 | No | 0 | 132 | **Yes*** |
| `221EPA` | `621 PUA` | 1 | No | 0 | 71 | **Yes** |
| `2665PA` | `665 PUA` | 1 | No | 0 | 96 | **Yes*** |
| `1970PA` | `970 PUA` | 1 | Yes | 0 | 86 | **Yes** |
| `261PUA` | `961 PUA` | 1 | Yes | 486 | 132 | Has QuikCvs (verify vs PAAGERAT) |

\*Catalog plans `280PUA` / `265PUA` already have QuikCvs in rates, but riders use **`280EPA` / `2665PA`**, which do not — so QLA still falls back to base unless those `*PA` keys get plan+rates (or ridr is remapped — out of scope per SD-1 pattern).

---

## Special problem: one QLA code, four LifePRO tables

`1960PA` alone mixes **four** different LifePRO CV tables. One QuikCvs under `1960PA` cannot correctly serve OL + PO + 65 + LP. Same naming pattern may collide elsewhere if bases share a 4-char prefix.

---

## Recommendation for Issue #56 scope

| Approach | Meaning |
|----------|---------|
| **Pilot only** | `1960PA` + `960 PO PUA` (Eric) — proves New Era path |
| **Full Issue #56** | Every `*PA` / PUA `MPLAN` missing plan+CV/TV — **10 LifePRO products / ~494 riders** |
| **Must decide** | Unique QLA plan code per LifePRO PUA product (cannot share `1960PA` across four CV tables) |

PAAGERAT shows **CV** for these PUAs; **TV** not in PAAGERAT (0 rows) — TV source for Robert’s “full CV and TV” requirement needs a separate locate (Rate_Table / other) during Development.
