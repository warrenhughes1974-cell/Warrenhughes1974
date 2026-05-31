# Non-Convertible Benefit Row Governance Rule

**Status:** ACTIVE — P3G+ baseline for P3F/P3H validation layers  
**Authority:** LifePRO Product Book review + PPBEN analysis (P3G)  
**Last updated:** 2026-05-26

## Rule

Treat **BENEFIT_SEQ = 99** and associated non-product rows (especially **BENEFIT_TYPE = UV** with blank **PLAN_CODE**) as:

> **NON-CONVERTIBLE / NON-PRODUCT administrative structures**

unless explicitly overridden by business.

## Governance interpretation

| Requirement | Policy |
|-------------|--------|
| Authoritative product? | **No** — not authoritative product coverages |
| MPLAN resolution required? | **No** — do not force authoritative MPLAN |
| quikplan/quikridr product authority? | **No** — do not force into closed catalog emit |
| Orphan hard-fail? | **No** — do not hard-fail as orphan products |
| Classification | **`EXPECTED_NON_PRODUCT_ROW`** |
| Source data | Preserve **exact** raw values in business review reports |

## Evidence (current migration)

- Rows typically contain blank source PLAN values (often space-padded)
- Rows do not map to authoritative product catalog entries
- Rows persist after all legitimate P3G catalog/quikplan gaps were corrected
- Rows frequently use `BENEFIT_TYPE = UV`
- Rows behave as administrative/value-tracking structures, not convertible riders/products
- No authoritative quikplan PLAN dependency exists for these rows
- P3C/P3E/P3G stabilization eliminated all true product orphan conditions while these rows remained (~2,348 blank MPLAN rows, all classified)

## LifePRO Product Book alignment

- No evidence that **BENEFIT_SEQ 99** represents a convertible product/rider structure
- Platform contains many non-product internal value/administrative segments
- Current behavior is consistent with policy-level/system-level accounting or value structures

## Implementation (code)

Central module: `qla_core/non_product_row_governance.py`

```python
from qla_core.non_product_row_governance import (
    classify_blank_mplan_governance,
    is_non_convertible_benefit_row,
    EXPECTED_NON_PRODUCT_ROW,
)
```

Consumers:
- `qla_core/mplan_authority.py` — P3E quikridr MPLAN trace
- `qla_core/p3g_completeness.py` — blank MPLAN business review report
- Future P3F (quikactg), P3H (batch parity) — must import shared rule, not reimplement

## Prohibited actions

- Do **NOT** auto-map BENEFIT_SEQ 99 rows into authoritative MPLAN values
- Do **NOT** create synthetic catalog rows for these records
- Do **NOT** hard-fail these rows as orphan products
- Do **NOT** trim/normalize/overlay raw source values in business review outputs

## Business override criteria

Reclassify only when **all** apply:

1. Source PLAN exists with business-confirmed product semantics
2. Business explicitly identifies convertible behavior
3. Downstream operational dependency proves product identity (not admin/value-only)

Until override is documented, classification remains **`EXPECTED_NON_PRODUCT_ROW`**.

## Validation expectations (P3F/P3H)

- `governance_status` = `BLANK_ALLOWED` or `CLASSIFIED_OK` for EXPECTED_NON_PRODUCT_ROW
- `governance_errors` count excludes BENEFIT_SEQ 99 / UV blank-PLAN rows
- Business report: `blank_mplan_business_review_report.csv` retains exact PPBEN fields
