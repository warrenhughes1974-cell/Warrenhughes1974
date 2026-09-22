# Issue 151 — Validation Report

**Date:** 2026-09-22  
**Engine:** v59.18  
**Result:** **PASS — conversion fix validated; fresh QLAdmin valuation remains UAT**

## Validated result

Policy `9010969231C` now has zero false-surrender history in full
`QLA_Migration/Output/`:

- `QuikIsrr`: 0 rows
- `quikclms`: 0 PS-/SRR phase-0 rows
- `quikclmp`: 0 phase-0 companion rows
- `quikbenh`: 0 type-8 rows

Exactly eight rows were removed from each table. No non-candidate rows changed.

## Preserved policy values

| Field | Validated value |
|---|---:|
| quikridr phase-1 MUNIT | 5.00000 |
| quikridr phase-1 MPREM | 37.62 |
| quikridr phase-1 MCV0 | -812.49000 |
| quikmstr MMODEPREM | 163.10 |

The `$163.10` load premium remains correct under Closed Issue 139. The conversion
does not load `$2,899.79`.

## Regression controls

- `9010761639C`: one genuine QuikIsrr row for `$271.00` retained.
- `9010760840C`: two genuine rows totaling `$716.40` retained.
- Original Issue 146 allowlist: zero QuikIsrr leaks.
- Issue 145B validator: PASS.
- Issue 146 validator: PASS with 21 allowlist policies.
- Named Issue 151 fail-closed smoke: PASS.

## Commands

```text
python tools/validators/validate_issue151_pc_isrr.py
python tools/validators/validate_issue146_pc_isrr.py
python tools/validators/validate_issue145b_vb_isrr_exclude.py
python tools/validators/validate_release_closed_issues.py --smoke-only
```

The release smoke ran Issue 151 successfully. The overall release gate remains
blocked by pre-existing Issue 160 and Issue 161 failures; neither is caused by
Issue 151.

## Test Validation publish

Published the four validated tables:

```text
python tools/publish_test_validation.py QuikIsrr quikclms quikclmp quikbenh --issue Issue_151
```

`Output/Test_Validation/` now contains the validated `quikisrr.csv`,
`quikclms.csv`, `quikclmp.csv`, and `quikbenh.csv`.

## Open UAT item

The available `QuikValf.dbf` is still the before-state valuation and therefore
still shows 3.4952 units, Extended Term, and `$2,899.79`. Run a fresh QLAdmin
valuation after loading these tables and confirm:

1. units remain 5.0000;
2. the policy is premium-paying rather than Extended Term; and
3. the `$2,899.79` valuation premium is gone.

Do not mark Issue 151 Closed until UAT, Regression, G7 accountability, and Closure
are complete.
