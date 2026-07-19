# DG-R-001 — Validation

**Date:** 2026-07-18  
**Data region:** `Q:\CSO\CSO_Test_6_30_2025`  
**Overall:** Target rules **Passed**

---

## Commands run

From repo root:

```bash
python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2025" --output "data_governance/docs/remediation/items/DG-R-001_company_codes_G_V/validation_out/DG-QUIKLIST-002" --rule DG-QUIKLIST-002

python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2025" --output "data_governance/docs/remediation/items/DG-R-001_company_codes_G_V/validation_out/DG-QUIKPLAN-032" --rule DG-QUIKPLAN-032
```

---

## Results

| Rule | Overall | Records checked | Passed | Problems | Source modified |
|------|---------|----------------:|-------:|---------:|-----------------|
| DG-QUIKLIST-002 | **Passed** | 0 | 0 | 0 | False |
| DG-QUIKPLAN-032 | **Passed** | 5023 | 5023 | 0 | False |

### DG-QUIKLIST-002 note

QuikList is empty after deleting the three test groups. The rule evaluates List rows against QuikComp; with **0 rows**, result is Passed / “No records were evaluated.” That is the expected outcome for this decision (delete groups rather than remap their MCOMP).

### DG-QUIKPLAN-032 note

Company-code checks on QuikAgts / QuikActg / QuikList / QuikChrt: **100% pass**, **0** problems. No remaining G/V findings on in-scope tables.

---

## Run folders

- `validation_out/DG-QUIKLIST-002/DG-20260718_135637_781516/`
- `validation_out/DG-QUIKPLAN-032/DG-20260718_135639_331016/`

---

## Inventory re-check (post-apply)

| Table | Residual MCOMP in {G,V} |
|-------|------------------------:|
| QuikList | 0 |
| QuikChrt | 0 |
| QuikAgts | 0 |
| QuikActg | 0 |
| QuikComp codes | `C` only (exactly once); G/V not inserted |

---

## Residuals (not blocking this item)

| Item | Detail |
|------|--------|
| `quikgrpimp.dbf` | Still has 3 rows with `MGROUP=TERMG` (import staging). Out of DG-R-001 approved write scope. |
| Policy last-char G/V | None found on QuikMstr (0/0). |
| NTX indexes | May be stale until QLAdmin reindex. |
