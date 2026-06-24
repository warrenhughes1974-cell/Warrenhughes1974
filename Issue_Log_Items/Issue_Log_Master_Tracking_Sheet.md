# Master Issue Log — LifePRO → QLAdmin Conversion

**Last updated:** 2026-06-21 · **Engine:** `app.py` **v57.23**
**Purpose:** Single tracking sheet for **policy conversion (Issue #21)** and **claims conversion (Items 14–19)**.

---

## How to run (one path for client UAT)

1. Run **`QLA_Migration/run_converter.bat`** (or `_run_full_batch_test.py` headless)
2. Set paths to `QLA_Migration` folders (Source, Output, Configs, Mapping)
3. Click **EXECUTE FULL BATCH MIGRATION**

**v57.23 automatically:**
- Converts all policy tables (quikmstr, quikridr, etc.) including Issue #21 fixes
- Emits **claims from Phase 24 client-decision populations** (Items 14–16 applied)
- Applies **Item 18** combined claim amounts and **Item 19** payee overrides after emit
- Falls back to Phase 17 sources if client-decision files are missing (rollback-safe)

**Output:** `QLA_Migration/Output/quikclms.csv`, `quikclmp.csv` (+ all policy CSVs)

---

## Summary roll-up

| Area | Implemented in v57.23 | Awaiting client | Closed |
|---|---:|---:|---:|
| **Policy (Issue #21)** | 3 (21B, 21C, 21H ABA) | 8 + 21H target-field | 1 (21L) |
| **Claims (Items 14–19)** | 5 (14, 15, 16, 18, 19) | 147 claims in review | — |
| **Production cutover** | — | Authorization (`production_dbf_flag=N`) | — |

---

## A. Policy conversion — Issue #21

| ID | Item | Status | Client question (if open) |
|---|---|---|---|
| 21A | NFO / Dividend Options | AWAITING CLIENT | What should QLAdmin show for combined NFO values like "APL ETI"? |
| 21B | Bill Day | **IMPLEMENTED ✓** | Ready for UAT — verify Bill Day on sample policies |
| 21C | Policy Fees | **IMPLEMENTED ✓** | Ready for UAT — verify fee on base rider row |
| 21D | Interest Crediting Rate | AWAITING CLIENT | Authoritative rate: 4.00% or 4.50%? |
| 21E | Cash Value | AWAITING CLIENT | Load LifePRO value or let QLAdmin calculate? |
| 21F | Premium History | AWAITING CLIENT | How far back must premium history go? |
| 21G | Total Premium / Cost Basis | AWAITING CLIENT | Where should totals appear in QLAdmin? |
| 21H | Banking (ABA + target field) | **ABA IMPLEMENTED ✓** / target field AWAITING | Verify 9-digit ABA; confirm Bill Acct vs Credit Card ID field |
| 21I | Beneficiary Information | AWAITING CLIENT | Which beneficiary attributes are mandatory? |
| 21J | Modal Premium Factors | AWAITING CLIENT | Approved product-specific modal factors? |
| 21K | PUA Amount Precision | AWAITING CLIENT (New Era) | QUIKRIDR.MUNIT precision on DBF load? |
| 21L | Last Change Date | **CLOSED** | QLAdmin sets date on load |
| 21M | Policy Notes / ENS | IN SCOPE | Confirm sources + QUIKMEMO target |

**Detail:** `Issue_Log_Items/Issue_21/Issue_21_Tracking_Sheet.md`

---

## B. Claims conversion — Items 14–19

| Item | Description | Status in v57.23 | Notes |
|---|---|---|---|
| **14** | Surrender validation — approved payout patterns only | **IMPLEMENTED ✓** | 479 cleared; **21** remain for client review |
| **15** | Orphan payments — convert standalone | **IMPLEMENTED ✓** | 374 payments promoted with settled headers |
| **16** | Unbalanced claims — exclude `2023` div-on-dep; rebalance | **IMPLEMENTED ✓** | 155 promoted post-rebalance; **126** still unbalanced |
| **18** | Death claim amount = DB + loan + interest | **IMPLEMENTED ✓** | Auto-applied after emit (~518 rows) |
| **19** | Payee override (`010807842C`) | **IMPLEMENTED ✓** | Auto-applied after emit (1 row) |

**Client decisions:** `docs/claims_conversion_reference/client_issue_log_decisions_2026-06-11.md`

---

## C. Claims still awaiting client business review (147)

These are **not in the UAT emit** until the client decides. They are documented in the Phase 26 review packet — not a code gap.

| Queue | Count | Client decision needed |
|---|---:|---|
| Unbalanced death claims (post-rebalance) | **126** | Approve UAT / header-only / exclude |
| Surrender — insufficient payout evidence | **21** | Approve pattern / exclude / reclassify |
| **Total** | **147** | |

**Review packet:** `claims_analysis/phase26_client_business_review_packet/client_business_review_packet.md`

---

## D. What the client gets in UAT (after full batch, v57.23)

| Output | Expected population |
|---|---|
| Policy tables | Full batch (~5,083 quikmstr, ~7,002 quikridr, etc.) |
| **quikclms.csv** | ~**2,114** claims (client-decision UAT emit) |
| **quikclmp.csv** | ~**1,709** payments |
| UAT DBFs | Generated when `QLA_GENERATE_UAT_CLAIMS_DBF=1` (UAT mode) |

**Not included (by design until client decides):** the 147 deferred claims above, plus governance-quarantined pseudo-chains and other excluded populations.

---

## E. Outstanding before production

- Client answers on Issue #21 open items (21A, 21D–21G, 21I, 21J, 21K, 21H target-field)
- Client decisions on **147** deferred claims (Phase 26)
- Enterprise sign-off to set `production_dbf_flag=Y`

---

*Single master log. Policy detail: `Issue_21/Issue_21_Tracking_Sheet.md`. Claims decisions: `client_issue_log_decisions_2026-06-11.md`.*
