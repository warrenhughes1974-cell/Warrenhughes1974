# Master Issue Log — LifePRO → QLAdmin Conversion

**Last updated:** 2026-07-14 (**YE 12/31/2025** conversion COMPLETE v57.86; Source=`LifePRO_Extracts_20260102`) · **Engine:** `app.py` **v57.86**
**Purpose:** Single tracking sheet for **policy conversion (Issue #21)** and **claims conversion (Items 14–19)**.

**Data accountability (midyear):** `Issue_Log_Items/Issue_Log_Data_Accountability_20260714.md`  
**Year-end package:** `Issue_Log_Items/YearEnd_20251231_Conversion_Notes.md` · load `Output/Test_Validation/`  
**Completed issues release checklist:** `Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md` (update on every close/commit)

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
| **Policy (Issue #21)** | 8 (#21B, 21C, 21F, 21H ABA, 21M, 21M-FU, + cumulative #25/#26) | 6 + 21H target-field + 21K | **4 (21A, 21F, 21J, 21L)** |
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
| 21F | Premium History | **CLOSED ✓** | **v57.73** | Non-ISWL Conversion Adjustment `quikprmh` row @ 12/31/2017 when LifePRO Base+PUA+SU+SL > history; ISWL excluded (v57.73). UAT pending. |
| 21G | Total Premium / Cost Basis | **CLOSED ✓** | v57.63 (staged only) | Not required in QL — New Era; no master-field load |
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
| **#143** | Units Incorrect (RPU) | **CLOSED ✓** | **v58.96** | Issue #143 is Closed in v58.96. The 23 SME-authorized BF Reduced Paid-Up policies now derive MUNIT from BF_CURRENT_DB / VALUE_PER_UNIT so QLAdmin Amount Ins reproduces the LifePRO paid-up death benefit. Validation, Regression, and final Smoke testing passed (PASS 9/9; release smoke RELEASE_OK). The existing Issue #124 QuikIswl emit was subsequently executed (COMPLETE), and all 23 affected ISWL records now store MDB = corrected MUNIT × 1000. Gold 9010757606C now contains MUNIT 19.10196 and MDB 19101.96. Authorized MUNIT corrections 23; unauthorized 0; unexplained diffs 0; outstanding #143 downstream dependencies 0. Detail: `Issue_Log_Items/Issue_143/` |
| **#2** | 11 Character Policy Number | **CLOSED ✓** | **v58.29** | Resolution: QLAdmin policy numbers now keep the LifePRO source policy number with a trailing C and are right-justified to 11 characters (replacing the old strip-9 crosswalk and 10-character pad). Detail: `Issue_Log_Items/Issue_2/` |
| **#13** | Incorrect QL Status (`quikmstr.MSTATUS`) | **CLOSED ✓** | **v57.48** | When CONTRACT_CODE=T, MSTATUS follows CONTRACT_REASON not PAID_UP_TYPE; 607 policies (v57.48). |
| **#25** | MPOLICY 10-char left-pad | **SUPERSEDED by #2** | v57.30 / v57.34 | Replaced by Issue #2 width-11 source+`C` (v58.29). |
| **#26** | quikridr.MPREM mapping | **RELEASED ✓** | v57.31 / v57.34 | |
| **#28** | Product catalog PLAN mapping (crosswalk authority) | **CLOSED ✓** | **v57.35** | |
| **#37** | Age/Duration rate placement — fleet-wide | **CLOSED ✓** · **v57.43** · QuikCvs grid fix | **v57.43** | |
| **#38** | Dividend Accumulations (`quikdvdp.MDEPOSIT`) | **CLOSED ✓** · **v57.44** · 59 policies | **v57.44** | |
| **#40** | Inherited CV rate load — missing QuikCvs on CV-capable plans | **IMPLEMENTED / CLIENT UAT** · QuikCvs + QuikPlCv regenerated | — | 10 inherited plans emit 101,793 source-matched CV rows; `17085M` now 1,002 keys; 100% source-to-QLA PASS; full guarded emit still blocked by unrelated QuikUint |
| **#41** | CV age-100 endpoint off by one | **IMPLEMENTED / CLIENT UAT** · QuikCvs regenerated | — | 1960PO CV M/26 value 784.65 now maps to QLA duration index 57; age-100 endpoint proof PASS; full guarded emit still blocked by unrelated QuikUint dependency |
| **#42** | Missing rate extract rows — L01 10Y NP and L10 LP9595 | **CLOSED** · **v57.97** | **v57.97** | PDAGE miss-fill; 20260714 refresh. Eric 2026-07-20: 0824/GPO OL NP **N/A** (PPBEN Status T / Reason EX) |
| **#23** | ISWL 3.5% premium expense charge (plan setup) | **DECIDED / Ready for plan setup** | — | Eric 2026-07-13: all ISWL have 3.5%; statement Censi I proves Premium Charge ≈ 3.5% of premium; exclude single premium |
| **#43** | ISWL expense charge source discovery | **DECIDED / Ready for plan setup** | — | Eric 2026-07-13: $25 POLICY_FEE taken monthly (~$2.08/mo); 3.5% confirmed; U6 = COI not expense |
| **#44** | QuikLoan stale PLOAN latest-row (`LAST_CHG_TIME` sort) | **CLOSED ✓** · **v57.60** · Phase A only | **v57.60** | Resolution: QuikLoan sorts PLOAN LAST_CHG_TIME as HHMMSS so same-day zero clears win; Phase B withdrawn |
| **#36** | Modal factors on `quikmstr` (Names-tab Modal Premiums) | **CLOSED ✓** · **v57.62** | **v57.62** | Resolution: quikmstr now receives plan-level modal factors (MSEMI/MQTRL/MMTHD/MMTHB) from quikplan, with PAC GL85 quarterly=25 and semiannual=50 overrides, so Names-tab Modal Premiums work (v57.62). |
| **#47** | Bill Day zero → Paid-To day | **CLOSED ✓** · **v57.65** | **v57.65** | Resolution: When Bill Day is zero, quikmstr.MBILLDAY now uses the day from Paid-To date while non-zero Issue #21B bill days stay unchanged (v57.65). |
| **#48** | Secondary Rate File (PAAGERAT fallback) | **G5 PASS → Ready for Regression** · **v57.69** | **v57.69** | Path wiring only; 0 new rates vs prior Rate_Table/PAAGERAT; 158 RT-only keys pre-existing |
| **#49** | QuikMstr Active Phase Status | **CLOSED ✓** · **v57.71** | **v57.71** | QuikMstr uses first active later phase when phase 1 display ≥50; phase-1 MPHSTAT unchanged (v57.71 fix); 35 policies MSTATUS 54→22 |
| **#50** | Policy Notes Missing (`quikmemo` / PNOTE) | **CLOSED ✓** · **v57.75** | **v57.75** | Resolution: QUIKMEMO fixed-width PNOTE parse + DBF MEMOKEY left-pad for Memo tab SEEK. New notes e.g. 01159D276C, 01222DCC, 01330D153C, 014075AC, 018187C, 018253C, 018910C, 01ML8522C. |
| **#45** | Bank Draft Account / PPPAC fallback (`quikmstr.MBANKNO`) | **CLOSED ✓** · **v57.77** | **v57.77** | Resolution: Bank-draft policies missing PPACH account numbers now fall back to PPPAC `E_ACCOUNT_NUMBER`, with ABA from routing lookup or RelationshipNameAddress, and emit `MBANKNO` only when both account and routing resolve. |
| **#51** | Missing Interest Table (`QuikAint` for A60MIR / A96DAR) — Projected Values crash loop | **Ready for Client UAT** · **v57.76** | **v57.76** | Resolution: Added QuikAint interest-rate stubs for closed riders A60MIR and A96DAR so QLAdmin Projected Values no longer fails looking up a missing interest table. |
| **#54** | Full Loan History Load (PACTG → **QuikBenh** + PLOAN seed + side-aware 0412) | **CLOSED ✓** · **v57.82** | **v57.82** | Resolution: Loan History now loads from QuikBenh with a PLOAN opening-balance seed for mid-stream loans, and CREDIT-side PACTG 0412 interest offsets map to type 12 so QLAdmin Balance closes to the QuikLoan current balance. |
| **#55** | Unit Issues (tiny `MUNIT` floor + leading-zero emit) | **CLOSED ✓** · **v57.78** | **v57.78** | Resolution: quikridr MUNIT below 0.001 floored to zero; rider decimals emit with leading digit (0.53000 not .53000); #25/#26 preserved. QLAdmin false `3000` Units = out of scope. |
| **#56** | PUA CV incorrect (`010310404C` / `960 PO PUA`) | **WITHDRAWN — superseded by #60** | — | Chris (actuary) plan wins: do not add PA plans; fix PUA phase + base interest. See Issue #60. |
| **#57** | NFO Option incorrect (LP 3/4/5 + PUT overwrite) | **CLOSED ✓** | v57.78 | **Resolution:** NFO codes 3/4/5 → MNFOPT 1/2/3; removed PAID_UP_TYPE→MNFOPT. Eric: 010367131C, 010148272C, 010143726C (ETI); 010392763C (RPU); 011221309C (APL). |
| **#58** | Premium Mode Amounts Incorrect (Names-tab fees) | **IMPLEMENTED v57.80** | **v57.80** | Derive `quikridr` M*FEE = MANNLFEE × post-PAC factors. Eric 010367131C → 15.90/5.40. Re-batch + validator. |
| **#59** | Incorrect QL Status (`quikmstr.MSTATUS`) | **CLOSED ✓** | **v57.84** | Resolution: For seven client-cited policies only, Active+LP→22 (not 54); S+DP→50 (not Paid Up). Exactly 7 MSTATUS deltas. UAT: reload Test_Validation quikmstr+quikridr. |
| **#60** | PUA phase + base interest (Chris 7/14) | **G6 PASS → Ready for Client UAT** · **v57.85** | **v57.85** | Track A: PUA-only phase fix; 0 non-PUA/phase-1 field drift. UAT: Test_Validation quikridr + rebuild CV. Track B (NFOINT) blocked. |
| **#70** | QuikPlan `LOANINTX` Advance/Arrears | **IMPLEMENTED v57.89 — Awaiting CSO** | **v57.89** | Fleet LOANINTX normalized to `A` (141 plans). Emit + Test_Validation published. Still need CSO: fleet Advance vs Arrears (`R`) plan list. |
| **#71** | Rate/plan/policy BAND → `00` | **CLOSED ✓** | **v57.90** | **Resolution:** All rate factor and rate-key BAND values (and QuikPlBd BDCODE) now emit as `00` (NOT APPLICABLE) to match quikridr MBAND=00, restoring Policy Display cash-value lookup. Client UAT PASS (`010718309C`). |
| **#72** | NFO must match ETI/RPU status (44→2, 45→3) | **Ready for Validation** · **v57.91** | **v57.91** | Post-map force MNFOPT from final MSTATUS 44/45; 277 policies; validator PASS; `Test_Validation/quikmstr.csv`. |
| **#74** | Var DB Code (`quikplan.VARDB`) `4` → `0` only | **CLOSED ✓** | — | **Resolution:** Rulebook VARDB `4`→`0` (121 plans); structure `1`/`2`/`3` unchanged (20). Val+Reg PASS. `Test_Validation/quikplan.csv`. |
| **#75** | Bank Acct / `MBANKNO` QLA validation | **CLOSED ✓** · **v58.35** | **v58.35** | Resolution: Bank-draft MBANKNO rebuilt from June PPCOM (checksum-valid 9-digit ABA / digits-only account). |
| **#77** | Fleet rate setup validation (PVO + default keys vs loaded rates / EX guide) | **CLOSED ✓** | **v57.95** | Resolution: Rate setup now ensures every plan with loaded rates has GP/DB/CV/TV/DV keys and correct Plan Values Options checkboxes, using NOT APPLICABLE defaults only when no real codes exist, without inventing factor values. |
| **#80** | CSO Valuation Setup → exact QuikPlCv / QuikPlTv assumptions | **Closed** (v58.01) | **Resolution:** CSO Valuation_Setup is now the authoritative source for cash-value and reserve assumption codes on 51 non-PUA plans, writing exact QuikPlCv, QuikPlTv, and quikplan NFOINT/INTMETHCV values with blank workbook cells left blank. | G5+G6 PASS; UAT: Test_Validation quikplan + QuikPlCv/Tv. Follow-ups: #81, #82. |
| **#81** | Valuation Setup PUA rows missing QLA Plan codes | **Intake** (parked) | — | Four rows: `622 PUA`, `675 61 PUA`, `675 AD PUA`, `991 PUA`. Split from #80. |
| **#82** | Valuation Setup PUA QuikPl* keys vs #60 (no PA in quikplan) | **Intake** (parked) | — | Whether to write QuikPlCv/Tv for PUA plan codes without adding PA to quikplan. Split from #80. |
| **#83** | Fleet gender companion rate keys (F/M; Values=N) | **CLOSED ✓** | **v58.02** | **Resolution:** Rate setup now emits missing Female/Male companion keys fleet-wide when a plan declares both gender members but a GP/DB/CV/TV/DV family only had one sex key, without inventing factor values (QLAdmin Values=N on companions with no factors). Val+Reg PASS; UAT pending (`221END` anchor). |
| **#84** | `quikclms` money-field decomposition (Policy-book parity) | **Track A Implemented v58.12 — Awaiting Validation** | **v58.12** | Track A: claim-key MPAID/PDDATE backfill after #85. Track B deferred. Out of scope: CLAIMSTAT (#79), new payees (#78). |
| **#85** | Duplicate claim headers (same policy + phase) | **Implemented v58.03 — Awaiting Validation** | **v58.03** | Merge 177 dups; rephase 3,034; payee re-attach 3,115 (15 exceptions). Headers 5,624→5,447; 0 dup pol+phase. Dev on Grok 4.5 (override). |
| **#86** | QuikDate full rebuild (prior-month-end + screenshot defaults) | **Implemented v58.13 — Awaiting Validation** | **v58.13** | Full single-row quikdate emit: PME on all date fields (ESC blank); PDUEDAYS=31, VERSION=5.318, UPDATENUM=359, ACH 0+A. Not crosswalk. Validator PASS 2026-07-19. |
| **#87** | QuikForge Balancing (source↔QLAdmin recon report) | **G5+G6 PASS — Ready for Client UAT** | **v58.14** | Balancing UI button + `qla_core/balancing.py`; reports → `Balancing/`. Val+Reg PASS 2026-07-19. BAL-D07 MSPLIT finding for client review. |
| **#88** | Blank ANN_PPU fallback loads full MODE_PREMIUM into Prem/Unit (valuation × units) | **CLOSED ✓** | **v58.23** | **Resolution:** When ANN_PREM_PER_UNIT is blank, quikridr.MPREM now uses annualized MODE_PREMIUM ÷ NUMBER_OF_UNITS instead of full modal premium; quikmstr Mode Prem unchanged. Val+Reg PASS; anchor 010779727C; reload Test_Validation/quikridr.csv. |
| **#89** | Policy fee wipe after `quikridr`-only rebatch (`MANNLFEE` / modal fees) | **CLOSED ✓** | **v58.24** | **Resolution:** Policy fees now load from LifePRO on every `quikridr` emit (including ridr-only rebatches), with a fail-closed guard so a blank fleet fee wipe cannot ship again; annual and modal fees are restored on fee-bearing policies. |
| **#95** | Declared Interest Rates Incorrect (PDINTTBL vs QuikUint) | **Blocked — Awaiting Client Clarification** | — | Eric No-Go 7/21: PDINTTBL rates DAR/DIV/IBA/L10=3.50%, SAL=2.00%, ISWL=4.50%. Source matches; QuikUint ISWL-only today. Gate FAIL — need target screen + MPLAN scope. |
| **#96** | CSO val cannot use SAL MULTPL / L17 RV (PVO + QuikPl* wiring) | **CLOSED ✓** | **v58.26 / v58.27** | **Resolution:** CSO valuation now enables Plan Values Options when QuikTvs/Cvs exist for SAL MULTPL and L17 RV plans, and `1SALMI` carries the same M/F QuikPlCv/QuikPlTv keys as `1SALOL`. Val+Reg PASS. |
| **#97** | Pol fee $0 / Names modal $ wrong / Memos blank (010398471C) | **Risk Complete — Awaiting Dev approval (verify track)** | — | Output already matches Eric (10.44; S/Q/M 62.40/31.80/10.80; memo CSV full). Same stack as #21C/#36/#58/#89/#50 — likely stale UAT load. **No-Go for formula code.** |
| **#98** | CV Endpoint Off By One (010398471C / 17085M) — #41 follow-up | **CLOSED ✓** | **v58.27** | **Resolution:** GL85 CV duration placement now starts `.06` in year 3 for male issue ages 1–17 and keeps the age-100 terminal `1000` (Eric `010398471C` / `17085M` M age 14). Val+Reg PASS; reload `Test_Validation/rates/QuikCvs.csv`. |
| **#99** | ISWL QuikPlan MKTG/PRODUCT/HLOB = ISWLFE | **Implemented v58.28 — Awaiting Validation** | **v58.28** | Sujitha: tag 8 ISWL plans MKTG/PRODUCT/HLOB=`ISWLFE` so QL picks them up as ISWL. Validator PASS; UAT reload `Test_Validation/quikplan.csv`. |
| **#104** | Loan Handling (claim/surrender payoff interest) | **Risk Complete — No-Go for Development (await SME)** | — | Eric No-Go 7/23: `010331768C` QL $3707.11+$194.01=$3901.12 vs LP $3707.11−$18.19=$3688.92. Same #32 QuikLoan emit. SME must choose Option A/B/C. Detail: `Issue_Log_Items/Issue_104/` |
| **#105** | QuikRidr MPAR for participating products | **CLOSED ✓** | **v58.30** | **Resolution:** Participating products now set QuikRidr.MPAR to True (1) from the product’s QuikPlan PAR flag by MPLAN. Val+Reg PASS; IN_DATA; UAT reload `Test_Validation/quikridr.csv`. |
| **#119** | PUA MPAR always non-participating (0) | **CLOSED ✓** | **v58.43** | **Resolution:** Paid-Up Addition coverages now set QuikRidr.MPAR to 0 (non-participating), matching QLAdmin PA-add behavior instead of copying the base coverage’s participating flag. Val+Reg PASS; IN_DATA; UAT reload `Test_Validation/quikridr.csv`. |
| **#135** | Claims Settlement vs CSO | **CLOSED ✓** | **v58.61** | **Resolution:** Death and surrender claim paid amounts now follow CSO Total_Paid with interest set to zero, missing payees filled from source accounting or policy roles, and QLAdmin claim/payee screens joining correctly. Detail: `Issue_Log_Items/Issue_135/`. |
| **#106** | RV Rates Off by One Duration (QuikTvs) | **CLOSED ✓** | **v58.31** | **Resolution:** QuikTvs RV factors now use the same duration year as LifePRO (Dur N to Dur N) instead of shifting one year early. Val+Reg PASS; IN_DATA; UAT `Test_Validation/rates/QuikTvs.csv`. Follow-up source mismatch → **#107**. |
| **#107** | `1L1095` RV source vs L10 LP9595 | **Open — DG BLOCKED (await Eric/extract)** | — | Follow-up from #106: QL `1L1095` pulls **L10 LP95**; client samples are LP9595; **0** LP9595 rows in extract. Need confirm or rates. Detail: `Issue_Log_Items/Issue_107/` |
| **#57** | NFO Option incorrect (LP 3/4/5 + PUT overwrite) | **CLOSED ✓** | v57.78 | **Resolution:** NFO codes 3/4/5 → MNFOPT 1/2/3; removed PAID_UP_TYPE→MNFOPT. Eric: 010367131C, 010148272C, 010143726C (ETI); 010392763C (RPU); 011221309C (APL). |
| **#58** | Premium Mode Amounts Incorrect (Names-tab fees) | **IMPLEMENTED v57.80** | **v57.80** | Derive `quikridr` M*FEE = MANNLFEE × post-PAC factors. Eric 010367131C → 15.90/5.40. Re-batch + validator. |
| **#59** | Incorrect QL Status (`quikmstr.MSTATUS`) | **CLOSED ✓** | **v57.84** | Resolution: For seven client-cited policies only, Active+LP→22 (not 54); S+DP→50 (not Paid Up). Exactly 7 MSTATUS deltas. UAT: reload Test_Validation quikmstr+quikridr. |
| **#18** | Citizens FoxPro Rate Tables (Reserve / Plans / CIFIANU1) | **OPEN — Awaiting source** | — | Request full tables from Tom/Debbie/Jelaine. Schema evidence in `SourceData_11-18-2024` Rate.cpy, Plan.cpy, AnnPrems,cpy. No Go until received. CFIC tracker: `CFIC_Rates/tracking/`. |
| **A** | QuikPlan / PVO / rate-key structural defects (Robert) | **INTERNAL — A10 Gate PASS** | — | A1/A4/A8/A9b done v58.21. **A10 QuikUwpo** Gate PASS (await Risk/Dev). A2/A3/A5/A7 open. **Not client-facing.** |

### Internal track (not client-facing)

| ID | Item | Status | Notes |
|---|---|---|---|
| **A** | QuikPlan / PVO / rate-key defects (Robert 2026-07-20) | **A10 Gate PASS** | QuikUwpo master missing NS/PR/SM/ST. Checklist every conversion. |
| **112** | Stale issue validators / accountability harness | **Active — partial** | Not a conversion defect. Most checkers fixed 2026-07-25; seven still on retired `_20260530` extract (WARN). **Do not put on CSO log.** |
| **108G** | Status consistency governance checks (DG-QUIKMSTR-027–032) | **Active — Part 1 done** | Governance only; no app.py. Part 2 (retire status forcing) waits on 108E. **Do not put on CSO log.** |

**Issue A detail:** `Issue_Log_Items/Issue_A/` · Risk: `Issue_A_Risk_Review_Report.md` · Checklist + `.cursor/rules/issue-a-conversion-checklist.mdc`

**#112 detail:** `Issue_Log_Items/Issue_112/Issue_112_Internal_Track.md` · Implementation: `Issue_112_Implementation_Notes.md`

**108G detail:** `Issue_Log_Items/Issue_108/Issue_108G_Internal_Track.md` · Implementation: `Issue_108G_Implementation_Notes.md`

**#18 detail:** `Issue_Log_Items/Issue_18/` · Citizens QLAdmin rate load · Not Warren app.py · Reserve file = CV/reserve/paid-up/ETI only (not gross premium, dividends, COI, loan values)

**#13 detail:** `Issue_Log_Items/Issue_13/` · Option A termination precedence · G5/G6 PASS · samples 010516211C→54, 011101663C→56

**#28 detail:** `Issue_Log_Items/Issue_28/` · Client UAT PASS 2026-06-27 · 33 PLAN corrections + DISCHO25

**#37 detail:** `Issue_Log_Items/Issue_37/` · CV duration placement · G5/G6 PASS · rollback: revert QuikCvs + loader

**#38 detail:** `Issue_Log_Items/Issue_38/` · PPBENTYP balance authority · PACTG 641 MINTYTD/MINTDATE · G5/G6 PASS · client UAT pending on 010378830C / 010380808C

**#40 detail:** `Issue_Log_Items/Issue_40/` · G5 PASS — `cv_inheritance_loader` + 100% source parity on 10 plans · `QuikCvs.csv` 38,047 rows · client UAT pending on `17085M` sample policies

**#41 detail:** `Issue_Log_Items/Issue_41/` · QuikCvs endpoint follow-up to Issue #37 · `1960PO` M/26 source-vs-QLA proof PASS · `QuikCvs.csv` regenerated with 26,495 rows · next: client UAT reload + resolve unrelated `QuikUint` full-emit blocker

**#80 detail:** `Issue_Log_Items/Issue_80/` · **CLOSED v58.01** · `Issue_80_Resolution_Summary.md` · UAT: Test_Validation · parked: #81, #82

**#81 detail:** `Issue_Log_Items/Issue_81/` · Intake parked · four Valuation_Setup PUA rows missing QLA Plan

**#82 detail:** `Issue_Log_Items/Issue_82/` · Intake parked · PUA QuikPlCv/Tv keys vs #60 SD-60-1

**#42 detail:** `Issue_Log_Items/Issue_42/` · **CLOSED** · **v57.97** · Resolution: PDAGE miss-fill + segment resolve → QuikNps/Tvs · 20260714 refresh · QuikUint waived (PDINTTBL missing) · Eric 2026-07-20 closed residual `0824 P DTH` / `L10 GPO OL` NP as **not applicable** (PPBEN Status T / Reason EX)

**#23 detail:** `Issue_Log_Items/Issue_23/` · **DECIDED 2026-07-13** · 3.5% premium expense all ISWL (non–single premium) · statement proof `Annual_Statement_Censi_I_9010817956.pdf` · companion #43

**#43 detail:** `Issue_Log_Items/Issue_43/` · **DECIDED 2026-07-13** · $25 Policy fee = monthly per-policy expense amortized ($2.08/mo) · 3.5% premium expense confirmed · U6 Curr COI is **not** expense · Decisions: `Issue_43_Meeting_Decisions_20260713.md` · Next: Sujitha plan expense setup

**#44 detail:** `Issue_Log_Items/Issue_44/` · **CLOSED** · **v57.60** Phase A · Resolution: QuikLoan sorts PLOAN LAST_CHG_TIME as HHMMSS so same-day zero clears win; Phase B withdrawn

**#47 detail:** `Issue_Log_Items/Issue_47/` · **CLOSED** · **v57.65** · Resolution: When Bill Day is zero, quikmstr.MBILLDAY now uses the day from Paid-To date while non-zero Issue #21B bill days stay unchanged (v57.65).

**#48 detail:** `Issue_Log_Items/Issue_48/` · **v57.69** · G5 PASS · 0 new rate content · Next: Regression (G6)

**#49 detail:** `Issue_Log_Items/Issue_49/` · **CLOSED** · **v57.71** · QuikMstr-only override; phase-1 MPHSTAT preserved via provisional inherit cache; validator asserts phase1 unchanged

**#50 detail:** `Issue_Log_Items/Issue_50/` · **CLOSED** · **v57.75** · Resolution: QUIKMEMO fixed-width PNOTE parse + DBF MEMOKEY left-pad for Memo tab SEEK; UAT Pass on 018495BC; new notes e.g. 01159D276C, 01222DCC, 01330D153C, 014075AC, 018187C, 018253C, 018910C, 01ML8522C

**#45 detail:** `Issue_Log_Items/Issue_45/` · **CLOSED** · **v57.77** · Resolution: Bank-draft policies missing PPACH account numbers now fall back to PPPAC `E_ACCOUNT_NUMBER`, with ABA from routing lookup or RelationshipNameAddress, and emit `MBANKNO` only when both account and routing resolve. · 739 fills; **24 still incomplete** (13 no account, 11 missing routing — list + MSTATUS in Resolution Summary Fleet Impact) · UAT: `Output/Test_Validation/quikmstr.csv` · samples 010157076C, 010161748C, 010348734C

**#51 detail:** `Issue_Log_Items/Issue_51/` · **Ready for Client UAT** · **v57.76** · G0–G6 PASS · Resolution: Added QuikAint interest-rate stubs for closed riders A60MIR and A96DAR so QLAdmin Projected Values no longer fails looking up a missing interest table. · UAT: load QuikAint; retest Projected Values on 010348734C · Git commit/push pending user request

**#54 detail:** `Issue_Log_Items/Issue_54/` · **CLOSED** · **v57.82** · UAT Pass. Resolution: QuikBenh loan history + PLOAN seed + CREDIT 0412→type 12 for Balance close. `Issue_54_Resolution_Summary.md`.

**#55 detail:** `Issue_Log_Items/Issue_55/` · **CLOSED** · **v57.78** · Resolution: MUNIT floor + leading-zero decimal emit on quikridr; 148 floor rows; G0–G7 PASS. `Issue_55_Resolution_Summary.md`. Client UAT: reload quikridr + DBF Append Tool v1.5.

**#56 detail:** `Issue_Log_Items/Issue_56/` · **WITHDRAWN 2026-07-14** — superseded by Chris plan in Issue #60. Do not Develop add-`1960PA` path.

**#70 detail:** `Issue_Log_Items/Issue_70/` · **IMPLEMENTED v57.89 — Awaiting CSO** · fleet `LOANINTX=A` (141) · `Output/quikplan.csv` + `Test_Validation/quikplan.csv` · CSO still needed for any `R` plans

**#71 detail:** `Issue_Log_Items/Issue_71/` · **CLOSED 2026-07-14** · **v57.90** · Resolution: rate BAND/BDCODE→`00` aligns with MBAND=00; CV lookup restored. Reload `Test_Validation/rates/` on network after pull.

**#72 detail:** `Issue_Log_Items/Issue_72/` · **Ready for Validation** · **v57.91** · 277 MNFOPT forced · `010407670C` 45→NFO 3 · `Test_Validation/quikmstr.csv`

**#73 detail:** `Issue_Log_Items/Issue_73/` · **CLOSED 2026-07-15** · `MISSCNTRY` default `USA`→`0000` (rulebook) · `Issue_73_Resolution_Summary.md`

**#74 detail:** `Issue_Log_Items/Issue_74/` · **CLOSED 2026-07-15** · `Issue_74_Resolution_Summary.md` · rulebook-only · 121×`4`→`0` / 20 keep · `Test_Validation/quikplan.csv`

**#75 detail:** `Issue_Log_Items/Issue_75/` · **CLOSED ✓** · **v58.35** · G7 IN_DATA · draft filled 2081/2132 · `Issue_75_Resolution_Summary.md`

**#77 detail:** `Issue_Log_Items/Issue_77/` · **CLOSED v57.95** · `Issue_77_Resolution_Summary.md` · UAT: reload `Test_Validation/quikplan.csv` + `rates/QuikPl*`

**#76 detail:** `Issue_Log_Items/Issue_76/` · **CLOSED 2026-07-15** · **v57.93** · `Issue_76_Resolution_Summary.md` · 400 ETI/RPU phase-1 adjusted · `Test_Validation/quikridr.csv` · UAT: Rebuild CV on `010407670C`

**#78 detail:** `Issue_Log_Items/Issue_78/` · **Implemented v57.98 — Awaiting Validation** · 729 policies / +932 `quikclmp` rows · `Issue_78_Implementation_Notes.md` · UAT: reload `Test_Validation/quikclmp.csv`

**#79 detail:** `Issue_Log_Items/Issue_79/` · **Implemented v57.99 — Awaiting Validation** · 1,769 CLAIMSTAT remapped (death→2, surrender→99) · `Issue_79_Implementation_Notes.md` · UAT: reload `Test_Validation/quikclms.csv`

**#84 detail:** `Issue_Log_Items/Issue_84/` · **Track A Implemented v58.12 — Awaiting Validation** · Claim-key MPAID/PDDATE backfill after #78/#79/#85 · Audit `Reports/issue84_money_field_audit.csv` · Track B (PACTG components + 898-policy recon) deferred · `Issue_84_Implementation_Notes.md`

**#85 detail:** `Issue_Log_Items/Issue_85/` · **Implemented v58.03 — Awaiting Validation** · G5 PASS · Dev Grok 4.5 override · 5,624→5,447 headers; 177 merges; 3,034 rephase; 6,151 payees unchanged · UAT: `Test_Validation/quikclms.csv` + `quikclmp.csv` · `Issue_85_Implementation_Notes.md`

**#87 detail:** `Issue_Log_Items/Issue_87/` · **G5+G6 PASS — Ready for Client UAT** · v58.14 · Val+Reg 2026-07-19 · Next: Closure Agent or client UAT (Balancing button)

**#89 detail:** `Issue_Log_Items/Issue_89/` · **CLOSED ✓** · **v58.24** · `Issue_89_Resolution_Summary.md` · UAT: `Test_Validation/quikridr.csv`

**#95 detail:** `Issue_Log_Items/Issue_95/` · Intake + Planning + Dependency Gate 2026-07-22 · **Gate FAIL** · Awaiting Eric: QuikUint confirm, 3.50% plan list, 668 vs 669, SALMI, history vs current-only

**#59 detail:** `Issue_Log_Items/Issue_59/` · **CLOSED 2026-07-14** · **v57.84** · Resolution: seven-policy scoped MSTATUS fix (6×54→22; 010521213C→50). `Issue_59_Resolution_Summary.md`. Client UAT pending Eric.

**#60 detail:** `Issue_Log_Items/Issue_60/` · **G6 PASS** v57.85 Track A · `Issue_60_Regression_Report.md` · Ready for Client UAT / Closure · Track B NFOINT still blocked.

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
