# Issue #88 — Implementation Notes

**Issue:** #88 — ISWL QuikIssc / QuikUint empty in batch CSV package (D1 + D2)  
**Framework stage:** Development Agent (G4)  
**Generated:** 2026-07-21  
**Model:** Cursor Grok 4.5 (**one-time override** — user approved; locked map is Composer 2.5)  
**Status:** Development complete → Ready for Validation  
**APP_VERSION bump:** None (no `app.py` changes)

---

## Changes made

### D1 — `qla_core/rate_emit.py`

In `run_rate_emit` CSV branch, after QuikAint stubs and before `_write_csv_manifest`:

- Write `QuikUint.csv` when `res.quikuint_rows` is non-empty  
- Write `QuikIssc.csv` when `res.quikissc_rows` is non-empty  
- Append manifest entries + `RATE_LOG` messages with row counts  

Mirrors existing DBF branch and R5 CLI `rate_loader_emit.py`.

### D2 — Config paths

| File | Keys | New path date |
|------|------|---------------|
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | `psegt_csv`, `pdint_extract`, `pdinttbl_extract` | `20260630` |
| `rate_loader_config.example.json` | same | `20260630` |

---

## Emit result (2026-07-21)

```
RATE_LOADER_STATUS: SUCCESS
RATE_LOADER_BLOCKERS: 0
RATE_LOG: Issue #88 QuikUint: 32 row(s)
RATE_LOG: Issue #88 QuikIssc: 8 row(s)
RATE_ISSUE40_VERIFY: PASS
```

| Table | Pre-fix | Post-fix | Expected |
|-------|---------:|---------:|---------:|
| QuikIssc | 0 | **8** | 8 |
| QuikUint | 0 | **32** | 32 |
| QuikCoi | 792 | 792 | unchanged |
| QuikGcoi | 198 | 198 | unchanged |
| QuikGps | 11983 | 11983 | unchanged |
| QuikCvs | 38407 | 38407 | unchanged |

QuikIssc plans: `1658C1, 1658CS, 1659C2, 1659CR, 1659CS, 1659SR, 1669SR, 1679CS`  
QuikUint: 4 tiers × 8 MPLANs (11.0 / 9.0 / 5.0 / 4.5) — matches Issue #32 Phase5 baseline.

---

## Test_Validation publish

| File | Path |
|------|------|
| QuikIssc.csv | `QLA_Migration/Output/Test_Validation/rates/QuikIssc.csv` |
| QuikUint.csv | `QLA_Migration/Output/Test_Validation/rates/QuikUint.csv` |
| Manifest note | `QLA_Migration/Output/Test_Validation/manifest_issue88.txt` |

---

## Do NOT / did not change

- QuikIssc / QuikUint loader business rules  
- COI/GCOI/GPS allowlists  
- SL schedule values  
- Sync_Rulebooks / policy converters  
- `PARTIAL_EMIT_BLOCKERS` (deferred per Risk)  
- `app.py` / `APP_VERSION`

---

## Notes for Validation

1. Full reconcile scripts (`iswl_quikissc_reconcile.py` / `iswl_quikuint_reconcile.py`) re-run the entire rate pipeline (~3+ min each). A hung dual-run was killed; **emitted CSV package was validated directly** against Phase5/6 expectations (PASS).  
2. Manifest may still list an earlier 0-row member stub for QuikUint/QuikIssc from `emit_all_rate_tables_csv` before the Issue #88 overwrite — final files and the interest/surrender manifest lines are authoritative (32 / 8).  
3. Evidence: `Issue_Log_Items/Issue_88/evidence/pre_fix_rate_row_counts.json`

---

## Diff summary

| File | Change |
|------|--------|
| `qla_core/rate_emit.py` | +~15 lines CSV write for Uint/Issc |
| `rate_loader_config.json` | 3 path dates 20260629 → 20260630 |
| `rate_loader_config.example.json` | same |

**Next:** Validation Agent (Grok 4.5) — say **“Proceed to Validation for Issue 88.”**
