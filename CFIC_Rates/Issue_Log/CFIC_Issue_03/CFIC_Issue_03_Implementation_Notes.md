# CFIC Issue #03 — Reserve DBF → QLAdmin (CV / TV / NP + Keys)

**Track:** Standalone CFIC pipeline (not Warren `app.py`)  
**Source:** `CFIC_Rates/docs/cifi0007.DBF` (369K-row Reserve file)  
**Pilot:** PermaLife 7 `P7MN` (+ P7FN/P7FS/P7MS for full PL7 quad)

## Pipeline

```
cifi0007.DBF  →  extract_cfic_reserve_dbf.py  →  extracted_reserve/staging/
                                              →  validate_cfic_reserve_rates.py  (vs Access CSV)
                                              →  emit_cfic_reserve_rates.py  →  output/rates/
                                                    QuikCvs + QuikPlCv
                                                    QuikTvs + QuikNps + QuikPlTv (shared)
                                                    QuikPlGd/Uw/Bd/St/Nb (member tables)
```

Uses the same `qla_core` factor grid + key generation pattern as CSO (`build_factor_grid`, `build_key_rows`, `build_member_rows`).

## Publish (standard)

```powershell
python CFIC_Rates/scripts/package_cfic_rates.py --wave reserve --plans P7MN,P7FN,P7FS,P7MS --extract --validate --clean-legacy
```

See `CFIC_Rates/RUN_GUIDE.md` for the full CSO-aligned process.

## Manual steps (debug)

```powershell
python CFIC_Rates/Issue_Log/CFIC_Issue_03/scripts/extract_cfic_reserve_dbf.py --plans P7MN,P7FN,P7FS,P7MS
python CFIC_Rates/Issue_Log/CFIC_Issue_03/scripts/validate_cfic_reserve_rates.py --plan P7MN
python CFIC_Rates/scripts/package_cfic_rates.py --wave reserve --plans P7MN,P7FN,P7FS,P7MS --clean-legacy
```

## Output locations

| Stage | Path |
|-------|------|
| Staging | `CFIC_Rates/extracted_reserve/staging/{CFIC_PLAN}/reserve_grid.csv` |
| **Load package** | `CFIC_Rates/Output/rates/QuikCvs.csv`, `QuikPlCv.csv`, … |
| Manifest | `CFIC_Rates/Reports/rate_csv_manifest.csv` |
| Validation | `CFIC_Rates/Validation/cfic_issue03_*_validation.csv` |
| Assumptions | `CFIC_Rates/Issue_Log/CFIC_Issue_03/business_inputs/cfic_rate_key_assumptions.csv` |

## Field mapping (reserve → QLAdmin)

| Reserve field | QLAdmin table | Notes |
|---------------|---------------|-------|
| `CASH_VALUE` | `QuikCvs` | Per $1,000 face (`DEATH_BEN`=1000) |
| `TERM_RSV` | `QuikTvs` | Terminal reserve |
| `PUP_INS` | `QuikNps` | Paid-up insurance (shared `QuikPlTv` key) |
| `RL_NETPREM` | *(staging only)* | Matches Access over-100K rate; not emitted as QuikGps yet |

## Segmentation

- Sex/smoker encoded in CFIC plan code (`P7MN` → M/NS, `P7MS` → M/SM, etc.)
- Face-amount band not in reserve file → `BAND` = `00`
- `ISSCNTRY` = `0000`, `ISSUEST` = `00`, `EFFDATE` = `19000101`

## OBQ-2 — Rate-key assumptions

`QuikPlCv` / `QuikPlTv` assumption fields must be supplied in `business_inputs/cfic_rate_key_assumptions.csv` before QLAdmin load. Keys are emitted with blank placeholders until actuarial fills the CSV (same pattern as CSO crosswalk).

## Related

- CFIC Issue #02: PDF gross premium (OCR — deprioritized for CV/PU)
- Issue #18: FoxPro table request (Reserve + Plans now in `docs/`)
