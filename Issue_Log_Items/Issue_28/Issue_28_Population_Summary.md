# Issue #28 — Population Summary

**Engine version:** v57.34  
**Intake date:** 2026-06-24  
**Analysis script:** `Issue_Log_Items/Issue_28/_issue28_intake_analysis.py` (read-only)

---

## Authoritative Crosswalk Baseline

| Metric | Count |
|--------|------:|
| Policy Form Crosswalk 5.22.2026 rows | 141 |
| Unique LifePRO Coverage_IDs | 141 |
| Duplicate Coverage_IDs in crosswalk | 0 |

---

## Converter Mapping Universe

| Metric | Count |
|--------|------:|
| product_catalog_crosswalk.csv (plan_governance — **runtime path**) | 140 |
| product_catalog_crosswalk.csv (QLA_Migration/Mapping copy) | 133 |
| Master_Crosswalk product (non-policy) rows | 427 |
| quikplan.csv output rows | 141 |
| quikplan.csv unique PLAN values | 139 |
| quikridr.csv unique MPLAN values | 137 |

---

## Crosswalk vs Runtime Comparison

Comparison method: For each of 141 authoritative crosswalk rows, resolve runtime PLAN via `load_crosswalk_authority().product_plan_map` (v57.34 default path, overlay OFF).

| Metric | Count |
|--------|------:|
| **Exact matches** (runtime PLAN = authoritative QL Plan Code) | **108** |
| **Mismatches** | **33** |
| Match rate | 76.6% |

### Mismatch breakdown

| discrepancy_type | Count | Description |
|------------------|------:|-------------|
| COMPAT_EMIT_VS_CROSSWALK_AUTHORITY | 33 | All mismatches are `mapping_status=CROSSWALK_DIVERGENT` — `ql_plan_code` ≠ `crosswalk_ql_plan_code` |
| MISSING_FROM_CATALOG | 0 | All 141 crosswalk IDs present in governance catalog (1 ID differs between migration copy and governance) |

---

## CROSSWALK_DIVERGENT Population

| Metric | Count |
|--------|------:|
| Catalog rows flagged CROSSWALK_DIVERGENT | 33 |
| Divergent rows that mismatch authoritative crosswalk at runtime | 33 (100%) |
| Divergent rows present in quikplan output with compat PLAN | 33 |

**Interpretation:** The entire divergent population is accounted for by the dual-column catalog design. No additional undocumented mapping drift was found beyond these 33 rows.

---

## Missing / Extra Mappings

| Category | Count | Detail |
|----------|------:|--------|
| Crosswalk rows missing from QLA_Migration/Mapping catalog | 8 | Present in governance catalog; migration copy is stale |
| Crosswalk rows missing from governance catalog | 1 | See `Issue_28_Missing_From_Converter.csv` |
| Extra converter mappings not in crosswalk | 0 | No orphan catalog rows outside crosswalk scope |

### Catalog copy drift (QLA_Migration vs plan_governance)

Seven LifePRO IDs exist in governance catalog but not migration copy:

`DISCHO20 B`, `DISCHO80`, `DISCHO90`, `L15`, `L16`, `L16POLFEE`, `L17 BASE`

Runtime batch uses **plan_governance** path — migration copy lag is a packaging risk, not current runtime behavior.

---

## Mapping Cardinality

| Pattern | Count | Notes |
|---------|------:|-------|
| One LifePRO ID → one QL Plan Code (authoritative) | 141 | All crosswalk rows |
| Many LifePRO IDs → one QL Plan Code | 0 | No many-to-one in authoritative crosswalk |
| One LifePRO ID → multiple QL Plan Codes | 0 | No duplicates |
| Runtime many-to-one (compat PLAN) | 0 | Each divergent row has unique compat passthrough |

---

## quikridr MPLAN Population Note

Current batch `quikridr.csv` does not contain MPLAN values `10827 MN5K`, `0823 960CH`, or `0824 P DIS` — indicating no in-scope policies in the current batch export carry these riders. PLAN/MPLAN mapping logic was verified via runtime simulation and quikplan product catalog rows; rider-level evidence would require a batch containing affected policies.

---

## Client Examples — Confirmed in Divergent Population

| LifePRO ID | Authoritative PLAN | Runtime PLAN | In quikplan output |
|------------|-------------------|--------------|-------------------|
| 10827 MN5K | 1CSIMN | 10827 MN5K | Yes |
| 0823 960CH | 960CWP | 0823 960CH | Yes |
| 0824 P DIS | 94PDIS | 0824 P DIS | Yes |

---

## Supporting Artifacts

| File | Description |
|------|-------------|
| `Issue_28_Crosswalk_Inventory.csv` | Full authoritative crosswalk export |
| `Issue_28_Mapping_Differences.csv` | Row-level runtime vs authoritative comparison |
| `Issue_28_Missing_From_Converter.csv` | Crosswalk IDs absent from governance catalog |
| `Issue_28_Extra_In_Converter.csv` | Extra converter rows (empty — 0 rows) |
| `_population_stats.json` | Machine-readable summary counts |
