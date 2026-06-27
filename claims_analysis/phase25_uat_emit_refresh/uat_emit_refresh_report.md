# Phase 25 — UAT Emit Refresh Report

**Run date:** 2026-06-12
**Rollback snapshot:** `PHASE25-UAT-EMIT-REFRESH-20260612T130309Z`

## Population sources

- Claims: `phase24_client_balancing_rerun/uat_candidate_quikclms_post_rebalance.csv` (5,965 UAT claims)
- Payments: `phase24_client_balancing_rerun/uat_candidate_quikclmp_post_rebalance.csv` (1,709 UAT payments)

## Emit results

| Table | Rows emitted | Output |
|---|---:|---|
| QUIKCLMS | 2114 | `C:\Users\warren\Documents\GitHub\Warrenhughes1974\QLA_Migration\Output\quikclms.csv` |
| QUIKCLMP | 1709 | `C:\Users\warren\Documents\GitHub\Warrenhughes1974\QLA_Migration\Output\quikclmp.csv` |

## Client overlays applied post-emit

- **Item 18** — combined claim amounts: 518 QUIKCLMS rows updated (NETDB/MPAID/MFACE)
- **Item 19** — payee override: 1 QUIKCLMP rows updated (`010807842C` → KENNETH WAYNE MATTHEW)

## Notes

- MPOLICY cross-table validation disabled (`QLA_VALIDATE_CLAIMS_MPOLICY=0`) because converted `quikmstr.csv` was not present in output.
- Phase 22 semantic governance hold remains active; pseudo surrender chains in baseline UAT are quarantined at emit.
- `production_dbf_flag=N` — no production DBFs generated.

Audit: `phase25_emit_audit.json`
