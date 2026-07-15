# Issue #72 — Implementation Notes

**Issue:** NFO must match ETI/RPU status (44→2, 45→3)  
**Version:** v57.91  
**Date:** 2026-07-15  
**Model:** Composer 2.5 (Development)

---

## Change summary

Post-map hook on completed `quikmstr` rows: when final `MSTATUS` is **44** or **45**, force `MNFOPT` to **2** or **3** respectively. Runs after #13/#59/`ST_`/#49 status finalization and before Issue #45 bank-draft gate.

Issue **#57** election mapping (`NF_*` + PPBENTYP enrich) unchanged for all other statuses.

---

## Files changed

| File | Change |
|------|--------|
| `app.py` | `APP_VERSION` v57.91; `_apply_issue72_mnfopt_status_force`; call + log |
| `QLA_Migration/app.py` | Mirror |
| `tools/validators/validate_issue72_mnfopt_status.py` | New |

**Not changed:** rulebooks, `Master_Value_Translation.csv`, `quikridr`, rates.

---

## Before / after trace

| Policy | MSTATUS | MNFOPT before | MNFOPT after |
|--------|---------|---------------|--------------|
| 010407670C | 45 | 2 | **3** |
| 010165095C | 45 | 2 | **3** |
| 010374099C | 44 | 1 | **2** |
| 010367131C | 22 | 2 | 2 (unchanged) |

**Expected fleet deltas:** 277 policies.

---

## Validation

```bash
python tools/validators/validate_issue72_mnfopt_status.py
```

**Result (2026-07-15):** PASS — 0 violations @44/45; `010407670C` MNFOPT=3; 277 forced on rebatch.  
**NFO>0 life-with-CV:** PASS — 4,512 policies checked; 0 failures (phase-1 plan has QuikPlCv key or VARDB≠0).

Publish on PASS: `Output/Test_Validation/quikmstr.csv` only. **Published.**

---

## UAT

Reload `Test_Validation/quikmstr.csv` → Data Admin on sample `010407670C` → rebuild CV if checking cash values.
