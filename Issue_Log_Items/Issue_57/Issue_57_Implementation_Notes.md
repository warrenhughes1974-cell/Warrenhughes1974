# Issue #57 — Implementation Notes

**Issue:** #57 — NFO Option incorrect  
**Framework stage:** Development (G4)  
**Approved:** Option B (Risk report 2026-07-13)  
**Generated:** 2026-07-13  
**Engine:** No `app.py` change — rulebook + translation only  

---

## Changes

| File | Change |
|------|--------|
| `Master_Value_Translation.csv` | Add `NF_3`/`NFO_3`→1; `NF_4`/`NFO_4`→2; `NF_5`/`NFO_5`→3 |
| `QLA_Migration/Mapping/Master_Value_Translation.csv` | Mirror |
| `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv` | **Removed** `PAID_UP_TYPE→MNFOPT` |
| `tools/validators/validate_issue57_mnfopt.py` | New validator |

**Not changed:** `app.py`, PPBENTYP cache (#21A), MSTATUS `PUT_` interceptor, `NF_1`/`NF_2`/`NF_9`.

---

## Before / After (Eric traces)

| Policy | LP code | Before | After (expected) |
|--------|:---:|:---:|:---:|
| 010367131C | 4 ETI | 0 | **2** |
| 010148272C | 4 ETI | 0 | **2** |
| 010143726C | 4 ETI | 0 | **2** |
| 010392763C | 5 RPU (PUT=PU) | 0 | **3** |
| 011221309C | 3 APL | 3 (showed RPU) | **1** |

---

## Validation

```bash
python Issue_Log_Items/Issue_57/scripts/rebatch_quikmstr.py
python tools/validators/validate_issue57_mnfopt.py
```

**Result (2026-07-13):** Validator **PASS** — all Eric traces + #21A control 010391876C.

---

## Rollback

1. Restore `PAID_UP_TYPE,MNFOPT,0` rulebook row  
2. Revert translation `NF_3`/`NFO_3`; set `NF_4`/`NFO_4`→0, `NF_5`/`NFO_5`→0  
3. Re-run batch  
