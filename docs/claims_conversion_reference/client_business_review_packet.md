# Client Business Review Packet — Remaining Deferred Claims

**Prepared:** 2026-06-12  
**Rollback snapshot:** `PHASE26-CLIENT-BUSINESS-REVIEW-20260612T183159Z`  
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

## Queue 1 — Unbalanced death claims ({len(unbal_df)})

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

Detail: `unbalanced_claims_review_workbook.csv`

---

## Queue 2 — Surrender review (21)

Per client Item 14, 479 surrender items with approved payout evidence were cleared. These **21** items lack payout evidence codes (`1020`/`0560`/`0094`/`1900`/`0567`) in transaction history.

### Client decision options

1. **APPROVE_UAT** — Client confirms true surrender despite missing codes in extract
2. **EXCLUDE_LOAN_ACCOUNTING** — Reclassify as loan activity (not QUIKCLMS)
3. **DEFER** — Keep out of September scope

Detail: `surrender_review_workbook.csv`

---

## Artifacts in this folder

| File | Purpose |
|---|---|
| `combined_client_review_queue.csv` | Full 147-item review queue |
| `unbalanced_claims_review_workbook.csv` | 126 unbalanced death claims with financial detail |
| `surrender_review_workbook.csv` | 21 surrender items |
| `client_review_representative_examples.csv` | Top examples for client meeting |
| `unbalanced_distortion_pattern_summary.csv` | Pattern counts |
| `client_review_decision_template.md` | Decision capture form |

**Safety:** `production_dbf_flag=N`. No production DBF changes from this packet.
