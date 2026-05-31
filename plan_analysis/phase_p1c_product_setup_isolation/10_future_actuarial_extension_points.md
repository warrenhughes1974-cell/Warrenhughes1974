# Future Actuarial Extension Points (Phase P1C)

## Scope Boundary

**Do NOT implement** gross premiums, cash values, terminal reserves, dividends, or HRIGPKEY population in P1C/P2.

This document identifies **extension points** in the isolated product setup architecture so future actuarial phases attach cleanly without redesign.

---

## QLAdmin Product Configuration Model (Confirmed)

`quikplan` = master product configuration catalog containing ALL product types (base, riders, supplemental, ADB, fees, disability).

Future actuarial loads attach **to PLAN configurations** already in quikplan — they do not redefine product semantics.

---

## Extension Point 1: HRIGPKEY

| Attribute | Detail |
|---|---|
| Field | `quikplan.HRIGPKEY` |
| QLAdmin role | Logical indicator for gross premium rate lookup in QuikPlbd |
| Current state | Blank on all 133 rows (correct) |
| Future phase | P5 — HRIGPKEY governance + population |
| Extension hook | `plan_governance/config/hrigpkey_rules.json` |
| Governance | Hold category: `MISSING_HRIGPKEY` blocks actuarial load only, not catalog emit |
| Runner integration | Add optional stage after emit: `--validate-hrigpkey` (diagnostic only until P5) |

---

## Extension Point 2: Vary-By Dimensions

| Field Group | QLAdmin Purpose | Current State |
|---|---|---|
| `UWVARYGP/DB/CV/TV/DV` | Underwriting class vary-by | Blank |
| `BDVARYGP/DB/CV/TV/DV` | Band vary-by (QuikPlbd: PLAN + BDCODE) | GP/DB defaulted to 0 |
| `STVARYGP/DB/CV/TV/DV` | State/country vary-by | Blank |
| `GDVARYGP/DB/CV/TV/DV` | Gender vary-by | GP/DB defaulted to 0 |

**Future phase:** P5 — vary-by governance before rate table attachment.

**Extension hook:** `plan_governance/config/varyby_governance_rules.json`

**Diagnostic (future):** Invalid vary-by combination → hold actuarial load, not catalog emit.

---

## Extension Point 3: QuikPlbd Rate Attachment

```
QuikPlbd index key: PLAN + BDCODE
Rate lookup: HRIGPKEY + vary-by dimensions
```

**Architecture:**

```
quikplan.csv (catalog)
    → actuarial load phase (future)
    → QuikPlbd.dbf / gross premium tables
    → validation manifest
```

Product setup runner produces stable PLAN codes; actuarial phase consumes emitted catalog as frozen input.

**Folder (future):**

```
plan_governance/phase_p5_actuarial_attachment/
    gross_premium_load_runner.py
    quikplbd_dbf_generator.py
    actuarial_attachment_manifest.csv
```

---

## Extension Point 4: Cash Values / Terminal Reserves / Dividends

| Load Type | Attach To | Future Table |
|---|---|---|
| Gross premiums | PLAN + HRIGPKEY + vary-by | QuikPlbd |
| Cash values | PLAN + issue age/duration grids | QuikCvbd (future) |
| Terminal reserves | PLAN + valuation basis | Actuarial tables |
| Dividends | PLAN + dividend option | QuikDvpr linkage |

**Extension point in product runner manifest:**

```csv
catalog_version,plan_count,hrigpkey_populated,varyby_ready,actuarial_load_status
```

Future actuarial runner checks manifest before load.

---

## Extension Point 5: PLANTYPE

| Attribute | Detail |
|---|---|
| Current | Blank on all rows |
| Future | Business classification for actuarial grouping |
| Extension | Additive field population phase — does not change PLAN identity |
| Governance | Diagnostic WARN if blank when actuarial load attempted |

---

## Extension Point 6: PCOMP Issue Amounts

| Attribute | Detail |
|---|---|
| Current | MINUNIT/MAXUNIT via PCOMP lookup in rulebook |
| Future | May extend to additional actuarial band limits |
| Extension | Rulebook lookup pattern already supports PCOMP join — add fields via rulebook lines only |

---

## Extension Point 7: DBF Generation Pipeline

Current P4 plan: `quikplan.dbf` from emitted CSV (configuration load).

Future: separate DBF generators for actuarial tables, each with:

- CSV source of truth
- Alignment manifest (CSV rows = DBF rows)
- `production_dbf_flag=N` until authorized
- Rollback via CSV snapshot

Mirror Phase 21B claims pattern exactly.

---

## Extension Point 8: Crosswalk Versioning + Effective Dates

Future business requirement: product versioning by effective date.

**Extension hook in crosswalk adapter:**

```python
def build_crosswalk_map(xwalk_path, effective_date=None):
    """Future: filter crosswalk rows by effective date."""
```

Not implemented in P2 — architecture reserves parameter without changing current join behavior.

---

## Dependency Chain (Future)

```
P2: Product catalog isolation (quikplan.csv)
    ↓
P3: Crosswalk authority migration
    ↓
P4: quikplan.dbf UAT generation
    ↓
P5: HRIGPKEY + vary-by governance
    ↓
P6: Gross premium load (QuikPlbd)
    ↓
P7: Cash value / reserve loads
    ↓
P8: Dividend table attachment
```

Each phase consumes **frozen output** of prior phase. No retroactive catalog mutation without rollback.

---

## What Must NOT Change for Actuarial Phases

- quikplan includes all product types (no rider extraction)
- Sync_Rulebook_quikplan mappings/defaults
- PLAN as primary key
- Policy batch reads catalog — does not rebuild it
- Claims governance independence

---

## Diagnostic Fields to Add Later (Stub in Manifest)

| Field | Phase |
|---|---|
| hrigpkey_populated_count | P5 |
| varyby_complete_count | P5 |
| actuarial_load_ready | P5 |
| quikplbd_row_count | P6 |
| gross_premium_load_timestamp | P6 |

Product setup runner manifest schema should include nullable columns for these future fields now (empty in P2).
