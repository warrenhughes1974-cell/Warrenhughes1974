# Issue #21 — Tracking Sheet

**Source policies:** 010391876C · 010391895C · 010448806C · 010713704C · 010718309C · 010765930C · 010818663C
**Prepared:** 2026-06-19 · **Last updated:** 2026-06-27 (v57.34 release integration)
**References:** `Issue_21_Final_Analysis.md` (technical) · `Issue_21_Remediation_Plan.md` (planning)

**Status legend:** `IMPLEMENTED` = change applied + validated in full batch · `CLOSED` = not a defect / out of scope · `AWAITING CLIENT` = blocked on a clarification answer · `IN SCOPE` = confirmed scope, new build

> **Implementation note (2026-06-21):** Three fixes **implemented and full-batch validated** (engine **v57.22**): **21B** Bill Day, **21C** Policy Fees, **21H** Banking ABA. **21L CLOSED.** **21K** reclassified (QLAdmin/DBF precision, not conversion). See roll-up and batch results below.

| ID | Item | Description (with example) | Phase | Risk | Status | Owner |
|---|---|---|:---:|:---:|---|---|
| 21A | NFO / Dividend Options | Non-Forfeiture Option (NFO) and Dividend Option from LifePRO are not appearing correctly in QLAdmin — both show **0** instead of the real election. **Example:** LifePRO policy 010391895C shows NFO = **ETI** and Dividend Option = **4 (Purchase of PUA)**; QLAdmin shows **NFO 0** and **DIV 0**. Combined values like **APL ETI** also need a business rule. | 2 | Med | AWAITING CLIENT | Conversion + Client |
| 21B | Bill Day | The day-of-month used for billing/draft was taken from the **issue date** instead of the policy's specified bill day. **Example:** Policy 010713704C — LifePRO Specified Bill Day = **15**, but QLAdmin showed Bill Day = **19** (the day from issue date 04/19/1984). **Fix applied:** map `POLICY_BILL_DAY → MBILLDAY`. Full-batch: 713704C→15, 765930C→28, 718309C→22, 818663C→12. | 1 | Low | **IMPLEMENTED ✓** | Conversion |
| 21C | Policy Fees | Annual policy fee from LifePRO was missing in QLAdmin (showed **$0**). **Example:** Policy 010391876C — LifePRO Policy Fee = **$10.44**; QLAdmin showed **Pol Fee 0.0000**. Policy 010713704C — LifePRO fee **$25.00**. **Fix applied:** populate `MANNLFEE` on the base-coverage rider row from policy-master `POLICY_FEE`. Full-batch: 4,459 base rows fee'd; 391876C→10.44, 713704C→25.00. | 2 | Med | **IMPLEMENTED ✓** | Conversion |
| 21D | Interest Crediting Rate | QLAdmin shows a different interest crediting rate than the client expects. **Example:** QLAdmin policy 010713704C shows Dividend Accum Int Rate = **4.00%**; client expects **4.50%**. (The 4.50% rate was not visible on a LifePRO screenshot — needs business confirmation of the authoritative rate.) | 2 | High | AWAITING CLIENT | Client (with Conversion) |
| 21E | Cash Value | Cash values in QLAdmin do not match LifePRO fund/policy values — some show **$0**, others show a wrong non-zero amount. **Example:** UL policy 010713704C — LifePRO Fund Value = **$45,567.58**; QLAdmin Cash Value = **$0.00**. Policy 010818663C — LifePRO Fund Value = **$12,481.13**; QLAdmin = **$0.00**. Policy 010391895C shows a wrong non-zero **$7,204.30** instead of the expected value. | 2 | High | AWAITING CLIENT | Client (with Conversion) |
| 21F | Premium History | Premium payment history in QLAdmin is truncated — only recent payments appear, not the full LifePRO accounting history. **Example:** QLAdmin for 010713704C lists only **2026** payments; LifePRO accounting runs back to **2001/2002**. Client annotation suggests history may cut off around **Jan 2018**. | 3 | Med | AWAITING CLIENT | Client + Source-extract team |
| 21G | Total Premium / Cost Basis | LifePRO carries Total Premiums Paid and Tax/Cost Basis, but QLAdmin does not show equivalent totals. **Example:** Policy 010448806C — LifePRO shows Premiums Paid = **$6,552.00** and Tax Basis = **$2,483.97**; no matching totals appear on the QLAdmin screens reviewed. | 2 | Med | AWAITING CLIENT | Client (with Conversion) |
| 21H | Banking Information | Bank routing (ABA) and account information is wrong or missing in QLAdmin. **Example:** Policy 010713704C — LifePRO shows Checking Actual Draft, ABA **104000016**, account **47374579**, First National Bank of Omaha; QLAdmin showed **8-digit ABA 10400001** in the **"Credit Card ID"** field (wrong field + truncated routing). **ABA fix applied:** full 9-digit routing recovered from PPCOM (1,712 of 1,996 banked policies). **Still open:** which QLAdmin field should hold the bank account, and bank-name mapping. | 3 | High | **IMPLEMENTED (ABA) ✓** / AWAITING CLIENT (target field) | Conversion + Client |
| 21I | Beneficiary Information | Beneficiary name, type, relationship, or split percentage is wrong or defaulted in QLAdmin. **Example:** Policy 010818663C — QLAdmin shows beneficiary type **"Unknown"** at **100%**, then lists the correct name (PROCTOR, JACKI) separately. Client also reported duplicate "Beneficiary 1" rows on 010391876C. | 2 | Med-High | AWAITING CLIENT | Conversion + Client |
| 21J | Modal Premium Factors | Modal premium amounts (monthly, quarterly, draft) do not match LifePRO — QLAdmin appears to use generic factors instead of product-specific ones. **Example:** Policy 010713704C — QLAdmin Annl **$1,095.44** / Mthly **$91.29** / Draft **$43.91**; monthly looks like Annl÷12 rather than the product's actual modal factor. | 2 | Med | AWAITING CLIENT | Client (with Conversion) |
| 21K | PUA Amount Precision | Paid-Up Addition (PUA) face amount loses cents when loaded into QLAdmin. **Example:** Policy 010448806C — LifePRO Accumulated PUA Face = **$5,752.96**; QLAdmin shows **$5,752.00**. Conversion output already carries full unit precision (`MUNIT` = 5.75296); the loss appears to occur in QLAdmin/DBF field storage (~3 decimal places). | 1 | Low-Med | AWAITING CLIENT (New Era) | Conversion + Client (New Era) |
| 21L | Last Change Date | Client reported Last Change Date in QLAdmin did not match LifePRO. **Example:** LifePRO 010448806C Last Change Date = **07/07/2010**; QLAdmin showed the issue date instead. **Closed:** client confirmed QLAdmin sets this date on load — not pulled from LifePRO. | — | Low | **CLOSED** | Client |
| 21M | Policy Notes / ENS Messages | Policy notes and ENS messages from LifePRO are not converted to QLAdmin. **Released v57.34:** greenfield QUIKMEMO pipeline; 4,380 rows; client UAT pending on 010335038C. | 4 | Low | **RELEASED ✓** (UAT pending) | Conversion + Client |

---

### Gating questions & next actions

Clear questions for each open item. Implemented/closed items show verification steps instead.

| ID | Status | Question / next action |
|---|---|---|
| **21A** | AWAITING CLIENT | **What should QLAdmin display when LifePRO shows a combined NFO value such as "APL ETI"?** Should it map to a single QLAdmin code, split across fields, or use a specific translation table entry? Please provide the approved mapping for ETI, RPU, APL ETI, and Dividend Option values. |
| **21B** | IMPLEMENTED ✓ | **No client question — ready for UAT.** Please verify Bill Day on sample policies in QLAdmin (e.g., 010713704C should show **15**, not 19). |
| **21C** | IMPLEMENTED ✓ | **No client question — ready for UAT.** Please verify Policy Fee on the base-coverage rider screen (e.g., 010391876C = **$10.44**, 010713704C = **$25.00**). |
| **21D** | AWAITING CLIENT | **What is the authoritative interest crediting rate for converted policies — 4.00% or 4.50%?** Should QLAdmin display the guaranteed rate, the current credited rate, or both? If 4.50%, where in LifePRO is that rate stored for policy 010713704C? |
| **21E** | AWAITING CLIENT | **Should QLAdmin load the existing LifePRO cash/fund value at conversion, or should QLAdmin calculate cash values from rate tables after load?** For UL policies like 010713704C ($45,567.58 fund value), do you expect the converted value to match LifePRO exactly on day one? |
| **21F** | AWAITING CLIENT | **How far back must premium payment history be converted?** (Full history back to issue? To a specific date such as Jan 2018? Through paid-to date only?) This determines whether we need a fuller LifePRO accounting re-extract. |
| **21G** | AWAITING CLIENT | **Where should Total Premium Paid and Cost/Tax Basis appear in QLAdmin?** Please identify the target screen and field name(s), or confirm if these are informational-only and not required at conversion. |
| **21H** | IMPLEMENTED (ABA) ✓ / AWAITING CLIENT | **ABA (done):** verify 9-digit routing on banked policies (e.g., 010713704C = **104000016/47374579**). **Still need answer:** **Should checking/savings draft accounts appear in the Bill Acct / bank-account field instead of "Credit Card ID"?** What is the rule for classifying account type (Checking Actual Draft vs credit card)? How should bank name (e.g., First National Bank of Omaha) be mapped? Review **342 ambiguous accounts** in `reconciliation/issue21h_ambiguous_accounts.csv`. |
| **21I** | AWAITING CLIENT | **Which beneficiary attributes are mandatory at conversion — name, type, relationship, split %, and primary/contingent designation?** For policy 010818663C, should "Unknown 100%" ever appear, or must every beneficiary have a valid type before load? |
| **21J** | AWAITING CLIENT | **Please provide the approved modal premium factors by product/plan** (or confirm QLAdmin should use plan-specific factors from QuikPlan rather than Annl÷12). Which modal breakdown is authoritative for policy 010713704C — LifePRO draft amount ($43.91) or the QLAdmin-calculated monthly ($91.29)? |
| **21K** | AWAITING CLIENT (New Era) | **Does QUIKRIDR.MUNIT support 5 decimal places on DBF load, or is it truncated to 3?** If truncated, how should PUA face amounts with cents (e.g., $5,752.96) be carried — via a different field, rounding rule, or QLAdmin configuration change? |
| **21L** | CLOSED | **No action required.** QLAdmin sets Last Change Date on load; LifePRO last-change is not converted. |
| **21M** | RELEASED ✓ (v57.34) | **Client UAT pending.** Deploy `quikmemo_uat_dbf/quikmemo.dbf` + `.dbt` together. Verify Memo tab on **010335038C** (merged PNOTE segments). See `Issue_Log_Items/Issue_21M/Issue_21M_Release_Status_v57.34.md`. |

---

### Status roll-up (2026-06-27 — v57.34)

| Status | Count | Items |
|---|:---:|---|
| RELEASED (full-batch validated) | 4 | 21B, 21C, 21H (ABA), 21M |
| CLOSED (not a defect) | 1 | 21L |
| AWAITING CLIENT | 8 | 21A, 21D, 21E, 21F, 21G, 21I, 21J, 21K (New Era), + 21H target-field |

### Changes applied (v57.34 release)

| Item | File(s) changed | Version |
|---|---|---|
| 21B Bill Day | `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv` | v57.22 |
| 21C Policy Fees | `app.py` (root + `QLA_Migration/app.py`) | v57.22 |
| 21H Banking ABA | `app.py` + `aba_routing_lookup.csv` | v57.22 |
| 21M QUIKMEMO | `qla_core/quikmemo_converter.py`, `quikmemo_dbf_generator.py` | v57.32–34 |
| 21M-FU merge | `qla_core/quikmemo_converter.py` | **v57.34** |
| #25 MPOLICY | `qla_core/normalize_utils.py` | v57.30 |
| #26 MPREM | rulebook + `app.py` | v57.31 |

### Full batch run (2026-06-21)

- **Duration:** ~14.5 min · **Exit code:** 0 · **Engine:** v57.22
- **Log:** `QLA_Migration/Output/_full_batch_test_log.txt`
- **21B/21C/21H confirmed** in `QLA_Migration/Output/quikmstr.csv` and `quikridr.csv`

### Ready for QLAdmin UAT load testing (v57.34)
- **21B** — Bill Day on sample policies
- **21C** — Policy Fee on base-coverage rider row
- **21H** — 9-digit ABA on banked policies (target-field placement still pending client answer)
- **21M / 21M-FU** — QUIKMEMO deploy from `Output/quikmemo_uat_dbf/`; verify Memo tab on **010335038C**

*Tracking artifact. Last release: v57.34 (2026-06-27).*
