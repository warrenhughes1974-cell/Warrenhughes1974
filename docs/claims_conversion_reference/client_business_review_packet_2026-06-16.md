# Client Business Review Packet — Remaining Deferred Claims

**Prepared:** 2026-06-16  
**Rollback snapshot:** `PHASE26-CLIENT-BUSINESS-REVIEW-20260616T141135Z`  
**Context:** UAT DBF load and spot-checks passed (Phase 25). This packet covers populations still excluded from UAT pending client business decisions.

---

## Executive summary

| Queue | Count | Disposition needed |
|---|---:|---|
| Unbalanced death claims (post-rebalance) | 126 | Approve UAT / header-only / exclude |
| Surrender insufficient evidence | 21 | Approve pattern / exclude / reclassify |
| **Total client review** | **147** | |

### UAT already delivered (for reference)

- **2,114** QUIKCLMS / **1,709** QUIKCLMP emitted and loaded to UAT DBFs
- Client Items 14–19 applied (surrender triage, orphans, rebalance promotions, combined amounts, payee override)
- **155** additional death claims cleared via Phase 24 dividend-on-deposit rebalance

---

## Queue 1 — Unbalanced death claims (126)

These claims received the client-authorized `2023` / `603703R` dividend-on-deposit exclusion (Phase 24) but **remain outside balancing tolerance** after adjustment.

### Distortion patterns

- **PARTIAL_PAYOUT_MULTI_PAYEE_OR_INCOMPLETE:** 103
- **DIV_ON_DEP_EXCLUDED_STILL_VARIANCE:** 23

**Dominant pattern:** `PARTIAL_PAYOUT_MULTI_PAYEE_OR_INCOMPLETE` — payout total is less than reconstructed net benefit (typical multi-beneficiary split or incomplete payout chain).

### Client decision options (per claim or batch)

1. **APPROVE_UAT** — Accept variance; promote to UAT like Items 16.2/16.3 exemplars
2. **HEADER_ONLY** — Convert settled header with no financial history
3. **EXCLUDE** — Permanently exclude from claims conversion
4. **DEFER** — Keep out of scope for September go-live

### Representative policy examples — unbalanced death claims

Use these LifePRO policy numbers when validating in source accounting or QLAdmin.

| Policy | Claim # | Activity date | Pattern | Net benefit | Payout total | Div-on-dep excluded | Remaining gap | Codes |
|---|---|---|---|---:|---:|---:|---:|---|
| **9011196134** | CLM0004500 | 20200314 | Partial Payout Multi Payee Or Incomplete | $150000.00 | $76963.55 | $74045.81 | $147082.26 | 0038|0094|0530 |
| **9010736035** | CLM0000888 | 20190613 | Partial Payout Multi Payee Or Incomplete | $148656.00 | $81378.18 | $67531.60 | $134809.42 | 0038|0094|0530 |
| **9011217970** | CLM0005027 | 20190301 | Partial Payout Multi Payee Or Incomplete | $24000.00 | $7988.35 | $16034.95 | $32046.60 | 0038|0094|0530 |
| **9010776653** | CLM0001339 | 20190302 | Partial Payout Multi Payee Or Incomplete | $30803.41 | $30663.38 | $181.99 | $322.02 | 0038|0094|0530 |
| **9010771662** | CLM0001267 | 20220923 | Div On Dep Excluded Still Variance | $46012.47 | $46125.62 | $46238.77 | $46125.62 | 0038|0094|0530 |
| **9010761882** | CLM0001129 | 20200722 | Div On Dep Excluded Still Variance | $60000.00 | $60118.74 | $20415.59 | $20296.85 | 0038|0094|0530 |
| **9010941103** | CLM0003011 | 20211018 | Partial Payout Multi Payee Or Incomplete | $22866.91 | $0.00 | $22866.91 | $45733.82 | 0038|0530|0630 |

**How to read these:**
- **9011196134** / **9010736035** — large death benefits with payouts well below net (likely multi-beneficiary or incomplete payout chain in extract).
- **9011217970** — mid-size partial payout; benefit exceeds recorded payout after div-on-dep exclusion.
- **9010771662** — div-on-dep excluded but payout/clearing layers still do not tie out.
- **9010941103** — funded death claim with **$0** payout rows in LifePRO extract (header-only candidate?).
- **9010776653** — smallest remaining gap; closest to passing balance check.
Detail: `unbalanced_claims_review_workbook.csv` | Policy examples: `client_review_policy_examples_unbalanced.csv`

---

## Queue 2 — Surrender review (21)

Per client Item 14, 479 surrender items with approved payout evidence were cleared. These **21** items lack payout evidence codes (`1020`/`0560`/`0094`/`1900`/`0567`) in transaction history.

### Representative policies — surrender insufficient evidence

Five policies account for all **21** deferred surrender chains. Each shows code **0561** (partial surrender / total cash) but **no** approved payout evidence codes from Item 14.

| Policy | Chains in queue | Date range | Codes seen | Sample claim id |
|---|---:|---|---|---|
| **9010776027** | 2 | 20181227 – 20191227 | 0561 | `RC-9010776027-2-SURRENDER_CLAIM-C0-20181227` |
| **9010780411** | 1 | 20180205 | 0561 | `RC-9010780411-2-SURRENDER_CLAIM-C0-20180205` |
| **9010780591** | 1 | 20230209 | 0561 | `RC-9010780591-3-SURRENDER_CLAIM-C0-20230209` |
| **9011072813** | 8 | 20180624 – 20250624 | 0561 | `RC-9011072813-2-SURRENDER_CLAIM-C0-20180624` |
| **9011107796** | 9 | 20180317 – 20260317 | 0561 | `RC-9011107796-3-SURRENDER_CLAIM-C0-20180317` |

**Policy notes for client review:**
- **9011072813** — 8 annual surrender chains (2018–2025); recurring 0561-only activity.
- **9011107796** — 9 annual chains (2018–2026); same pattern.
- **9010776027** — 2 chains (2018, 2019).
- **9010780411**, **9010780591** — single-chain policies.

Full chain detail: `surrender_review_workbook.csv` (filter by `policy_number`).
### Client decision options

1. **APPROVE_UAT** — Client confirms true surrender despite missing codes in extract
2. **EXCLUDE_LOAN_ACCOUNTING** — Reclassify as loan activity (not QUIKCLMS)
3. **DEFER** — Keep out of September scope

Detail: `surrender_review_workbook.csv` | Policy summary: `client_review_policy_examples_surrender.csv`

---

## Artifacts in this folder

| File | Purpose |
|---|---|
| `combined_client_review_queue.csv` | Full 147-item review queue |
| `unbalanced_claims_review_workbook.csv` | 126 unbalanced death claims with financial detail |
| `surrender_review_workbook.csv` | 21 surrender items |
| `client_review_representative_examples.csv` | Top examples for client meeting |
| `client_review_policy_examples_unbalanced.csv` | Curated unbalanced policy examples with amounts |
| `client_review_policy_examples_surrender.csv` | Surrender policies with chain counts |
| `unbalanced_distortion_pattern_summary.csv` | Pattern counts |
| `client_review_decision_template.md` | Decision capture form |

**Safety:** `production_dbf_flag=N`. No production DBF changes from this packet.
