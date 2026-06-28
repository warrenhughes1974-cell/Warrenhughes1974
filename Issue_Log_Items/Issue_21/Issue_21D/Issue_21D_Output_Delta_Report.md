# Issue #21D — Output Delta Report (v57.35 → v57.36)

**Date:** 2026-06-27  
**Baseline:** v57.35 (documented Development metrics)  
**Current:** v57.36 (`QLA_Migration/Output/` full batch)

**Note:** No archived v57.35 output snapshot on disk; row-count baseline from Development Agent evidence. Field-level delta analysis performed on v57.36 output against documented v57.35 expectations.

---

## 1. Table row-count comparison

| Table | v57.35 | v57.36 | Delta | Authorized? |
|-------|--------|--------|-------|-------------|
| quikmstr.csv | 5,083 | 5,083 | 0 | ✅ |
| quikridr.csv | 7,002 | 7,002 | 0 | ✅ |
| quikplan.csv | 141 | 141 | 0 | ✅ |
| quikclid.csv | 46,753 | 46,753 | 0 | ✅ |
| **quikclnt.csv** | **13,502** | **13,514** | **+12** | ✅ Track B1 |
| quikprmh.csv | 205,577 | 205,577 | 0 | ✅ |
| quikmemo.csv | 4,380 | 4,380 | 0 | ✅ |
| quikdvdp.csv | 5,083 | 5,083 | 0 | ✅ |

**Unexpected row-count changes:** None

---

## 2. quikdvdp field delta (Track A)

| Field | v57.35 | v57.36 | Change scope |
|-------|--------|--------|--------------|
| MDEPINT | All 5,083 @ 4.00 | 2,268 @ 4.50; 2,815 @ 4.00 | **ISWL only** |
| MDEPOSIT | Unchanged | Unchanged | — |
| MINTYTD | Unchanged | Unchanged | — |
| MINTDATE | Unchanged | Unchanged | — |
| MPOLICY | Unchanged | Unchanged | — |

**Non-ISWL MDEPINT changes:** **0** (all remain 4.00)  
**ISWL MDEPINT changes:** **2,268** (all to 4.50)

**Unexpected quikdvdp changes:** None

---

## 3. quikclnt field delta (Track B1)

| Aspect | v57.35 | v57.36 |
|--------|--------|--------|
| Row count | 13,502 | 13,514 (+12) |
| New MCLIENTIDs | — | 12 recovered from RNA (CANCEL_DATE NULL literal fix) |
| Schema / field order | Baseline | Unchanged |
| Duplicate MCLIENTID | 0 | 0 |

**Recovered client IDs (sample):** 592064, 607190, 589330, 589331, 604080, 705619, 709065, 710463, 712148, 712432, 712433, 713149

**Excluded by design:** 598766 (cancelled in source)

---

## 4. Tables with zero delta (no #21D touch)

| Table | Status |
|-------|--------|
| quikmstr | No row or field changes from #21D |
| quikridr | No MPREM/MPLAN/MUNIT changes |
| quikplan | NFOINT unchanged for ISWL |
| quikclid | No row-count change |
| quikmemo | No grain change |
| quikprmh | Unchanged |

---

## 5. Blank-name population delta

| Metric | v57.35 | v57.36 |
|--------|--------|--------|
| Both-blank (population CSV) | 25 | 9 |
| B1-target fixed | 0 | 7 |
| RNA-deficient remainder | 18 planned | **9 actual** (additional 7 recovered beyond B1 list via +12 quikclnt rows) |

---

## 6. Unexpected differences

| Item | Assessment |
|------|------------|
| quikclnt +12 rows | ✅ Expected (Track B1) |
| MDEPINT ISWL 4.50 | ✅ Expected (Track A) |
| All other tables | ✅ No unexpected delta |

```text
No unexpected output differences detected.
```

---

*Output delta report complete.*
