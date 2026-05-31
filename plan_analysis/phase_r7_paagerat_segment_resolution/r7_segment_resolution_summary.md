# R7 — PAAGERAT Segment Resolution (Business Action)

## Business directive

1. **Join chain:** PAAGERAT → PCOVRSGT → PCOVR using segment relationships  
2. **Filter:** PAAGERAT `TYPE_CODE = 'PR'` for policy gross premium rates  
3. **Extracts:** Future data drops must include **PAAGERAT**, **PCOVRSGT**, and **PCOVR**

## Implementation status

| Component | Location | Status |
|---|---|---|
| Segment join logic | `qla_core/rate_segment_resolution.py` | **Implemented** |
| PAAGERAT PR transform (PR-only) | `qla_core/paagerat_pr_loader.py` | **Implemented** |
| Source data | `plan_analysis/source_data/coverage/` | PCOVR + PCOVRSGT present |
| Reconciliation script | `_reconcile_paagerat.py` | **Implemented** |
| Guarded QuikGps re-emit merge | `rate_pipeline.py` | **Not yet** — pending attained-age grid rule |

## Join chain (confirmed)

```
PAAGERAT.COVERAGE_ID  (= segment ID)
        ↓  PCOVRSGT.SEGT_ID where SEGT_FLAG = 'Y'
PCOVRSGT.COVERAGE_ID  (= parent coverage)
        ↓  PCOVR.COVERAGE_ID (enrichment / validation)
Policy Form Crosswalk   (= parent COVERAGE_ID → PLAN)
        ↓
Authoritative QLAdmin PLAN
```

**Do not** map PAAGERAT `COVERAGE_ID` directly to policy form names (e.g. `670 GL85-M`).

## Required future extracts

Place refreshed files in `plan_analysis/source_data/`:

| Table | Path | Required columns |
|---|---|---|
| PAAGERAT | `rates/PAAGERAT_*.csv` | COVERAGE_ID, TYPE_CODE, SEX, BAND, UWCLS, SEQ, VALUE_INFO |
| PCOVRSGT | `coverage/PCOVRSGT.csv` | COVERAGE_ID, SEGT_ID, SEGT_FLAG |
| PCOVR | `coverage/PCOVR.csv` | COVERAGE_ID, DESCRIPTION, POLICY_FORM_NUM, STATUS_CODE |
| Policy Form Crosswalk | `crosswalk/Policy Form Crosswalk *.xlsx` | LifePRO COVERAGE_ID → QL Plan Code |

Update paths in `rate_loader_config.example.json` when filenames change.

## R7 reconciliation results (current extracts)

| Metric | Value |
|---|---|
| PAAGERAT PR rows resolved (`IN_SCOPE`) | 14,772 |
| Non-PR rows excluded | 9,466 |
| Unresolved PR segments | **0** |
| Distinct PLANs from segment chain | 75 |
| Plans in current emitted `QuikGps` | 11 |
| Overlap | 0 (PAAGERAT PR is net-new vs R5 Rate_Table GP emit) |

Run `_reconcile_paagerat.py` after any extract refresh.

```bash
python plan_analysis/phase_r7_paagerat_segment_resolution/_reconcile_paagerat.py
```

## Open item before re-emit

PAAGERAT is **attained-age** shaped (`SEQ` = age). QuikGps is **issue-age × duration** grid. Business must confirm how attained-age PR maps to QLAdmin `AGE` / `CNTL` columns before merging into guarded emit.

## Example traces

| PAAGERAT segment | Parent coverage | PLAN |
|---|---|---|
| `960 PO` | `960 PO` | `1960PO` |
| `0823 960LP` | `0823 960LP` | `9065WP` |
| `960 LP65` | `960 LP65` | `196065` |

Plans like `17085M` / `196085` (`670 GL85-M` / `960 LP85-M`) have **crosswalk entries** but **no PAAGERAT PR rows** — business must confirm where base-plan GP rates live.
