# Issue #166 — Resolution Summary

**Issue:** #166 — Div Accumulation Crediting
**Framework stage:** Closure Agent (G7)
**Final status:** **Closed**
**Engine version:** v59.13
**Closed date:** 2026-09-13
**Owner:** Conversion
**Accountability:** **IN_DATA** (issue validator PASS on full Output; `#166` registered in fleet accountability + `SMOKE_JOBS`)
**#21D override:** Warren Approved for Development 2026-09-13

---

## Resolution (issue log — paste-ready)

09/13/2026 Resolution: Dividend accumulation interest now uses the same plan rates as declared interest — 3.50% for ordinary residual plans, 2.00% for SAL OL/ML, and 4.50% for ISWL and 1668SP — and year-end interest-paid-to dates on balances move back to the prior anniversary so the statement can credit a full year. Examples: 9010728947C 3.50% paid-to 9/4/2025 deposit $1,875.38; 9010380808C 3.50% paid-to 12/1/2025; 9010824098C 4.50%; 901122D991C 2.00%.

> Copy the line above into tracking sheets and client readouts. Long-form detail follows.

---

## Problem Statement

Eric reported that policy 9010728947C was not crediting 3.50% on dividend accumulations. LifePRO showed interest of $65.63 (3.50% of $1,875.38) for a new total of $1,941.01. QLAdmin showed $50.44 and $1,925.82. He tied this to Closed #95.

---

## Root Cause

**Category:** [x] Scope gap

#95 already put 3.50% on `QuikUint` for plan `1960OL`. The annual statement uses `quikdvdp.MDEPINT` (Dividend Accum Int Rate), which Closed #21D left at **4.00%** for every non-ISWL policy. Interest Paid To was the last year-end PACTG 0641 date (12/31/2025), so QLAdmin accrued only a partial year. We do not emit the statement dollar; QLAdmin calculates it.

---

## Resolution

`MDEPINT` now follows the same #95 plan buckets on the policy table. Year-end `*1231` paid-to dates on deposit rows overlay to the prior policy anniversary so a full year can accrue. ISWL stays 4.50%. QuikUint was not rebuilt. Deposit $1,875.38 on the gold policy is unchanged.

### Files changed

| File | Change |
|---|---|
| `qla_core/mdepint_buckets.py` | Bucket + anniversary helpers |
| `app.py` / `QLA_Migration/app.py` | v59.13 emit hook |
| `tools/validators/validate_issue166_mdepint.py` | Fail-closed validator |
| `tools/validators/validate_release_closed_issues.py` | `SMOKE_JOBS` #166 |
| `tools/validators/validate_issue_log_accountability.py` | `#166` job |
| `tools/validators/validate_issue21d_mdepint.py` | Non-ISWL now #95 buckets |
| `Completed_Issues_Release_Validation_Guide.md` | Closed row + high-risk smoke |

### Engine changes

Surgical `quikdvdp` enrichment only. Version **v59.13**.

---

## Evidence

| Artifact | Path / result |
|---|---|
| Validation | `Issue_166_Validation_Report.md` — **PASS** |
| Regression | `Issue_166_Regression_Report.md` — **PASS** |
| Full Output validator | `python tools/validators/validate_issue166_mdepint.py` — **PASS** |
| Accountability | **#166 IN_DATA** (same validator job) |
| Test_Validation | `Output/Test_Validation/quikdvdp.csv` |
| Release smoke | `validate_release_closed_issues.py --smoke-only` includes **#166 quikdvdp MDEPINT buckets** |

### G7 gate

| Requirement | Status |
|---|---|
| Issue validator PASS on full Output | **PASS** |
| Accountability IN_DATA | **IN_DATA** |
| Test_Validation published | `quikdvdp.csv` |
| Guide row + high-risk smoke | **Yes** |
| SMOKE_JOBS registered | **Yes** |

---

## Trace Policy Confirmation

| Policy | Before | After | Match |
|---|---|---|---|
| 9010728947C | 4.00 / 20251231 / 1875.38 | 3.50 / 20250904 / 1875.38 | Yes |
| 9010380808C | 4.00 / 20251231 / 9220.33 | 3.50 / 20251201 / 9220.33 | Yes |
| 9010713704C | 4.50 | 4.50 | Yes |
| 9010824098C | 4.00 | 4.50 | Yes |
| 901122D991C | 4.00 | 2.00 | Yes |

---

## Explicitly not changed

- `rates/QuikUint.csv` / #95 smoke
- `ISWL_MPLAN_ALLOWLIST`
- Gold `MDEPOSIT` / `MINTYTD`
- `quikbenh` ledger
- Premium / MPOLICY padding

---

## Residual / follow-up

QLAdmin still calculates the statement interest dollar after load. Confirm on UAT reload that 9010728947C shows ~$65.63 / $1,941.01 as of the 9/4 anniversary.

---

## Rollback

1. Revert v59.13 `app.py` hooks and `mdepint_buckets.py`.
2. Restore `quikdvdp.csv` from `evidence/quikdvdp_pre_issue166.csv`.
3. Remove the #166 `SMOKE_JOBS` entry if rolling back the Closed row.

---

## Git release

Recorded after commit/push in this file’s footer.
