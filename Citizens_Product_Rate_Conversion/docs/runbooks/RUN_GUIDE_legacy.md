# CFIC Rates — Run Guide

Standalone Citizens rate pipeline. **Does not modify Warren `app.py` or `QLA_Migration/Output/`.**

## Folder map (CSO-aligned)

| Folder | Purpose |
|--------|---------|
| `Output/rates/` | **QLAdmin load package** — PascalCase `Quik*.csv` only |
| `Reports/` | `rate_csv_manifest.csv`, `emit_summary.json` |
| `Validation/` | Parity checks vs Access / business checkpoints |
| `Logs/` | Batch run logs (future) |
| `extracted_reserve/staging/` | Reserve DBF extract staging |
| `extracted_pdf_rates/staging/` | PDF gross-premium staging |
| `Issue_Log/CFIC_Issue_*` | Framework artifacts per issue |

## Standard publish (Reserve wave — PermaLife 7)

One command — extract, validate, publish, audit:

```powershell
python CFIC_Rates/scripts/package_cfic_rates.py `
  --wave reserve `
  --plans P7MN,P7FN,P7FS,P7MS `
  --extract `
  --validate `
  --clean-legacy
```

### What it does

1. **Extract** — `cifi0007.DBF` → `extracted_reserve/staging/{PLAN}/reserve_grid.csv`
2. **Validate** — P7MN milestones vs `extracted/PermaLife7AdultBefore.csv` → `Validation/`
3. **Build** — factor grids + rate keys + member tables (same `qla_core` path as CSO)
4. **Publish** — `Output/rates/QuikCvs.csv`, `QuikPlCv.csv`, etc. (PascalCase)
5. **Report** — `Reports/rate_csv_manifest.csv` + `Reports/emit_summary.json`
6. **Audit** — fails if `Output/rates/` contains anything other than allowed `Quik*.csv`

## Scale to all reserve plans

```powershell
python CFIC_Rates/scripts/package_cfic_rates.py --wave reserve --plans ALL --extract --clean-legacy
```

## Manual steps (debug)

```powershell
# 1. Extract only
python CFIC_Rates/Issue_Log/CFIC_Issue_03/scripts/extract_cfic_reserve_dbf.py --plans P7MN

# 2. Validate only
python CFIC_Rates/Issue_Log/CFIC_Issue_03/scripts/validate_cfic_reserve_rates.py --plan P7MN

# 3. Publish only (staging must exist)
python CFIC_Rates/scripts/package_cfic_rates.py --wave reserve --plans P7MN
```

## Before QLAdmin handoff

1. Fill OBQ-2 assumptions in `Issue_Log/CFIC_Issue_03/business_inputs/cfic_rate_key_assumptions.csv`
2. Re-run publish after assumptions are populated
3. Confirm `Reports/emit_summary.json` shows `output_audit_clean: true`
4. Confirm `Validation/` parity PASS for pilot plans

## Full fleet (reserve DBF — no gross premium)

```powershell
python CFIC_Rates/scripts/package_cfic_rates.py --wave reserve --plans ALL --extract --extract-plans
```

## DBF coverage

| DBF | Role | In load package? |
|-----|------|------------------|
| `cifi0007.DBF` | Cash value, terminal reserve, paid-up | **Yes** → `Output/rates/` |
| `cifi0004.dbf` | Plan master, loan IR history | Staging only (`extracted_plans/`) — plan setup wave |
| `cifianu1.dbf` | Annuity payment transactions | **No** — not a life rate table |

## Waves (roadmap)

| Wave | Source | Tables | Status |
|------|--------|--------|--------|
| **Reserve** | `docs/cifi0007.DBF` | QuikCvs, QuikTvs, QuikNps + keys + members | **Full fleet published** |
| **Gross premium** | Access / PDF | QuikGps, QuikPlGp | **Deferred** (not in scope) |
| **Plan setup** | `cifi0004.dbf` | QuikPlan, loan IR on QuikPlSt | Staging ready |

## Related

- `CFIC_Rates/Output/README.md` — load package policy
- `CFIC_Rates/Issue_Log/README.md` — issue framework
- Warren CSO analogue: `plan_analysis/phase_r5_rate_loader/rate_loader_emit.py` → `QLA_Migration/Output/rates/`
