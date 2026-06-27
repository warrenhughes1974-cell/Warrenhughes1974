# Issue #28 — Release Manifest

**Version:** v57.35  
**Issue:** #28 — Incorrect Plan Number Mapping  
**Status:** CLOSED  
**Release date:** 2026-06-27

---

## Release package contents

### Code (required deploy)

| File | Phase | Description |
|------|-------|-------------|
| `qla_core/product_catalog_authority.py` | 1, 2 | Authority promotion + P3E default |
| `app.py` | 1, 2 | v57.35 + P3E batch refresh |
| `QLA_Migration/app.py` | 1, 2 | Mirror |
| `tools/validators/validate_issue28_plan_mapping.py` | — | Regression validator |

### Data (required deploy)

| File | Phase | Description |
|------|-------|-------------|
| `plan_governance/product_catalog_crosswalk.csv` | 0 | DISCHO25 + 141 rows |
| `QLA_Migration/Mapping/product_catalog_crosswalk.csv` | 0 | Synced copy |

### Unchanged (do not replace for #28 alone)

- `Sync_Rulebook_quikplan.csv`
- `Master_Crosswalk.csv`
- Policy Form Crosswalk xlsx

---

## Validation evidence (reference)

| Artifact | Location |
|----------|----------|
| PLAN diff (33 rows) | `evidence/v57.35_quikplan_plan_diff.csv` |
| Validator output | `evidence/validate_issue28_results.txt` |
| Intake analysis | `evidence/issue28_intake_analysis_v5735.txt` |
| Protected regressions | `evidence/validate_issue25_mpolicy.txt`, etc. |

---

## Client acceptance

| Field | Value |
|-------|-------|
| UAT | PASS |
| Sign-off | 2026-06-27 |
| Scope | 141/141 mappings; 33 corrections; DISCHO25 |

---

## Git release tag reference

Commit message: `Release v57.35 - close Issue #28 plan mapping authority`

See `Issue_28_Release_Integration_Report.md` for commit hash after publish.
