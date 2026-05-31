# R6A — QLAdmin Member Table Import Validation Summary

Lightweight validation package for the five R5-generated member/dimension tables.
**Read-only:** no loader, factor, rate-key, or governance logic modified. No values invented.

## Verdict: **PASS** (structural + referential)

All automated R6A checks passed against emitted DBFs in
`plan_analysis/phase_r5_rate_loader/emitted_dbf/`.

| Check | Result |
|---|---|
| All 5 member DBFs readable | PASS |
| Row counts populated | PASS (384 total) |
| PLAN values populated | PASS (0 blank PLAN) |
| No unexpected duplicates | PASS |
| No orphan PLAN references | PASS (64/64 aligned to rate keys) |
| Member codes cover key segmentation | PASS |
| Placeholder governance documented | PASS (`MEMBER_PLACEHOLDER_DEFERRED`) |

## Files created

| File | Purpose |
|---|---|
| `_build_r6a_package.py` | Read-only validator + artifact generator |
| `r6a_member_table_manifest.csv` | Per-table row/plan counts and status |
| `r6a_member_sample_validation.csv` | 31 UAT sample rows (`VALIDATED` blank for tester) |
| `r6a_member_validation_results.json` | Machine-readable structural/referential results |
| `r6a_member_import_checklist.md` | Sandbox import procedure and load order |
| `r6a_member_validation_summary.md` | This document |

## Member table manifest

| TABLE_NAME | ROW_COUNT | DISTINCT_PLAN_COUNT | STATUS |
|---|---:|---:|---|
| QuikPlGd | 110 | 64 | PASS |
| QuikPlUw | 80 | 64 | PASS |
| QuikPlBd | 66 | 64 | PASS |
| QuikPlSt | 64 | 64 | PASS |
| QuikPlNb | 64 | 64 | PASS |

## Structural validation detail

- **QuikPlGd** — unique key `PLAN + GDCODE`; gender codes M/F/J present in sample.
- **QuikPlUw** — unique key `PLAN + UWCODE`; UW codes 00/NS/SM/PR/ST present in sample.
- **QuikPlBd** — unique key `PLAN + BDCODE`; bands 01/02/03 present in sample.
- **QuikPlSt** — unique key `PLAN + ISSCNTRY + ISSUEST`; default `0000/00` segmentation.
- **QuikPlNb** — unique key `PLAN + ISSCNTRY + ISSUEST + EFFDATE`; all `EFFDATE = 19000101`.

## Referential validation detail

Cross-checked all member-table PLANs against the union of rate-key tables
(`QuikPlGp`, `QuikPlDv`, `QuikPlDb`, `QuikPlCv`, `QuikPlTv`):

- **0** member-table PLANs without a rate-key parent.
- **0** rate-key PLANs missing member-table entries.
- **0** segmentation codes in keys missing from the corresponding member table.

## Placeholder governance (`MEMBER_PLACEHOLDER_DEFERRED`)

These are **expected** and must **not** be treated as import defects:

| Field | Count | Expected | Notes |
|---|---:|---|---|
| `QuikPlBd.BDLOWVAL` | 66 | `0` | Band breakpoint amounts — business input pending |
| `QuikPlSt.MLOANINT` | 64 | blank | Loan interest — business input pending |
| `QuikPlNb.TERMDATE` | 64 | blank/open | Plan availability end — business input pending |

Actuarial rate-key assumptions (MORT, RSVINT, etc.) remain separately deferred per R5/R6 — out of R6A scope.

## Sample validation matrix (UAT)

`r6a_member_sample_validation.csv` includes 31 cases covering:

- Gender members (M, F, J) including plan `7687J3` (JOINT)
- UW classes (00, NS, SM, PR, ST)
- Bands (01, 02, 03) including plan `2665ST`
- State/country `0000/00` display text
- New-business window `EFFDATE=19000101` / open `TERMDATE`
- Three `MEMBER_PLACEHOLDER_DEFERRED` governance rows

QLAdmin tester: complete the `VALIDATED` column during sandbox plan-maintenance review.

## Code changes

**No changes** to R5 factor generation, rate-key generation, `app.py`, or `qla_core` loader modules.

New files only under `plan_analysis/phase_r6a_member_table_validation/` (isolated read-only validation layer).

## Impact analysis

| Area | Impact |
|---|---|
| R5 emitted DBFs | None — read-only inspection |
| Rate loader pipeline | None |
| Product/claims governance | None |
| R6 import package | Complementary — extends load order with explicit member-table validation |
| QLAdmin sandbox import | Member tables should load before keys/factors (documented in checklist) |

## Rollback analysis

- R6A adds documentation and a read-only script only; **zero production risk**.
- If member import fails in sandbox, restore pre-import snapshot — emitted DBFs unchanged.
- Re-run `_build_r6a_package.py` after any R5 re-emit to refresh manifest/sample CSVs.

## Open items (not R6A blockers)

- Populate `BDLOWVAL` band breakpoints before production band-dependent behavior.
- Populate `MLOANINT` before loan-interest-dependent plan maintenance.
- Set `TERMDATE` when plan availability windows are finalized.
- Complete manual QLAdmin `VALIDATED` column in sample CSV during UAT.

## Commands

```bash
# Regenerate R6A artifacts (read-only)
python plan_analysis/phase_r6a_member_table_validation/_build_r6a_package.py

# Full rate library re-emit (only if R5 inputs change — not required for R6A)
python plan_analysis/phase_r5_rate_loader/rate_loader_emit.py
python plan_analysis/phase_r5_rate_loader/effdate_verification.py
python plan_analysis/phase_r6_qla_rate_import_validation/_build_r6_package.py
```
