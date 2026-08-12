# Issue 139 — Policy fees withheld for ISWL / UNKNOWN only

**Raised:** 2026-08-09 (Warren)
**Refined:** 2026-08-11 (Warren) — restore non-ISWL #21C/#58 fees
**Status:** Validated — pending G7 accountability / Closure
**Engine:** v58.91 (`app.py` and `QLA_Migration/app.py`)
**Override approved:** Warren, 2026-08-09 (fleet suppress); refinement 2026-08-11

---

## Business decision

Withhold policy fees from the load for **ISWL** and **UNKNOWN** (blank/missing
phase-1 `MPLAN`) only. Confirmed **non-ISWL** policies keep the existing #21C/#58
fee values and fee-inclusive `MMODEPREM`. Revisit ISWL fee treatment later.

## Classification (authoritative)

| Source | Rule |
|---|---|
| Runtime class | Phase-1 `quikridr.MPLAN` only (`MPHASE` 1/01) via `is_iswl_mplan()` |
| Not a class source | `quikmstr` (joined by normalized `MPOLICY` after class for `MMODEPREM` only) |
| Rider phases | Ignored; cannot override phase-1 class |
| Blank/missing phase-1 MPLAN | **UNKNOWN** — suppressed (safest); counted/listed; clean acceptance needs UNKNOWN=0 |

Baseline estimates (~2249 ISWL, ~2191 non-ISWL, ~$16323.81) are sanity checks only.

## Closed-issue override

| Issue | What it did | Status now |
|---|---|---|
| 21C | Mapped LifePRO `POLICY_FEE` into `quikridr.MANNLFEE` on the base coverage row | Suppressed for ISWL/UNKNOWN; active for non-ISWL |
| 58 | Derived modal fees from `MANNLFEE` × modal factors | Same as 21C |
| 89 | Fail-closed guard so a fee wipe cannot ship | Active: flag=0 fleet wipe; flag on = non-ISWL wipe still FATAL |

## Scope

**Non-ISWL:** no Issue 139 zeroing and no `MMODEPREM` subtraction — #21C/#58
outputs (including legitimate zeros) pass through unchanged.

**ISWL / UNKNOWN:** zero the five `quikridr` fee fields and subtract the
mode-appropriate fee from `quikmstr.MMODEPREM` using the existing guards
(zero premium / below-fee skip). No manual fee add.

**Flag:** `QLA_SUPPRESS_POLICY_FEES` default/on = mixed suppression; `=0`
disables Issue 139 for all and restores original full-fleet #89 guard.

## Implementation

| File | Change |
|---|---|
| `qla_core/modal_premium_factors.py` | Classifier gate + cohort stats/audit (`issue139_fee_class`) |
| `app.py`, `QLA_Migration/app.py` | v58.91; scoped #89 guard; cohort log line |
| `tools/validators/validate_issue58_quikridr_modal_fees.py` | Cohort-aware; no blanket SKIP |
| `tools/validators/validate_issue139_policy_fee_suppression.py` | Mixed-population controls |
| `tools/validators/validate_issue_log_accountability.py` | Non-ISWL fee assert + ISWL zero control |

## Validation result

Controlled full-batch validation passed on the 2026-07-31 source cut:
5,083 phase-1 policies; ISWL 2,268; non-ISWL 2,815; UNKNOWN 0;
non-ISWL fee-bearing rows restored 2,191; ISWL/UNKNOWN nonzero-fee exceptions 0.
The #58 focused validator, Issue 139 validator, #96/A7 regression, and #118
regression passed. Existing negative `MMODEPREM` records were unchanged.

Issue 139 remains pending G7 accountability and formal Closure; do not mark
Closed until the full Output gate passes.
