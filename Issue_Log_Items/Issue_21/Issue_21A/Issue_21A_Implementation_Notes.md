# Issue #21A — Implementation Notes

**Issue:** #21A — NFO / Dividend Options  
**Date:** 2026-07-04  
**Converter version:** v57.47  
**Framework stage:** Development (G4)

---

## Changes applied

| File | Change |
|---|---|
| `app.py` | v57.47 — PPBENTYP `NON_FORFEITURE` cache prefers `BF_NON_FORFEITURE` when `TYPE_CODE=BF` |
| `QLA_Migration/app.py` | Mirror of root `app.py` |
| `Master_Value_Translation.csv` | Added `NF_1→1`, `NF_2→1`, `NF_9→0` |
| `QLA_Migration/Mapping/Master_Value_Translation.csv` | Mirror |
| `tools/validators/validate_issue21a_mnfopt.py` | Post-dev trace + domain validation |

**Preserved (unchanged):**

- Enrich-on-zero guard (`MNFOPT`/`MDIVOPT` only pulled from `lifepro_extra` when rulebook value is `0`/blank).
- `NF_3`–`NF_6` translation entries (`NF_4→0`, `NF_5→0`, passthrough for 3/6).
- `MDIVOPT` / dividend cache logic.
- `MPOLICY` (#25), `MPREM` (#26), `quikplan.NFOINT`.

---

## Root cause fix

**Track A:** ISWL/BF policies store NFO election on `BF_NON_FORFEITURE`; engine cache read only `NON_FORFEITURE` → blank → `MNFOPT=0`.

**Track B:** LifePRO code **2** (APL/RPU) passthrough to QLAdmin **2**; SME: codes **1** and **2** → **APL (`MNFOPT=1`)** because APL is attempted first.

**Safety:** Code **9** (83 BF policies) may enter cache after Track A fix; `NF_9→0` prevents invalid `MNFOPT=9` (QLAdmin domain is 0–3).

---

## Trace policy expectations (after batch rerun)

| MPOLICY | Source | Current (v57.46) | Expected (v57.47) | Notes |
|---|---|:---:|:---:|---|
| 010765930C | BF_NON_FORFEITURE=1 | 0 | **1** | Cache + NF_1 |
| 010718309C | BF_NON_FORFEITURE=1 | 0 | **1** | Cache + NF_1 |
| 010818663C | BF_NON_FORFEITURE=1 | 0 | **1** | Cache + NF_1 |
| 010469666C | NON_FORFEITURE=2 | 2 | **1** | NF_2→1 only |
| 010391895C | NON_FORFEITURE=4 | 0 | **0** | Out of scope |
| 010448806C | NON_FORFEITURE=5 | 0 | **0** | Out of scope |
| 010713704C | BF_NON_FORFEITURE=4 | 0 | **0** | Out of scope |
| 010391876C | NON_FORFEITURE=4 | 2 | **2** | Must not overwrite |

---

## Validation

```powershell
python tools/validators/validate_issue21a_mnfopt.py
```

Requires batch conversion rerun (`v57.47`) so `QLA_Migration/Output/quikmstr.csv` reflects the fix.

**Expected population impact:** ~1,253 policies (`0→1` enrich + 5 `2→1`); no change to policies already at `MNFOPT` 2/3 from rulebook.

---

## Regression risks

| Risk | Mitigation |
|---|---|
| Overwrite existing MNFOPT 2/3 | Enrich-on-zero guard unchanged |
| Invalid MNFOPT 9 | `NF_9→0` |
| Codes 3–6 remapped | Translation entries untouched |
| Row count / MPOLICY / MPREM | No logic in those paths |
