# R6A — QLAdmin Member Table Import Checklist

> **SANDBOX ONLY.** Import member tables into a QLAdmin **sandbox/test** environment first.
> Member tables declare valid segmentation members per PLAN and must load **before** rate-key
> and factor tables. Deferred placeholders (`BDLOWVAL`, `MLOANINT`, `TERMDATE`) are expected —
> classify as `MEMBER_PLACEHOLDER_DEFERRED`, not defects.

Source DBFs: `plan_analysis/phase_r5_rate_loader/emitted_dbf/`  
Manifest: `r6a_member_table_manifest.csv`  
Sample UAT cases: `r6a_member_sample_validation.csv`

## Prerequisite (must already exist)

- [ ] **QuikPlan** — every PLAN in the member tables (64 distinct plans) must exist in governed quikplan setup.
- [ ] Sandbox backup/snapshot taken of any existing member, key, and factor tables you will replace or append to.

## Recommended load order (full rate library)

### Phase A — Member / dimension tables (R6A scope)

1. [ ] `QuikPlGd` — gender members (110 rows)
2. [ ] `QuikPlUw` — underwriting-class members (80 rows)
3. [ ] `QuikPlBd` — band members (66 rows; `BDLOWVAL = 0` placeholder)
4. [ ] `QuikPlSt` — state/country members (64 rows; `MLOANINT` blank placeholder)
5. [ ] `QuikPlNb` — new-business window (64 rows; `EFFDATE = 19000101`, open `TERMDATE`)

### Phase B — Rate-key tables (existing R6)

6. [ ] `QuikPlGp`
7. [ ] `QuikPlDv`
8. [ ] `QuikPlDb`
9. [ ] `QuikPlCv`
10. [ ] `QuikPlTv` *(shared by Terminal Reserve and Net Premium)*

### Phase C — Factor tables (existing R6)

11. [ ] `QuikGps`
12. [ ] `QuikDvs`
13. [ ] `QuikDbs`
14. [ ] `QuikCvs`
15. [ ] `QuikTvs`
16. [ ] `QuikNps`

## Per-table import steps

For each member table:

- [ ] Confirm target table backed up.
- [ ] Import DBF (append/replace per sandbox procedure).
- [ ] Confirm imported row count matches manifest `ROW_COUNT`.
- [ ] Confirm no blank `PLAN` values.
- [ ] Confirm no duplicate member keys (see structural validation in summary).
- [ ] Record import timestamp and operator.

## Post-import structural checks (automated baseline — R6A)

- [ ] All 5 member DBFs readable.
- [ ] Row counts match manifest (384 total member rows).
- [ ] 64 distinct PLAN values across member tables.
- [ ] Every member-table PLAN exists in rate-key tables (no orphan PLAN references).
- [ ] Every rate-key PLAN has corresponding member rows for GENDER / UWCLASS / BAND / ISSCNTRY+ISSUEST.
- [ ] No unexpected duplicate keys within any member table.

## Post-import functional checks (QLAdmin tester — manual)

Use `r6a_member_sample_validation.csv`. For each row, open the plan in QLAdmin plan maintenance and confirm the member code is **visible and displayable**. Record `VALIDATED` (Y/N/Notes).

Coverage targets in the sample matrix:

| Member type | Codes to confirm |
|---|---|
| Gender (`QuikPlGd`) | M, F, J |
| UW class (`QuikPlUw`) | 00, NS, SM, PR, ST |
| Band (`QuikPlBd`) | 01, 02, 03 |
| State/country (`QuikPlSt`) | `0000/00` (ALL OTHER) |
| New business (`QuikPlNb`) | `EFFDATE=19000101`, open termination |

Special plans included: `130JEB`, `1658C1`, `1L10OD`, `2665ST`, `A96DAR`, `7687J3`.

## Placeholder governance (expected — do NOT fail import)

| Field | Table | Expected value | Classification |
|---|---|---|---|
| `BDLOWVAL` | `QuikPlBd` | `0` | `MEMBER_PLACEHOLDER_DEFERRED` |
| `MLOANINT` | `QuikPlSt` | blank | `MEMBER_PLACEHOLDER_DEFERRED` |
| `TERMDATE` | `QuikPlNb` | blank/open | `MEMBER_PLACEHOLDER_DEFERRED` |

Do **not** populate these during R6A. Supply business/actuarial values before production load that depends on band breakpoints, loan interest, or plan termination windows.

## Rollback

1. Restore sandbox snapshot taken before import.
2. Do not hand-edit emitted DBFs.
3. Re-run `_build_r6a_package.py` to regenerate validation artifacts if DBFs are re-emitted.

## Regenerate validation package

```bash
python plan_analysis/phase_r6a_member_table_validation/_build_r6a_package.py
```
