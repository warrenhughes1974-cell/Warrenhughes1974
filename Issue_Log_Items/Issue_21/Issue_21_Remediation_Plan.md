# Issue #21 — Remediation Plan & Client Clarification Package

> **Status:** Planning document only. The Issue #21 investigation (initial analysis, root cause assessment, screenshot validation, and confidence scoring) is substantially complete. **No code, mapping, configuration, source data, or remediation work has been performed or is proposed at an implementation level in this document.** Its purpose is to prepare for future remediation while ensuring no assumptions are made about business requirements or QLAdmin expectations.
>
> Companion documents: `Issue_21_Analysis_Draft.md` (working draft) and `Issue_21_Final_Analysis.md` (screenshot-validated technical findings).

---

# 1. Executive Summary

Issue #21 bundled together a number of data-quality observations the client raised after comparing seven sample policies in LifePRO against the same policies converted into QLAdmin. Our review — including a second pass that examined the actual screenshots, not just the written notes — confirms that this is **not one problem but a group of distinct items** with different causes and different owners. They fall into four clearly separated groups.

### Confirmed Conversion Mapping Issues
*(Items where the conversion process is producing a value that does not match the source, and the cause sits within our control.)*

- **Non-Forfeiture and Dividend Options** are showing as a default/blank value instead of the option recorded in LifePRO (e.g., ETI, RPU, APL ETI).
- **Bill Day** is being derived from the policy's original issue date rather than the policy's actual billing day.
- **Policy Fee** is showing as zero even though the source policy carries a fee.
- **Beneficiary information** is showing a single default percentage and an "Unknown" label, even when the correct name is present.
- **Modal premium amounts** (semi-annual, quarterly, monthly) are being calculated using generic factors rather than product-specific factors.
- **Paid-Up Additions amounts** are losing their cents (rounding to the whole dollar).

### Confirmed Source Extract Issues
*(Items where the data we received from the source system is itself incomplete; these cannot be corrected by changing the conversion process.)*

- **Bank routing numbers** are arriving one digit short (eight digits instead of nine) and therefore cannot be completed downstream.
- **Premium / payment history** appears to have been provided only from a recent cut-off point forward, so older history is not available to convert.

### Business Decision / Clarification Items
*(Items where the correct outcome depends on a business answer before any work should begin.)*

- **Cash Value** — converted values are missing or do not match LifePRO. We need to know whether QLAdmin should carry the existing value or calculate its own.
- **Interest Crediting Rate** — the rate in QLAdmin differs from the rate the client expects; we need the authoritative rate.
- **Total Premium Paid / Cost Basis** — present in LifePRO; we need to know where and how it should appear in QLAdmin.
- **Last Change Date** — differs between the two systems; we need to know whether the LifePRO date should be preserved or whether QLAdmin is expected to set its own.

### Scope Clarification Items
*(Items that may represent additional project scope rather than defects.)*

- **Policy Notes and ENS messages** are visible in LifePRO but are not currently part of the conversion. We need confirmation on whether they belong in scope.
- **Banking detail level** — beyond the routing-number issue, we need confirmation of how much banking information must be preserved and how accounts should be classified.

---

# 2. Recommended Issue Breakdown

We recommend Issue #21 be split into the following individually tracked items so each can be owned, prioritized, and closed independently.

### 21A — NFO / Dividend Options
- **Description:** The Non-Forfeiture Option and Dividend Option are displaying a default/blank value in QLAdmin instead of the option held in LifePRO.
- **Current Status:** Confirmed by screenshots. High confidence on the discrepancy; cause understood at a planning level.
- **Risk Level:** Medium.
- **Business Impact:** Affects how a policy behaves if premiums stop and how dividends are applied — important for accurate policy administration.
- **Recommended Next Action:** Confirm with the client how combined options (e.g., "APL ETI") should be represented, then schedule for remediation.

### 21B — Bill Day
- **Description:** The billing day shown in QLAdmin reflects the policy's issue date rather than its actual billing day.
- **Current Status:** Confirmed by screenshots (clearly reproducible on two policies). High confidence.
- **Risk Level:** Low.
- **Business Impact:** Affects billing/draft timing accuracy.
- **Recommended Next Action:** Approve for remediation; this is the most isolated and lowest-risk item.

### 21C — Policy Fees
- **Description:** Annual policy fees show as zero in QLAdmin despite being present in LifePRO.
- **Current Status:** Confirmed by screenshots. High confidence.
- **Risk Level:** Medium.
- **Business Impact:** Affects premium accuracy and policyholder billing.
- **Recommended Next Action:** Confirm where policy fees should appear in QLAdmin, then schedule remediation.

### 21D — Interest Crediting Rate
- **Description:** The interest rate in QLAdmin (4.00%) differs from the rate the client expects (4.50%).
- **Current Status:** QLAdmin value confirmed by screenshot; the expected rate is based on the client's note only (no source screenshot available). Medium confidence on cause.
- **Risk Level:** High.
- **Business Impact:** Influences interest calculations and may affect cash value results.
- **Recommended Next Action:** Obtain the authoritative crediting rate from the client; treat jointly with Cash Value.

### 21E — Cash Value
- **Description:** Cash/fund values are missing (zero) on some policies and incorrect (non-zero but wrong) on another.
- **Current Status:** Discrepancy confirmed by screenshots (including two policies with substantial LifePRO fund values). Root cause open. High confidence on the defect; medium on cause.
- **Risk Level:** High.
- **Business Impact:** Cash value is highly visible to policyholders and central to policy value reporting.
- **Recommended Next Action:** Obtain the client's "source of truth" decision (load vs. calculate) before any work.

### 21F — Premium History
- **Description:** Only recent premium history appears in QLAdmin; older history present in LifePRO is not available.
- **Current Status:** Confirmed by screenshots; appears to originate from the data provided rather than the conversion. High confidence.
- **Risk Level:** Medium.
- **Business Impact:** Affects completeness of historical reporting.
- **Recommended Next Action:** Confirm required history depth; if full history is required, request an updated data extract.

### 21G — Total Premium Paid / Cost Basis
- **Description:** Cumulative premium and cost basis exist in LifePRO but do not have a confirmed home in QLAdmin.
- **Current Status:** Source values confirmed by screenshots; target location undefined. Medium-high confidence.
- **Risk Level:** Medium.
- **Business Impact:** Important for tax basis and policyholder value reporting.
- **Recommended Next Action:** Confirm the expected QLAdmin location and validation criteria.

### 21H — Banking Information
- **Description:** Bank routing numbers arrive one digit short; in at least one case the account is classified as a credit card rather than a bank account; in another, banking is missing entirely.
- **Current Status:** Confirmed by screenshots. The short routing number originates in the source data. High confidence.
- **Risk Level:** High.
- **Business Impact:** Directly affects automatic payment/draft processing.
- **Recommended Next Action:** Request a corrected (full-length) banking extract and confirm required banking detail and account classification rules.

### 21I — Beneficiary Information
- **Description:** Beneficiary entries default to 100% and an "Unknown" label even when the correct name is present; duplicate "primary" entries were reported.
- **Current Status:** Confirmed by screenshot on one policy ("Unknown 100%"); duplicate-primary pattern reported but not directly imaged. High confidence.
- **Risk Level:** Medium-High.
- **Business Impact:** Beneficiary accuracy is critical for claims and payout integrity.
- **Recommended Next Action:** Confirm which beneficiary attributes are mandatory for validation, then schedule remediation.

### 21J — Modal Premium Factors
- **Description:** Premium amounts for non-annual modes are calculated with generic factors, producing amounts that differ from expected.
- **Current Status:** Incorrect amounts confirmed by screenshots; the exact corrective factors are from the client's note. High confidence on the defect.
- **Risk Level:** Medium.
- **Business Impact:** Affects displayed/charged premium amounts by mode.
- **Recommended Next Action:** Obtain the approved product-specific mode factors from the client.

### 21K — PUA Amount Precision
- **Description:** Paid-Up Additions amounts lose their cents in QLAdmin (e.g., $5,752.96 shown as $5,752.00).
- **Current Status:** Confirmed by screenshots on both systems. High confidence.
- **Risk Level:** Low-Medium.
- **Business Impact:** Small per-policy dollar differences that affect value accuracy.
- **Recommended Next Action:** Approve for remediation; isolated and low risk.

### 21L — Last Change Date
- **Description:** The Last Change Date differs between LifePRO and QLAdmin; QLAdmin appears to show the issue date in some cases.
- **Current Status:** Difference confirmed by screenshots; mapping appears inconsistent. Medium-high confidence.
- **Risk Level:** Low.
- **Business Impact:** Affects audit/history accuracy; may be cosmetic depending on business intent.
- **Recommended Next Action:** Confirm whether this date should be preserved from LifePRO or set by QLAdmin.

### 21M — Policy Notes / ENS Messages
- **Description:** Policy notes and ENS messages exist in LifePRO but are not currently converted.
- **Current Status:** Referenced in the client's notes; not currently in project scope. Medium confidence (scope question).
- **Risk Level:** Low.
- **Business Impact:** Loss of contextual/administrative history if not included.
- **Recommended Next Action:** Confirm whether these are in scope for this release.

---

# 3. Development Readiness Assessment

*(No implementation details — readiness classification only.)*

| Item | Ready for Development | Requires Client Decision | Requires Additional Analysis | Requires Source Re-Extract |
|---|:---:|:---:|:---:|:---:|
| 21A — NFO / Dividend Options | After 21A question answered | ✓ (combined-option meaning) | — | — |
| 21B — Bill Day | ✓ | — | — | — |
| 21C — Policy Fees | — | ✓ (display location) | — | — |
| 21D — Interest Crediting Rate | — | ✓ (authoritative rate) | ✓ (joint with 21E) | — |
| 21E — Cash Value | — | ✓ (load vs. calculate) | ✓ | — |
| 21F — Premium History | — | ✓ (required depth) | — | ✓ (if full history needed) |
| 21G — Total Premium / Cost Basis | — | ✓ (target location) | ✓ | — |
| 21H — Banking Information | Partial (classification) | ✓ (detail & classification) | — | ✓ (full-length routing) |
| 21I — Beneficiary Information | After 21I question answered | ✓ (required attributes) | Partial (duplicate pattern) | — |
| 21J — Modal Premium Factors | — | ✓ (approved factors) | — | — |
| 21K — PUA Amount Precision | ✓ | — | — | — |
| 21L — Last Change Date | — | ✓ (preserve vs. system-set) | — | — |
| 21M — Policy Notes / ENS | — | ✓ (scope inclusion) | — | — |

**Ready for development after approval (no further input needed):** 21B, 21K.
**Ready once a single client answer is received:** 21A, 21C, 21I, 21J, 21L, 21M.
**Requires a business decision plus joint analysis:** 21D, 21E, 21G.
**Requires updated data from the source system:** 21F, 21H.

---

# 4. Client Clarification Questions

*Written for business users and validation staff. Each item describes the business question in plain language.*

### Cash Value

**Question:**
For policies that accumulate value over time, should the converted cash value be brought into QLAdmin exactly as it exists today, or should QLAdmin calculate the value after conversion using its own calculation methods?

**Why We Are Asking:**
We found examples where the value shown in LifePRO differs from the value shown in QLAdmin. Before determining the correct solution, we need to understand which system should be considered the source of truth for these values.

**Impact of the Answer:**
This determines whether the project should focus on loading existing values or validating QLAdmin-generated values.

### Interest Crediting Rate

**Question:**
What should be considered the authoritative interest crediting rate for these policies during validation?

**Why We Are Asking:**
The validation examples indicate a difference between the rate expected by the client and the rate currently shown in QLAdmin.

**Impact of the Answer:**
This affects interest-related calculations and may influence cash value results.

### Total Premium Paid / Cost Basis

**Question:**
Where would you expect Total Premium Paid and Cost Basis information to appear within QLAdmin?

**Why We Are Asking:**
The information exists in LifePRO, but we need confirmation regarding how it should be represented and validated after conversion.

**Impact of the Answer:**
This determines whether additional conversion work is required and what validation criteria should be used.

### Policy Fee

**Question:**
How should annual policy fees be displayed and maintained within QLAdmin?

**Why We Are Asking:**
Policy fees are visible in LifePRO but are not currently appearing during validation.

**Impact of the Answer:**
This determines the expected target location and validation approach.

### Premium History

**Question:**
For conversion validation purposes, how much historical premium activity should be available in QLAdmin?

**Why We Are Asking:**
The validation examples suggest that only a portion of the historical premium activity may currently be available.

**Impact of the Answer:**
This determines whether additional historical data needs to be included.

### Banking Information

**Question:**
What banking information is required for successful validation and ongoing administration after conversion?

**Why We Are Asking:**
Some banking-related values appear incomplete or differently classified than expected.

**Impact of the Answer:**
This determines the level of banking detail that must be preserved.

### Beneficiary Information

**Question:**
What beneficiary information is considered critical for validation (percentages, beneficiary type, relationships, ordering, etc.)?

**Why We Are Asking:**
We found examples where beneficiary information appears incomplete or displayed differently than expected.

**Impact of the Answer:**
This helps define the required validation criteria.

### Modal Premium Factors

**Question:**
Are there approved premium mode factors that should be used for these products?

**Why We Are Asking:**
Several examples indicate differences between expected and displayed modal premium amounts.

**Impact of the Answer:**
This will determine how premium amounts should be validated.

### Last Change Date

**Question:**
Should the Last Change Date be preserved from LifePRO, or is it expected that QLAdmin will establish its own date after conversion?

**Why We Are Asking:**
Validation examples show differences between the two systems.

**Impact of the Answer:**
This determines whether the difference represents a defect or expected system behavior.

### Policy Notes / ENS Messages

**Question:**
Should policy notes and ENS messages be included in the scope of this conversion project?

**Why We Are Asking:**
Several examples reference notes and messages that are visible in LifePRO but are not currently available in QLAdmin.

**Impact of the Answer:**
This determines whether additional conversion scope is required.

---

# 5. Recommended Sequencing

### Phase 1 — Ready After Approval
*Lowest risk, fully understood, no outside input required.*
- **21B — Bill Day**
- **21K — PUA Amount Precision**

### Phase 2 — Client Decision Required
*Each can move quickly once the relevant clarification question is answered.*
- **21A — NFO / Dividend Options** (combined-option meaning)
- **21C — Policy Fees** (display location)
- **21I — Beneficiary Information** (required attributes)
- **21J — Modal Premium Factors** (approved factors)
- **21L — Last Change Date** (preserve vs. system-set)
- **21D + 21E — Interest Crediting Rate & Cash Value** (treated together; authoritative rate + source-of-truth decision)
- **21G — Total Premium Paid / Cost Basis** (target location)

### Phase 3 — Source Extract Actions
*Cannot be resolved by the conversion process; requires corrected/expanded data from the source system.*
- **21H — Banking Information** (full-length routing numbers)
- **21F — Premium History** (full historical depth, if required)

### Phase 4 — Future Scope Considerations
*Potential additional scope, subject to client confirmation.*
- **21M — Policy Notes / ENS Messages**
- **21H (extended)** — additional banking detail and account-classification rules beyond the routing-number correction

---

# 6. Management Summary

**Prepared for:** project sponsors, business analysts, conversion managers, and client stakeholders.

**What was reviewed.**
The team conducted a full review of Issue #21 using nine client-supplied comparison packets covering seven sample policies. Beyond reading the written notes, we examined the **actual screenshots** from both systems to make sure every conclusion is supported by evidence rather than assumption.

**What was confirmed.**
The review confirmed that Issue #21 is a collection of **thirteen distinct items**, not a single defect. Several are clearly within the conversion team's control and are well understood — billing day, policy fees, non-forfeiture/dividend options, beneficiary display, modal premium amounts, and a rounding issue on paid-up additions. Two items originate in the **data provided by the source system** (shortened bank routing numbers and limited premium history) and cannot be fixed by adjusting the conversion alone. Two highly visible items — **cash value** and **interest crediting rate** — were confirmed as discrepancies, but their correct resolution depends on a business decision about which system should be considered authoritative.

**What requires client guidance.**
Nine plain-language clarification questions have been prepared (Section 4). The most important are the **cash value source-of-truth** decision and the **authoritative interest rate**, because they are linked and influence one another. Additional decisions are needed on policy-fee presentation, total premium/cost basis, beneficiary requirements, approved premium mode factors, treatment of the Last Change Date, required premium-history depth, banking detail, and whether policy notes/ENS messages are in scope.

**What can proceed immediately.**
Two items — **Bill Day** and **PUA amount precision** — are low-risk, fully understood, and ready to schedule as soon as remediation work is approved. A further group can begin as soon as a single clarification answer is received for each.

**What should be deferred until business decisions are made.**
Cash value, interest rate, and total premium/cost basis should **not** be worked until the client confirms the expected behavior, because acting early risks building to the wrong target. The two source-data items should be raised with the source-extract team in parallel, as they sit outside the conversion process.

**Recommended next step.**
Circulate the Section 4 clarification questions to the client, confirm the Phase 1 items for scheduling, and hold Phases 2–4 pending the responses. No development, configuration, mapping, or data changes should begin until these answers are received and approved.

---

*This is a business-ready planning document. No code, configuration, mapping, value-translation, source-extract, or remediation changes have been made or proposed at an implementation level. All technical detail supporting these conclusions is retained in `Issue_21_Final_Analysis.md`.*
