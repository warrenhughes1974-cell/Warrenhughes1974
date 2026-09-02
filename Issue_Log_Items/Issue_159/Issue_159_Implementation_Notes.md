# Issue #159 — Implementation Notes

**Issue:** #159 — L10/L14 traditional-life reserves at $0 (UW key mismatch)  
**Engine:** **v59.08**  
**Developed:** 2026-09-02  
**Code + Output remap applied** (PPBEN-letter remap of `quikridr` only)

---

## What changed

1. **Both `app.py` copies** — `map_rider_uwclass(val, plan=MPLAN)` so the next full batch keeps the #118 form-aware map (L10 S→SM, L14 N→NT / Q→PQ / T→ST / R→PR).
2. **Current Output** — remapped `quikridr.MUWCLASS` from `PPBEN_PolicyBenefit_Extract_20260831.csv` letters with `plan=`. 6,956 rows; **616** MUWCLASS deltas; every other field identical.
3. **Validator** — `tools/validators/validate_issue159_muwclass_plan_aware.py` (fail-closed). Register in `SMOKE_JOBS` at Closure.

Rate tables, PVO, MPREM, MPOLICY, and bands were not edited.

---

## Files touched

| File | Change |
|---|---|
| `app.py` | plan= + APP_VERSION v59.08 |
| `QLA_Migration/app.py` | same |
| `QLA_Migration/Output/quikridr.csv` | MUWCLASS remap |
| `tools/validators/validate_issue159_muwclass_plan_aware.py` | new |
| `Issue_Log_Items/Issue_159/tools/apply_issue159_muwclass_remap.py` | letter-sourced remap |
| `QLA_Migration/Archive/issue159_pre_remap/quikridr_pre_issue159.csv` | before snapshot |

---

## Before / after (UAT)

| Policy | Plan | Letter | Before | After |
|---|---|---|---|---|
| 9011189929C | 1L1095 | B | BL | BL |
| 9011190516C | 1L1095 | S | ST | SM |
| 9011193156C | 1L1095 | P | PR | PR |
| 9011059291C | 5L0110 | S | ST | ST |
| 9011206462C | 1L14SC | N | 00 | NT |
| 9011208194C | 1L14SC | T | 00 | ST |
| 9011207210C | 1L14SC | Q | 00 | PQ |

Counts: L10 ST→SM = 384; L14 00 split NT 101 / PQ 111 / PR 13 / ST 7.

---

## Not invented

L14 PQ/ST/PR reserve grids — source remains N-only. Those classes can still value at $0 after CSO reload.

---

## Rollback

Restore `QLA_Migration/Archive/issue159_pre_remap/quikridr_pre_issue159.csv` and revert the `map_rider_uwclass` argument in both `app.py` files.
