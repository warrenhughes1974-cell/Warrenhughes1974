# Release Manifest — v57.35

| Field | Value |
|-------|-------|
| **Version** | v57.35 |
| **Release date** | 2026-06-27 |
| **Prior version** | v57.34 |
| **Primary issue** | **#28 — Incorrect Plan Number Mapping (CLOSED)** |
| **Client UAT** | PASS — 2026-06-27 |

---

## Issue Numbers Included

| Issue | Version | In v57.35 release |
|-------|---------|-------------------|
| **#28** PLAN mapping authority | v57.35 | **Yes — primary / CLOSED** |
| #25 MPOLICY padding | v57.30 | Preserved |
| #26 MPREM mapping | v57.31 | Preserved |
| #21M / #21M-FU QUIKMEMO | v57.32–34 | Preserved |

---

## Engine & Core Files

| File | Change |
|------|--------|
| `app.py` | v57.35; post-quikplan P3E refresh |
| `QLA_Migration/app.py` | Mirror |
| `qla_core/product_catalog_authority.py` | `crosswalk_ql_plan_code` authority; P3E default ON |
| `plan_governance/product_catalog_crosswalk.csv` | DISCHO25 row; 141 data rows |
| `QLA_Migration/Mapping/product_catalog_crosswalk.csv` | Synced catalog |
| `tools/validators/validate_issue28_plan_mapping.py` | Issue #28 validator (new) |

---

## Documentation

| Path | Purpose |
|------|---------|
| `Issue_Log_Items/Issue_28/` | Full framework artifact set |
| `Issue_Log_Items/Issue_Log_Master_Tracking_Sheet.md` | #28 CLOSED |
| `Release_Notes/v57.35_Release_Notes.md` | Release notes |
| `Release_Manifest_v57.35.md` | This manifest |

---

## Validation at release cut

| Validator | Result |
|-----------|--------|
| `validate_issue28_plan_mapping.py` | PASS |
| `validate_mpolicy_width.py` | PASS |
| `validate_issue26_mprem.py` | PASS |
| `validate_issue21m_quikmemo.py` | PASS |
| `validate_issue21m_dbf_packaging.py` | PASS |

---

## Environment defaults

| Variable | v57.35 default |
|----------|----------------|
| `QLA_CLOSED_MPLAN_AUTHORITY` | **1** (enabled) |
| `CROSSWALK_OVERLAY` | 0 |

---

## Excluded from this manifest

- Batch-generated `plan_analysis/phase_p3e_*` / `phase_p3f_*` trace files (runtime artifacts)
- `QLA_Migration/Output/` conversion output (environment-specific)
- Unrelated open issues (#21K HOLD, deferred claims)

---

*Release manifest v57.35 — Issue #28 closed — 2026-06-27.*
