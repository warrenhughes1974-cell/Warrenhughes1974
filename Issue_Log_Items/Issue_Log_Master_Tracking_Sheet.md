# Master Issue Log — LifePRO → QLAdmin Conversion

**Last updated:** 2026-06-27 · **Engine:** `app.py` **v57.34**
**Purpose:** Single tracking sheet for **policy conversion (Issue #21)** and **claims conversion (Items 14–19)**.

---

## How to run (one path for client UAT)

1. Run **`QLA_Migration/run_converter.bat`** (or `_run_full_batch_test.py` headless)
2. Set paths to `QLA_Migration` folders (Source, Output, Configs, Mapping)
3. Click **EXECUTE FULL BATCH MIGRATION**

**v57.34 automatically:**
- Converts all policy tables (quikmstr, quikridr, quikmemo, etc.) including Issue #21 fixes
- Emits **QUIKMEMO** at production grain (one row per MEMOKEY — Issue #21M-FU)
- Packages memo DBF+DBT in `Output/quikmemo_uat_dbf/`
- Emits **claims from Phase 24 client-decision populations** (Items 14–16 applied)
- Applies **Item 18** combined claim amounts and **Item 19** payee overrides after emit
- Falls back to Phase 17 sources if client-decision files are missing (rollback-safe)

**Output:** `QLA_Migration/Output/quikclms.csv`, `quikclmp.csv`, `quikmemo.csv` (+ all policy CSVs)

---

## Summary roll-up

| Area | Released in v57.34 | Awaiting client UAT / answers | Closed |
|---|---:|---:|---:|
| **Policy (Issue #21)** | 7 (#21B, 21C, 21H ABA, 21M, 21M-FU, + cumulative #25/#26) | 8 + 21H target-field + 21K | 1 (21L) |
| **Claims (Items 14–19)** | 5 (14, 15, 16, 18, 19) | 147 claims in review | — |
| **Production cutover** | Engine v57.34 ready | Authorization (`production_dbf_flag=N`) | — |

---

## A. Policy conversion — Issue #21

| ID | Item | Status | Release | Client action (if open) |
|---|---|---|---|---|
| 21A | NFO / Dividend Options | AWAITING CLIENT | — | Mapping for ETI, APL ETI, Dividend Option |
| 21B | Bill Day | **RELEASED ✓** | v57.22 / v57.34 | UAT — verify Bill Day on sample policies |
| 21C | Policy Fees | **RELEASED ✓** | v57.22 / v57.34 | UAT — verify fee on base rider row |
| 21D | Interest Crediting Rate | AWAITING CLIENT | — | Authoritative rate: 4.00% or 4.50%? |
| 21E | Cash Value | AWAITING CLIENT | — | Load LifePRO value or QLAdmin calculate? |
| 21F | Premium History | AWAITING CLIENT | — | How far back must history go? |
| 21G | Total Premium / Cost Basis | AWAITING CLIENT | — | Target screen/field for totals |
| 21H | Banking (ABA + target field) | **ABA RELEASED ✓** / target AWAITING | v57.22 / v57.34 | Verify 9-digit ABA; confirm Bill Acct vs Credit Card ID |
| 21I | Beneficiary Information | AWAITING CLIENT | — | Mandatory beneficiary attributes |
| 21J | Modal Premium Factors | AWAITING CLIENT | — | Product-specific modal factors |
| 21K | PUA Amount Precision | AWAITING CLIENT (New Era) | Companion tooling only | Six-table MUNIT migration + UI UAT on 010448806C |
| 21L | Last Change Date | **CLOSED** | — | QLAdmin sets date on load |
| 21M | Policy Notes / ENS | **RELEASED ✓** | v57.32–34 | UAT — Memo tab on 010335038C |
| 21M-FU | QUIKMEMO one row per MEMOKEY | **RELEASED ✓** | **v57.34** | UAT — merged memo display on 010335038C |

**Detail:** `Issue_Log_Items/Issue_21/Issue_21_Tracking_Sheet.md` · **21M:** `Issue_Log_Items/Issue_21M/`

---

## B. Cross-cutting issues (released in v57.34)

| ID | Item | Status | Release |
|---|---|---|---|
| **#25** | MPOLICY 10-char left-pad | **RELEASED ✓** | v57.30 / v57.34 |
| **#26** | quikridr.MPREM mapping | **RELEASED ✓** | v57.31 / v57.34 |

---

## C. Claims conversion — Items 14–19

| Item | Description | Status in v57.34 | Notes |
|---|---|---|---|
| **14** | Surrender validation — approved payout patterns only | **IMPLEMENTED ✓** | 479 cleared; **21** remain for client review |
| **15** | Orphan payments — convert standalone | **IMPLEMENTED ✓** | 374 payments promoted with settled headers |
| **16** | Unbalanced claims — exclude `2023` div-on-dep; rebalance | **IMPLEMENTED ✓** | 155 promoted post-rebalance; **126** still unbalanced |
| **18** | Death claim amount = DB + loan + interest | **IMPLEMENTED ✓** | Auto-applied after emit (~518 rows) |
| **19** | Payee override (`010807842C`) | **IMPLEMENTED ✓** | Auto-applied after emit (1 row) |

**Client decisions:** `docs/claims_conversion_reference/client_issue_log_decisions_2026-06-11.md`

---

## D. Claims still awaiting client business review (147)

These are **not in the UAT emit** until the client decides.

| Queue | Count | Client decision needed |
|---|---:|---|
| Unbalanced death claims (post-rebalance) | **126** | Approve UAT / header-only / exclude |
| Surrender — insufficient payout evidence | **21** | Approve pattern / exclude / reclassify |
| **Total** | **147** | |

**Review packet:** `claims_analysis/phase26_client_business_review_packet/client_business_review_packet.md`

---

## E. What the client gets in UAT (after full batch, v57.34)

| Output | Expected population |
|---|---|
| Policy tables | Full batch (~5,083 quikmstr, ~7,002 quikridr, etc.) |
| **quikmemo.csv / DBF** | **4,380** rows (one per MEMOKEY) |
| **quikclms.csv** | ~**2,114** claims (client-decision UAT emit) |
| **quikclmp.csv** | ~**1,709** payments |
| UAT DBFs | Generated when `QLA_GENERATE_UAT_CLAIMS_DBF=1` (UAT mode) |

---

## F. Release documentation

| Document | Path |
|----------|------|
| Release Notes | `Release_Notes/v57.34_Release_Notes.md` |
| Release Manifest | `Release_Manifest_v57.34.md` |

---

## G. Outstanding before production sign-off

- Client UAT on **21M-FU** memo display (`010335038C`)
- Client answers on Issue #21 open items (21A, 21D–21G, 21I, 21J, 21K, 21H target-field)
- Client decisions on **147** deferred claims (Phase 26)
- Enterprise sign-off to set `production_dbf_flag=Y`

---

*Single master log. Policy detail: `Issue_21/Issue_21_Tracking_Sheet.md`. Release: v57.34 (2026-06-27).*
