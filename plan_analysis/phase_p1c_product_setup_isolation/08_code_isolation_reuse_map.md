# Code Isolation & Reuse Map (Phase P1C)

## Summary

Product setup conversion logic currently lives **inline inside `app.py` `process_data()`** — shared with all QLA tables via a generic rulebook loop. Isolation requires **extracting the quikplan path** into a shared module without altering behavior.

---

## app.py — Exact Reuse Targets

### 1. Schema Definition

```162:162:app.py
"quikplan": ["PLAN", "FORM", "DESCR", "PAR", "SEX", ... "MGTDANNV"],
```

**Extract to:** `qla_core/schema_constants.py` → `QUIKPLAN_SCHEMA`

**Reuse:** CSV column order, DBF layout, validation.

---

### 2. Normalization Utilities

```2833:2837:app.py
def normalize(self, val):
    if pd.isna(val) or str(val).strip().lower() in ['nan', 'none', '']: return ""
    s = str(val).strip().upper()
    if s.endswith('.0'): s = s[:-2]
    return s
```

```2839:2845:app.py
def extract_day(self, date_str):
    ...
```

**Extract to:** `qla_core/normalize_utils.py`

**Reuse:** All field normalization in quikplan converter.

---

### 3. quikplan Source Pre-Processing

```3426:3427:app.py
elif t_id.lower() == "quikplan":
    if 'COVERAGE_ID' in source.columns: source = source.drop_duplicates(subset=['COVERAGE_ID'], keep='first')
```

**Extract to:** `qla_core/quikplan_converter.py` → `prepare_quikplan_source()`

**Behavior:** Dedupe on COVERAGE_ID; skip separator rows (`---` in first columns).

---

### 4. Generic Rulebook Loop (quikplan path)

**Location:** `app.py` lines ~3119–3862 (full table loop); quikplan uses generic path.

Core mapping logic (~3453–3705):

```3453:3488:app.py
for i, src_row in source.iterrows():
    if any("---" in str(v) for v in src_row.values[:3]): continue
    row_data = {h: "" for h in schema}
    for _, rule in rules.iterrows():
        s_f = str(rule.get('Source_Field', '')).strip().upper()
        t_f = str(rule.get('Target_Field', '')).strip().upper()
        ...
        # lookup join for PCOMP
        # default value routing
        # source field mapping
```

**Extract to:** `qla_core/quikplan_converter.py` → `convert_quikplan(source, rules, lookups, trans_map, cw_map, schema)`

---

### 5. quikplan-Specific Transformation Handlers

| Handler | Location | Rulebook Note |
|---|---|---|
| PAR pass-through | `app.py` ~3657-3658 | No PAR_ translation for quikplan |
| Age/YRS zfill | `app.py` ~3595-3597 | LOAGE, HIAGE, PAYYRS, etc. |
| ROUTE_PAY_YRS | `app.py` ~3545-3547 | PREM_CEASE_TYPE == 'D' |
| ROUTE_PAY_AGE | `app.py` ~3548-3550 | PREM_CEASE_TYPE == 'A' |
| ROUTE_INS_YRS | `app.py` ~3551-3553 | BENEFIT_CEASE_TYPE == 'D' |
| ROUTE_INS_AGE | `app.py` ~3554-3556 | BENEFIT_CEASE_TYPE == 'A' |
| trans_map application | `app.py` ~3660-3662 | Master_Value_Translation |
| PLAN cw_map | `app.py` ~3669-3670 | Master_Crosswalk plan rows |

**Extract to:** Same converter module — preserve conditionals exactly.

---

### 6. PCOMP Lookup Loader

```3143:3165:app.py
lookups = {}
if 'Lookup_Table' in rules.columns and 'Join_Key' in rules.columns:
    unique_lookups = rules['Lookup_Table'].dropna().unique()
    for lt in unique_lookups:
        lt_path = os.path.normpath(os.path.join(os.path.dirname(src_path), f"{lt_clean}.csv"))
        ...
```

**Extract to:** `qla_core/lookup_loader.py` → `build_lookup_tables(rules, source_dir)`

**quikplan usage:** PCOMP join on COVERAGE_ID for MINUNIT/MAXUNIT.

---

### 7. Output Writer

```3860:3862:app.py
out_dir = self.path_vars["Out"][0].get()
pd.DataFrame(output, columns=schema).to_csv(os.path.normpath(os.path.join(out_dir, f"{t_id}.csv")), index=False)
```

**Extract to:** Converter returns DataFrame; runner handles staged vs emitted paths.

---

### 8. Audit Log Writer

```3864:3879:app.py
audit_path = os.path.normpath(os.path.join(out_dir, "Migration_Audit_Log.txt"))
...
audit_msg = f"... TABLE: QUIKPLAN | SOURCE RECORDS: {source_count} | QLA OUTPUT: {output_count} ..."
```

**Reuse pattern:** Product runner writes parallel `product_setup_audit.log` with same counts.

---

## Sync_Rulebook_quikplan.csv — Field Routing (Preserve Exactly)

| Source_Field | Target_Field | Lookup | Note |
|---|---|---|---|
| COVERAGE_ID | PLAN | — | Map to crosswalk via engine |
| POLICY_FORM_NUM | FORM | — | |
| DESCRIPTION | DESCR | — | |
| DESCRIPTION | PLANNAME | — | |
| SEX_BASIS | SEX | — | |
| MIN_ISSUE_AGE | LOAGE | — | |
| MAX_ISSUE_AGE | HIAGE | — | |
| PREM_CEASE_POINT | PAYYRS/PAYAGE | — | ROUTE_PAY_* |
| BEN_CEASE_POINT | INSYRS/INSAGE | — | ROUTE_INS_* |
| MIN_ISSUE_AMT1 | MINUNIT | PCOMP | TO_UNITS |
| MAX_ISSUE_AMT1 | MAXUNIT | PCOMP | TO_UNITS |
| PRODUCT_TYPE | PRODUCT | — | |
| (defaults) | PAR, LOANINT, VARDB, ANNL, ... | — | Rulebook Default_Value |

**80 rulebook lines — do not modify.**

---

## Crosswalk Enrichment Adapter (New — P2)

**New file:** `qla_core/crosswalk_enrichment.py`

```python
def build_crosswalk_map(xwalk_path) -> dict:
    """lifepro_coverage_id -> {plan, form, descr, planname}"""

def apply_crosswalk_overlay(row_data, coverage_id, crosswalk_map, fields=("PLAN","FORM","DESCR","PLANNAME")):
    """Apply ONLY when crosswalk match exists; do not blank existing rulebook values."""
```

Called **after** rulebook conversion, **before** final CSV write.

During P2: overlay disabled by default (`CROSSWALK_OVERLAY=0`) to preserve identical output.

---

## Claims Subprocess Pattern — Reuse for Product

Mirror these app.py methods (structure, not code):

| Claims Method | Product Equivalent |
|---|---|
| `_invoke_external_uat_dbf_generation()` | `_invoke_product_setup_runner()` |
| `_parse_phase21b_uat_dbf_stdout()` | `_parse_product_setup_stdout()` |
| `_write_claims_uat_dbf_manifest()` | `_write_product_setup_manifest()` |
| `_claims_uat_dbf_dir()` | `_product_governance_dir()` |

Reference: `app.py` lines ~1118–1230.

---

## DBF Generation — Reuse Pattern

Mirror: `claims_analysis/phase19_uat_emitted_csv_dbf/uat_emitted_csv_dbf_generator.py`

New: `plan_governance/phase_p2_product_setup_runner/quikplan_dbf_generator.py`

- Input: final emitted `quikplan.csv` only
- Layout: from QLAdmin quikplan field spec (TABLE_SCHEMAS + QLAdmin Help)
- Output: `plan_governance/dbf/quikplan.dbf`
- Manifest: CSV/DBF row count alignment

---

## What NOT to Extract (Stay in app.py)

| Code | Reason |
|---|---|
| quikmstr relationship injection | Policy-only |
| quikridr MRIDRID / MPHSTAT sync | Policy-only |
| quikclnt name cache | Policy-only |
| Claims orchestration Phase 18–22 | Out of scope |
| quikprmh special handler | Policy-only |
| Batch table ordering | Policy batch concern |

---

## Import Strategy (P2)

```python
# app.py (minimal change)
from qla_core.quikplan_converter import convert_quikplan, prepare_quikplan_source

elif t_id.lower() == "quikplan":
    source = prepare_quikplan_source(source)
    output_df = convert_quikplan(source, rules, lookups, trans_map, cw_map, self.TABLE_SCHEMAS["quikplan"])
    output = output_df.values.tolist()
    # existing write/audit path unchanged
```

Subprocess runner imports same module — zero logic duplication.
