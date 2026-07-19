# DG-R-006 — Validation

**Date:** 2026-07-18  
**Data region:** `Q:\CSO\CSO_Test_6_30_2026`

## Checks

| Check | Result |
|-------|--------|
| `list_rule_definitions()` contains `DG-QUIKPLAN-022` | **False** (61 rules registered) |
| `get_rule("DG-QUIKPLAN-022")` | **KeyError** Unknown governance rule ID |
| Neighboring rules 021 / 023 / 030 on CSO | **Passed** 142/142 (run `DG-20260718_193244_858757`) |
| Explicit `--rule DG-QUIKPLAN-022` | Incomplete selection (rule unknown) — expected |
| `pytest` test_dg_quikplan + test_framework | **Pass** after count 62→61 |

## Residual

None for this item. Historical validation_out folders under other DG-R-* items may still mention 022 in generated manifests; those are archives, not live catalog.
