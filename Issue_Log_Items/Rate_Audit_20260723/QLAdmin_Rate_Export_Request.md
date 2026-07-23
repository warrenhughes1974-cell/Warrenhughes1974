# QLAdmin Rate Export Request

To complete the loaded-data portion of the exhaustive rate audit, export the post-load QLAdmin rate tables after importing the current package.

The export can be CSV or DBF. Use the exact table names below if possible. Put the files in one folder and run:

```powershell
python Issue_Log_Items\Rate_Audit_20260723\scripts\run_rate_audit.py --qla-export C:\path\to\QLAdmin\rate_export
```

---

## Required Rate Tables

Factor tables:

- `QuikCvs`
- `QuikDbs`
- `QuikDvs`
- `QuikGps`
- `QuikNff`
- `QuikNps`
- `QuikTvs`
- `QuikCoi`
- `QuikGcoi`

Key tables:

- `QuikPlCv`
- `QuikPlDb`
- `QuikPlDv`
- `QuikPlGp`
- `QuikPlTv`

Member / dimension tables:

- `QuikPlBd`
- `QuikPlGd`
- `QuikPlNb`
- `QuikPlSt`
- `QuikPlUw`
- `QuikUwpo`

Special rate tables:

- `QuikAint`
- `QuikIssc`
- `QuikUint`

Companion setup table:

- `quikplan`

---

## Separate Scope Decision Needed

`QuikAing` is not emitted by the current `QLA_Migration/Output/rates` pipeline. If QLAdmin needs guaranteed annuity interest rows from `QuikAing`, export it too and open/fold in a separate issue to wire it into the enterprise rate package.

---

## Export Requirements

- Export after loading the same `QLA_Migration/Output/rates/` package being audited.
- Do not manually edit exported files before comparison.
- Preserve DBF field names and field order when exporting to CSV.
- Include all rows, not only changed rows or current-plan filters.

