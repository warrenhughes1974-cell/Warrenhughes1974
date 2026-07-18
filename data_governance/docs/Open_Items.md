# QLAdmin Data Governance — Open Items

Tracked future work for the governance framework.  
**Do not implement items listed here until explicitly approved for development.**

---

## Future Data Governance Item — QuikChrt Chart of Accounts Integrity

| Field | Value |
|-------|--------|
| Status | **Not implemented** — documentation only |
| Proposed governance item ID | `DG-QUIKCHRT` (tentative) |
| Proposed item name | QuikChrt Chart of Accounts Integrity |
| Related current item | `DG-ACCOUNTING` (QuikActg) — **separate**; do not fold into Item 3 |

### Why this stays separate from QuikActg

| Table | Business purpose | Uniqueness focus |
|-------|------------------|------------------|
| **QuikActg** | Accounting *assignments* (plan/event config) | Verified composite key **MCOMP + MPLAN** (DG-QUIKACTG-001) |
| **QuikChrt** | Chart of *accounts* master | Company code + account number (proposed DG-QUIKCHRT-001) |

These are different business purposes and must not be combined into one governance item.

### Proposed rule: DG-QUIKCHRT-001

| Field | Value |
|-------|--------|
| Rule ID | `DG-QUIKCHRT-001` |
| Business name | Company and Account Number Combination Must Be Unique |
| Severity | Critical (proposed) |

**Business rule (supplied):**

A company may have multiple account numbers, and the same account number may exist for different companies. However, the same normalized company-code and account-number combination must not appear more than once in QuikChrt.

**Valid examples (conceptual):**

- Company A / Account 1000, Company A / Account 2000 — valid  
- Company A / Account 1000, Company B / Account 1000 — valid  

**Invalid example (conceptual):**

- Company A / Account 1000 appearing twice — fail  

### Pre-implementation verification required

Before coding this rule, verify and document:

1. Actual QuikChrt physical field names (preliminary observation: `MCOMP` C(1), `MACCOUNT` C(10), `MDESCR` C(30) from CSO / docs samples — **re-confirm at implementation time**).  
2. Field types and lengths.  
3. QuikChrt index / key definition if present in the QLAdmin manual or repository.  
4. Documented relationship between QuikChrt and QuikActg (e.g. whether every QuikActg-assigned account must exist in QuikChrt — that would be a **separate** reference rule, not part of uniqueness alone).  

### Explicitly out of scope until approved

- Do not implement DG-QUIKCHRT-001 yet.  
- Do not add QuikChrt uniqueness into `DG-ACCOUNTING`.  
- Do not add QuikActg ↔ QuikChrt reference matching until that relationship is confirmed as its own rule.
