# CFIC Rates — Issue Log

Citizens / CFIC rate-load issues are numbered **independently** from the Warren LifePRO → QLAdmin issue log (`Issue_Log_Items/`).

## Framework

Use the same gated process as `AI_Agents/Framework.md`:

Intake → Planning → Dependency Gate → Risk → Development → Validation → Regression → Closure

| Rule | CFIC application |
|------|------------------|
| No production code | Intake through Risk: no `QLA_Migration/app.py`, no Warren rulebooks |
| Artifact root | `CFIC_Rates/Issue_Log/CFIC_Issue_<NN>/` |
| **Load package** | `CFIC_Rates/Output/rates/` — **PascalCase `Quik*.csv` only** |
| Reports / validation | `CFIC_Rates/Reports/`, `CFIC_Rates/Validation/` |
| Warren isolation | Do not merge into `QLA_Migration/Output/` until a future integration issue approves |

**Publish command:** `python CFIC_Rates/scripts/package_cfic_rates.py` — see `CFIC_Rates/RUN_GUIDE.md`

## Issues

| ID | Title | Status |
|----|-------|--------|
| **01** | Green-Sheet NF / Reserve Rate Extraction | **Wave 1 dev complete — OCR validation FAIL** | See `CFIC_Issue_01_Implementation_Notes.md` |
| **02** | Docs PDF gross premium extract → QuikGps | **Pilot built — P7MN adult 53 rows** | See `CFIC_Issue_02_Implementation_Notes.md` |
| **03** | Reserve DBF → QuikCvs/Tvs/Nps + keys | **Pilot ready — PL7 quad** | See `CFIC_Issue_03_Implementation_Notes.md` |

## Related

- `CFIC_Rates/README.md`
- `CFIC_Rates/RUN_GUIDE.md`
- `CFIC_Rates/Output/README.md`
- `CFIC_Rates/docs/cash_value_extraction_plan.md`
- `AI_Agents/Framework.md`
