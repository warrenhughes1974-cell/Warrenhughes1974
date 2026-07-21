# Rate Type Catalog

**Owner:** Actuarial / Product  
**Update frequency:** When a rate type is formally defined or approved for conversion

## Purpose

Formal catalog of Citizens rate types: business purpose, dimensions, basis, units, validation rules, QLAdmin destination, and approval status.

## Catalog Entry Template

For each rate type, capture:

| Attribute | Description |
|-----------|-------------|
| Rate-type code | Controlled code (e.g. `CASH_VALUE`, `GROSS_PREMIUM`) |
| Rate-type name | Display name |
| Business purpose | Why the rate exists |
| Applicable product types | Product families |
| Expected dimensions | Issue age, duration, sex, smoker, band, etc. |
| Rate basis | Per $1,000, per unit, absolute, etc. |
| Rate unit | Factor representation |
| Required precision | Decimal places / CHAR width |
| Percentage representation | How percents are stored |
| Destination table | QLAdmin factor/key table |
| Zero valid? | Y/N/Conditional |
| Blank valid? | Y/N/Conditional |
| Interpolation permitted? | Y/N |
| Multiple effective periods? | Y/N |
| Required validation | Checkpoint rules |
| Source authority | Link to SOURCE_AUTHORITY |
| Approval status | `UNKNOWN` / `PENDING REVIEW` / `APPROVED` |

## Rate Types (Framework — Not Approved)

| Code | Name | Approval Status | Source Authority Status |
|------|------|-----------------|------------------------|
| GROSS_PREMIUM | Gross Premium | PENDING REVIEW | PENDING REVIEW |
| CASH_VALUE | Cash Value | PENDING REVIEW | PENDING REVIEW |
| NET_PREMIUM | Net Premium | PENDING REVIEW | PENDING REVIEW |
| TERM_RESERVE | Terminal Reserve | PENDING REVIEW | PENDING REVIEW |
| MEAN_RESERVE | Mean Reserve | PENDING REVIEW | UNKNOWN |
| PAID_UP | Paid-Up Insurance | PENDING REVIEW | PENDING REVIEW |
| EXTENDED_TERM | Extended Term Insurance | UNKNOWN | UNKNOWN |
| DIVIDEND | Dividend | UNKNOWN | UNKNOWN |
| DIVIDEND_INTEREST | Dividend Interest | UNKNOWN | UNKNOWN |
| CREDITED_INTEREST | Credited Interest | UNKNOWN | UNKNOWN |
| GUARANTEED_INTEREST | Guaranteed Interest | UNKNOWN | UNKNOWN |
| CURRENT_INTEREST | Current Interest | UNKNOWN | UNKNOWN |
| LOAN_INTEREST | Loan Interest | PENDING REVIEW | PENDING REVIEW |
| COST_OF_INSURANCE | Cost of Insurance | UNKNOWN | UNKNOWN |
| EXPENSE_CHARGE | Expense Charge | UNKNOWN | UNKNOWN |
| POLICY_FEE | Policy Fee | PENDING REVIEW | PENDING REVIEW |
| PREMIUM_LOAD | Premium Load | UNKNOWN | UNKNOWN |
| SURRENDER_CHARGE | Surrender Charge | UNKNOWN | UNKNOWN |
| WITHDRAWAL_CHARGE | Withdrawal Charge | UNKNOWN | UNKNOWN |
| MODAL_FACTOR | Modal Factor | UNKNOWN | UNKNOWN |
| RIDER_PREMIUM | Rider Premium | UNKNOWN | UNKNOWN |
| PAID_UP_ADDITION | Paid-Up Addition Rate | UNKNOWN | UNKNOWN |
| REDUCED_PAID_UP | Reduced Paid-Up Value | UNKNOWN | UNKNOWN |
| GUIDELINE_PREMIUM | Guideline Premium | UNKNOWN | UNKNOWN |
| MEC_SEVEN_PAY | MEC / Seven-Pay Premium | UNKNOWN | UNKNOWN |
| TARGET_PREMIUM | Target Premium | UNKNOWN | UNKNOWN |
| MINIMUM_PREMIUM | Minimum Premium | UNKNOWN | UNKNOWN |
| MAXIMUM_PREMIUM | Maximum Premium | UNKNOWN | UNKNOWN |
| SETTLEMENT_FACTOR | Settlement Factor | UNKNOWN | UNKNOWN |
| OTHER | Other Actuarial Factor | UNKNOWN | UNKNOWN |

## Update Instructions

1. Promote a rate type to `APPROVED` only with actuarial sign-off and `DECISION_LOG` entry.
2. Never infer missing rate types or manufacture rate data to satisfy catalog completeness.
3. Cross-reference `manifests/rate_manifest.csv` for segment-level tracking.
