# Master Issue Log — LifePRO → QLAdmin Conversion

**Last updated:** 2026-07-10 · **Engine:** `app.py` **v57.71** / cumulative **v57.34+**
**Purpose:** Single tracking sheet for **policy conversion (Issue #21)** and **claims conversion (Items 14–19)**.

---

## How to run (one path for client UAT)

1. Run **`QLA_Migration/run_converter.bat`** (or `tools/batch_tests/run_full_batch_test.py` headless; legacy stub: `QLA_Migration/_run_full_batch_test.py`)
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

| Area | Released in v57.34–35 | Awaiting client UAT / answers | Closed |
|---|---:|---:|---:|
| **Policy (Issue #21)** | 7 (#21B, 21C, 21H ABA, 21M, 21M-FU, + cumulative #25/#26) | 7 + 21H target-field + 21K | **3 (21A, 21J, 21L)** |
| **Cross-cutting (#25/#26/#28)** | 3 (#25, #26, **#28**) | — | **2 (#28, #13)** |
| **Claims (Items 14–19)** | 5 (14, 15, 16, 18, 19) | 147 claims in review | — |
| **Production cutover** | Engine v57.35 (#28) ready | Authorization (`production_dbf_flag=N`) | — |

---

## A. Policy conversion — Issue #21

| ID | Item | Status | Release | Resolution |
|---|---|---|---|---|
| 21A | NFO / Dividend Options | **CLOSED ✓** | **v57.47** | PPBENTYP cache reads BF_NON_FORFEITURE for ISWL/BF; NFO codes 1/2 → APL (MNFOPT=1) per SME (v57.47). |
| 21B | Bill Day | **RELEASED ✓** | v57.22 / v57.34 | UAT — verify Bill Day on sample policies |
| 21C | Policy Fees | **RELEASED ✓** | v57.22 / v57.34 | UAT — verify fee on base rider row |
| 21D | Interest Crediting Rate | **DECIDED ✓** | v57.36 | ISWL 4.50% / non-ISWL 4.00% |
| 21E | Cash Value | **DECIDED ✓** | v57.63 | Traditional=compute QuikCvs; UL=load FV_BALANCE2→MCV0 |
| 21F | Premium History | **DECIDED ✓** | — | Accept ~2017 source floor |
| 21G | Total Premium / Cost Basis | **DECIDED ✓** | v57.63 | Source locked; staged to Reports/ |
| 21H | Banking (ABA + target field) | **ABA RELEASED ✓** / target AWAITING | v57.22 / v57.34 | Verify 9-digit ABA; confirm Bill Acct vs Credit Card ID |
| 21I | Beneficiary Information | **DECIDED ✓** | v57.29/63 | Type/split OK; MRELATION=1000 intentional |
| 21J | Modal Premium Factors | **CLOSED ✓** | **v57.46** | UAT — Coverage Detail modal grid on sample policies |
| 21K | PUA Amount Precision | AWAITING CLIENT (New Era) | Companion tooling only | Six-table MUNIT migration + UI UAT on 010448806C |
| 21L | Last Change Date | **CLOSED** | — | QLAdmin sets date on load |
| 21M | Policy Notes / ENS | **RELEASED ✓** | v57.32–34 | UAT — Memo tab on 010335038C |
| 21M-FU | QUIKMEMO one row per MEMOKEY | **RELEASED ✓** | **v57.34** | UAT — merged memo display on 010335038C |

**Detail:** `Issue_Log_Items/Issue_21/Issue_21_Tracking_Sheet.md` · **21M:** `Issue_Log_Items/Issue_21M/`

---

## B. Cross-cutting issues

| ID | Item | Status | Release | Resolution |
|---|---|---|---|---|
| **#13** | Incorrect QL Status (`quikmstr.MSTATUS`) | **CLOSED ✓** | **v57.48** | When CONTRACT_CODE=T, MSTATUS follows CONTRACT_REASON not PAID_UP_TYPE; 607 policies (v57.48). |
| **#25** | MPOLICY 10-char left-pad | **RELEASED ✓** | v57.30 / v57.34 | |
| **#26** | quikridr.MPREM mapping | **RELEASED ✓** | v57.31 / v57.34 | |
| **#28** | Product catalog PLAN mapping (crosswalk authority) | **CLOSED ✓** | **v57.35** | |
| **#37** | Age/Duration rate placement — fleet-wide | **CLOSED ✓** · **v57.43** · QuikCvs grid fix | **v57.43** | |
| **#38** | Dividend Accumulations (`quikdvdp.MDEPOSIT`) | **CLOSED ✓** · **v57.44** · 59 policies | **v57.44** | |
| **#40** | Inherited CV rate load — missing QuikCvs on CV-capable plans | **IMPLEMENTED / CLIENT UAT** · QuikCvs + QuikPlCv regenerated | — | 10 inherited plans emit 101,793 source-matched CV rows; `17085M` now 1,002 keys; 100% source-to-QLA PASS; full guarded emit still blocked by unrelated QuikUint |
| **#41** | CV age-100 endpoint off by one | **IMPLEMENTED / CLIENT UAT** · QuikCvs regenerated | — | 1960PO CV M/26 value 784.65 now maps to QLA duration index 57; age-100 endpoint proof PASS; full guarded emit still blocked by unrelated QuikUint dependency |
| **#42** | Missing rate extract rows — L01 10Y NP and L10 LP9595 | **AWAITING CSO SOURCE EXTRACT** | — | Client screenshots show rates; delivered Rate_Table and PAAGERAT contain 0 exact rows; converter proof complete; CSO must resend extracts |
| **#43** | ISWL expense charge source discovery | **INVESTIGATION COMPLETE / AWAITING CLIENT** | — | PCOVR.POLICY_FEE=25.00 on all 8 ISWL coverages; not proven equivalent to monthly expense per policy; no source for % premium or per-$1K charges |
| **#44** | QuikLoan stale PLOAN latest-row (`LAST_CHG_TIME` sort) | **CLOSED ✓** · **v57.60** · Phase A only | **v57.60** | Resolution: QuikLoan sorts PLOAN LAST_CHG_TIME as HHMMSS so same-day zero clears win; Phase B withdrawn |
| **#36** | Modal factors on `quikmstr` (Names-tab Modal Premiums) | **CLOSED ✓** · **v57.62** | **v57.62** | Resolution: quikmstr now receives plan-level modal factors (MSEMI/MQTRL/MMTHD/MMTHB) from quikplan, with PAC GL85 quarterly=25 and semiannual=50 overrides, so Names-tab Modal Premiums work (v57.62). |
| **#47** | Bill Day zero → Paid-To day | **CLOSED ✓** · **v57.65** | **v57.65** | Resolution: When Bill Day is zero, quikmstr.MBILLDAY now uses the day from Paid-To date while non-zero Issue #21B bill days stay unchanged (v57.65). |
| **#48** | Secondary Rate File (PAAGERAT fallback) | **G5 PASS → Ready for Regression** · **v57.69** | **v57.69** | Path wiring only; 0 new rates vs prior Rate_Table/PAAGERAT; 158 RT-only keys pre-existing |
| **#49** | QuikMstr Active Phase Status | **CLOSED ✓** · **v57.71** | **v57.71** | QuikMstr uses first active later phase when phase 1 display ≥50; phase-1 MPHSTAT unchanged (v57.71 fix); 35 policies MSTATUS 54→22 |

**#13 detail:** `Issue_Log_Items/Issue_13/` · Option A termination precedence · G5/G6 PASS · samples 010516211C→54, 011101663C→56

**#28 detail:** `Issue_Log_Items/Issue_28/` · Client UAT PASS 2026-06-27 · 33 PLAN corrections + DISCHO25

**#37 detail:** `Issue_Log_Items/Issue_37/` · CV duration placement · G5/G6 PASS · rollback: revert QuikCvs + loader

**#38 detail:** `Issue_Log_Items/Issue_38/` · PPBENTYP balance authority · PACTG 641 MINTYTD/MINTDATE · G5/G6 PASS · client UAT pending on 010378830C / 010380808C

**#40 detail:** `Issue_Log_Items/Issue_40/` · G5 PASS — `cv_inheritance_loader` + 100% source parity on 10 plans · `QuikCvs.csv` 38,047 rows · client UAT pending on `17085M` sample policies

**#41 detail:** `Issue_Log_Items/Issue_41/` · QuikCvs endpoint follow-up to Issue #37 · `1960PO` M/26 source-vs-QLA proof PASS · `QuikCvs.csv` regenerated with 26,495 rows · next: client UAT reload + resolve unrelated `QuikUint` full-emit blocker

**#42 detail:** `Issue_Log_Items/Issue_42/` · Screenshot-only source gaps · L01 10Y NP and L10 LP9595 NP/RV absent from delivered Rate_Table and PAAGERAT · proof in `client_l10_l01_followup/source_gap_proof/` · **No Go** until CSO resends missing extract rows

**#43 detail:** `Issue_Log_Items/Issue_43/` · Client question on Policy fee vs monthly expense per policy for 8 ISWL products · `PCOVR.POLICY_FEE=25.00` confirmed · UF segment zero-valued only · **No Go** for expense mapping until client confirms equivalence and missing-charge defaults

**#44 detail:** `Issue_Log_Items/Issue_44/` · **CLOSED** · **v57.60** Phase A · Resolution: QuikLoan sorts PLOAN LAST_CHG_TIME as HHMMSS so same-day zero clears win; Phase B withdrawn

**#47 detail:** `Issue_Log_Items/Issue_47/` · **CLOSED** · **v57.65** · Resolution: When Bill Day is zero, quikmstr.MBILLDAY now uses the day from Paid-To date while non-zero Issue #21B bill days stay unchanged (v57.65).

**#48 detail:** `Issue_Log_Items/Issue_48/` · **v57.69** · G5 PASS · 0 new rate content · Next: Regression (G6)

**#49 detail:** `Issue_Log_Items/Issue_49/` · **CLOSED** · **v57.71** · QuikMstr-only override; phase-1 MPHSTAT preserved via provisional inherit cache; validator asserts phase1 unchanged

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
| Release Notes (latest) | `Release_Notes/v57.35_Release_Notes.md` |
| Release Manifest (latest) | `Release_Manifest_v57.35.md` |
| Release Notes (prior) | `Release_Notes/v57.34_Release_Notes.md` |
| Release Manifest (prior) | `Release_Manifest_v57.34.md` |
| Issue #28 closure | `Issue_Log_Items/Issue_28/Issue_28_Closure_Report.md` |

---

## G. Outstanding before production sign-off

- Client UAT on **21M-FU** memo display (`010335038C`)
- Issue #21 open items 21D/E/F/G/I **DECIDED** (v57.63) — see `Issue_21/Issue_21_Open_Items_Official_Decisions.md`; remaining client items: 21K, 21H target-field
- Client decisions on **147** deferred claims (Phase 26)
- Enterprise sign-off to set `production_dbf_flag=Y`

---

*v57.35 release — Issue #28 CLOSED (2026-06-27). Prior: v57.34. Policy detail: `Issue_21/Issue_21_Tracking_Sheet.md`. Issue #28: `Issue_Log_Items/Issue_28/`.*
