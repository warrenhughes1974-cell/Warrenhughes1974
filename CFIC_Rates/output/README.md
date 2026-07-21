# CFIC QLAdmin Load Package

**This folder is the Citizens rate handoff package — table CSVs only.**

Mirrors Warren CSO policy: `QLA_Migration/Output/rates/` holds PascalCase `Quik*.csv` files ready for QLAdmin append/DBF conversion. CFIC stays isolated under `CFIC_Rates/` until a future integration issue approves merge.

## Allowed here

| Path | Contents |
|------|----------|
| `Output/rates/QuikCvs.csv` | Cash value factors |
| `Output/rates/QuikTvs.csv` | Terminal reserve factors |
| `Output/rates/QuikNps.csv` | Paid-up / net premium factors |
| `Output/rates/QuikPlCv.csv` | Cash value rate keys |
| `Output/rates/QuikPlTv.csv` | Reserve / NP rate keys (shared) |
| `Output/rates/QuikPlGd.csv` … `QuikPlNb.csv` | Member / dimension tables |
| `Output/rates/QuikGps.csv` | Gross premium (when Wave GP is published) |
| `Output/rates/QuikPlGp.csv` | Gross premium keys |

## Do NOT leave here

| Type | Relocate to |
|------|-------------|
| Manifests / emit summaries | `CFIC_Rates/Reports/` |
| Validation parity CSVs | `CFIC_Rates/Validation/` |
| Batch logs | `CFIC_Rates/Logs/` |
| Staging / OCR / DBF extracts | `extracted_reserve/`, `extracted_pdf_rates/` |
| Old lowercase drafts | `Archive/` or delete via `--clean-legacy` |

## Publish

```powershell
python CFIC_Rates/scripts/package_cfic_rates.py --extract --validate --plans P7MN,P7FN,P7FS,P7MS --clean-legacy
```

See `CFIC_Rates/RUN_GUIDE.md` for the full process.
