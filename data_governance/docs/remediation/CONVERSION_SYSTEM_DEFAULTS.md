# Conversion system defaults (governance remediation)

**Purpose:** While walking the DG-R remediation list, capture **system defaults** so future conversions do not reintroduce the same governance failures. Prefer rulebook / emit defaults over one-off DBF patches alone.

## Principle

1. **System defaults** — When LifePRO/source does **not** supply a value, conversion must emit the approved QLAdmin default.
2. **Do not blind-force over real source** — If source explicitly provides a value (e.g. True/`T`/`Y`/`1` for a logical), preserve it unless a separate business rule says otherwise.
3. **Data cleanup vs conversion** — Patching a live DBF fixes today’s region; rulebook/emit defaults prevent the next batch from bringing the defect back.

## Defaults locked during remediation

| Item | Table / field | Default | Rule / notes |
|------|---------------|---------|--------------|
| DG-R-003 | QuikDate PACBILL, DIRBILL, REINBILL | Prior month-end of run date | Emit via `qla_core/quikdate_converter.py`; ACHFILEID=0, ACHFILEID2=A, ESC_DATE blank |
| DG-R-004 | QuikPlan MNAICLOB | `NAPLAN` | Already in `Sync_Rulebook_quikplan.csv`; governance rule 024 expects NAPLAN |
| DG-R-005 | QuikPlan HCOMMIP, HRIGPKEY | `F` | `Sync_Rulebook_quikplan.csv` Default_Value=`F` (2026-07-18). MEDS plans need both True when PLANTYPE=MEDS — if source later maps these fields, True wins when present; empty → F |
| DG-R-006 | QuikPlan PLANVALOPT | Rate/PVO driven (often `Y`) | **No closed-book force-off.** DG-QUIKPLAN-022 retired; PVO independent of BACTIVE |
| DG-R-007 | QuikPlan LOAGE | Source `MIN_ISSUE_AGE` (default `0` if empty) | **Do not force LOAGE=0** over real min issue age. Rule 008 only requires LOAGE &lt; HIAGE |
| DG-R-008 | QuikPlan / QuikPl* PLAN | Never emit blank PLAN | Current `quikplan.csv` emit already skips blanks; do not load blank-PLAN shells into DBF |
| DG-R-009 | QuikPlan single-premium pay | PAYYRS=1; PAYAGE/SEMI/QTRL/MTHD/MTHB=0 | Confirmed plans in `QLA_Migration/Configs/single_premium_plans.csv`; applied after ROUTE_PAY_* (v58.10) |

## Rulebook mechanics (QuikPlan)

In `qla_core/quikplan_converter.py` field mapping:

- Empty `Source_Field` + `Default_Value` → emit the default.
- Non-empty source that resolves to a value → use source.
- Empty after source resolve → fall back to `Default_Value`.

So `HCOMMIP`/`HRIGPKEY` = `F` means: default False unless a future source mapping supplies True.

## Related files

- `QLA_Migration/Configs/Sync_Rulebook_quikplan.csv`
- `QLA_Migration/Data_Goverence.txt`
- Per-item folders under `data_governance/docs/remediation/items/`
