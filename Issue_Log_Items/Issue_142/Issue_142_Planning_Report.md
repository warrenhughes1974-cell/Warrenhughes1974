# Issue 142 — Planning Report

**Date:** 2026-08-29 · **Stage:** Planning (no production code)
**Design principle:** surgical edits, rollback-safe, minimal blast radius, schema untouched.

## Design summary

Emit each **Active** SL row (STATUS_CODE = A, 22 rows in the 06/30 source) as its own quikridr
phase under new plan code **9SUBLF**, with the value-per-unit zeroed so no insured amount is
added, and the rating premium preserved through the standard per-unit premium field.
Terminated SL rows (46) remain suppressed under the existing Issue #27 governance.

## Change 1 — quikplan: seed the 9SUBLF plan row

9SUBLF has no LifePRO PCOVR coverage row, so it cannot come through the rulebook. Seed it as a
post-emit enrichment step in the quikplan pipeline (same layer as `apply_issue_a_plan_setup`
in `qla_core/quikplan_converter.py::run_quikplan_conversion`), appended only when absent
(idempotent, append-only).

Proposed row (follows the 9SLADB supplemental pattern + Issue A checklist):

| Field | Value | Why |
|---|---|---|
| PLAN | 9SUBLF | Eric-assigned code |
| DESCR / PLANNAME | SUBSTANDARD LIFE PREMIUM RIDER | plain description |
| PAR | 0 | A9b: prefix-9 supplemental PAR=0 |
| VARDB | 0, VARGP | 3 | matches 9SLADB supplemental pattern |
| ANNL/SEMI/QTRL/MTHD/MTHB | 100.0000 / 50.0000 / 25.0000 / 8.3333 / 8.3333 | neutral 1/n factors; rounding accepted (decision 4); riders assumed non-billing (decision 3) |
| INITVAL | 0.00 | benefit tied to zero — a later policy edit cannot re-introduce insured amount |
| LOAGE 00 / HIAGE 100 / PAYYRS 100 / INSYRS 100 / RENEW N | standard supplemental bounds |
| PRODUCT (supp type) | populated (supplemental) | A9a: supp type must not be blank |
| All *VARY* = N, DEFICIENCY = N, RRULE B, LOANINT 0.00, fees 0 | no rates, no loans, no fees |

Rates: **none required.** The A3 default-key-stub mechanism (`qla_core/rate_pipeline.py`)
extends TESTRD-style default PVO keys to the full authoritative QuikPlan universe, so 9SUBLF
gets default keys (including gender 0) automatically on the next rate emit.

## Change 2 — product catalog: route SL rows to 9SUBLF

Add one row to `QLA_Migration/Mapping/product_catalog_crosswalk.csv`:
`lifepro_coverage_id = 9SUBLF → ql_plan_code = 9SUBLF` (identity entry, STABLE_EMIT-style,
governance note referencing Issue 142). This lets the closed MPLAN authority resolve the
sentinel and pass `exists_in_quikplan`.

## Change 3 — app.py quikridr block: split SL handling (the surgical edit)

Current block (app.py ~8700–8726) suppresses every SL row. New behavior:

1. Partition SL rows by `STATUS_CODE`:
   - **A (22 rows)** → keep in source with three column transforms **before** generic mapping:
     `PLAN_CODE → '9SUBLF'` (routes MPLAN via Change 2), `VALUE_PER_UNIT → '0'` (MVPU = 0),
     everything else untouched.
   - **Not A (46 rows)** → suppress exactly as today, Issue #27 audit unchanged for them.
2. Everything downstream is the existing standard pipeline — no new field logic:
   - MPHASE = BENEFIT_SEQ (unique per policy; no collisions — verified).
   - MPHSTAT = standard status translation (A → 22).
   - MPREM = ANN_PREM_PER_UNIT (Issue 26 mapping). Zero-premium SL rows stay 0: the Issue
     88/137 fallback requires MODE_PREMIUM > 0 **and** units > 0, so the 14 informational rows
     and the 9010782078 outlier (0 units, 0 APU) emit MPREM = 0 by existing logic (decision 2).
   - MPAR = quikplan PAR for 9SUBLF = 0 (Issue #105 logic, automatic).
   - MRIDRID / MUWCLASS / dates map from PPBEN columns as for any rider row.
3. Write an Issue 142 emit audit CSV (`Issue_Log_Items/Issue_142/evidence/`) listing the 22
   emitted rows; narrow the Issue #27 audit wording to "non-active SL rows".
4. **Bump APP_VERSION in BOTH `app.py` (root) and `QLA_Migration/app.py`.**

## Change 4 — quikuwpo (A11)

Active SL rows carry UNDERWRITING_CLASS values **0 (11), S (8), B (2), P (1)**. Confirm the
existing quikuwpo generation picks up plan 9SUBLF × each distinct UW class (one row per
combo, no dupes). If quikuwpo is driven off quikridr/PPBEN generically this is automatic;
verify in Validation, add rows to the generator only if missing.

## Change 5 — governance module

`qla_core/sl_benefit_governance.py`: add an `is_active` predicate (STATUS_CODE = A) used by
the app.py split; keep `build_sl_suppression_audit_rows` for the suppressed subset. Docstring
updated: Issue #27 narrowed by Issue #142 (Warren override 2026-08-29).

## Smoke test (designed now, registered at Closure per Framework rule 14)

`tools/validators/validate_issue142_sl_rider.py` — fail-closed (exit 1) against full
`QLA_Migration/Output/`:

1. quikplan contains exactly one 9SUBLF row with PAR=0.
2. quikridr 9SUBLF row count ≥ 22 (count floor — catches a rebatch that drops the fix).
3. **Every** 9SUBLF row has MVPU = 0 (duplication guard).
4. All 22 anchor policies have a 9SUBLF phase; the 8 red anchors match source
   (e.g. 9010886099C: MUNIT 100, MPREM 26.34; 9010469666C: MUNIT 10, MPREM 2.50;
   9011201237C: MUNIT 25, MPREM 11.935).
5. 9010782078C 9SUBLF row has MPREM = 0 (decision 2 guard).

At Closure: append `("#142 SL rider 9SUBLF", [script], True)` to `SMOKE_JOBS`, add the guide
high-risk smoke row, prove `--smoke-only` PASS.

## Validation & regression plan

- Full batch with `QLA_VALUATION_DATE=20260630` (06/30 source package).
- Issue validator (above) PASS on full Output.
- Regression: quikridr = baseline + exactly 22 new 9SUBLF rows, zero deltas on non-SL rows;
  quikplan = baseline + 1 row; quikmstr/quikclnt/etc. byte-identical; rates delta limited to
  A3 default key stubs for 9SUBLF.
- Issue A conversion checklist run (A1–A12) on the new Output.
- Publish modified tables (quikplan, quikridr, quikuwpo if touched) to `Output/Test_Validation/`.
- Accountability IN_DATA for issue 142; G7 gate before Closed.

## Rollback

Single-commit revert restores blanket SL suppression; no schema, no field-order, no rate-value
changes anywhere. Baseline quikridr/quikplan snapshots retained in evidence before apply.
