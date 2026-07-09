# Issue #36 — Implementation Notes (G4 Development)

**Issue:** #36 — Modal Premium factors at policy level (`quikmstr`)  
**Engine:** **v57.62**  
**Date:** 2026-07-09  
**Status:** Development complete — ready for Validation (G5)

---

## 1. What changed

After `quikridr` emit, the batch now:

1. **Copies** phase-1 plan modal factors from `quikplan` (or mapping fallback) onto every `quikmstr` row:
   - `SEMI` → `MSEMI`
   - `QTRL` → `MQTRL`
   - `MTHD` → `MMTHD` (monthly **direct** — independent)
   - `MTHB` → `MMTHB` (monthly **bank draft** — independent)
2. **Then** applies existing #21J PAC GL85 special modes:
   - PAC + mode 3 + plans `170858`/`17085M` → `MQTRL = 25.0000`
   - PAC + mode 6 + same plans → `MSEMI = 50.0000`

`MMODEPREM` and all other `quikmstr` / `quikridr` / `quikplan` fields are untouched.

---

## 2. Files changed

| File | Change |
|------|--------|
| `qla_core/modal_premium_factors.py` | Added `apply_plan_modal_factors_to_quikmstr`; shared `_phase1_mplan_lookup`; PAC uses shared helper |
| `app.py` | Import + call plan copy before PAC; **APP_VERSION v57.62** |
| `QLA_Migration/app.py` | Same as root `app.py` |
| `tools/validators/validate_issue36_quikmstr_modal_factors.py` | **New** G5 validator |

No rulebook schema changes (post-emit enrichment, same pattern as PAC).

---

## 3. Before / after traces (Output refreshed with v57.62 logic)

| Policy | Before (all four) | After MSEMI / MQTRL / MMTHD / MMTHB | Note |
|--------|-------------------|--------------------------------------|------|
| 010148856C | blank | 51.0140 / 26.0010 / 8.9964 / 8.9989 | Names-tab example; MMTHD≠MMTHB |
| 010713704C | blank | 52.5000 / 27.0000 / 9.1999 / 8.8018 | Census / #21J |
| 010560185C | blank | 52.0000 / **25.0000** / 9.0000 / 8.3333 | PAC **Q** special mode |
| 010442216C | blank | **50.0000** / 26.5000 / 9.0000 / 8.3333 | PAC **S** special mode |

**Fleet (self-check on current Output):**

| Metric | Value |
|--------|------:|
| Policies updated (plan copy) | 5,083 |
| Missing plan / factors | 0 / 0 |
| PAC quarterly overrides | 4 |
| PAC semiannual overrides | 8 |
| MMODEPREM changed | **0** |

---

## 4. Self-check commands

```bat
python tools\validators\validate_issue36_quikmstr_modal_factors.py
python tools\validators\validate_issue21j_modal_factors.py
```

---

## 5. Regression risks

| Risk | Mitigation |
|------|------------|
| Collapse MMTHD/MMTHB | Independent field map; validator checks differing plans |
| PAC overwritten by plan copy | Order: plan copy **then** PAC |
| MMODEPREM / #26 | Not in write set; validator asserts non-blank |
| quikplan missing in isolated batch | Falls back to `Modal_Premium_Factors_By_Plan.csv` |

---

## 6. Gate G4 checklist

- [x] Only approved scope implemented
- [x] Version bump both `app.py` files → **v57.62**
- [x] Validation script added
- [x] Implementation notes published
- [x] Before/after traces documented
- [x] No wholesale rewrite / schema reorder

**G4 status:** **PASS** — proceed to Validation Agent (G5).
