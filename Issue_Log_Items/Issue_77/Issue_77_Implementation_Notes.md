# Issue #77 — Implementation Notes

**Issue:** #77 — Fleet rate setup (default keys + Plan Values Options)  
**Release:** **v57.95** (follow-up to v57.94)  
**Model:** Cursor Grok 4.5 (user override of Composer 2.5 for this Dev)  
**Date:** 2026-07-17  

---

## What changed

1. **Default rate keys** — For every plan with loaded factor rates, each of GP/DB/CV/TV/DV gets at least one QuikPl* key. Missing families get one stub. Stub uses **real** Gender/UW/Band already on the plan when present; NOT APPLICABLE (`0`/`00`) only when no real codes exist (EX pattern).  
2. **Members** — Do **not** keep Gender `0` / UW `00` / Band `00` beside real codes; QuikPlSt.MLOANINT defaults to `0.00`.  
3. **Plan Values Options** — Recompute from keys: Band Y if family present; STVARYGP Y if GP present; Gender/UW Y only if multi-value; PLANVALOPT Y/N only.  
4. **Output applied** — `_apply_issue77_rate_setup.py` updated current `Output/rates` + `quikplan.csv` and published to `Output/Test_Validation/`.

---

## Files changed

| File | Change |
|------|--------|
| `qla_core/rate_key_setup.py` | `ensure_default_key_stubs`, `make_default_key_row`, `rated_plans_from_grids` |
| `qla_core/rate_member_setup.py` | MLOANINT=`0.00`; `ensure_members_for_keys` |
| `qla_core/rate_pipeline.py` | Call stubs + member sync after key build |
| `qla_core/quikplan_rate_variation_flags.py` | Issue #77 PVO rule; CSV key scan; stub stats; STVARY check |
| `app.py` / `QLA_Migration/app.py` | **v57.94** |
| `QLA_Migration/_apply_issue77_rate_setup.py` | Apply to current Output |
| `QLA_Migration/_validate_issue77_rate_setup.py` | Validator |

---

## Apply results (2026-07-17)

| Metric | Value |
|--------|------:|
| Default key stubs added | **352** |
| Member rows added | 190 |
| quikplan plans with PVO field diffs | 133 |
| PLANVALOPT=Y after | 133 |
| Validator | **PASS** (126 rated plans) |

---

## Before / after (1658CS)

| Item | Before | After |
|------|--------|-------|
| QuikPlDb / QuikPlDv | 0 keys | 1 default key each |
| STVARYGP | N | Y |
| BDVARYDB | N | Y |
| Factor QuikGps/Cvs/Tvs counts | unchanged | unchanged |

---

## Rollback

1. Revert the `qla_core` + `app.py` version commits.  
2. Restore prior `Output/rates/QuikPl*.csv`, `QuikPlSt.csv`, members, and `quikplan.csv` from backup/git.  

---

## Next

Validation Agent (Grok 4.5) then Regression — user prompt when ready.
