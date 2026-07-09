# Issue #47 — Regression Report (G6)

**Issue:** Bill Day zero → Paid-To day  
**Date:** 2026-07-09  
**Engine:** **v57.65**  
**Status:** **PASS**

---

## Scope

| In scope | Out of scope |
|----------|--------------|
| `quikmstr.MBILLDAY` only | Premiums, status, dates, other tables |
| Zero → Paid-To day fallback | Non-zero #21B values |

---

## Checks run

```text
python Issue_Log_Items/Issue_47/scripts/_g6_regression_checks.py
→ PASS
```

| Metric | Value |
|--------|------:|
| quikmstr rows | 5083 |
| Schema column order match | Yes |
| MPOLICY max length | 10 (#25) |
| Remaining `MBILLDAY` zeros | **0** |
| Risk delta vs output fails | **0** |
| Paid≠Billed edge fails | **0** |

Evidence: `evidence/issue47_regression_summary.csv`

---

## Prior fix preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY ≤ 10 chars | **PASS** |
| Issue #21B samples 15/28/22/12 | **PASS** |
| Issue #26 `quikridr.MPREM` column present | **PASS** |
| 6 Paid-To ≠ Billed-To edges use Paid-To day | **PASS** |

---

## Untouched surfaces (by design)

- `MPAIDTO` / `MBILLTO` mapping formulas  
- `MSTATUS` / Issue #13  
- `MMODEPREM` / modal factors (#36)  
- `quikridr.MPREM` (#26)  
- `MBLLDOM` / `MORGBLLDOM` (still blank)

---

## G6 gate: **PASS**

**Next:** Closure Agent (G7) — resolution summary + commit/push.
