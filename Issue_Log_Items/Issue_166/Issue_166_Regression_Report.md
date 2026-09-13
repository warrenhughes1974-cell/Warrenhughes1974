# Issue #166 — Regression Report

**Issue:** #166 — Div Accumulation Crediting
**Framework stage:** Regression Agent
**Engine version:** v59.13
**Baseline:** `Issue_Log_Items/Issue_166/evidence/quikdvdp_pre_issue166.csv`
**Output directory:** `QLA_Migration/Output/`
**Valuation date:** 20260831
**Generated:** 2026-09-13
**Verdict:** **PASS**

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|---|---|
| Target | `quikdvdp.MDEPINT` (2,815) and year-end `MINTDATE` overlay (21) |
| Other quikdvdp fields | Gold deposit unchanged; six non-gold deposits refreshed from current 8/31 PPBENTYP/641 |
| Other tables | No row-count change (quikdvdp-only rebatch) |
| QuikUint / #95 | Untouched |

---

## 2. Row Count Comparison

| Table | After | Notes | OK? |
|---|---:|---|---|
| quikmstr | 5,083 | Unchanged vs #167 regression | Yes |
| quikridr | 6,956 | Unchanged | Yes |
| quikprmh | 211,709 | Unchanged | Yes |
| quikplan | 142 | Unchanged | Yes |
| quikclid | 32,285 | Unchanged | Yes |
| quikclnt | 13,598 | Unchanged | Yes |
| quikbenh | 41,465 | Unchanged | Yes |
| quikdvdp | 5,083 | Same as pre snapshot | Yes |

---

## 3. Non-Target Field Diff (quikdvdp)

| Check | Result |
|---|---|
| Header | MPOLICY, MDEPOSIT, MINTYTD, MDEPINT, MINTDATE — identical |
| Keys | Same 5,083 policies |
| MDEPINT | 2,815 changed (all former 4.00) |
| MINTDATE | 21 changed (year-end overlay) |
| MDEPOSIT | 6 changed (8/31 source refresh, not gold) |
| MINTYTD | Same 6 rows (0641 YTD on those refreshes) |
| Gold 9010728947C deposit | 1875.38 unchanged |

---

## 4. Prior Issue Fix Regression

Catalog: `Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md`

| Issue ID | Check | Result |
|---|---|---|
| **#166** | `validate_issue166_mdepint.py` | **PASS** |
| **#21D** | ISWL 4.50; non-ISWL now #95 buckets | **PASS** |
| **#95** | QuikUint / PDINTTBL | **PASS** (107/83) |
| **#2** | MPOLICY width-11 | **PASS** (316,753 fields) |
| **#116** | No future MINTDATE with a balance | **PASS** on current Output (WARN missing archive) |
| **#26** | `validate_issue26_mprem.py` | **N/A environmental** — script still pins `PPBEN`/`PPOLC` `20260530` (same class as #38). MPREM not in this emit. |

---

## 5. Schema Integrity

| Check | Result |
|---|---|
| Field order | Preserved |
| Field types | Preserved (2-decimal rate, YYYYMMDD date) |
| New blank MPOLICY | 0 |
| QuikUint schema | Unchanged |

---

## 6. Batch / Fleet Checks

| Check | Result |
|---|---|
| Full policy batch | No — targeted `quikdvdp` rebatch only |
| Unique MDEPINT | 2.00 / 3.50 / 4.50 only |
| ISWL 4.50 | 2,268 unchanged |

---

## 7. Failures

None on issue-owned tables. #26/#38 20260530 extract pins are pre-existing and out of this emit.

---

## 8. Recommendation

- [x] Advance to **Closure Agent**
