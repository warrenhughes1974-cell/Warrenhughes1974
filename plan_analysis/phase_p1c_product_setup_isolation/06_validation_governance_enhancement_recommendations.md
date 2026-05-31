# Validation & Governance Enhancement Recommendations (Phase P1C)

## Principle: Additive Only

Governance enhancements **report and hold optionally** — they do not change rulebook mappings, defaults, or transformation behavior unless business explicitly enables blocking.

Default mode: **WARN + manifest** (emit proceeds).  
Blocking mode: `QLA_PRODUCT_GOVERNANCE_BLOCK=1` (future opt-in).

---

## Recommended Diagnostics

### 1. Duplicate PLAN Detection

| Field | Detail |
|---|---|
| Trigger | Same PLAN value on multiple staged rows |
| Severity | ERROR |
| Current state | `9DIS25` appears twice in output (132 unique / 133 rows) |
| Action | Report in diagnostics; block emit only if BLOCK flag set |
| Auto-fix | **Never** |

### 2. Missing Crosswalk Match

| Field | Detail |
|---|---|
| Trigger | LifePRO COVERAGE_ID in source with no Policy Form Crosswalk row |
| Severity | WARN |
| Current state | 0/133 missing (full coverage in crosswalk 5.22.26) |
| Action | Business review queue |
| Auto-fix | **Never** |

### 3. Orphan MPLAN Diagnostic

| Field | Detail |
|---|---|
| Trigger | quikridr.MPLAN not found in staged/emitted quikplan.PLAN |
| Severity | WARN |
| Current state | 7 codes, 56 rows (`1L15GD`, `1L16GD`, `9DIS80`, `9DIS90`, `DISCHO20 B`, `L16POLFEE`, `L17 BASE`) |
| Action | Cross-reference report for product team; policy batch unchanged |
| Auto-fix | **Never** |

### 4. Blank MPLAN Diagnostic

| Field | Detail |
|---|---|
| Trigger | quikridr row with blank MPLAN |
| Severity | INFO/WARN |
| Current state | 2,348 rows |
| Action | Data quality report; separate from product catalog governance |
| Auto-fix | **Never** |

### 5. Missing FORM Diagnostic

| Field | Detail |
|---|---|
| Trigger | Blank FORM in staged quikplan row |
| Severity | WARN |
| Action | Report; rulebook default may apply |
| Auto-fix | **Never** |

### 6. Crosswalk Field Mismatch

| Field | Detail |
|---|---|
| Trigger | Staged output differs from crosswalk for PLAN/FORM/DESCR/PLANNAME |
| Severity | WARN |
| Current state | 94 FORM mismatches (LifePRO form vs QL Form Number) |
| Action | Business decides whether crosswalk or rulebook wins — **do not auto-override in P2** |
| Note | P1C preserves current rulebook behavior; mismatch is informational until business approves overlay precedence |

### 7. Blank Critical Field Diagnostic

| Field | Detail |
|---|---|
| Trigger | Blank PLAN, blank DESCR, or blank PRODUCT after rulebook |
| Severity | ERROR (if PLAN blank) / WARN (others) |
| Fields monitored | PLAN, FORM, DESCR, PRODUCT |
| Auto-fix | **Never** |

### 8. Schema Integrity

| Field | Detail |
|---|---|
| Trigger | Column count/order differs from TABLE_SCHEMAS quikplan |
| Severity | ERROR |
| Source | `validation_config/key_definitions.json` + app.py schema |
| Action | Block emit |

### 9. Row Count Audit

| Field | Detail |
|---|---|
| Trigger | Source rows (minus separator) ≠ staged rows |
| Severity | WARN |
| Current | 133 source → 133 output (after COVERAGE_ID dedupe) |
| Mirrors | Existing Migration_Audit_Log.txt pattern |

---

## Diagnostic Output Schema

`plan_governance/manifests/product_governance_diagnostics.csv`

```
diagnostic_id,run_timestamp,severity,category,lifepro_coverage_id,output_plan,
target_field,expected_value,actual_value,governance_action,business_review_required,notes
```

---

## Governance vs. Claims Pattern Comparison

| Aspect | Claims Phase 22 | Product P1C |
|---|---|---|
| Hold at emit | Yes (semantic pseudo-claims) | Optional (default OFF) |
| Manifest | claims_review_hold_manifest.csv | product_governance_diagnostics.csv |
| Rollback env | QLA_SEMANTIC_GOVERNANCE_HOLD=0 | QLA_PRODUCT_SETUP_ROLLBACK=1 |
| Integration in app.py | Filter staged CSV at emit | Subprocess + optional batch skip |

Product governance is **lighter by default** because the catalog is business-maintained configuration, not derived transactional data.

---

## Crosswalk Enrichment Governance (Not Semantic)

When business approves crosswalk overlay precedence (future):

1. Document decision in manifest: `CROSSWALK_OVERLAY_APPROVED=Y`
2. Overlay applies ONLY to: PLAN, FORM, DESCR, PLANNAME
3. All other fields remain rulebook-driven
4. Re-run parallel diff against prior output before emit

Until approved: diagnostics report mismatches; **rulebook + Master_Crosswalk plan map behavior unchanged**.

---

## Validation Pipeline (Additive)

```
staged quikplan.csv
    → schema order check (TABLE_SCHEMAS)
    → PLAN uniqueness check (key_definitions)
    → crosswalk coverage check
    → optional quikridr MPLAN orphan check
    → write diagnostics CSV
    → emit gate (if enabled)
```

---

## Explicitly NOT in Scope

- HRIGPKEY validation (future actuarial phase)
- Vary-by combination validation (future)
- Auto-remediation of duplicate PLAN
- Silent dropping of unmatched source rows
- Rider/plan semantic reclassification (business confirmed quikplan includes all product types)
