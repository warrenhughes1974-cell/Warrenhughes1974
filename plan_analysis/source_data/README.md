# Plan & Rate Source Data (Authoritative)

Consolidated LifePRO extracts and QLAdmin reference artifacts for **plan analysis** and **rate conversion**.

## Layout

| Path | Contents |
|---|---|
| `rates/` | LifePRO rate extracts (`Rate_Table_Extract`, `PAAGERAT`) |
| `coverage/` | LifePRO coverage/segment tables (`PCOVR`, `PCOVRSGT`) |
| `crosswalk/` | Policy Form Crosswalk (business-owned) |
| `reference_dbf/` | QLAdmin V5 template DBFs (physical schema source of truth) |

## Product sources (plan_analysis root)

| Path | Contents |
|---|---|
| `../quikplan_source.csv` | Primary quikplan product catalog source |
| `../PCOMP.csv` | Component lookup for rulebook |

## Emitted outputs

| Path | Contents |
|---|---|
| `../phase_r5_rate_loader/emitted_dbf/` | Generated rate library (16 DBFs) |
| `../../QLA_Migration/Output/rates/` | **Append-ready rate CSVs** (16 tables + manifest) |

## Notes

- **PCOVRSGT** maps `SEGT_ID` → parent coverage; required for correct PAAGERAT `COVERAGE_ID` resolution.
- **PAAGERAT.COVERAGE_ID** is a segment ID, not a policy form name.
- **Required extract set:** PAAGERAT + PCOVRSGT + PCOVR + Policy Form Crosswalk (all four on every refresh).
- Segment join implementation: `qla_core/rate_segment_resolution.py` · R7 reconciliation: `phase_r7_paagerat_segment_resolution/`.
- Operational conversion outputs remain in `QLA_Migration/Output/` (claims/product batch).
- Phase deliverables remain under `plan_analysis/phase_*/`.

## Legacy path

Files previously under `docs/plan_conversion_reference/` were relocated here (2026-05-29).
