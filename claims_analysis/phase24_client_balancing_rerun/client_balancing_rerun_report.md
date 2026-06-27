# Phase 24 — Client Balancing Re-run Report

**Run date:** 2026-06-12
**Rollback snapshot:** `PHASE24-CLIENT-BALANCING-RERUN-20260612T125815Z`
**Authority:** Client Item 16 — exclude `2023` / `603703R` dividend-on-deposit from DB balancing

## Results

| Metric | Count |
|---|---:|
| Rebalance queue | 281 |
| BALANCED after GL exclusion | 137 |
| MINOR_VARIANCE after GL exclusion | 18 |
| Still UNBALANCED | 126 |
| Promoted to UAT | 155 |
| Remaining deferred | 126 |

## UAT population

| Population | Phase 23 refreshed | Post-rebalance | Change |
|---|---:|---:|---:|
| UAT candidate claims | 5810 | **5965** | **+155** |
| UAT candidate payments | 1709 | 1709 | 0 |

## Exclusion mechanics

- Primary: PACTG `CREDIT_ACCOUNT` / `DEBIT_ACCOUNT` rows matching `2023` or `603703R` on claim activity window
- Fallback: lifecycle `0038` clearing total when no PACTG GL rows detected
- Source mix: `{'LIFECYCLE_0038_FALLBACK': 271, 'PACTG_GL_2023_603703R': 10}`

## Remaining risk

- 126 claims remain unbalanced after GL exclusion (partial payouts, multi-beneficiary splits, or non-dividend distortion).
- These stay in `rebalance_remaining_deferred.csv` for business review.

**Safety:** `production_dbf_flag=N`. No engine or `app.py` changes.
