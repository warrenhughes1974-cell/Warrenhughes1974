# Issue 138 — Gross premium rates filed one year above the age they rate

**Raised:** 2026-08-09 (Warren, during Issue 118 UAT review)
**Status:** Validation PASS — ready for Regression
**Engine:** v58.88 (`app.py` and `QLA_Migration/app.py`)
**Valuation date:** 20260630

---

## Symptom

Every gross premium screen in QLAdmin rendered `0.00`. Plan `1L14SC` was the anchor:
Gross Prems opened on a full grid of zeros for every gender and underwriting class,
while the same plan's Terminal Reserves screen displayed correct values.

## What was actually wrong

LifePRO's `PAAGERAT.SEQ` is a **1-based ordinal**, so the rate carried on `SEQ n`
belongs to issue age `n - 1`. The loader passed `SEQ` straight through as the QLAdmin
`AGE`, so every gross premium was filed one year above the age it rates.

`1L14SC` is issued at ages **45–85**. Its reserve grid runs 45–85 and displays. Its
premium grid ran **46–86** — starting one past the first age QLAdmin builds from plan
setup, and running one past the last age the plan allows.

Elsewhere in the conversion LifePRO ordinals are already converted on the way in
(`rate_dbf_schema.source_duration_to_ql` subtracts 1 for durations). The age axis was
never given the same treatment.

### Why the screen showed zeros rather than shifted values

The `AGE = 45` row QLAdmin looks for first did not exist, so the grid opened empty.
This was misread twice before the cause was found — first as "scroll to a populated
age," then as a wrong `VARGP` code. Toggling Var GP between 0 and 3 changed nothing,
because no variation code can rescue a grid whose first age is missing.

## Evidence

`quikridr.MPREM` carries LifePRO `ANN_PREM_PER_UNIT` (Issue 88) — a policy field, not
a conversion product — so it is an independent check on the rate grid. Every in-force
policy was tested against the rate at its own issue age versus one year either side.

| Result | Plans | Detail |
|---|---|---|
| Premium matched `age + 1` | 22 | 100% of policies on each: `1L14SC` 224/224, `1L10SO` 339/339, `17085M` 138/138 |
| Rate flat across ages | 5 | ADB riders; every offset matches, consistent but not discriminating |
| Not testable this way | 18 | ISWL / banded plans where `MPREM` is not a plain per-unit grid read |
| Contradicted `age + 1` | **0** | — |

Worked example — policy `9011206462C`, M/NT, issued at age **64**, LifePRO premium
`63.24`. Before: grid age 64 held `59.88` and `63.24` sat at age 65. After: grid age 64
holds `63.24`.

## Fix

Two loaders derived `AGE` from `SEQ`, and both needed the same offset:

| File | Change |
|---|---|
| `qla_core/paagerat_pr_loader.py` | Added `PR_AGE_OFFSET = -1` and an `age_offset` parameter on `transform_paagerat_attained_age`; only `transform_paagerat_pr` passes it |
| `qla_core/shared_rate_candidate_loader.py` | `_transform_paagerat_row` applies the same offset when `TYPE_CODE == "PR"` |

The offset is opt-in per caller. `NF`, `BP`, `DB` and `COI` still ride the unshifted
axis, because the policy-premium evidence only covers `PR`. `1L10SR` and `1L10OD` draw
premiums through the shared-rate path and were still a year high after the first pass,
which is what surfaced the second loader.

Rows that would fall below age 0 after the offset are emitted as `BAD_VALUE` with
lineage rather than silently clamped.

## Validation

```
python tools/validators/validate_issue138_rate_age_alignment.py
```

New validator, anchored on LifePRO premiums rather than our own output. Per plan it
counts how many policies find their own premium at offset -1, 0 and +1, and fails any
plan that rates a policy better at a neighbouring age.

**Result: PASS** — 77 plans scored; 27 ALIGNED, 1 PARTIAL (`1SALOL`), 17 UNTESTABLE,
32 skipped as too few policies to outvote noise. **0 MISALIGNED.**

Supporting checks on the rebuilt package:

- Rate emit: SUCCESS, 0 blockers, 23 tables, 191,673 rows
- `1L14SC` F/NT grid now runs 45–85; age 64 = `63.24` = policy `9011206462C`
- Release gate high-risk smokes: 12 of 12 PASS, including A7 VARGP/VARDB, L14 QuikCvs
  and #106 QuikTvs
- Accountability: 64 IN_DATA, 0 GAP

### Collateral fix

`tools/validators/validate_issue_log_accountability.py` still spot-checked `1659C2`
under UW class `SM`. Issue 118 remapped that plan (not an L10 form) to `ST`, and the
`#106` smoke had already been corrected; the accountability copy was missed and was
reporting a GAP against intact data (`ST` dur1 = `1.00`, dur83 = `978.00`). Expectation
updated to `ST`.

## Still open

1. **18 untestable plans** — ISWL / banded forms (`1659C2`, `1658C1`, `5L0110`,
   `1L1095`, `5667AT` and others) where `MPREM` is not a direct per-unit lookup. The
   offset was applied to them on the strength of the loader-level defect, not
   plan-level proof. They need a band-aware or ISWL-aware check.
2. **Attained-age storage axis** — the 37 rider plans (`543CTR`, `943CWP`, `920ADB`,
   `9CDTWP`) whose grids genuinely run past the issue-age window to age 99. The real
   QLAdmin `QuikDbs` reference table stores a non-issue-age grid as `AGE='00'` with
   `CNTL` paging (`plan_analysis/source_data/reference_dbf/QuikDbs.dbf`), and the
   schema inventory confirms column `GPn` is slot `CNTL*10 + n`. Whether attained-age
   premiums belong on that axis instead is unresolved and is **not** changed here.
3. **Full batch** — rates were re-emitted in place via the R5 runner. A full batch
   should be run before Closure so `quikplan` and the rate package come off the same
   commit (G7).

## Rollback

Prior rate package archived to
`QLA_Migration/Archive/rates_pre_issue138_20260809T162636Z/` (23 tables).
