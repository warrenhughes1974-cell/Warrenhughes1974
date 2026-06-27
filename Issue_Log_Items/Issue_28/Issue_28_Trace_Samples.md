# Issue #28 — End-to-End Trace Samples

**Engine version:** v57.34  
**Intake date:** 2026-06-24

---

## Trace Methodology

Each example traced through:

1. LifePRO source (quikplan_source / PCOMP lineage)
2. Rulebook mapping step
3. Crosswalk / catalog lookup
4. MPLAN assignment path (quikridr)
5. Final quikplan / quikridr output

Runtime behavior verified via read-only import of `load_crosswalk_authority()` against live artifacts. Output verified in `QLA_Migration/Output/quikplan.csv`.

---

## Example 1 — 10827 CSI Life MN $5000 → 1CSIMN

### Client reference

| Field | Value |
|-------|-------|
| LifePRO Coverage_ID | `10827 MN5K` |
| Client description | 10827 CSI Life MN$5000 |
| Expected QLAdmin PLAN | `1CSIMN` |

### Step 1 — Source record

**File:** `plan_analysis/quikplan_source.csv` (row 20)

| Field | Value |
|-------|-------|
| COVERAGE_ID | `10827 MN5K` |
| DESCRIPTION | CSI Life MN $5000 |
| POLICY_FORM_NUM | 10827 |
| STATUS | A |

### Step 2 — Rulebook

**File:** `Sync_Rulebook_quikplan.csv`

```
COVERAGE_ID → PLAN  (Map to crosswalk via engine)
```

Source value `10827 MN5K` enters crosswalk engine as PLAN lookup key.

### Step 3 — Mapping artifacts

| Artifact | Lookup key | Result | Authoritative? |
|----------|------------|--------|----------------|
| Master_Crosswalk.csv (product rows) | `10827 MN5K` | **Not found** — no product row | N/A |
| product_catalog_crosswalk.csv `ql_plan_code` | `10827 MN5K` | `10827 MN5K` (passthrough) | **Runtime emit column** |
| product_catalog_crosswalk.csv `crosswalk_ql_plan_code` | `10827 MN5K` | `1CSIMN` | Authoritative crosswalk — **not used at runtime** |
| Policy Form Crosswalk xlsx | `10827 MN5K` | `1CSIMN` | Authoritative source |
| mapping_status | — | `CROSSWALK_DIVERGENT` | Documented divergence |

**Runtime `product_plan_map`:** `10827 MN5K → 10827 MN5K`

### Step 4 — MPLAN (quikridr)

**Rulebook:** `PLAN_CODE → MPLAN`

| Mode | Input PLAN_CODE | MPLAN emitted |
|------|-----------------|---------------|
| Default (P3E OFF) | `10827 MN5K` | `10827 MN5K` (Master_Crosswalk passthrough) |
| P3E ON, no legacy fallback | `10827 MN5K` | **UNAUTHORIZED** — authoritative `1CSIMN` not in quikplan PLAN set |
| P3E ON, legacy fallback | `10827 MN5K` | `10827 MN5K` |

### Step 5 — Final output

**File:** `QLA_Migration/Output/quikplan.csv` line 19

| Field | Emitted | Expected |
|-------|---------|----------|
| PLAN | `10827 MN5K` | `1CSIMN` |
| FORM | `10827` | `10827 MN5K` (crosswalk form) |
| DESCR | CSI LIFE MN $5000 | CSI Life MN $5000 |

**Ownership:** Discrepancy originates at **`load_product_catalog_crosswalk()` reading `ql_plan_code`** (compat passthrough), not from missing xlsx or missing crosswalk data.

---

## Example 2 — 0823 9 Waiver of Premium - Child → 960CWP

### Client reference

| Field | Value |
|-------|-------|
| LifePRO Coverage_ID | `0823 960CH` |
| Client shorthand | 0823 9 |
| Expected QLAdmin PLAN | `960CWP` |

### Step 1 — Source record

**File:** `plan_analysis/quikplan_source.csv` (row 10)

| Field | Value |
|-------|-------|
| COVERAGE_ID | `0823 960CH` |
| DESCRIPTION | Waiver of Premium - Child |
| POLICY_FORM_NUM | 0823 |

### Step 2 — Rulebook

`COVERAGE_ID → PLAN` via engine crosswalk.

### Step 3 — Mapping artifacts

| Artifact | Result |
|----------|--------|
| Master_Crosswalk.csv | **Not found** for `0823 960CH` |
| product_catalog `ql_plan_code` | `0823 960CH` (passthrough) |
| product_catalog `crosswalk_ql_plan_code` | `960CWP` |
| xlsx authoritative | `960CWP` |
| mapping_status | `CROSSWALK_DIVERGENT` |

**Runtime `product_plan_map`:** `0823 960CH → 0823 960CH`

### Step 4 — MPLAN

Same pattern as Example 1: default passthrough `0823 960CH`; P3E cannot emit `960CWP` while quikplan emits passthrough.

### Step 5 — Final output

**File:** `QLA_Migration/Output/quikplan.csv` line 9

| Field | Emitted | Expected |
|-------|---------|----------|
| PLAN | `0823 960CH` | `960CWP` |

---

## Example 3 — 0824P Payor Disability Rider → 94PDIS

### Client reference

| Field | Value |
|-------|-------|
| LifePRO Coverage_ID | `0824 P DIS` |
| Client shorthand | 0824P |
| Expected QLAdmin PLAN | `94PDIS` |

### Step 1 — Source record

**File:** `plan_analysis/quikplan_source.csv` (row 15)

| Field | Value |
|-------|-------|
| COVERAGE_ID | `0824 P DIS` |
| DESCRIPTION | & Payor Disability Rider |

### Step 2–3 — Mapping

| Artifact | Result |
|----------|--------|
| Master_Crosswalk.csv | **Not found** (note: `0824 P DTH → 90PDTH` exists for death rider, not disability) |
| product_catalog `ql_plan_code` | `0824 P DIS` |
| product_catalog `crosswalk_ql_plan_code` | `94PDIS` |
| mapping_status | `CROSSWALK_DIVERGENT` |

**Runtime `product_plan_map`:** `0824 P DIS → 0824 P DIS`

### Step 4 — MPLAN

Default passthrough `0824 P DIS`. P3E authoritative target `94PDIS` blocked by quikplan emit universe.

### Step 5 — Final output

**File:** `QLA_Migration/Output/quikplan.csv` line 14

| Field | Emitted | Expected |
|-------|---------|----------|
| PLAN | `0824 P DIS` | `94PDIS` |

---

## Cross-Cutting Trace Finding

All three client examples share identical failure mode:

1. Authoritative crosswalk value is **present** in `crosswalk_ql_plan_code` and xlsx.
2. Runtime loader **`load_product_catalog_crosswalk()` selects `ql_plan_code`** (compat passthrough).
3. **`CROSSWALK_OVERLAY=0`** — xlsx not applied post-conversion.
4. **Master_Crosswalk** has no product-row override for these Coverage_IDs.
5. quikplan and quikridr emit LifePRO-style identifiers instead of approved QL Plan Codes.

This is **documented catalog configuration**, not an undocumented converter bug — but it **conflicts with client expectation** that Policy Form Crosswalk 5.22.2026 is authoritative at runtime.
