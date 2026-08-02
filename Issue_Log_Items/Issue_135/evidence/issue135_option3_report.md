# Issue #135 — Option 3 Economic Reconstruction (Overlay)

Generated: 2026-08-02T20:20:28Z

## Decision

Warren approved **Option 3**: correct upstream accounting reconstruction, then derive both quikclmp payees and quikclms headers from corrected economic payments.

## Production safety

- Production Output mutated: **False**
- app.py wired: **False**
- MINTAMT remains 0: **True**
- Eric 459 gaps touched: **False**

## Narrowest upstream location

Economic over-count enters when reinstatement/endow (1015/6044) and intra-co (2019 / 1058000256) PACTG legs are treated as payout events before Phase 8–10 derive quikclmp/quikclms. Correct **economic events** first (policy/date/payee/amount/account), then set `MPAID = sum(corrected MAMOUNT)`. Do not patch only final MPAID.

## Counts

| Metric | Count |
|---|---:|
| AVAILABLE_MISMATCH deep-dive rows | 61 |
| CANDIDATE in | 45 |
| CORRECTED (overlay) | 43 |
| Candidate still HOLD | 2 |
| Prior Phase B HOLD (untouched) | 16 |
| Overlay quikclms rows | 43 |
| Overlay quikclmp rows | 51 |
| Promote stubs needing payee identity | 10 |
| Eric supply gaps (untouched) | 459 |

### Corrected by evidence class

| Class | Corrected |
|---|---:|
| MISSING_DEATH_MPAID_BUT_PACTG_PAYOUT | 5 |
| MULTIPLICITY_X2_DUPLICATE_OR_CLEARING | 17 |
| MULTIPLICITY_X3_REINSTATEMENT | 21 |

## Teacher cases

| Policy | Status | CSO | Corrected MPAID |
|---|---|---:|---:|
| 9011156098C | CORRECTED | 15000.0 | 15000.00 |
| 9010914301C | CORRECTED | 25019.98 | 25019.98 |
| 9010391359C | CORRECTED | 1260.06 | 1260.06 |

## Rules applied

| Rule | Meaning |
|---|---|
| `EXCLUDE_REVERSAL_DATE_REVERSED` | DATE_REVERSED blank/0 is NOT reversed |
| `EXCLUDE_REINSTATEMENT_ENDOW_LOOP` | 1058↔1015 / 6044 lifecycle excluded from economic payout |
| `EXCLUDE_INTRACO_UNAPPLIED_LOOP` | 2019 / 1058000256 re-payout excluded |
| `KEEP_ECONOMIC_DEATH_PAYOUT_2032_TO_1058` | Keep 2032→1058 (0094/0090) death cash legs |
| `DEDUP_SUBSET_MATCH_CSO_TOTAL_PAID` | Dedup/select payee subset summing to CSO Total_Paid |
| `PROMOTE_MISSING_DEATH_PAYOUT_FROM_PACTG` | Promote missing death payout only with PACTG+CSO proof |
| `HOLD_NO_CSO_MATCHING_SUBSET` / `HOLD_MISSING_NO_PACTG_CSO_MATCH` | Unresolved → HOLD |

## Remaining gate

Overlay proven on available CANDIDATE policies. Production quikclms/quikclmp amounts unchanged. Wire Option-3 filter upstream of Phase 10a/10b derivation (or controlled post-emit consume of overlay) only after user approval of production consume path + focused re-validation on full Output.

## Artifacts

- `candidate_summary`: `issue135_option3_candidate_summary.csv`
- `corrected_events`: `issue135_option3_corrected_events.csv`
- `quikclmp_overlay`: `issue135_option3_quikclmp_overlay.csv`
- `quikclms_overlay`: `issue135_option3_quikclms_overlay.csv`
- `hold_unresolved`: `issue135_option3_hold_unresolved.csv`
