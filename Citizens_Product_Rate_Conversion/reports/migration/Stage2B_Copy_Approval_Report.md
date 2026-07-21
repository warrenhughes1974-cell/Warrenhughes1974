# Stage 2B Copy Approval Report

**Generated:** 2026-07-12T14:56:36Z

## Summary

| Metric | Value |
|--------|------:|
| Total rows | 503 |
| Approved for copy (active) | 237 |
| Approved for archive | 138 |
| Approved for quarantine | 5 |
| Excluded | 123 |
| Review remains open | 0 |
| Blocked | 0 |
| Total approved bytes | 2,915,996,668 |
| Approved ZIP count | 21 |
| Approved ZIP bytes | 2,779,867,173 |
| Files about to copy | 380 |

## Sensitive Quarantine

- `docs/cifianu1.dbf` → `quarantine/sensitive_review/cifianu1.dbf`
- `extracted/AgentName.csv` → `quarantine/sensitive_review/AgentName.csv`

## Duplicate Canonical Selections

- **DUP-0001**: canonical=`N/A` — Dev/sample PDF duplicates; both EXCLUDE_GENERATED per 2B-05/2B-08
- **DUP-0002**: canonical=`source/CFIProposalMaker.zip` — source/ is canonical over root duplicate per 2B-03
- **DUP-0003**: canonical=`source/CFIProposalMakerRev2.mdb` — source/original/access canonical; extracted/ is working copy per 2B-03
- **DUP-0004**: canonical=`validation/cfic_issue03_p7mn_validation.csv` — validation/ folder canonical for validation evidence; Issue_Log copy to duplicate_review
- **DUP-0005**: canonical=`N/A` — Identical PT1 content; both archived with distinct paths (legacy SourceData structure)

## Blockers

None.
