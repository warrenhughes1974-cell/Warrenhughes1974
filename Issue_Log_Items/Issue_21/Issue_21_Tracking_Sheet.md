# Issue #21 — Tracking Sheet

**Source policies:** 010391876C · 010391895C · 010448806C · 010713704C · 010718309C · 010765930C · 010818663C
**Last updated:** 2026-07-11 (21F closed v57.73)
**References:** `Issue_21_Final_Analysis.md` (technical) · `Issue_21_Remediation_Plan.md` (planning)

**Status legend:** `IMPLEMENTED` = change applied + validated in full batch · `CLOSED` = not a defect / out of scope · `AWAITING CLIENT` = blocked on a clarification answer · `IN SCOPE` = confirmed scope, new build

> **Implementation note (2026-06-21):** Three fixes **implemented and full-batch validated** (engine **v57.22**): **21B** Bill Day, **21C** Policy Fees, **21H** Banking ABA. **21L CLOSED.** **21K** reclassified (QLAdmin/DBF precision, not conversion). See roll-up and batch results below.

| ID | Item | Description (with example) | Phase | Risk | Status | Owner |
|---|---|---|:---:|:---:|---|---|
| 21A | NFO / Dividend Options | NFO from LifePRO showed 0 in QLAdmin. Example: BF policies 010765930C / 010718309C / 010818663C had LifePRO code 1 (APL/ETI) but QLAdmin MNFOPT=0. | 2 | Med | **CLOSED ✓** | Conversion + Client |
| 21B | Bill Day | The day-of-month used for billing/draft was taken from the **issue date** instead of the policy's specified bill day. **Example:** Policy 010713704C — LifePRO Specified Bill Day = **15**, but QLAdmin showed Bill Day = **19** (the day from issue date 04/19/1984). **Fix applied:** map `POLICY_BILL_DAY → MBILLDAY`. Full-batch: 713704C→15, 765930C→28, 718309C→22, 818663C→12. | 1 | Low | **IMPLEMENTED ✓** | Conversion |
| 21C | Policy Fees | Annual policy fee from LifePRO was missing in QLAdmin (showed **$0**). **Example:** Policy 010391876C — LifePRO Policy Fee = **$10.44**; QLAdmin showed **Pol Fee 0.0000**. Policy 010713704C — LifePRO fee **$25.00**. **Fix applied:** populate `MANNLFEE` on the base-coverage rider row from policy-master `POLICY_FEE`. Full-batch: 4,459 base rows fee'd; 391876C→10.44, 713704C→25.00. | 2 | Med | **IMPLEMENTED ✓** | Conversion |
| 21D | Interest Crediting Rate | QLAdmin shows a different interest crediting rate than the client expects. **Example:** QLAdmin policy 010713704C shows Dividend Accum Int Rate = **4.00%**; client expects **4.50%**. | 2 | High | **DECIDED ✓** (v57.36) | Conversion |
| 21E | Cash Value | Cash values in QLAdmin do not match LifePRO fund/policy values — some show **$0**, others show a wrong non-zero amount. **Example:** UL policy 010713704C — LifePRO Fund Value ≈ **$45,551.94**; QLAdmin Cash Value = **$0.00**. | 2 | High | **DECIDED ✓** (v57.63 UL load; traditional via QuikCvs) | Conversion |
| 21F | Premium History | Premium payment history in QLAdmin is truncated — only recent payments appear, not the full LifePRO accounting history. **Remedy:** Conversion Adjustment `quikprmh` row (non-ISWL) @ 12/31/2017. | 3 | Med | **CLOSED ✓** (v57.73) | Conversion |
| 21G | Total Premium / Cost Basis | LifePRO carries Total Premiums Paid and Tax/Cost Basis, but QLAdmin does not show equivalent totals. **Example:** Policy 010448806C — LifePRO shows Premiums Paid = **$6,552.00** and Tax Basis = **$2,483.97**. | 2 | Med | **CLOSED ✓** (not required in QL — New Era) | Conversion + Client |
| 21H | Banking Information | Bank routing (ABA) and account information is wrong or missing in QLAdmin. **Example:** Policy 010713704C — LifePRO shows Checking Actual Draft, ABA **104000016**, account **47374579**, First National Bank of Omaha; QLAdmin showed **8-digit ABA 10400001** in the **"Credit Card ID"** field (wrong field + truncated routing). **ABA fix applied:** full 9-digit routing recovered from PPCOM (1,712 of 1,996 banked policies). **Still open:** which QLAdmin field should hold the bank account, and bank-name mapping. | 3 | High | **IMPLEMENTED (ABA) ✓** / AWAITING CLIENT (target field) | Conversion + Client |
| 21I | Beneficiary Information | Beneficiary name, type, relationship, or split percentage is wrong or defaulted in QLAdmin. **Example:** Policy 010818663C — QLAdmin shows beneficiary type **"Unknown"** at **100%**, then lists the correct name (PROCTOR, JACKI) separately. Client also reported duplicate "Beneficiary 1" rows on 010391876C. | 2 | Med-High | **DECIDED ✓** (type/split fixed v57.29; MRELATION=1000 intentional) | Conversion |
| 21J | Modal Premium Factors | Modal premium amounts (monthly, quarterly, draft) do not match LifePRO — QLAdmin appears to use generic factors instead of product-specific ones. **Example:** Policy 010713704C — QLAdmin Annl **$1,095.44** / Mthly **$91.29** / Draft **$43.91**; monthly looks like Annl÷12 rather than the product's actual modal factor. | 2 | Med | **CLOSED ✓** | **Released v57.46** — per-plan factors + PAC GL85 overrides + fleet memos |
| 21K | PUA Amount Precision | Paid-Up Addition (PUA) face amount loses cents when loaded into QLAdmin. **Example:** Policy 010448806C — LifePRO Accumulated PUA Face = **$5,752.96**; QLAdmin shows **$5,752.00**. Conversion output already carries full unit precision (`MUNIT` = 5.75296); the loss appears to occur in QLAdmin/DBF field storage (~3 decimal places). | 1 | Low-Med | AWAITING CLIENT (New Era) | Conversion + Client (New Era) |
| 21L | Last Change Date | Client reported Last Change Date in QLAdmin did not match LifePRO. **Example:** LifePRO 010448806C Last Change Date = **07/07/2010**; QLAdmin showed the issue date instead. **Closed:** client confirmed QLAdmin sets this date on load — not pulled from LifePRO. | — | Low | **CLOSED** | Client |
| 21M | Policy Notes / ENS Messages | Policy notes and ENS messages from LifePRO are not converted to QLAdmin. **Released v57.34:** greenfield QUIKMEMO pipeline; 4,380 rows; client UAT pending on 010335038C. | 4 | Low | **RELEASED ✓** (UAT pending) | Conversion + Client |

---

| ID | Status | Resolution |
|---|---|---|
| **21A** | **CLOSED ✓** | **Resolution:** PPBENTYP cache reads BF_NON_FORFEITURE for ISWL/BF; NFO codes 1/2 → APL (MNFOPT=1) per SME (v57.47). |
| **21B** | IMPLEMENTED ✓ | **Resolution:** Map `POLICY_BILL_DAY → MBILLDAY` (v57.22). |
| **21C** | IMPLEMENTED ✓ | **Resolution:** Populate `MANNLFEE` on base rider from `POLICY_FEE` (v57.22). |
| **21J** | **CLOSED ✓** | **Resolution:** Per-plan modal factors from client mapping + PAC GL85 overrides + fleet memos (v57.46). |
| **21L** | CLOSED | **Resolution:** Not converted — QLAdmin sets Last Change Date on load. |

### Gating questions & next actions (open items)

| ID | Status | Question / next action |
|---|---|---|
| **21B** | IMPLEMENTED ✓ | **No client question — ready for UAT.** Please verify Bill Day on sample policies in QLAdmin (e.g., 010713704C should show **15**, not 19). |
| **21C** | IMPLEMENTED ✓ | **No client question — ready for UAT.** Please verify Policy Fee on the base-coverage rider screen (e.g., 010391876C = **$10.44**, 010713704C = **$25.00**). |
| **21D** | **DECIDED ✓** | **ISWL = 4.50% / non-ISWL = 4.00%** (v57.36 MDEPINT allowlist). See `Issue_21_Open_Items_Official_Decisions.md`. |
| **21E** | **DECIDED ✓** | **Traditional = compute via QuikCvs; UL = load FV_BALANCE2 → MCV0** (v57.63). Traditional CV quality still depends on rate tables (#40/#41). |
| **21F** | **CLOSED ✓** | **Resolution:** Non-ISWL Conversion Adjustment `quikprmh` row @ 12/31/2017 when LifePRO Base+PUA+SU+SL > history; ISWL excluded; negatives exception-only (v57.73). UAT: `Test_Validation/quikprmh.csv` + Reports. |
| **21G** | **CLOSED ✓** | **Resolution:** QLAdmin has no programmed cost basis / taxable-gain field for life policies and does not compute or withhold taxable gains on life surrenders; conversion will not load LifePRO Premiums Paid or Tax Basis into a QLAdmin master field — use premium history and/or the staged report for any manual estimate outside QL. |
| **21H** | IMPLEMENTED (ABA) ✓ / AWAITING CLIENT | **ABA (done):** verify 9-digit routing on banked policies (e.g., 010713704C = **104000016/47374579**). **Still need answer:** **Should checking/savings draft accounts appear in the Bill Acct / bank-account field instead of "Credit Card ID"?** What is the rule for classifying account type (Checking Actual Draft vs credit card)? How should bank name (e.g., First National Bank of Omaha) be mapped? Review **342 ambiguous accounts** in `reconciliation/issue21h_ambiguous_accounts.csv`. |
| **21I** | **DECIDED ✓** | **Type + split mandatory and already correct (v57.29).** `MRELATION=1000` intentional — RNA has no kinship field for B1/B2. |
| **21K** | AWAITING CLIENT (New Era) | **Does QUIKRIDR.MUNIT support 5 decimal places on DBF load, or is it truncated to 3?** If truncated, how should PUA face amounts with cents (e.g., $5,752.96) be carried — via a different field, rounding rule, or QLAdmin configuration change? |
| **21M** | RELEASED ✓ (v57.34) | **Client UAT pending.** Deploy `quikmemo_uat_dbf/quikmemo.dbf` + `.dbt` together. Verify Memo tab on **010335038C** (merged PNOTE segments). See `Issue_Log_Items/Issue_21M/Issue_21M_Release_Status_v57.34.md`. |

---

### Status roll-up (2026-06-27 — v57.34)

| Status | Count | Items |
|---|:---:|---|
| CLOSED | 5 | 21A, 21F, 21G, 21J, 21L |
| RELEASED (full-batch validated) | 4 | 21B, 21C, 21H (ABA), 21M |
| DECIDED (21D/E/I) | 3 | 21D, 21E, 21I — see Official Decisions (v57.63) |
| AWAITING CLIENT | 2 | 21K (New Era), + 21H target-field |

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
