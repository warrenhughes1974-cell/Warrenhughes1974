# Issue #47 — Implementation Notes

**Issue:** #47 — Bill Day zero fallback from Paid-To day  
**Framework stage:** Development Agent (G4)  
**Engine:** **v57.65**  
**Date:** 2026-07-09  

---

## Changes

| File | Change |
|------|--------|
| `app.py` | `APP_VERSION=v57.65`; quikmstr `MBILLDAY` interceptor — if 0/blank, day of `PAID_TO_DATE` |
| `QLA_Migration/app.py` | Same (kept in sync) |
| `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv` | Transformation note documents Issue #47 fallback |
| `QLA_Migration/_validate_issue47_billday.py` | Fleet + sample validation script |

---

## Behavior

1. Map `POLICY_BILL_DAY → MBILLDAY` as before (#21B).  
2. If normalized `MBILLDAY` is `''` / `0` / `0.0` / `00`, set from `extract_day(PAID_TO_DATE)` (fallback `MPAIDTO` if present), as unpadded integer string (`28`, not `028`).  
3. Non-zero specified bill days are **never** overwritten.

---

## Before / after (post re-emit)

| Policy | Before | After | Notes |
|--------|-------:|------:|-------|
| `018187C` | 0 | **28** | BA screenshot |
| `010713704C` | 15 | 15 | #21B preserve |
| `010765930C` | 28 | 28 | #21B preserve |
| `010718309C` | 22 | 22 | #21B preserve |
| `010818663C` | 12 | 12 | #21B preserve |

Fleet validate (self-check): **2967** source zeros now have Paid-To day; **0** mismatches; **2116/2116** non-zero parity.

---

## Explicitly not changed

- Non-zero `POLICY_BILL_DAY` path (#21B)  
- `MPAIDTO` / `MBILLTO`  
- `MBLLDOM` / `MORGBLLDOM`  
- Issue #25 MPOLICY padding / #26 MPREM / #36 modal factors / #13 MSTATUS  

---

## Self-check run

```
python QLA_Migration/_validate_issue47_billday.py
→ PASS (018187C=28; fleet_mismatches=0)
```

Quikmstr single-table re-emit completed under **v57.65**.

---

## Ready for

**Validation Agent (G5)** → Regression (G6) → Closure (G7).
