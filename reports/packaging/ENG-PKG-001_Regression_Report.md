# ENG-PKG-001 Regression Report

**Date:** 2026-07-12  
**Verdict:** PASS WITH REVIEW ITEMS  

## Existing engine test suite

No dedicated pre-existing `qla_core` unit test suite was found in the authoritative repository. Monorepo tests in `data_governance/tests/` and `tools/validators/` reference qla_core indirectly but are client-governance scoped.

**Regression gap:** Documented — not constructed from confidential client files.

## ENG-PKG-001 packaging tests

| Environment | Result |
|-------------|--------|
| Source tree | 9 passed, 1 skipped (metadata — requires install) |
| Clean venv (installed wheel) | 10 passed |

## Behavioral fixtures (packaging tests)

| Area | Test | Result |
|------|------|--------|
| Rate schema | `duration_to_cntl_col`, `source_duration_to_ql`, `format_factor` | PASS |
| Factor loader | `LoaderConfig` defaults | PASS |
| Key setup | Blank `AssumptionProvider` | PASS |
| Member setup | Empty grids | PASS |
| Import safety | No sys.path mutation, no file writes | PASS |

## Business behavior

No rate calculation, normalization, key construction, member construction, or writer formatting code was modified.

## Review items

- Broader monorepo regression not executed (out of ENG-PKG-001 scope)
- License metadata unresolved
