# Client Review Decision Template

**Date:** __________  
**Reviewer:** __________  
**Packet snapshot:** `PHASE26-CLIENT-BUSINESS-REVIEW-20260616T141135Z`

## Batch decisions (check one per queue)

### Unbalanced death claims (126)

- [ ] Batch **APPROVE_UAT** all 126
- [ ] Batch **EXCLUDE** all 126
- [ ] Batch **DEFER** past go-live
- [ ] Item-by-item review (attach annotated workbook)

### Surrender insufficient evidence (21)

- [ ] Batch **APPROVE_UAT** all 21
- [ ] Batch **EXCLUDE_LOAN_ACCOUNTING** all 21
- [ ] Batch **DEFER** past go-live
- [ ] Item-by-item review (attach annotated workbook)

## Item-specific notes (pre-filled examples)

| reconstructed_claim_id | policy_number | queue | decision | notes |
|---|---|---|---|---|
| RC-9011196134-1-DEATH_CLAIM-C0-20200314 | **9011196134** | Unbalanced | | Gap $147082.26; Large partial payout — benefit far exceeds recorded payout |
| RC-9010736035-1-DEATH_CLAIM-C0-20190613 | **9010736035** | Unbalanced | | Gap $134809.42; Large partial payout — second high-variance case |
| RC-9011217970-1-DEATH_CLAIM-C0-20190301 | **9011217970** | Unbalanced | | Gap $32046.60; Mid-size partial payout — typical multi-payee split |
| RC-9010776653-1-DEATH_CLAIM-C0-20190302 | **9010776653** | Unbalanced | | Gap $322.02; Smallest remaining variance — near tolerance |
| RC-9010771662-1-DEATH_CLAIM-C0-20220923 | **9010771662** | Unbalanced | | Gap $46125.62; Post-exclusion variance — clearing/payout timing distortion |
| RC-9010761882-1-DEATH_CLAIM-C0-20200722 | **9010761882** | Unbalanced | | Gap $20296.85; Post-exclusion variance — div-on-dep excluded but gap remains |
| RC-9010941103-1-DEATH_CLAIM-C0-20211018 | **9010941103** | Unbalanced | | Gap $45733.82; Funded claim with no payout rows in extract |
| RC-9010776027-2-SURRENDER_CLAIM-C0-20181227 | **9010776027** | Surrender (2 chains) | | 2 surrender chain(s); codes 0561 only — no approved payout evidence (1020/0560/0094/1900/0567) |
| RC-9010780411-2-SURRENDER_CLAIM-C0-20180205 | **9010780411** | Surrender (1 chains) | | 1 surrender chain(s); codes 0561 only — no approved payout evidence (1020/0560/0094/1900/0567) |
| RC-9010780591-3-SURRENDER_CLAIM-C0-20230209 | **9010780591** | Surrender (1 chains) | | 1 surrender chain(s); codes 0561 only — no approved payout evidence (1020/0560/0094/1900/0567) |
| RC-9011072813-2-SURRENDER_CLAIM-C0-20180624 | **9011072813** | Surrender (8 chains) | | 8 surrender chain(s); codes 0561 only — no approved payout evidence (1020/0560/0094/1900/0567) |
| RC-9011107796-3-SURRENDER_CLAIM-C0-20180317 | **9011107796** | Surrender (9 chains) | | 9 surrender chain(s); codes 0561 only — no approved payout evidence (1020/0560/0094/1900/0567) |
| | | | | |

## Sign-off

- [ ] Decisions recorded; authorized to apply in Phase 27
- [ ] No May re-validation required (per prior client guidance)
