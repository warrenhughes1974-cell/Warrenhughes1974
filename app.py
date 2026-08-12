# =============================================================================
# APPLICATION VERSION
# =============================================================================
# Version:     v58.93
# Date:        2026-08-12
# SYNC:        Must match QLA_Migration/app.py — run_converter.bat launches THIS file (repo root app.py).
# Change Note: v58.93 — Issue 104 validated advance-loan pilot: allowlisted policies
#              only back out LOAN_BALANCE×(1−rate) into MLOANPRIN/MLOANBAL after
#              runtime formula checks; flag QLA_ISSUE104_VALIDATED_LOAN_BACKOUT
#              (default 1). Non-cohort loans unchanged. Full-batch smoke wired.
#              v58.92 — QuikSpec emit: PPOLC.RES_STATE → quikspec.RESSTATE with
#              authoritative MPOLICY; VANISH defaults False / VANISHDT blank until
#              vanish mapping is in scope. Sync_Rulebook_quikspec.csv + PPOLC source;
#              SKIP_TRANSLATION avoids WA/IN/PA/GU relationship-code collisions.
#              Full-batch smoke: tools/validators/validate_quikspec_resident_state.py.
#              v58.81 — Client IDs: numeric→zero-decimal string, trim, left-pad to 12
#              (MCLIENTID/MPRIMID/MBENFID/…); was width 11.
#              v58.80 — Issue #137: blank ANN MPREM fallback uses modalized annual
#              (MODE ÷ mode-factor%) then ÷ units; crude ×12/4/2 only if factor missing.
#              v58.79 — Issue #21F CONV_ADJ for all plans including ISWL (PPBEN FV_GUAR_DEPOSITS).
#              v58.78 — TEMP quikclnt EOF high-water client (max+1) so QLAdmin New Client
#              does not collide with low LifePRO NAME_IDs; disable via QLA_QUIKCLNT_HIGHWATER=0.
#              v58.77 — Right-justify client-ID keys (incl. MBENFID) for QLAdmin SEEK;
#              Append Tool packs MCLIENTID/MPRIMID/…/MBENFID like MPOLICY (not left-justified).
#              v58.75 — L17 RV QuikTvs: PDAGE page VALUE1..10 annual expansion with
#              identity Dur mapping; auditable PDAGE fallback when active cut lacks L17.
#              v58.73 — Durable QuikTvs TV0 blank fill: non-SP rows emit `.00` zero;
#              true single-premium plans preserve blank TV0 (config + quikplan evidence).
#              v58.72 — Sync twin QLA_Migration/app.py byte-identical to root (PRELSA dated resolve + phase1 inherit path parity).
#              v58.61 — Issue #135: surrender CLAIMSTAT=99 zero-payee backfill
#              (PE 90/92/94 sum-match, else OWNR/INSD/PAYR); PRELSA dated extract resolve.
#              v58.60 — Issue #135: evidence-gated MATCH_CSO_EXISTING_HEADER_ZERO_PAYEE
#              cohort quikclmp backfill (SAFE_BACKFILL via 2032->1058 + PE/B1; holds residual).
#              v58.59 — Issue #135: allowlisted MATCH_CSO_EXISTING_HEADER_ZERO_PAYEE
#              quikclmp backfill for 9011156655C only (4 PE payees; header money unchanged).
#              v58.57 — Issue #135/#134: run PNOTE-B claim memo overlay AFTER #135 CSO
#              expansion so 142 DERIVED_HIGH headers receive MEMOTEXT; preserve 308 marker.
#              v58.56 — Issue #135: Option-3 consume + 459 CSO expansion (142 derived,
#              308 header-only no-PACTG, 9 hold); MINTAMT=0 retained; #134 marker-safe.
#              v58.55 — GP variation flags derive from real emitted GP key segmentation;
#              CV/TV collapse and default-only cleanup cannot clear GP variation.
#              v58.54 — Issue #135 Phase A: always emit quikclms.MINTAMT=0.00 (client lock;
#              interest not needed). Post-emit force after #134; MPAID/MAMOUNT untouched.
#              v58.52 — Issue #59: do not let Issue #49 later-active-phase override replace
#              Death Claim Pending (50) on scoped S/DP policy 9010521213C / 010521213C.
#              Other #49 overrides unchanged; #59 Active+LP interceptor unchanged.
#              v58.50 — Issue #70: QuikPlan LOANINTX from PCOVR.LOAN_ADV_ARREARS (0/N→A, 1→R);
#              retain SKIP_TRANSLATION + invalid→A safety net; QuikLoan lookup unchanged.
#              v58.49 — Issue A11 + A3: default-only PVO/key handling, independent CV/TV UW collapse,
#              fleet DEFICIENCY/PAR guards, and focused regression checks.
#              v58.48 — Issue #120: emit quiklist.csv for active six LST groups (PPOLC+RNA GP);
#              MCOMP=C, governance defaults, deterministic postal address preference, 07132 repair.
#              v58.47 — Issue #134: PNOTE FILE_TYPE=B → quikclms.MEMOTEXT (Claims Tab memo);
#              exclude B from quikmemo Policy Memo. Post-emit overlay after #79/#85/#84.
#              v58.46 — Item 18 claims overlay: apply combined amounts only when loan offset
#              is present. Interest-only (0630) rows must not inflate NETDB/MPAID/MFACE above
#              the 0094 payout (double-count fix; e.g. 9010402010 10700.73 → 8920.15).
#              v58.45 — Issue #124: emit QuikIswl month-0 seed rows for all ISWL base policies
#              (MLOB=I, MLASTANNV=MISSDT, MDB=MUNIT*1000, MMONTH=0). Batch hook default ON
#              (QLA_ENABLE_QUIKISWL_EMIT=0 to skip). Post-load anniversary remains client ops.
#              v58.44 — Issue #121: ART family (5667AT/5646AT/57ATCR) must not emit ETI.
#              PAID_UP_TYPE LE/ET no longer wins on Annual Renewable Term; use CONTRACT_CODE+REASON.
#              v58.43 — Issue #119: PUA coverages force quikridr.MPAR=0 (non-participating).
#              Robert: when QLAdmin adds a PA rider it sets PAR/MPAR to 0; do not inherit base.
#              v58.42 — Honor Source\\<package>\\ extract folders (e.g. 12312025_Data) when
#              Source Data File points inside a package subdir; do not collapse to Source root.
#              v58.41 — Auto-launch DBF_Append_Tool\\run_app.bat after any successful conversion
#              (single table, product setup, rates, or full batch). Disable with
#              QLA_LAUNCH_DBF_APPEND_TOOL=0.
#              v58.40 — After successful full batch, auto-launch DBF_Append_Tool\\run_app.bat
#              (set QLA_LAUNCH_DBF_APPEND_TOOL=0 to disable).
#              v58.39 — Always publish Output quik*.csv + rates/*.csv (flat) to
#              C:\Users\warren\Desktop\DBF_Append_Tool\input for the append tool.
#              v58.38 — QuikMemo UAT DBF+DBT always emit to
#              C:\Users\warren\Desktop\DBF_Append_Tool\output (append-tool load path).
#              v58.37 — Issues #116 + #117: dividend accumulation accuracy.
#              #116 quikdvdp: the PACTG 0641 interest cache was keyed on the crosswalk
#              New_Value while the enrichment looked it up by emitted MPOLICY, so no row ever
#              matched and MINTDATE fell through to the premium paid-to date — a future date
#              that made QLAdmin show negative accrued interest. Cache now registers both keys.
#              #117 quikbenh: Dividend History is a ledger, not a credits list. Adds MBENTYP 6
#              (interest on policy funds, PACTG 0641/0310) and MBENTYP 7 (surrendered dividend
#              accumulations, debit 0310), nets self-reversing 0310 pairs, and splits the
#              20171231 opening into its type 3 and type 6 halves so the window foots to the
#              QuikDvdp balance. Issue #114 type 3 amounts are unchanged.
#              v58.36 — Issue #114: LifePRO dividend history → QuikBenh benefit types 1-5.
#              Layer A loads PACTG dividend election codes 0514/0515/0516/0517/0518 (DEBIT leg
#              only — the credit leg is the contra side and would double-count) as dated rows;
#              Layer B adds one conversion adjustment row per policy (20171231) for the pre-extract
#              remainder so each policy ties to PPBENTYP.DIVIDENDS_CREDITED. Gated by
#              QLA_ENABLE_QUIKBENH_DIVIDEND_EMIT / QLA_QUIKBENH_DIVIDEND_WRITE_OUTPUT.
#              Appends only — MBENTYP 8 (#34) and 10/11/12 (#54) preserved in place.
#              v58.35 — Issue #75 reopen: rebuild aba_routing_lookup from June PPCOM
#              (PPACH+PPPAC accounts; unique + latest-ambiguous; checksum-valid 9-digit ABA).
#              Keep QLA-safe MBANKNO gate; preserve source account leading zeros (digits-only);
#              ABA leading zero kept when part of validated 9-digit routing.
#              v58.34 — Issue #110: PPBENTYP dividend cache keyed off source POLICY_NUMBER
#              (same Issue #2 key regression as #108F; MDIVOPT was 0 on all 5,083 policies).
#              v58.33 — Issue #108F: PPBENTYP non-forfeiture cache keyed off source POLICY_NUMBER.
#              The Issue #2 (v58.29) MPOLICY change left the crosswalk lookup resolving nothing,
#              dropping the NFO election on 4,346 policies. Issue #72 downgraded from a force to
#              Reports/nfo_election_status_mismatch.csv per Robert 2026-07-25.
#              v58.32 — Issue #108 (Robert NFO conformance), ETI/RPU phase-1 only:
#              108B quikridr.MAGE = attained age at MPAIDTO (was issue age) and Issue #76
#              MLASTANN now anniversary-accurate against the batch valuation date;
#              108C ETI (44) MPREM = 0.00 (RPU 45 unchanged per spec);
#              108D PUA rider on an ETI/RPU base = MPHSTAT 54, not Issue #60's 41;
#              108A MSAVE* left blank on ETI/RPU phase 1 (v57.96 mirror suppressed).
#              v58.31 — Issue #106: QuikTvs Dur identity for 1L1095 / L10 fleet.
#              v58.30 — Issue #105: quikridr.MPAR from product quikplan.PAR by MPLAN (participating=1).
#              v58.29 — Issue #2: MPOLICY = source POLICY_NUMBER + C, right-justify width 11 (supersedes #25).
#              v58.28 — Issue #99: ISWL quikplan MKTG/PRODUCT/HLOB = ISWLFE (8 MPLAN allowlist).
#              v58.27 — Issue #98: GL85 CV endpoint remap (male ages 1–17); age-100 terminal preserved.
#              v58.26 — Issue #96: CSO val PVO enablement when QuikTvs/Cvs present; 1SALMI on
#              CSO Valuation_Setup (PlTv/PlCv = SAL OL); re-run R7B on quikplan after rate emit.
#              v58.25 — L17 child plans inherit QuikTvs RV from segment L17 (Eric 7/22);
#              SAL MULTPL/ML→SAL OL RV already live; L01/L05/L07/667 ART held for actuarial.
#              v58.24 — Issue #89: load POLICY_FEE cache on quikridr path (ridr-only rebatch safe);
#              fail-closed guard if MANNLFEE fleet wipe detected after emit.
#              v58.22 — Issue A A10: emit QuikUwpo (UW class master) from distinct plan UW codes.
#              v58.21 — Issue A A4/A6/A8/A9b internal QuikPlan setup fixes.
#              v58.20 — Single Table quikplan: define out_dir before variation audit write.
#              v58.19 — Issue A A1: single-prem SP modal zeros re-applied after #21J overlay (4 DESCR plans).
#              v58.18 — QUIKConvert branding + rotating header taglines (UI only).
#              v58.17 — Issue #87: Balancing progress bar uses a real 6-stage plan (was stuck on Stage 1).
#              v58.16 — Issue #87: plain-English Balancing report wording (no RNA/PPOLC jargon).
#              v58.15 — Issue #87: Balancing reports match Data Governance style (HTML executive
#              summary + Items Needing Attention CSV per run folder).
#              v58.14 — Issue #87: QuikForge Balancing button — read-only Source↔Output reconciliation
#              report under QLA_Migration/Balancing/ (PASS/EXPLAINED/FAIL controls).
#              v58.13 — Issue #86: full QuikDate rebuild (PME on all date fields; screenshot defaults).
#              v58.12 — Issue #84 Track A: backfill quikclms MPAID/PDDATE from claim-keyed payees.
#              v58.11 — Policy Data Governance: MBILLDAY from MISSDT; clear MBENPID/MBENCID;
#              non-INSD QuikClid MPHASE→0; MLANGUAGE default E; transform audit CSV.
#              v58.10 — DG-R-009 single-premium PAYYRS/PAYAGE + modal zeros.
#              v58.09 — UI theme: QuikForge red/white brand palette (QLAdmin-aligned accents).
#              v58.08 — UI brand: QuikForge — "Forge. Validate. Deliver." (source-agnostic).
#              v58.07 — DG-R-003: emit quikdate.csv on batch with prior-month-end PAC/DIR/REIN
#              bill dates + ACH defaults (shared prior_month_end from data_governance).
#              v58.06 — UI: web-style Operator Console (all run actions + KPI tiles); remove
#              redundant bottom Run Controls; Single Table + Rate Tables promoted to dashboard.
#              v58.05 — UI: Governance Data Folder picker (CSV or DBF region) for on-demand
#              QLAdmin Data Governance; post-batch still audits Output.
#              v58.04 — Replace legacy data_governance audit with QLAdmin Data Governance
#              framework (DG-QUIKCOMP-001/002/003); outputs under Reports/data_governance/.
#              v58.03 — Issue #85: unique quikclms claim identity — merge same-CLAIMNUM
#              duplicates; re-phase distinct claims (Policy-book pattern); re-attach quikclmp
#              phases (D4); CLAIMSTAT/#78 invent unchanged; audits in Reports/.
#              Dev model override: Cursor Grok 4.5 (user one-time override 2026-07-17).
#              v58.02 — Issue #83: fleet gender companion rate keys (F/M) when QuikPlGd declares
#              both members and a family already has one sex key; no factor invent (Values=N).
#              v58.01 — Issue #80 validation fixes: QuikPlTv MORT blank rule; QA to Reports/; Test_Validation
#              publish cleanup; strengthened validator (package purity, schema, PUA isolation).
#              v58.00 — Issue #80: CSO Valuation_Setup authority for 51 non-PUA plans — QuikPlCv/Tv
#              via rate_pipeline CompositeAssumptionProvider; quikplan NFOINT/INTMETHCV overlay after
#              CSO crosswalk (Valuation_Setup wins); blank workbook cells emit blank.
#              v57.99 — Issue #79: remap quikclms.CLAIMSTAT to Policy-book conventions
#              (death→2 Paid in Full, surrender/partial/disbursement→99, maturity→98;
#              close false Pending); ORIGSTTUS and quikclmp unchanged; audit in Reports/.
#              v57.98 — Issue #78: recover missing quikclmp rows for claim policies with zero
#              payments when PACTG live payout exists; Tier 1/2/3 PE/B1/estate payee fallback;
#              append-only + Reports/issue78_quikclmp_recovery_audit.csv; quikclms unchanged.
#              v58.27 — Rate audit fixes: durable 1SALMI M/F PlCv/PlTv keys (#96) and
#              Issue #98 GL85 CV duration endpoint alignment.
#              v57.97 — Wire rate loader to LifePRO 20260714 PDAGE/PAAGERAT package (Issue #42
#              miss-fill path + plan_source_paths prefer 20260714; key/seg defaults unchanged).
#              v57.96 — Policy-book alignment: BF_LST→3 translation; quikmstr MBILLTO 0/blank→MPAIDTO,
#              MORIGBILL/MORIGMODE default to final bill form/mode, MISSCLASS=00 / MBFCY=0 / MACHCNT=0
#              rulebook defaults; quikridr MRRULE=A / MANNSTAT=0 / MCOMMID=CNVT / blank MUWCLASS=00
#              defaults + blank MSAVE* mirror final MAGE/MUNIT/MVPU/MPREM/MPHSTAT.
#              v57.95 — Issue #77: omit NOT APPLICABLE member/key (0/00) when real codes exist
#              (EX pattern; e.g. no Gender 0 beside F/M).
#              v57.94 — Issue #77: rate-key default stubs (GP/DB/CV/TV/DV), Plan Values Options
#              recompute from keys, QuikPlSt.MLOANINT default 0.00; no factor invent.
#              v57.93 — Issue #76: quikridr phase-1 MPAYUP←MPAIDTO + MLASTANN=sys year−payup
#              year when quikmstr MSTATUS 44/45 (ETI/RPU CV anniversary dates); #60 PUA untouched.
#              v57.92 — Issue #75: quikmstr.MBANKNO QLA-safe emit — 9-digit ABA only, digits-only
#              account, single slash; strip punct; blank + exception when unrecoverable (#45 gate).
#              v57.91 — Issue #72: quikmstr MNFOPT forced from final MSTATUS when exercised
#              (44→2 ETI, 45→3 RPU); #57 election mapping unchanged for other statuses.
#              v57.89 — Issue #70: quikplan LOANINTX fleet-normalize to A when missing/invalid
#              (A/R only; interim Advance default pending CSO guidance).
#              v57.88 — Chris UAT: quikclnt MTAXIDTYPE default S (SKIP_TRANSLATION; was 55 via S→55);
#              right-justify MCLIENTID and linked client IDs to C(11), including rel_map MPRIMID/MRIDRID;
#              quikridr MBAND default 00.
#              v58.10 — DG-R-009: single-premium quikplan payment settings (PAYYRS=1, PAYAGE/SEMI/QTRL/MTHD/MTHB=0) via Configs/single_premium_plans.csv.
#              v57.87 — quikplan: SEX_BASIS B → blank SEX; SKIP_TRANSLATION on RENEW/CALCADV/BACTIVE/LOANINTX
#              so defaults N/A are not flipped by bare Master_Value_Translation (N→T, A→22).
#              v57.86 — QLA_VALUATION_DATE=YYYYMMDD overrides QUIKRIDR.MLASTANN valuation date
#              (year-end / extract-as-of runs; default remains conversion run date).
#              v57.85 — Issue #60: PUA phase fields (Chris plan) — gated by _is_paid_up_addition_product
#              only; inherit MEFFDATE/MAGE from base; MPAYUP=MEFFDATE; MPHSTAT=41 when base < 50;
#              MLASTANN follows inherited MEFFDATE. Other riders unchanged. No PA plan file.
#              v57.84 — Issue #59: quikmstr.MSTATUS — scoped fix for 7 client policies only:
#              Active+PAID_UP_TYPE=LP → A_ (22); CONTRACT_CODE=S → S_{REASON} (DP→50).
#              Does not alter PUT precedence for any other policy (#13/#49 preserved).
#              v57.83 — quikridr MUWCLASS must NOT use bare status translations
#              (S→55, P→41, N→T, T→56); map LifePRO UW → SM/PR/NS/ST/00 (Q→NS for L14 rates).
#              v57.82 — Issue #54: PACTG side-aware QuikBenh map (CREDIT 0412 → MBENTYP 12) so
#              Loan History Balance closes to QuikLoan; keeps PLOAN opening seed.
#              v57.81 — Issue #54: QuikBenh loan history (PACTG 10/11/12) + PLOAN opening-balance
#              seed for mid-stream policies; gated QLA_ENABLE_QUIKBENH_LOAN_EMIT.
#              v57.80 — Issue #58: derive quikridr MSEMIFEE/MQTRLFEE/MMTHDFEE/MMTHBFEE from
#              MANNLFEE × post-PAC quikmstr modal factors (Names-tab premium amounts).
#              v57.78 — Issue #55: quikridr MUNIT floor (0 < x < 0.001 → 0) + leading-zero decimal
#              emit for rider numerics (never `.53000`); MPREM #26 numeric preserved.
#              v57.77 — Issue #45: PPPAC E_ACCOUNT_NUMBER fallback when PPACH account missing;
#              ABA via lookup/RNA; emit MBANKNO only when both present; refined exceptions.
#              v57.76 — Issue #51: emit QuikAint stubs for A60MIR/A96DAR (Projected Values crash-stop).
#              v57.75 — Issue #50 UAT: QUIKMEMO DBF MEMOKEY left-pad preserved (Memo tab SEEK match).
#              v57.74 — Issue #50: PNOTE fixed-width reader preserves notes with commas in LINE text.
#              v57.73 — Issue #21F fix: BA/BF-only base, sum SU/SL, strip-rebuild CONV_ADJ,
#              validation report FINAL/VARIANCE math; OPENING_BALANCE status.
#              v57.72 — Issue #21F: non-ISWL conversion premium adjustment rows on quikprmh
#              (DATEPAID=20171231, MSOURCE=CONV_ADJ); validation/exception reports in Reports/.
#              v57.71 — Issue #49 fix: phase-1 MPHSTAT inherit uses pre-override (Issue #13)
#              provisional MSTATUS so QuikMstr active-phase override does not change phase 1.
#              v57.70 — Issue #49: when quikmstr first-phase display status is >=50 and a later
#              phase is 0–49, set MSTATUS to that first active later phase (after Issue #13).
#              v57.67 — Remove Validate Output / Final Output Validation from UI; governance audit only.
#              v57.66 — UI: RUN DATA GOVERNANCE AUDIT button (data_governance module → Reports/).
#              v57.65 — Issue #47: when quikmstr.MBILLDAY is 0/blank, fallback to day of
#              PAID_TO_DATE (preserve non-zero POLICY_BILL_DAY / Issue #21B).
#              v57.64 — Resolve PACTG_Accounting_Extract*.csv by pattern/date (QuikIsrr + claims);
#              stop hardcoding 20260427/20260530 extract filenames.
#              v57.63 — Issue #21 open decisions locked: 21E UL FV_BALANCE2→MCV0 on phase-1;
#              21G staged premium/basis report; 21D/21F/21I documented (no further code).
#              v57.62 — Issue #36: copy quikplan SEMI/QTRL/MTHD/MTHB → quikmstr MSEMI/MQTRL/MMTHD/MMTHB
#              (Names-tab Modal Premiums); PAC GL85 Q/S overrides still applied after plan copy.
#              v57.61 — Issue #45: bank-draft (MBILLFRM=2) missing PPACH account → blank MBANKNO +
#              Reports/bank_draft_account_exceptions.csv; #21H ABA path unchanged for valid accounts.
#              v57.60 — Issue #44 Phase B withdrawn: QuikLoan no longer suppresses ETI/RPU by MSTATUS;
#              Phase A LAST_CHG_TIME HHMMSS sort retained (clears stale same-day PLOAN balances).
#              v57.59 — Issue #44: QuikLoan latest-row LAST_CHG_TIME HHMMSS sort (Phase A) + suppress
#              emit when MSTATUS is ETI/RPU 44/45 (Phase B); clears stale loan balances on ETI.
#              v57.58 — quikplan.LOANINT from PLOAN.INTEREST_RATE (modal AS_PERCENT) on Product Setup
#              and batch quikplan; LOANINTX set to A when missing/invalid (e.g. 170858 → 5.00).
#              v57.57 — quikplan.PAR from LifePRO EXHIBIT_PAR_NONPAR (P→1, N→0 via PAR_ translation);
#              fixes participating plans (e.g. 2665ST) emitting PAR=0.
#              v57.56 — UI: RUN PRODUCT SETUP CONVERSION always visible in Run Controls + Operator Dashboard
#              (was below fold / off-screen on shorter displays).
#              v57.55 — Root app synced with QLA_Migration engine; Issue #40 rate emit via qla_core.rate_emit;
#              version banner now matches launcher (fixes v57.53 display when using run_converter.bat).
#              v57.54 — Issue #40: inherited CV rate emit integrated in-app (QuikCvs/QuikPlCv/member tables).
#              v57.53 — RNA reader preserves over-wide LifePRO rows so IN/PO/PA relationships are not skipped.
#              v57.52 — UI version display synced to engine; UAT launcher enables reinsurance Phase 1 emit.
#              v57.51 — Issue #30: RNA relationship MPOLICY fallback from IDENTIFYING_ALPHA; exact quikclid dedupe.
#              v57.50 — Phase 1 Reinsurance: gated QuikRein/QuikRmst batch hook (root app parity with QLA_Migration).
#              v57.48 — Issue #13: quikmstr.MSTATUS termination precedence when CONTRACT_CODE=T
#              (CONTRACT_REASON wins; PAID_UP_TYPE ignored for terminated contracts).
#              v57.47 — Issue #21A: PPBENTYP BF_NON_FORFEITURE cache for TYPE_CODE=BF;
#              NF_1/NF_2→APL, NF_9→0 safety (codes 3–6 translation unchanged).
#              v57.46 — Issue #21J fix: PAC billing detected as translated MBILLFRM=2 (BF_PAC) for GL85 overrides.
#              v57.45 — Issue #21J: per-plan modal premium factors from client mapping; PAC GL85
#              quikmstr.MSEMI/MQTRL overrides; fleet-wide QUIKMEMO [CONVERSION] governance memos.
#              v57.44 — Issue #38: quikdvdp MDEPOSIT from PPBENTYP ACCUM_DIVIDENDS (stop zero-on-miss);
#              PACTG 641-only cache for MINTYTD/MINTDATE; dynamic PACTG source via resolve_table_source.
#              v57.43 — Issue #37: fleet QuikCvs CV duration grid (LifePRO placement; maturity 100−age)
#              via R5 rate pipeline / qla_core (values unchanged; GENERATE RATE TABLES emits corrected QuikCvs).
#              v57.43 — Enterprise UI polish: status strip, summary cards, collapsible diagnostics (no logic changes).
#              v57.41 — Full UAT batch integration: ISWL rate tables (Issues #31–33 QuikUint/QuikIssc via R5),
#              QuikLoan batch emit (#32), QuikIsrr partial-surrender package (#34 PR-7 append to quikclms/clmp).
#              UAT launcher enables all phases via run_converter.bat env flags.
#              v57.40 — Issue #32: QuikLoan v1.2 mapping (PLOAN→QuikLoan; MLOANACCR=0; AS_PERCENT; MLOANINTX plan lookup + default A).
#              v57.39 — Issue 27: suppress PPBEN BENEFIT_TYPE SL from quikridr emit (Substandard Life is not coverage); SL suppression audit CSV.
#              v57.38 — Rollback Issue 21J: remove QUIKMEMO [CONVERSION] modal factor memo (restores v57.36 quikmemo behavior).
#              v57.37 — Issue 21J: QUIKMEMO [CONVERSION] modal premium factor governance memo per policy (documentation only) [ROLLED BACK in v57.38].
#              v57.36 — Issue 21D Track A: ISWL-scoped quikdvdp.MDEPINT=4.50 via MPLAN allowlist; Track B1: quikclnt emit for RNA CANCEL_DATE/ADDRESS_ID NULL literals.
#              v57.35 — Issue 28: product catalog crosswalk_ql_plan_code runtime authority; DISCHO25 catalog row; P3E MPLAN default ON.
#              v57.34 — Release integration: Issue 21M-FU QUIKMEMO one row per MEMOKEY (production grain).
#              v57.33 — Issue 21M: quikmemo DBF+DBT packaged in Output/quikmemo_uat_dbf/ (hygiene skip).
#              v57.32 — Issue 21M: QUIKMEMO from PNOTE + PENSE dual-source merge (CSV + DBF/FPT).
#              v58.23 — Issue 88: blank ANN_PREM_PER_UNIT MPREM fallback = annualized MODE_PREMIUM / units (not raw MODE_PREMIUM).
#              v57.31 — Issue 26: quikridr.MPREM maps ANN_PREM_PER_UNIT with MODE_PREMIUM fallback.
#              v58.29 — Issue #2: MPOLICY = source POLICY_NUMBER + C, right-justify width 11 (supersedes #25 strip9+C/10-pad).
#              v57.30 — QLAdmin MPOLICY fixed-width 10-char emit (leading-space left-pad after crosswalk).
#              v57.29 — Issue 21I: quikbenf dedupe by (MPOLICY, MBENFID, MTYPE) and equal MSPLIT
#              within each (MPOLICY, MTYPE) primary/contingent group (100.00 total per group).
#              v57.28 — block LifePRO PRIMARY_PERSON type flags (e.g. "I") from quikmstr.MPRIMID.
# =============================================================================

import pandas as pd
import os
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext, ttk
import threading
import time
import zipfile
import json
import re
import csv
from datetime import datetime

from qla_core.normalize_utils import (
    CLIENT_ID_TARGET_FIELDS,
    format_qladmin_mclientid,
    format_qladmin_mpolicy,
)
from qla_core.quikridr_decimal_emit import apply_quikridr_decimal_emit
from qla_core.rate_dbf_schema import map_rider_uwclass
from qla_core.schema_constants import (
    QUIKPLAN_SCHEMA,
    QUIKACTG_SCHEMA,
    QUIKLOAN_SCHEMA,
    QUIKREIN_SCHEMA,
    QUIKRMST_SCHEMA,
    QUIKBENH_SCHEMA,
    QUIKLIST_SCHEMA,
)
from qla_core import run_logging as RL
from qla_core.quikconvert_tagline import (
    APP_PRIMARY_TAGLINE,
    QUIKCONVERT_TAGLINES,
    TAGLINE_ROTATION_INTERVAL_MS,
    TaglineRotator,
)
from qla_core.quikplan_converter import (
    convert_quikplan_to_output,
    prepare_quikplan_source,
    apply_rate_variation_flag_enrichment,
    apply_single_premium_payment_settings,
    apply_ploan_loanint_enrichment,
    apply_iswl_product_tags,
    _restore_authoritative_loanintx_from_source,
)
from qla_core.issue_a_plan_setup import apply_issue_a_plan_setup
from qla_core.cso_mortality_crosswalk import (
    apply_quikplan_cv_assumptions,
    default_crosswalk_path,
    is_iswl_mplan,
    iswl_mdepint_percent,
    load_cso_mortality_crosswalk,
)
from qla_core.cso_valuation_setup import (
    apply_quikplan_valuation_setup,
    default_valuation_setup_path,
    load_valuation_setup,
)
from qla_core.quikplan_source_loader import load_quikplan_source_csv
from qla_core.variation_classification import (
    VariationClassificationConfig,
    classify_all_plans,
    recommendations_by_plan,
    write_variation_audit_csv,
)
from qla_core.quikactg_converter import convert_quikactg_from_pactg
from qla_core.quikloan_converter import convert_quikloan_from_ploan, load_derivation_rules
from qla_core.quikbenh_loan_history_converter import (
    convert_quikbenh_loan_history_from_pactg,
    load_derivation_rules as load_benh_loan_rules,
    write_quikbenh_csv,
)
from qla_core.quikbenh_dividend_history_converter import (
    convert_quikbenh_dividend_history,
    load_dividend_rules as load_benh_dividend_rules,
    write_quikbenh_csv as write_benh_dividend_csv,
)
from qla_core.reinsurance_converter import convert_reinsurance_phase1, load_derivation_rules as load_reinsurance_derivation_rules
from qla_core import rate_emit as RE
from qla_core.quikmemo_converter import convert_quikmemo_from_pnote_pense
from qla_core.quikmemo_dbf_generator import write_quikmemo_dbf
from qla_core.quikdate_converter import emit_quikdate_csv
from qla_core.quiklist_converter import emit_quiklist_csv
from qla_core.modal_premium_factors import (
    apply_modal_factors_to_quikplan as apply_issue21j_modal_factors,
    apply_modal_policy_fees_to_quikridr,
    apply_plan_modal_factors_to_quikmstr,
    apply_pac_gl85_modal_overrides,
    append_issue21j_conversion_memos,
    blank_ann_annual_ppu,
    format_mprem_ppu,
    load_modal_factor_mapping,
    issue139_fee_class,
    policy_fees_suppressed,
    suppress_policy_fees,
)
from qla_core.issue21_open_item_decisions import (
    apply_ul_fund_balance_to_quikridr_row,
    build_premium_basis_totals,
    build_ul_fund_balance_cache,
    resolve_ppben_path,
    resolve_ppbentyp_extract_path,
    write_premium_basis_report,
)
from qla_core.issue21f_premium_adjustment import apply_issue21f_conversion_adjustments
from qla_core.quikmstr_active_phase_status import (
    bare_status_map_from_trans_map,
    build_ppben_phase_cache,
    select_mstatus_from_active_phase,
)
from qla_core.issue121_art_no_eti import (
    build_art_lifepro_policy_cache,
    should_suppress_art_put_nfo,
)
from qla_core.crosswalk_enrichment import resolve_crosswalk_overlay_config
from qla_core.product_catalog_authority import (
    allow_legacy_mplan_fallback,
    build_authoritative_mplan_resolver,
    closed_mplan_authority_enabled,
    load_crosswalk_authority,
    load_quikplan_plan_set,
    resolve_authoritative_mplan,
)
from qla_core.mplan_authority import (
    apply_mplan_emit_filter,
    resolution_to_trace_row,
    validate_emitted_quikridr,
    write_p3e_governance_outputs,
    write_p3f_governance_outputs,
)
from qla_core.lifepro_source_resolver import resolve_table_source, expected_legacy_filename, resolve_quikmemo_sources, resolve_reinsurance_sources
from qla_core.sl_benefit_governance import (
    SL_BENEFIT_TYPE,
    build_sl_suppression_audit_rows,
    load_sl_table_code_cache,
    resolve_ppbentyp_path,
    write_sl_suppression_audit,
)
from qla_core.claims_emit_enhancements import (
    apply_claims_emit_enhancements,
    build_plan_metadata_lookup,
    validate_claims_emit_enhancements,
    write_claims_emit_enhancement_validation,
)
from qla_core.issue78_quikclmp_recovery import (
    recover_missing_quikclmp_payments,
    write_recovery_audit,
)
from qla_core.issue79_claimstat_remap import (
    remap_quikclms_claimstat,
    write_remap_audit,
)
from qla_core.issue85_claim_header_structure import (
    apply_issue85_header_structure,
    write_structure_audits,
)
from qla_core.issue84_track_a_header_backfill import (
    backfill_quikclms_headers_from_payees,
    write_money_field_audit,
)
from qla_core.issue134_claim_memo_overlay import (
    apply_issue134_claim_memos,
    write_issue134_orphan_audit,
)
from qla_core.issue135_mintamt_zero import apply_issue135_mintamt_zero
from qla_core.issue135_cso_claims_expansion import (
    apply_issue135_cso_claims_expansion,
    write_issue135_expansion_audits,
)
from qla_core.claims_payee_mseq_align import (
    ClaimsPayeeMseqAlignError,
    align_claims_csv_dir,
)

# --- Phase 18A–20: Claims orchestration, UAT handoff/emit/batch/DBF, MPOLICY validation ---
VALID_RUN_MODES = ("UAT", "PRODUCTION", "DISABLED")
DEFAULT_RUN_MODE = "UAT"
DEFAULT_ORCHESTRATION_TIMEOUT_SECONDS = 600
CLAIMS_TABLE_IDS = ("quikclms", "quikclmp")

# Paid-Up Addition rider products (PLAN_CODE authority) — inherit Phase 1 MPLAN/MEXPRY/MPAYUP.
PAID_UP_ADDITION_PRODUCTS = frozenset({
    "280PUA",
    "121PUA",
    "1970PA",
    "170PUA",
    "165PUA",
    "185PUA",
    "261PUA",
    "1OLPUA",
    "1POPUA",
    "265PUA",
})
# LifePRO PPBEN PLAN_CODE labels not present in Master_Crosswalk (catalog authority elsewhere).
PAID_UP_ADDITION_LIFEPRO_SOURCE_CODES = frozenset({
    "970 PUA",
})
QUIKCLMS_SCHEMA = [
    "MPOLICY", "MPHASE", "CLAIMNUM", "CLAIMSTAT", "DTOFDEATH", "RPTDATE", "PDDATE",
    "MPAID", "MFACE", "DIVIDENDS", "LOAN", "NETDB", "PREMIUM", "SUSPENSE", "ADJUST",
    "CAUSE", "MEMOTEXT", "ORIGSTTUS", "ACCPTDATE", "MCONTEST", "MINTST", "MINTDAYS",
    "MINTRATE", "MINTAMT", "MSURRCHG", "MSEQ", "MHOLDINT", "MFEDTAX", "MSTTAX",
    "MCLMPNDLTR", "MFACPMT", "MPHPAIDTO",
]
QUIKCLMP_SCHEMA = [
    "MPOLICY", "MPHASE", "MCHECKNO", "MAMOUNT", "MPAYNAME", "MPAYADDR1", "MPAYADDR2",
    "MPAYCITY", "MPAYST", "MPAYZIP", "MPAYZIP2", "MTIN", "MBANKNO", "MHDPMT", "MHDCODE",
    "MCHKDATE", "MPMTDATE", "MSEQ", "MHOLDINT", "MFEDTAX", "MSTTAX", "MGROSS", "MDOB",
    "MGENDER", "MCOUNTRY",
]
GOVERNANCE_LOG_VIEWS = {
    "business_exclusion_log.csv": {
        "title": "Business Exclusion Log (read-only preview)",
        "columns": ["record_type", "blocker_category", "reason_excluded", "business_explanation"],
    },
    "representative_issue_examples.csv": {
        "title": "Representative Issue Examples (read-only preview)",
        "columns": ["example_category", "before_status", "after_status", "why_issue_occurred", "remediation_path"],
    },
    "governance_exception_catalog.csv": {
        "title": "Governance Exception Catalog (read-only preview)",
        "columns": ["blocker_category", "exception_count", "business_explanation", "governance_status"],
    },
}
UAT_PACKAGE_CATEGORIES = {
    "01_uat_candidate_data": [
        "uat_candidate_quikclms.csv",
        "uat_candidate_quikclmp.csv",
        "uat_candidate_summary.txt",
        "uat_candidate_metrics.csv",
    ],
    "02_deferred_governance": [
        "deferred_governance_claims.csv",
        "deferred_governance_payments.csv",
        "governance_hold_summary.txt",
        "governance_population_metrics.csv",
    ],
    "03_business_review_logs": [
        "business_exclusion_log.csv",
        "governance_exception_catalog.csv",
        "remediation_recommendation_log.csv",
        "representative_issue_examples.csv",
        "replay_success_examples.csv",
        "unresolved_issue_examples.csv",
    ],
    "04_executive_reporting": [
        "executive_uat_dashboard.csv",
        "governance_kpi_summary.csv",
        "blocker_trend_analysis.csv",
        "phase17_executive_summary.txt",
        "business_review_workbench_summary.txt",
        "business_exclusion_summary.txt",
        "business_example_summary.txt",
    ],
    "05_business_workbenches": [
        "surrender_review_workbench.csv",
        "orphan_review_workbench.csv",
        "high_priority_business_decisions.csv",
    ],
}
UAT_PACKAGE_SUBDIR = "claims_uat_packages"
CLAIMS_REVIEW_HOLD_MANIFEST = "claims_review_hold_manifest.csv"
CLAIMS_UAT_DBF_SUBDIR = "claims_uat_dbf"
QUIKCLMS_UAT_DBF_NAME = "QUIKCLMS_PHASE19_UAT.DBF"
QUIKCLMP_UAT_DBF_NAME = "QUIKCLMP_PHASE19_UAT.DBF"
PHASE11_CLMS_PROTOTYPE_DBF = "QUIKCLMS_PROTOTYPE.DBF"
PHASE11_CLMP_PROTOTYPE_DBF = "QUIKCLMP_PROTOTYPE.DBF"
CLAIMS_UAT_DBF_MANIFEST = "claims_uat_dbf_manifest.csv"
CLAIMS_UAT_DBF_SUMMARY = "claims_uat_dbf_generation_summary.txt"
CLAIMS_UAT_DBF_ALIGNMENT_MANIFEST = "claims_uat_dbf_alignment_manifest.csv"
CLAIMS_UAT_DBF_ALIGNMENT_SUMMARY = "claims_uat_dbf_alignment_summary.txt"
CLAIMS_UAT_DBF_ROLLBACK_REF = "rollback_snapshot_reference.txt"
UAT_DBF_GOVERNANCE_POPULATION = "UAT_EMITTED_VALIDATED_ONLY"
PHASE21B_UAT_DBF_LINEAGE = "PHASE21B_UAT_DBF_FROM_EMITTED_CSV"
PHASE22_SEMANTIC_GOVERNANCE_LINEAGE = "PHASE22A_SEMANTIC_GOVERNANCE_HOLD|PHASE22B_QLADMIN_DOMAIN_ALIGNMENT|PHASE22C_CLAIM_DOMAIN_ELIGIBILITY"
SEMANTIC_HOLD_CATEGORY = "SEMANTIC_PSEUDO_CLAIM"
SEMANTIC_HOLD_EXPLANATION = (
    "Non-claim loan accounting (LifePRO 04xx Borrowed Money: 0411-0417, 0451) lacks claim payout/benefit "
    "semantics and belongs in QuikLoan/Loan History per QLAdmin Help — not QUIKCLMS Death Claims. "
    "Held from UAT emit pending business review — not deleted."
)
SEMANTIC_HOLD_REMEDIATION = (
    "Business review required. Future target domain: QuikLoan (MLOANACCR/MLOANBAL). "
    "Do not auto-convert in Phase 22. Set QLA_SEMANTIC_GOVERNANCE_HOLD=0 to rollback emit filter."
)
CLAIMS_CROSS_TABLE_VALIDATION_REPORT = "claims_cross_table_validation_report.csv"
CLAIMS_CROSS_TABLE_VALIDATION_SUMMARY = "claims_cross_table_validation_summary.txt"
CLAIMS_EMIT_ENHANCEMENT_VALIDATION_REPORT = "claims_emit_enhancement_validation.csv"
CLAIMS_EMIT_ENHANCEMENT_VALIDATION_SUMMARY = "claims_emit_enhancement_validation_summary.txt"
PHASE20_RULEBOOK_LINEAGE = "PHASE20_MPOLICY_CROSS_TABLE_VALIDATION"
PHASE20_HOLD_EXPLANATION = (
    "The claim or payment references a policy that was not present in the converted policy "
    "master file, so it was held from UAT output."
)
PHASE20_REMEDIATION = (
    "Review policy conversion/crosswalk. Confirm whether the policy should exist in "
    "quikmstr.csv before claim is included in UAT."
)
PHASE21_RULEBOOK_LINEAGE = "PHASE21_UAT_QLA_EMIT|PHASE10_DERIVATION|Sync_Rulebook"
CLAIMS_MONEY_FIELDS = {
    "quikclms": {
        "MPAID", "MFACE", "DIVIDENDS", "LOAN", "NETDB", "PREMIUM", "SUSPENSE", "ADJUST",
        "MINTAMT", "MHOLDINT", "MFEDTAX", "MSTTAX",
    },
    "quikclmp": {"MAMOUNT", "MHOLDINT", "MFEDTAX", "MSTTAX", "MGROSS"},
}
CLAIMS_PAYMENT_MHDPMT_MAP = {
    "DEATH": "C",
    "CLAIM": "C",
    "DISBURSEMENT": "C",
    "DEATH_CLAIM_PAYOUT": "C",
    "CLAIM_PAYMENT": "C",
    "CASH_DISBURSEMENT": "C",
}
PRODUCT_SETUP_RUNNER_TIMEOUT = 120
PRODUCT_SETUP_VALIDATION_DIR = os.path.join("plan_analysis", "phase_p2a_validation")
PRODUCT_SETUP_VALIDATION_SUMMARY = "validation_summary.md"
PRODUCT_SETUP_DIAGNOSTICS_MANIFEST = os.path.join("plan_governance", "manifests", "product_governance_diagnostics.csv")
RATE_LOADER_RUNNER_TIMEOUT = 900
RATE_LOADER_RUNNER = os.path.join("plan_governance", "phase_r5_rate_loader_runner", "rate_loader_gui_runner.py")
QUIKISRR_EMIT_RUNNER_TIMEOUT = 600
QUIKISRR_EMIT_RUNNER = os.path.join("Issue_Log_Items", "Issue_34", "tools", "quikisrr_pr7_emit.py")
APP_VERSION = "v58.93"
DBF_APPEND_TOOL_INPUT = r"C:\Users\warren\Desktop\DBF_Append_Tool\input"
DBF_APPEND_TOOL_OUTPUT = r"C:\Users\warren\Desktop\DBF_Append_Tool\output"
DBF_APPEND_TOOL_BAT = r"C:\Users\warren\Desktop\DBF_Append_Tool\run_app.bat"
APP_BRAND = "QUIKConvert"
APP_TAGLINE = APP_PRIMARY_TAGLINE


class QLAdminEnterpriseIntegrationSuite:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_BRAND} — {APP_TAGLINE}  {APP_VERSION}")
        self.root.geometry("1200x980")
        self.root.minsize(1080, 820)
        self._tagline_rotator = None

        # QUIKConvert / QLAdmin-aligned red + white theme
        self.bg_main = "#F5F5F5"
        self.bg_card = "#FFFFFF"
        self.bg_nav = "#B91C1C"
        self.bg_nav_muted = "#FECACA"
        self.brand_red = "#B91C1C"
        self.brand_red_dark = "#7F1D1D"
        self.brand_red_deep = "#450A0A"
        self.ui_strip_bg = "#FFF8F8"
        self.ui_strip_border = "#E5E7EB"
        self.ui_status_ok = "#15803D"
        self.ui_status_warn = "#D97706"
        self.ui_status_err = "#B91C1C"
        self.ui_status_muted = "#6B7280"
        self.accent = "#7F1D1D"
        self.btn_action = "#DC2626"
        self.btn_batch = "#B91C1C"
        self.btn_backup = "#991B1B"
        self.btn_product = "#9F1239"
        self.btn_rates = "#7F1D1D"
        self.btn_gov = "#450A0A"
        self.btn_balancing = "#15803D"
        self.btn_secondary = "#6B7280"
        self.text_color = "#374151"
        self.root.configure(bg=self.bg_main)

        self.TABLE_SCHEMAS = {
            "quikplan": QUIKPLAN_SCHEMA,
            "quikmstr": ["MPOLICY","MSTATUS","MSTATDATE","MISSDT","MPAIDTO","MBILLTO","MNFOPT","MDIVOPT","MBILLFRM","MBILLDAY","MACCTNO","MBANKNO","MPREBILL","MMODE","MMODEPREM","MSEMI","MQTRL","MMTHD","MMTHB","MINQUIRY","MISSUEST","MBFCY","MGROUP","MPRIMID","MOWNRID","MPAYRID","MASGNID","MBENPID","MBENCID","MAPPDATE","MSUBMDATE","MRELDATE","MRELOTHER","MORIGBILL","MORIGMODE","MISSCNTRY","MOWNCID","MACHCNT","MACHNXTDT","MRESSTATE","MBLLDOM","MSPCODE","MISSCLASS","MMSMBI","MORGBLLDOM"],
            "quikspec": ["MPOLICY", "VANISH", "VANISHDT", "RESSTATE"],
            "quikclnt": ["MCLIENTID", "MTYPE", "MTAXID", "MTAXIDTYPE", "MTITLE", "MFNAME", "MMNAME", "MLNAME", "MSUFFIX", "MADDR1", "MADDR2", "MCITY", "MSTATE", "MZIP", "MZIP2", "MCOUNTRY", "MPHONEHOME", "MPHONEOFC", "MPHOFCEXT", "MPHONECELL", "MPHONEFAX", "MEMAIL", "MDOB", "MSEX", "MMEMBERID", "MLANGUAGE", "MPDFPSSWD", "MEMAILCORR", "MVALID", "MDNC", "MOFAC", "MMEMBERDT", "MMSMBI", "MFOREIGN", "MOCCODE"],
            "quikridr": ["MPOLICY", "MPHASE", "MPHSTAT", "MLASTANN", "MANNSTAT", "MPHDOB", "MSEX", "MPLAN", "MPAR", "MEFFDATE", "MEXPRY", "MPAYUP", "MAGE", "MUNIT", "MVPU", "MPREM", "MANNLFEE", "MSEMIFEE", "MQTRLFEE", "MMTHDFEE", "MMTHBFEE", "MRRULE", "MCOMMID", "MCV0", "MCV1", "MCV2", "MSAVEAGE", "MSAVEUNIT", "MSAVEVPU", "MSAVEPREM", "MRIDRID", "MSSN", "MUWCLASS", "MBAND", "MSAVESTAT", "MCOMMPREM", "MSPCODE", "MLOCKTYP", "MLOCKDT", "MUNLCKDT"],
            "quikbenf": ["MPOLICY", "MBENFID", "MTYPE", "MRELATION", "MSPLIT"],
            "quikclid": ["MCLIENTID", "MPOLICY", "MPHASE", "MRELATION"],
            "quikdvdp": ["MPOLICY", "MDEPOSIT", "MINTYTD", "MDEPINT", "MINTDATE"],
            "quikdvpr": ["MPOLICY", "MDATE", "MDIV"],
            "quikprmh": ["MPOLICY", "DATEPAID", "RENEWAL", "PREMIUM", "MLIFE", "MTERM", "MSUPP", "MANN", "MHEALTH", "XS", "MPAIDTO", "POSTDATE", "MPOSTDATE", "MSOURCE", "MBATCH", "USER_ID", "MBILLFRM", "MMODEPD"],
            "quikactg": QUIKACTG_SCHEMA,
            "quikloan": QUIKLOAN_SCHEMA,
            "quikbenh": QUIKBENH_SCHEMA,
            "quikrein": QUIKREIN_SCHEMA,
            "quikrmst": QUIKRMST_SCHEMA,
            "quikagts": ["MAGENT", "MAGTNAME", "MAGTADDR1", "MAGTADDR2", "MAGTCITY", "MAGTST", "MAGTZIP", "MAGTZIP2", "MAGTSSN", "MAGTFEIN", "MCOMP", "MAGENCY", "MAGCYNAME", "MDATE", "MAGTACCT", "MAGTPHONE", "MAGTFAX", "MAGTCELL", "MAGTOFCE", "MAGTEMAIL", "MEMOTEXT", "MSUPPRESS", "MCOMMGRP", "MOTHNAME", "MPREMACCT", "MSTATUS", "MAGTNPN", "MTAXIDTYPE"],
            "quikmemo": ["MEMOKEY", "MEMOTEXT"],
            "quikclms": QUIKCLMS_SCHEMA,
            "quikclmp": QUIKCLMP_SCHEMA,
            "quiklist": QUIKLIST_SCHEMA,
        }

        self.RUN_MODE = self._resolve_run_mode()
        self.CLAIMS_ORCHESTRATION = self._build_claims_orchestration_config()
        
        self.is_running = False
        self.start_time = None
        self.debug_rel_fallback = os.environ.get("QLA_DEBUG_REL_FALLBACK", "").strip().lower() in ("1", "true", "yes")
        self._last_uat_dbf_result = None
        self._last_cross_table_validation = None
        self._last_product_setup_result = None
        self._last_governance_report = None
        self._ui_last_run_at = None
        self._ui_last_governance_at = None
        self._ui_run_state = "Ready"
        self.setup_ui()

    def setup_ui(self):
        self._setup_top_nav()
        self._setup_uat_status_banner()

        card = tk.LabelFrame(
            self.root, text=" System Configuration ", bg=self.bg_card, fg=self.accent,
            padx=20, pady=14, font=("Segoe UI", 10, "bold"),
            highlightbackground=self.ui_strip_border, highlightthickness=1, bd=0, labelanchor="nw",
        )
        card.pack(padx=24, fill="x", pady=(0, 8))

        base_dir = self._repo_root()
        parent_dir = os.path.dirname(os.path.abspath(__file__))
        mig_map = os.path.join(base_dir, "QLA_Migration", "Mapping")
        mig_src = os.path.join(base_dir, "QLA_Migration", "Source", "quikmstr.csv")
        mig_out = os.path.join(base_dir, "QLA_Migration", "Output")

        def auto_locate(search_paths, keywords):
            for s_path in search_paths:
                for root, dirs, files in os.walk(s_path):
                    if root.count(os.sep) - s_path.count(os.sep) > 3:
                        del dirs[:]
                    dirs[:] = [
                        d for d in dirs
                        if not any(m in os.path.join(root, d).lower() for m in [
                            "expectred_outputs", "expected_outputs", "z_sourcefortesting",
                        ])
                    ]
                    for file_name in files:
                        f_lower = file_name.lower()
                        if f_lower.endswith(".csv") and all(k in f_lower for k in keywords):
                            if not any(bad in f_lower for bad in ['copy', 'old', 'backup', 'archive']):
                                full = os.path.normpath(os.path.join(root, file_name))
                                if "expectred_outputs" not in full.lower():
                                    return full
            return ""

        search_dirs = [mig_map, base_dir, parent_dir]

        default_trans = self._first_existing_file(
            os.path.join(mig_map, "Master_Value_Translation.csv"),
            auto_locate(search_dirs, ["master", "translation"]),
        )
        default_cw = self._first_existing_file(
            os.path.join(mig_map, "Master_Crosswalk.csv"),
            auto_locate(search_dirs, ["master", "crosswalk"]),
        )
        default_src = mig_src if os.path.isfile(mig_src) else ""
        default_out = mig_out if os.path.isdir(mig_out) else ""
        mig_cfg = os.path.join(base_dir, "QLA_Migration", "Configs", "Sync_Rulebook_quikplan.csv")
        default_rule = mig_cfg if os.path.isfile(mig_cfg) else ""
        default_rel = os.path.join(mig_out, "quikclid.csv") if os.path.isfile(os.path.join(mig_out, "quikclid.csv")) else ""
        env_gov = os.environ.get("QLA_GOVERNANCE_DATA_DIR", "").strip()
        default_gov = env_gov if env_gov and os.path.isdir(env_gov) else default_out

        self.path_vars = {
            "Rule": [tk.StringVar(value=default_rule), "file", "Field Mapping (Rulebook):"],
            "Src": [tk.StringVar(value=default_src), "file", "Source Data File:"],
            "Trans": [tk.StringVar(value=default_trans), "file", "Value Translation (CSV):"],
            "CW": [tk.StringVar(value=default_cw), "file", "ID Crosswalk (CSV):"],
            "Rel": [tk.StringVar(value=default_rel), "file", "Relational File (quikclid):"],
            "Out": [tk.StringVar(value=default_out), "folder", "Output Directory:"],
            "GovData": [
                tk.StringVar(value=default_gov),
                "folder",
                "Governance Data Folder (CSV or DBF):",
            ],
        }

        self.path_display_vars = {}
        self._path_entries = {}
        for i, (key, settings) in enumerate(self.path_vars.items()):
            var, mode, label_text = settings
            disp = tk.StringVar(value=self._ui_short_path(var.get()))
            self.path_display_vars[key] = disp
            tk.Label(card, text=label_text, bg=self.bg_card, fg=self.text_color, font=("Segoe UI", 9, "bold")).grid(row=i, column=0, sticky="w", pady=3)
            entry = tk.Entry(card, textvariable=disp, width=72, bg=self.ui_strip_bg, fg=self.accent, borderwidth=1, relief="solid")
            entry.grid(row=i, column=1, padx=12, sticky="ew")
            self._path_entries[key] = entry
            self._ui_attach_tooltip(entry, lambda k=key: self.path_vars[k][0].get())
            self._ui_action_button(
                card, "Browse", self.btn_secondary, lambda v=var, m=mode, k=key: self.browse(v, m, k),
                width=10, pady=4,
            ).grid(row=i, column=2)
        card.grid_columnconfigure(1, weight=1)

        context = tk.Frame(
            self.root, bg=self.bg_card, padx=16, pady=10,
            highlightbackground=self.ui_strip_border, highlightthickness=1,
        )
        context.pack(padx=24, fill="x", pady=(0, 8))
        tk.Label(
            context, text="Conversion Target", bg=self.bg_card, fg=self.ui_status_muted,
            font=("Segoe UI", 8, "bold"),
        ).pack(side="left", padx=(0, 8))
        self.table_var = tk.StringVar()
        self.table_dropdown = ttk.Combobox(
            context, textvariable=self.table_var,
            values=[k for k in self.TABLE_SCHEMAS.keys() if k.startswith("quik")],
            width=42, state="readonly",
        )
        self.table_dropdown.pack(side="left", padx=(0, 12))
        self.table_dropdown.bind("<<ComboboxSelected>>", self.on_table_select)
        tk.Label(
            context, text="Used by Single Table Conversion", bg=self.bg_card,
            fg=self.ui_status_muted, font=("Segoe UI", 8),
        ).pack(side="left")
        self._ui_action_button(
            context, "FULL PROJECT BACKUP", self.btn_backup, self.create_snapshot, width=22,
        ).pack(side="right")

        progress_card = tk.Frame(
            self.root, bg=self.bg_card, padx=16, pady=12,
            highlightbackground=self.ui_strip_border, highlightthickness=1,
        )
        progress_card.pack(padx=24, fill="x", pady=(0, 8))
        progress_header = tk.Frame(progress_card, bg=self.bg_card)
        progress_header.pack(fill="x")
        tk.Label(
            progress_header, text="Run Progress", bg=self.bg_card, fg=self.accent,
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left")
        self.lbl_timer = tk.Label(
            progress_header, text="Elapsed: 00:00:00", bg=self.bg_card, fg=self.accent,
            font=("Consolas", 10, "bold"),
        )
        self.lbl_timer.pack(side="right")
        self.progress = ttk.Progressbar(progress_card, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", pady=(8, 6))
        self.stage_color_idle = self.text_color
        self.stage_color_success = self.ui_status_ok
        self.stage_color_error = self.ui_status_err
        self.lbl_stage = tk.Label(
            progress_card, text="Stage 0 — Ready", bg=self.bg_card, fg=self.stage_color_idle,
            font=("Segoe UI", 10, "bold"), anchor="w",
        )
        self.lbl_stage.pack(fill="x")
        self.lbl_stage_detail = tk.Label(
            progress_card, text="", bg=self.bg_card, fg=self.text_color,
            font=("Segoe UI", 9), anchor="w",
        )
        self.lbl_stage_detail.pack(fill="x", pady=(0, 2))
        self._progress_plan = None
        self._run_start_time = None

        self._setup_product_setup_panel()
        self._setup_rate_loader_panel()
        self._setup_diagnostics_panel()

        log_frame = tk.LabelFrame(
            self.root, text=" Activity Log ", bg=self.bg_card, fg=self.accent,
            padx=8, pady=6, font=("Segoe UI", 10, "bold"),
            highlightbackground=self.ui_strip_border, highlightthickness=1, bd=0, labelanchor="nw",
        )
        log_frame.pack(padx=24, pady=(0, 12), fill="both", expand=True)
        self.console = scrolledtext.ScrolledText(
            log_frame, height=12, bg=self.ui_strip_bg, fg="#1E293B",
            font=("Consolas", 9), relief="flat", borderwidth=0,
        )
        self.console.pack(fill="both", expand=True)
        self._refresh_governance_visibility()
        self._refresh_product_setup_visibility()
        self._refresh_rate_loader_visibility()
        self._ui_update_status_strip()

    def log(self, msg):
        self.console.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.console.see(tk.END)

    def _ui_short_path(self, path, max_len=58):
        if not path:
            return ""
        norm = os.path.normpath(str(path))
        if len(norm) <= max_len:
            return norm
        tail = os.path.basename(norm)
        if len(tail) + 6 <= max_len:
            return f"...{os.sep}{tail}" if len(norm) > len(tail) else tail
        return f"...{norm[-(max_len - 3):]}"

    def _ui_attach_tooltip(self, widget, text_getter):
        tip = {"win": None}

        def show(_event=None):
            text = text_getter() if callable(text_getter) else str(text_getter or "")
            if not text:
                return
            if tip["win"]:
                tip["win"].destroy()
            tip["win"] = tw = tk.Toplevel(widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{widget.winfo_rootx() + 12}+{widget.winfo_rooty() + widget.winfo_height() + 4}")
            tk.Label(
                tw, text=text, bg="#1E293B", fg="#F8FAFC",
                font=("Segoe UI", 8), padx=8, pady=4, justify="left",
            ).pack()

        def hide(_event=None):
            if tip["win"]:
                tip["win"].destroy()
                tip["win"] = None

        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)

    def _ui_sync_path_display(self, key=None):
        if not hasattr(self, "path_display_vars"):
            return
        keys = [key] if key else list(self.path_display_vars.keys())
        for k in keys:
            full = self.path_vars[k][0].get() if k in self.path_vars else ""
            self.path_display_vars[k].set(self._ui_short_path(full))

    def _ui_production_output_label(self, summary=None):
        prod_flag = self.CLAIMS_ORCHESTRATION.get("production_dbf_flag", "N")
        if prod_flag == "Y":
            return "Enabled"
        if summary and summary.get("run_mode") == "PRODUCTION":
            auth = self.CLAIMS_ORCHESTRATION.get("production_authorization_flag", "N")
            if auth == "Y":
                return "Authorized (Not Executed)"
        return "Disabled"

    def _ui_readiness_label(self, summary):
        status = (summary or {}).get("threshold_status", "Awaiting Data")
        mapping = {
            "NOT READY": "Pending Review",
            "NOT YET GENERATED": "Awaiting Data",
            "UAT REVIEW IN PROGRESS": "In Progress",
        }
        return mapping.get(status, status)

    def _ui_has_active_blocker(self, summary):
        if not summary:
            return False
        if summary.get("threshold_status") == "NOT READY":
            return True
        if summary.get("top_blocker"):
            return True
        return False

    def _ui_project_label(self):
        cfg = self.CLAIMS_ORCHESTRATION
        go_live = cfg.get("go_live_target", "2026-09-01")
        return f"{APP_BRAND}  |  Enterprise Conversion  |  Go-Live {go_live}"

    def _ui_source_package_status(self):
        src = ""
        if hasattr(self, "path_vars"):
            src = self.path_vars.get("Src", [None])[0].get().strip()
        if not src:
            src_dir = self._migration_source_dir()
            if os.path.isdir(src_dir):
                csv_count = sum(1 for f in os.listdir(src_dir) if f.lower().endswith(".csv"))
                return f"Source folder ready ({csv_count} CSV files)" if csv_count else "Source folder empty"
            return "Source not configured"
        if os.path.isfile(src):
            return f"Ready — {os.path.basename(src)}"
        return "Source file missing"

    def _ui_output_readiness_label(self):
        out_dir = self._migration_output_dir()
        if hasattr(self, "path_vars"):
            custom = self.path_vars.get("Out", [None])[0].get().strip()
            if custom:
                out_dir = custom
        if not out_dir or not os.path.isdir(out_dir):
            return "Output folder not found"
        table_csvs = [
            f for f in os.listdir(out_dir)
            if f.lower().endswith(".csv") and f.lower().startswith("quik")
        ]
        rates_dir = os.path.join(out_dir, "rates")
        rate_count = 0
        if os.path.isdir(rates_dir):
            rate_count = sum(1 for f in os.listdir(rates_dir) if f.lower().endswith(".csv"))
        if not table_csvs:
            return "Awaiting conversion run"
        label = f"{len(table_csvs)} table CSV(s) ready"
        if rate_count:
            label += f" + {rate_count} rate table(s)"
        return label

    def _ui_governance_status_label(self):
        report = getattr(self, "_last_governance_report", None)
        if report is None:
            return "Not yet audited"
        status = getattr(report, "overall_status", None)
        failed = int(getattr(report, "failed_count", 0) or 0)
        errors = int(getattr(report, "error_count", 0) or 0)
        findings = len(getattr(report, "findings", None) or [])
        if status == "PASS" and findings == 0:
            return "Governance PASS"
        return (
            f"Governance {status or 'DONE'}: findings={findings} "
            f"(fail={failed} err={errors})"
        )

    def _ui_format_timestamp(self, ts):
        return ts if ts else "—"

    def _ui_run_state_color(self):
        state = getattr(self, "_ui_run_state", "Ready")
        if state == "Success":
            return self.ui_status_ok
        if state == "Failed":
            return self.ui_status_err
        if state == "Running":
            return self.ui_status_warn
        return self.accent

    def _ui_record_run_timestamp(self, state):
        self._ui_last_run_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._ui_run_state = state
        self._ui_update_status_strip()

    def _ui_record_governance_timestamp(self):
        self._ui_last_governance_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._ui_update_status_strip()

    def _ui_open_output_folder(self):
        out_dir = self.path_vars["Out"][0].get().strip() if hasattr(self, "path_vars") else ""
        if not out_dir or not os.path.isdir(out_dir):
            out_dir = self._migration_output_dir()
        if not os.path.isdir(out_dir):
            messagebox.showwarning("Open Output", f"Output folder not found:\n{out_dir}")
            return
        try:
            os.startfile(out_dir)  # noqa: S606 — Windows operator folder open
        except OSError as exc:
            messagebox.showerror("Open Output", f"Could not open folder:\n{out_dir}\n\n{exc}")

    def _ui_open_reports_folder(self):
        reports = self._reports_dir()
        os.makedirs(reports, exist_ok=True)
        try:
            os.startfile(reports)  # noqa: S606
        except OSError as exc:
            messagebox.showerror("Open Reports", f"Could not open folder:\n{reports}\n\n{exc}")

    def _ui_update_status_strip(self, summary=None):
        if summary is None:
            summary = self._build_governance_summary()
        env = summary.get("run_mode", self.RUN_MODE)
        prod_out = self._ui_production_output_label(summary)
        readiness = self._ui_readiness_label(summary)
        go_live = summary.get("go_live_target", self.CLAIMS_ORCHESTRATION.get("go_live_target", ""))
        if hasattr(self, "env_status_var"):
            self.env_status_var.set(f"Environment: {env}")
        if hasattr(self, "prod_output_status_var"):
            self.prod_output_status_var.set(f"Production Output: {prod_out}")
        if hasattr(self, "readiness_status_var"):
            self.readiness_status_var.set(f"Readiness Review: {readiness}")
        if hasattr(self, "golive_status_var"):
            self.golive_status_var.set(f"Go-Live Target: {go_live}")
        if hasattr(self, "dash_project_var"):
            self.dash_project_var.set(self._ui_project_label())
        if hasattr(self, "dash_source_var"):
            self.dash_source_var.set(self._ui_source_package_status())
        if hasattr(self, "dash_output_var"):
            self.dash_output_var.set(self._ui_output_readiness_label())
        if hasattr(self, "dash_validation_var"):
            self.dash_validation_var.set(self._ui_governance_status_label())
        if hasattr(self, "dash_last_run_var"):
            self.dash_last_run_var.set(self._ui_format_timestamp(self._ui_last_run_at))
        if hasattr(self, "dash_last_validation_var"):
            self.dash_last_validation_var.set(self._ui_format_timestamp(self._ui_last_governance_at))
        if hasattr(self, "dash_run_state_var"):
            self.dash_run_state_var.set(getattr(self, "_ui_run_state", "Ready"))
        if hasattr(self, "dash_run_state_badge"):
            self.dash_run_state_badge.config(fg=self._ui_run_state_color())
        if self._ui_has_active_blocker(summary):
            if hasattr(self, "gov_alert_badge"):
                self.gov_alert_badge.config(
                    text="Review item pending — open Advanced / Diagnostics",
                    fg=self.ui_status_warn,
                )
        elif hasattr(self, "gov_alert_badge"):
            self.gov_alert_badge.config(text="", fg=self.ui_status_muted)

    def _ui_toggle_diagnostics(self):
        if self.diagnostics_visible.get():
            self.diagnostics_body.pack(fill="x", pady=(4, 0))
        else:
            self.diagnostics_body.pack_forget()

    PATH_EXCLUDED_DIR_MARKERS = (
        "expectred_outputs", "expected_outputs", "copy", "old", "backup", "archive",
        "__pycache__", ".git", "node_modules", "z_sourcefortesting",
    )

    def _app_base_dir(self):
        return os.path.dirname(os.path.abspath(__file__))

    def _repo_root(self):
        """Repository root (parent when app.py lives under QLA_Migration/)."""
        base = self._app_base_dir()
        parent = os.path.dirname(base)
        if os.path.basename(os.path.normpath(base)).lower() == "qla_migration":
            if os.path.isdir(os.path.join(parent, "qla_core")):
                return parent
        return base

    def _migration_root(self):
        return os.path.normpath(os.path.join(self._repo_root(), "QLA_Migration"))

    def _migration_source_dir(self):
        return os.path.normpath(os.path.join(self._migration_root(), "Source"))

    def _migration_output_dir(self):
        return os.path.normpath(os.path.join(self._migration_root(), "Output"))

    def _migration_mapping_dir(self):
        return os.path.normpath(os.path.join(self._migration_root(), "Mapping"))

    def _migration_configs_dir(self):
        return os.path.normpath(os.path.join(self._migration_root(), "Configs"))

    def _emit_quikbenh_dividend_history(self, pactg_path, src_base, cw_map):
        """Issue #114: PACTG dividend elections + PPBENTYP lifetime total -> QuikBenh types 1-5."""
        ppbentyp_path = resolve_ppbentyp_extract_path(src_base)
        if not ppbentyp_path:
            ppbentyp_path = resolve_ppbentyp_extract_path(self._migration_source_dir())
        if not ppbentyp_path:
            self.log("Issue #114: skipped — PPBENTYP extract not found")
            return

        self.log("Working Table: QUIKBENH (PACTG + PPBENTYP → dividend history Issue #114)")
        self.log(f"  PPBENTYP lifetime source: {ppbentyp_path}")
        out_dir = self.path_vars["Out"][0].get()
        existing_benh = os.path.normpath(os.path.join(out_dir, "quikbenh.csv"))
        phase_dir = os.path.normpath(
            os.path.join(self._app_base_dir(), "plan_analysis", "phase_benh_dividend_history")
        )
        try:
            merged_df, dividend_df, plug_df, exceptions_df, stats = (
                convert_quikbenh_dividend_history(
                    pactg_path,
                    ppbentyp_path,
                    cw_map=cw_map,
                    rules=load_benh_dividend_rules(),
                    output_dir=phase_dir,
                    existing_benh_path=existing_benh if os.path.isfile(existing_benh) else None,
                    reports_dir=os.path.normpath(os.path.join(self._migration_root(), "Reports")),
                )
            )
        except Exception as e:
            self.log(f"Warning: Issue #114 dividend history failed - {e}")
            return

        self.log(
            f"QUIKBENH Issue #114: {len(dividend_df)} PACTG dividend rows + "
            f"{len(plug_df)} conversion adjustments -> {stats.get('merged_rows', 0)} merged; "
            f"reconciled {stats.get('reconciled_dollars', 0):,.2f} of "
            f"{stats.get('lifetime_target_dollars', 0):,.2f}; "
            f"exceptions={len(exceptions_df)}; "
            f"preserved non-dividend rows={stats.get('existing_preserved_rows', 0)}; "
            f"reports -> {phase_dir}"
        )
        if os.environ.get("QLA_QUIKBENH_DIVIDEND_WRITE_OUTPUT", "").strip() == "1":
            out_path = os.path.normpath(os.path.join(out_dir, "quikbenh.csv"))
            write_benh_dividend_csv(merged_df, out_path)
            self.log(f"GATED OUTPUT: {out_path} ({len(merged_df)} rows)")

    def _is_excluded_path(self, path):
        lower = os.path.normpath(path).lower()
        return any(marker in lower for marker in self.PATH_EXCLUDED_DIR_MARKERS)

    def _first_existing_file(self, *candidates):
        for path in candidates:
            if path and os.path.isfile(path):
                return os.path.normpath(path)
        return ""

    def _find_migration_file(self, filename, *, search_dirs=None, exclude_output_paths=False):
        preferred_dirs = search_dirs or []
        for folder in preferred_dirs:
            if not folder or self._is_excluded_path(folder):
                continue
            candidate = os.path.normpath(os.path.join(folder, filename))
            if exclude_output_paths and "output" in candidate.lower():
                continue
            if os.path.isfile(candidate):
                return candidate

        matches = []
        for s_path in [self._app_base_dir(), os.path.dirname(self._app_base_dir())]:
            if not os.path.exists(s_path):
                continue
            for root, dirs, files in os.walk(s_path):
                dirs[:] = [
                    d for d in dirs
                    if not self._is_excluded_path(os.path.join(root, d))
                ]
                for f in files:
                    if f.lower() != filename.lower():
                        continue
                    full = os.path.normpath(os.path.join(root, f))
                    if exclude_output_paths and "output" in full.lower():
                        continue
                    if self._is_excluded_path(full):
                        continue
                    matches.append(full)

        migration_matches = [m for m in matches if "qla_migration" in m.lower()]
        if migration_matches:
            return migration_matches[0]
        return matches[0] if matches else ""

    def _resolve_batch_src_base(self, src_input):
        migration_src = self._migration_source_dir()
        if src_input:
            norm_input = os.path.normpath(src_input)
            explicit = norm_input if os.path.isdir(norm_input) else os.path.dirname(norm_input)
            if os.path.isdir(explicit):
                # Dated packages (e.g. Source\12312025_Data) must win over Source root.
                try:
                    mig_abs = os.path.abspath(migration_src)
                    exp_abs = os.path.abspath(explicit)
                    if (
                        os.path.isdir(mig_abs)
                        and exp_abs != mig_abs
                        and os.path.commonpath([exp_abs, mig_abs]) == mig_abs
                    ):
                        return exp_abs
                except ValueError:
                    pass
                if "qla_migration" in norm_input.lower() and os.path.isdir(migration_src):
                    return migration_src
                return explicit
        if os.path.isdir(migration_src):
            return migration_src
        return os.path.dirname(os.path.abspath(__file__))

    def _resolve_batch_rule_base(self, rule_input):
        migration_cfg = self._migration_configs_dir()
        if rule_input:
            rule_dir = os.path.dirname(os.path.normpath(rule_input))
            if "qla_migration" in rule_dir.lower() and os.path.isdir(migration_cfg):
                return migration_cfg
            if os.path.isdir(rule_dir):
                return rule_dir
        if os.path.isdir(migration_cfg):
            return migration_cfg
        return self._app_base_dir()

    def _resolve_table_source_path(self, table_id, src_dir):
        """Resolve LifePRO or legacy source CSV for a conversion table."""
        path, label = resolve_table_source(src_dir, table_id)
        if path and label:
            self.log(f"  Source resolved ({label})")
        return path

    def _resolve_rna_source_path(self, src_dir):
        """Resolve the active RelationshipNameAddress source, including dated extracts."""
        path, label = resolve_table_source(src_dir, "quikclnt")
        if path and label:
            self.log(f"  RNA source resolved ({label})")
        return path

    def _build_client_name_lookup(self, rel_name_cache=None, quikclnt_path=None):
        """Build NAME_ID -> name hints for rel_map duplicate-role resolution."""
        lookup = {}
        if rel_name_cache:
            for cid, row in rel_name_cache.items():
                first = str(row.get("INDIVIDUAL_FIRST", "")).strip()
                last = str(row.get("INDIVIDUAL_LAST", "")).strip()
                lookup[self.normalize(cid)] = {"first": first, "last": last}
        if quikclnt_path and os.path.isfile(quikclnt_path):
            try:
                clnt = pd.read_csv(quikclnt_path, dtype=str).fillna("")
                clnt.columns = [c.strip().upper() for c in clnt.columns]
                id_col = "MCLIENTID" if "MCLIENTID" in clnt.columns else None
                if id_col:
                    for _, row in clnt.iterrows():
                        cid = self.normalize(row.get(id_col, ""))
                        if not cid:
                            continue
                        first = str(row.get("MFNAME", "")).strip()
                        last = str(row.get("MLNAME", "")).strip()
                        if cid not in lookup or (first or last):
                            lookup[cid] = {"first": first, "last": last}
            except Exception:
                pass
        return lookup

    def _client_is_entity_name(self, cid, name_lookup):
        """LifePRO entity rows (FAMILY, ESTATE, TRUST) are not person insureds."""
        info = name_lookup.get(self.normalize(cid), {})
        first = str(info.get("first", "")).strip().upper()
        return first in ("FAMILY", "ESTATE", "TRUST", "THE", "UNKNOWN")

    def _pick_rel_client_id(self, rel_code, candidates, resolved_phase, name_lookup):
        """When multiple clients share a role, pick the best insured/owner match."""
        if not candidates:
            return ""
        if len(candidates) == 1:
            return candidates[-1]
        if rel_code in ("IN", "INSD"):
            owner = resolved_phase.get("PO") or resolved_phase.get("OWNR")
            if owner and owner in candidates:
                return owner
            non_entity = [c for c in candidates if not self._client_is_entity_name(c, name_lookup)]
            if non_entity:
                return non_entity[-1]
        return candidates[-1]

    def _load_rel_map(self, rel_path, trans_map, log_label="relational map", name_lookup=None):
        rel_map = {}
        if not rel_path or not os.path.exists(rel_path):
            return rel_map
        clid_df = pd.read_csv(rel_path, dtype=str).fillna("")
        clid_df.columns = [c.strip().upper() for c in clid_df.columns]
        candidates_map = {}
        for _, row in clid_df.iterrows():
            pol = self.normalize(row.get("MPOLICY", ""))
            rel_raw = self.normalize(row.get("MRELATION", ""))
            cid = self.normalize(row.get("MCLIENTID", ""))
            phase = self.normalize(row.get("MPHASE", ""))
            if not phase or phase == "0":
                phase = "1"
            rel = trans_map.get(rel_raw, rel_raw)
            if not pol or not rel or not cid:
                continue
            candidates_map.setdefault(pol, {}).setdefault(phase, {}).setdefault(rel, [])
            if cid not in candidates_map[pol][phase][rel]:
                candidates_map[pol][phase][rel].append(cid)

        name_lookup = name_lookup or {}
        for pol, phases in candidates_map.items():
            rel_map[pol] = {}
            for phase, rels in phases.items():
                resolved = {}
                for rel, cids in rels.items():
                    if rel in ("IN", "INSD") and len(cids) > 1:
                        continue
                    resolved[rel] = cids[-1] if cids else ""
                for rel in ("IN", "INSD"):
                    if rel in rels:
                        if len(rels[rel]) > 1:
                            resolved[rel] = self._pick_rel_client_id(rel, rels[rel], resolved, name_lookup)
                        elif rel not in resolved:
                            resolved[rel] = rels[rel][-1] if rels[rel] else ""
                rel_map[pol][phase] = resolved

        policy_count = len(rel_map)
        self.log(f"Loaded {log_label} from: {rel_path} ({policy_count} policies)")
        return rel_map

    @staticmethod
    def _compute_quikbenf_equal_splits(n):
        """Return N MSPLIT percentage strings summing exactly to 100.00 (Issue 21I)."""
        if n <= 0:
            return []
        if n == 1:
            return ["100.00"]
        total_cents = 10000
        base_cents = total_cents // n
        remainder = total_cents - (base_cents * n)
        splits = []
        for i in range(n):
            cents = base_cents + (remainder if i == n - 1 else 0)
            splits.append(f"{cents / 100:.2f}")
        return splits

    def _apply_quikbenf_dedupe_and_equal_split(self, output, schema):
        """Dedupe quikbenf rows and assign equal MSPLIT per (MPOLICY, MTYPE) group (Issue 21I)."""
        col_index = {h: i for i, h in enumerate(schema)}
        ipol = col_index.get("MPOLICY")
        ibenf = col_index.get("MBENFID")
        imtype = col_index.get("MTYPE")
        isplit = col_index.get("MSPLIT")
        if ipol is None or ibenf is None or imtype is None or isplit is None:
            return output, {"dedupe_removed": 0, "groups_recalculated": 0}

        seen = set()
        deduped = []
        dedupe_removed = 0
        for row in output:
            key = (
                self.normalize(row[ipol]),
                self.normalize(row[ibenf]),
                self.normalize(row[imtype]),
            )
            if key in seen:
                dedupe_removed += 1
                continue
            seen.add(key)
            deduped.append(list(row))

        groups = {}
        group_order = []
        for row in deduped:
            gkey = (self.normalize(row[ipol]), self.normalize(row[imtype]))
            if gkey not in groups:
                groups[gkey] = []
                group_order.append(gkey)
            groups[gkey].append(row)

        groups_recalculated = 0
        result = []
        for gkey in group_order:
            rows = groups[gkey]
            if not gkey[1]:
                result.extend(rows)
                continue
            splits = self._compute_quikbenf_equal_splits(len(rows))
            groups_recalculated += 1
            for row, split in zip(rows, splits):
                row[isplit] = split
                result.append(row)

        return result, {
            "dedupe_removed": dedupe_removed,
            "groups_recalculated": groups_recalculated,
        }

    def _apply_quikclid_exact_dedupe(self, output, schema):
        """Remove exact duplicate client-policy relationship rows."""
        col_index = {h: i for i, h in enumerate(schema)}
        required = ("MCLIENTID", "MPOLICY", "MPHASE", "MRELATION")
        if any(col_index.get(h) is None for h in required):
            return output, {"dedupe_removed": 0}

        seen = set()
        deduped = []
        removed = 0
        for row in output:
            key = tuple(self.normalize(row[col_index[h]]) for h in required)
            if key in seen:
                removed += 1
                continue
            seen.add(key)
            deduped.append(row)
        return deduped, {"dedupe_removed": removed}

    def _read_lifepro_rna_csv(self, path):
        """Read LifePRO RNA extracts without dropping over-wide relationship rows."""
        with open(path, newline="", encoding="latin1") as f:
            reader = csv.reader(f)
            raw_header = next(reader)
            header = []
            seen = {}
            for col in raw_header:
                base = str(col).replace("\ufeff", "").strip().upper()
                if not base:
                    base = "UNNAMED"
                count = seen.get(base, 0) + 1
                seen[base] = count
                header.append(base if count == 1 else f"{base}_{count}")

            width = len(header)
            rows = []
            overwide = 0
            short = 0
            for row in reader:
                if len(row) > width:
                    overwide += 1
                    row = row[:width]
                elif len(row) < width:
                    short += 1
                    row = row + [""] * (width - len(row))
                rows.append(row)

        df = pd.DataFrame(rows, columns=header).fillna("")
        if overwide or short:
            self.log(
                f"RNA CSV reader: preserved {len(rows)} row(s); "
                f"truncated {overwide} over-wide row(s), padded {short} short row(s)"
            )
        return df

    def _is_preconverted_qla_client_source(self, source_df):
        cols = {str(c).strip().upper() for c in source_df.columns}
        return "MCLIENTID" in cols and "NAME_ID" not in cols and "CLIENT_ID" not in cols

    def _is_active_rna_cancel_date(self, val):
        """LifePRO RNA CANCEL_DATE: blank/0/NULL literal means active (Issue #21D B1)."""
        n = self.normalize(val)
        return n in ("", "0", "NULL")

    def _dedupe_quikclnt_rna_source(self, source_df):
        """One quikclnt row per NAME_ID; prefer rows with individual name fields."""
        if "NAME_ID" not in source_df.columns:
            return source_df
        name_cols = (
            "INDIVIDUAL_LAST", "INDIVIDUAL_FIRST", "KEY_NAME",
            "LAST_NAME", "FIRST_NAME", "CLIENT_ID",
        )

        def _name_score(row):
            return sum(
                1 for c in name_cols
                if c in row.index and str(row.get(c, "")).strip()
            )

        df = source_df.copy()
        df["_name_score"] = df.apply(_name_score, axis=1)
        df = df.sort_values("_name_score", ascending=False)
        df = df.drop_duplicates(subset=["NAME_ID"], keep="first")
        return df.drop(columns=["_name_score"])

    def _bridge_rna_quikclnt_columns(self, source_df):
        bridges = {
            "CLIENT_ID": "NAME_ID",
            "FIRST_NAME": "INDIVIDUAL_FIRST",
            "MIDDLE_NAME": "INDIVIDUAL_MIDDLE",
            "LAST_NAME": "INDIVIDUAL_LAST",
            "SUFFIX": "INDIVIDUAL_SUFFIX",
            "TAX_ID": "SOC_SEC_NUMBER",
            "ADDRESS_LINE_1": "ADDR_LINE_1",
            "ADDRESS_LINE_2": "ADDR_LINE_2",
            "CITY": "CITY",
            "STATE": "STATE",
            "ZIP_CODE": "ZIP",
            "ZIP_EXTENSION": "ZIP_EXTENSION",
            "COUNTRY_CODE": "COUNTRY",
            "HOME_PHONE": "TELE_NUM",
            "FAX_PHONE": "FAX_NUM",
            "BIRTH_DATE": "DATE_OF_BIRTH",
            "SEX": "SEX_CODE",
        }
        for target_col, source_col in bridges.items():
            if target_col not in source_df.columns and source_col in source_df.columns:
                source_df[target_col] = source_df[source_col]
        return source_df

    def _resolve_run_mode(self):
        mode = os.environ.get("QLA_RUN_MODE", DEFAULT_RUN_MODE).strip().upper()
        if mode not in VALID_RUN_MODES:
            return DEFAULT_RUN_MODE
        return mode

    def _claims_analysis_root(self):
        return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "claims_analysis"))

    def _migration_source_dir(self):
        return os.path.normpath(os.path.join(self._app_base_dir(), "QLA_Migration", "Source"))

    def _resolve_claims_prelsa_path(self):
        """Resolve PRELSA/RNA — prefer dated Source extract (20260630 package)."""
        env_path = os.environ.get("QLA_CLAIMS_PRELSA_PATH", "").strip()
        if env_path and os.path.isfile(env_path):
            return os.path.normpath(env_path)
        src_dir = self._migration_source_dir()
        # Prefer LifePRO dated RelationshipNameAddress_Extract_YYYYMMDD.csv (newest first)
        dated = []
        if os.path.isdir(src_dir):
            for name in os.listdir(src_dir):
                if name.lower().startswith("relationshipnameaddress_extract") and name.lower().endswith(".csv"):
                    dated.append(os.path.join(src_dir, name))
        dated.sort(reverse=True)
        # Also try table resolver (same patterns as quikclnt)
        resolved, _label = resolve_table_source(src_dir, "quikclnt")
        candidates = dated + [
            resolved if resolved else "",
            os.path.join(src_dir, "RelationshipNameAddress_Extract.csv"),
            os.path.join(self._app_base_dir(), "docs", "claims_conversion_reference", "RelationshipNameAddress_Extract.csv"),
        ]
        for path in candidates:
            if path and os.path.isfile(path):
                return os.path.normpath(path)
        return os.path.normpath(
            os.path.join(src_dir, "RelationshipNameAddress_Extract_20260630.csv")
        )

    def _resolve_claims_pactg_path(self):
        env_path = os.environ.get("QLA_CLAIMS_PACTG_PATH", "").strip()
        if env_path and os.path.isfile(env_path):
            return os.path.normpath(env_path)
        # Prefer any dated PACTG_Accounting_Extract*.csv in Source (newest wins).
        src_dir = self._migration_source_dir()
        path, _label = resolve_table_source(src_dir, "quikprmh")
        if path and os.path.isfile(path):
            return os.path.normpath(path)
        docs_fallback = os.path.join(
            self._app_base_dir(),
            "docs",
            "claims_conversion_reference",
            "PACTG_Accounting_Extract20260427.csv",
        )
        if os.path.isfile(docs_fallback):
            return os.path.normpath(docs_fallback)
        return os.path.normpath(os.path.join(src_dir, "PACTG_Accounting_Extract.csv"))

    def _claims_lineage_refresh_enabled(self):
        flag = os.environ.get("QLA_REFRESH_CLAIMS_LINEAGE", "").strip().lower() in ("1", "true", "yes")
        return flag and self.CLAIMS_ORCHESTRATION["run_mode"] == "UAT"

    def _invoke_phase10a_quikclmp_refresh(self):
        claims_root = self._claims_analysis_root()
        runner = os.path.join(
            claims_root, "phase10a_quikclmp_derivation", "quikclmp_rulebook_derivation_engine.py",
        )
        prelsa_path = self._resolve_claims_prelsa_path()
        output_dir = os.path.join(claims_root, "phase10a_quikclmp_derivation_design")
        timeout = self.CLAIMS_ORCHESTRATION.get("orchestration_timeout_seconds", DEFAULT_ORCHESTRATION_TIMEOUT_SECONDS)
        if not os.path.isfile(runner):
            self.log(f"PHASE 22 LINEAGE REFRESH: Phase 10A runner not found — {runner}")
            return False
        if not os.path.isfile(prelsa_path):
            self.log(f"PHASE 22 LINEAGE REFRESH: PRELSA source missing — {prelsa_path}")
            return False
        cmd = [sys.executable, runner, "--prelsa", prelsa_path, "--output", output_dir]
        self.log("PHASE 22 LINEAGE REFRESH: Re-deriving Phase 10A QUIKCLMP candidates from resolved PRELSA...")
        self.log(f"  PRELSA source: {prelsa_path}")
        self.log(f"  Command: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd, cwd=claims_root, capture_output=True, text=True, timeout=timeout, check=False,
            )
            self._log_subprocess_stream("phase10a-stdout", result.stdout or "")
            self._log_subprocess_stream("phase10a-stderr", result.stderr or "")
            ok = result.returncode == 0
            self.log(f"PHASE 22 LINEAGE REFRESH: Phase 10A status={'SUCCESS' if ok else 'FAILED'} return_code={result.returncode}")
            return ok
        except subprocess.TimeoutExpired:
            self.log(f"PHASE 22 LINEAGE REFRESH: Phase 10A exceeded {timeout}s timeout")
            return False
        except OSError as exc:
            self.log(f"PHASE 22 LINEAGE REFRESH ERROR: {exc}")
            return False

    def _resolve_claims_uat_candidate_sources(self):
        """Prefer client-decision populations (Phases 23–24) for UAT emit; fall back to Phase 17."""
        claims_root = self._claims_analysis_root()
        p17 = os.path.join(claims_root, "phase17_uat_governance_reporting")
        p23 = os.path.join(claims_root, "phase23_client_decision_application")
        p24 = os.path.join(claims_root, "phase24_client_balancing_rerun")
        candidates = [
            (
                "Phase24 post-rebalance (client Items 14–16)",
                os.path.join(p24, "uat_candidate_quikclms_post_rebalance.csv"),
                os.path.join(p24, "uat_candidate_quikclmp_post_rebalance.csv"),
            ),
            (
                "Phase23 client-decision refresh (Items 14–19)",
                os.path.join(p23, "uat_candidate_quikclms_refreshed.csv"),
                os.path.join(p23, "uat_candidate_quikclmp_refreshed.csv"),
            ),
            (
                "Phase17 governance baseline",
                os.path.join(p17, "uat_candidate_quikclms.csv"),
                os.path.join(p17, "uat_candidate_quikclmp.csv"),
            ),
        ]
        for label, clms_path, clmp_path in candidates:
            if os.path.isfile(clms_path) and os.path.isfile(clmp_path):
                return label, clms_path, clmp_path
        return "Phase17 governance baseline (paths missing — check claims_analysis)", \
            os.path.join(p17, "uat_candidate_quikclms.csv"), \
            os.path.join(p17, "uat_candidate_quikclmp.csv")

    @staticmethod
    def _claimnum_prefix(reconstructed_claim_id):
        text = str(reconstructed_claim_id or "").strip()
        return text[:13] if text else ""

    def _client_claim_overlay_paths(self):
        claims_root = self._claims_analysis_root()
        p23 = os.path.join(claims_root, "phase23_client_decision_application")
        return {
            "combined_amounts": os.path.join(p23, "combined_claim_amount_adjustments.csv"),
            "payee_overrides": os.path.join(p23, "payee_override_application.csv"),
        }

    def _apply_client_claim_decision_overlays(self, output_dir):
        """Apply Item 18 (combined amounts) and Item 19 (payee overrides) post-emit."""
        paths = self._client_claim_overlay_paths()
        clms_out = os.path.normpath(os.path.join(output_dir, "quikclms.csv"))
        clmp_out = os.path.normpath(os.path.join(output_dir, "quikclmp.csv"))
        result = {"item18": {}, "item19": {}, "applied": False}

        adj_path = paths["combined_amounts"]
        if os.path.isfile(clms_out) and os.path.isfile(adj_path):
            try:
                clms = pd.read_csv(clms_out, dtype=str).fillna("")
                adj = pd.read_csv(adj_path, dtype=str)
                adj["combined_claim_amount"] = pd.to_numeric(adj["combined_claim_amount"], errors="coerce")
                adj = adj.dropna(subset=["combined_claim_amount"])
                # Item 18: loan-settlement only. Skip interest-only rows (0630 already in 0094).
                if "offset" in adj.columns:
                    adj["offset"] = pd.to_numeric(adj["offset"], errors="coerce").fillna(0.0)
                    adj = adj[adj["offset"] != 0.0]
                prefix_map = {
                    self._claimnum_prefix(row["reconstructed_claim_id"]): row["combined_claim_amount"]
                    for _, row in adj.iterrows()
                }
                applied = 0
                for idx, row in clms.iterrows():
                    claimnum = str(row.get("CLAIMNUM", "")).strip()
                    amount = prefix_map.get(claimnum)
                    if amount is None:
                        continue
                    amt_str = f"{float(amount):.2f}"
                    for field in ("NETDB", "MPAID", "MFACE"):
                        if field in clms.columns:
                            clms.at[idx, field] = amt_str
                    applied += 1
                clms.to_csv(clms_out, index=False, encoding="utf-8")
                result["item18"] = {"applied": applied, "eligible": len(adj), "source": adj_path}
            except Exception as exc:
                result["item18"] = {"applied": 0, "error": str(exc)}
        else:
            result["item18"] = {"applied": 0, "reason": "missing_file"}

        ovr_path = paths["payee_overrides"]
        if os.path.isfile(clmp_out) and os.path.isfile(ovr_path):
            try:
                clmp = pd.read_csv(clmp_out, dtype=str).fillna("")
                ovr = pd.read_csv(ovr_path, dtype=str)
                applied = 0
                details = []
                for _, spec in ovr.iterrows():
                    policy = str(spec.get("policy_number", "")).strip()
                    new_payee = str(spec.get("new_payee", "")).strip()
                    if not policy or not new_payee:
                        continue
                    mask = clmp["MPOLICY"].astype(str).str.strip() == policy
                    count = int(mask.sum())
                    if count:
                        clmp.loc[mask, "MPAYNAME"] = new_payee
                        applied += count
                        details.append({
                            "policy_number": policy,
                            "rows_updated": count,
                            "new_payee": new_payee,
                        })
                clmp.to_csv(clmp_out, index=False, encoding="utf-8")
                result["item19"] = {"applied": applied, "details": details, "source": ovr_path}
            except Exception as exc:
                result["item19"] = {"applied": 0, "error": str(exc)}
        else:
            result["item19"] = {"applied": 0, "reason": "missing_file"}

        result["applied"] = bool(result.get("item18", {}).get("applied") or result.get("item19", {}).get("applied"))
        return result

    def _log_client_claim_overlay_summary(self, overlay_result):
        if not overlay_result:
            return
        i18 = overlay_result.get("item18", {})
        i19 = overlay_result.get("item19", {})
        self.log("CLIENT CLAIM OVERLAYS (Items 18–19, post-emit):")
        self.log(f"  Item 18 combined amounts: applied={i18.get('applied', 0)} eligible={i18.get('eligible', 'n/a')}")
        self.log(f"  Item 19 payee overrides:  applied={i19.get('applied', 0)}")
        if i19.get("details"):
            for detail in i19["details"]:
                self.log(f"    payee override: {detail.get('policy_number')} -> {detail.get('new_payee')}")

    def _apply_issue78_quikclmp_recovery(self, output_dir):
        """Issue #78: append quikclmp rows for zero-payment claim policies with PACTG payouts."""
        clms_path = os.path.normpath(os.path.join(output_dir, "quikclms.csv"))
        clmp_path = os.path.normpath(os.path.join(output_dir, "quikclmp.csv"))
        result = {
            "applied": False,
            "policies_recovered": 0,
            "rows_added": 0,
            "audit_path": "",
            "reason": "",
        }
        if not os.path.isfile(clms_path) or not os.path.isfile(clmp_path):
            result["reason"] = "missing_quikclms_or_quikclmp"
            return result

        pactg_path = self._resolve_claims_pactg_path()
        rel_path = self._resolve_claims_prelsa_path()
        cw_path = os.path.join(self._migration_mapping_dir(), "Master_Crosswalk.csv")
        if not os.path.isfile(pactg_path):
            result["reason"] = "missing_pactg"
            return result
        if not os.path.isfile(rel_path):
            result["reason"] = "missing_relationship_extract"
            return result

        try:
            clms_df = pd.read_csv(clms_path, dtype=str).fillna("")
            clmp_before = pd.read_csv(clmp_path, dtype=str).fillna("")
            before_count = len(clmp_before)
            clmp_after, audit_df = recover_missing_quikclmp_payments(
                clms_df,
                clmp_before,
                pactg_path,
                rel_path,
                cw_path,
                format_mpolicy=self._format_qladmin_mpolicy,
            )
            added = len(clmp_after) - before_count
            if added <= 0:
                result["reason"] = "no_recoverable_rows"
                return result

            tmp_path = clmp_path + ".tmp"
            clmp_after.to_csv(tmp_path, index=False, encoding="utf-8")
            os.replace(tmp_path, clmp_path)
            audit_path = write_recovery_audit(audit_df, self._reports_dir())
            result.update(
                {
                    "applied": True,
                    "policies_recovered": len(audit_df),
                    "rows_added": added,
                    "audit_path": audit_path,
                    "tier_counts": audit_df["tier"].value_counts().to_dict() if not audit_df.empty else {},
                }
            )
            return result
        except Exception as exc:
            result["reason"] = f"error:{exc}"
            return result

    def _log_issue78_recovery_summary(self, recovery_result):
        if not recovery_result:
            return
        self.log("ISSUE #78 QUIKCLMP RECOVERY (post-emit):")
        if not recovery_result.get("applied"):
            self.log(f"  Skipped: {recovery_result.get('reason', 'unknown')}")
            return
        self.log(
            f"  Recovered policies={recovery_result.get('policies_recovered', 0)} "
            f"rows_added={recovery_result.get('rows_added', 0)}"
        )
        tiers = recovery_result.get("tier_counts") or {}
        if tiers:
            self.log(f"  Tier counts: {tiers}")
        if recovery_result.get("audit_path"):
            self.log(f"  Audit: {recovery_result['audit_path']}")

    def _apply_issue79_claimstat_remap(self, output_dir):
        """Issue #79: align quikclms.CLAIMSTAT to Policy-book conventions (SD-79)."""
        clms_path = os.path.normpath(os.path.join(output_dir, "quikclms.csv"))
        clmp_path = os.path.normpath(os.path.join(output_dir, "quikclmp.csv"))
        result = {
            "applied": False,
            "rows_changed": 0,
            "audit_path": "",
            "reason": "",
            "after_counts": {},
        }
        if not os.path.isfile(clms_path):
            result["reason"] = "missing_quikclms"
            return result
        try:
            clms_df = pd.read_csv(clms_path, dtype=str).fillna("")
            clmp_df = (
                pd.read_csv(clmp_path, dtype=str).fillna("")
                if os.path.isfile(clmp_path)
                else pd.DataFrame()
            )
            clms_after, audit_df = remap_quikclms_claimstat(clms_df, clmp_df)
            changed = len(audit_df)
            if changed <= 0:
                result["reason"] = "no_remap_needed"
                return result
            tmp_path = clms_path + ".tmp"
            clms_after.to_csv(tmp_path, index=False, encoding="utf-8")
            os.replace(tmp_path, clms_path)
            audit_path = write_remap_audit(audit_df, self._reports_dir())
            after_counts = clms_after["CLAIMSTAT"].astype(str).str.strip().value_counts().to_dict()
            result.update(
                {
                    "applied": True,
                    "rows_changed": changed,
                    "audit_path": audit_path,
                    "after_counts": after_counts,
                }
            )
            return result
        except Exception as exc:
            result["reason"] = f"error:{exc}"
            return result

    def _log_issue79_remap_summary(self, remap_result):
        if not remap_result:
            return
        self.log("ISSUE #79 CLAIMSTAT REMAP (post-emit):")
        if not remap_result.get("applied"):
            self.log(f"  Skipped: {remap_result.get('reason', 'unknown')}")
            return
        self.log(f"  Rows changed={remap_result.get('rows_changed', 0)}")
        counts = remap_result.get("after_counts") or {}
        if counts:
            self.log(f"  After CLAIMSTAT counts: {counts}")
        if remap_result.get("audit_path"):
            self.log(f"  Audit: {remap_result['audit_path']}")

    def _apply_issue134_claim_memos(self, output_dir):
        """Issue #134: PNOTE FILE_TYPE=B → quikclms.MEMOTEXT (Claims Tab). After #79 lineage use."""
        clms_path = os.path.normpath(os.path.join(output_dir, "quikclms.csv"))
        result = {
            "applied": False,
            "rows_updated": 0,
            "policies_updated": 0,
            "orphan_b_policies": 0,
            "audit_path": "",
            "reason": "",
        }
        if not os.path.isfile(clms_path):
            result["reason"] = "missing_quikclms"
            return result
        try:
            src_dir = self._migration_source_dir()
            pnote_path, _pnote_label, _pense_path, _pense_label = resolve_quikmemo_sources(src_dir)
            if not pnote_path:
                result["reason"] = "missing_pnote"
                return result
            clms_df = pd.read_csv(clms_path, dtype=str).fillna("")
            clms_after, orphan_df, stats = apply_issue134_claim_memos(clms_df, pnote_path)
            updated = int(stats.get("rows_updated", 0) or 0)
            if updated <= 0:
                result["reason"] = stats.get("reason") or "no_b_memos_applied"
                result["orphan_b_policies"] = int(stats.get("orphan_b_policies", 0) or 0)
                if not orphan_df.empty:
                    result["audit_path"] = write_issue134_orphan_audit(orphan_df, self._reports_dir())
                return result
            tmp_path = clms_path + ".tmp"
            clms_after.to_csv(tmp_path, index=False, encoding="utf-8")
            os.replace(tmp_path, clms_path)
            audit_path = ""
            if not orphan_df.empty:
                audit_path = write_issue134_orphan_audit(orphan_df, self._reports_dir())
            result.update(
                {
                    "applied": True,
                    "rows_updated": updated,
                    "policies_updated": int(stats.get("policies_updated", 0) or 0),
                    "orphan_b_policies": int(stats.get("orphan_b_policies", 0) or 0),
                    "audit_path": audit_path,
                }
            )
            return result
        except Exception as exc:
            result["reason"] = f"error:{exc}"
            return result

    def _log_issue134_claim_memo_summary(self, overlay_result):
        if not overlay_result:
            return
        self.log("ISSUE #134 CLAIM MEMOS (PNOTE B → quikclms.MEMOTEXT):")
        if not overlay_result.get("applied"):
            self.log(f"  Skipped: {overlay_result.get('reason', 'unknown')}")
            if overlay_result.get("orphan_b_policies"):
                self.log(f"  Orphan B policies: {overlay_result.get('orphan_b_policies')}")
            if overlay_result.get("audit_path"):
                self.log(f"  Orphan audit: {overlay_result['audit_path']}")
            return
        self.log(
            f"  Rows updated={overlay_result.get('rows_updated', 0)} "
            f"policies={overlay_result.get('policies_updated', 0)} "
            f"orphan_b={overlay_result.get('orphan_b_policies', 0)}"
        )
        if overlay_result.get("audit_path"):
            self.log(f"  Orphan audit: {overlay_result['audit_path']}")

    def _apply_issue135_cso_claims_expansion(self, output_dir):
        """Issue #135: Option-3 consume + 459 CSO expansion (pre-#134 PNOTE-B, pre-MINTAMT zero)."""
        clms_path = os.path.normpath(os.path.join(output_dir, "quikclms.csv"))
        clmp_path = os.path.normpath(os.path.join(output_dir, "quikclmp.csv"))
        result = {
            "applied": False,
            "reason": "",
            "option3_headers_updated": 0,
            "derived_headers_emitted": 0,
            "header_only_308_emitted": 0,
            "holds_9": 0,
        }
        if not os.path.isfile(clms_path) or not os.path.isfile(clmp_path):
            result["reason"] = "missing_quikclms_or_quikclmp"
            return result
        try:
            clms_df = pd.read_csv(clms_path, dtype=str).fillna("")
            clmp_df = pd.read_csv(clmp_path, dtype=str).fillna("")
            clms_after, clmp_after, stats = apply_issue135_cso_claims_expansion(
                clms_df,
                clmp_df,
                pactg_path=self._resolve_claims_pactg_path(),
                prelsa_path=self._resolve_claims_prelsa_path(),
            )
            evidence_dir = os.path.join(
                self._repo_root(),
                "Issue_Log_Items",
                "Issue_135",
                "evidence",
            )
            reports_dir = os.path.join(self._migration_root(), "Reports")
            write_issue135_expansion_audits(stats, evidence_dir, reports_dir)
            tmp_clms = clms_path + ".tmp"
            tmp_clmp = clmp_path + ".tmp"
            clms_after.to_csv(tmp_clms, index=False, encoding="utf-8")
            clmp_after.to_csv(tmp_clmp, index=False, encoding="utf-8")
            os.replace(tmp_clms, clms_path)
            os.replace(tmp_clmp, clmp_path)
            result.update(
                {
                    "applied": bool(stats.get("applied")),
                    "option3_headers_updated": int(stats.get("option3_headers_updated", 0) or 0),
                    "derived_headers_emitted": int(stats.get("derived_headers_emitted", 0) or 0),
                    "derived_payees_emitted": int(stats.get("derived_payees_emitted", 0) or 0),
                    "derived_payee_holds": int(stats.get("derived_payee_holds", 0) or 0),
                    "header_only_308_emitted": int(stats.get("header_only_308_emitted", 0) or 0),
                    "holds_9": int(stats.get("holds_9", 0) or 0),
                    "zero_payee_backfill_policies": int(
                        stats.get("zero_payee_backfill_policies", 0) or 0
                    ),
                    "zero_payee_backfill_rows": int(stats.get("zero_payee_backfill_rows", 0) or 0),
                    "surrender_zero_payee_backfill_policies": int(
                        stats.get("surrender_zero_payee_backfill_policies", 0) or 0
                    ),
                    "surrender_zero_payee_backfill_rows": int(
                        stats.get("surrender_zero_payee_backfill_rows", 0) or 0
                    ),
                    "surrender_zero_payee_rule1_policies": int(
                        (stats.get("surrender_zero_payee_backfill_stats") or {}).get(
                            "rule1_policies", 0
                        )
                        or 0
                    ),
                    "surrender_zero_payee_rule2_policies": int(
                        (stats.get("surrender_zero_payee_backfill_stats") or {}).get(
                            "rule2_policies", 0
                        )
                        or 0
                    ),
                    "clms_rows_after": int(stats.get("clms_rows_after", 0) or 0),
                    "clmp_rows_after": int(stats.get("clmp_rows_after", 0) or 0),
                    "reason": "",
                }
            )
            return result
        except Exception as exc:
            result["reason"] = f"error:{exc}"
            return result

    def _log_issue135_cso_expansion_summary(self, overlay_result):
        if not overlay_result:
            return
        self.log("ISSUE #135 CSO CLAIMS EXPANSION (Option-3 + 459):")
        if not overlay_result.get("applied"):
            self.log(f"  Skipped: {overlay_result.get('reason', 'unknown')}")
            return
        self.log(
            f"  Option3 headers={overlay_result.get('option3_headers_updated', 0)} "
            f"derived_hdr={overlay_result.get('derived_headers_emitted', 0)} "
            f"derived_payees={overlay_result.get('derived_payees_emitted', 0)} "
            f"header_only_308={overlay_result.get('header_only_308_emitted', 0)} "
            f"holds_9={overlay_result.get('holds_9', 0)}"
        )
        if overlay_result.get("zero_payee_backfill_rows"):
            self.log(
                f"  MATCH_CSO zero-payee backfill rows="
                f"{overlay_result.get('zero_payee_backfill_rows')} "
                f"policies={overlay_result.get('zero_payee_backfill_policies')}"
            )
        self.log(
            f"  SURRENDER zero-payee backfill rows="
            f"{overlay_result.get('surrender_zero_payee_backfill_rows', 0)} "
            f"policies={overlay_result.get('surrender_zero_payee_backfill_policies', 0)} "
            f"(PE payout={overlay_result.get('surrender_zero_payee_rule1_policies', 0)}, "
            f"relationship fallback={overlay_result.get('surrender_zero_payee_rule2_policies', 0)})"
        )

    def _apply_issue135_mintamt_zero(self, output_dir):
        """Issue #135 Phase A: force quikclms.MINTAMT=0.00 after other claim post-emit steps."""
        clms_path = os.path.normpath(os.path.join(output_dir, "quikclms.csv"))
        result = {
            "applied": False,
            "rows_updated": 0,
            "nonzero_before": 0,
            "reason": "",
        }
        if not os.path.isfile(clms_path):
            result["reason"] = "missing_quikclms"
            return result
        try:
            clms_df = pd.read_csv(clms_path, dtype=str).fillna("")
            clms_after, stats = apply_issue135_mintamt_zero(clms_df)
            updated = int(stats.get("rows_updated", 0) or 0)
            result["nonzero_before"] = int(stats.get("nonzero_before", 0) or 0)
            if updated <= 0:
                result["reason"] = stats.get("reason") or "already_zero"
                return result
            tmp_path = clms_path + ".tmp"
            clms_after.to_csv(tmp_path, index=False, encoding="utf-8")
            os.replace(tmp_path, clms_path)
            result.update(
                {
                    "applied": True,
                    "rows_updated": updated,
                    "reason": "",
                }
            )
            return result
        except Exception as exc:
            result["reason"] = f"error:{exc}"
            return result

    def _log_issue135_mintamt_summary(self, overlay_result):
        if not overlay_result:
            return
        self.log("ISSUE #135 MINTAMT FORCE ZERO:")
        if not overlay_result.get("applied"):
            self.log(f"  Skipped: {overlay_result.get('reason', 'unknown')}")
            self.log(f"  Nonzero before: {overlay_result.get('nonzero_before', 0)}")
            return
        self.log(
            f"  Rows updated={overlay_result.get('rows_updated', 0)} "
            f"nonzero_before={overlay_result.get('nonzero_before', 0)}"
        )

    def _apply_claims_payee_mseq_align(self, output_dir):
        """Force QUIKCLMP.MSEQ to claim-header MSEQ so QLAdmin payee UI joins."""
        result = {"applied": False, "ok": False, "reason": "", "align": {}, "gate": {}}
        try:
            tv = os.path.join(output_dir, "Test_Validation")
            info = align_claims_csv_dir(
                output_dir,
                test_validation_dir=tv,
                require_golden=False,
            )
            result.update(
                {
                    "applied": True,
                    "ok": True,
                    "align": info.get("align") or {},
                    "gate": info.get("gate") or {},
                    "test_validation_copied": info.get("test_validation_copied"),
                }
            )
            return result
        except ClaimsPayeeMseqAlignError as exc:
            result["reason"] = str(exc)
            return result
        except Exception as exc:
            result["reason"] = f"error:{exc}"
            return result

    def _log_claims_payee_mseq_align_summary(self, align_result):
        if not align_result:
            return
        self.log("CLAIMS PAYEE MSEQ ALIGN (QLAdmin join MPOLICY+MPHASE+MSEQ):")
        if not align_result.get("ok"):
            self.log(f"  FAIL: {align_result.get('reason', 'unknown')}")
            return
        align = align_result.get("align") or {}
        self.log(
            f"  rows={align.get('rows', 0)} changed={align.get('changed', 0)} "
            f"already_aligned={align.get('already_aligned', 0)}"
        )
        golden = (align_result.get("gate") or {}).get("golden") or {}
        if golden.get("present"):
            self.log(
                f"  golden 9011156655C payees={golden.get('payee_n')} "
                f"mseqs={golden.get('mseqs')} ok={golden.get('ok')}"
            )

    def _apply_issue85_claim_header_structure(self, output_dir):
        """Issue #85: merge/re-phase quikclms headers; re-attach quikclmp phases (D1–D4)."""
        clms_path = os.path.normpath(os.path.join(output_dir, "quikclms.csv"))
        clmp_path = os.path.normpath(os.path.join(output_dir, "quikclmp.csv"))
        result = {
            "applied": False,
            "headers_before": 0,
            "headers_after": 0,
            "merge_drops": 0,
            "rephase_moves": 0,
            "payee_exceptions": 0,
            "audit_paths": {},
            "reason": "",
        }
        if not os.path.isfile(clms_path):
            result["reason"] = "missing_quikclms"
            return result
        try:
            clms_df = pd.read_csv(clms_path, dtype=str).fillna("")
            clmp_df = (
                pd.read_csv(clmp_path, dtype=str).fillna("")
                if os.path.isfile(clmp_path)
                else pd.DataFrame()
            )
            before_n = len(clms_df)
            clms_after, clmp_after, merge_audit, rephase_payee_audit = apply_issue85_header_structure(
                clms_df, clmp_df
            )
            merge_drops = len(merge_audit)
            rephase_moves = int(
                (rephase_payee_audit.get("action") == "REPHASE").sum()
                if len(rephase_payee_audit) and "action" in rephase_payee_audit.columns
                else 0
            )
            if len(rephase_payee_audit) and "exception" in rephase_payee_audit.columns:
                payee_exceptions = int((rephase_payee_audit["exception"] == "Y").sum())
            else:
                payee_exceptions = 0
            if merge_drops <= 0 and rephase_moves <= 0:
                payee_moves = int(
                    (rephase_payee_audit.get("action") == "PAYEE_REPHASE").sum()
                    if len(rephase_payee_audit) and "action" in rephase_payee_audit.columns
                    else 0
                )
                if payee_moves <= 0 and payee_exceptions <= 0:
                    result["reason"] = "no_structure_change"
                    result["headers_before"] = before_n
                    result["headers_after"] = before_n
                    return result

            tmp_clms = clms_path + ".tmp"
            clms_after.to_csv(tmp_clms, index=False, encoding="utf-8")
            os.replace(tmp_clms, clms_path)
            if os.path.isfile(clmp_path) and not clmp_after.empty:
                tmp_clmp = clmp_path + ".tmp"
                clmp_after.to_csv(tmp_clmp, index=False, encoding="utf-8")
                os.replace(tmp_clmp, clmp_path)
            audit_paths = write_structure_audits(merge_audit, rephase_payee_audit, self._reports_dir())
            result.update(
                {
                    "applied": True,
                    "headers_before": before_n,
                    "headers_after": len(clms_after),
                    "merge_drops": merge_drops,
                    "rephase_moves": rephase_moves,
                    "payee_exceptions": payee_exceptions,
                    "audit_paths": audit_paths,
                }
            )
            return result
        except Exception as exc:
            result["reason"] = f"error:{exc}"
            return result

    def _log_issue85_structure_summary(self, structure_result):
        if not structure_result:
            return
        self.log("ISSUE #85 CLAIM HEADER STRUCTURE (post-emit):")
        if not structure_result.get("applied"):
            self.log(f"  Skipped: {structure_result.get('reason', 'unknown')}")
            return
        self.log(
            f"  Headers {structure_result.get('headers_before', 0)} -> "
            f"{structure_result.get('headers_after', 0)} "
            f"(merge_drops={structure_result.get('merge_drops', 0)}, "
            f"rephase={structure_result.get('rephase_moves', 0)}, "
            f"payee_exceptions={structure_result.get('payee_exceptions', 0)})"
        )
        paths = structure_result.get("audit_paths") or {}
        for key, path in paths.items():
            self.log(f"  Audit[{key}]: {path}")

    def _apply_issue84_track_a_header_backfill(self, output_dir):
        """Issue #84 Track A: backfill header MPAID/PDDATE from claim-keyed quikclmp payees."""
        clms_path = os.path.normpath(os.path.join(output_dir, "quikclms.csv"))
        clmp_path = os.path.normpath(os.path.join(output_dir, "quikclmp.csv"))
        result = {
            "applied": False,
            "rows_changed": 0,
            "audit_path": "",
            "reason": "",
        }
        if not os.path.isfile(clms_path) or not os.path.isfile(clmp_path):
            result["reason"] = "missing_quikclms_or_quikclmp"
            return result
        try:
            clms_df = pd.read_csv(clms_path, dtype=str).fillna("")
            clmp_df = pd.read_csv(clmp_path, dtype=str).fillna("")
            clms_after, audit_df = backfill_quikclms_headers_from_payees(clms_df, clmp_df)
            changed = len(audit_df)
            if changed <= 0:
                result["reason"] = "no_backfill_needed"
                return result
            tmp_path = clms_path + ".tmp"
            clms_after.to_csv(tmp_path, index=False, encoding="utf-8")
            os.replace(tmp_path, clms_path)
            audit_path = write_money_field_audit(audit_df, self._reports_dir())
            result.update(
                {
                    "applied": True,
                    "rows_changed": changed,
                    "audit_path": audit_path,
                }
            )
            return result
        except Exception as exc:
            result["reason"] = f"error:{exc}"
            return result

    def _log_issue84_track_a_summary(self, track_a_result):
        if not track_a_result:
            return
        self.log("ISSUE #84 TRACK A — HEADER MPAID/PDDATE BACKFILL (post-emit):")
        if not track_a_result.get("applied"):
            self.log(f"  Skipped: {track_a_result.get('reason', 'unknown')}")
            return
        self.log(f"  Headers backfilled={track_a_result.get('rows_changed', 0)}")
        if track_a_result.get("audit_path"):
            self.log(f"  Audit: {track_a_result['audit_path']}")

    def _load_claims_orchestration_rules(self):
        rules_path = os.path.join(self._claims_analysis_root(), "config", "app_claims_uat_orchestration_rules.json")
        if not os.path.isfile(rules_path):
            return {}
        try:
            with open(rules_path, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            return {}

    def _build_claims_orchestration_config(self):
        base = os.path.dirname(os.path.abspath(__file__))
        claims_root = self._claims_analysis_root()
        rules = self._load_claims_orchestration_rules()
        phase17_out = os.path.join(claims_root, "phase17_uat_governance_reporting")
        uat_label, uat_clms, uat_clmp = self._resolve_claims_uat_candidate_sources()
        auth_flag = os.environ.get(
            "QLA_PRODUCTION_DBF_AUTHORIZED",
            rules.get("production_authorization_flag", "N"),
        ).strip().upper()
        return {
            "run_mode": self._resolve_run_mode(),
            "production_dbf_flag": rules.get("production_dbf_flag", "N"),
            "production_authorization_flag": auth_flag,
            "go_live_target": rules.get("go_live_target", "2026-09-01"),
            "allow_inline_claims_conversion": False,
            "uat_candidate_dir": phase17_out,
            "uat_source_label": uat_label,
            "uat_quikclms_source": uat_clms,
            "uat_quikclmp_source": uat_clmp,
            "orchestration_runner": os.path.join(
                claims_root, "phase17_uat_governance_reporting", "phase17_uat_governance_reporting_runner.py",
            ),
            "future_claims_pipeline_runner": os.path.join(claims_root, "phase16_business_triage", "phase16_business_triage_runner.py"),
            "staging_subdir": rules.get("uat_staging_subdir", "claims_uat_staging"),
            "orchestration_timeout_seconds": int(
                rules.get("orchestration_timeout_seconds", DEFAULT_ORCHESTRATION_TIMEOUT_SECONDS)
            ),
            "uat_dbf_generator_runner": os.path.join(
                claims_root, "phase19_uat_emitted_csv_dbf", "uat_emitted_csv_dbf_generator.py",
            ),
            "uat_dbf_timeout_seconds": int(
                rules.get("orchestration_timeout_seconds", DEFAULT_ORCHESTRATION_TIMEOUT_SECONDS)
            ),
            "semantic_governance_runner": os.path.join(
                claims_root, "phase22_semantic_governance", "phase22_semantic_governance_runner.py",
            ),
            "prelsa_source_path": self._resolve_claims_prelsa_path(),
            "pactg_source_path": self._resolve_claims_pactg_path(),
            "app_base_dir": base,
        }

    def _is_claims_table(self, table_id):
        return str(table_id or "").strip().lower() in CLAIMS_TABLE_IDS

    def _claims_uat_source_path(self, table_id):
        cfg = self.CLAIMS_ORCHESTRATION
        if table_id.lower() == "quikclms":
            return cfg["uat_quikclms_source"]
        if table_id.lower() == "quikclmp":
            return cfg["uat_quikclmp_source"]
        return ""

    def _claims_orchestrate_enabled(self):
        flag = os.environ.get("QLA_CLAIMS_ORCHESTRATE", "").strip().lower() in ("1", "true", "yes")
        return flag and self.CLAIMS_ORCHESTRATION["run_mode"] == "UAT"

    def _claims_uat_emit_enabled(self):
        flag = os.environ.get("QLA_CLAIMS_UAT_EMIT", "1").strip().lower()
        if flag in ("0", "false", "no"):
            return False
        return self.CLAIMS_ORCHESTRATION["run_mode"] == "UAT"

    def _batch_include_claims_uat_enabled(self):
        flag = os.environ.get("QLA_BATCH_INCLUDE_CLAIMS_UAT", "").strip().lower() in ("1", "true", "yes")
        return flag and self.CLAIMS_ORCHESTRATION["run_mode"] == "UAT"

    def _batch_include_quikisrr_enabled(self):
        flag = os.environ.get("QLA_ENABLE_QUIKISRR_EMIT", "").strip().lower() in ("1", "true", "yes")
        return flag and self.CLAIMS_ORCHESTRATION["run_mode"] == "UAT"

    def _batch_include_quikiswl_enabled(self):
        # Issue #124: default ON for full batch; set QLA_ENABLE_QUIKISWL_EMIT=0 to skip.
        flag = os.environ.get("QLA_ENABLE_QUIKISWL_EMIT", "1").strip().lower()
        return flag not in ("0", "false", "no")

    def _claims_uat_dbf_generation_enabled(self):
        flag = os.environ.get("QLA_GENERATE_UAT_CLAIMS_DBF", "").strip().lower() in ("1", "true", "yes")
        return flag and self.CLAIMS_ORCHESTRATION["run_mode"] == "UAT"

    def _claims_semantic_governance_enabled(self):
        flag = os.environ.get("QLA_SEMANTIC_GOVERNANCE_HOLD", "1").strip().lower()
        if flag in ("0", "false", "no"):
            return False
        return self.CLAIMS_ORCHESTRATION["run_mode"] == "UAT"

    def _claims_mpolicy_validation_enabled(self):
        flag = os.environ.get("QLA_VALIDATE_CLAIMS_MPOLICY", "1").strip().lower()
        if flag in ("0", "false", "no"):
            return False
        return self.CLAIMS_ORCHESTRATION["run_mode"] == "UAT"

    def _claims_staging_dir(self):
        staging_dir = os.path.normpath(os.path.join(
            self._migration_root(), "Staging", "claims_uat_staging",
        ))
        os.makedirs(staging_dir, exist_ok=True)
        return staging_dir

    def _append_orchestration_execution_log(self, staging_dir, lines):
        exec_log = os.path.normpath(os.path.join(staging_dir, "claims_uat_orchestration_execution_log.txt"))
        with open(exec_log, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        return exec_log

    def _log_subprocess_stream(self, label, text):
        if not text:
            return
        for line in text.splitlines():
            stripped = line.rstrip()
            if stripped:
                self.log(f"  [{label}] {stripped}")

    def _invoke_external_claims_pipeline(self, staging_dir):
        cfg = self.CLAIMS_ORCHESTRATION
        runner = cfg["orchestration_runner"]
        timeout = cfg.get("orchestration_timeout_seconds", DEFAULT_ORCHESTRATION_TIMEOUT_SECONDS)
        started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        claims_root = self._claims_analysis_root()

        if not os.path.isfile(runner):
            msg = f"Orchestration runner not found: {runner}"
            self.log(f"  CLAIMS PIPELINE ERROR: {msg}")
            self._append_orchestration_execution_log(staging_dir, [
                f"[{started}] EXTERNAL_RUNNER_FAILED",
                f"RUN_MODE={cfg['run_mode']}",
                f"production_dbf_flag={cfg['production_dbf_flag']}",
                f"runner={runner}",
                f"error={msg}",
            ])
            return False

        cmd = [sys.executable, runner]
        env = os.environ.copy()
        env["QLA_CLAIMS_PRELSA_PATH"] = cfg.get("prelsa_source_path", self._resolve_claims_prelsa_path())
        env["QLA_CLAIMS_PACTG_PATH"] = cfg.get("pactg_source_path", self._resolve_claims_pactg_path())
        self.log("CLAIMS PIPELINE: Starting external Phase 17 runner (subprocess)...")
        self.log(f"  Command: {' '.join(cmd)}")
        self.log(f"  Working directory: {claims_root}")
        self.log(f"  Resolved PRELSA lineage source: {env['QLA_CLAIMS_PRELSA_PATH']}")
        self.log(f"  Timeout: {timeout}s")

        return_code = -1
        stdout_text = ""
        stderr_text = ""
        status = "FAILED"
        error_detail = ""

        try:
            result = subprocess.run(
                cmd,
                cwd=claims_root,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                env=env,
            )
            return_code = result.returncode
            stdout_text = result.stdout or ""
            stderr_text = result.stderr or ""
            status = "SUCCESS" if return_code == 0 else "FAILED"
        except subprocess.TimeoutExpired as exc:
            status = "TIMEOUT"
            error_detail = f"Runner exceeded {timeout}s timeout"
            stdout_text = (exc.stdout or "") if exc.stdout else ""
            stderr_text = (exc.stderr or "") if exc.stderr else ""
            self.log(f"  CLAIMS PIPELINE ERROR: {error_detail}")
        except OSError as exc:
            status = "FAILED"
            error_detail = str(exc)
            self.log(f"  CLAIMS PIPELINE ERROR: {error_detail}")

        finished = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log(f"CLAIMS PIPELINE: Completed with status={status} return_code={return_code}")
        self._log_subprocess_stream("stdout", stdout_text)
        self._log_subprocess_stream("stderr", stderr_text)

        self._append_orchestration_execution_log(staging_dir, [
            f"[{finished}] EXTERNAL_RUNNER_{status}",
            f"started={started}",
            f"RUN_MODE={cfg['run_mode']}",
            f"production_dbf_flag={cfg['production_dbf_flag']}",
            f"runner={runner}",
            f"return_code={return_code}",
            f"timeout_seconds={timeout}",
            f"error={error_detail}" if error_detail else "error=",
            "--- stdout ---",
            stdout_text.rstrip() or "(empty)",
            "--- stderr ---",
            stderr_text.rstrip() or "(empty)",
        ])
        if status == "SUCCESS" and self._claims_semantic_governance_enabled():
            self._invoke_phase22_semantic_governance(staging_dir)
        return status == "SUCCESS"

    def _phase22_semantic_governance_dir(self):
        return os.path.normpath(os.path.join(self._claims_analysis_root(), "phase22_semantic_governance"))

    def _invoke_phase22_semantic_governance(self, staging_dir):
        cfg = self.CLAIMS_ORCHESTRATION
        runner = cfg.get("semantic_governance_runner")
        timeout = cfg.get("orchestration_timeout_seconds", DEFAULT_ORCHESTRATION_TIMEOUT_SECONDS)
        claims_root = self._claims_analysis_root()
        started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not runner or not os.path.isfile(runner):
            self.log(f"  PHASE 22 ERROR: semantic governance runner not found: {runner}")
            return False
        cmd = [sys.executable, runner]
        self.log("PHASE 22 SEMANTIC GOVERNANCE (22A/22B): detecting pseudo-claims + QLAdmin alignment...")
        self.log(f"  Command: {' '.join(cmd)}")
        self.log("  Authoritative manuals: docs/claims_conversion_reference/QLAdmin_Help.pdf + LifePRO Accounting Transactions")
        return_code = -1
        stdout_text = ""
        stderr_text = ""
        try:
            proc = subprocess.run(
                cmd, cwd=claims_root, capture_output=True, text=True,
                timeout=timeout, check=False,
            )
            return_code = proc.returncode
            stdout_text = proc.stdout or ""
            stderr_text = proc.stderr or ""
        except subprocess.TimeoutExpired as exc:
            self.log(f"  PHASE 22 ERROR: runner exceeded {timeout}s timeout")
            stdout_text = (exc.stdout or "") if exc.stdout else ""
            stderr_text = (exc.stderr or "") if exc.stderr else ""
        except OSError as exc:
            self.log(f"  PHASE 22 ERROR: {exc}")
        self.log(f"PHASE 22 SEMANTIC GOVERNANCE: Completed return_code={return_code}")
        self._log_subprocess_stream("phase22-stdout", stdout_text)
        self._log_subprocess_stream("phase22-stderr", stderr_text)
        self._append_orchestration_execution_log(staging_dir, [
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] PHASE22_SEMANTIC_GOVERNANCE",
            f"started={started}",
            f"return_code={return_code}",
            f"runner={runner}",
            f"rulebook_lineage={PHASE22_SEMANTIC_GOVERNANCE_LINEAGE}",
            "--- stdout ---",
            stdout_text.rstrip() or "(empty)",
            "--- stderr ---",
            stderr_text.rstrip() or "(empty)",
        ])
        if return_code == 0:
            hold_path = os.path.join(self._phase22_semantic_governance_dir(), "semantic_governance_hold_population.csv")
            self.log(f"  Phase 22 hold manifest: {hold_path}")
        return return_code == 0

    def _load_semantic_governance_hold_index(self):
        hold_path = os.path.join(self._phase22_semantic_governance_dir(), "semantic_governance_hold_population.csv")
        rc_ids = set()
        deriv_ids = set()
        reason_map = {}
        if not os.path.isfile(hold_path):
            return rc_ids, deriv_ids, reason_map, hold_path
        try:
            df = pd.read_csv(hold_path, dtype=str).fillna("")
            df.columns = [str(c).strip().lower() for c in df.columns]
            for _, row in df.iterrows():
                rc = str(row.get("reconstructed_claim_id", "")).strip()
                deriv = str(row.get("derivation_candidate_id", "")).strip()
                reason = str(row.get("reason_excluded", "SEMANTIC_PSEUDO_CLAIM")).strip()
                if rc:
                    rc_ids.add(rc)
                    reason_map[rc] = reason
                if deriv:
                    deriv_ids.add(deriv)
                    reason_map[deriv] = reason
        except Exception:
            pass
        return rc_ids, deriv_ids, reason_map, hold_path

    def _build_semantic_hold_row(
        self, row, table_key, staged_path, dest_path, reason_excluded, mpolicy_raw,
        audit_ts, prod_flag,
    ):
        row_dict = row.to_dict() if hasattr(row, "to_dict") else dict(row)
        normalized = {str(k).strip().lower(): v for k, v in row_dict.items()}
        rc = str(normalized.get("reconstructed_claim_id", "")).strip()
        deriv = str(normalized.get("derivation_candidate_id", "")).strip()
        record_type = "CLAIM" if table_key == "quikclms" else "PAYMENT"
        record_identifier = deriv or rc or str(normalized.get("canonical_payment_stage_id", "")).strip()
        return {
            "audit_timestamp": audit_ts,
            "emit_timestamp": audit_ts,
            "production_dbf_flag": prod_flag,
            "hold_category": SEMANTIC_HOLD_CATEGORY,
            "record_type": record_type,
            "record_identifier": record_identifier,
            "record_id": record_identifier,
            "reconstructed_claim_id": rc,
            "derivation_candidate_id": deriv,
            "MPOLICY": mpolicy_raw,
            "blocker_category": "SEMANTIC_DOMAIN_MISMATCH",
            "reason_excluded": reason_excluded or "SEMANTIC_PSEUDO_CLAIM",
            "reason_held": reason_excluded or "SEMANTIC_PSEUDO_CLAIM",
            "governance_status": "SEMANTIC_GOVERNANCE_HOLD",
            "business_review_required": "Y",
            "business_explanation": SEMANTIC_HOLD_EXPLANATION,
            "remediation_recommendation": SEMANTIC_HOLD_REMEDIATION,
            "source_file": staged_path,
            "target_file": dest_path,
            "rulebook_lineage": PHASE22_SEMANTIC_GOVERNANCE_LINEAGE,
        }

    def _stage_uat_candidate_file(self, staging_dir, table_key, source_path):
        if not source_path or not os.path.isfile(source_path):
            return False, ""
        staged_path = os.path.normpath(os.path.join(staging_dir, f"{table_key}.csv"))
        shutil.copy2(source_path, staged_path)
        return True, staged_path

    def _restage_all_uat_candidates(self, staging_dir):
        cfg = self.CLAIMS_ORCHESTRATION
        staged = []
        for table_key, source_key in (("quikclms", "uat_quikclms_source"), ("quikclmp", "uat_quikclmp_source")):
            ok, path = self._stage_uat_candidate_file(staging_dir, table_key, cfg[source_key])
            if ok:
                staged.append((table_key, path, cfg[source_key]))
        return staged

    def _phase17_governance_dir(self):
        return os.path.normpath(self.CLAIMS_ORCHESTRATION["uat_candidate_dir"])

    def _load_governance_csv_safe(self, filename, directory=None):
        base_dir = directory or self._phase17_governance_dir()
        path = os.path.join(base_dir, filename)
        if not os.path.isfile(path):
            return None
        try:
            df = pd.read_csv(path, dtype=str)
            df.columns = [str(c).strip().lower() for c in df.columns]
            return df
        except Exception:
            return None

    def _count_governance_csv_rows(self, filename, directory=None):
        base_dir = directory or self._phase17_governance_dir()
        path = os.path.join(base_dir, filename)
        if not os.path.isfile(path):
            return None
        try:
            with open(path, encoding="utf-8") as fh:
                return max(sum(1 for _ in fh) - 1, 0)
        except OSError:
            return None

    def _dashboard_kpi_value(self, dashboard_df, kpi_key):
        if dashboard_df is None or dashboard_df.empty or "kpi" not in dashboard_df.columns:
            return None
        if "value" not in dashboard_df.columns:
            return None
        match = dashboard_df[dashboard_df["kpi"].astype(str).str.strip().str.lower() == kpi_key.lower()]
        if match.empty:
            return None
        return str(match.iloc[0]["value"]).strip()

    def _format_governance_metric(self, value, suffix=""):
        if value is None or str(value).strip() == "":
            return "NOT YET GENERATED"
        text = str(value).strip()
        if suffix and not text.endswith(suffix):
            return f"{text}{suffix}"
        return text

    def _top_blocker_from_kpi_summary(self, kpi_df):
        if kpi_df is None or kpi_df.empty:
            return None, None
        if "kpi_name" not in kpi_df.columns or "kpi_value" not in kpi_df.columns:
            return None, None
        blockers = kpi_df[kpi_df["kpi_name"].astype(str).str.startswith("blocker_")].copy()
        if blockers.empty:
            return None, None
        blockers["_val"] = pd.to_numeric(blockers["kpi_value"], errors="coerce").fillna(0)
        top = blockers.sort_values("_val", ascending=False).iloc[0]
        label = str(top["kpi_name"]).replace("blocker_", "").replace("_", " ").strip().title()
        return label, int(top["_val"])

    def _load_phase16_governance_status(self):
        phase16_dir = os.path.join(self._claims_analysis_root(), "phase16_business_triage_remediation")
        df = self._load_governance_csv_safe("phase16_decision_checkpoint.csv", directory=phase16_dir)
        if df is None or df.empty:
            return None, None
        row = df.iloc[0]
        decision = str(row.get("decision_category", "")).strip() or None
        governance = str(row.get("governance_status", "")).strip() or None
        return decision, governance

    def _build_governance_summary(self):
        dashboard = self._load_governance_csv_safe("executive_uat_dashboard.csv")
        kpi_summary = self._load_governance_csv_safe("governance_kpi_summary.csv")
        blocker_trend = self._load_governance_csv_safe("blocker_trend_analysis.csv")
        exclusion_df = self._load_governance_csv_safe("business_exclusion_log.csv")
        cfg = self.CLAIMS_ORCHESTRATION

        top_blocker, top_blocker_count = self._top_blocker_from_kpi_summary(kpi_summary)
        phase16_decision, phase16_governance = self._load_phase16_governance_status()
        exclusion_count = len(exclusion_df) if exclusion_df is not None else None
        surrender_queue = self._count_governance_csv_rows("surrender_review_workbench.csv")
        orphan_queue = self._count_governance_csv_rows("orphan_review_workbench.csv")

        go_live = self._dashboard_kpi_value(dashboard, "go_live_target") or cfg.get("go_live_target", "2026-09-01")
        orphan_reduction = self._dashboard_kpi_value(dashboard, "orphan_reduction")

        if dashboard is None:
            threshold_status = "NOT YET GENERATED"
        elif phase16_governance == "PRODUCTION_BLOCKED" or phase16_decision == "PRODUCTION_BLOCKED":
            threshold_status = "NOT READY"
        else:
            threshold_status = "UAT REVIEW IN PROGRESS"

        if cfg["run_mode"] == "PRODUCTION" and cfg.get("production_authorization_flag") == "Y":
            production_status = "AUTHORIZED (NOT EXECUTED)"
        elif phase16_decision:
            production_status = phase16_decision.replace("_", " ")
        else:
            production_status = "BLOCKED"

        files_present = any(
            os.path.isfile(os.path.join(self._phase17_governance_dir(), name))
            for name in (
                "executive_uat_dashboard.csv",
                "governance_kpi_summary.csv",
                "blocker_trend_analysis.csv",
                "business_exclusion_log.csv",
            )
        )

        return {
            "files_present": files_present,
            "uat_claims": self._dashboard_kpi_value(dashboard, "uat_candidate_claims"),
            "uat_payments": self._dashboard_kpi_value(dashboard, "uat_candidate_payments"),
            "deferred_claims": self._dashboard_kpi_value(dashboard, "deferred_governance_claims"),
            "deferred_payments": self._dashboard_kpi_value(dashboard, "deferred_governance_payments"),
            "orphan_count": self._dashboard_kpi_value(dashboard, "orphan_count_phase15"),
            "recon_pass_pct": self._dashboard_kpi_value(dashboard, "reconciliation_pass_rate_phase15_pct"),
            "replay_recovery": orphan_reduction,
            "top_blocker": top_blocker,
            "top_blocker_count": top_blocker_count,
            "exclusion_records": exclusion_count,
            "surrender_queue": surrender_queue,
            "orphan_queue": orphan_queue,
            "go_live_target": go_live,
            "production_status": production_status,
            "threshold_status": threshold_status,
            "run_mode": cfg["run_mode"],
            "blocker_trend_loaded": blocker_trend is not None,
            **self._load_uat_dbf_panel_status(),
            **self._load_cross_table_validation_panel_status(),
        }

    def _claims_uat_dbf_dir(self):
        return os.path.normpath(os.path.join(
            self._migration_root(), "Staging", CLAIMS_UAT_DBF_SUBDIR,
        ))

    def _uat_emit_csv_paths(self, output_dir):
        return {
            "quikclms": os.path.normpath(os.path.join(output_dir, "quikclms.csv")),
            "quikclmp": os.path.normpath(os.path.join(output_dir, "quikclmp.csv")),
        }

    def _get_governance_rollback_snapshot_reference(self):
        dashboard = self._load_governance_csv_safe("executive_uat_dashboard.csv")
        if dashboard is not None and not dashboard.empty:
            if "rollback_snapshot_id" in dashboard.columns:
                val = str(dashboard.iloc[0]["rollback_snapshot_id"]).strip()
                if val and val.lower() not in ("nan", "none"):
                    return val
        prep_path = os.path.join(self._phase17_governance_dir(), "phase17_execution_summary.txt")
        if os.path.isfile(prep_path):
            return f"See {prep_path}"
        return "NOT_AVAILABLE"

    def _parse_phase21b_uat_dbf_stdout(self, stdout_text):
        parsed = {
            "quikclms": {"csv_rows": None, "dbf_rows": None, "row_match": None},
            "quikclmp": {"csv_rows": None, "dbf_rows": None, "row_match": None},
            "alignment_status": "",
            "alignment_manifest": "",
            "alignment_summary": "",
        }
        for line in (stdout_text or "").splitlines():
            stripped = line.strip()
            for table in ("QUIKCLMS", "QUIKCLMP"):
                key = table.lower()
                csv_match = re.match(rf"{table}_CSV_ROWS:\s*(\d+)", stripped, re.IGNORECASE)
                dbf_match = re.match(rf"{table}_DBF_ROWS:\s*(\d+|UNKNOWN)", stripped, re.IGNORECASE)
                match_match = re.match(rf"{table}_ROW_MATCH:\s*(Y|N|UNKNOWN)", stripped, re.IGNORECASE)
                if csv_match:
                    parsed[key]["csv_rows"] = int(csv_match.group(1))
                if dbf_match:
                    val = dbf_match.group(1)
                    parsed[key]["dbf_rows"] = None if val.upper() == "UNKNOWN" else int(val)
                if match_match:
                    parsed[key]["row_match"] = match_match.group(1).upper()
            status_match = re.match(r"ALIGNMENT_STATUS:\s*(.+)", stripped, re.IGNORECASE)
            manifest_match = re.match(r"ALIGNMENT_MANIFEST:\s*(.+)", stripped, re.IGNORECASE)
            summary_match = re.match(r"ALIGNMENT_SUMMARY:\s*(.+)", stripped, re.IGNORECASE)
            if status_match:
                parsed["alignment_status"] = status_match.group(1).strip()
            if manifest_match:
                parsed["alignment_manifest"] = manifest_match.group(1).strip()
            if summary_match:
                parsed["alignment_summary"] = summary_match.group(1).strip()
        return parsed

    def _load_phase21b_alignment_manifest(self, dbf_dir):
        manifest_path = os.path.join(dbf_dir, CLAIMS_UAT_DBF_ALIGNMENT_MANIFEST)
        if not os.path.isfile(manifest_path):
            return None
        try:
            return pd.read_csv(manifest_path, dtype=str)
        except Exception:
            return None

    def _load_uat_dbf_panel_status(self):
        dbf_dir = self._claims_uat_dbf_dir()
        manifest_path = os.path.join(dbf_dir, CLAIMS_UAT_DBF_MANIFEST)
        if not os.path.isfile(manifest_path):
            return {
                "uat_dbf_status": "NOT YET GENERATED",
                "uat_dbf_timestamp": "NOT YET GENERATED",
                "uat_dbf_folder": dbf_dir,
            }
        try:
            df = pd.read_csv(manifest_path, dtype=str)
            if df.empty:
                raise ValueError("empty manifest")
            ts = str(df.iloc[0].get("generation_timestamp", "")).strip() or "UNKNOWN"
            flags = df.get("generated_flag", pd.Series(dtype=str)).astype(str).str.upper()
            if len(flags) and (flags == "Y").all():
                status = "UAT PROTOTYPE ONLY (NOT PRODUCTION)"
            elif (flags == "Y").any():
                status = "PARTIAL — REVIEW REQUIRED"
            else:
                status = "GENERATION FAILED"
            return {
                "uat_dbf_status": status,
                "uat_dbf_timestamp": ts,
                "uat_dbf_folder": dbf_dir,
            }
        except Exception:
            return {
                "uat_dbf_status": "MANIFEST READ ERROR",
                "uat_dbf_timestamp": "NOT YET GENERATED",
                "uat_dbf_folder": dbf_dir,
            }

    def _write_claims_uat_dbf_manifest(self, dbf_dir, manifest_rows):
        manifest_path = os.path.normpath(os.path.join(dbf_dir, CLAIMS_UAT_DBF_MANIFEST))
        fieldnames = [
            "dbf_name", "source_csv", "generated_flag", "generation_timestamp", "record_count",
            "production_dbf_flag", "governance_population", "deferred_population_included",
            "run_mode", "rollback_snapshot_reference",
        ]
        with open(manifest_path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(manifest_rows)
        return manifest_path

    def _write_claims_uat_dbf_summary(self, dbf_dir, emit_result, dbf_result):
        cfg = self.CLAIMS_ORCHESTRATION
        go_live = cfg.get("go_live_target", "2026-09-01")
        emitted = emit_result.get("emitted", {}) if emit_result else {}
        clms_rows = (emitted.get("quikclms") or {}).get("row_count", "N/A")
        clmp_rows = (emitted.get("quikclmp") or {}).get("row_count", "N/A")
        hold_count = emit_result.get("hold_count", "N/A") if emit_result else "N/A"
        alignment = dbf_result.get("alignment", {}) or {}
        lines = [
            "QLAdmin Enterprise Claims — UAT DBF Generation Summary (Phase 21B)",
            "=" * 60,
            "",
            "IMPORTANT — UAT REHEARSAL ONLY",
            "-" * 30,
            "DBF files were generated directly from the final emitted UAT CSV files.",
            "Deferred and governance-hold records were excluded at Phase 21 emit.",
            "This is NOT production cutover.",
            "This is NOT production authorized DBF generation.",
            f"production_dbf_flag={cfg.get('production_dbf_flag', 'N')}",
            f"governance_population={UAT_DBF_GOVERNANCE_POPULATION}",
            "deferred_population_included=N",
            f"rulebook_lineage={PHASE21B_UAT_DBF_LINEAGE}",
            f"Go-Live Target: {go_live}",
            "",
            "EMITTED UAT CSV POPULATION",
            "-" * 30,
            f"Governance-cleared UAT claims emitted: {clms_rows}",
            f"Governance-cleared UAT payments emitted: {clmp_rows}",
            f"Deferred/excluded records held for review: {hold_count}",
            "",
            "ROW ALIGNMENT",
            "-" * 30,
            f"Alignment status: {alignment.get('status', dbf_result.get('alignment_status', 'UNKNOWN'))}",
            f"QUIKCLMS CSV/DBF row match: {alignment.get('quikclms_row_match', 'UNKNOWN')}",
            f"QUIKCLMP CSV/DBF row match: {alignment.get('quikclmp_row_match', 'UNKNOWN')}",
            f"Alignment manifest: {dbf_result.get('alignment_manifest_path', '')}",
            f"Alignment summary: {dbf_result.get('alignment_summary_path', '')}",
            "",
            "DBF GENERATION RESULT",
            "-" * 30,
            f"Status: {dbf_result.get('status', 'UNKNOWN')}",
            f"Output folder: {dbf_dir}",
            f"Rollback snapshot reference: {dbf_result.get('rollback_snapshot_reference', 'NOT_AVAILABLE')}",
            "",
            "Generated by app.py Phase 21B UAT DBF-from-CSV subprocess hook.",
            "Authoritative source: output/quikclms.csv and output/quikclmp.csv only.",
        ]
        if dbf_result.get("error"):
            lines.extend(["", "Error detail:", str(dbf_result["error"])])
        summary_path = os.path.join(dbf_dir, CLAIMS_UAT_DBF_SUMMARY)
        with open(summary_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        return summary_path

    def _invoke_external_uat_dbf_generation(self, emit_result):
        cfg = self.CLAIMS_ORCHESTRATION
        dbf_dir = self._claims_uat_dbf_dir()
        os.makedirs(dbf_dir, exist_ok=True)

        generation_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rollback_ref = self._get_governance_rollback_snapshot_reference()
        output_dir = emit_result.get("output_dir") or self._resolve_output_base_dir()
        csv_paths = self._uat_emit_csv_paths(output_dir)
        prod_flag = cfg.get("production_dbf_flag", "N")
        run_mode = cfg.get("run_mode", "UAT")
        gov_pop = UAT_DBF_GOVERNANCE_POPULATION

        base_result = {
            "status": "FAILED",
            "generation_timestamp": generation_ts,
            "dbf_dir": dbf_dir,
            "rollback_snapshot_reference": rollback_ref,
            "manifest_path": None,
            "summary_path": None,
            "alignment_manifest_path": None,
            "alignment_summary_path": None,
            "alignment_status": "FAILED",
            "error": "",
            "manifest_rows": [],
            "alignment": {},
        }

        for table_key, csv_path in csv_paths.items():
            if not os.path.isfile(csv_path):
                base_result["error"] = f"UAT emit CSV missing (required gate): {csv_path}"
                self.log(f"  UAT DBF ERROR: {base_result['error']}")
                return base_result

        runner = cfg.get("uat_dbf_generator_runner")
        timeout = cfg.get("uat_dbf_timeout_seconds", DEFAULT_ORCHESTRATION_TIMEOUT_SECONDS)
        claims_root = self._claims_analysis_root()

        if not runner or not os.path.isfile(runner):
            base_result["error"] = f"Phase 21B UAT DBF runner not found: {runner}"
            self.log(f"  UAT DBF ERROR: {base_result['error']}")
            return base_result

        cmd = [
            sys.executable, runner,
            "--clms-csv", csv_paths["quikclms"],
            "--clmp-csv", csv_paths["quikclmp"],
            "--output-dir", dbf_dir,
            "--run-mode", run_mode,
        ]
        self.log("UAT DBF GENERATION (Phase 21B): from final emitted CSV only...")
        self.log(f"  Command: {' '.join(cmd)}")
        self.log(f"  Working directory: {claims_root}")
        self.log(f"  Authoritative CSVs: {csv_paths['quikclms']} | {csv_paths['quikclmp']}")

        return_code = -1
        stdout_text = ""
        stderr_text = ""
        subprocess_status = "FAILED"
        error_detail = ""

        try:
            proc = subprocess.run(
                cmd,
                cwd=claims_root,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            return_code = proc.returncode
            stdout_text = proc.stdout or ""
            stderr_text = proc.stderr or ""
            subprocess_status = "SUCCESS" if return_code == 0 else "FAILED"
        except subprocess.TimeoutExpired as exc:
            subprocess_status = "TIMEOUT"
            error_detail = f"Phase 21B runner exceeded {timeout}s timeout"
            stdout_text = (exc.stdout or "") if exc.stdout else ""
            stderr_text = (exc.stderr or "") if exc.stderr else ""
        except OSError as exc:
            subprocess_status = "FAILED"
            error_detail = str(exc)

        self.log(f"UAT DBF GENERATION: Completed subprocess_status={subprocess_status} return_code={return_code}")
        self._log_subprocess_stream("uat-dbf-stdout", stdout_text)
        self._log_subprocess_stream("uat-dbf-stderr", stderr_text)

        exec_log = os.path.join(dbf_dir, "claims_uat_dbf_execution_log.txt")
        with open(exec_log, "a", encoding="utf-8") as fh:
            fh.write("\n".join([
                f"[{generation_ts}] UAT_DBF_{subprocess_status}",
                f"return_code={return_code}",
                f"production_dbf_flag={prod_flag}",
                f"governance_population={gov_pop}",
                f"rulebook_lineage={PHASE21B_UAT_DBF_LINEAGE}",
                f"runner={runner}",
                f"error={error_detail}" if error_detail else "error=",
                "--- stdout ---",
                stdout_text.rstrip() or "(empty)",
                "--- stderr ---",
                stderr_text.rstrip() or "(empty)",
            ]) + "\n")

        parsed = self._parse_phase21b_uat_dbf_stdout(stdout_text)
        alignment_manifest_path = parsed.get("alignment_manifest") or os.path.join(dbf_dir, CLAIMS_UAT_DBF_ALIGNMENT_MANIFEST)
        alignment_summary_path = parsed.get("alignment_summary") or os.path.join(dbf_dir, CLAIMS_UAT_DBF_ALIGNMENT_SUMMARY)
        if not os.path.isfile(alignment_manifest_path):
            alignment_manifest_path = os.path.join(dbf_dir, CLAIMS_UAT_DBF_ALIGNMENT_MANIFEST)
        if not os.path.isfile(alignment_summary_path):
            alignment_summary_path = os.path.join(dbf_dir, CLAIMS_UAT_DBF_ALIGNMENT_SUMMARY)

        alignment_df = self._load_phase21b_alignment_manifest(dbf_dir)
        table_map = [
            (QUIKCLMS_UAT_DBF_NAME, "quikclms"),
            (QUIKCLMP_UAT_DBF_NAME, "quikclmp"),
        ]
        manifest_rows = []
        all_generated = True
        alignment_matches = []

        for uat_name, table_key in table_map:
            dest_dbf = os.path.join(dbf_dir, uat_name)
            generated = subprocess_status == "SUCCESS" and os.path.isfile(dest_dbf)
            if not generated:
                all_generated = False
            csv_source = csv_paths[table_key]
            csv_rows = self._count_csv_data_rows(csv_source)
            table_parsed = parsed.get(table_key, {})
            row_match = table_parsed.get("row_match")
            dbf_rows = table_parsed.get("dbf_rows")

            if alignment_df is not None and not alignment_df.empty:
                row_df = alignment_df[alignment_df["dbf_name"].astype(str).str.upper() == uat_name.upper()]
                if not row_df.empty:
                    row_match = str(row_df.iloc[0].get("row_count_match", row_match or "")).strip().upper() or row_match
                    dbf_val = str(row_df.iloc[0].get("dbf_row_count", "")).strip()
                    if dbf_val and dbf_val.upper() != "UNKNOWN":
                        try:
                            dbf_rows = int(float(dbf_val))
                        except ValueError:
                            pass

            if row_match:
                alignment_matches.append(row_match)
            manifest_rows.append({
                "dbf_name": uat_name,
                "source_csv": csv_source,
                "generated_flag": "Y" if generated else "N",
                "generation_timestamp": generation_ts,
                "record_count": csv_rows,
                "production_dbf_flag": prod_flag,
                "governance_population": gov_pop,
                "deferred_population_included": "N",
                "run_mode": run_mode,
                "rollback_snapshot_reference": rollback_ref,
            })
            if generated and row_match == "N":
                error_detail = error_detail or f"Row count mismatch for {uat_name}: CSV={csv_rows} DBF={dbf_rows}"

        if parsed.get("alignment_status"):
            alignment_status = parsed["alignment_status"].upper()
        elif alignment_matches and all(m == "Y" for m in alignment_matches):
            alignment_status = "PASS"
        elif any(m == "N" for m in alignment_matches):
            alignment_status = "FAILED"
        elif alignment_matches and any(m == "UNKNOWN" for m in alignment_matches):
            alignment_status = "UNKNOWN"
        else:
            alignment_status = "UNKNOWN"

        if subprocess_status != "SUCCESS":
            final_status = subprocess_status
        elif not all_generated:
            final_status = "FAILED"
            error_detail = error_detail or "One or more UAT DBF files were not produced"
        elif alignment_status == "PASS":
            final_status = "SUCCESS"
        elif alignment_status == "FAILED":
            final_status = "FAILED"
            error_detail = error_detail or "CSV and DBF row counts do not match"
        else:
            final_status = "UNKNOWN"
            error_detail = error_detail or "DBF row count alignment could not be verified"

        manifest_path = self._write_claims_uat_dbf_manifest(dbf_dir, manifest_rows)
        rollback_path = os.path.join(dbf_dir, CLAIMS_UAT_DBF_ROLLBACK_REF)
        with open(rollback_path, "w", encoding="utf-8") as fh:
            fh.write(f"rollback_snapshot_reference={rollback_ref}\n")
            fh.write(f"generation_timestamp={generation_ts}\n")
            fh.write("production_dbf_flag=N\n")
            fh.write(f"governance_population={gov_pop}\n")
            fh.write(f"rulebook_lineage={PHASE21B_UAT_DBF_LINEAGE}\n")

        result = {
            "status": final_status,
            "generation_timestamp": generation_ts,
            "dbf_dir": dbf_dir,
            "rollback_snapshot_reference": rollback_ref,
            "manifest_path": manifest_path,
            "summary_path": None,
            "alignment_manifest_path": alignment_manifest_path if os.path.isfile(alignment_manifest_path) else None,
            "alignment_summary_path": alignment_summary_path if os.path.isfile(alignment_summary_path) else None,
            "alignment_status": alignment_status,
            "error": error_detail,
            "manifest_rows": manifest_rows,
            "return_code": return_code,
            "alignment": {
                "status": alignment_status,
                "quikclms_row_match": parsed.get("quikclms", {}).get("row_match", "UNKNOWN"),
                "quikclmp_row_match": parsed.get("quikclmp", {}).get("row_match", "UNKNOWN"),
            },
        }
        result["summary_path"] = self._write_claims_uat_dbf_summary(dbf_dir, emit_result, result)
        return result

    def _log_claims_uat_dbf_summary(self, dbf_result):
        if not dbf_result:
            return
        self.log("UAT DBF SUMMARY (Phase 21B — NOT PRODUCTION):")
        self.log(f"  Status: {dbf_result.get('status', 'UNKNOWN')}")
        self.log(f"  Alignment: {dbf_result.get('alignment_status', 'UNKNOWN')}")
        self.log(f"  Output folder: {dbf_result.get('dbf_dir', '')}")
        for row in dbf_result.get("manifest_rows", []):
            self.log(
                f"  {row.get('dbf_name')}: generated={row.get('generated_flag')} "
                f"records={row.get('record_count')} source={row.get('source_csv')}"
            )
        self.log(f"  Manifest: {dbf_result.get('manifest_path', '')}")
        self.log(f"  Alignment manifest: {dbf_result.get('alignment_manifest_path', '')}")
        self.log(f"  Alignment summary: {dbf_result.get('alignment_summary_path', '')}")
        self.log(f"  Summary: {dbf_result.get('summary_path', '')}")
        self.log(f"  governance_population={UAT_DBF_GOVERNANCE_POPULATION} | deferred_population_included=N")
        self.log(f"  rulebook_lineage={PHASE21B_UAT_DBF_LINEAGE}")
        if dbf_result.get("error"):
            self.log(f"  UAT DBF WARNING: {dbf_result['error']}")
            self.log("  CSV emit and review manifest remain valid.")

    def _maybe_generate_uat_claims_dbf(self, emit_result):
        if not self._claims_uat_dbf_generation_enabled():
            return None
        if not emit_result:
            self.log("UAT DBF generation skipped — no CSV emit result available.")
            return None
        if emit_result.get("validation_blocked") or emit_result.get("validation_error"):
            self.log("UAT DBF generation skipped — MPOLICY cross-table validation blocked emit.")
            return None
        if emit_result.get("validation_ok") is False:
            self.log("UAT DBF generation skipped — validated CSV emit did not complete.")
            return None
        self.log("UAT DBF GENERATION (Phase 21B): gated on validated output/quikclms.csv + quikclmp.csv...")
        dbf_result = self._invoke_external_uat_dbf_generation(emit_result)
        self._last_uat_dbf_result = dbf_result
        self._log_claims_uat_dbf_summary(dbf_result)
        return dbf_result

    def _ui_action_button(self, parent, text, color, command, width=16, pady=7):
        """Flat web-style action button (tkinter approximation of a SaaS toolbar control)."""
        return tk.Button(
            parent,
            text=text,
            bg=color,
            fg="white",
            activebackground=color,
            activeforeground="white",
            disabledforeground="#CBD5E1",
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=pady,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
            width=width,
            command=command,
        )

    def _ui_section_label(self, parent, text):
        return tk.Label(
            parent, text=text.upper(), bg=self.bg_card, fg=self.brand_red,
            font=("Segoe UI", 8, "bold"), anchor="w",
        )

    def _ui_kpi_tile(self, parent, title, var, column):
        shell = tk.Frame(
            parent, bg=self.bg_card,
            highlightbackground=self.ui_strip_border, highlightthickness=1,
        )
        shell.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 0))
        parent.grid_columnconfigure(column, weight=1, uniform="kpi")
        tk.Frame(shell, bg=self.brand_red, height=3).pack(fill="x")
        tile = tk.Frame(shell, bg=self.ui_strip_bg, padx=12, pady=10)
        tile.pack(fill="both", expand=True)
        tk.Label(
            tile, text=title.upper(), bg=self.ui_strip_bg, fg=self.brand_red,
            font=("Segoe UI", 8, "bold"), anchor="w",
        ).pack(fill="x")
        value_lbl = tk.Label(
            tile, textvariable=var, bg=self.ui_strip_bg, fg=self.brand_red_deep,
            font=("Segoe UI", 10, "bold"), anchor="w", wraplength=220, justify="left",
        )
        value_lbl.pack(fill="x", pady=(6, 0))
        return value_lbl

    def _setup_top_nav(self):
        nav = tk.Frame(self.root, bg=self.bg_nav, height=72)
        nav.pack(fill="x")
        nav.pack_propagate(False)
        inner = tk.Frame(nav, bg=self.bg_nav)
        inner.pack(fill="both", expand=True, padx=24, pady=8)
        left = tk.Frame(inner, bg=self.bg_nav)
        left.pack(side="left", fill="y")
        tk.Label(
            left, text=APP_BRAND, bg=self.bg_nav, fg="#FFFFFF",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")
        # Fixed-height tagline slot so rotation never shifts the layout.
        tagline_slot = tk.Frame(left, bg=self.bg_nav, height=22)
        tagline_slot.pack(anchor="w", fill="x", pady=(2, 0))
        tagline_slot.pack_propagate(False)
        self._tagline_label = tk.Label(
            tagline_slot,
            text=APP_TAGLINE,
            bg=self.bg_nav,
            fg="#FFFFFF",
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
            wraplength=720,
        )
        self._tagline_label.pack(fill="both", expand=True)
        # Decorative / non-urgent: screen readers should not treat rotations as alerts.
        try:
            self._tagline_label.configure(takefocus=0)
        except Exception:
            pass
        right = tk.Frame(inner, bg=self.bg_nav)
        right.pack(side="right", anchor="n")
        tk.Label(
            right,
            text=f"{APP_BRAND} | Version {APP_VERSION}",
            bg=self.bg_nav,
            fg="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
        ).pack(side="right")
        tk.Frame(self.root, bg=self.brand_red_dark, height=3).pack(fill="x")
        if self._tagline_rotator is not None:
            self._tagline_rotator.close()
        self._tagline_rotator = TaglineRotator(
            self.root,
            self._tagline_label,
            taglines=QUIKCONVERT_TAGLINES,
            interval_ms=TAGLINE_ROTATION_INTERVAL_MS,
            fg_active="#FFFFFF",
            fg_muted=self.bg_nav_muted,
            bg=self.bg_nav,
        )
        try:
            self.root.protocol("WM_DELETE_WINDOW", self._on_app_close)
        except Exception:
            pass

    def _on_app_close(self):
        if self._tagline_rotator is not None:
            self._tagline_rotator.close()
            self._tagline_rotator = None
        self.root.destroy()

    def _setup_uat_status_banner(self):
        self.gov_banner_frame = tk.Frame(
            self.root, bg=self.bg_card, padx=18, pady=14,
            highlightbackground=self.ui_strip_border, highlightthickness=1,
        )
        self.gov_banner_frame.pack(fill="x", padx=24, pady=(14, 8))

        title_row = tk.Frame(self.gov_banner_frame, bg=self.bg_card)
        title_row.pack(fill="x")
        tk.Label(
            title_row, text="Operator Console",
            bg=self.bg_card, fg=self.brand_red, font=("Segoe UI", 12, "bold"), anchor="w",
        ).pack(side="left")
        self.dash_project_var = tk.StringVar(value=self._ui_project_label())
        tk.Label(
            title_row, textvariable=self.dash_project_var, bg=self.bg_card,
            fg=self.ui_status_muted, font=("Segoe UI", 9), anchor="e",
        ).pack(side="right")

        kpi = tk.Frame(self.gov_banner_frame, bg=self.bg_card)
        kpi.pack(fill="x", pady=(12, 0))
        self.dash_source_var = tk.StringVar(value="—")
        self.dash_output_var = tk.StringVar(value="—")
        self.dash_validation_var = tk.StringVar(value="—")
        self.dash_run_state_var = tk.StringVar(value="Ready")
        self._ui_kpi_tile(kpi, "Source Package", self.dash_source_var, 0)
        self._ui_kpi_tile(kpi, "Output Readiness", self.dash_output_var, 1)
        self._ui_kpi_tile(kpi, "Governance Status", self.dash_validation_var, 2)
        self.dash_run_state_badge = self._ui_kpi_tile(kpi, "Run State", self.dash_run_state_var, 3)

        meta = tk.Frame(self.gov_banner_frame, bg=self.bg_card)
        meta.pack(fill="x", pady=(10, 0))
        self.dash_last_run_var = tk.StringVar(value="—")
        self.dash_last_validation_var = tk.StringVar(value="—")
        self.env_status_var = tk.StringVar(value=f"Environment: {self.RUN_MODE}")
        self.prod_output_status_var = tk.StringVar(value="Production Output: Disabled")
        self.readiness_status_var = tk.StringVar(value="Readiness Review: Awaiting Data")
        self.golive_status_var = tk.StringVar(value="Go-Live Target: —")
        for idx, var in enumerate((
            self.dash_last_run_var, self.dash_last_validation_var,
            self.env_status_var, self.readiness_status_var,
        )):
            prefix = ("Last Run", "Last Governance", "", "")[idx]
            if prefix:
                tk.Label(
                    meta, text=f"{prefix}:", bg=self.bg_card, fg=self.ui_status_muted,
                    font=("Segoe UI", 8),
                ).grid(row=0, column=idx * 2, sticky="w", padx=(0, 4))
                tk.Label(
                    meta, textvariable=var, bg=self.bg_card, fg=self.accent,
                    font=("Segoe UI", 8, "bold"),
                ).grid(row=0, column=idx * 2 + 1, sticky="w", padx=(0, 18))
            else:
                tk.Label(
                    meta, textvariable=var, bg=self.bg_card, fg=self.text_color,
                    font=("Segoe UI", 8),
                ).grid(row=0, column=idx * 2, sticky="w", padx=(0, 18))

        divider = tk.Frame(self.gov_banner_frame, bg=self.brand_red, height=2)
        divider.pack(fill="x", pady=(12, 10))

        self._ui_section_label(self.gov_banner_frame, "Operations").pack(fill="x")
        ops = tk.Frame(self.gov_banner_frame, bg=self.bg_card)
        ops.pack(fill="x", pady=(6, 0))
        primary_actions = [
            ("Product Setup", self.btn_product, self.start_product_setup_from_ui),
            ("Full Batch", self.btn_batch, lambda: self.start_thread(True)),
            ("Single Table", self.btn_action, lambda: self.start_thread(False)),
            ("Rate Tables", self.btn_rates, self.start_rate_loader_thread),
            ("Governance Audit", self.btn_gov, self.start_governance_audit_thread),
            ("Balancing", self.btn_balancing, self.start_balancing_thread),
        ]
        for text, color, cmd in primary_actions:
            self._ui_action_button(ops, text, color, cmd, width=16).pack(side="left", padx=(0, 8))

        self._ui_section_label(self.gov_banner_frame, "Workspace").pack(fill="x", pady=(12, 0))
        workspace = tk.Frame(self.gov_banner_frame, bg=self.bg_card)
        workspace.pack(fill="x", pady=(6, 0))
        self._ui_action_button(
            workspace, "Open Output", self.btn_action, self._ui_open_output_folder, width=14, pady=5,
        ).pack(side="left", padx=(0, 8))
        self._ui_action_button(
            workspace, "Open Reports", self.btn_secondary, self._ui_open_reports_folder, width=14, pady=5,
        ).pack(side="left")

        self.gov_alert_badge = tk.Label(
            self.gov_banner_frame, text="", bg=self.bg_card,
            fg=self.ui_status_muted, font=("Segoe UI", 8), anchor="w",
        )
        self.gov_alert_badge.pack(fill="x", pady=(10, 0))

    def _setup_diagnostics_panel(self):
        panel = tk.LabelFrame(
            self.root,
            text=" Advanced / Diagnostics ",
            bg=self.bg_card,
            fg=self.accent,
            padx=16,
            pady=8,
            font=("Segoe UI", 10, "bold"),
            highlightbackground=self.ui_strip_border, highlightthickness=1, bd=0, labelanchor="nw",
        )
        panel.pack(padx=24, fill="x", pady=(0, 8))

        header = tk.Frame(panel, bg=self.bg_card)
        header.pack(fill="x")
        self.diagnostics_visible = tk.BooleanVar(value=False)
        tk.Checkbutton(
            header, text="Show Advanced / Diagnostics", variable=self.diagnostics_visible,
            bg=self.bg_card, fg=self.text_color, font=("Segoe UI", 9),
            command=self._ui_toggle_diagnostics,
        ).pack(side="left")
        tk.Button(
            header, text="Refresh All Status", width=18,
            command=self._refresh_all_status_panels,
        ).pack(side="right", padx=(0, 4))

        self.diagnostics_body = tk.Frame(panel, bg=self.bg_card)
        self.diag_notebook = ttk.Notebook(self.diagnostics_body)
        self.diag_notebook.pack(fill="x", pady=(6, 0))

        claims_tab = tk.Frame(self.diag_notebook, bg=self.bg_card)
        product_tab = tk.Frame(self.diag_notebook, bg=self.bg_card)
        rate_tab = tk.Frame(self.diag_notebook, bg=self.bg_card)
        system_tab = tk.Frame(self.diag_notebook, bg=self.bg_card)
        self.diag_notebook.add(claims_tab, text="Claims UAT")
        self.diag_notebook.add(product_tab, text="Product Setup")
        self.diag_notebook.add(rate_tab, text="Rate Tables")
        self.diag_notebook.add(system_tab, text="System Flags")

        self.gov_metric_vars = {}
        claims_metrics = [
            ("uat_claims", "UAT Candidate Claims:"),
            ("uat_payments", "UAT Candidate Payments:"),
            ("deferred_claims", "Deferred Claims:"),
            ("deferred_payments", "Deferred Payments:"),
            ("orphan_count", "Orphan Count (Phase 15):"),
            ("recon_pass_pct", "Reconciliation Pass %:"),
            ("replay_recovery", "Replay Orphan Recovery:"),
            ("top_blocker", "Top Blocker Category:"),
            ("exclusion_records", "Exclusion Log Records:"),
            ("surrender_queue", "Surrender Review Queue:"),
            ("orphan_queue", "Orphan Review Queue:"),
            ("uat_dbf_status", "UAT DBF Generation Status:"),
            ("uat_dbf_timestamp", "Last DBF Generation Timestamp:"),
            ("uat_dbf_folder", "UAT DBF Folder Path:"),
            ("mpolicy_validation_status", "MPOLICY Validation Status:"),
            ("claims_held_missing_policy", "Claims Held For Missing Policy:"),
            ("payments_held_missing_policy", "Payments Held For Missing Policy:"),
            ("cross_table_validation_report", "Cross-Table Validation Report Path:"),
        ]
        claims_grid = tk.Frame(claims_tab, bg=self.bg_card)
        claims_grid.pack(fill="x", padx=4, pady=4)
        for idx, (key, label_text) in enumerate(claims_metrics):
            row, col = divmod(idx, 2)
            tk.Label(claims_grid, text=label_text, bg=self.bg_card, fg=self.text_color, font=("Segoe UI", 9, "bold")).grid(
                row=row, column=col * 2, sticky="w", padx=(0, 6), pady=2,
            )
            var = tk.StringVar(value="NOT YET GENERATED")
            self.gov_metric_vars[key] = var
            tk.Label(claims_grid, textvariable=var, bg=self.bg_card, fg=self.accent, font=("Consolas", 8)).grid(
                row=row, column=col * 2 + 1, sticky="w", padx=(0, 20), pady=2,
            )
        claims_actions = tk.Frame(claims_tab, bg=self.bg_card)
        claims_actions.pack(fill="x", pady=(6, 4))
        tk.Button(claims_actions, text="View Exclusion Log", width=18, command=lambda: self._view_governance_log("business_exclusion_log.csv")).pack(side="left", padx=4)
        tk.Button(claims_actions, text="View Issue Examples", width=18, command=lambda: self._view_governance_log("representative_issue_examples.csv")).pack(side="left", padx=4)
        tk.Button(claims_actions, text="View Exception Catalog", width=20, command=lambda: self._view_governance_log("governance_exception_catalog.csv")).pack(side="left", padx=4)
        tk.Button(
            claims_actions, text="CREATE UAT BUSINESS PACKAGE", width=28, bg=self.btn_batch, fg="white",
            command=self._on_create_uat_business_package,
        ).pack(side="right", padx=4)

        self.product_metric_vars = {}
        product_metrics = [
            ("product_status", "Last Run Status:"),
            ("product_rows", "Staged Rows:"),
            ("product_validation", "Parallel Validation (P2A):"),
            ("product_warnings", "Validation Warnings:"),
            ("product_errors", "Validation Errors:"),
            ("product_staged_path", "Staged Output:"),
            ("product_emitted_path", "Emitted Output:"),
            ("product_isolation", "Batch Isolation:"),
        ]
        product_grid = tk.Frame(product_tab, bg=self.bg_card)
        product_grid.pack(fill="x", padx=4, pady=4)
        for idx, (key, label_text) in enumerate(product_metrics):
            row, col = divmod(idx, 2)
            tk.Label(product_grid, text=label_text, bg=self.bg_card, fg=self.text_color, font=("Segoe UI", 9, "bold")).grid(
                row=row, column=col * 2, sticky="w", padx=(0, 6), pady=2,
            )
            var = tk.StringVar(value="NOT YET RUN")
            self.product_metric_vars[key] = var
            tk.Label(product_grid, textvariable=var, bg=self.bg_card, fg=self.accent, font=("Consolas", 8)).grid(
                row=row, column=col * 2 + 1, sticky="w", padx=(0, 20), pady=2,
            )

        self.rate_metric_vars = {}
        rate_metrics = [
            ("rate_status", "Last Run Status:"),
            ("rate_blockers", "Validation Blockers:"),
            ("rate_tables", "Tables Written:"),
            ("rate_csv_rows", "CSV Rows Written:"),
            ("rate_csv_dir", "CSV Output Folder:"),
            ("rate_dbf_dir", "Sandbox DBF Folder:"),
        ]
        rate_grid = tk.Frame(rate_tab, bg=self.bg_card)
        rate_grid.pack(fill="x", padx=4, pady=4)
        for idx, (key, label_text) in enumerate(rate_metrics):
            row, col = divmod(idx, 2)
            tk.Label(rate_grid, text=label_text, bg=self.bg_card, fg=self.text_color, font=("Segoe UI", 9, "bold")).grid(
                row=row, column=col * 2, sticky="w", padx=(0, 6), pady=2,
            )
            var = tk.StringVar(value="NOT YET RUN")
            self.rate_metric_vars[key] = var
            tk.Label(rate_grid, textvariable=var, bg=self.bg_card, fg=self.accent, font=("Consolas", 8)).grid(
                row=row, column=col * 2 + 1, sticky="w", padx=(0, 20), pady=2,
            )

        self.system_diag_vars = {}
        system_metrics = [
            ("diag_run_mode", "RUN_MODE:"),
            ("diag_production_dbf", "production_dbf_flag:"),
            ("diag_production_status", "Internal Production Status:"),
            ("diag_threshold_status", "Review Threshold Status:"),
            ("diag_production_auth", "production_authorization_flag:"),
        ]
        system_grid = tk.Frame(system_tab, bg=self.bg_card)
        system_grid.pack(fill="x", padx=4, pady=4)
        for idx, (key, label_text) in enumerate(system_metrics):
            tk.Label(system_grid, text=label_text, bg=self.bg_card, fg=self.text_color, font=("Segoe UI", 9, "bold")).grid(
                row=idx, column=0, sticky="w", padx=(0, 6), pady=2,
            )
            var = tk.StringVar(value="—")
            self.system_diag_vars[key] = var
            tk.Label(system_grid, textvariable=var, bg=self.bg_card, fg=self.accent, font=("Consolas", 8)).grid(
                row=idx, column=1, sticky="w", pady=2,
            )

    def _refresh_all_status_panels(self):
        self._refresh_governance_visibility()
        self._refresh_product_setup_visibility()
        self._refresh_rate_loader_visibility()
        self._ui_update_status_strip()

    def _setup_governance_summary_panel(self):
        """Legacy hook — governance metrics now live in Diagnostics tab."""
        pass

    def _product_setup_runner_path(self):
        return os.path.normpath(os.path.join(
            self._app_base_dir(), "plan_governance", "phase_p2_product_setup_runner", "product_setup_runner.py",
        ))

    def _product_setup_isolated(self):
        flag = os.environ.get("QLA_PRODUCT_SETUP_ISOLATED", "0").strip().lower()
        if hasattr(self, "product_isolated_var") and self.product_isolated_var.get():
            return True
        return flag in ("1", "true", "yes")

    def _closed_mplan_authority_enabled(self):
        return closed_mplan_authority_enabled()

    def _allow_legacy_mplan_fallback(self):
        return allow_legacy_mplan_fallback()

    def _is_paid_up_addition_product(self, source_plan_code, cw_map=None):
        """True when LifePRO PLAN_CODE or its crosswalk catalog code is a PUA product."""
        code = self.normalize(source_plan_code).upper()
        if code in PAID_UP_ADDITION_PRODUCTS:
            return True
        if code in PAID_UP_ADDITION_LIFEPRO_SOURCE_CODES:
            return True
        if cw_map:
            mapped = self.normalize(cw_map.get(code, "")).upper()
            if mapped in PAID_UP_ADDITION_PRODUCTS:
                return True
        return False

    def _quikridr_status_code_int(self, raw):
        """Parse QUIKRIDR/QUIKMSTR status code for Issue #60 active-base check."""
        try:
            return int(re.sub(r"[^0-9]", "", str(raw).strip() or "") or "99")
        except ValueError:
            return 99

    def _cache_quikridr_base_phase(self, base_phase_cache, mpolicy, row_data):
        """Store converted Phase 1 fields for PUA inheritance (quikridr only)."""
        if not mpolicy:
            return
        base_phase_cache[mpolicy] = {
            "MPLAN": self.normalize(row_data.get("MPLAN", "")),
            "MEXPRY": self.normalize(row_data.get("MEXPRY", "")),
            "MPAYUP": self.normalize(row_data.get("MPAYUP", "")),
            "MEFFDATE": self.normalize(row_data.get("MEFFDATE", "")),
            "MAGE": self.normalize(row_data.get("MAGE", "")),
            "MPHSTAT": self.normalize(row_data.get("MPHSTAT", "")),
        }

    def _apply_pua_rider_inheritance(self, row_data, mpolicy, source_plan_code, base_phase_cache, cw_map=None):
        """PUA riders inherit base phase dates/age/status; other riders are not touched."""
        if not self._is_paid_up_addition_product(source_plan_code, cw_map):
            return row_data
        # Issue #119: PUA coverage is never participating. QLAdmin sets PAR/MPAR=0 on PA add
        # even when the base coverage is participating (Robert 2026-07-27).
        row_data["MPAR"] = "0"
        entry = base_phase_cache.get(mpolicy)
        if not entry:
            self.log(f"PUA RULE WARNING: Base phase not found for policy {mpolicy}")
            return row_data
        base_mplan = entry.get("MPLAN", "")
        new_mplan = (base_mplan[:4] + "PA") if base_mplan else ""
        base_meff = entry.get("MEFFDATE", "")
        base_mage = entry.get("MAGE", "")
        row_data["MPLAN"] = new_mplan
        row_data["MEXPRY"] = entry.get("MEXPRY", row_data.get("MEXPRY", ""))
        if base_meff:
            row_data["MEFFDATE"] = base_meff
            row_data["MPAYUP"] = base_meff
        if base_mage:
            row_data["MAGE"] = base_mage
        base_status = self._quikridr_status_code_int(entry.get("MPHSTAT", ""))
        if base_status in (44, 45):
            # Issue #108D: base on ETI/RPU terminates every other coverage (spec 54).
            # Statuses 44/45 fall inside the Issue #60 "< 50" window but are not the
            # active base that rule was written for.
            row_data["MPHSTAT"] = "54"
        elif base_status < 50:
            row_data["MPHSTAT"] = "41"
        self.log(
            "PUA RULE APPLIED: "
            f"MPOLICY={mpolicy} BASE_MPLAN={base_mplan} PUA_MPLAN={new_mplan} "
            f"BASE_MEFFDATE={base_meff} BASE_MAGE={base_mage} "
            f"PUA_MPHSTAT={row_data.get('MPHSTAT', '')} PUA_MPAR=0"
        )
        return row_data

    def _init_mplan_authority(self, out_dir: str, cw_path: str):
        catalog_path = os.path.normpath(os.path.join(self._app_base_dir(), "plan_governance", "product_catalog_crosswalk.csv"))
        quikplan_path = os.path.normpath(os.path.join(out_dir, "quikplan.csv"))
        quikplan_set = load_quikplan_plan_set(quikplan_path)
        authority = load_crosswalk_authority(cw_path, catalog_path) if cw_path and os.path.isfile(cw_path) else load_crosswalk_authority("", catalog_path)
        resolver = build_authoritative_mplan_resolver(
            legacy_product_map=authority.legacy_product_map,
            quikplan_plan_set=quikplan_set,
            catalog_path=catalog_path,
        )
        return resolver, quikplan_set, catalog_path

    def _product_setup_default_paths(self):
        root = self._repo_root()
        return {
            "source": os.path.join(root, "plan_analysis", "quikplan_source.csv"),
            "output": self.path_vars["Out"][0].get().strip() or self._migration_output_dir(),
            "stage": os.path.join(root, "plan_governance", "staged"),
        }

    def _setup_product_setup_panel(self):
        panel = tk.LabelFrame(
            self.root,
            text=" Product Setup ",
            bg=self.bg_card,
            fg=self.accent,
            padx=16,
            pady=10,
            font=("Segoe UI", 10, "bold"),
            highlightbackground=self.ui_strip_border, highlightthickness=1, bd=0, labelanchor="nw",
        )
        panel.pack(padx=24, fill="x", pady=(0, 8))

        summary = tk.Frame(panel, bg="#F8FAFC", padx=12, pady=10, highlightbackground="#E2E8F0", highlightthickness=1)
        summary.pack(fill="x")
        self.product_summary_vars = {}
        summary_fields = [
            ("summary_status", "Status"),
            ("summary_rows", "Rows Staged"),
            ("summary_validation", "Validation"),
            ("summary_output", "Output"),
        ]
        for idx, (key, label_text) in enumerate(summary_fields):
            tk.Label(summary, text=f"{label_text}:", bg="#F8FAFC", fg=self.ui_status_muted, font=("Segoe UI", 9)).grid(
                row=0, column=idx * 2, sticky="w", padx=(0, 4),
            )
            var = tk.StringVar(value="Not Yet Run")
            self.product_summary_vars[key] = var
            value_lbl = tk.Label(summary, textvariable=var, bg="#F8FAFC", fg=self.accent, font=("Segoe UI", 9, "bold"))
            value_lbl.grid(row=0, column=idx * 2 + 1, sticky="w", padx=(0, 18))
            if key == "summary_validation":
                self.product_validation_badge = value_lbl

        opts = tk.Frame(panel, bg=self.bg_card)
        opts.pack(fill="x", pady=(8, 0))
        self.product_emit_var = tk.BooleanVar(value=True)
        self.product_overlay_var = tk.BooleanVar(value=False)
        self.product_isolated_var = tk.BooleanVar(
            value=os.environ.get("QLA_PRODUCT_SETUP_ISOLATED", "0").strip().lower() in ("1", "true", "yes"),
        )
        self.product_block_var = tk.BooleanVar(
            value=os.environ.get("QLA_PRODUCT_GOVERNANCE_BLOCK", "0").strip().lower() in ("1", "true", "yes"),
        )
        self.product_strict_var = tk.BooleanVar(
            value=os.environ.get("QLA_STRICT_PRODUCT_AUTHORITY", "0").strip().lower() in ("1", "true", "yes"),
        )
        self.product_closed_var = tk.BooleanVar(
            value=os.environ.get("QLA_CLOSED_PRODUCT_AUTHORITY", "1").strip().lower() not in ("0", "false", "no"),
        )
        self.product_legacy_fallback_var = tk.BooleanVar(
            value=os.environ.get("QLA_ALLOW_LEGACY_PRODUCT_FALLBACK", "0").strip().lower() in ("1", "true", "yes"),
        )
        tk.Checkbutton(opts, text="Emit quikplan.csv to Output", variable=self.product_emit_var, bg=self.bg_card).pack(side="left", padx=(0, 10))
        tk.Checkbutton(opts, text="Product Authority Cutover", variable=self.product_overlay_var, bg=self.bg_card).pack(side="left", padx=(0, 10))
        tk.Checkbutton(opts, text="Strict Authority (P3B)", variable=self.product_strict_var, bg=self.bg_card).pack(side="left", padx=(0, 10))
        tk.Checkbutton(opts, text="Closed Catalog (P3C)", variable=self.product_closed_var, bg=self.bg_card).pack(side="left", padx=(0, 10))
        tk.Checkbutton(opts, text="Isolate from batch", variable=self.product_isolated_var, bg=self.bg_card).pack(side="left", padx=(0, 10))
        tk.Checkbutton(opts, text="Block emit on ERROR", variable=self.product_block_var, bg=self.bg_card).pack(side="left", padx=(0, 10))
        tk.Checkbutton(opts, text="Legacy fallback (rollback)", variable=self.product_legacy_fallback_var, bg=self.bg_card).pack(side="left", padx=(0, 10))

        actions = tk.Frame(panel, bg=self.bg_card)
        actions.pack(fill="x", pady=(8, 0))
        tk.Label(
            actions,
            text="Use Product Setup in the Operator Console to convert quikplan.",
            bg=self.bg_card, fg=self.ui_status_muted, font=("Segoe UI", 8),
        ).pack(side="left")

    def start_product_setup_from_ui(self):
        """Always-visible Product Setup entry point — ensures emit is on for Output write."""
        if hasattr(self, "product_emit_var") and not self.product_emit_var.get():
            self.product_emit_var.set(True)
            self.log("PRODUCT SETUP: Emit quikplan.csv to Output enabled for this run.")
        self.start_product_setup_thread()

    def _load_product_validation_status(self):
        summary_path = os.path.normpath(os.path.join(
            self._app_base_dir(), PRODUCT_SETUP_VALIDATION_DIR, PRODUCT_SETUP_VALIDATION_SUMMARY,
        ))
        if not os.path.isfile(summary_path):
            return "NOT YET RUN"
        try:
            with open(summary_path, encoding="utf-8") as fh:
                text = fh.read()
            if "**IDENTICAL**" in text:
                for line in text.splitlines():
                    if line.startswith("- Baseline rows:"):
                        rows = line.split(":")[-1].strip()
                    if line.startswith("- Baseline columns:"):
                        cols = line.split(":")[-1].strip()
                try:
                    return f"Parallel validation successful — {rows} rows × {cols} columns — 0 differences detected."
                except NameError:
                    return "Parallel validation successful — IDENTICAL (see validation_summary.md)"
            if "DIFFERENCES DETECTED" in text:
                return "Validation differences detected — review phase_p2a_validation/"
        except OSError:
            pass
        return "Validation summary unreadable"

    def _refresh_product_setup_visibility(self):
        display = {key: "NOT YET RUN" for key in getattr(self, "product_metric_vars", {})}
        display["product_validation"] = self._load_product_validation_status()
        display["product_isolation"] = "ENABLED" if self._product_setup_isolated() else "DISABLED (default)"

        diag_path = os.path.normpath(os.path.join(self._app_base_dir(), PRODUCT_SETUP_DIAGNOSTICS_MANIFEST))
        staged = os.path.normpath(os.path.join(self._app_base_dir(), "plan_governance", "staged", "quikplan_staged.csv"))
        if os.path.isfile(staged):
            try:
                sdf = pd.read_csv(staged, dtype=str, keep_default_na=False)
                display["product_rows"] = str(len(sdf))
                display["product_staged_path"] = staged
            except Exception:
                display["product_staged_path"] = staged
        if os.path.isfile(diag_path):
            try:
                ddf = pd.read_csv(diag_path, dtype=str)
                display["product_warnings"] = str((ddf.get("severity", pd.Series()) == "WARN").sum())
                display["product_errors"] = str((ddf.get("severity", pd.Series()) == "ERROR").sum())
            except Exception:
                pass

        out_path = os.path.normpath(os.path.join(self._product_setup_default_paths()["output"], "quikplan.csv"))
        display["product_emitted_path"] = out_path if os.path.isfile(out_path) else "NOT EMITTED"
        if hasattr(self, "_last_product_setup_result") and self._last_product_setup_result:
            display["product_status"] = self._last_product_setup_result.get("status", "NOT YET RUN")

        for key, val in display.items():
            if key in getattr(self, "product_metric_vars", {}):
                self.product_metric_vars[key].set(val)

        if hasattr(self, "product_summary_vars"):
            status = display.get("product_status", "Not Yet Run")
            if status == "NOT YET RUN":
                status = "Not Yet Run"
            rows = display.get("product_rows", "—")
            err_count = display.get("product_errors", "0")
            warn_count = display.get("product_warnings", "0")
            try:
                err_n = int(err_count)
                warn_n = int(warn_count)
                if err_n > 0 or warn_n > 0:
                    validation = f"{err_n} Error(s) / {warn_n} Warning(s)"
                elif display.get("product_validation", "NOT YET RUN") != "NOT YET RUN":
                    validation = "Passed"
                else:
                    validation = "Not Yet Run"
            except ValueError:
                validation = display.get("product_validation", "Not Yet Run")
            emitted = display.get("product_emitted_path", "NOT EMITTED")
            output = "quikplan.csv" if emitted != "NOT EMITTED" else "Not emitted"
            self.product_summary_vars["summary_status"].set(status)
            self.product_summary_vars["summary_rows"].set(rows if rows != "NOT YET RUN" else "—")
            self.product_summary_vars["summary_validation"].set(validation)
            self.product_summary_vars["summary_output"].set(output)
            if hasattr(self, "product_validation_badge"):
                if "Error" in validation:
                    self.product_validation_badge.config(fg=self.ui_status_err)
                elif "Warning" in validation:
                    self.product_validation_badge.config(fg=self.ui_status_warn)
                elif validation == "Passed":
                    self.product_validation_badge.config(fg=self.ui_status_ok)
                else:
                    self.product_validation_badge.config(fg=self.accent)

    def _parse_product_setup_stdout(self, stdout_text):
        parsed = {"status": "UNKNOWN", "warnings": "0", "errors": "0", "staged_path": "", "emitted_path": ""}
        for line in (stdout_text or "").splitlines():
            line = line.strip()
            if line.startswith("PRODUCT_SETUP_STATUS:"):
                parsed["status"] = line.split(":", 1)[1].strip()
            elif line.startswith("DIAGNOSTIC_WARNINGS:"):
                parsed["warnings"] = line.split(":", 1)[1].strip()
            elif line.startswith("DIAGNOSTIC_ERRORS:"):
                parsed["errors"] = line.split(":", 1)[1].strip()
            elif line.startswith("STAGED_PATH:"):
                parsed["staged_path"] = line.split(":", 1)[1].strip()
            elif line.startswith("EMITTED_PATH:"):
                parsed["emitted_path"] = line.split(":", 1)[1].strip()
        return parsed

    def _invoke_product_setup_runner(self):
        runner = self._product_setup_runner_path()
        if not os.path.isfile(runner):
            self.log(f"PRODUCT SETUP ERROR: runner not found: {runner}")
            return {"status": "FAILED", "error": "runner not found"}

        paths = self._product_setup_default_paths()
        os.environ["QLA_PRODUCT_SETUP_ISOLATED"] = "1" if self.product_isolated_var.get() else "0"
        os.environ["QLA_PRODUCT_UAT_OVERLAY"] = "1" if self.product_overlay_var.get() else "0"
        os.environ.pop("CROSSWALK_OVERLAY", None)
        if not self.product_overlay_var.get():
            os.environ["CROSSWALK_OVERLAY"] = "0"
        os.environ["QLA_PRODUCT_GOVERNANCE_BLOCK"] = "1" if self.product_block_var.get() else "0"
        os.environ["QLA_STRICT_PRODUCT_AUTHORITY"] = "1" if self.product_strict_var.get() else "0"
        os.environ["QLA_CLOSED_PRODUCT_AUTHORITY"] = "1" if self.product_closed_var.get() else "0"
        os.environ["QLA_ALLOW_LEGACY_PRODUCT_FALLBACK"] = "1" if self.product_legacy_fallback_var.get() else "0"

        cmd = [
            sys.executable, runner,
            "--source", paths["source"],
            "--stage-dir", paths["stage"],
            "--output-dir", paths["output"],
        ]
        if self.product_emit_var.get():
            cmd.append("--emit")

        if self.product_overlay_var.get():
            cmd.append("--uat-overlay")
        if self.product_strict_var.get():
            cmd.append("--strict-authority")
        if self.product_closed_var.get():
            cmd.append("--closed-product-authority")
        if self.product_legacy_fallback_var.get():
            cmd.append("--allow-legacy-product-fallback")

        self.log("PRODUCT SETUP: launching isolated subprocess runner...")
        self.log(f"  QLA_PRODUCT_UAT_OVERLAY={os.environ.get('QLA_PRODUCT_UAT_OVERLAY', '0')}")
        self.log(f"  QLA_STRICT_PRODUCT_AUTHORITY={os.environ.get('QLA_STRICT_PRODUCT_AUTHORITY', '0')}")
        self.log(f"  QLA_CLOSED_PRODUCT_AUTHORITY={os.environ.get('QLA_CLOSED_PRODUCT_AUTHORITY', '0')}")
        self.log(f"  QLA_ALLOW_LEGACY_PRODUCT_FALLBACK={os.environ.get('QLA_ALLOW_LEGACY_PRODUCT_FALLBACK', '0')}")
        self.log(f"  QLA_PRODUCT_SETUP_ISOLATED={os.environ.get('QLA_PRODUCT_SETUP_ISOLATED', '0')}")
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=PRODUCT_SETUP_RUNNER_TIMEOUT,
                cwd=self._repo_root(),
            )
            stdout_text = proc.stdout or ""
            stderr_text = proc.stderr or ""
            self._log_subprocess_stream("product-setup-stdout", stdout_text)
            self._log_subprocess_stream("product-setup-stderr", stderr_text)
            parsed = self._parse_product_setup_stdout(stdout_text)
            parsed["return_code"] = proc.returncode
            if proc.returncode != 0 and parsed["status"] == "UNKNOWN":
                parsed["status"] = "FAILED"
            return parsed
        except subprocess.TimeoutExpired:
            self.log("PRODUCT SETUP ERROR: subprocess timeout")
            return {"status": "TIMEOUT"}
        except Exception as exc:
            self.log(f"PRODUCT SETUP ERROR: {exc}")
            return {"status": "FAILED", "error": str(exc)}

    def start_product_setup_thread(self):
        if self.is_running:
            messagebox.showwarning("Busy", "A conversion is already running.")
            return
        self.is_running = True
        self.start_time = time.time()
        threading.Thread(target=self.update_timer, daemon=True).start()
        threading.Thread(target=self._run_product_setup_job, daemon=True).start()

    def _run_product_setup_job(self):
        run_error_log = self._new_run_error_log()
        try:
            self.start_run_progress("product_setup")
            self.update_run_progress(1, detail="Preparing product setup")
            self.log("PRODUCT SETUP CONVERSION (Phase P2C): starting...")
            self.update_run_progress(3, detail="Converting quikplan + CSO assumptions")
            self._last_product_setup_result = self._invoke_product_setup_runner()
            self._refresh_product_setup_visibility()
            status = self._last_product_setup_result.get("status", "UNKNOWN")
            self.update_run_progress(4, detail=f"validation — status={status}")
            self.log(f"PRODUCT SETUP: completed status={status}")
            package_ok = self._run_output_hygiene(run_error_log)
            if status == "SUCCESS" and package_ok:
                self._launch_dbf_append_tool()
                self.complete_run_progress("Complete — quikplan.csv written to QLA_Migration\\Output")
                messagebox.showinfo("Product Setup", "Product setup conversion completed successfully.")
            elif status == "SUCCESS" and not package_ok:
                self.fail_run_progress(
                    "Append Tool packaging",
                    "Append package gate failed after product setup",
                    run_error_log.folder,
                )
                messagebox.showerror(
                    "Product Setup",
                    "Product setup CSVs were written, but the DBF Append Tool package failed.\n\n"
                    f"Details:\n{run_error_log.folder}",
                )
            elif status == "BLOCKED":
                run_error_log.write_failed_stage("Validation and blocker checks",
                                                 "Product setup emit blocked by validation controls.")
                self.fail_run_progress("Validation and blocker checks",
                                       "Emit blocked by validation controls", run_error_log.folder)
                messagebox.showwarning("Product Setup", "Conversion completed but output was blocked by validation controls.")
            else:
                run_error_log.write_failed_stage("Product setup", f"status={status}")
                self.fail_run_progress("Product setup", f"status={status}", run_error_log.folder)
                messagebox.showerror("Product Setup", f"Product setup conversion status: {status}")
        except Exception as e:
            run_error_log.write_exception("Product setup", e)
            self.fail_run_progress("Product setup", str(e), run_error_log.folder)
            messagebox.showerror("Product Setup", f"Product setup failed.\n\nDetails:\n{run_error_log.folder}")
        finally:
            self.is_running = False
            self.lbl_timer.config(text="Elapsed: 00:00:00")

    def _rate_loader_runner_path(self):
        return os.path.normpath(os.path.join(self._repo_root(), RATE_LOADER_RUNNER))

    def _rate_loader_config_path(self):
        phase = os.path.join(self._repo_root(), "plan_analysis", "phase_r5_rate_loader")
        preferred = os.path.join(phase, "rate_loader_config.json")
        example = os.path.join(phase, "rate_loader_config.example.json")
        return preferred if os.path.isfile(preferred) else example

    def _rate_loader_csv_dir(self):
        out_var = self.path_vars.get("Out") if hasattr(self, "path_vars") else None
        out = out_var[0].get().strip() if out_var else ""
        if out:
            return os.path.normpath(os.path.join(out, "rates"))
        return os.path.normpath(os.path.join(self._repo_root(), "QLA_Migration", "Output", "rates"))

    def _rate_loader_dbf_dir(self):
        return os.path.normpath(os.path.join(
            self._repo_root(), "plan_analysis", "phase_r5_rate_loader", "emitted_dbf",
        ))

    def _setup_rate_loader_panel(self):
        panel = tk.LabelFrame(
            self.root,
            text=" Rate Table Generation ",
            bg=self.bg_card,
            fg=self.accent,
            padx=16,
            pady=10,
            font=("Segoe UI", 10, "bold"),
            highlightbackground=self.ui_strip_border, highlightthickness=1, bd=0, labelanchor="nw",
        )
        panel.pack(padx=24, fill="x", pady=(0, 8))

        summary = tk.Frame(panel, bg="#F8FAFC", padx=12, pady=10, highlightbackground="#E2E8F0", highlightthickness=1)
        summary.pack(fill="x")
        self.rate_summary_status = tk.StringVar(value="Not Yet Run")
        self.rate_summary_detail = tk.StringVar(value="Tables: —  |  Blockers: —  |  CSV Rows: —")
        tk.Label(summary, text="Status:", bg="#F8FAFC", fg=self.ui_status_muted, font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
        self.rate_status_badge = tk.Label(summary, textvariable=self.rate_summary_status, bg="#F8FAFC", fg=self.accent, font=("Segoe UI", 9, "bold"))
        self.rate_status_badge.grid(row=0, column=1, sticky="w", padx=(4, 24))
        tk.Label(summary, textvariable=self.rate_summary_detail, bg="#F8FAFC", fg=self.text_color, font=("Segoe UI", 9)).grid(row=0, column=2, sticky="w")

        opts = tk.Frame(panel, bg=self.bg_card)
        opts.pack(fill="x", pady=(8, 0))
        self.rate_emit_csv_var = tk.BooleanVar(value=True)
        self.rate_emit_dbf_var = tk.BooleanVar(value=False)
        self.rate_include_batch_var = tk.BooleanVar(
            value=os.environ.get("QLA_BATCH_INCLUDE_RATE_TABLES", "0").strip().lower() in ("1", "true", "yes"),
        )
        tk.Checkbutton(opts, text="Emit CSV tables (Output/rates/)", variable=self.rate_emit_csv_var, bg=self.bg_card).pack(side="left", padx=(0, 10))
        tk.Checkbutton(opts, text="Emit sandbox DBF tables", variable=self.rate_emit_dbf_var, bg=self.bg_card).pack(side="left", padx=(0, 10))
        tk.Checkbutton(opts, text="Include in full batch migration", variable=self.rate_include_batch_var, bg=self.bg_card).pack(side="left", padx=(0, 10))

        actions = tk.Frame(panel, bg=self.bg_card)
        actions.pack(fill="x", pady=(8, 0))
        tk.Button(
            actions, text="GENERATE RATE TABLES", width=28, bg="#0D9488", fg="white",
            command=self.start_rate_loader_thread,
        ).pack(side="left", padx=(0, 8))

    def _parse_rate_loader_stdout(self, stdout_text):
        parsed = {
            "status": "UNKNOWN", "blockers": "", "tables": "", "csv_rows": "",
            "csv_dir": "", "dbf_dir": "", "csv_manifest": "", "config": "",
        }
        for line in (stdout_text or "").splitlines():
            line = line.strip()
            if line.startswith("RATE_LOADER_STATUS:"):
                parsed["status"] = line.split(":", 1)[1].strip()
            elif line.startswith("RATE_LOADER_BLOCKERS:"):
                parsed["blockers"] = line.split(":", 1)[1].strip()
            elif line.startswith("RATE_TABLES_WRITTEN:"):
                parsed["tables"] = line.split(":", 1)[1].strip()
            elif line.startswith("RATE_CSV_ROWS:"):
                parsed["csv_rows"] = line.split(":", 1)[1].strip()
            elif line.startswith("RATE_CSV_DIR:"):
                parsed["csv_dir"] = line.split(":", 1)[1].strip()
            elif line.startswith("RATE_DBF_DIR:"):
                parsed["dbf_dir"] = line.split(":", 1)[1].strip()
            elif line.startswith("RATE_CSV_MANIFEST:"):
                parsed["csv_manifest"] = line.split(":", 1)[1].strip()
            elif line.startswith("RATE_CONFIG:"):
                parsed["config"] = line.split(":", 1)[1].strip()
        return parsed

    def _invoke_rate_loader_runner(self, emit_csv=None, emit_dbf=None, dry_run=False):
        emit_csv = self.rate_emit_csv_var.get() if emit_csv is None else emit_csv
        emit_dbf = self.rate_emit_dbf_var.get() if emit_dbf is None else emit_dbf
        csv_dir = self._rate_loader_csv_dir()
        dbf_dir = self._rate_loader_dbf_dir()
        config = self._rate_loader_config_path()

        self.log("RATE TABLE GENERATION (Phase R5): running in-process rate pipeline...")
        self.log(f"  Config: {config}")
        self.log(f"  CSV dir: {csv_dir}")
        if emit_dbf:
            self.log(f"  DBF dir: {dbf_dir}")
        try:
            result = RE.run_rate_emit(
                self._repo_root(),
                config,
                csv_dir=csv_dir,
                dbf_dir=dbf_dir,
                emit_csv=emit_csv,
                emit_dbf=emit_dbf,
                dry_run=dry_run,
            )
            for msg in result.get("messages") or []:
                self.log(f"  RATE: {msg}")
            if result.get("inherited_plans"):
                self.log(
                    f"  RATE: Inherited CV plans: {', '.join(result['inherited_plans'])}"
                )
            iv = result.get("inherited_verify") or {}
            if iv:
                self.log(
                    f"  RATE: Issue #40 verify: "
                    f"{'PASS' if iv.get('pass') else 'FAIL'}"
                )
            if result.get("partial_emit"):
                self.log("  RATE: Partial emit — CV/key/member tables written despite non-CV blockers")
            result["return_code"] = result.get("return_code", 0 if result.get("status") == "SUCCESS" else 2)
            return result
        except Exception as exc:
            self.log(f"RATE LOADER ERROR: {exc}")
            return {"status": "FAILED", "error": str(exc), "blockers": "", "tables": "0", "csv_rows": "0"}

    def _refresh_rate_loader_visibility(self):
        display = {key: "NOT YET RUN" for key in getattr(self, "rate_metric_vars", {})}
        last = getattr(self, "_last_rate_loader_result", None) or {}
        if last:
            display["rate_status"] = last.get("status", "NOT YET RUN")
            display["rate_blockers"] = last.get("blockers", "")
            display["rate_tables"] = last.get("tables", "")
            display["rate_csv_rows"] = last.get("csv_rows", "")
            display["rate_csv_dir"] = last.get("csv_dir", "") or self._rate_loader_csv_dir()
            display["rate_dbf_dir"] = last.get("dbf_dir", "")
        else:
            manifest = os.path.join(
                self._migration_root(), "Reports", "rates", "rate_csv_manifest.csv",
            )
            if os.path.isfile(manifest):
                display["rate_status"] = "PRIOR RUN (see manifest)"
                display["rate_csv_dir"] = self._rate_loader_csv_dir()
        for key, var in getattr(self, "rate_metric_vars", {}).items():
            var.set(display.get(key, "NOT YET RUN"))

        if hasattr(self, "rate_summary_status"):
            status = display.get("rate_status", "Not Yet Run")
            if status == "NOT YET RUN":
                status = "Not Yet Run"
            blockers = display.get("rate_blockers", "—") or "0"
            tables = display.get("rate_tables", "—") or "0"
            csv_rows = display.get("rate_csv_rows", "—") or "0"
            self.rate_summary_status.set(status)
            self.rate_summary_detail.set(f"Tables: {tables}  |  Blockers: {blockers}  |  CSV Rows: {csv_rows}")
            if hasattr(self, "rate_status_badge"):
                if str(status).upper() in ("FAILED", "TIMEOUT", "BLOCKED"):
                    self.rate_status_badge.config(fg=self.ui_status_err)
                elif str(blockers) not in ("", "0", "—", "NOT YET RUN"):
                    self.rate_status_badge.config(fg=self.ui_status_warn)
                elif str(status).upper() == "SUCCESS":
                    self.rate_status_badge.config(fg=self.ui_status_ok)
                else:
                    self.rate_status_badge.config(fg=self.accent)

    def start_rate_loader_thread(self):
        if self.is_running:
            messagebox.showwarning("Busy", "A conversion is already running.")
            return
        if not self.rate_emit_csv_var.get() and not self.rate_emit_dbf_var.get():
            messagebox.showwarning("Rate Tables", "Select at least one output format (CSV and/or DBF).")
            return
        self.is_running = True
        self.start_time = time.time()
        threading.Thread(target=self.update_timer, daemon=True).start()
        threading.Thread(target=self._run_rate_loader_job, kwargs={"from_batch": False}, daemon=True).start()

    def _run_rate_loader_job(self, from_batch=False):
        run_error_log = self._new_run_error_log()
        try:
            if not from_batch:
                self.start_run_progress("rate_only")
                self.update_run_progress(2, detail="rate extracts + segmentation")
            self.log("RATE TABLE GENERATION (Phase R5): starting...")
            if not from_batch:
                if not self.rate_emit_csv_var.get() and not self.rate_emit_dbf_var.get():
                    self.log("RATE LOADER: skipped — no emit format selected.")
                    return
                self.update_run_progress(3, detail="building factor / key / member tables")
            result = self._invoke_rate_loader_runner()
            self._last_rate_loader_result = result
            self._refresh_rate_loader_visibility()
            status = result.get("status", "UNKNOWN")
            self.log(f"RATE LOADER: completed status={status} blockers={result.get('blockers', '?')}")
            # Issue #96: re-apply R7B PVO after rates exist so QuikTvs/Cvs plans get PLANVALOPT/GDVARY*
            if status in ("SUCCESS", "PARTIAL") or result.get("partial_emit"):
                try:
                    from qla_core.quikplan_rate_variation_flags import integrate_quikplan_file
                    out_dir = self.path_vars["Out"][0].get()
                    qp_path = os.path.normpath(os.path.join(out_dir, "quikplan.csv"))
                    if os.path.isfile(qp_path):
                        r7 = integrate_quikplan_file(qp_path, repo_root=self._repo_root())
                        self.log(
                            f"Issue #96: post-rate quikplan PVO refresh — "
                            f"PLANVALOPT=Y plans={r7.planvalopt_y} blockers={r7.validation_blockers}"
                        )
                except Exception as exc:
                    self.log(f"Issue #96: post-rate PVO refresh skipped: {exc}")
            if not from_batch:
                self.update_run_progress(4, detail=f"validation — status={status}")
                package_ok = self._run_output_hygiene(run_error_log)
                if package_ok and (status == "SUCCESS" or result.get("partial_emit")):
                    self._launch_dbf_append_tool()
                if status == "SUCCESS" and package_ok:
                    detail = "Complete — rate tables written to QLA_Migration\\Output\\rates"
                    if result.get("partial_emit"):
                        detail += " (partial: non-CV blockers ignored)"
                    self.complete_run_progress(detail)
                    msg = "Rate tables generated successfully."
                    if result.get("partial_emit"):
                        msg += (
                            f"\n\nNote: {result.get('blockers', '?')} non-CV blocker(s) remain "
                            "(e.g. QuikUint). QuikCvs, QuikPlCv, and member tables were still written."
                        )
                    if result.get("inherited_plans"):
                        msg += f"\n\nInherited CV plans: {', '.join(result['inherited_plans'])}"
                    if result.get("csv_dir"):
                        msg += f"\n\nCSV folder:\n{result['csv_dir']}"
                    messagebox.showinfo("Rate Tables", msg)
                elif status == "SUCCESS" and not package_ok:
                    self.fail_run_progress(
                        "Append Tool packaging",
                        "Append package gate failed after rate tables",
                        run_error_log.folder,
                    )
                    messagebox.showerror(
                        "Rate Tables",
                        "Rate tables were written, but the DBF Append Tool package failed.\n\n"
                        f"Details:\n{run_error_log.folder}",
                    )
                elif status == "BLOCKED":
                    run_error_log.write_failed_stage("Rate validation",
                                                     f"{result.get('blockers', '?')} blocker(s) prevented emit.")
                    self.fail_run_progress("Rate validation and blocker checks",
                                           f"{result.get('blockers', '?')} blocker(s)", run_error_log.folder)
                    messagebox.showwarning(
                        "Rate Tables",
                        f"Rate validation blocked emit ({result.get('blockers', '?')} blocker(s)).\n"
                        "Review the conversion log and phase_r5_rate_loader validation reports.",
                    )
                else:
                    run_error_log.write_failed_stage("Rate table generation", f"status={status}")
                    self.fail_run_progress("Rate table generation", f"status={status}", run_error_log.folder)
                    messagebox.showerror("Rate Tables", f"Rate table generation status: {status}")
        except Exception as e:
            if not from_batch:
                run_error_log.write_exception("Rate table generation", e)
                self.fail_run_progress("Rate table generation", str(e), run_error_log.folder)
                messagebox.showerror("Rate Tables", f"Rate generation failed.\n\nDetails:\n{run_error_log.folder}")
            else:
                raise
        finally:
            if not from_batch:
                self.is_running = False
                self.lbl_timer.config(text="Elapsed: 00:00:00")

    def _refresh_governance_visibility(self):
        summary = self._build_governance_summary()
        if not hasattr(self, "gov_metric_vars"):
            self._ui_update_status_strip(summary)
            return
        dbf_panel = self._load_uat_dbf_panel_status()
        if not summary["files_present"]:
            display = {key: "NOT YET GENERATED" for key in self.gov_metric_vars}
            display["uat_dbf_status"] = dbf_panel.get("uat_dbf_status", "NOT YET GENERATED")
            display["uat_dbf_timestamp"] = dbf_panel.get("uat_dbf_timestamp", "NOT YET GENERATED")
            display["uat_dbf_folder"] = dbf_panel.get("uat_dbf_folder", self._claims_uat_dbf_dir())
            val_panel = self._load_cross_table_validation_panel_status()
            display["mpolicy_validation_status"] = val_panel.get("mpolicy_validation_status", "NOT YET GENERATED")
            display["claims_held_missing_policy"] = val_panel.get("claims_held_missing_policy", "NOT YET GENERATED")
            display["payments_held_missing_policy"] = val_panel.get("payments_held_missing_policy", "NOT YET GENERATED")
            display["cross_table_validation_report"] = val_panel.get("cross_table_validation_report", "NOT YET GENERATED")
        else:
            display = {
                "uat_claims": self._format_governance_metric(summary["uat_claims"]),
                "uat_payments": self._format_governance_metric(summary["uat_payments"]),
                "deferred_claims": self._format_governance_metric(summary["deferred_claims"]),
                "deferred_payments": self._format_governance_metric(summary["deferred_payments"]),
                "orphan_count": self._format_governance_metric(summary["orphan_count"]),
                "recon_pass_pct": self._format_governance_metric(summary["recon_pass_pct"], suffix="%"),
                "replay_recovery": self._format_governance_metric(summary["replay_recovery"]),
                "exclusion_records": self._format_governance_metric(summary["exclusion_records"]),
                "surrender_queue": self._format_governance_metric(summary["surrender_queue"]),
                "orphan_queue": self._format_governance_metric(summary["orphan_queue"]),
            }
            if summary["top_blocker"]:
                display["top_blocker"] = f"{summary['top_blocker']} ({summary['top_blocker_count']})"
            else:
                display["top_blocker"] = "NOT YET GENERATED"
            display["uat_dbf_status"] = summary.get("uat_dbf_status", "NOT YET GENERATED")
            display["uat_dbf_timestamp"] = summary.get("uat_dbf_timestamp", "NOT YET GENERATED")
            display["uat_dbf_folder"] = summary.get("uat_dbf_folder", self._claims_uat_dbf_dir())
            display["mpolicy_validation_status"] = summary.get("mpolicy_validation_status", "NOT YET GENERATED")
            display["claims_held_missing_policy"] = summary.get("claims_held_missing_policy", "NOT YET GENERATED")
            display["payments_held_missing_policy"] = summary.get("payments_held_missing_policy", "NOT YET GENERATED")
            display["cross_table_validation_report"] = summary.get("cross_table_validation_report", "NOT YET GENERATED")

        for key, var in self.gov_metric_vars.items():
            var.set(display.get(key, "NOT YET GENERATED"))

        self._ui_update_status_strip(summary)
        if hasattr(self, "system_diag_vars"):
            cfg = self.CLAIMS_ORCHESTRATION
            self.system_diag_vars["diag_run_mode"].set(cfg.get("run_mode", ""))
            self.system_diag_vars["diag_production_dbf"].set(cfg.get("production_dbf_flag", "N"))
            self.system_diag_vars["diag_production_status"].set(summary.get("production_status", ""))
            self.system_diag_vars["diag_threshold_status"].set(summary.get("threshold_status", ""))
            self.system_diag_vars["diag_production_auth"].set(cfg.get("production_authorization_flag", "N"))

    def _log_governance_console_summary(self):
        summary = self._build_governance_summary()
        if not summary["files_present"]:
            self.log("VALIDATION SUMMARY: Phase 17 outputs NOT YET GENERATED")
            return
        lines = [
            "VALIDATION SUMMARY (UAT reporting — read-only)",
            f"  UAT Candidate Claims: {self._format_governance_metric(summary['uat_claims'])}",
            f"  UAT Candidate Payments: {self._format_governance_metric(summary['uat_payments'])}",
            f"  Deferred Claims: {self._format_governance_metric(summary['deferred_claims'])}",
            f"  Deferred Payments: {self._format_governance_metric(summary['deferred_payments'])}",
            f"  Exclusion Records: {self._format_governance_metric(summary['exclusion_records'])}",
            f"  Orphan Count: {self._format_governance_metric(summary['orphan_count'])}",
            f"  Reconciliation Pass %: {self._format_governance_metric(summary['recon_pass_pct'], suffix='%')}",
            f"  Replay Orphan Recovery: {self._format_governance_metric(summary['replay_recovery'])}",
            f"  Production Status: {summary['production_status']}",
        ]
        if summary["top_blocker"]:
            lines.append(f"  Top Blocker: {summary['top_blocker']} ({summary['top_blocker_count']})")
        self.log("\n".join(lines))

    def _view_governance_log(self, filename):
        view_cfg = GOVERNANCE_LOG_VIEWS.get(filename, {})
        title = view_cfg.get("title", f"Governance Log — {filename}")
        preview_cols = view_cfg.get("columns", [])
        path = os.path.join(self._phase17_governance_dir(), filename)
        preview_limit = 40

        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("980x420")
        win.configure(bg=self.bg_main)

        header = tk.Label(
            win,
            text=f"{title}\nSource: {path}",
            bg=self.bg_main,
            fg=self.accent,
            font=("Segoe UI", 9, "bold"),
            justify="left",
            anchor="w",
        )
        header.pack(fill="x", padx=12, pady=(10, 4))

        text = scrolledtext.ScrolledText(win, bg="#F8FAFC", fg="#1E293B", font=("Consolas", 9))
        text.pack(padx=12, pady=8, fill="both", expand=True)

        if not os.path.isfile(path):
            text.insert(tk.END, "NOT YET GENERATED\n\nGovernance output file not found.\nRun Phase 17 UAT governance reporting to materialize this log.")
            text.config(state=tk.DISABLED)
            return

        try:
            df = pd.read_csv(path, dtype=str)
            df.columns = [str(c).strip().lower() for c in df.columns]
            total_rows = len(df)
            preview = df.head(preview_limit)
            if preview_cols:
                cols = [c for c in preview_cols if c in preview.columns]
                if cols:
                    preview = preview[cols]
            text.insert(tk.END, preview.to_string(index=False))
            text.insert(tk.END, f"\n\n--- read-only preview ({min(total_rows, preview_limit)} of {total_rows} rows) ---")
        except Exception as exc:
            text.insert(tk.END, f"Unable to preview file safely: {exc}")
        text.config(state=tk.DISABLED)

    def _review_hold_manifest_fieldnames(self):
        return [
            "audit_timestamp", "emit_timestamp", "production_dbf_flag", "hold_category",
            "record_type", "record_identifier", "record_id", "reconstructed_claim_id",
            "derivation_candidate_id", "MPOLICY", "blocker_category", "reason_excluded",
            "reason_held", "governance_status", "business_review_required",
            "business_explanation", "remediation_recommendation", "source_file",
            "target_file", "rulebook_lineage",
        ]

    def _load_policy_crosswalk_map(self):
        cw_path = ""
        cw_var = self.path_vars.get("CW") if hasattr(self, "path_vars") else None
        if cw_var and cw_var[0].get().strip():
            cw_path = cw_var[0].get().strip()
        if not cw_path or not os.path.isfile(cw_path):
            cw_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Master_Crosswalk.csv")
        if not os.path.isfile(cw_path):
            return {}
        try:
            cw_df = pd.read_csv(cw_path, dtype=str)
            return {
                self.normalize(k): self.normalize(v)
                for k, v in zip(cw_df.iloc[:, 0], cw_df.iloc[:, 1])
            }
        except Exception:
            return {}

    def _load_converted_mpolicy_set(self, output_dir=None):
        base = output_dir or self._resolve_output_base_dir()
        quikmstr_path = os.path.normpath(os.path.join(base, "quikmstr.csv"))
        if not os.path.isfile(quikmstr_path):
            return None, quikmstr_path
        try:
            qm_df = pd.read_csv(quikmstr_path, dtype=str, usecols=lambda c: str(c).strip().upper() == "MPOLICY")
        except ValueError:
            qm_df = pd.read_csv(quikmstr_path, dtype=str)
        if "MPOLICY" not in [str(c).strip().upper() for c in qm_df.columns]:
            qm_df.columns = [str(c).strip().upper() for c in qm_df.columns]
        if "MPOLICY" not in qm_df.columns:
            return set(), quikmstr_path
        mpolicy_col = [c for c in qm_df.columns if str(c).upper() == "MPOLICY"][0]
        values = {
            self.normalize(v)
            for v in qm_df[mpolicy_col].tolist()
            if str(v).strip() and str(v).strip().lower() not in ("nan", "none")
        }
        return values, quikmstr_path

    def _resolve_claims_rulebook_path(self, table_key):
        cfg_dir = self._migration_configs_dir()
        candidates = [
            os.path.join(cfg_dir, f"Sync_Rulebook_{table_key}.csv"),
            os.path.join(self._app_base_dir(), f"Sync_Rulebook_{table_key}.csv"),
        ]
        for path in candidates:
            if os.path.isfile(path):
                return path
        return candidates[0]

    def _phase10_derivation_path(self, table_key):
        claims_root = self._claims_analysis_root()
        paths = {
            "quikclms": os.path.join(
                claims_root, "phase10b_quikclms_derivation_design", "quikclms_derivation_candidates.csv",
            ),
            "quikclmp": os.path.join(
                claims_root, "phase10a_quikclmp_derivation_design", "quikclmp_derivation_candidates.csv",
            ),
        }
        return paths.get(table_key, "")

    def _build_clms_p10_rc_index(self):
        index, _ = self._load_phase10_derivation_index("quikclms")
        by_rc = {}
        for row in index.values():
            rc = str(row.get("reconstructed_claim_id", "")).strip()
            if rc:
                by_rc[rc] = row
        return by_rc

    def _enrich_payment_combined_from_claim(self, combined, clms_p10_by_rc):
        enriched = dict(combined)
        rc = str(enriched.get("reconstructed_claim_id", "")).strip()
        parent = clms_p10_by_rc.get(rc, {})
        for key in (
            "claimstat", "mclaimstatus", "claim_family", "mclaimfamily",
            "mclaimtype", "policy_number",
        ):
            if parent.get(key) and not enriched.get(key):
                enriched[key] = parent[key]
        return enriched

    def _load_phase10_derivation_index(self, table_key):
        path = self._phase10_derivation_path(table_key)
        index = {}
        if not path or not os.path.isfile(path):
            return index, path
        try:
            df = pd.read_csv(path, dtype=str).fillna("")
        except Exception:
            return index, path
        for _, row in df.iterrows():
            row_dict = {
                str(k).strip().lower(): str(v).strip()
                for k, v in row.to_dict().items()
            }
            deriv_id = row_dict.get("derivation_candidate_id", "")
            if deriv_id:
                index[deriv_id] = row_dict
        return index, path

    def _load_claims_sync_rulebook(self, table_key):
        rb_path = self._resolve_claims_rulebook_path(table_key)
        if not os.path.isfile(rb_path):
            return None, rb_path
        try:
            return pd.read_csv(rb_path, dtype=str).fillna(""), rb_path
        except Exception:
            return None, rb_path

    def _format_claims_money(self, val):
        try:
            return f"{float(str(val).replace(',', '').strip() or 0):.2f}"
        except Exception:
            return "0.00"

    def _derive_claims_mhdpmt(self, normalized):
        paytype = str(normalized.get("mpaytype", "")).strip().upper()
        return CLAIMS_PAYMENT_MHDPMT_MAP.get(paytype, "C")

    def _prepare_claims_source_row(self, combined, table_key):
        normalized = dict(combined)
        if table_key == "quikclmp" and not normalized.get("derived_mhdpmt"):
            normalized["derived_mhdpmt"] = self._derive_claims_mhdpmt(normalized)
        if table_key == "quikclms":
            if not normalized.get("netdb") and normalized.get("mnetamt"):
                normalized["netdb"] = normalized["mnetamt"]
            if not normalized.get("claimstat") and normalized.get("mclaimstatus"):
                normalized["claimstat"] = normalized["mclaimstatus"]
        return normalized

    def _transform_claims_source_row(self, combined, table_key, rules, crosswalk):
        schema = self.TABLE_SCHEMAS[table_key]
        normalized = self._prepare_claims_source_row(combined, table_key)
        money_fields = CLAIMS_MONEY_FIELDS.get(table_key, set())
        row_data = {h: "" for h in schema}
        for _, rule in rules.iterrows():
            s_f = str(rule.get("Source_Field", "")).strip()
            t_f = str(rule.get("Target_Field", "")).strip().upper()
            default_val = str(rule.get("Default_Value", "")).strip()
            if t_f not in [h.upper() for h in schema]:
                continue
            actual_h = [h for h in schema if h.upper() == t_f][0]
            val = ""
            if s_f:
                val = normalized.get(s_f.lower(), "")
            if not val and default_val and default_val.lower() not in ("nan", "none"):
                val = default_val
            val = self.normalize(val) if val else ""
            if t_f == "MPOLICY" and val:
                # Issue #2: source + C (no strip-9 crosswalk)
                val = self._format_qladmin_mpolicy(val)
            if t_f in money_fields:
                val = self._format_claims_money(val if val else default_val)
            row_data[actual_h] = val
        return row_data

    def _build_mpolicy_derivation_lookup(self):
        claims_root = self._claims_analysis_root()
        lookups = {"quikclms": {}, "quikclmp": {}}
        sources = {
            "quikclms": os.path.join(claims_root, "phase10b_quikclms_derivation_design", "quikclms_derivation_candidates.csv"),
            "quikclmp": os.path.join(claims_root, "phase10a_quikclmp_derivation_design", "quikclmp_derivation_candidates.csv"),
        }
        for table_key, path in sources.items():
            if not os.path.isfile(path):
                continue
            try:
                df = pd.read_csv(path, dtype=str)
                df.columns = [str(c).strip().lower() for c in df.columns]
            except Exception:
                continue
            target = lookups[table_key]
            for _, row in df.iterrows():
                mpolicy = self.normalize(str(row.get("mpolicy", row.get("policy_number", ""))))
                if not mpolicy:
                    continue
                for key_col in ("reconstructed_claim_id", "derivation_candidate_id"):
                    key_val = str(row.get(key_col, "")).strip()
                    if key_val:
                        target[key_val] = mpolicy
        return lookups

    def _parse_mpolicy_from_reconstructed_id(self, reconstructed_claim_id):
        rc = str(reconstructed_claim_id or "").strip()
        if rc.upper().startswith("RC-"):
            parts = rc.split("-")
            if len(parts) >= 2:
                return self.normalize(parts[1])
        return ""

    def _resolve_row_mpolicy(self, row, table_key, lookups, crosswalk):
        row_dict = row.to_dict() if hasattr(row, "to_dict") else dict(row)
        normalized = {str(k).strip().lower(): v for k, v in row_dict.items()}
        raw = self.normalize(str(normalized.get("mpolicy", "")))
        if not raw:
            deriv = str(normalized.get("derivation_candidate_id", "")).strip()
            rc = str(normalized.get("reconstructed_claim_id", "")).strip()
            table_lookup = lookups.get(table_key, {})
            combined = {}
            combined.update(lookups.get("quikclms", {}))
            combined.update(lookups.get("quikclmp", {}))
            for key in (deriv, rc):
                if key and key in table_lookup:
                    raw = table_lookup[key]
                    break
                if key and key in combined:
                    raw = combined[key]
                    break
            if not raw and rc:
                raw = self._parse_mpolicy_from_reconstructed_id(rc)
        converted = crosswalk.get(raw, raw) if raw else ""
        return raw, converted

    def _build_cross_table_hold_row(
        self, row, table_key, staged_path, dest_path, reason_excluded, mpolicy_raw,
        audit_ts, prod_flag,
    ):
        row_dict = row.to_dict() if hasattr(row, "to_dict") else dict(row)
        normalized = {str(k).strip().lower(): v for k, v in row_dict.items()}
        rc = str(normalized.get("reconstructed_claim_id", "")).strip()
        deriv = str(normalized.get("derivation_candidate_id", "")).strip()
        record_type = "CLAIM" if table_key == "quikclms" else "PAYMENT"
        if str(normalized.get("record_type", "")).strip().upper() == "QUIKCLMP":
            record_type = "PAYMENT"
        elif str(normalized.get("record_type", "")).strip().upper() == "QUIKCLMS":
            record_type = "CLAIM"
        record_identifier = deriv or rc or str(normalized.get("canonical_payment_stage_id", "")).strip()
        explanation = PHASE20_HOLD_EXPLANATION
        if reason_excluded == "QUIKMSTR_OUTPUT_MISSING":
            explanation = "Converted policy master output/quikmstr.csv was not available, so claims were held from UAT emit."
        elif reason_excluded == "BLANK_MPOLICY":
            explanation = "The claim or payment did not resolve to an MPOLICY value, so it was held from UAT output."
        elif reason_excluded == "MISSING_DERIVATION_CANDIDATE":
            explanation = (
                "The UAT governance row did not resolve to a Phase 10 derivation candidate, "
                "so QLA-shaped emit was held."
            )
        return {
            "audit_timestamp": audit_ts,
            "emit_timestamp": audit_ts,
            "production_dbf_flag": prod_flag,
            "hold_category": "CROSS_TABLE_VALIDATION",
            "record_type": record_type,
            "record_identifier": record_identifier,
            "record_id": record_identifier,
            "reconstructed_claim_id": rc,
            "derivation_candidate_id": deriv,
            "MPOLICY": mpolicy_raw,
            "blocker_category": "CROSS_TABLE_POLICY_MISSING",
            "reason_excluded": reason_excluded,
            "reason_held": reason_excluded,
            "governance_status": "GOVERNANCE_HOLD",
            "business_review_required": "Y",
            "business_explanation": explanation,
            "remediation_recommendation": PHASE20_REMEDIATION,
            "source_file": staged_path,
            "target_file": dest_path,
            "rulebook_lineage": PHASE20_RULEBOOK_LINEAGE,
        }

    def _validate_and_filter_staged_claims_csv(
        self, staged_path, table_key, mpolicy_set, quikmstr_path, lookups, crosswalk,
        quikmstr_missing, audit_ts, prod_flag, output_dir, validation_enabled=True,
        plan_lookup=None, clms_p10_by_rc=None,
    ):
        dest_path = os.path.normpath(os.path.join(output_dir, f"{table_key}.csv"))
        schema = self.TABLE_SCHEMAS[table_key]
        stats = {
            "validation_name": f"{table_key.upper()}_QLA_EMIT",
            "source_file": staged_path,
            "reference_file": quikmstr_path,
            "total_source_rows": 0,
            "emitted_rows": 0,
            "held_rows": 0,
            "semantic_hold_rows": 0,
            "blank_mpolicy_rows": 0,
            "missing_mpolicy_rows": 0,
            "missing_derivation_rows": 0,
            "validation_status": "PASS",
        }
        hold_rows = []
        semantic_rc_ids = set()
        semantic_deriv_ids = set()
        semantic_reason_map = {}
        if self._claims_semantic_governance_enabled():
            semantic_rc_ids, semantic_deriv_ids, semantic_reason_map, semantic_hold_path = (
                self._load_semantic_governance_hold_index()
            )
            if semantic_rc_ids or semantic_deriv_ids:
                stats["reference_file"] = f"{quikmstr_path}|semantic_hold={semantic_hold_path}"
        if not os.path.isfile(staged_path):
            stats["validation_status"] = "SOURCE_MISSING"
            return None, hold_rows, stats

        try:
            df = pd.read_csv(staged_path, dtype=str).fillna("")
        except Exception as exc:
            stats["validation_status"] = f"ERROR:{exc}"
            raise

        stats["total_source_rows"] = len(df)
        rules, rb_path = self._load_claims_sync_rulebook(table_key)
        if rules is None:
            stats["validation_status"] = "RULEBOOK_MISSING"
            stats["held_rows"] = len(df)
            for _, row in df.iterrows():
                hold_rows.append(self._build_cross_table_hold_row(
                    row, table_key, staged_path, dest_path, "RULEBOOK_MISSING",
                    "", audit_ts, prod_flag,
                ))
            return None, hold_rows, stats

        p10_index, p10_path = self._load_phase10_derivation_index(table_key)
        if not p10_index:
            stats["validation_status"] = "PHASE10_MISSING"
            stats["held_rows"] = len(df)
            for _, row in df.iterrows():
                hold_rows.append(self._build_cross_table_hold_row(
                    row, table_key, staged_path, dest_path, "PHASE10_DERIVATION_MISSING",
                    "", audit_ts, prod_flag,
                ))
            return None, hold_rows, stats

        stats["reference_file"] = f"{quikmstr_path}|{p10_path}|{rb_path}"

        if quikmstr_missing and validation_enabled:
            stats["validation_status"] = "BLOCKED_QUIKMSTR_MISSING"
            stats["held_rows"] = len(df)
            for _, row in df.iterrows():
                _, converted = self._resolve_row_mpolicy(row, table_key, lookups, crosswalk)
                hold_rows.append(self._build_cross_table_hold_row(
                    row, table_key, staged_path, dest_path, "QUIKMSTR_OUTPUT_MISSING",
                    converted, audit_ts, prod_flag,
                ))
            return None, hold_rows, stats

        emit_rows = []
        for _, row in df.iterrows():
            uat_dict = {
                str(k).strip().lower(): str(v).strip()
                for k, v in row.to_dict().items()
            }
            deriv = uat_dict.get("derivation_candidate_id", "")
            p10_row = p10_index.get(deriv, {})
            if not p10_row:
                stats["missing_derivation_rows"] += 1
                stats["held_rows"] += 1
                _, converted = self._resolve_row_mpolicy(row, table_key, lookups, crosswalk)
                hold_rows.append(self._build_cross_table_hold_row(
                    row, table_key, staged_path, dest_path, "MISSING_DERIVATION_CANDIDATE",
                    converted, audit_ts, prod_flag,
                ))
                continue

            combined = dict(p10_row)
            combined.update(uat_dict)
            rc = str(uat_dict.get("reconstructed_claim_id", p10_row.get("reconstructed_claim_id", ""))).strip()
            deriv = str(uat_dict.get("derivation_candidate_id", "")).strip()
            if self._claims_semantic_governance_enabled():
                is_semantic_hold = (
                    (rc and rc in semantic_rc_ids)
                    or (deriv and deriv in semantic_deriv_ids)
                )
                if is_semantic_hold:
                    stats["semantic_hold_rows"] += 1
                    stats["held_rows"] += 1
                    reason = semantic_reason_map.get(deriv) or semantic_reason_map.get(rc) or "SEMANTIC_PSEUDO_CLAIM"
                    _, converted = self._resolve_row_mpolicy(row, table_key, lookups, crosswalk)
                    hold_rows.append(self._build_semantic_hold_row(
                        row, table_key, staged_path, dest_path, reason, converted, audit_ts, prod_flag,
                    ))
                    continue

            if table_key == "quikclmp" and clms_p10_by_rc:
                combined = self._enrich_payment_combined_from_claim(combined, clms_p10_by_rc)

            qla_row = self._transform_claims_source_row(combined, table_key, rules, crosswalk)
            qla_row = apply_claims_emit_enhancements(
                qla_row, combined, table_key, plan_lookup or {},
            )
            mpolicy = self.normalize(qla_row.get("MPOLICY", ""))

            if validation_enabled:
                if not mpolicy:
                    stats["blank_mpolicy_rows"] += 1
                    stats["held_rows"] += 1
                    hold_rows.append(self._build_cross_table_hold_row(
                        row, table_key, staged_path, dest_path, "BLANK_MPOLICY", mpolicy, audit_ts, prod_flag,
                    ))
                elif mpolicy not in mpolicy_set:
                    stats["missing_mpolicy_rows"] += 1
                    stats["held_rows"] += 1
                    hold_rows.append(self._build_cross_table_hold_row(
                        row, table_key, staged_path, dest_path, "MPOLICY_NOT_IN_OUTPUT",
                        mpolicy, audit_ts, prod_flag,
                    ))
                else:
                    emit_rows.append(qla_row)
            else:
                emit_rows.append(qla_row)

        stats["emitted_rows"] = len(emit_rows)
        if stats["held_rows"]:
            stats["validation_status"] = "HELD_ROWS_PRESENT"
        emit_df = pd.DataFrame(emit_rows, columns=schema) if emit_rows else pd.DataFrame(columns=schema)
        return emit_df, hold_rows, stats

    def _write_cross_table_validation_report(self, output_dir, report_rows, audit_ts, prod_flag):
        report_path = os.path.normpath(os.path.join(output_dir, CLAIMS_CROSS_TABLE_VALIDATION_REPORT))
        fieldnames = [
            "audit_timestamp", "production_dbf_flag", "validation_name", "source_file",
            "reference_file", "total_source_rows", "emitted_rows", "held_rows",
            "blank_mpolicy_rows", "missing_mpolicy_rows", "validation_status", "rulebook_lineage",
        ]
        rows = []
        for item in report_rows:
            rows.append({
                "audit_timestamp": audit_ts,
                "production_dbf_flag": prod_flag,
                "validation_name": item.get("validation_name", ""),
                "source_file": item.get("source_file", ""),
                "reference_file": item.get("reference_file", ""),
                "total_source_rows": item.get("total_source_rows", 0),
                "emitted_rows": item.get("emitted_rows", 0),
                "held_rows": item.get("held_rows", 0),
                "blank_mpolicy_rows": item.get("blank_mpolicy_rows", 0),
                "missing_mpolicy_rows": item.get("missing_mpolicy_rows", 0),
                "validation_status": item.get("validation_status", ""),
                "rulebook_lineage": PHASE20_RULEBOOK_LINEAGE,
            })
        with open(report_path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return report_path

    def _write_cross_table_validation_summary(self, output_dir, report_rows, hold_rows, audit_ts, prod_flag, quikmstr_path):
        cfg = self.CLAIMS_ORCHESTRATION
        summary_path = os.path.normpath(os.path.join(output_dir, CLAIMS_CROSS_TABLE_VALIDATION_SUMMARY))
        lines = [
            "QLAdmin Enterprise Claims — Cross-Table MPOLICY Validation Summary",
            "=" * 60,
            "",
            "IMPORTANT — UAT SAFETY GATE ONLY",
            "-" * 30,
            "This validation is for UAT output safety only.",
            "This is NOT production cutover.",
            "This is NOT production authorized DBF generation.",
            f"production_dbf_flag={prod_flag}",
            f"Go-Live Target: {cfg.get('go_live_target', '2026-09-01')}",
            "",
            f"Audit Timestamp: {audit_ts}",
            f"Reference Policy Master: {quikmstr_path}",
            "",
            "WHAT WAS CHECKED",
            "-" * 30,
            "Each governance-cleared staged claim/payment was checked against converted output/quikmstr.csv.",
            "Records referencing missing or blank MPOLICY values were held from UAT emit.",
            "",
        ]
        for item in report_rows:
            lines.extend([
                f"{item.get('validation_name', 'VALIDATION')}:",
                f"  Source: {item.get('source_file', '')}",
                f"  Total staged rows: {item.get('total_source_rows', 0)}",
                f"  Emitted rows: {item.get('emitted_rows', 0)}",
                f"  Held rows: {item.get('held_rows', 0)}",
                f"  Blank MPOLICY rows: {item.get('blank_mpolicy_rows', 0)}",
                f"  Missing MPOLICY rows: {item.get('missing_mpolicy_rows', 0)}",
                f"  Status: {item.get('validation_status', '')}",
                "",
            ])
        lines.extend([
            f"Total cross-table validation holds appended to manifest: {len(hold_rows)}",
            "",
            "Held records were blocked because the policy was missing from quikmstr.csv,",
            "blank/unresolved, or because quikmstr.csv itself was not available.",
        ])
        with open(summary_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        return summary_path

    def _load_cross_table_validation_panel_status(self):
        output_dir = self._resolve_output_base_dir() if hasattr(self, "path_vars") else os.path.join(
            self.CLAIMS_ORCHESTRATION.get("app_base_dir", ""), "output",
        )
        report_path = os.path.join(output_dir, CLAIMS_CROSS_TABLE_VALIDATION_REPORT)
        if self._last_cross_table_validation:
            val = self._last_cross_table_validation
            return {
                "mpolicy_validation_status": val.get("validation_status_label", "NOT YET GENERATED"),
                "claims_held_missing_policy": str(val.get("claims_held_missing_policy", "NOT YET GENERATED")),
                "payments_held_missing_policy": str(val.get("payments_held_missing_policy", "NOT YET GENERATED")),
                "cross_table_validation_report": val.get("validation_report_path", report_path),
            }
        if not os.path.isfile(report_path):
            return {
                "mpolicy_validation_status": "NOT YET GENERATED",
                "claims_held_missing_policy": "NOT YET GENERATED",
                "payments_held_missing_policy": "NOT YET GENERATED",
                "cross_table_validation_report": report_path,
            }
        try:
            df = pd.read_csv(report_path, dtype=str)
            claims_row = df[df["validation_name"].str.contains("QUIKCLMS", case=False, na=False)]
            pay_row = df[df["validation_name"].str.contains("QUIKCLMP", case=False, na=False)]
            claims_held = int(claims_row.iloc[0]["held_rows"]) if not claims_row.empty else 0
            pay_held = int(pay_row.iloc[0]["held_rows"]) if not pay_row.empty else 0
            statuses = df["validation_status"].astype(str).tolist()
            if any("BLOCKED" in s for s in statuses):
                status_label = "BLOCKED — QUIKMSTR MISSING"
            elif any("HELD" in s for s in statuses):
                status_label = "HELD ROWS PRESENT (UAT ONLY)"
            elif any("PASS" in s for s in statuses):
                status_label = "PASS (UAT ONLY — NOT PRODUCTION)"
            else:
                status_label = statuses[0] if statuses else "UNKNOWN"
            return {
                "mpolicy_validation_status": status_label,
                "claims_held_missing_policy": str(claims_held),
                "payments_held_missing_policy": str(pay_held),
                "cross_table_validation_report": report_path,
            }
        except Exception:
            return {
                "mpolicy_validation_status": "REPORT READ ERROR",
                "claims_held_missing_policy": "NOT YET GENERATED",
                "payments_held_missing_policy": "NOT YET GENERATED",
                "cross_table_validation_report": report_path,
            }

    def _resolve_output_base_dir(self):
        cfg = self.CLAIMS_ORCHESTRATION
        out_var = self.path_vars.get("Out")
        if out_var and out_var[0].get().strip():
            norm = os.path.normpath(out_var[0].get().strip())
        else:
            norm = os.path.normpath(os.path.join(cfg["app_base_dir"], "output"))
        staging_sub = cfg.get("staging_subdir", "claims_uat_staging")
        if os.path.basename(norm).lower() == staging_sub.lower():
            return os.path.dirname(norm)
        return norm

    def _count_csv_data_rows(self, path):
        if not os.path.isfile(path):
            return 0
        try:
            with open(path, encoding="utf-8") as fh:
                return max(sum(1 for _ in fh) - 1, 0)
        except OSError:
            return 0

    def _append_review_hold_rows(self, manifest_rows, seen_keys, df, hold_category, source_file, prod_flag, emit_ts):
        if df is None or df.empty:
            return
        id_fields = (
            "reconstructed_claim_id", "derivation_candidate_id", "record_identifier",
            "canonical_payment_stage_id", "prototype_claimnum",
        )
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            normalized = {str(k).strip().lower(): v for k, v in row_dict.items()}
            record_type = str(normalized.get("record_type", "")).strip().upper() or "UNKNOWN"
            record_id = ""
            for field in id_fields:
                val = str(normalized.get(field, "")).strip()
                if val and val.lower() not in ("nan", "none"):
                    record_id = val
                    break
            dedupe_key = (record_type, record_id, hold_category)
            if not record_id or dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            blocker = str(normalized.get("blocker_category", "")).strip()
            reason = str(
                normalized.get("deferred_category", "")
                or normalized.get("reason_excluded", "")
                or blocker
            ).strip()
            rc = str(normalized.get("reconstructed_claim_id", "")).strip()
            deriv = str(normalized.get("derivation_candidate_id", "")).strip()
            manifest_rows.append({
                "audit_timestamp": emit_ts,
                "emit_timestamp": emit_ts,
                "production_dbf_flag": str(normalized.get("production_dbf_flag", prod_flag)).strip() or prod_flag,
                "hold_category": hold_category,
                "record_type": record_type,
                "record_identifier": record_id,
                "record_id": record_id,
                "reconstructed_claim_id": rc,
                "derivation_candidate_id": deriv,
                "MPOLICY": str(normalized.get("mpolicy", "")).strip(),
                "blocker_category": blocker,
                "reason_excluded": reason,
                "reason_held": reason,
                "governance_status": str(normalized.get("governance_status", "")).strip(),
                "business_review_required": str(normalized.get("business_review_required", "")).strip(),
                "business_explanation": str(normalized.get("business_explanation", "")).strip(),
                "remediation_recommendation": str(normalized.get("remediation_recommendation", "")).strip(),
                "source_file": source_file,
                "target_file": "",
                "rulebook_lineage": str(normalized.get("rulebook_lineage", "")).strip(),
            })

    def _append_cross_table_hold_rows(self, manifest_rows, seen_keys, hold_rows):
        for row in hold_rows:
            dedupe_key = (
                row.get("record_type", ""),
                row.get("record_id", ""),
                row.get("hold_category", "CROSS_TABLE_VALIDATION"),
            )
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            manifest_rows.append(row)

    def _build_review_hold_manifest_rows(self, cross_table_hold_rows=None):
        cfg = self.CLAIMS_ORCHESTRATION
        gov_dir = self._phase17_governance_dir()
        emit_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prod_flag = cfg.get("production_dbf_flag", "N")
        manifest_rows = []
        seen_keys = set()
        sources = [
            ("deferred_governance_claims.csv", "DEFERRED_CLAIM", gov_dir),
            ("deferred_governance_payments.csv", "DEFERRED_PAYMENT", gov_dir),
            ("business_exclusion_log.csv", "EXCLUSION", gov_dir),
        ]
        for filename, hold_category, directory in sources:
            df = self._load_governance_csv_safe(filename, directory=directory)
            self._append_review_hold_rows(
                manifest_rows, seen_keys, df, hold_category, filename, prod_flag, emit_ts,
            )
        if cross_table_hold_rows:
            self._append_cross_table_hold_rows(manifest_rows, seen_keys, cross_table_hold_rows)
        return manifest_rows

    def _write_review_hold_manifest(self, output_dir, manifest_rows):
        manifest_path = os.path.normpath(os.path.join(output_dir, CLAIMS_REVIEW_HOLD_MANIFEST))
        fieldnames = self._review_hold_manifest_fieldnames()
        with open(manifest_path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(manifest_rows)
        return manifest_path

    def _emit_uat_claims_to_main_output(self, staging_dir):
        cfg = self.CLAIMS_ORCHESTRATION
        output_dir = self._resolve_output_base_dir()
        os.makedirs(output_dir, exist_ok=True)
        emit_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prod_flag = cfg.get("production_dbf_flag", "N")
        emitted = {}
        missing = []
        cross_table_holds = []
        report_rows = []
        validation_enabled = self._claims_mpolicy_validation_enabled()
        lookups = self._build_mpolicy_derivation_lookup()
        crosswalk = self._load_policy_crosswalk_map()

        if validation_enabled:
            mpolicy_set, quikmstr_path = self._load_converted_mpolicy_set(output_dir)
            quikmstr_missing = mpolicy_set is None
            if quikmstr_missing:
                self.log("PHASE 20 MPOLICY VALIDATION: output/quikmstr.csv missing — claims emit blocked.")
            else:
                self.log(
                    f"PHASE 20 MPOLICY VALIDATION: loaded {len(mpolicy_set)} converted MPOLICY values "
                    f"from {quikmstr_path}"
                )
        else:
            mpolicy_set = set()
            quikmstr_path = os.path.join(output_dir, "quikmstr.csv")
            quikmstr_missing = False
            self.log(
                "PHASE 21 QLA EMIT: MPOLICY validation disabled — writing QLA-shaped rows without cross-table filter."
            )

        self.log(
            f"PHASE 21 QLA EMIT: transforming UAT governance rows via Phase 10 + Sync_Rulebook "
            f"({PHASE21_RULEBOOK_LINEAGE})"
        )
        prelsa_path = self._resolve_claims_prelsa_path()
        p10_path = self._phase10_derivation_path("quikclmp")
        self.log(f"PHASE 22 LINEAGE: PRELSA source for payee enrichment = {prelsa_path}")
        self.log(f"PHASE 22 LINEAGE: Phase 10A derivation index = {p10_path}")
        plan_lookup = build_plan_metadata_lookup(
            os.path.join(output_dir, "quikridr.csv"),
            os.path.join(output_dir, "quikplan.csv"),
        )
        clms_p10_by_rc = self._build_clms_p10_rc_index()
        emitted_frames = {}

        try:
            for table_key, source_key in (
                ("quikclms", "uat_quikclms_source"),
                ("quikclmp", "uat_quikclmp_source"),
            ):
                staged_path = os.path.normpath(os.path.join(staging_dir, f"{table_key}.csv"))
                uat_source = cfg[source_key]
                if os.path.isfile(staged_path):
                    copy_from = staged_path
                elif os.path.isfile(uat_source):
                    copy_from = uat_source
                else:
                    missing.append(table_key)
                    emitted[table_key] = None
                    continue

                dest_path = os.path.normpath(os.path.join(output_dir, f"{table_key}.csv"))
                emit_df, hold_rows, stats = self._validate_and_filter_staged_claims_csv(
                    copy_from, table_key, mpolicy_set or set(), quikmstr_path,
                    lookups, crosswalk, quikmstr_missing, emit_ts, prod_flag, output_dir,
                    validation_enabled=validation_enabled,
                    plan_lookup=plan_lookup,
                    clms_p10_by_rc=clms_p10_by_rc,
                )
                cross_table_holds.extend(hold_rows)
                report_rows.append(stats)

                if emit_df is None:
                    emitted[table_key] = None
                    continue

                tmp_path = dest_path + ".tmp"
                emit_df.to_csv(tmp_path, index=False, encoding="utf-8")
                os.replace(tmp_path, dest_path)
                emitted_frames[table_key] = emit_df
                emitted[table_key] = {
                    "dest_path": dest_path,
                    "source_path": copy_from,
                    "row_count": len(emit_df),
                    "held_rows": stats.get("held_rows", 0),
                }

            manifest_rows = self._build_review_hold_manifest_rows(cross_table_holds)
            manifest_path = self._write_review_hold_manifest(output_dir, manifest_rows)
            validation_report_path = None
            validation_summary_path = None
            enhancement_report_path = None
            enhancement_summary_path = None
            if report_rows:
                validation_report_path = self._write_cross_table_validation_report(
                    output_dir, report_rows, emit_ts, prod_flag,
                )
                validation_summary_path = self._write_cross_table_validation_summary(
                    output_dir, report_rows, cross_table_holds, emit_ts, prod_flag, quikmstr_path,
                )

            if emitted_frames.get("quikclms") is not None or emitted_frames.get("quikclmp") is not None:
                enhancement_metrics = validate_claims_emit_enhancements(
                    emitted_frames.get("quikclms"),
                    emitted_frames.get("quikclmp"),
                    QUIKCLMS_SCHEMA,
                    QUIKCLMP_SCHEMA,
                )
                enhancement_report_path, enhancement_summary_path = (
                    write_claims_emit_enhancement_validation(
                        output_dir, enhancement_metrics, emit_ts, prod_flag,
                        CLAIMS_EMIT_ENHANCEMENT_VALIDATION_REPORT,
                        CLAIMS_EMIT_ENHANCEMENT_VALIDATION_SUMMARY,
                    )
                )
                self.log(
                    "CLAIMS EMIT ENHANCEMENTS: "
                    f"CLAIMNUM normalized={enhancement_metrics.get('claimnum_normalized_count', 0)} "
                    f"ISWL/98={enhancement_metrics.get('iswl_status_98_count', 0)} "
                    f"MSEQ non-98 violations="
                    f"{enhancement_metrics.get('non98_clms_mseq_not_zero', 0)}+"
                    f"{enhancement_metrics.get('non98_clmp_mseq_not_zero', 0)} "
                    f"status={enhancement_metrics.get('validation_status', '')}"
                )
                self.log(f"  Enhancement validation report: {enhancement_report_path}")

            hold_by_category = {}
            for row in manifest_rows:
                cat = row.get("hold_category", "UNKNOWN")
                hold_by_category[cat] = hold_by_category.get(cat, 0) + 1

            claims_held = sum(
                1 for h in cross_table_holds
                if str(h.get("record_type", "")).upper() in ("CLAIM", "QUIKCLMS")
            )
            payments_held = sum(
                1 for h in cross_table_holds
                if str(h.get("record_type", "")).upper() in ("PAYMENT", "QUIKCLMP")
            )
            semantic_held = sum(
                1 for h in cross_table_holds
                if str(h.get("hold_category", "")).upper() == SEMANTIC_HOLD_CATEGORY
            )
            if quikmstr_missing and validation_enabled:
                validation_status_label = "BLOCKED — QUIKMSTR MISSING"
                validation_ok = False
            elif cross_table_holds and validation_enabled:
                validation_status_label = "HELD ROWS PRESENT (UAT ONLY)"
                validation_ok = True
            elif validation_enabled:
                validation_status_label = "PASS (UAT ONLY — NOT PRODUCTION)"
                validation_ok = True
            else:
                validation_status_label = "DISABLED"
                validation_ok = True

            result = {
                "emit_timestamp": emit_ts,
                "output_dir": output_dir,
                "emitted": emitted,
                "missing_tables": missing,
                "manifest_path": manifest_path,
                "hold_count": len(manifest_rows),
                "hold_by_category": hold_by_category,
                "validation_ok": validation_ok,
                "validation_blocked": bool(quikmstr_missing and validation_enabled),
                "validation_error": None,
                "validation_enabled": validation_enabled,
                "validation_status_label": validation_status_label,
                "claims_held_missing_policy": claims_held,
                "payments_held_missing_policy": payments_held,
                "semantic_hold_rows": semantic_held,
                "validation_report_path": validation_report_path,
                "validation_summary_path": validation_summary_path,
                "enhancement_validation_report_path": enhancement_report_path,
                "enhancement_validation_summary_path": enhancement_summary_path,
                "cross_table_hold_count": len(cross_table_holds),
            }
            self._last_cross_table_validation = result
            return result
        except Exception as exc:
            self.log(f"PHASE 20 MPOLICY VALIDATION ERROR: {exc}")
            return {
                "emit_timestamp": emit_ts,
                "output_dir": output_dir,
                "emitted": emitted,
                "missing_tables": missing,
                "manifest_path": None,
                "hold_count": 0,
                "hold_by_category": {},
                "validation_ok": False,
                "validation_blocked": False,
                "validation_error": str(exc),
                "validation_enabled": validation_enabled,
                "validation_status_label": "ERROR",
                "claims_held_missing_policy": 0,
                "payments_held_missing_policy": 0,
                "validation_report_path": None,
                "validation_summary_path": None,
                "cross_table_hold_count": 0,
            }

    def _log_uat_emit_summary(self, emit_result):
        if not emit_result:
            return
        self.log("UAT CLAIMS EMIT (Phase 21 — QLA-shaped via Phase 10 + Sync_Rulebook; MPOLICY validated when enabled):")
        self.log(f"  Main output folder: {emit_result['output_dir']}")
        if self._claims_semantic_governance_enabled():
            self.log(
                f"  Phase 22 semantic governance hold: {emit_result.get('semantic_hold_rows', 0)} rows "
                f"quarantined ({SEMANTIC_HOLD_CATEGORY})"
            )
            self.log("  Authoritative manuals: docs/claims_conversion_reference/QLAdmin_Help.pdf + LifePRO Accounting Transactions")
        if emit_result.get("validation_enabled"):
            self.log(f"  MPOLICY validation: {emit_result.get('validation_status_label', 'UNKNOWN')}")
            if emit_result.get("validation_report_path"):
                self.log(f"  Validation report: {emit_result['validation_report_path']}")
            self.log(
                f"  Cross-table holds: claims={emit_result.get('claims_held_missing_policy', 0)} "
                f"payments={emit_result.get('payments_held_missing_policy', 0)}"
            )
        for table_key, info in emit_result["emitted"].items():
            if info:
                held_note = ""
                if info.get("held_rows"):
                    held_note = f" ({info['held_rows']} held before emit)"
                self.log(f"  Emitted {table_key.upper()}: {info['row_count']} rows -> {info['dest_path']}{held_note}")
                self.log(f"    Source: {info['source_path']}")
            else:
                self.log(f"  {table_key.upper()}: NOT EMITTED")
        if emit_result.get("validation_blocked"):
            self.log("  All staged claims/payments held — output/quikmstr.csv not found.")
        if emit_result.get("validation_error"):
            self.log(f"  Validation error: {emit_result['validation_error']}")
        self.log(f"  Review hold manifest: {emit_result.get('manifest_path', '')}")
        self.log(f"  Records held for review (total manifest): {emit_result.get('hold_count', 0)}")
        for cat, count in sorted(emit_result.get("hold_by_category", {}).items()):
            self.log(f"    {cat}: {count}")
        self.log("  Deferred/excluded populations were NOT emitted to main output.")
        self.log(f"  production_dbf_flag={self.CLAIMS_ORCHESTRATION.get('production_dbf_flag', 'N')}")

    def _uat_packages_root(self):
        return os.path.normpath(os.path.join(self._resolve_output_base_dir(), UAT_PACKAGE_SUBDIR))

    def _write_uat_package_readme(self, package_dir, package_timestamp, copied_count, missing_count):
        cfg = self.CLAIMS_ORCHESTRATION
        go_live = cfg.get("go_live_target", "2026-09-01")
        lines = [
            "QLAdmin Enterprise Claims — UAT Business Review Package",
            "=" * 60,
            "",
            f"Package Timestamp: {package_timestamp}",
            f"Generated By: app.py v54.7 (Phase 18D — copy-only handoff)",
            "",
            "IMPORTANT — UAT REVIEW ONLY",
            "-" * 30,
            "This package is for UAT and business review only.",
            "This is NOT production cutover.",
            "No production DBF files are included in this package.",
            f"production_dbf_flag={cfg.get('production_dbf_flag', 'N')}",
            f"Go-Live Target: {go_live}",
            "",
            "app.py did not modify claims logic. All contents were copied read-only",
            "from Phase 17 UAT governance reporting outputs.",
            "",
            "PACKAGE CONTENTS",
            "-" * 30,
            "01_uat_candidate_data/",
            "  Good/testable UAT candidate claim and payment populations cleared for review.",
            "",
            "02_deferred_governance/",
            "  Claims and payments deferred by governance rules — not included in UAT candidates.",
            "",
            "03_business_review_logs/",
            "  Exclusion reasons, exception catalog, remediation notes, and issue examples.",
            "",
            "04_executive_reporting/",
            "  Executive dashboard KPIs, blocker trends, and summary text reports.",
            "",
            "05_business_workbenches/",
            "  Business review work queues (surrender, orphan, high-priority decisions).",
            "",
            "FILE COPY SUMMARY",
            "-" * 30,
            f"Files copied: {copied_count}",
            f"Files missing (listed in package_manifest.csv): {missing_count}",
            "",
            "See package_manifest.csv for per-file copy status.",
        ]
        readme_path = os.path.join(package_dir, "README_UAT_PACKAGE.txt")
        with open(readme_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        return readme_path

    def _write_uat_package_manifest(self, package_dir, package_timestamp, manifest_rows):
        manifest_path = os.path.join(package_dir, "package_manifest.csv")
        fieldnames = [
            "package_timestamp", "source_file", "package_file", "category",
            "copied_flag", "missing_reason", "production_dbf_flag",
        ]
        with open(manifest_path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(manifest_rows)
        return manifest_path

    def _create_uat_package_zip(self, packages_root, package_name, package_dir):
        zip_path = os.path.normpath(os.path.join(packages_root, f"{package_name}.zip"))
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(package_dir):
                for filename in files:
                    full_path = os.path.join(root, filename)
                    arcname = os.path.join(package_name, os.path.relpath(full_path, package_dir))
                    zf.write(full_path, arcname)
        return zip_path

    def _create_uat_business_package(self):
        cfg = self.CLAIMS_ORCHESTRATION
        source_root = self._phase17_governance_dir()
        package_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stamp_token = datetime.now().strftime("%Y%m%d_%H%M%S")
        package_name = f"UAT_PACKAGE_{stamp_token}"
        packages_root = self._uat_packages_root()
        package_dir = os.path.normpath(os.path.join(packages_root, package_name))
        os.makedirs(package_dir, exist_ok=True)

        manifest_rows = []
        copied_count = 0
        missing_count = 0
        prod_flag = cfg.get("production_dbf_flag", "N")

        for category, filenames in UAT_PACKAGE_CATEGORIES.items():
            category_dir = os.path.join(package_dir, category)
            os.makedirs(category_dir, exist_ok=True)
            for filename in filenames:
                source_path = os.path.normpath(os.path.join(source_root, filename))
                package_rel = os.path.join(category, filename)
                package_path = os.path.normpath(os.path.join(package_dir, package_rel))
                row = {
                    "package_timestamp": package_timestamp,
                    "source_file": source_path,
                    "package_file": package_rel.replace("\\", "/"),
                    "category": category,
                    "copied_flag": "N",
                    "missing_reason": "",
                    "production_dbf_flag": prod_flag,
                }
                if os.path.isfile(source_path):
                    shutil.copy2(source_path, package_path)
                    row["copied_flag"] = "Y"
                    copied_count += 1
                else:
                    row["missing_reason"] = "SOURCE_NOT_FOUND"
                    missing_count += 1
                manifest_rows.append(row)

        readme_path = self._write_uat_package_readme(
            package_dir, package_timestamp, copied_count, missing_count,
        )
        manifest_path = self._write_uat_package_manifest(package_dir, package_timestamp, manifest_rows)

        zip_path = None
        zip_error = None
        try:
            zip_path = self._create_uat_package_zip(packages_root, package_name, package_dir)
        except Exception as exc:
            zip_error = str(exc)

        return {
            "package_name": package_name,
            "package_dir": package_dir,
            "packages_root": packages_root,
            "readme_path": readme_path,
            "manifest_path": manifest_path,
            "zip_path": zip_path,
            "zip_error": zip_error,
            "copied_count": copied_count,
            "missing_count": missing_count,
            "total_files": copied_count + missing_count,
            "package_timestamp": package_timestamp,
        }

    def _on_create_uat_business_package(self):
        self.log("UAT BUSINESS PACKAGE: starting copy-only handoff generation (Phase 18D)...")
        try:
            result = self._create_uat_business_package()
        except Exception as exc:
            self.log(f"UAT BUSINESS PACKAGE ERROR: {exc}")
            messagebox.showerror("UAT Package Error", f"Package creation failed:\n{exc}")
            return

        self.log(f"UAT BUSINESS PACKAGE: folder created -> {result['package_dir']}")
        self.log(f"  README -> {result['readme_path']}")
        self.log(f"  Manifest -> {result['manifest_path']}")
        self.log(f"  Files copied: {result['copied_count']} | Missing: {result['missing_count']}")
        if result["zip_path"]:
            self.log(f"UAT BUSINESS PACKAGE: ZIP created -> {result['zip_path']}")
        elif result["zip_error"]:
            self.log(f"UAT BUSINESS PACKAGE WARNING: ZIP creation failed — {result['zip_error']}")
            self.log("  Package folder retained; review files directly.")

        messagebox.showinfo(
            "UAT Business Package Created",
            "\n".join([
                "UAT business review package created successfully.",
                "",
                f"Folder:\n{result['package_dir']}",
                "",
                f"Copied: {result['copied_count']} file(s)",
                f"Missing: {result['missing_count']} file(s)",
                "",
                f"ZIP: {result['zip_path'] or 'Not created (see console warning)'}",
                "",
                "This package is for UAT review only — not production cutover.",
            ]),
        )

    def _execute_claims_orchestration(self, table_id, full_uat_population=False, batch_context=False):
        cfg = self.CLAIMS_ORCHESTRATION
        t_id = table_id.lower()
        phase_label = "Phase 18A–20" if batch_context else "Phase 18A–20"
        self.log(f"CLAIMS ORCHESTRATION: {t_id.upper()} ({phase_label} — external pipeline + UAT emit)")
        self.log(f"  UAT population source: {cfg.get('uat_source_label', 'Phase17')}")
        if batch_context:
            self.log("  Batch context: full UAT population (quikclms + quikclmp)")
        self.log(f"  RUN_MODE={cfg['run_mode']} | production_dbf_flag={cfg['production_dbf_flag']} | go_live={cfg['go_live_target']}")

        result = {"emit_result": None, "staging_dir": None, "batch_context": batch_context, "dbf_result": None}

        if cfg["run_mode"] == "DISABLED":
            self.log("  Claims orchestration DISABLED. No staging action taken.")
            self._refresh_governance_visibility()
            return result

        if cfg["run_mode"] == "PRODUCTION":
            self.log("  PRODUCTION orchestration blocked until later authorization.")
            self.log("  External Phase 17 runner will NOT execute. No production DBF generation.")
            self._refresh_governance_visibility()
            return result

        staging_dir = self._claims_staging_dir()
        result["staging_dir"] = staging_dir
        pre_existing = {
            "quikclms": os.path.isfile(os.path.join(staging_dir, "quikclms.csv")),
            "quikclmp": os.path.isfile(os.path.join(staging_dir, "quikclmp.csv")),
        }

        runner_success = None
        if self._claims_lineage_refresh_enabled():
            refresh_ok = self._invoke_phase10a_quikclmp_refresh()
            if not refresh_ok:
                self.log("  Phase 10A lineage refresh failed — emit will use existing derivation candidates.")
        if self._claims_orchestrate_enabled():
            if not getattr(self, "_claims_pipeline_runner_completed", False):
                runner_success = self._invoke_external_claims_pipeline(staging_dir)
                self._claims_pipeline_runner_completed = True
                self._claims_pipeline_runner_success = runner_success
            else:
                runner_success = getattr(self, "_claims_pipeline_runner_success", False)
                self.log("  External Phase 17 runner already executed this session.")

            if runner_success:
                restaged = self._restage_all_uat_candidates(staging_dir)
                for table_key, staged_path, source_path in restaged:
                    self.log(f"  UAT restage: {table_key.upper()} -> {staged_path}")
                    self.log(f"    Source: {source_path}")
                if not restaged:
                    self.log("  Runner succeeded but UAT candidate sources were not found for restaging.")
            else:
                self.log("  Runner failed — preserving pre-existing staged files only (no stale restage).")
                for table_key, existed in pre_existing.items():
                    if existed:
                        self.log(f"  Preserved existing staged file: {table_key}.csv")
                    else:
                        self.log(f"  No staged file created for {table_key}.csv")
        else:
            if full_uat_population:
                restaged = self._restage_all_uat_candidates(staging_dir)
                for table_key, staged_path, source_path in restaged:
                    self.log(f"  UAT staging: {table_key.upper()} -> {staged_path}")
                    self.log(f"    Source population: {source_path}")
                if not restaged:
                    self.log("  UAT candidate sources not found for one or both claims tables.")
                    self.log("  Run Phase 17 UAT governance reporting to materialize candidate populations.")
            else:
                uat_source = self._claims_uat_source_path(t_id)
                if os.path.isfile(uat_source):
                    ok, staged_path = self._stage_uat_candidate_file(staging_dir, t_id, uat_source)
                    if ok:
                        self.log(f"  UAT staging: copied governance-cleared candidate -> {staged_path}")
                        self.log(f"  Source population: {uat_source}")
                else:
                    self.log(f"  UAT candidate source not found: {uat_source}")
                    self.log("  Run Phase 17 UAT governance reporting to materialize candidate populations.")
            self.log("  Orchestration hook: PREP ONLY (set QLA_CLAIMS_ORCHESTRATE=1 to execute Phase 17 runner)")

        prep_log = os.path.normpath(os.path.join(staging_dir, "claims_uat_orchestration_prep.txt"))
        with open(prep_log, "a", encoding="utf-8") as fh:
            fh.write("\n".join([
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] table={t_id.upper()}",
                f"batch_context={batch_context}",
                f"full_uat_population={full_uat_population}",
                f"RUN_MODE={cfg['run_mode']}",
                f"production_dbf_flag={cfg['production_dbf_flag']}",
                f"production_authorization_flag={cfg['production_authorization_flag']}",
                f"orchestrate_enabled={self._claims_orchestrate_enabled()}",
                f"runner_success={runner_success}",
                "inline_claims_conversion=BLOCKED",
                f"orchestration_runner={cfg['orchestration_runner']}",
            ]) + "\n")

        emit_result = None
        if self._claims_uat_emit_enabled():
            emit_result = self._emit_uat_claims_to_main_output(staging_dir)
            self._log_uat_emit_summary(emit_result)
            if emit_result and os.path.isfile(os.path.join(emit_result.get("output_dir", ""), "quikclms.csv")):
                overlay_result = self._apply_client_claim_decision_overlays(
                    emit_result.get("output_dir") or self._resolve_output_base_dir()
                )
                emit_result["client_overlays"] = overlay_result
                self._log_client_claim_overlay_summary(overlay_result)
                recovery_result = self._apply_issue78_quikclmp_recovery(
                    emit_result.get("output_dir") or self._resolve_output_base_dir()
                )
                emit_result["issue78_recovery"] = recovery_result
                self._log_issue78_recovery_summary(recovery_result)
                if recovery_result.get("applied") and emit_result.get("emitted", {}).get("quikclmp"):
                    emit_result["emitted"]["quikclmp"]["row_count"] = (
                        int(emit_result["emitted"]["quikclmp"].get("row_count", 0))
                        + int(recovery_result.get("rows_added", 0))
                    )
                remap_result = self._apply_issue79_claimstat_remap(
                    emit_result.get("output_dir") or self._resolve_output_base_dir()
                )
                emit_result["issue79_remap"] = remap_result
                self._log_issue79_remap_summary(remap_result)
                structure_result = self._apply_issue85_claim_header_structure(
                    emit_result.get("output_dir") or self._resolve_output_base_dir()
                )
                emit_result["issue85_structure"] = structure_result
                self._log_issue85_structure_summary(structure_result)
                if structure_result.get("applied") and emit_result.get("emitted", {}).get("quikclms"):
                    emit_result["emitted"]["quikclms"]["row_count"] = int(
                        structure_result.get("headers_after", 0)
                    )
                track_a_result = self._apply_issue84_track_a_header_backfill(
                    emit_result.get("output_dir") or self._resolve_output_base_dir()
                )
                emit_result["issue84_track_a"] = track_a_result
                self._log_issue84_track_a_summary(track_a_result)
                # Order locked v58.57: #135 expansion first (creates 142 derived headers),
                # then #134 PNOTE-B MEMOTEXT overlay (covers new + existing death rows;
                # preserves CSO_CONTROLLED_NO_PACTG_HISTORY on 308), then MINTAMT=0.
                issue135_expand = self._apply_issue135_cso_claims_expansion(
                    emit_result.get("output_dir") or self._resolve_output_base_dir()
                )
                emit_result["issue135_cso_expansion"] = issue135_expand
                self._log_issue135_cso_expansion_summary(issue135_expand)
                issue134_result = self._apply_issue134_claim_memos(
                    emit_result.get("output_dir") or self._resolve_output_base_dir()
                )
                emit_result["issue134_claim_memos"] = issue134_result
                self._log_issue134_claim_memo_summary(issue134_result)
                issue135_result = self._apply_issue135_mintamt_zero(
                    emit_result.get("output_dir") or self._resolve_output_base_dir()
                )
                emit_result["issue135_mintamt"] = issue135_result
                self._log_issue135_mintamt_summary(issue135_result)
                # Last claims CSV mutate before UAT DBF generate / Append packaging.
                mseq_align = self._apply_claims_payee_mseq_align(
                    emit_result.get("output_dir") or self._resolve_output_base_dir()
                )
                emit_result["claims_payee_mseq_align"] = mseq_align
                self._log_claims_payee_mseq_align_summary(mseq_align)
                if not mseq_align.get("ok"):
                    emit_result["validation_ok"] = False
                    emit_result["validation_error"] = (
                        "claims_payee_mseq_align_failed:"
                        + str(mseq_align.get("reason") or "unknown")
                    )
        else:
            self.log("  UAT emit skipped (RUN_MODE != UAT or QLA_CLAIMS_UAT_EMIT=0).")

        result["emit_result"] = emit_result
        if emit_result and emit_result.get("validation_ok"):
            dbf_result = self._maybe_generate_uat_claims_dbf(emit_result)
            result["dbf_result"] = dbf_result
        elif self._claims_uat_dbf_generation_enabled():
            self.log("  UAT DBF generation skipped — validated CSV emit did not complete.")

        self._log_governance_console_summary()
        self._refresh_governance_visibility()
        return result

    def _execute_batch_claims_uat_finale(self):
        if not self._batch_include_claims_uat_enabled():
            self.log("BATCH UAT CLAIMS (18F): not enabled (set QLA_BATCH_INCLUDE_CLAIMS_UAT=1 in UAT mode).")
            return None
        self.log("=" * 60)
        self.log("BATCH UAT CLAIMS FINALE (Phase 18F — after standard table batch)")
        self.log(f"  UAT population source: {self.CLAIMS_ORCHESTRATION.get('uat_source_label', 'Phase17')}")
        self.log("  Client-decision overlays (Items 18–19) applied automatically after emit.")
        self.log("  Governance-cleared UAT candidates only; deferred populations excluded.")
        self.log(f"  production_dbf_flag={self.CLAIMS_ORCHESTRATION.get('production_dbf_flag', 'N')}")
        orch_result = self._execute_claims_orchestration(
            "quikclms", full_uat_population=True, batch_context=True,
        )
        emit_result = orch_result.get("emit_result") if orch_result else None
        dbf_result = orch_result.get("dbf_result") if orch_result else None
        self._log_batch_claims_uat_summary(emit_result, dbf_result)
        return {"emit_result": emit_result, "dbf_result": dbf_result}

    def _log_batch_claims_uat_summary(self, emit_result, dbf_result=None):
        self.log("BATCH UAT CLAIMS SUMMARY (Phase 18F):")
        if not emit_result:
            self.log("  No UAT claims emit result (orchestration blocked or emit disabled).")
            return
        emitted = emit_result.get("emitted", {})
        for table_key in ("quikclms", "quikclmp"):
            info = emitted.get(table_key)
            if info:
                self.log(f"  {table_key.upper()} in main output: {info['row_count']} rows")
            else:
                self.log(f"  {table_key.upper()}: not emitted")
        self.log(f"  Review holds: {emit_result.get('hold_count', 0)} records -> {emit_result.get('manifest_path', '')}")
        self.log(f"  Main output folder: {emit_result.get('output_dir', '')}")
        if dbf_result:
            self.log(f"  UAT DBF folder: {dbf_result.get('dbf_dir', '')} (status={dbf_result.get('status')})")
        self.log("=" * 60)

    def _quikisrr_emit_script_path(self):
        return os.path.normpath(os.path.join(self._repo_root(), QUIKISRR_EMIT_RUNNER))

    def _invoke_quikisrr_emit(self):
        script = self._quikisrr_emit_script_path()
        if not os.path.isfile(script):
            self.log(f"QUIKISRR ERROR: emit script not found: {script}")
            return {"status": "FAILED", "error": "script not found"}
        cmd = [sys.executable, script]
        self.log("QUIKISRR EMIT (Issue #34 PR-7): launching isolated subprocess...")
        self.log(f"  Script: {script}")
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=QUIKISRR_EMIT_RUNNER_TIMEOUT,
                cwd=self._repo_root(),
            )
            stdout_text = proc.stdout or ""
            stderr_text = proc.stderr or ""
            self._log_subprocess_stream("quikisrr-stdout", stdout_text)
            self._log_subprocess_stream("quikisrr-stderr", stderr_text)
            summary = {}
            start = stdout_text.find("{")
            end = stdout_text.rfind("}")
            if start >= 0 and end > start:
                try:
                    summary = json.loads(stdout_text[start:end + 1])
                except json.JSONDecodeError:
                    pass
            status = "SUCCESS" if proc.returncode == 0 else "FAILED"
            return {"status": status, "return_code": proc.returncode, "summary": summary}
        except subprocess.TimeoutExpired:
            self.log("QUIKISRR ERROR: subprocess timeout")
            return {"status": "TIMEOUT"}
        except Exception as exc:
            self.log(f"QUIKISRR ERROR: {exc}")
            return {"status": "FAILED", "error": str(exc)}

    def _execute_batch_quikisrr_finale(self, batch_claims_result=None):
        if not self._batch_include_quikisrr_enabled():
            self.log("BATCH QUIKISRR (Issue #34): not enabled (set QLA_ENABLE_QUIKISRR_EMIT=1 in UAT mode).")
            return None
        if not batch_claims_result or not batch_claims_result.get("emit_result"):
            self.log("BATCH QUIKISRR (Issue #34): skipped — UAT claims emit did not complete.")
            return None
        self.log("=" * 60)
        self.log("BATCH QUIKISRR FINALE (Issue #34 PR-7 — after UAT claims emit)")
        result = self._invoke_quikisrr_emit()
        self._last_quikisrr_result = result
        summary = result.get("summary") or {}
        emitted = summary.get("emitted") or {}
        self.log(
            f"QUIKISRR (batch finale): status={result.get('status', '?')} "
            f"events={emitted.get('rows', '?')} policies={emitted.get('policies', '?')}"
        )
        for name, info in (summary.get("outputs") or {}).items():
            if isinstance(info, dict):
                self.log(f"  {name}: {info.get('rows', '?')} rows (appended={info.get('appended', '')})")
        self.log("=" * 60)
        return result

    def _execute_batch_quikiswl_seed(self):
        """Issue #124 — QuikIswl month-0 seeds from converted quikmstr/quikridr."""
        if not self._batch_include_quikiswl_enabled():
            self.log("BATCH QUIKISWL (Issue #124): skipped (QLA_ENABLE_QUIKISWL_EMIT=0).")
            return None
        self.log("=" * 60)
        self.log("BATCH QUIKISWL SEED (Issue #124 — month-0 QuikIswl)")
        try:
            from qla_core.quikiswl_loader import emit_quikiswl_seeds

            out_dir = self._migration_output_dir()
            summary = emit_quikiswl_seeds(out_dir)
            self._last_quikiswl_result = summary
            self.log(
                f"QUIKISWL (batch): status={summary.get('status', '?')} "
                f"rows={summary.get('rows', '?')} output={summary.get('output', '')}"
            )
            if summary.get("by_plan"):
                self.log(f"  by_plan: {summary.get('by_plan')}")
            self.log("=" * 60)
            return summary
        except Exception as exc:
            self.log(f"QUIKISWL ERROR: {exc}")
            self.log("=" * 60)
            return {"status": "FAILED", "error": str(exc)}

    def on_table_select(self, event=None):
        table = self.table_var.get()
        if not table: return

        if self._is_claims_table(table):
            cfg = self.CLAIMS_ORCHESTRATION
            claims_root = self._claims_analysis_root()
            uat_src = self._claims_uat_source_path(table)
            out_dir = self._migration_output_dir()
            if not os.path.isdir(out_dir):
                out_dir = os.path.join(cfg["app_base_dir"], "output")
            staging_dir = os.path.join(out_dir, cfg["staging_subdir"])
            rb_path = os.path.join(claims_root, "config", "app_claims_uat_orchestration_rules.json")
            self.path_vars["Rule"][0].set(rb_path if os.path.isfile(rb_path) else "")
            self.path_vars["Src"][0].set(uat_src if os.path.isfile(uat_src) else "")
            self.path_vars["Trans"][0].set("")
            self.path_vars["CW"][0].set("")
            self.path_vars["Rel"][0].set("")
            self.path_vars["Out"][0].set(out_dir)
            self._ui_sync_path_display()
            self.log(f"System UI: Claims UAT orchestration paths for {table.upper()} (RUN_MODE={cfg['run_mode']})")
            self.log(f"  Staging: {staging_dir} | Main output emit: {out_dir}")
            return

        src_dir = self._migration_source_dir()
        out_dir = self._migration_output_dir()
        map_dir = self._migration_mapping_dir()
        cfg_dir = self._migration_configs_dir()

        rb_path = self._first_existing_file(
            os.path.join(cfg_dir, f"Sync_Rulebook_{table}.csv"),
            self._find_migration_file(f"Sync_Rulebook_{table}.csv", search_dirs=[cfg_dir]),
        )
        src_path = self._resolve_table_source_path(table, src_dir)
        if not src_path:
            legacy_hint = expected_legacy_filename(table)
            src_path = self._first_existing_file(
                self._find_migration_file(legacy_hint, search_dirs=[src_dir], exclude_output_paths=True),
            )
        trans_path = self._first_existing_file(
            os.path.join(map_dir, "Master_Value_Translation.csv"),
            self._find_migration_file("Master_Value_Translation.csv", search_dirs=[map_dir]),
        )
        cw_path = self._first_existing_file(
            os.path.join(map_dir, "Master_Crosswalk.csv"),
            self._find_migration_file("Master_Crosswalk.csv", search_dirs=[map_dir]),
        )
        rel_path = self._first_existing_file(
            os.path.join(out_dir, "quikclid.csv"),
            self._find_migration_file("quikclid.csv", search_dirs=[out_dir]),
        )

        if not os.path.isdir(out_dir):
            out_dir = os.path.join(self._app_base_dir(), "output")

        self.path_vars["Rule"][0].set(rb_path)
        self.path_vars["Src"][0].set(src_path)
        self.path_vars["Trans"][0].set(trans_path)
        self.path_vars["CW"][0].set(cw_path)
        self.path_vars["Rel"][0].set(rel_path)
        self.path_vars["Out"][0].set(out_dir)
        self._ui_sync_path_display()

        self.log(f"System UI: Auto-populated paths for {table.upper()} (QLA_Migration preferred)")
        self.log(f"  Source dir: {src_dir}")
        self.log(f"  Source file: {src_path or '(not found)'}")
        self.log(f"  Output dir: {out_dir}")

    def browse(self, var, mode, key):
        path = filedialog.askdirectory() if mode == "folder" else filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if path:
            var.set(path)
            self._ui_sync_path_display(key)
            if key == "Src":
                filename = os.path.basename(path).lower()
                for k in self.TABLE_SCHEMAS.keys():
                    if k in filename:
                        self.table_var.set(k)
                        break
            self.refresh_table_list(path)

    def refresh_table_list(self, path):
        directory = path if os.path.isdir(path) else os.path.dirname(path)
        if os.path.exists(directory):
            csv_files = sorted([os.path.splitext(f)[0] for f in os.listdir(directory) if f.lower().endswith('.csv') and f.lower().startswith('quik')])
            self.table_dropdown['values'] = csv_files

    def create_snapshot(self):
        target_zip = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("Zip Files", "*.zip")])
        if target_zip:
            with zipfile.ZipFile(target_zip, 'w') as zipf:
                zipf.write(__file__, arcname=os.path.basename(__file__))
            self.log(f"Backup Created: {os.path.basename(target_zip)}")

    def normalize(self, val):
        if pd.isna(val) or str(val).strip().lower() in ['nan', 'none', '']: return ""
        s = str(val).strip().upper()
        if s.endswith('.0'): s = s[:-2]
        return s

    def _format_qladmin_mpolicy(self, val):
        return format_qladmin_mpolicy(val)

    def _derive_rna_policy_from_identifying_alpha(self, src_row, cw_map):
        """Derive LifePRO policy from RNA IDENTIFYING_ALPHA when POLICY_NUMBER is blank."""
        raw = self.normalize(src_row.get("IDENTIFYING_ALPHA", ""))
        if not raw:
            return ""

        candidates = []
        if raw.startswith("03") and len(raw) > 2:
            candidates.append(raw[2:])
        candidates.append(raw)

        for candidate in candidates:
            if candidate in cw_map:
                return candidate
        return ""

    def extract_day(self, date_str):
        d = re.sub(r'[^0-9/]', '', str(date_str))
        if len(d) == 8: return d[-2:]
        if '/' in d:
            parts = d.split('/')
            if len(parts) >= 2: return parts[1].zfill(2)
        return ""

    def _parse_conversion_date(self, raw):
        """Parse LifePRO/QLA date values to datetime.date for duration math."""
        cleaned = re.sub(r'[^0-9/]', '', str(raw).strip())
        for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d"):
            try:
                return datetime.strptime(cleaned[:10], fmt).date()
            except ValueError:
                continue
        digits = re.sub(r'[^0-9]', '', str(raw).strip())
        if len(digits) == 8 and int(digits[:4]) >= 1900:
            try:
                return datetime(int(digits[:4]), int(digits[4:6]), int(digits[6:8])).date()
            except ValueError:
                return None
        return None

    def _compute_quikridr_mlastann(self, issue_date_raw, valuation_date=None):
        """
        Current policy year for QUIKRIDR.MLASTANN.
        Issue source: PPBEN.ISSUE_DATE (converted to MEFFDATE).
        Valuation source: conversion run date (datetime.now().date()).
        Methodology: valuation_year - issue_year (calendar-year duration).
        """
        val = valuation_date or datetime.now().date()
        issue = self._parse_conversion_date(issue_date_raw)
        if not issue or issue > val:
            return ""
        duration = val.year - issue.year
        return str(duration) if duration >= 0 else ""

    def _apply_quikridr_mlastann(self, row_data, src_row, valuation_date):
        issue_raw = row_data.get("MEFFDATE") or src_row.get("ISSUE_DATE", "")
        row_data["MLASTANN"] = self._compute_quikridr_mlastann(issue_raw, valuation_date)

    def _normalize_yyyymmdd_date(self, raw):
        """Return 8-digit YYYYMMDD when value is a valid calendar date, else blank."""
        digits = re.sub(r'[^0-9]', '', str(raw).strip())
        if len(digits) != 8 or digits < "19000101":
            return ""
        try:
            datetime(int(digits[:4]), int(digits[4:6]), int(digits[6:8]))
            return digits
        except ValueError:
            return ""

    def _derive_mphdob_from_issue_age(self, issue_raw, age_raw):
        """Derive DOB as issue date minus issue age (same month/day)."""
        issue = self._parse_conversion_date(issue_raw)
        if not issue:
            return ""
        try:
            age = int(re.sub(r'[^0-9]', '', str(age_raw).strip() or "0"))
        except ValueError:
            return ""
        if age <= 0 or age > 120:
            return ""
        birth_year = issue.year - age
        if birth_year < 1900:
            return ""
        try:
            datetime(birth_year, issue.month, issue.day)
            return f"{birth_year:04d}{issue.month:02d}{issue.day:02d}"
        except ValueError:
            return ""

    def _resolve_quikridr_mphdob(self, row_data, src_row, rel_name_cache):
        """
        Harden QUIKRIDR.MPHDOB against corrupt LifePRO dates (e.g. 19291131).
        Priority: valid PPBEN value -> RNA by MRIDRID -> derive from issue+age.
        """
        original = self.normalize(row_data.get("MPHDOB", ""))
        current = self._normalize_yyyymmdd_date(row_data.get("MPHDOB", ""))
        if current:
            row_data["MPHDOB"] = current
            return False

        rel_id = self.normalize(row_data.get("MRIDRID", ""))
        if rel_id and rel_name_cache and rel_id in rel_name_cache:
            rna = rel_name_cache[rel_id]
            for key in ("DATE_OF_BIRTH", "BIRTH_DATE", "MDOB"):
                candidate = self._normalize_yyyymmdd_date(rna.get(key, ""))
                if candidate:
                    row_data["MPHDOB"] = candidate
                    if original and original != candidate:
                        self.log(
                            f"QUIKRIDR MPHDOB FIX: MPOLICY={row_data.get('MPOLICY', '')} "
                            f"MRIDRID={rel_id} {original} -> {candidate} (RNA {key})"
                        )
                    return True

        derived = self._derive_mphdob_from_issue_age(
            row_data.get("MEFFDATE") or src_row.get("ISSUE_DATE", ""),
            row_data.get("MAGE") or src_row.get("ISSUE_AGE", ""),
        )
        if derived:
            row_data["MPHDOB"] = derived
            if original and original != derived:
                self.log(
                    f"QUIKRIDR MPHDOB FIX: MPOLICY={row_data.get('MPOLICY', '')} "
                    f"MRIDRID={rel_id} {original} -> {derived} (derived issue-age)"
                )
            return True

        row_data["MPHDOB"] = ""
        if original:
            self.log(
                f"QUIKRIDR MPHDOB WARNING: MPOLICY={row_data.get('MPOLICY', '')} "
                f"MRIDRID={rel_id} could not resolve invalid DOB {original}"
            )
        return bool(original)

    def start_thread(self, batch):
        if not self.is_running:
            self.is_running = True
            self.start_time = time.time()
            threading.Thread(target=self.update_timer, daemon=True).start()
            threading.Thread(target=self.process_data, args=(batch,), daemon=True).start()

    def update_timer(self):
        while self.is_running:
            self.lbl_timer.config(text=f"Elapsed: {RL.fmt_elapsed(time.time() - self.start_time)}")
            time.sleep(1)

    # ------------------------------------------------------------------
    # Staged run progress (presentation only — never affects output data)
    # ------------------------------------------------------------------
    def _error_logs_root(self):
        return os.path.normpath(os.path.join(self._migration_root(), "Error_Logs"))

    def _reports_dir(self):
        return os.path.normpath(os.path.join(self._migration_root(), "Reports"))

    def _logs_dir(self):
        """Batch / migration text logs (not QLAdmin table CSVs)."""
        path = os.path.normpath(os.path.join(self._migration_root(), "Logs"))
        os.makedirs(path, exist_ok=True)
        return path

    def _issue45_usable_bank_account(self, acct_raw):
        """Issue #45: PPPAC fallback account usability (>=4 digits, not masked/zero)."""
        raw = str(acct_raw or "").strip()
        if not raw or raw.lower() in ("nan", "none", ""):
            return ""
        if re.search(r"[xX*]{2,}|REDACT|MASK|HIDDEN|XXXX", raw, re.I):
            return ""
        acct_d = re.sub(r"\D", "", raw)
        if not acct_d or set(acct_d) <= {"0"} or len(acct_d) < 4:
            return ""
        if acct_d in ("1234", "123456", "123456789", "0000", "1111", "9999", "999999999"):
            return ""
        return re.sub(r"\s+", "", raw)

    def _issue75_aba_checksum_ok(self, aba_digits):
        """Issue #75: ABA routing check-digit (3-7-1 weighted mod 10)."""
        a = str(aba_digits or "")
        if len(a) != 9 or not a.isdigit() or set(a) == {"0"}:
            return False
        d = [int(x) for x in a]
        return (3 * (d[0] + d[3] + d[6]) + 7 * (d[1] + d[4] + d[7]) + (d[2] + d[5] + d[8])) % 10 == 0

    def _issue45_lookup_aba_for_account(self, acct_digits, aba_lookup):
        """Issue #45 / #21H / #75: resolve checksum-valid 9-digit ABA from PPCOM lookup."""
        if not acct_digits or not aba_lookup:
            return ""
        for lk_key in (acct_digits, acct_digits.lstrip("0") or "0", acct_digits.zfill(17)):
            full_aba = aba_lookup.get(lk_key)
            if not full_aba:
                continue
            aba = str(full_aba).strip()
            if aba.endswith(".0"):
                aba = aba[:-2]
            aba_d = re.sub(r"\D", "", aba)
            if self._issue75_aba_checksum_ok(aba_d):
                return aba_d
        return ""

    def _issue75_usable_acct_digits(self, acct_raw):
        """Issue #75: digits-only account half for QLA-safe MBANKNO.

        Preserves leading zeros from source/PPCOM (do not strip or zfill accounts).
        """
        usable = self._issue45_usable_bank_account(acct_raw)
        if not usable:
            return ""
        acct_d = re.sub(r"\D", "", usable)
        if not acct_d or len(acct_d) < 4:
            return ""
        return acct_d

    def _issue75_usable_aba_digits(self, aba_raw, acct_digits=None, aba_lookup=None):
        """Issue #75: emit only checksum-valid 9-digit ABA — PPCOM lookup first, else raw 9."""
        if acct_digits and aba_lookup:
            lk = self._issue45_lookup_aba_for_account(acct_digits, aba_lookup)
            if lk:
                return lk
        aba = str(aba_raw or "").strip()
        if aba.endswith(".0"):
            aba = aba[:-2]
        aba_d = re.sub(r"\D", "", aba)
        if self._issue75_aba_checksum_ok(aba_d):
            return aba_d
        return ""

    def _issue75_build_mbankno(self, aba_digits, acct_digits):
        """Issue #75: QLA Bank Acct = 9-digit routing / digits-only account (zeros preserved)."""
        if not aba_digits or not acct_digits:
            return ""
        if not self._issue75_aba_checksum_ok(aba_digits):
            return ""
        return f"{aba_digits}/{acct_digits}"

    def _issue75_mbankno_is_ql_safe(self, mbankno):
        """Issue #75: routing validated in QLA — single slash, 9-digit ABA, digits-only account."""
        mb = str(mbankno or "").strip()
        if not mb or mb.count("/") != 1:
            return False
        aba, acct = mb.split("/", 1)
        aba_d = re.sub(r"\D", "", aba)
        acct_d = re.sub(r"\D", "", acct)
        if not self._issue75_aba_checksum_ok(aba_d) or not acct_d or len(acct_d) < 4:
            return False
        if re.search(r"[^0-9]", acct or ""):
            return False
        return True

    def _apply_issue45_bank_draft_gate(self, row_data, src_row, exceptions):
        """Issue #45/#75: MBILLFRM=2 without QLA-safe bank account+ABA → blank MBANKNO + exception.

        PPACH primary; PPPAC fallback when PPACH account missing. Does not change MBILLFRM.
        """
        if exceptions is None:
            return
        mbillfrm = str(row_data.get("MBILLFRM", "")).strip()
        if mbillfrm != "2":
            return
        if self._issue75_mbankno_is_ql_safe(row_data.get("MBANKNO", "")):
            return
        raw_pol = self.normalize(src_row.get("POLICY_NUMBER", src_row.get("MPOLICY", "")))
        meta = getattr(self, "_ppach_acct_meta", {}).get(raw_pol, {}) or {}
        pppac_only = getattr(self, "_pppac_acct_only_meta", {}).get(raw_pol, {}) or {}
        acct = str(meta.get("account", "")).strip()
        aba = str(meta.get("aba", "")).strip()
        acct_digits = re.sub(r"\D", "", acct) if acct and acct.lower() not in ("nan", "none", "") else ""
        aba_digits = re.sub(r"\D", "", aba) if aba and aba.lower() not in ("nan", "none", "") else ""
        row_data["MBANKNO"] = ""
        pppac_acct = str(pppac_only.get("account", "")).strip()
        if acct_digits and aba_digits and len(aba_digits) != 9:
            exc_reason = "ABA_NOT_9"
            exc_detail = "MBILLFRM=2; account present but routing is not 9 digits"
            bank_source = str(meta.get("bank_source", "")).strip()
            aba_source = str(meta.get("aba_source", "")).strip()
        elif acct_digits and not aba_digits:
            exc_reason = "MISSING_ROUTING"
            exc_detail = "MBILLFRM=2; account present but ABA unresolved"
            bank_source = str(meta.get("bank_source", "PPPAC" if pppac_acct else "")).strip()
            aba_source = str(meta.get("aba_source", "")).strip()
        elif pppac_acct and pppac_acct.lower() not in ("nan", "none", ""):
            exc_reason = "MISSING_ROUTING"
            exc_detail = "MBILLFRM=2; PPPAC account present but ABA unresolved"
            bank_source = "PPPAC"
            aba_source = ""
        elif str(row_data.get("MBANKNO", "")).strip():
            exc_reason = "ACCT_INVALID"
            exc_detail = "MBILLFRM=2; MBANKNO not QLA-safe (punctuation or multi-slash)"
            bank_source = str(meta.get("bank_source", "")).strip()
            aba_source = str(meta.get("aba_source", "")).strip()
        else:
            exc_reason = "MISSING_BANK_ACCOUNT"
            exc_detail = "MBILLFRM=2 but no usable account in PPACH or PPPAC"
            bank_source = ""
            aba_source = ""
        exceptions.append({
            "MPOLICY": str(row_data.get("MPOLICY", "")).strip(),
            "SOURCE_POLICY": raw_pol,
            "MBILLFRM": mbillfrm,
            "MBANKNO_EMITTED": "",
            "PPACH_ACCOUNT": acct if acct.lower() not in ("nan", "none") else "",
            "PPACH_ABA": aba if aba.lower() not in ("nan", "none") else "",
            "PPPAC_ACCOUNT": pppac_acct if pppac_acct.lower() not in ("nan", "none") else "",
            "ABA_SOURCE": str(meta.get("aba_source", aba_source)).strip(),
            "BANK_SOURCE": str(meta.get("bank_source", bank_source)).strip(),
            "EXCEPTION_REASON": exc_reason,
            "EXCEPTION_DETAIL": exc_detail,
        })

    def _check_issue72_mnfopt_status(self, row_data, exceptions):
        """Issue #72 → #108G: ETI/RPU status vs NFO election — report, do not force.

        Robert 2026-07-25: the election should come from the crosswalk and any
        disagreement with the policy status should be raised for source review. The
        prior force overwrote the source election, which both destroyed the value and
        guaranteed the mismatch check could never fire.
        """
        st = self.normalize(row_data.get("MSTATUS", ""))
        expected = {"44": "2", "45": "3"}.get(st)
        if expected is None or exceptions is None:
            return
        actual = self.normalize(row_data.get("MNFOPT", ""))
        if actual == expected:
            return
        exceptions.append({
            "MPOLICY": self.normalize(row_data.get("MPOLICY", "")),
            "MSTATUS": st,
            "NFO_TYPE": "ETI" if st == "44" else "RPU",
            "MNFOPT_EMITTED": actual,
            "MNFOPT_EXPECTED": expected,
            "EXCEPTION_REASON": (
                "NFO election missing" if actual in ("", "0")
                else "NFO election disagrees with policy status"
            ),
        })

    def _write_issue72_mnfopt_status_exceptions(self, exceptions):
        """Write Issue #72 NFO election vs status review CSV under Reports/ (header always)."""
        cols = [
            "MPOLICY",
            "MSTATUS",
            "NFO_TYPE",
            "MNFOPT_EMITTED",
            "MNFOPT_EXPECTED",
            "EXCEPTION_REASON",
        ]
        reports = self._reports_dir()
        os.makedirs(reports, exist_ok=True)
        path = os.path.normpath(os.path.join(reports, "nfo_election_status_mismatch.csv"))
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            writer.writeheader()
            for row in exceptions or []:
                writer.writerow({c: row.get(c, "") for c in cols})
        self.log(
            f"Issue #72: NFO election vs status mismatches: {len(exceptions or [])} -> {path}"
        )
        return path

    def _apply_quikmstr_v5796_defaults(self, row_data):
        """v57.96: MBILLTO 0/blank -> MPAIDTO; MORIGBILL/MORIGMODE default to final bill form/mode."""
        billto = str(row_data.get("MBILLTO", "")).strip()
        if billto in ("", "0"):
            paidto = str(row_data.get("MPAIDTO", "")).strip()
            if paidto and paidto != "0":
                row_data["MBILLTO"] = paidto
                self._v5796_mbillto_fix_count = (
                    getattr(self, "_v5796_mbillto_fix_count", 0) + 1
                )
        if not str(row_data.get("MORIGBILL", "")).strip():
            row_data["MORIGBILL"] = str(row_data.get("MBILLFRM", "")).strip()
        if not str(row_data.get("MORIGMODE", "")).strip():
            row_data["MORIGMODE"] = str(row_data.get("MMODE", "")).strip()

    def _apply_quikridr_v5796_defaults(self, row_data, nfo_phase1=False):
        """v57.96: blank MSAVE* mirror final live fields; MRRULE default A (post-translation,
        because a rulebook default would hit the bare A→22 status translation).

        Issue #108A: on ETI/RPU phase 1 the live fields are already the post-nonforfeiture
        values, so mirroring them would make a QLAdmin reinstatement restore the policy
        back into ETI/RPU. The save fields hold the pre-NFO snapshot, which conversion does
        not have, so they are left blank.
        """
        if not nfo_phase1:
            for save_f, live_f in (
                ("MSAVEAGE", "MAGE"),
                ("MSAVEUNIT", "MUNIT"),
                ("MSAVEVPU", "MVPU"),
                ("MSAVEPREM", "MPREM"),
                ("MSAVESTAT", "MPHSTAT"),
            ):
                if not str(row_data.get(save_f, "")).strip():
                    row_data[save_f] = str(row_data.get(live_f, "")).strip()
        if not str(row_data.get("MRRULE", "")).strip():
            row_data["MRRULE"] = "A"

    def _apply_issue76_eti_rpu_phase1_payup_mlastann(self, row_data, qm_status, qm_paidto, valuation_date=None):
        """Issue #76: ETI/RPU phase-1 pay-up = paid-to; duration = completed NFO years.

        Issue #108B: duration is measured to the NFO anniversary against the batch
        valuation date. Calendar-year subtraction ran a year high whenever the
        anniversary had not yet occurred, and datetime.now() made MLASTANN differ
        between reruns of the same batch. MLASTANN drives QLAdmin CV interpolation.
        """
        st = self.normalize(qm_status)
        if st not in ("44", "45"):
            return
        paidto = self._normalize_yyyymmdd_date(qm_paidto)
        if not paidto:
            return
        nfo = self._parse_conversion_date(paidto)
        if not nfo:
            return
        before_payup = self.normalize(row_data.get("MPAYUP", ""))
        before_mlast = self.normalize(row_data.get("MLASTANN", ""))
        val = valuation_date or datetime.now().date()
        duration = val.year - nfo.year - ((val.month, val.day) < (nfo.month, nfo.day))
        new_mlast = str(duration if duration >= 0 else 0)
        row_data["MPAYUP"] = paidto
        row_data["MLASTANN"] = new_mlast
        if before_payup != paidto or before_mlast != new_mlast:
            self._issue76_payup_adjust_count = (
                getattr(self, "_issue76_payup_adjust_count", 0) + 1
            )

    def _apply_issue108_nfo_phase1_fields(self, row_data, qm_status, qm_paidto):
        """Issue #108: ETI/RPU phase-1 age and premium per QLAdmin_ETI_RPU spec.

        MAGE becomes the attained age at the date of nonforfeiture (paid-to). QLAdmin
        rebuilds NFO cash values as q(x+t) where x is the age at nonforfeiture, so
        emitting the issue age evaluates mortality decades too young.

        MPREM is zeroed on ETI only — the specification does not zero it for RPU.

        Caller must invoke this after MPHDOB resolution: _derive_mphdob_from_issue_age
        reads MAGE, so writing the attained age first would corrupt MPHDOB.
        """
        st = self.normalize(qm_status)
        if st not in ("44", "45"):
            return
        nfo = self._parse_conversion_date(self._normalize_yyyymmdd_date(qm_paidto))
        dob = self._parse_conversion_date(row_data.get("MPHDOB", ""))
        if nfo and dob and nfo >= dob:
            attained = nfo.year - dob.year - ((nfo.month, nfo.day) < (dob.month, dob.day))
            if attained >= 0:
                before_age = self.normalize(row_data.get("MAGE", ""))
                new_age = str(attained).zfill(max(len(before_age), 2))
                row_data["MAGE"] = new_age
                if before_age != new_age:
                    self._issue108_mage_count = (
                        getattr(self, "_issue108_mage_count", 0) + 1
                    )
        if st == "44":
            before_prem = self.normalize(row_data.get("MPREM", ""))
            row_data["MPREM"] = "0"
            if before_prem not in ("", "0"):
                self._issue108_eti_mprem_count = (
                    getattr(self, "_issue108_eti_mprem_count", 0) + 1
                )

    def _write_bank_draft_account_exceptions(self, exceptions):
        """Write Issue #45 client-review exception CSV under Reports/ (header always)."""
        cols = [
            "MPOLICY",
            "SOURCE_POLICY",
            "MBILLFRM",
            "MBANKNO_EMITTED",
            "PPACH_ACCOUNT",
            "PPACH_ABA",
            "PPPAC_ACCOUNT",
            "ABA_SOURCE",
            "BANK_SOURCE",
            "EXCEPTION_REASON",
            "EXCEPTION_DETAIL",
        ]
        reports = self._reports_dir()
        os.makedirs(reports, exist_ok=True)
        path = os.path.normpath(os.path.join(reports, "bank_draft_account_exceptions.csv"))
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            writer.writeheader()
            for row in exceptions or []:
                writer.writerow({c: row.get(c, "") for c in cols})
        self.log(
            f"Issue 45: bank draft account exceptions: {len(exceptions or [])} -> {path}"
        )
        return path

    def _new_run_error_log(self):
        self._run_error_log = RL.RunErrorLog(self._error_logs_root())
        return self._run_error_log

    def start_run_progress(self, run_type):
        self._progress_plan = RL.stage_plan(run_type)
        self._progress_run_type = run_type
        self._run_start_time = time.time()
        self._ui_run_state = "Running"
        self._ui_update_status_strip()
        self.update_progress(0, "Stage 0 — Ready")
        if hasattr(self, "lbl_stage_detail"):
            self.lbl_stage_detail.config(text="")

    def update_run_progress(self, stage_number, stage_name=None, detail=None):
        plan = self._progress_plan or RL.stage_plan("full_batch")
        total = len(plan)
        pct = None
        name = stage_name
        for (no, nm, p) in plan:
            if no == stage_number:
                pct = p
                name = stage_name or nm
                break
        label = f"Stage {stage_number} of {total} — {name}" if name else f"Stage {stage_number} of {total}"
        self.update_progress(pct, label)
        if hasattr(self, "lbl_stage_detail"):
            self.lbl_stage_detail.config(text=detail or "")
        self.log(label + (f" — {detail}" if detail else ""))

    def complete_run_progress(self, message=None):
        msg = message or "Complete — CSV outputs written to QLA_Migration\\Output"
        self.update_progress(100, msg, state="success")
        if hasattr(self, "lbl_stage_detail"):
            self.lbl_stage_detail.config(text="")
        self._ui_record_run_timestamp("Success")

    def fail_run_progress(self, stage_name, error_message, error_log_folder=None):
        msg = f"Failed at {stage_name}. See logs."
        if error_log_folder:
            msg = f"Failed at {stage_name}. See {error_log_folder}"
        self.update_progress(None, msg, state="error")
        if hasattr(self, "lbl_stage_detail"):
            self.lbl_stage_detail.config(text=str(error_message)[:160])
        self.log(f"!!! {msg}")
        self._ui_record_run_timestamp("Failed")

    def _run_post_conversion_governance(self, error_log=None):
        """Run QLAdmin Data Governance after full batch (report-only; never blocks emit)."""
        if os.environ.get("QLA_SKIP_GOVERNANCE_AUDIT", "").strip() == "1":
            self.log("DATA GOVERNANCE: skipped (QLA_SKIP_GOVERNANCE_AUDIT=1)")
            return {"status": "SKIPPED", "failed": 0, "errors": 0, "total": 0}
        try:
            # Post-batch always audits the conversion Output folder (CSV emit).
            out_dir = ""
            if hasattr(self, "path_vars"):
                out_dir = self.path_vars["Out"][0].get().strip()
            if not out_dir or not os.path.isdir(out_dir):
                out_dir = self._migration_output_dir()
            summary = self._execute_governance_audit(
                open_report=False, show_dialog=False, data_dir=out_dir,
            )
            if error_log and (summary.get("failed") or summary.get("errors")):
                error_log.write_warnings([
                    ("WARN", "governance", "data_governance",
                     f"Failed={summary.get('failed')} Errors={summary.get('errors')} "
                     f"see {summary.get('report_dir', 'Reports/data_governance')}"),
                ])
            return summary
        except Exception as exc:
            self.log(f"DATA GOVERNANCE: non-fatal failure — {exc}")
            if error_log:
                error_log.write_warnings([("WARN", "governance", "data_governance", str(exc))])
            return {"status": "ERROR", "failed": 0, "errors": 0, "total": 0, "error": str(exc)}

    def _governance_ui_progress(self, event, **kwargs):
        """Drive progress bar / stage detail during an on-demand governance run."""
        try:
            if event == "load":
                self.update_run_progress(2, detail="Loading QuikComp / QuikAgts / QuikMstr")
            elif event == "check":
                idx = int(kwargs.get("index", 0))
                total = max(int(kwargs.get("total", 1)), 1)
                name = str(kwargs.get("name") or "rule")
                pct = 20 + int(70 * ((idx + 1) / total))
                plan = self._progress_plan or RL.stage_plan("governance_audit")
                stage_total = len(plan)
                self.update_progress(
                    pct,
                    f"Stage 3 of {stage_total} — Running governance rule checks",
                )
                if hasattr(self, "lbl_stage_detail"):
                    self.lbl_stage_detail.config(
                        text=f"Rule {idx + 1}/{total}: {name}"
                    )
                if hasattr(self, "root"):
                    self.root.update_idletasks()
            elif event == "report":
                self.update_run_progress(4, detail="Writing governance CSV / markdown reports")
            elif event == "done":
                self.update_run_progress(
                    5,
                    detail=(
                        f"Status={kwargs.get('overall_status', '?')} "
                        f"findings={kwargs.get('total_findings', '?')}"
                    ),
                )
        except Exception:
            pass

    def _resolve_governance_data_dir(self, explicit=None):
        """Resolve folder of Quik*.dbf / Quik*.csv tables for an on-demand governance run."""
        candidates = []
        if explicit:
            candidates.append(str(explicit).strip())
        if hasattr(self, "path_vars") and "GovData" in self.path_vars:
            candidates.append(self.path_vars["GovData"][0].get().strip())
        env_gov = os.environ.get("QLA_GOVERNANCE_DATA_DIR", "").strip()
        if env_gov:
            candidates.append(env_gov)
        if hasattr(self, "path_vars") and "Out" in self.path_vars:
            candidates.append(self.path_vars["Out"][0].get().strip())
        candidates.append(self._migration_output_dir())
        for path in candidates:
            if path and os.path.isdir(path):
                return os.path.normpath(path)
        return ""

    def _prompt_governance_data_folder(self):
        """Ask user to pick a CSV/DBF data region; store on GovData path field."""
        path = filedialog.askdirectory(
            title="Select Governance Data Folder (Quik*.csv or Quik*.dbf)",
        )
        if not path:
            return ""
        path = os.path.normpath(path)
        if hasattr(self, "path_vars") and "GovData" in self.path_vars:
            self.path_vars["GovData"][0].set(path)
            self._ui_sync_path_display("GovData")
        return path

    def _execute_governance_audit(
        self, open_report=True, show_dialog=True, with_ui_progress=False, data_dir=None,
    ):
        """Shared QLAdmin Data Governance runner for UI and post-batch. Returns summary dict."""
        data_region = self._resolve_governance_data_dir(data_dir)
        if not data_region:
            raise FileNotFoundError(
                "Governance data folder not found. Browse to a folder of Quik*.csv or Quik*.dbf files."
            )

        repo = self._repo_root()
        if repo not in sys.path:
            sys.path.insert(0, repo)
        from data_governance import run_data_governance

        report_dir = os.path.normpath(os.path.join(self._reports_dir(), "data_governance"))
        os.makedirs(report_dir, exist_ok=True)

        self.log("DATA GOVERNANCE: starting QLAdmin Data Governance (read-only)...")
        self.log(f"  Data folder: {data_region}")
        if with_ui_progress:
            self.update_run_progress(1, detail="Preparing QLAdmin Data Governance")
        report = run_data_governance(
            data_dir=data_region,
            output_dir=report_dir,
            write_reports=True,
            progress_callback=self._governance_ui_progress if with_ui_progress else None,
        )
        self._last_governance_report = report
        failed = int(report.failed_count or 0)
        errors = int(report.error_count or 0)
        incomplete = int(getattr(report, "checks_incomplete_count", 0) or 0)
        business_result = getattr(report, "business_overall_result", "") or report.overall_status
        what_checked = getattr(report, "what_was_checked_path", "") or ""
        items_csv = getattr(report, "items_needing_attention_path", "") or ""
        run_folder = getattr(report, "output_dir", "") or report_dir

        self.log("DATA GOVERNANCE COMPLETE:")
        self.log(f"  Overall result: {business_result}")
        self.log(
            f"  Records checked={report.records_evaluated} "
            f"Passed={report.passed_count} Problems={failed} "
            f"Incomplete checks={incomplete}"
        )
        self.log(f"  What Was Checked: {what_checked}")
        self.log(f"  Items Needing Attention: {items_csv}")

        summary = {
            "status": report.overall_status,
            "business_result": business_result,
            "failed": failed,
            "errors": errors,
            "passed": int(report.passed_count or 0),
            "total": failed + incomplete,
            "critical": failed,
            "high": 0,
            "report_dir": run_folder,
            "what_was_checked_path": what_checked,
            "items_needing_attention_path": items_csv,
            "results_csv_path": getattr(report, "results_csv_path", ""),
            "report_md_path": getattr(report, "report_md_path", ""),
            "findings_csv_path": getattr(report, "findings_csv_path", ""),
            "summary_csv_path": getattr(report, "summary_csv_path", ""),
            "clean": business_result == "Passed",
        }

        if show_dialog:
            msg = (
                f"Overall result: {business_result}\n"
                f"Problems found: {failed}\n"
                f"Checks that could not be completed: {incomplete}\n\n"
                f"What Was Checked:\n{what_checked}\n\n"
                f"Items Needing Attention:\n{items_csv}"
            )
            if business_result == "Passed":
                messagebox.showinfo("QLAdmin Data Governance", f"Passed.\n\n{msg}")
            else:
                messagebox.showwarning("QLAdmin Data Governance", msg)

        if open_report and what_checked and os.path.isfile(what_checked):
            try:
                os.startfile(what_checked)  # noqa: S606
            except OSError:
                pass

        self._ui_record_governance_timestamp()
        self._ui_update_status_strip()
        return summary

    def _publish_dbf_append_tool_input(self, out_dir=None):
        """Publish Append Tool package: safe CSVs to input; memo/claims DBFs to output.

        quikmemo / quikclms / quikclmp are excluded from Append Tool input so EXECUTE
        cannot blank MEMOTEXT. Claims CSVs are MSEQ-aligned, UAT DBFs regenerated,
        join-gated, then placed into Desktop\\DBF_Append_Tool\\output.
        """
        try:
            from qla_core.dbf_append_tool_package import (
                DbfAppendPackageError,
                finalize_dbf_append_tool_package,
            )

            src_dir = out_dir or (
                self.path_vars["Out"][0].get().strip() if hasattr(self, "path_vars") else ""
            ) or self._migration_output_dir()
            if not src_dir or not os.path.isdir(src_dir):
                return 0
            repo_root = os.path.normpath(
                getattr(self, "repo_root", None)
                or os.path.dirname(os.path.abspath(__file__))
            )
            # Root app.py lives at repo root; QLA_Migration/app.py needs parent.
            if os.path.basename(repo_root).lower() == "qla_migration":
                repo_root = os.path.dirname(repo_root)
            result = finalize_dbf_append_tool_package(
                src_dir,
                repo_root,
                append_input=DBF_APPEND_TOOL_INPUT,
                append_output=DBF_APPEND_TOOL_OUTPUT,
                publish_csvs=True,
            )
            csv_n = int((result.get("csv_publish") or {}).get("copied") or 0)
            skipped = (result.get("csv_publish") or {}).get("skipped") or []
            memo = result.get("quikmemo") or {}
            claims = result.get("claims") or {}
            align = (result.get("mseq_align") or {}).get("align") or {}
            self.log(
                f"DBF Append Tool: published {csv_n} CSV(s) → {DBF_APPEND_TOOL_INPUT} "
                f"(excluded memo/claims CSV: {', '.join(skipped) or 'none'})"
            )
            self.log(
                f"DBF Append Tool: payee MSEQ align changed={align.get('changed', 0)} "
                f"rows={align.get('rows', 0)}"
            )
            if memo.get("ok"):
                self.log(
                    f"DBF Append Tool: quikmemo.dbf+sidecar → {DBF_APPEND_TOOL_OUTPUT} "
                    f"rows={memo.get('dbf_rows')}"
                )
            if claims.get("ok"):
                gate = (result.get("append_claims_gate") or {})
                self.log(
                    f"DBF Append Tool: claims UAT DBF/DBT → {DBF_APPEND_TOOL_OUTPUT} "
                    f"clms={gate.get('clms_rows')} clmp={gate.get('clmp_rows')} "
                    f"c11={gate.get('mpolicy_c11')}"
                )
            self._last_dbf_append_package_ok = True
            return csv_n
        except DbfAppendPackageError as exc:
            self._last_dbf_append_package_ok = False
            self.log(f"DBF Append Tool: PACKAGE FAIL (blocking): {exc}")
            return -1
        except Exception as exc:
            self._last_dbf_append_package_ok = False
            self.log(f"DBF Append Tool: PACKAGE FAIL (blocking): {exc}")
            return -1

    def _launch_dbf_append_tool(self):
        """Open Desktop\\DBF_Append_Tool\\run_app.bat after any successful conversion.

        Called after single-table, product setup, rate-only, or full batch success.
        Launches the Append Tool GUI (non-blocking). Does not auto-click EXECUTE —
        paths are already defaulted to input/output. Disable with
        QLA_LAUNCH_DBF_APPEND_TOOL=0.
        """
        if getattr(self, "_last_dbf_append_package_ok", True) is False:
            self.log("DBF Append Tool: launch blocked — package gate failed")
            return False
        flag = os.environ.get("QLA_LAUNCH_DBF_APPEND_TOOL", "1").strip().lower()
        if flag in ("0", "false", "no", "off"):
            self.log("DBF Append Tool: launch skipped (QLA_LAUNCH_DBF_APPEND_TOOL=0)")
            return False
        bat = os.path.normpath(DBF_APPEND_TOOL_BAT)
        if not os.path.isfile(bat):
            self.log(f"DBF Append Tool: launch skipped — not found: {bat}")
            return False
        try:
            # Detached so conversion UI is not blocked waiting on the append tool.
            if os.name == "nt":
                os.startfile(bat)  # noqa: S606 — operator desktop launcher
            else:
                subprocess.Popen(["bash", bat], cwd=os.path.dirname(bat))
            self.log(f"DBF Append Tool: launched {bat}")
            return True
        except Exception as exc:
            self.log(f"DBF Append Tool: launch failed (non-fatal): {exc}")
            return False

    def _cut_journal_start(self, is_batch):
        """Start Wave 1 cut-completeness journal for full-batch runs only."""
        self._cut_journal = None
        self._last_cut_manifest = None
        self._cut_journal_required = bool(is_batch)
        self._cut_journal_start_error = None
        if not is_batch:
            return
        try:
            from qla_core.cut_completeness_manifest import CutRunJournal

            src_base = None
            rule_base = None
            try:
                src_input = self.path_vars["Src"][0].get()
                rule_input = self.path_vars["Rule"][0].get()
                src_base = self._resolve_batch_src_base(src_input) if src_input else None
                rule_base = self._resolve_batch_rule_base(rule_input) if rule_input else None
            except Exception:
                pass
            self._cut_journal = CutRunJournal.start(
                app_version=APP_VERSION,
                launched_app_path=os.path.abspath(__file__),
                run_mode=getattr(self, "RUN_MODE", os.environ.get("QLA_RUN_MODE", "")),
                locked_src_base=src_base,
                locked_rule_base=rule_base,
            )
            self.log("Cut Completeness: journal started (Wave 1 fail-closed gate)")
        except Exception as exc:
            self._cut_journal_start_error = str(exc)
            self._cut_journal = None
            self.log(f"Cut Completeness: journal start FAILED (fail-closed): {exc}")

    def _cut_record(self, table_id, status, **kwargs):
        journal = getattr(self, "_cut_journal", None)
        if journal is None:
            return
        try:
            extra = dict(kwargs.pop("extra", None) or {})
            if "output_dir" not in extra:
                try:
                    out_dir = self.path_vars["Out"][0].get().strip() or self._migration_output_dir()
                    if out_dir:
                        extra["output_dir"] = out_dir
                except Exception:
                    pass
            if extra:
                kwargs["extra"] = extra
            journal.record(table_id, status, **kwargs)
        except Exception as exc:
            self.log(f"Cut Completeness: journal record failed for {table_id}: {exc}")

    def _publish_cut_tv_parity_tables(self):
        """Refresh T1 Test_Validation copies from current Output so cut TV parity is truthful."""
        try:
            from tools.publish_test_validation import publish_tables

            dest = publish_tables(
                ["quikprmh", "quikbenh", "quikclms", "quikclmp"],
                issue_tag="Cut_Completeness_T1",
            )
            self.log(f"Cut Completeness: published T1 Test_Validation tables → {dest}")
            return True
        except Exception as exc:
            self.log(f"Cut Completeness: T1 Test_Validation publish failed: {exc}")
            return False

    def _evaluate_cut_completeness_gate(self, package_ok, error_log=None):
        """Evaluate cut manifest after hygiene; gate Append/Complete on PASS ∧ package_ok."""
        journal = getattr(self, "_cut_journal", None)
        if journal is None and getattr(self, "_cut_journal_required", False):
            reason = getattr(self, "_cut_journal_start_error", None) or "batch journal unavailable"
            try:
                from qla_core.cut_completeness_manifest import write_journal_unavailable_manifest

                reports = self._reports_dir()
                manifest = write_journal_unavailable_manifest(
                    reason=reason,
                    reports_dir=reports,
                    package_ok=bool(package_ok),
                    app_version=APP_VERSION,
                    launched_app_path=os.path.abspath(__file__),
                )
                self._last_cut_manifest = manifest
                self.log(
                    f"Cut Completeness: JOURNAL_UNAVAILABLE — handoff blocked. "
                    f"manifest → {(manifest.get('artifacts') or {}).get('json')}"
                )
            except Exception as exc:
                self._last_cut_manifest = {
                    "status": "FAIL",
                    "detail": f"JOURNAL_UNAVAILABLE: {reason}; artifact write failed: {exc}",
                    "handoff_ok": False,
                    "findings": [{"code": "JOURNAL_UNAVAILABLE", "detail": reason}],
                }
                self.log(f"Cut Completeness: JOURNAL_UNAVAILABLE (artifact write failed): {exc}")
            if error_log is not None:
                try:
                    error_log.write_failed_stage("Cut Completeness Gate", f"JOURNAL_UNAVAILABLE: {reason}")
                except Exception:
                    pass
            return False
        if journal is None:
            self._last_cut_manifest = {
                "status": "SKIPPED",
                "detail": "no journal (non-batch)",
                "handoff_ok": bool(package_ok),
            }
            return bool(package_ok)
        if getattr(self, "_cut_journal_required", False) and journal is not None:
            self._publish_cut_tv_parity_tables()
        try:
            from qla_core.cut_completeness_manifest import build_and_evaluate_cut_manifest

            out_dir = self.path_vars["Out"][0].get().strip() or self._migration_output_dir()
            reports = self._reports_dir()
            manifest = build_and_evaluate_cut_manifest(
                journal,
                output_dir=out_dir,
                reports_dir=reports,
                run_validators=True,
                write_artifacts=True,
                package_ok=bool(package_ok),
                mutate_hygiene=False,
            )
            self._last_cut_manifest = manifest
            arts = manifest.get("artifacts") or {}
            self.log(
                f"Cut Completeness: status={manifest.get('status')} "
                f"findings={len(manifest.get('findings') or [])} "
                f"handoff_ok={manifest.get('handoff_ok')} "
                f"semantics={manifest.get('pass_semantics')}"
            )
            if arts.get("json"):
                self.log(f"Cut Completeness: manifest → {arts.get('json')}")
            deferred = manifest.get("deferred_gaps") or []
            if deferred:
                ids = ",".join(str(d.get("id")) for d in deferred)
                self.log(
                    f"Cut Completeness: deferred_gaps=[{ids}] "
                    "(PASS ≠ full Closed-fleet green)"
                )
            for warn in manifest.get("warnings") or []:
                self.log(f"Cut Completeness WARN: {warn}")
            if manifest.get("status") != "PASS":
                for finding in (manifest.get("findings") or [])[:25]:
                    self.log(f"  FAIL {finding.get('code')}: {finding.get('detail')}")
                if error_log is not None:
                    try:
                        error_log.write_failed_stage(
                            "Cut Completeness Gate",
                            f"status=FAIL findings={len(manifest.get('findings') or [])}",
                        )
                    except Exception:
                        pass
                return False
            return bool(package_ok)
        except Exception as exc:
            self._last_cut_manifest = {"status": "FAIL", "detail": str(exc), "handoff_ok": False}
            self.log(f"Cut Completeness: gate evaluation ERROR (blocking): {exc}")
            return False

    def _run_output_hygiene(self, error_log=None):
        """Keep QLA_Migration/Output CSV-only and finalize Append Tool package.

        Returns True when Append packaging succeeded (or was not required);
        False when packaging failed. Callers must not report a clean Complete
        when this returns False.
        """
        try:
            out_dir = self.path_vars["Out"][0].get().strip() or self._migration_output_dir()
            if not out_dir or not os.path.isdir(out_dir):
                self._last_dbf_append_package_ok = False
                return False
            reports = self._reports_dir()
            sandbox = self._rate_loader_dbf_dir()
            res = RL.relocate_non_csv(out_dir, reports, sandbox, error_log)
            if res["moved"]:
                self.log(f"Output hygiene: moved {len(res['moved'])} non-CSV file(s) out of Output "
                         f"(Reports/sandbox/Error_Logs). Output is CSV-only.")
            if res["skipped"]:
                self.log(f"Output hygiene WARNING: {len(res['skipped'])} non-CSV file(s) could not be moved "
                         f"(left in place, not deleted):")
                for src, reason in res["skipped"]:
                    self.log(f"  - {os.path.basename(src)}: {reason}")
            # Wave 1: relocate non-table CSVs (claims_*.csv, manifests, audits)
            try:
                csv_res = RL.relocate_non_table_csvs(out_dir, reports, error_log)
                if csv_res.get("moved"):
                    self.log(
                        f"Output hygiene: moved {len(csv_res['moved'])} non-table CSV(s) "
                        f"out of Output root → Reports."
                    )
                if csv_res.get("skipped"):
                    for src, reason in csv_res["skipped"]:
                        self.log(f"  - {os.path.basename(src)}: {reason}")
            except Exception as hyg_exc:
                self.log(f"Output hygiene WARNING: non-table CSV relocate failed: {hyg_exc}")
            pub_rc = self._publish_dbf_append_tool_input(out_dir)
            ok = pub_rc >= 0 and getattr(self, "_last_dbf_append_package_ok", False) is True
            self._last_dbf_append_package_ok = ok
            return ok
        except Exception as exc:
            self._last_dbf_append_package_ok = False
            self.log(f"Output hygiene / Append package FAIL (blocking): {exc}")
            return False

    def start_governance_audit_thread(self):
        if self.is_running:
            messagebox.showwarning("Governance Audit", "A conversion or batch job is already running.")
            return
        data_region = self._resolve_governance_data_dir()
        if not data_region:
            data_region = self._prompt_governance_data_folder()
            if not data_region:
                messagebox.showwarning(
                    "Governance Audit",
                    "Select a Governance Data Folder containing Quik*.csv or Quik*.dbf files.",
                )
                return
        self.is_running = True
        self.start_time = time.time()
        threading.Thread(target=self.update_timer, daemon=True).start()
        threading.Thread(target=self._run_governance_audit_ui, daemon=True).start()

    def _run_governance_audit_ui(self):
        """On-demand QLAdmin Data Governance — report-only; never blocks or modifies data."""
        try:
            self.start_run_progress("governance_audit")
            self.update_run_progress(1, detail="Preparing QLAdmin Data Governance")
            summary = self._execute_governance_audit(
                open_report=True, show_dialog=True, with_ui_progress=True,
            )
            status = summary.get("status", "DONE")
            detail = (
                f"Complete — Status={status} "
                f"Failed={summary.get('failed', 0)} "
                f"Errors={summary.get('errors', 0)} "
                f"Findings={summary.get('total', 0)}"
            )
            if status == "PASS":
                self.complete_run_progress("Complete — QLAdmin Data Governance PASS (no findings)")
            else:
                self.complete_run_progress(detail)
        except Exception as exc:
            self.log(f"DATA GOVERNANCE ERROR: {exc}")
            self.fail_run_progress("QLAdmin Data Governance", str(exc))
            messagebox.showerror("QLAdmin Data Governance", str(exc))
        finally:
            self.is_running = False
            # Leave final elapsed time visible (timer thread stops when is_running is False).

    def _balancing_dir(self):
        return os.path.normpath(os.path.join(self._migration_root(), "Balancing"))

    def _resolve_balancing_source_dir(self):
        candidates = []
        if hasattr(self, "path_vars") and "Src" in self.path_vars:
            src_file = self.path_vars["Src"][0].get().strip()
            if src_file:
                candidates.append(os.path.dirname(src_file))
        candidates.append(self._migration_source_dir())
        for path in candidates:
            if path and os.path.isdir(path):
                return os.path.normpath(path)
        return ""

    def _resolve_balancing_output_dir(self):
        if hasattr(self, "path_vars") and "Out" in self.path_vars:
            out = self.path_vars["Out"][0].get().strip()
            if out and os.path.isdir(out):
                return os.path.normpath(out)
        return self._migration_output_dir()

    def _execute_balancing(self, open_report=True, show_dialog=True, with_ui_progress=False):
        """Shared Source ↔ QLAdmin balancing runner for UI. Returns summary dict."""
        src_dir = self._resolve_balancing_source_dir()
        out_dir = self._resolve_balancing_output_dir()
        if not src_dir:
            raise FileNotFoundError(
                "Source folder not found. Set Source Data File path or use QLA_Migration/Source."
            )
        if not out_dir or not os.path.isdir(out_dir):
            raise FileNotFoundError("Output folder not found. Run conversion or set Output path.")

        repo = self._repo_root()
        if repo not in sys.path:
            sys.path.insert(0, repo)
        from qla_core.balancing import run_balancing

        balancing_dir = self._balancing_dir()
        crosswalk = os.path.join(self._migration_mapping_dir(), "Master_Crosswalk.csv")
        exclusions = os.path.join(self._migration_configs_dir(), "balancing_exclusions.csv")

        self.log("BALANCING: starting Source ↔ QLAdmin reconciliation (read-only)...")
        self.log(f"  Source folder: {src_dir}")
        self.log(f"  Output folder: {out_dir}")

        def _progress(msg, stage=None):
            self.log(f"  {msg}")
            if with_ui_progress:
                if stage is not None:
                    self.update_run_progress(int(stage), detail=str(msg)[:80])
                elif hasattr(self, "lbl_stage_detail"):
                    self.lbl_stage_detail.config(text=str(msg)[:80])
                if hasattr(self, "root"):
                    try:
                        self.root.after(0, self.root.update_idletasks)
                    except Exception:
                        pass

        if with_ui_progress:
            self.update_run_progress(1, detail="Starting Balancing review")

        summary = run_balancing(
            src_dir=src_dir,
            out_dir=out_dir,
            balancing_dir=balancing_dir,
            crosswalk_path=crosswalk,
            exclusions_path=exclusions,
            progress_callback=_progress,
        )

        self.log("BALANCING COMPLETE:")
        self.log(f"  Overall: {summary.get('overall_result') or summary.get('overall_status')}")
        self.log(
            f"  PASS={summary.get('pass_count')} "
            f"EXPLAINED={summary.get('explained_count')} "
            f"FAIL={summary.get('fail_count')}"
        )
        what_checked = summary.get("what_was_checked_path") or summary.get("report_path")
        attention = summary.get("attention_csv_path") or ""
        run_folder = summary.get("run_folder") or balancing_dir
        self.log(f"  What Was Checked: {what_checked}")
        self.log(f"  Items Needing Attention: {attention}")

        if show_dialog:
            msg = (
                f"Overall result: {summary.get('overall_result') or summary.get('overall_status')}\n"
                f"Problems found (FAIL): {summary.get('fail_count')}\n"
                f"Explained variances: {summary.get('explained_count')}\n\n"
                f"What Was Checked:\n{what_checked}\n\n"
                f"Items Needing Attention:\n{attention}"
            )
            if summary.get("overall_status") == "PASS":
                messagebox.showinfo("QUIKConvert Balancing", msg)
            else:
                messagebox.showwarning("QUIKConvert Balancing", msg)

        if open_report and what_checked and os.path.isfile(what_checked):
            try:
                os.startfile(what_checked)  # noqa: S606
            except OSError:
                pass
        if open_report and run_folder and os.path.isdir(run_folder):
            try:
                os.startfile(run_folder)  # noqa: S606
            except OSError:
                pass

        return summary

    def start_balancing_thread(self):
        if self.is_running:
            messagebox.showwarning("Balancing", "A conversion or batch job is already running.")
            return
        if not self._resolve_balancing_source_dir():
            messagebox.showwarning(
                "Balancing",
                "Source folder not found. Set Source Data File path in System Configuration.",
            )
            return
        out_dir = self._resolve_balancing_output_dir()
        if not out_dir or not os.path.isdir(out_dir):
            messagebox.showwarning(
                "Balancing",
                "Output folder not found. Run conversion or set Output path.",
            )
            return
        self.is_running = True
        self.start_time = time.time()
        threading.Thread(target=self.update_timer, daemon=True).start()
        threading.Thread(target=self._run_balancing_ui, daemon=True).start()

    def _run_balancing_ui(self):
        """On-demand Source ↔ QLAdmin balancing — report-only; never modifies conversion data."""
        try:
            self.start_run_progress("balancing")
            self.update_run_progress(1, detail="Preparing Source ↔ QLAdmin Balancing")
            summary = self._execute_balancing(
                open_report=True, show_dialog=True, with_ui_progress=True,
            )
            status = summary.get("overall_status", "DONE")
            fail_n = summary.get("fail_count", 0)
            if status == "PASS":
                self.complete_run_progress("Complete — QUIKConvert Balancing PASS")
            else:
                self.complete_run_progress(f"Complete — Balancing {status} (FAIL={fail_n})")
        except Exception as exc:
            self.log(f"BALANCING ERROR: {exc}")
            self.fail_run_progress("QUIKConvert Balancing", str(exc))
            messagebox.showerror("QUIKConvert Balancing", str(exc))
        finally:
            self.is_running = False

    def update_progress(self, stage_percent, stage_message, state="running"):
        """Cosmetic staged progress feedback. Updates the progress bar (when a percent
        is supplied) and the adjacent stage label. Never touches conversion data and is
        safe to call before the widgets exist. Pass stage_percent=None to update only the
        stage message without disturbing in-flight per-record bar movement."""
        try:
            if stage_percent is not None and hasattr(self, "progress"):
                self.progress["value"] = max(0, min(100, stage_percent))
            if hasattr(self, "lbl_stage"):
                color = {
                    "success": self.stage_color_success,
                    "error": self.stage_color_error,
                }.get(state, self.stage_color_idle)
                self.lbl_stage.config(text=stage_message, fg=color)
            if hasattr(self, "root"):
                self.root.update_idletasks()
        except Exception:
            # Presentation-only helper — must never interrupt a conversion run.
            pass

    def process_data(self, is_batch):
        run_error_log = self._new_run_error_log()
        current_stage = "Initializing run and folders"
        try:
            self.console.delete(1.0, tk.END)
            self.start_run_progress("full_batch" if is_batch else "single_table")
            self.update_run_progress(1, detail="Preparing conversion run")
            self.log(f"Initializing {APP_BRAND} {APP_VERSION} — {APP_TAGLINE}")
            from qla_core.policy_data_transforms import reset_policy_transform_audit
            reset_policy_transform_audit()
            self._diag_rel_fallback_count = 0
            self._claims_pipeline_runner_completed = False
            self._claims_pipeline_runner_success = False
            self._cut_journal_start(is_batch)
            if self.debug_rel_fallback:
                self.log("DEBUG REL: Relationship fallback logging enabled (QLA_DEBUG_REL_FALLBACK)")
            batch_claims_flag = self._batch_include_claims_uat_enabled()
            quikisrr_flag = self._batch_include_quikisrr_enabled()
            quikloan_flag = os.environ.get("QLA_ENABLE_QUIKLOAN_EMIT", "").strip() == "1"
            quikbenh_loan_flag = os.environ.get("QLA_ENABLE_QUIKBENH_LOAN_EMIT", "").strip() == "1"
            reinsurance_flag = os.environ.get("QLA_ENABLE_REINSURANCE_EMIT", "").strip() == "1"
            rate_batch_flag = os.environ.get("QLA_BATCH_INCLUDE_RATE_TABLES", "").strip().lower() in ("1", "true", "yes")
            uat_dbf_flag = self._claims_uat_dbf_generation_enabled()
            mpolicy_flag = self._claims_mpolicy_validation_enabled()
            self.log(
                f"RUN_MODE={self.RUN_MODE} | claims_orchestration=Phase18A–20 | "
                f"production_dbf_flag={self.CLAIMS_ORCHESTRATION['production_dbf_flag']} | "
                f"batch_include_claims_uat={'Y' if batch_claims_flag else 'N'} | "
                f"quikisrr_emit={'Y' if quikisrr_flag else 'N'} | "
                f"quikloan_emit={'Y' if quikloan_flag else 'N'} | "
                f"quikbenh_loan_emit={'Y' if quikbenh_loan_flag else 'N'} | "
                f"reinsurance_emit={'Y' if reinsurance_flag else 'N'} | "
                f"rate_tables_batch={'Y' if rate_batch_flag else 'N'} | "
                f"generate_uat_claims_dbf={'Y' if uat_dbf_flag else 'N'} | "
                f"validate_claims_mpolicy={'Y' if mpolicy_flag else 'N'}"
            )
            
            trans_path = self.path_vars["Trans"][0].get()
            trans_map = {}
            if trans_path and os.path.exists(trans_path):
                trans_df = pd.read_csv(trans_path, dtype=str)
                trans_map = {self.normalize(k): str(v).strip() for k, v in zip(trans_df.iloc[:, 0], trans_df.iloc[:, 1])}
                self.log(f"Successfully loaded Translation Matrix from: {os.path.basename(trans_path)}")
            else:
                self.log("Warning: Value Translation file not found.")

            cw_path = self.path_vars["CW"][0].get()
            cw_map = {}
            reverse_cw_map = {}
            if cw_path and os.path.exists(cw_path):
                cw_df = pd.read_csv(cw_path, dtype=str)
                cw_map = {self.normalize(k): self.normalize(v) for k, v in zip(cw_df.iloc[:, 0], cw_df.iloc[:, 1])}
                reverse_cw_map = {self.normalize(v): self.normalize(k) for k, v in zip(cw_df.iloc[:, 0], cw_df.iloc[:, 1])}
                self.log(f"Successfully loaded ID Crosswalk from: {os.path.basename(cw_path)}")
            else:
                self.log("Warning: ID Crosswalk file not found. Legacy linkages may fail.")

            mplan_resolver = None
            quikplan_plan_set = set()
            mplan_trace_rows = []
            mplan_src_file = ""
            if self._closed_mplan_authority_enabled():
                out_preview = self.path_vars["Out"][0].get()
                mplan_resolver, quikplan_plan_set, _ = self._init_mplan_authority(out_preview, cw_path)
                self.log(
                    f"P3E CLOSED MPLAN AUTHORITY: enabled "
                    f"(quikplan PLAN universe={len(quikplan_plan_set)}, "
                    f"legacy_fallback={'Y' if self._allow_legacy_mplan_fallback() else 'N'})"
                )

            rel_path = self.path_vars["Rel"][0].get()
            rel_map = self._load_rel_map(rel_path, trans_map, log_label="startup relational map")
            current_stage = "Loading source extracts"
            self.update_run_progress(2, detail="Loading source data and lookups")

            # --- RelationshipNameAddress Extract Cache ---
            rel_name_cache = {}
            self._diag_name_count = 0
            try:
                src_input_dir = os.path.dirname(self.path_vars["Src"][0].get()) if self.path_vars["Src"][0].get() else ""
                rel_ext_path = self._resolve_rna_source_path(src_input_dir) if src_input_dir else "RelationshipNameAddress_Extract.csv"
                
                self.log(f"DEBUG: Attempting to load RelationshipNameAddress from: {rel_ext_path}")
                
                with open(rel_ext_path, mode='r', encoding='utf-8-sig') as f:
                    first_line = f.readline()
                    f.seek(0) # Reset file pointer back to start for DictReader
                    
                    has_tabs = '\t' in first_line
                    self.log(f"DEBUG FILE: First line preview (100 chars): {first_line[:100].strip()}")
                    self.log(f"DEBUG FILE: Tabs detected: {has_tabs}")
                    
                    # Dynamically adjust delimiter based on tab detection
                    reader = csv.DictReader(f, delimiter='\t') if has_tabs else csv.DictReader(f)
                    
                    # Normalize fieldnames to strip trailing spaces and enforce uppercase
                    if reader.fieldnames:
                        reader.fieldnames = [str(h).strip().upper() for h in reader.fieldnames]
                        
                    self.log(f"DEBUG FILE: Parsed fieldnames count: {len(reader.fieldnames) if reader.fieldnames else 0}")
                    
                    first_row_logged = False
                    for r in reader:
                        if not first_row_logged:
                            self.log(f"DEBUG PARSE: First parsed row preview: {str(dict(list(r.items())[:5]))}...")
                            first_row_logged = True
                            
                        if 'NAME_ID' in r:
                            raw_name_id = str(r['NAME_ID']).strip()
                            # Skip empty rows or dashed separator rows
                            if not raw_name_id or set(raw_name_id) == {'-'}:
                                continue
                            rel_name_cache[self.normalize(r['NAME_ID'])] = r
                            
                self.log(f"DEBUG: Successfully loaded RelationshipNameAddress cache ({len(rel_name_cache)} records)")
            except FileNotFoundError:
                self.log(f"DEBUG: RelationshipNameAddress_Extract.csv not found at: {rel_ext_path}")
            # ---------------------------------------------

            tables = [self.table_var.get()]
            if is_batch:
                all_files = [t for t in self.TABLE_SCHEMAS.keys() if not self._is_claims_table(t)]
                priority = ['quikclnt', 'quikclid']
                tables = priority + [t for t in all_files if t not in priority]
                src_input_preview = self.path_vars["Src"][0].get()
                rule_input_preview = self.path_vars["Rule"][0].get()
                locked_src_base = self._resolve_batch_src_base(src_input_preview)
                locked_rule_base = self._resolve_batch_rule_base(rule_input_preview)
                self.log("=" * 60)
                self.log("BATCH SOURCE LOCK — all LifePRO tables read from one folder")
                self.log(f"  UI Source file: {src_input_preview or '(empty)'}")
                self.log(f"  Locked source root: {locked_src_base}")
                self.log(f"  Locked rulebook root: {locked_rule_base}")
                self.log(f"  Output folder: {self.path_vars['Out'][0].get()}")
                try:
                    from qla_core.valuation_date import apply_valuation_date_env

                    _batch_vd, _batch_vd_src = apply_valuation_date_env(locked_src_base)
                    self.log(
                        f"  Valuation date: {_batch_vd} ({_batch_vd_src}) -> QUIKRIDR.MLASTANN"
                    )
                except ValueError as _vd_err:
                    self.log(f"  !!! VALUATION DATE ERROR: {_vd_err}")
                    self.log("  Set QLA_VALUATION_DATE to match the source package before batch.")
                    return
                self.log("  NOTE: quikclms/quikclmp are NOT LifePRO source files — they come from Phase 17 UAT validation reporting.")
                if self._product_setup_isolated():
                    self.log("  PRODUCT SETUP ISOLATED: quikplan will be SKIPPED in batch (QLA_PRODUCT_SETUP_ISOLATED=1)")
                self.log("=" * 60)

            self._reinsurance_batch_done = False

            for t_id in tables:
                if not t_id: 
                    if not is_batch: self.log("!!! ERROR: Please select a table from the dropdown first.")
                    continue

                if self._is_claims_table(t_id):
                    current_stage = "Running claims / payment outputs"
                    self.update_run_progress(6, detail=f"claims table {t_id}")
                    self._execute_claims_orchestration(t_id)
                    continue

                current_stage = "Building QLAdmin policy/client/rider outputs"
                self.update_run_progress(5, detail=f"building {t_id}")

                if is_batch and t_id.lower() == "quikplan" and self._product_setup_isolated():
                    out_dir = self.path_vars["Out"][0].get()
                    qplan_path = os.path.normpath(os.path.join(out_dir, "quikplan.csv"))
                    self.log("PRODUCT SETUP ISOLATED: skipping quikplan in batch — use Product Setup Conversion panel.")
                    if os.path.isfile(qplan_path):
                        self.log(f"  Using existing catalog: {qplan_path}")
                        self._cut_record(
                            "quikplan",
                            "REUSED_EXISTING",
                            reason="PRODUCT_SETUP_ISOLATED",
                            output_relpath="quikplan.csv",
                        )
                    else:
                        self.log("  WARNING: output/quikplan.csv not found — run Product Setup Conversion first.")
                        self._cut_record(
                            "quikplan",
                            "SKIPPED",
                            reason="PRODUCT_SETUP_ISOLATED_MISSING",
                            output_relpath="quikplan.csv",
                        )
                    continue
                
                rule_input = self.path_vars["Rule"][0].get()
                src_input = self.path_vars["Src"][0].get()

                rule_base = self._resolve_batch_rule_base(rule_input) if is_batch else (
                    os.path.dirname(rule_input) if rule_input else os.path.dirname(os.path.abspath(__file__))
                )
                src_base = self._resolve_batch_src_base(src_input) if is_batch else (
                    os.path.dirname(src_input) if src_input else os.path.dirname(os.path.abspath(__file__))
                )

                rb_path = os.path.normpath(os.path.join(rule_base, f"Sync_Rulebook_{t_id}.csv")) if is_batch else rule_input
                if is_batch:
                    src_path = self._resolve_table_source_path(t_id, src_base)
                    if not src_path:
                        legacy_hint = expected_legacy_filename(t_id)
                        src_path = os.path.normpath(os.path.join(src_base, legacy_hint))
                else:
                    src_path = src_input

                if is_batch:
                    self.log(f"Working Table: {t_id.upper()}")
                    self.log(f"  LifePRO SOURCE: {src_path}")
                    self.log(f"  Rulebook: {rb_path}")
                if t_id.lower() == "quikprmh":
                    if not os.path.exists(src_path):
                        self.log(f"Skipping {t_id.upper()} -> Missing Source Data: {src_path}")
                        self._cut_record(
                            "quikprmh",
                            "SKIPPED",
                            reason="MISSING_SOURCE",
                            source_path=src_path,
                            output_relpath="quikprmh.csv",
                        )
                        continue
                    
                    self.log(f"Working Table: {t_id.upper()}")
                    source = pd.read_csv(src_path, encoding='latin1', low_memory=False, dtype=str, on_bad_lines='skip').fillna("")
                    source.columns = [str(col).replace('\ufeff', '').strip().upper() for col in source.columns]
                    
                    schema = self.TABLE_SCHEMAS.get(t_id.lower())
                    output = []
                    filtered_count = 0
                    
                    for i, src_row in source.iterrows():
                        credit_code = self.normalize(src_row.get("CREDIT_CODE", ""))
                        debit_code = self.normalize(src_row.get("DEBIT_CODE", ""))
                        excluded_codes = {"96", "412", "413", "514", "641", "710", "1110", "1111"}
                        
                        if credit_code == "110" and credit_code not in excluded_codes and debit_code not in excluded_codes:
                            filtered_count += 1
                            try:
                                t_amt = f"{float(str(src_row.get('TRANS_AMOUNT', '')).replace(',', '').strip() or 0):.2f}"
                            except Exception:
                                t_amt = "0.00"
                                
                            bill_mode = self.normalize(src_row.get("BILLING_MODE", ""))
                            mode_count_map = {"1": "1", "3": "4", "6": "2", "12": "12"}
                            mmodepd = mode_count_map.get(bill_mode, "0")
                            
                            bf_val = self.normalize(src_row.get("BILLING_FORM", ""))
                            mbillfrm = trans_map.get(f"BF_{bf_val}", trans_map.get(bf_val, bf_val))
                            
                            pol = self.normalize(src_row.get("POLICY_NUMBER", ""))
                            mpolicy = self._format_qladmin_mpolicy(pol)
                            
                            row_data = {
                                "MPOLICY": mpolicy,
                                "DATEPAID": self.normalize(src_row.get("EFFECTIVE_DATE", "")),
                                "RENEWAL": "2",
                                "PREMIUM": t_amt,
                                "MLIFE": t_amt,
                                "MTERM": "0.00",
                                "MSUPP": "0.00",
                                "MANN": "0.00",
                                "MHEALTH": "0.00",
                                "XS": "0.00",
                                "MPAIDTO": self.normalize(src_row.get("PAID_TO_DATE_NEW", "")),
                                "POSTDATE": "",
                                "MPOSTDATE": self.normalize(src_row.get("DATE_ADDED", "")),
                                "MSOURCE": "",
                                "MBATCH": self.normalize(src_row.get("BATCH_NUMBER", "")),
                                "USER_ID": self.normalize(src_row.get("CODER_ADDED", "")),
                                "MBILLFRM": mbillfrm,
                                "MMODEPD": mmodepd
                            }
                            output.append([row_data[h] for h in schema])
                        
                        if i % 1000 == 0:
                            self.progress["value"] = (i/len(source))*100
                            self.root.update_idletasks()
                    
                    out_dir = self.path_vars["Out"][0].get()
                    out_path = os.path.normpath(os.path.join(out_dir, f"{t_id}.csv"))
                    qdf = pd.DataFrame(output, columns=schema)

                    # Issue #21F: conversion premium adjustment (all plans; ISWL via FV deposits)
                    if is_batch:
                        try:
                            _src_root_21f = os.path.normpath(
                                os.path.join(self._app_base_dir(), "QLA_Migration", "Source")
                            )
                            _ppbentyp_21f = resolve_ppbentyp_extract_path(src_base)
                            if not _ppbentyp_21f:
                                _ppbentyp_21f = resolve_ppbentyp_extract_path(_src_root_21f)
                            _ppben_21f = resolve_ppben_path(src_base)
                            if not _ppben_21f:
                                _ppben_21f = resolve_ppben_path(_src_root_21f)
                            # Dated extract folders (e.g. LifePRO_Extracts_20260731)
                            if not _ppben_21f or not _ppbentyp_21f:
                                try:
                                    for _sub in sorted(os.listdir(_src_root_21f), reverse=True):
                                        _sub_path = os.path.join(_src_root_21f, _sub)
                                        if not os.path.isdir(_sub_path):
                                            continue
                                        if not _ppbentyp_21f:
                                            _ppbentyp_21f = resolve_ppbentyp_extract_path(_sub_path)
                                        if not _ppben_21f:
                                            _ppben_21f = resolve_ppben_path(_sub_path)
                                        if _ppbentyp_21f and _ppben_21f:
                                            break
                                except Exception:
                                    pass
                            if _ppbentyp_21f:
                                _reports_21f = os.path.normpath(
                                    os.path.join(self._app_base_dir(), "QLA_Migration", "Reports")
                                )
                                # Join CONV_ADJ to loadable quikmstr keys (Issue #2 90…C grain)
                                _mstr_keys_21f = set()
                                _mstr_path_21f = os.path.normpath(
                                    os.path.join(out_dir, "quikmstr.csv")
                                )
                                if os.path.isfile(_mstr_path_21f):
                                    try:
                                        _mstr_df_21f = pd.read_csv(
                                            _mstr_path_21f, dtype=str, encoding="latin1"
                                        ).fillna("")
                                        if "MPOLICY" in _mstr_df_21f.columns:
                                            _mstr_keys_21f = {
                                                str(v).strip()
                                                for v in _mstr_df_21f["MPOLICY"]
                                                if str(v).strip()
                                            }
                                    except Exception:
                                        _mstr_keys_21f = set()
                                qdf, _21f_stats = apply_issue21f_conversion_adjustments(
                                    qdf,
                                    _ppbentyp_21f,
                                    normalize_fn=self.normalize,
                                    format_mpolicy_fn=self._format_qladmin_mpolicy,
                                    crosswalk=cw_map,
                                    reports_dir=_reports_21f,
                                    mstr_mpolicy_keys=_mstr_keys_21f or None,
                                    reject_orphan_vs_mstr=bool(_mstr_keys_21f),
                                    ppben_path=_ppben_21f,
                                )
                                self.log(
                                    f"Issue #21F: conversion adjustments loaded={_21f_stats.get('loaded', 0)} "
                                    f"opening_balance={_21f_stats.get('opening_balance', 0)} "
                                    f"stripped_prior={_21f_stats.get('stripped_adj', 0)} "
                                    f"ISWL_loaded={_21f_stats.get('iswl_loaded', 0)} "
                                    f"neg_exceptions={_21f_stats.get('negative_exceptions', 0)} "
                                    f"rows {_21f_stats.get('rows_before', 0)}->{_21f_stats.get('rows_after', 0)}"
                                )
                                if not _ppben_21f:
                                    self.log(
                                        "Issue #21F WARNING: PPBEN extract not found — "
                                        "ISWL CONV_ADJ uses FV_GUAR_DEPOSITS and will be skipped/zero"
                                    )
                            else:
                                self.log("Issue #21F: skipped — PPBENTYP extract not found")
                        except Exception as e:
                            self.log(f"Warning: Issue #21F premium adjustment failed - {e}")

                    qdf.to_csv(out_path, index=False)
                    
                    self.log(f"Success: {t_id}.csv - {len(qdf)} records.")
                    self._cut_record(
                        "quikprmh",
                        "WRITTEN",
                        source_path=src_path,
                        output_relpath="quikprmh.csv",
                        row_count=len(qdf),
                    )
                    
                    audit_path = os.path.normpath(os.path.join(self._logs_dir(), "Migration_Audit_Log.txt"))
                    is_new_log = not os.path.exists(audit_path)
                    source_count = len(source)
                    output_count = len(qdf)
                    variance = source_count - output_count
                    
                    audit_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] TABLE: {t_id.upper():<10} | SOURCE RECORDS: {source_count:<8} | QLA OUTPUT: {output_count:<8} | VARIANCE: {variance} (Filtered)\n"
                    
                    with open(audit_path, "a") as f:
                        if is_new_log:
                            f.write("=== QLADMIN ENTERPRISE MIGRATION AUDIT LOG ===\n")
                            f.write("Tracks 1:1 record translation matching to guarantee zero data loss.\n\n")
                        f.write(audit_msg)
                    
                    self.log(f"Audit Verified: {source_count} Source -> {output_count} Output. Saved to Audit Log.")

                    unique_policies = qdf['MPOLICY'].nunique()
                    blank_datepaid = qdf['DATEPAID'].astype(str).str.strip().isin(["", "nan", "None"]).sum()
                    blank_paidto = qdf['MPAIDTO'].astype(str).str.strip().isin(["", "nan", "None"]).sum()
                    zero_premium = qdf['PREMIUM'].astype(str).str.strip().isin(["", "0", "0.0", "0.00", "nan", "None"]).sum()
                    duplicate_rows = qdf.duplicated().sum()
                    mode_dist = qdf['MMODEPD'].value_counts(dropna=False).to_dict()
                    
                    self.log("QUIKPRMH ENTERPRISE VALIDATION:")
                    self.log(f"  Total PACTG Source Rows: {len(source)}")
                    self.log(f"  Filtered Payment-History Rows: {filtered_count}")
                    self.log(f"  Unique Policies: {unique_policies}")
                    self.log(f"  Blank DATEPAID: {blank_datepaid}")
                    self.log(f"  Blank MPAIDTO: {blank_paidto}")
                    self.log(f"  Zero PREMIUM: {zero_premium}")
                    self.log(f"  Duplicate Exact Rows: {duplicate_rows}")
                    self.log(f"  MMODEPD Distribution: {mode_dist}")
                    
                    continue  # Safely abort the parent processing loop and move to the next batch table
                if t_id.lower() == "quikactg":
                    if not os.path.exists(src_path):
                        self.log(f"Skipping {t_id.upper()} -> Missing Source Data: {src_path}")
                        self._cut_record(
                            "quikactg",
                            "SKIPPED",
                            reason="MISSING_SOURCE",
                            source_path=src_path,
                            output_relpath="quikactg.csv",
                        )
                        continue

                    self.log(f"Working Table: {t_id.upper()} (PACTG plan-level accounting setup)")
                    closed_actg = self._closed_mplan_authority_enabled()
                    if closed_actg and mplan_resolver is None:
                        out_dir_preview = self.path_vars["Out"][0].get()
                        mplan_resolver, quikplan_plan_set, _ = self._init_mplan_authority(out_dir_preview, cw_path)

                    output_df, trace_df, actg_stats = convert_quikactg_from_pactg(
                        src_path,
                        cw_map=cw_map,
                        resolver=mplan_resolver,
                        quikplan_plan_set=quikplan_plan_set,
                        closed_authority=closed_actg,
                        allow_legacy=self._allow_legacy_mplan_fallback(),
                        rulebook_path=rb_path if os.path.isfile(rb_path) else None,
                    )

                    out_dir = self.path_vars["Out"][0].get()
                    out_path = os.path.normpath(os.path.join(out_dir, f"{t_id}.csv"))
                    output_df.to_csv(out_path, index=False)
                    self.log(f"Success: {t_id}.csv - {len(output_df)} plan records.")
                    self._cut_record(
                        "quikactg",
                        "WRITTEN",
                        source_path=src_path,
                        output_relpath="quikactg.csv",
                        row_count=len(output_df),
                        extra={"output_abs_path": out_path, "feature": "quikactg_pactg"},
                    )

                    if closed_actg and not trace_df.empty:
                        p3f_dir = os.path.normpath(
                            os.path.join(self._app_base_dir(), "plan_analysis", "phase_p3f_quikactg_authority_alignment")
                        )
                        passed, val_stats = validate_emitted_quikridr(output_df, quikplan_plan_set)
                        write_p3f_governance_outputs(
                            p3f_dir,
                            trace_df,
                            closed_enabled=True,
                            allow_legacy=self._allow_legacy_mplan_fallback(),
                            emitted_rows=len(output_df),
                            validation_passed=passed,
                            pactg_stats=actg_stats,
                        )
                        self.log(f"P3F MPLAN AUTHORITY: validation={'PASSED' if passed else 'FAILED'} stats={val_stats}")
                        self.log(f"P3F governance outputs: {p3f_dir}")

                    audit_path = os.path.normpath(os.path.join(self._logs_dir(), "Migration_Audit_Log.txt"))
                    is_new_log = not os.path.exists(audit_path)
                    audit_msg = (
                        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] TABLE: {t_id.upper():<10} | "
                        f"SOURCE RECORDS: {actg_stats.get('pactg_rows_read', 0):<8} | "
                        f"QLA OUTPUT: {len(output_df):<8} | "
                        f"VARIANCE: {actg_stats.get('pactg_rows_read', 0) - len(output_df)} (Plan-level pivot)\n"
                    )
                    with open(audit_path, "a") as f:
                        if is_new_log:
                            f.write("=== QLADMIN ENTERPRISE MIGRATION AUDIT LOG ===\n")
                            f.write("Tracks 1:1 record translation matching to guarantee zero data loss.\n\n")
                        f.write(audit_msg)
                    self.log(f"Audit Verified: PACTG -> {len(output_df)} quikactg plan rows. Saved to Audit Log.")
                    continue
                if t_id.lower() == "quikloan":
                    if os.environ.get("QLA_ENABLE_QUIKLOAN_EMIT", "").strip() != "1":
                        self.log(
                            "Skipping QUIKLOAN — set QLA_ENABLE_QUIKLOAN_EMIT=1 for Issue #32 QuikLoan "
                            "(or run plan_analysis/phase_l1_quikloan/quikloan_runner.py)."
                        )
                        self._cut_record(
                            "quikloan",
                            "SKIPPED",
                            reason="EMIT_OFF",
                            source_path=src_path if "src_path" in locals() else None,
                            output_relpath="quikloan.csv",
                        )
                        continue
                    if not os.path.exists(src_path):
                        self.log(f"Skipping {t_id.upper()} -> Missing Source Data: {src_path}")
                        self._cut_record(
                            "quikloan",
                            "SKIPPED",
                            reason="MISSING_SOURCE",
                            source_path=src_path,
                            output_relpath="quikloan.csv",
                        )
                        continue
                    self.log(f"Working Table: {t_id.upper()} (PLOAN → QuikLoan Issue #32 v1.2)")
                    phase_l1_dir = os.path.normpath(
                        os.path.join(self._app_base_dir(), "plan_analysis", "phase_l1_quikloan")
                    )
                    out_dir = self.path_vars["Out"][0].get()
                    qp_path = os.path.normpath(os.path.join(out_dir, "quikplan.csv"))
                    if not os.path.isfile(qp_path):
                        qp_path = ""
                    qm_path = os.path.normpath(os.path.join(out_dir, "quikmstr.csv"))
                    if not os.path.isfile(qm_path):
                        qm_path = ""
                    rules = load_derivation_rules()
                    passed_df, trace_df, exceptions_df, ql_stats = convert_quikloan_from_ploan(
                        src_path,
                        cw_map=cw_map,
                        rules=rules,
                        output_dir=phase_l1_dir,
                        quikplan_path=qp_path or None,
                        quikmstr_path=qm_path or None,
                    )
                    self.log(
                        f"QUIKLOAN Issue #32/#44A: {ql_stats.get('emit_passed', 0)} emit rows, "
                        f"{ql_stats.get('emit_exceptions', 0)} exceptions; "
                        f"MLOANINTX fallback={ql_stats.get('mloanintx_fallback_count', 0)}; "
                        f"reports -> {phase_l1_dir}"
                    )
                    if ql_stats.get("issue104_pilot_enabled"):
                        self.log(
                            "Issue 104 validated advance-loan pilot: "
                            f"encountered={ql_stats.get('issue104_cohort_encountered', 0)} "
                            f"adjusted={ql_stats.get('issue104_cohort_adjusted', 0)} "
                            f"runtime_fail={ql_stats.get('issue104_runtime_formula_failures', 0)} "
                            f"(disable QLA_ISSUE104_VALIDATED_LOAN_BACKOUT=0)"
                        )
                        if ql_stats.get("issue104_audit_path"):
                            self.log(f"Issue 104 pilot audit: {ql_stats.get('issue104_audit_path')}")
                        if ql_stats.get("issue104_runtime_formula_failures"):
                            self.log(
                                "WARNING: Issue 104 allowlisted policies failed runtime "
                                "formula checks — left on gross LOAN_BALANCE mapping."
                            )
                    if os.environ.get("QLA_QUIKLOAN_WRITE_OUTPUT", "").strip() == "1":
                        out_path = os.path.normpath(os.path.join(out_dir, "quikloan.csv"))
                        passed_df.to_csv(out_path, index=False)
                        self.log(f"GATED OUTPUT: {out_path} ({len(passed_df)} rows)")
                        self._cut_record(
                            "quikloan",
                            "WRITTEN",
                            source_path=src_path,
                            output_relpath="quikloan.csv",
                            row_count=len(passed_df),
                        )
                    else:
                        self._cut_record(
                            "quikloan",
                            "GATED_NO_WRITE",
                            reason="QLA_QUIKLOAN_WRITE_OUTPUT!=1",
                            source_path=src_path,
                            output_relpath="quikloan.csv",
                        )
                    continue
                if t_id.lower() == "quikbenh":
                    benh_loan_emit = (
                        os.environ.get("QLA_ENABLE_QUIKBENH_LOAN_EMIT", "").strip() == "1"
                    )
                    benh_dividend_emit = (
                        os.environ.get("QLA_ENABLE_QUIKBENH_DIVIDEND_EMIT", "").strip() == "1"
                    )
                    if not benh_loan_emit and not benh_dividend_emit:
                        self.log(
                            "Skipping QUIKBENH — set QLA_ENABLE_QUIKBENH_LOAN_EMIT=1 "
                            "for Issue #54 (or run plan_analysis/phase_benh_loan_history/"
                            "quikbenh_loan_runner.py), and/or "
                            "QLA_ENABLE_QUIKBENH_DIVIDEND_EMIT=1 for Issue #114 dividend history."
                        )
                        self._cut_record(
                            "quikbenh",
                            "SKIPPED",
                            reason="EMIT_OFF",
                            source_path=src_path if "src_path" in locals() else None,
                            output_relpath="quikbenh.csv",
                        )
                        continue
                    if not os.path.exists(src_path):
                        self.log(f"Skipping {t_id.upper()} -> Missing Source Data: {src_path}")
                        self._cut_record(
                            "quikbenh",
                            "SKIPPED",
                            reason="MISSING_SOURCE",
                            source_path=src_path,
                            output_relpath="quikbenh.csv",
                        )
                        continue
                    if benh_dividend_emit:
                        self._emit_quikbenh_dividend_history(src_path, src_base, cw_map)
                    if not benh_loan_emit:
                        continue
                    ploan_path, ploan_label = resolve_table_source(src_base, "quikloan")
                    if not ploan_path:
                        self.log(f"Skipping {t_id.upper()} -> Missing PLOAN source in {src_base}")
                        continue
                    self.log(
                        f"Working Table: {t_id.upper()} "
                        "(PACTG → QuikBenh loan history + PLOAN opening seed Issue #54)"
                    )
                    self.log(f"  PLOAN seed source: {ploan_path} ({ploan_label})")
                    phase_benh_dir = os.path.normpath(
                        os.path.join(self._app_base_dir(), "plan_analysis", "phase_benh_loan_history")
                    )
                    out_dir = self.path_vars["Out"][0].get()
                    existing_benh = os.path.normpath(os.path.join(out_dir, "quikbenh.csv"))
                    rules = load_benh_loan_rules()
                    merged_df, loan_df, trace_df, exceptions_df, bh_stats = (
                        convert_quikbenh_loan_history_from_pactg(
                            src_path,
                            cw_map=cw_map,
                            rules=rules,
                            ploan_path=ploan_path,
                            output_dir=phase_benh_dir,
                            existing_benh_path=existing_benh if os.path.isfile(existing_benh) else None,
                        )
                    )
                    self.log(
                        f"QUIKBENH Issue #54: {bh_stats.get('emit_passed', 0)} PACTG rows + "
                        f"{bh_stats.get('seed_emit', 0)} opening seeds -> "
                        f"{bh_stats.get('merged_rows', 0)} merged; "
                        f"type-8 preserved={bh_stats.get('existing_type8_rows', 0)}; "
                        f"seed_skip_no_prior={bh_stats.get('seed_skip_no_prior', 0)}; "
                        f"reports -> {phase_benh_dir}"
                    )
                    if os.environ.get("QLA_QUIKBENH_LOAN_WRITE_OUTPUT", "").strip() == "1":
                        out_path = os.path.normpath(os.path.join(out_dir, "quikbenh.csv"))
                        write_quikbenh_csv(merged_df, out_path)
                        self.log(f"GATED OUTPUT: {out_path} ({len(merged_df)} rows)")
                        self._cut_record(
                            "quikbenh",
                            "WRITTEN",
                            source_path=src_path,
                            output_relpath="quikbenh.csv",
                            row_count=len(merged_df),
                        )
                    else:
                        self._cut_record(
                            "quikbenh",
                            "GATED_NO_WRITE",
                            reason="QLA_QUIKBENH_LOAN_WRITE_OUTPUT!=1",
                            source_path=src_path,
                            output_relpath="quikbenh.csv",
                        )
                    continue
                if t_id.lower() in ("quikrein", "quikrmst"):
                    if getattr(self, "_reinsurance_batch_done", False):
                        continue
                    if os.environ.get("QLA_ENABLE_REINSURANCE_EMIT", "").strip() != "1":
                        self.log(
                            "Skipping REINSURANCE — set QLA_ENABLE_REINSURANCE_EMIT=1 "
                            "(or run plan_analysis/phase_r9_quikrein_rmst/reinsurance_runner.py)."
                        )
                        self._cut_record(
                            "quikrein",
                            "SKIPPED",
                            reason="EMIT_OFF",
                            output_relpath="quikrein.csv",
                        )
                        self._cut_record(
                            "quikrmst",
                            "SKIPPED",
                            reason="EMIT_OFF",
                            output_relpath="quikrmst.csv",
                        )
                        continue
                    ptrty_path, ptrty_label, prein_path, prein_label, preintrt_path, preintrt_label = resolve_reinsurance_sources(src_base)
                    missing = []
                    if not ptrty_path:
                        missing.append("PROD_PTRTY")
                    if not prein_path:
                        missing.append("PREIN")
                    if not preintrt_path:
                        missing.append("PREINTRT")
                    if missing:
                        self.log(f"Skipping REINSURANCE -> Missing sources: {', '.join(missing)} in {src_base}")
                        continue
                    self.log("Working Table: REINSURANCE Phase 1 (QuikRein + QuikRmst)")
                    self.log(f"  PROD_PTRTY: {ptrty_path} ({ptrty_label})")
                    self.log(f"  PREIN: {prein_path} ({prein_label})")
                    self.log(f"  PREINTRT: {preintrt_path} ({preintrt_label})")
                    phase_r9_dir = os.path.normpath(
                        os.path.join(self._repo_root(), "plan_analysis", "phase_r9_quikrein_rmst")
                    )
                    out_dir = self.path_vars["Out"][0].get()
                    qm_path = os.path.normpath(os.path.join(out_dir, "quikmstr.csv"))
                    if not os.path.isfile(qm_path):
                        qm_path = ""
                    qr_path = os.path.normpath(os.path.join(out_dir, "quikridr.csv"))
                    if not os.path.isfile(qr_path):
                        qr_path = ""
                    rules = load_reinsurance_derivation_rules()
                    rein_df, rmst_df, trace_df, rein_exc, rmst_exc, r_stats = convert_reinsurance_phase1(
                        ptrty_path,
                        prein_path,
                        preintrt_path,
                        cw_map=cw_map,
                        rules=rules,
                        output_dir=phase_r9_dir,
                        quikmstr_path=qm_path or None,
                        quikridr_path=qr_path or None,
                    )
                    self._reinsurance_batch_done = True
                    self.log(
                        f"REINSURANCE Phase 1: quikrein={r_stats.get('quikrein_emitted', 0)} rows, "
                        f"quikrmst={r_stats.get('quikrmst_emitted', 0)} rows; "
                        f"exceptions rein={r_stats.get('quikrein_exceptions', 0)} "
                        f"rmst={r_stats.get('quikrmst_exceptions', 0)}; "
                        f"ceded_recon={'PASS' if r_stats.get('ceded_reconciliation_ok') else 'FAIL'}; "
                        f"reports -> {phase_r9_dir}"
                    )
                    if os.environ.get("QLA_REINSURANCE_WRITE_OUTPUT", "").strip() == "1":
                        rein_out = os.path.normpath(os.path.join(out_dir, "quikrein.csv"))
                        rmst_out = os.path.normpath(os.path.join(out_dir, "quikrmst.csv"))
                        rein_df.to_csv(rein_out, index=False)
                        rmst_df.to_csv(rmst_out, index=False)
                        self.log(f"GATED OUTPUT: {rein_out} ({len(rein_df)} rows), {rmst_out} ({len(rmst_df)} rows)")
                        self._cut_record(
                            "quikrein",
                            "WRITTEN",
                            output_relpath="quikrein.csv",
                            row_count=len(rein_df),
                        )
                        self._cut_record(
                            "quikrmst",
                            "WRITTEN",
                            output_relpath="quikrmst.csv",
                            row_count=len(rmst_df),
                        )
                    else:
                        self._cut_record(
                            "quikrein",
                            "GATED_NO_WRITE",
                            reason="QLA_REINSURANCE_WRITE_OUTPUT!=1",
                            output_relpath="quikrein.csv",
                        )
                        self._cut_record(
                            "quikrmst",
                            "GATED_NO_WRITE",
                            reason="QLA_REINSURANCE_WRITE_OUTPUT!=1",
                            output_relpath="quikrmst.csv",
                        )
                    audit_path = os.path.normpath(os.path.join(self._logs_dir(), "Migration_Audit_Log.txt"))
                    is_new_log = not os.path.exists(audit_path)
                    audit_msg = (
                        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] TABLE: REINSURANCE | "
                        f"QUIKREIN: {len(rein_df):<6} | QUIKRMST: {len(rmst_df):<6} | "
                        f"PREINTRT IN: {r_stats.get('preintrt_rows', 0):<6} | "
                        f"EXCEPTIONS: {r_stats.get('quikrmst_exceptions', 0)}\n"
                    )
                    with open(audit_path, "a") as f:
                        if is_new_log:
                            f.write("=== QLADMIN ENTERPRISE MIGRATION AUDIT LOG ===\n")
                            f.write("Tracks 1:1 record translation matching to guarantee zero data loss.\n\n")
                        f.write(audit_msg)
                    continue
                if t_id.lower() == "quikmemo":
                    pnote_path, pnote_label, pense_path, pense_label = resolve_quikmemo_sources(src_base)
                    if not pnote_path and not pense_path:
                        self.log(f"Skipping QUIKMEMO -> Missing PNOTE and PENSE sources in {src_base}")
                        self._cut_record(
                            "quikmemo",
                            "SKIPPED",
                            reason="MISSING_SOURCE",
                            source_path=src_base,
                            output_relpath="quikmemo.csv",
                        )
                        continue
                    self.log("Working Table: QUIKMEMO (PNOTE + PENSE dual-source merge)")
                    if pnote_path:
                        self.log(f"  PNOTE SOURCE: {pnote_path} ({pnote_label})")
                    else:
                        self.log("  WARNING: PNOTE source not found")
                    if pense_path:
                        self.log(f"  PENSE SOURCE: {pense_path} ({pense_label})")
                    else:
                        self.log("  WARNING: PENSE source not found")
                    output_df, orphan_df, memo_stats = convert_quikmemo_from_pnote_pense(
                        pnote_path or None,
                        pense_path or None,
                        cw_map=cw_map,
                    )
                    out_dir = self.path_vars["Out"][0].get()
                    quikridr_path = os.path.normpath(os.path.join(out_dir, "quikridr.csv"))
                    quikmstr_path = os.path.normpath(os.path.join(out_dir, "quikmstr.csv"))
                    quikplan_path = os.path.normpath(os.path.join(out_dir, "quikplan.csv"))
                    output_df, conv_stats = append_issue21j_conversion_memos(
                        output_df,
                        conversion_version="v57.46",
                        quikmstr_path=quikmstr_path,
                        quikridr_path=quikridr_path,
                        quikplan_path=quikplan_path,
                    )
                    self.log(
                        f"Issue 21J: conversion memos added={conv_stats.get('conversion_memos_added', 0)} "
                        f"merged={conv_stats.get('conversion_memos_merged', 0)} "
                        f"new={conv_stats.get('conversion_memos_new_row', 0)} "
                        f"fleet={conv_stats.get('converted_policies', 0)}"
                    )
                    out_path = os.path.normpath(os.path.join(out_dir, "quikmemo.csv"))
                    output_df.to_csv(out_path, index=False)
                    self.log(f"Success: quikmemo.csv - {len(output_df)} memo records.")
                    self._cut_record(
                        "quikmemo",
                        "WRITTEN",
                        source_path=pnote_path or pense_path,
                        output_relpath="quikmemo.csv",
                        row_count=len(output_df),
                        extra={"output_abs_path": out_path, "feature": "quikmemo_pnote_pense"},
                    )
                    self.log(
                        f"  Stats: PNOTE emit={memo_stats.get('emitted_pnote', 0)} "
                        f"PENSE emit={memo_stats.get('emitted_pense', 0)} "
                        f"blank skip={memo_stats.get('skipped_blank_pnote', 0) + memo_stats.get('skipped_blank_pense', 0)} "
                        f"file_type_b skip={memo_stats.get('skipped_file_type_b', 0)} "
                        f"orphan={memo_stats.get('skipped_orphan', 0)} "
                        f"exact dup={memo_stats.get('skipped_exact_dup', 0)}"
                    )
                    if not orphan_df.empty:
                        orphan_path = os.path.normpath(os.path.join(out_dir, "quikmemo_orphan_log.csv"))
                        orphan_df.to_csv(orphan_path, index=False)
                        self.log(f"  Orphan audit: {orphan_path} ({len(orphan_df)} rows)")
                    try:
                        # Always land next to the DBF Append Tool load package (not under Output/).
                        dbf_dir = os.path.normpath(DBF_APPEND_TOOL_OUTPUT)
                        os.makedirs(dbf_dir, exist_ok=True)
                        dbf_path = os.path.normpath(os.path.join(dbf_dir, "quikmemo.dbf"))
                        dbf_info = write_quikmemo_dbf(out_path, dbf_path)
                        self.log(
                            f"  QUIKMEMO UAT DBF: {dbf_info['dbf_path']} "
                            f"({dbf_info['dbf_rows']} rows, sidecar={'yes' if dbf_info['fpt_exists'] else 'no'})"
                        )
                    except Exception as exc:
                        self.log(f"  WARNING: QUIKMEMO DBF generation failed: {exc}")
                    audit_path = os.path.normpath(os.path.join(self._logs_dir(), "Migration_Audit_Log.txt"))
                    is_new_log = not os.path.exists(audit_path)
                    audit_msg = (
                        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] TABLE: QUIKMEMO   | "
                        f"PNOTE IN: {memo_stats.get('pnote_source_rows', 0):<6} | "
                        f"PENSE IN: {memo_stats.get('pense_source_rows', 0):<6} | "
                        f"QLA OUTPUT: {len(output_df):<8} | "
                        f"ORPHAN: {memo_stats.get('skipped_orphan', 0)}\n"
                    )
                    with open(audit_path, "a") as f:
                        if is_new_log:
                            f.write("=== QLADMIN ENTERPRISE MIGRATION AUDIT LOG ===\n")
                            f.write("Tracks 1:1 record translation matching to guarantee zero data loss.\n\n")
                        f.write(audit_msg)
                    continue
                # --------------------------------------------------------

                if not os.path.exists(rb_path) or not os.path.exists(src_path): 
                    self.log(f"Skipping {t_id.upper()} -> Missing files at specified paths:")
                    if not os.path.exists(rb_path): self.log(f"   [X] Cannot find Rulebook: {rb_path}")
                    if not os.path.exists(src_path): self.log(f"   [X] Cannot find Source Data: {src_path}")
                    self._cut_record(
                        str(t_id).lower(),
                        "SKIPPED",
                        reason="MISSING_FILES",
                        source_path=src_path,
                        output_relpath=f"{t_id}.csv",
                    )
                    continue
                
                self.log(f"Working Table: {t_id.upper()}")
                
                rules = pd.read_csv(rb_path, dtype=str)
                rules.columns = [str(col).strip() for col in rules.columns]
                
                if t_id.lower() == "quikplan":
                    source, _ = load_quikplan_source_csv(src_path, collect_trace=False)
                    source.columns = [str(col).replace('\ufeff', '').strip().upper() for col in source.columns]
                elif (
                    t_id.lower() in ("quikclnt", "quikclid", "quikbenf")
                    and "relationshipnameaddress" in os.path.basename(src_path).lower()
                ):
                    source = self._read_lifepro_rna_csv(src_path)
                else:
                    source = pd.read_csv(src_path, encoding='latin1', low_memory=False, dtype=str, on_bad_lines='skip').fillna("")
                    source.columns = [str(col).replace('\ufeff', '').strip().upper() for col in source.columns]

                if is_batch and t_id.lower() == "quikclnt" and self._is_preconverted_qla_client_source(source):
                    rna_path = self._resolve_rna_source_path(src_base)
                    if os.path.isfile(rna_path):
                        self.log("WARNING: Source\\quikclnt.csv is pre-converted QLA output — not raw LifePRO.")
                        self.log(f"  Switching quikclnt input to: {rna_path}")
                        source = pd.read_csv(
                            rna_path, encoding='latin1', low_memory=False, dtype=str, on_bad_lines='skip',
                        ).fillna("")
                        source.columns = [str(col).replace('\ufeff', '').strip().upper() for col in source.columns]
                        source = self._bridge_rna_quikclnt_columns(source)
                    else:
                        self.log(
                            "WARNING: Pre-converted quikclnt.csv detected; "
                            "RelationshipNameAddress_Extract.csv not found in Source folder."
                        )

                lookups = {}
                if 'Lookup_Table' in rules.columns and 'Join_Key' in rules.columns:
                    unique_lookups = rules['Lookup_Table'].dropna().unique()
                    for lt in unique_lookups:
                        lt_clean = str(lt).strip()
                        if not lt_clean: continue
                        
                        lt_path = os.path.normpath(os.path.join(os.path.dirname(src_path), f"{lt_clean}.csv"))
                        if os.path.exists(lt_path):
                            try:
                                ldf = pd.read_csv(lt_path, encoding='latin1', low_memory=False, dtype=str, on_bad_lines='skip').fillna("")
                                ldf.columns = [str(col).strip().upper() for col in ldf.columns]
                                
                                jks = rules[rules['Lookup_Table'] == lt]['Join_Key'].dropna().unique()
                                lookups[lt_clean] = {}
                                for jk in jks:
                                    jk_clean = str(jk).strip().upper()
                                    if jk_clean in ldf.columns:
                                        ldf['__norm_jk'] = ldf[jk_clean].apply(self.normalize)
                                        lookups[lt_clean][jk_clean] = ldf.drop_duplicates(subset=['__norm_jk']).set_index('__norm_jk').to_dict('index')
                            except Exception as e: pass
                
                lifepro_extra = {}
                if t_id.lower() == "quikmstr":
                    src_dir = os.path.dirname(src_path)
                    
                    def find_extract(keyword):
                        search_dirs = [
                            src_dir, 
                            os.path.dirname(src_dir),
                            os.path.dirname(self.path_vars["Rule"][0].get()) if self.path_vars["Rule"][0].get() else "",
                            os.path.dirname(self.path_vars["Trans"][0].get()) if self.path_vars["Trans"][0].get() else ""
                        ]
                        all_matches = []
                        for d in search_dirs:
                            if not d or not os.path.exists(d): continue
                            for f in os.listdir(d):
                                if keyword.lower() in f.lower() and f.lower().endswith('.csv'):
                                    if not any(bad in f.lower() for bad in ['copy', 'old', 'backup', 'archive']):
                                        all_matches.append(os.path.normpath(os.path.join(d, f)))
                        if all_matches: return max(all_matches, key=os.path.getmtime)
                        return None

                    for keyword, ext_key, jk in [('ppbentyp', 'DIVIDEND', 'POLICY_NUMBER'), ('ppbentyp', 'NON_FORFEITURE', 'POLICY_NUMBER')]:
                        epath = find_extract(keyword)
                        if epath:
                            try:
                                edf = pd.read_csv(epath, encoding='latin1', low_memory=False, dtype=str, on_bad_lines='skip').fillna("")
                                edf.columns = [str(c).strip().upper() for c in edf.columns]
                                
                                if jk in edf.columns: edf[jk] = edf[jk].astype(str)
                                if ext_key in edf.columns: edf[ext_key] = edf[ext_key].astype(str)
                                
                                edf = edf[~edf.iloc[:, 0].astype(str).str.contains("---")]

                                if jk in edf.columns and ext_key in edf.columns:
                                    for seq_col in ['BENEFIT_SEQ', 'COVERAGE_SEQ']:
                                        if seq_col in edf.columns:
                                            edf[seq_col] = edf[seq_col].astype(str).str.strip().str.replace(".0", "", regex=False)
                                            edf = edf[edf[seq_col].isin(["1", "01"])]
                                            
                                    edf['__norm_jk'] = edf[jk].apply(self.normalize)
                                    if ext_key == 'NON_FORFEITURE':
                                        # Issue 21A: ISWL/BF rows store NFO on BF_NON_FORFEITURE, not NON_FORFEITURE.
                                        def _ppbentyp_nfo_val(row):
                                            tc = str(row.get('TYPE_CODE', '')).strip()
                                            bnf = str(row.get('BF_NON_FORFEITURE', '')).strip().replace('.0', '')
                                            nf = str(row.get('NON_FORFEITURE', '')).strip().replace('.0', '')
                                            def _usable(v):
                                                if not v or v.lower() in ('nan', 'none', 'null'):
                                                    return False
                                                return bool(v.replace('-', '').strip())
                                            if tc == 'BF' and _usable(bnf):
                                                return bnf
                                            if _usable(nf):
                                                return nf
                                            return ''
                                        edf['__resolved_val'] = edf.apply(_ppbentyp_nfo_val, axis=1)
                                        val_col = '__resolved_val'
                                    else:
                                        edf[ext_key] = edf[ext_key].astype(str).str.strip()
                                        val_col = ext_key
                                    edf_valid = edf[~edf[val_col].isin(["", "nan", "none", "null"])]
                                    edf_valid = edf_valid.drop_duplicates(subset=['__norm_jk'], keep='first')
                                    
                                    lifepro_extra[ext_key] = edf_valid.set_index('__norm_jk')[val_col].to_dict()
                                    
                                    sample_keys = list(lifepro_extra[ext_key].keys())[:5]
                                    self.log(f"Auto-loaded Base {ext_key} from {os.path.basename(epath)}")
                                    if ext_key == 'NON_FORFEITURE':
                                        self.log(f"  -> Issue 21A: BF_NON_FORFEITURE priority for TYPE_CODE=BF")
                                    self.log(f"  -> Cache Size: {len(lifepro_extra[ext_key])} | Key Sample: {sample_keys}")
                            except Exception as e:
                                self.log(f"Warning: Could not auto-load {os.path.basename(epath)} - {e}")
                                
                        # --- PPACH BANKING CACHE ---
                        self._ppach_bank_map = {}
                        self._ppach_acct_meta = {}
                        # Issue 21H / #75 reopen: full 9-digit ABA from PPCOM (E_TRAN_ABA_NUMBER),
                        # joined by bank account digits into aba_routing_lookup.csv (rebuild script:
                        # Issue_Log_Items/Issue_75/scripts/rebuild_aba_routing_lookup_from_ppcom.py).
                        # Includes PPACH+PPPAC accounts; unique + latest-ambiguous; checksum-valid.
                        # Falls back to raw PPACH only when already a checksum-valid 9-digit ABA.
                        aba_lookup = {}
                        try:
                            aba_lk_path = find_extract('aba_routing_lookup')
                            if aba_lk_path:
                                ldf = pd.read_csv(aba_lk_path, encoding='latin1', low_memory=False, dtype=str).fillna("")
                                ldf.columns = [str(c).strip().upper() for c in ldf.columns]
                                if 'ACCOUNT_DIGITS' in ldf.columns and 'FULL_ABA' in ldf.columns:
                                    aba_lookup = dict(zip(
                                        ldf['ACCOUNT_DIGITS'].astype(str).str.strip(),
                                        ldf['FULL_ABA'].astype(str).str.strip()))
                                    self.log(
                                        f"Auto-loaded ABA routing lookup (Issue 21H/#75 PPCOM): "
                                        f"{len(aba_lookup)} account keys"
                                    )
                        except Exception as e:
                            self.log(f"Warning: Could not load ABA routing lookup - {e}")
                        ppach_path = find_extract('ppach')
                        if ppach_path:
                            try:
                                pdf = pd.read_csv(ppach_path, encoding='latin1', low_memory=False, dtype=str, on_bad_lines='skip').fillna("")
                                pdf.columns = [str(c).strip().upper() for c in pdf.columns]
                                if 'POLICY_NUMBER' in pdf.columns and 'E_ABA_NUM' in pdf.columns and 'E_ACCOUNT_NUMBER' in pdf.columns:
                                    if 'CHANGE_DATE' in pdf.columns and 'CHANGE_TIME' in pdf.columns:
                                        pdf = pdf.sort_values(by=['CHANGE_DATE', 'CHANGE_TIME'], ascending=[True, True])
                                        
                                    aba_recovered = 0
                                    for _, r in pdf.iterrows():
                                        pol = self.normalize(r.get('POLICY_NUMBER'))
                                        aba = str(r.get('E_ABA_NUM')).strip()
                                        if aba.endswith('.0'): aba = aba[:-2]
                                        acct = str(r.get('E_ACCOUNT_NUMBER')).strip()
                                        if acct.endswith('.0'): acct = acct[:-2]
                                        
                                        if pol and aba and acct and aba.lower() not in ['nan', 'none', ''] and acct.lower() not in ['nan', 'none', '']:
                                            acct_digits = self._issue75_usable_acct_digits(acct)
                                            if not acct_digits:
                                                continue
                                            aba_digits = self._issue75_usable_aba_digits(
                                                aba, acct_digits, aba_lookup
                                            )
                                            if not aba_digits:
                                                self._ppach_acct_meta[pol] = {
                                                    "aba": aba,
                                                    "account": acct_digits,
                                                }
                                                continue
                                            if aba_digits != re.sub(r"\D", "", aba):
                                                aba_recovered += 1
                                            mbankno = self._issue75_build_mbankno(aba_digits, acct_digits)
                                            if not mbankno:
                                                continue
                                            self._ppach_bank_map[pol] = mbankno
                                            self._ppach_acct_meta[pol] = {
                                                "aba": aba_digits,
                                                "account": acct_digits,
                                            }
                                            
                                    self.log(f"Auto-loaded PPACH Banking Cache for quikmstr ({len(self._ppach_bank_map)} records; {aba_recovered} full-ABA recoveries)")
                            except Exception as e:
                                self.log(f"Warning: Could not load PPACH cache - {e}")

                        # --- PPPAC ACCOUNT FALLBACK (Issue #45) ---
                        self._pppac_acct_only_meta = {}
                        pppac_fallback_applied = 0
                        pppac_lookup_aba = 0
                        pppac_rna_aba = 0
                        rna_aba_by_pol = {}
                        try:
                            rna_path = self._resolve_rna_source_path(src_dir)
                            if rna_path and os.path.isfile(rna_path):
                                rdf = pd.read_csv(
                                    rna_path, encoding='latin1', low_memory=False, dtype=str, on_bad_lines='skip'
                                ).fillna("")
                                rdf.columns = [str(c).strip().upper() for c in rdf.columns]
                                if 'POLICY_NUMBER' in rdf.columns:
                                    for _, rr in rdf.iterrows():
                                        rpol = self.normalize(rr.get('POLICY_NUMBER'))
                                        if not rpol:
                                            continue
                                        abas = set(rna_aba_by_pol.get(rpol, []))
                                        for aba_col in ('ELEC_ABA_NUMBER', 'PAPER_ABA_NUM'):
                                            if aba_col not in rdf.columns:
                                                continue
                                            aba_raw = str(rr.get(aba_col, '')).strip()
                                            if aba_raw.endswith('.0'):
                                                aba_raw = aba_raw[:-2]
                                            aba_d = re.sub(r'\D', '', aba_raw)
                                            if (
                                                self._issue75_aba_checksum_ok(aba_d)
                                                and not re.search(r'[xX*]{2,}', aba_raw, re.I)
                                            ):
                                                abas.add(aba_d)
                                        if abas:
                                            rna_aba_by_pol[rpol] = sorted(abas)
                        except Exception as e:
                            self.log(f"Warning: Could not load RNA ABA aid for PPPAC fallback - {e}")

                        pppac_path = find_extract('pppac')
                        if pppac_path:
                            try:
                                pacdf = pd.read_csv(
                                    pppac_path, encoding='latin1', low_memory=False, dtype=str, on_bad_lines='skip'
                                ).fillna("")
                                pacdf.columns = [str(c).strip().upper() for c in pacdf.columns]
                                if 'POLICY_NUMBER' in pacdf.columns and 'E_ACCOUNT_NUMBER' in pacdf.columns:
                                    pacdf = pacdf[~pacdf['POLICY_NUMBER'].astype(str).str.contains('---', na=False)]
                                    for _, pr in pacdf.iterrows():
                                        pol = self.normalize(pr.get('POLICY_NUMBER'))
                                        if not pol or pol in self._ppach_bank_map:
                                            continue
                                        acct_raw = str(pr.get('E_ACCOUNT_NUMBER', '')).strip()
                                        acct_digits = self._issue75_usable_acct_digits(acct_raw)
                                        if not acct_digits:
                                            continue
                                        use_aba = self._issue45_lookup_aba_for_account(acct_digits, aba_lookup)
                                        aba_src = "LOOKUP" if use_aba else ""
                                        if not use_aba:
                                            pol_abas = rna_aba_by_pol.get(pol, [])
                                            if len(pol_abas) == 1:
                                                use_aba = pol_abas[0]
                                                aba_src = "RNA"
                                                pppac_rna_aba += 1
                                            elif len(pol_abas) > 1:
                                                self._pppac_acct_only_meta[pol] = {
                                                    "account": acct_digits,
                                                    "aba_source": "RNA_AMBIGUOUS",
                                                }
                                                continue
                                        else:
                                            pppac_lookup_aba += 1
                                        if not use_aba:
                                            self._pppac_acct_only_meta[pol] = {
                                                "account": acct_digits,
                                                "aba_source": "",
                                            }
                                            continue
                                        mbankno = self._issue75_build_mbankno(use_aba, acct_digits)
                                        if not mbankno:
                                            self._pppac_acct_only_meta[pol] = {
                                                "account": acct_digits,
                                                "aba_source": aba_src,
                                            }
                                            continue
                                        self._ppach_bank_map[pol] = mbankno
                                        self._ppach_acct_meta[pol] = {
                                            "aba": use_aba,
                                            "account": acct_digits,
                                            "bank_source": "PPPAC",
                                            "aba_source": aba_src,
                                        }
                                        pppac_fallback_applied += 1
                                    self.log(
                                        f"Issue 45: PPPAC banking fallback applied for {pppac_fallback_applied} policies "
                                        f"(lookup ABA={pppac_lookup_aba}, RNA ABA={pppac_rna_aba}; "
                                        f"account-only unresolved={len(self._pppac_acct_only_meta)})"
                                    )
                            except Exception as e:
                                self.log(f"Warning: Could not load PPPAC banking fallback - {e}")
                        # ---------------------------

                        # --- POLICY FEE CACHE (Issue 21C) ---
                        self._policy_fee_map = {}
                        try:
                            fee_df = pd.read_csv(src_path, encoding='latin1', low_memory=False, dtype=str, on_bad_lines='skip').fillna("")
                            fee_df.columns = [str(c).strip().upper() for c in fee_df.columns]
                            if 'POLICY_NUMBER' in fee_df.columns and 'POLICY_FEE' in fee_df.columns:
                                for _, r in fee_df.iterrows():
                                    pol = self.normalize(r.get('POLICY_NUMBER'))
                                    fee = str(r.get('POLICY_FEE')).strip()
                                    if fee.endswith('.0'): fee = fee[:-2]
                                    if not pol or fee.lower() in ['', 'nan', 'none', 'null']:
                                        continue
                                    try:
                                        if float(fee) == 0.0:
                                            continue
                                        fee = f"{float(fee):.2f}"
                                    except ValueError:
                                        pass
                                    self._policy_fee_map[pol] = fee
                                self.log(f"Auto-loaded Policy Fee Cache for quikmstr ({len(self._policy_fee_map)} records)")
                        except Exception as e:
                            self.log(f"Warning: Could not load Policy Fee cache - {e}")
                        # ---------------------------

                        # --- Issue #49: PPBEN phase cache for active-phase MSTATUS ---
                        self._ppben_phase_cache = {}
                        self._issue49_mstatus_override_count = 0
                        self._mstatus_provisional_for_phase1_cache = {}
                        # Issue #121: LifePRO POLICY_NUMBER set for phase-1 ART plans
                        self._issue121_art_lp_policies = set()
                        self._issue121_art_guard_count = 0
                        try:
                            _ppben_i49 = resolve_ppben_path(src_dir)
                            if _ppben_i49:
                                self._ppben_phase_cache = build_ppben_phase_cache(
                                    _ppben_i49, normalize_fn=self.normalize
                                )
                                self._issue121_art_lp_policies = build_art_lifepro_policy_cache(
                                    _ppben_i49, normalize_fn=self.normalize
                                )
                                self.log(
                                    f"Auto-loaded PPBEN phase cache for Issue #49 "
                                    f"({len(self._ppben_phase_cache)} policies; {os.path.basename(_ppben_i49)})"
                                )
                                self.log(
                                    f"Issue #121: ART policy cache "
                                    f"({len(self._issue121_art_lp_policies)} policies; "
                                    f"{os.path.basename(_ppben_i49)})"
                                )
                            else:
                                self.log("Issue #49: PPBEN extract not found — active-phase MSTATUS override skipped")
                        except Exception as e:
                            self._ppben_phase_cache = {}
                            self._issue121_art_lp_policies = set()
                            self.log(f"Warning: Could not load PPBEN phase cache for Issue #49 - {e}")
                        # ---------------------------
                
                quikmstr_paid_to = {}
                if t_id.lower() == "quikdvdp":
                    try:
                        base_d = os.path.dirname(os.path.abspath(__file__))
                        parent_d = os.path.dirname(base_d)
                        search_dirs = [
                            self.path_vars["Out"][0].get(),
                            self.path_vars["Src"][0].get(),
                            base_d, parent_d
                        ]
                        
                        all_matches = []
                        for d in search_dirs:
                            if not d or not os.path.exists(d): continue
                            for root, dirs, files in os.walk(d):
                                dirs[:] = [d_ for d_ in dirs if not any(b in d_.lower() for b in ['copy', 'old', 'backup', 'archive'])]
                                for f in files:
                                    if f.lower() == 'quikmstr.csv':
                                        all_matches.append(os.path.normpath(os.path.join(root, f)))
                        
                        all_matches = sorted(all_matches, key=lambda x: 'output' not in x.lower())
                        cache_built = False
                        
                        for qm_path in all_matches:
                            qm_df = pd.read_csv(qm_path, encoding='latin1', low_memory=False, dtype=str).fillna("")
                            qm_df.columns = [str(c).strip().upper() for c in qm_df.columns]
                            
                            if 'MPOLICY' in qm_df.columns and 'MPAIDTO' in qm_df.columns:
                                qm_df['__norm_pol'] = qm_df['MPOLICY'].apply(self.normalize)
                                qm_df['MPAIDTO'] = qm_df['MPAIDTO'].astype(str).str.strip()
                                valid = qm_df[~qm_df['MPAIDTO'].isin(["", "nan", "none", "null"])]
                                quikmstr_paid_to.update(valid.set_index('__norm_pol')['MPAIDTO'].to_dict())
                                cache_built = True
                                
                            elif 'POLICY_NUMBER' in qm_df.columns and 'PAID_TO_DATE' in qm_df.columns:
                                qm_df['__norm_pol'] = qm_df['POLICY_NUMBER'].apply(lambda x: cw_map.get(self.normalize(x), self.normalize(x)))
                                qm_df['PAID_TO_DATE'] = qm_df['PAID_TO_DATE'].astype(str).str.strip()
                                valid = qm_df[~qm_df['PAID_TO_DATE'].isin(["", "nan", "none", "null"])]
                                quikmstr_paid_to.update(valid.set_index('__norm_pol')['PAID_TO_DATE'].to_dict())
                                cache_built = True
                                
                            if cache_built:
                                self.log(f"Auto-loaded MPAIDTO fallback cache from {os.path.basename(qm_path)} ({len(quikmstr_paid_to)} policies)")
                                break
                                
                        if not cache_built:
                            self.log("Warning: Could not find any quikmstr.csv to build MPAIDTO cache. MINTDATE fallback will fail.")
                    except Exception as e: 
                        self.log(f"Warning: Error loading MPAIDTO cache - {str(e)}")

                    # --- QUIKDVDP TRANSACTION CACHE ---
                    quikdvdp_tx_cache = {}
                    quikdvdp_tx_policies = set()
                    quikridr_mplan_cache = {}
                    if t_id.lower() == "quikdvdp":
                        try:
                            qr_path = os.path.normpath(os.path.join(self.path_vars["Out"][0].get(), "quikridr.csv"))
                            if os.path.exists(qr_path):
                                qr_df = pd.read_csv(qr_path, encoding='latin1', low_memory=False, dtype=str).fillna("")
                                qr_df.columns = [str(c).strip().upper() for c in qr_df.columns]
                                if 'MPOLICY' in qr_df.columns and 'MPLAN' in qr_df.columns:
                                    for _, qrow in qr_df.iterrows():
                                        pol = self.normalize(qrow.get('MPOLICY', ''))
                                        phase = self.normalize(qrow.get('MPHASE', '')) or "1"
                                        if phase == "1" and pol and pol not in quikridr_mplan_cache:
                                            quikridr_mplan_cache[pol] = self.normalize(qrow.get('MPLAN', ''))
                                    self.log(
                                        f"Auto-loaded quikridr MPLAN cache for quikdvdp MDEPINT "
                                        f"({len(quikridr_mplan_cache)} policies)"
                                    )
                        except Exception as e:
                            self.log(f"Warning: Failed to load quikridr MPLAN cache for quikdvdp - {e}")
                        try:
                            pactg_path = self._resolve_table_source_path("quikprmh", src_base)
                            if pactg_path and os.path.exists(pactg_path):
                                self.log(
                                    f"Building quikdvdp dividend-interest cache (PACTG 641) from "
                                    f"{os.path.basename(pactg_path)}..."
                                )
                                tx_df = pd.read_csv(pactg_path, encoding='latin1', low_memory=False, dtype=str, on_bad_lines='skip').fillna("")
                                tx_df.columns = [str(col).replace('\ufeff', '').strip().upper() for col in tx_df.columns]
                                
                                pol_col = 'POLN' if 'POLN' in tx_df.columns else 'POLICY_NUMBER'
                                amt_col = 'TRAMT' if 'TRAMT' in tx_df.columns else 'TRANS_AMOUNT'
                                dt_col = 'TRDATE' if 'TRDATE' in tx_df.columns else 'EFFECTIVE_DATE'
                                trcd_col = 'TRCD'
                                
                                if pol_col in tx_df.columns and amt_col in tx_df.columns:
                                    current_year = str(datetime.now().year)
                                    
                                    for _, r in tx_df.iterrows():
                                        raw_pol = self.normalize(r.get(pol_col))
                                        if not raw_pol: continue
                                        
                                        # Enterprise-safe policy normalization:
                                        # Convert LifePRO policy IDs into QLAdmin MPOLICY space
                                        pol = self.normalize(cw_map.get(raw_pol, raw_pol))
                                        # Issue #116: the crosswalk New_Value is not the emitted
                                        # MPOLICY, so register the formatted key the enrichment
                                        # below actually looks up as well.
                                        pol_keys = [k for k in (
                                            pol,
                                            self.normalize(self._format_qladmin_mpolicy(raw_pol)),
                                        ) if k]
                                        
                                        trcd = self.normalize(r.get(trcd_col))
                                        if not trcd:
                                            cc = self.normalize(r.get('CREDIT_CODE', ''))
                                            dc = self.normalize(r.get('DEBIT_CODE', ''))
                                            if cc in ['0641', '641']: trcd = cc
                                            elif dc in ['0641', '641']: trcd = dc
                                        
                                        if trcd not in ['0641', '641']:
                                            continue

                                        amt_str = str(r.get(amt_col, '0')).replace(',', '').strip()
                                        try: amt = float(amt_str) if amt_str else 0.0
                                        except: amt = 0.0
                                        
                                        date_val = str(r.get(dt_col, '')).strip()
                                        
                                        entry = next(
                                            (quikdvdp_tx_cache[k] for k in pol_keys
                                             if k in quikdvdp_tx_cache),
                                            None,
                                        )
                                        if entry is None:
                                            entry = {'MINTYTD': 0.0, 'MINTDATE': ""}
                                        for _k in pol_keys:
                                            quikdvdp_tx_cache[_k] = entry
                                        quikdvdp_tx_policies.add(raw_pol)
                                        
                                        if current_year in date_val:
                                            entry['MINTYTD'] += amt
                                        
                                        curr_max = entry['MINTDATE']
                                        if not curr_max:
                                            entry['MINTDATE'] = date_val
                                        else:
                                            try:
                                                if pd.to_datetime(date_val) > pd.to_datetime(curr_max):
                                                    entry['MINTDATE'] = date_val
                                            except:
                                                if date_val > curr_max:
                                                    entry['MINTDATE'] = date_val
                                                            
                                self.log(f"Auto-loaded quikdvdp PACTG 641 cache ({len(quikdvdp_tx_policies)} policies)")
                        except Exception as e:
                            self.log(f"Warning: Failed to build quikdvdp transaction cache - {e}")
                    # ----------------------------------

                quikridr_par_cache = {}
                quikridr_product_par_map = {}
                self._billing_mode_map = getattr(self, "_billing_mode_map", {}) or {}
                if t_id.lower() == "quikridr":
                    try:
                        ppb_path = os.path.normpath(os.path.join(os.path.dirname(src_path), "PPBENTYP.csv"))
                        if os.path.exists(ppb_path):
                            ppb_df = pd.read_csv(ppb_path, encoding='latin1', low_memory=False, dtype=str, on_bad_lines='skip').fillna("")
                            ppb_df.columns = [str(c).strip().upper() for c in ppb_df.columns]
                            if 'POLICY_NUMBER' in ppb_df.columns and 'BENEFIT_SEQ' in ppb_df.columns and 'PAR_TYPE' in ppb_df.columns:
                                for _, r in ppb_df.iterrows():
                                    pol = self.normalize(r.get('POLICY_NUMBER'))
                                    seq = self.normalize(str(r.get('BENEFIT_SEQ')).replace('.0', ''))
                                    par = str(r.get('PAR_TYPE')).strip()
                                    if pol and seq and par not in ["", "nan", "none"]:
                                        quikridr_par_cache[(pol, seq)] = par
                                self.log(f"Auto-loaded PPBENTYP PAR Cache for quikridr ({len(quikridr_par_cache)} records)")
                    except Exception as e:
                        self.log(f"Warning: Failed to load PPBENTYP cache for quikridr - {e}")
                    # Issue #105: product participating (quikplan.PAR by MPLAN) is MPAR authority
                    try:
                        _qp_out = os.path.normpath(
                            os.path.join(self.path_vars["Out"][0].get().strip() or self._migration_output_dir(), "quikplan.csv")
                        )
                        if os.path.exists(_qp_out):
                            _qpdf = pd.read_csv(_qp_out, encoding="latin1", low_memory=False, dtype=str, on_bad_lines="skip").fillna("")
                            _qpdf.columns = [str(c).strip().upper() for c in _qpdf.columns]
                            if "PLAN" in _qpdf.columns and "PAR" in _qpdf.columns:
                                for _, r in _qpdf.iterrows():
                                    _pl = self.normalize(r.get("PLAN"))
                                    _pr = self.normalize(r.get("PAR"))
                                    if _pl and _pr in ("0", "1"):
                                        quikridr_product_par_map[_pl] = _pr
                                self.log(
                                    f"Issue #105: loaded product PAR map for quikridr MPAR "
                                    f"({len(quikridr_product_par_map)} plans)"
                                )
                            else:
                                self.log("Issue #105: quikplan.csv missing PLAN/PAR — MPAR defaults to 0")
                        else:
                            self.log("Issue #105: quikplan.csv not found — MPAR defaults to 0")
                    except Exception as e:
                        self.log(f"Warning: Issue #105 product PAR map failed - {e}")
                    # Issue #88/#137: PPOLC BILLING_MODE/FORM for Prem/Unit fallback
                    # Issue #89: POLICY_FEE cache on quikridr path (ridr-only rebatch must not wipe MANNLFEE)
                    try:
                        self._billing_mode_map = {}
                        self._billing_form_map = {}
                        self._policy_fee_map = {}
                        self._modal_factor_map = load_modal_factor_mapping()
                        self._issue137_modal_mprem = 0
                        self._issue137_crude_mprem = 0
                        _src_dir_i88 = os.path.dirname(src_path)
                        _ppolc_i88 = None
                        for _fn in os.listdir(_src_dir_i88):
                            if (
                                "ppolc" in _fn.lower()
                                and _fn.lower().endswith(".csv")
                                and not any(bad in _fn.lower() for bad in ("copy", "old", "backup", "archive"))
                            ):
                                _cand = os.path.normpath(os.path.join(_src_dir_i88, _fn))
                                if _ppolc_i88 is None or os.path.getmtime(_cand) > os.path.getmtime(_ppolc_i88):
                                    _ppolc_i88 = _cand
                        if _ppolc_i88:
                            _pmdf = pd.read_csv(
                                _ppolc_i88, encoding="latin1", low_memory=False, dtype=str, on_bad_lines="skip"
                            ).fillna("")
                            _pmdf.columns = [str(c).strip().upper() for c in _pmdf.columns]
                            if "POLICY_NUMBER" in _pmdf.columns:
                                _has_billing = "BILLING_MODE" in _pmdf.columns
                                _has_bill_form = "BILLING_FORM" in _pmdf.columns
                                _has_policy_fee = "POLICY_FEE" in _pmdf.columns
                                for _, _pr in _pmdf.iterrows():
                                    _pol = self.normalize(_pr.get("POLICY_NUMBER"))
                                    if not _pol:
                                        continue
                                    if _has_billing:
                                        _bm = str(_pr.get("BILLING_MODE", "")).strip()
                                        if _bm.endswith(".0"):
                                            _bm = _bm[:-2]
                                        if _bm.lower() not in ("", "nan", "none", "null"):
                                            try:
                                                self._billing_mode_map[_pol] = int(float(_bm))
                                            except (ValueError, TypeError):
                                                pass
                                    if _has_bill_form:
                                        _bf = str(_pr.get("BILLING_FORM", "")).strip()
                                        if _bf and _bf.lower() not in ("nan", "none", "null"):
                                            self._billing_form_map[_pol] = _bf
                                    if _has_policy_fee:
                                        _fee = str(_pr.get("POLICY_FEE", "")).strip()
                                        if _fee.endswith(".0"):
                                            _fee = _fee[:-2]
                                        if not _fee or _fee.lower() in ("", "nan", "none", "null"):
                                            continue
                                        try:
                                            if float(_fee) == 0.0:
                                                continue
                                            _fee = f"{float(_fee):.2f}"
                                        except ValueError:
                                            pass
                                        self._policy_fee_map[_pol] = _fee
                                if _has_billing:
                                    self.log(
                                        f"Issue #88/#137: loaded PPOLC BILLING_MODE cache "
                                        f"({len(self._billing_mode_map)} policies; {os.path.basename(_ppolc_i88)})"
                                    )
                                if _has_bill_form:
                                    self.log(
                                        f"Issue #137: loaded PPOLC BILLING_FORM cache "
                                        f"({len(self._billing_form_map)} policies)"
                                    )
                                if self._modal_factor_map:
                                    self.log(
                                        f"Issue #137: loaded modal factor map "
                                        f"({len(self._modal_factor_map)} plans) for blank-ANN MPREM"
                                    )
                                if _has_policy_fee:
                                    self.log(
                                        f"Issue #89: loaded Policy Fee cache for quikridr "
                                        f"({len(self._policy_fee_map)} records; {os.path.basename(_ppolc_i88)})"
                                    )
                    except Exception as e:
                        self.log(f"Warning: Issue #88/#89/#137 PPOLC cache failed - {e}")
                        self._billing_mode_map = {}
                        self._billing_form_map = {}
                        self._policy_fee_map = {}
                        self._modal_factor_map = {}

                quikagts_clnt_cache = {}
                if t_id.lower() == "quikagts":
                    try:
                        qc_path = os.path.normpath(os.path.join(self.path_vars["Out"][0].get(), "quikclnt.csv"))
                        if os.path.exists(qc_path):
                            qc_df = pd.read_csv(qc_path, encoding='latin1', low_memory=False, dtype=str).fillna("")
                            qc_df.columns = [str(c).strip().upper() for c in qc_df.columns]
                            if 'MCLIENTID' in qc_df.columns:
                                qc_df['__norm_cid'] = qc_df['MCLIENTID'].apply(self.normalize)
                                quikagts_clnt_cache = qc_df.drop_duplicates(subset=['__norm_cid'], keep='first').set_index('__norm_cid').to_dict('index')
                                self.log(f"Auto-loaded quikclnt cache for quikagts ({len(quikagts_clnt_cache)} records)")
                        else:
                            self.log("Warning: quikclnt.csv not found in Output. quikagts enrichment will be incomplete.")
                    except Exception as e:
                        self.log(f"Warning: Failed to load quikclnt cache for quikagts - {e}")

                if t_id.lower() == "quikridr":
                    mplan_trace_rows = []
                    mplan_src_file = os.path.basename(src_input) if src_input else "PPBEN.csv"
                    if self._closed_mplan_authority_enabled() and mplan_resolver is None:
                        out_dir_preview = self.path_vars["Out"][0].get()
                        mplan_resolver, quikplan_plan_set, _ = self._init_mplan_authority(out_dir_preview, cw_path)
                    # Issue #21E: build UL fund-balance cache BEFORE FV rows are filtered out.
                    ul_fund_balance_cache = {}
                    ul_fund_mcv0_count = 0
                    try:
                        _ppben_for_fv = resolve_ppben_path(os.path.dirname(src_path)) or src_path
                        ul_fund_balance_cache = build_ul_fund_balance_cache(
                            _ppben_for_fv, normalize_fn=self.normalize
                        )
                        if ul_fund_balance_cache:
                            self.log(
                                f"Issue #21E: UL fund-balance cache loaded "
                                f"({len(ul_fund_balance_cache)} policies from FV_BALANCE2)"
                            )
                    except Exception as e:
                        self.log(f"Warning: Issue #21E UL fund-balance cache failed - {e}")
                        ul_fund_balance_cache = {}
                    if 'BENEFIT_TYPE' in source.columns:
                        _qr_bt = source['BENEFIT_TYPE'].astype(str).str.strip().str.upper()
                        _qr_uv_removed = int((_qr_bt == 'UV').sum())
                        _qr_fv_removed = int((_qr_bt == 'FV').sum())
                        _qr_sl_removed = 0
                        if (_qr_bt == SL_BENEFIT_TYPE).any():
                            _ppb_sl_path = resolve_ppbentyp_path(os.path.dirname(src_path))
                            _sl_table_cache = load_sl_table_code_cache(
                                _ppb_sl_path, normalize_fn=self.normalize
                            )
                            _sl_audit_rows = build_sl_suppression_audit_rows(
                                source.loc[_qr_bt == SL_BENEFIT_TYPE],
                                sl_table_cache=_sl_table_cache,
                                cw_map=cw_map,
                                normalize_fn=self.normalize,
                            )
                            _sl_audit_path = write_sl_suppression_audit(_sl_audit_rows)
                            _qr_sl_removed = len(_sl_audit_rows)
                            self.log(
                                f"Issue #27 SL SUPPRESSION: Audited {_qr_sl_removed} rows → {_sl_audit_path}"
                            )
                        source = source[~_qr_bt.isin(['UV', 'FV', SL_BENEFIT_TYPE])]
                        self.log(
                            f"QUIKRIDR BENEFIT TYPE FILTER: Removed "
                            f"{_qr_uv_removed + _qr_fv_removed + _qr_sl_removed} UV/FV/SL rows from PPBEN source."
                        )
                        self.log(f"Remaining PPBEN rows for QUIKRIDR: {len(source)}")
                    if 'BENEFIT_SEQ' in source.columns:
                        source['BENEFIT_SEQ'] = source['BENEFIT_SEQ'].astype(str).str.strip().str.replace(".0", "", regex=False)
                        source = source[source['BENEFIT_SEQ'].apply(
                            lambda x: x.isdigit() and int(x) >= 1
                        )]
                elif t_id.lower() == "quikdvdp":
                    if 'BENEFIT_SEQ' in source.columns:
                        source['BENEFIT_SEQ'] = source['BENEFIT_SEQ'].astype(str).str.strip().str.replace(".0", "", regex=False)
                        source = source[source['BENEFIT_SEQ'].isin(["1", "01"])]
                elif t_id.lower() == "quikclnt":
                    if 'CANCEL_DATE' in source.columns:
                        source = source[source['CANCEL_DATE'].apply(self._is_active_rna_cancel_date)]
                    if 'NAME_ID' in source.columns:
                        source = self._bridge_rna_quikclnt_columns(source)
                        source = self._dedupe_quikclnt_rna_source(source)
                        self.log("RNA column bridge applied for quikclnt (ADDR/DOB/SEX/TAX LifePRO aliases)")
                    
                    # --- NEW SOURCE DIAGNOSTICS ---
                    self.log(f"DEBUG SOURCE: 'NAME_ID' in columns? {'NAME_ID' in source.columns}")
                    self.log(f"DEBUG SOURCE: First 25 columns: {list(source.columns)[:25]}")
                    
                    diag_cols = ['POLICY_NUMBER', 'NAME_ID', 'CLIENT_ID', 'ADDRESS_ID']
                    diag_cols.extend([c for c in source.columns if any(k in c for k in ['NAME', 'CLIENT', 'PARTY', 'PERSON', 'RELATION'])])
                    
                    # Deduplicate and keep only columns that actually exist in the dataframe
                    diag_cols = list(dict.fromkeys([c for c in diag_cols if c in source.columns]))
                    
                    for row_idx, s_row in enumerate(source.head(5).to_dict('records')):
                        diag_vals = {c: s_row.get(c, '') for c in diag_cols}
                        self.log(f"DEBUG SOURCE ROW {row_idx + 1}: {diag_vals}")
                    # ------------------------------
                    
                elif t_id.lower() == "quikbenf":
                    if 'RELATE_CODE' in source.columns:
                        source['RELATE_CODE'] = source['RELATE_CODE'].apply(self.normalize)
                        source = source[source['RELATE_CODE'].isin(['B1', 'B2', 'P', 'C'])]
                        
                elif t_id.lower() == "quikplan":
                    source = prepare_quikplan_source(source)

                elif t_id.lower() == "quikdvpr":
                    credit_match = pd.Series(False, index=source.index)
                    debit_match = pd.Series(False, index=source.index)
                    
                    if 'CREDIT_CODE' in source.columns:
                        source['CREDIT_CODE'] = source['CREDIT_CODE'].apply(self.normalize)
                        credit_match = source['CREDIT_CODE'].isin(['516', '0516'])
                        
                    if 'DEBIT_CODE' in source.columns:
                        source['DEBIT_CODE'] = source['DEBIT_CODE'].apply(self.normalize)
                        debit_match = source['DEBIT_CODE'].isin(['516', '0516'])
                        
                    if 'CREDIT_CODE' in source.columns or 'DEBIT_CODE' in source.columns:
                        source = source[credit_match | debit_match]

                schema = self.TABLE_SCHEMAS.get(t_id.lower())
                if not schema:
                    if 'Target_Field' in rules.columns:
                        schema = list(rules['Target_Field'].unique())
                    else:
                        self.log(f"!!! CRITICAL: 'Target_Field' header is completely missing in your Rulebook.")
                        continue

                if t_id.lower() == "quikplan":
                    out_dir = self.path_vars["Out"][0].get()
                    overlay_cfg = resolve_crosswalk_overlay_config()
                    cw_authority = load_crosswalk_authority(cw_path) if cw_path and os.path.exists(cw_path) else None
                    var_cfg = VariationClassificationConfig.from_env_and_defaults(self._app_base_dir())
                    audit_rows = classify_all_plans(var_cfg)
                    audit_path = os.path.normpath(os.path.join(self._reports_dir(), "variation_code_audit.csv"))
                    write_variation_audit_csv(audit_rows, audit_path)
                    self.log(f"Variation audit: {audit_path} ({len(audit_rows)} plans, "
                             f"auto_apply={'Y' if var_cfg.auto_apply_variation_codes else 'N'})")
                    variation_recs = recommendations_by_plan(audit_rows)
                    output = convert_quikplan_to_output(
                        source, rules, lookups, trans_map, cw_map, schema, overlay_cfg, cw_authority,
                        variation_recs, var_cfg.auto_apply_variation_codes,
                    )
                    qdf = pd.DataFrame(output, columns=schema)
                    # Issue #70: audit blank/unknown LOAN_ADV_ARREARS → A fallback
                    _loanintx_qa = getattr(convert_quikplan_to_output, "last_loanintx_qa", None) or {}
                    _fb = int(_loanintx_qa.get("fallback_count", 0) or 0)
                    if _fb:
                        self.log(
                            f"Issue #70 LOANINTX: {_fb} plan(s) used A fallback "
                            f"(blank/unknown LOAN_ADV_ARREARS); see convert audit."
                        )
                    if "LOANINTX" in qdf.columns:
                        _a = int((qdf["LOANINTX"].astype(str).str.strip().str.upper() == "A").sum())
                        _r = int((qdf["LOANINTX"].astype(str).str.strip().str.upper() == "R").sum())
                        self.log(f"Issue #70 LOANINTX emit: A={_a} R={_r}")
                    qdf = apply_rate_variation_flag_enrichment(qdf, self._app_base_dir())
                    qdf = apply_single_premium_payment_settings(qdf, self._app_base_dir(), log=self.log)
                    current_stage = "Applying rulebooks and crosswalks"
                    self.update_run_progress(4, detail="plan/rate enrichments + CSO assumptions")
                    self.log(f"Rate variation flags applied (R7B): {int((qdf['PLANVALOPT'] == 'Y').sum())} plans PLANVALOPT=Y")

                    cso_path = default_crosswalk_path(self._app_base_dir())
                    cso_resolver = load_cso_mortality_crosswalk(cso_path)
                    if cso_resolver.plans_loaded:
                        cso_qa = apply_quikplan_cv_assumptions(qdf, cso_resolver, log=self.log)
                        self.log(
                            f"CSO crosswalk (CV assumptions): loaded={cso_qa['plans_loaded']} "
                            f"matched={cso_qa['plans_matched']} missing={cso_qa['plans_missing']} "
                            f"review_flagged={cso_qa['plans_with_review_flag']} "
                            f"NFOINT/INTMETHCV cells updated={cso_qa['cells_updated']} "
                            f"(overwrites={cso_qa['cells_overwritten']})"
                        )
                        cso_qa_path = os.path.normpath(os.path.join(self._reports_dir(), "cso_mortality_crosswalk_qa.csv"))
                        with open(cso_qa_path, "w", newline="", encoding="utf-8") as f:
                            w = csv.writer(f)
                            w.writerow(["METRIC", "VALUE"])
                            for k in ("plans_loaded", "plans_matched", "plans_missing",
                                      "plans_using_default", "plans_with_review_flag",
                                      "cells_updated", "cells_overwritten", "blank_values_preserved"):
                                w.writerow([k, cso_qa.get(k, "")])
                            w.writerow(["missing_plan_codes", ";".join(cso_qa.get("missing_plan_codes", []))])
                            w.writerow(["review_flag_plan_codes", ";".join(cso_qa.get("review_flag_plan_codes", []))])
                            w.writerow([])
                            w.writerow(["PLAN", "FIELD", "OLD_VALUE", "NEW_VALUE"])
                            for d in cso_qa.get("diffs", []):
                                w.writerow([d["PLAN"], d["FIELD"], d["OLD"], d["NEW"]])
                        self.log(f"CSO crosswalk QA: {cso_qa_path}")
                    else:
                        self.log(f"CSO crosswalk not found at {cso_path}; quikplan CV assumptions left as-is.")

                    vs_path = default_valuation_setup_path(self._app_base_dir())
                    vs_resolver = load_valuation_setup(vs_path)
                    if vs_resolver.plans_loaded:
                        vs_qa = apply_quikplan_valuation_setup(qdf, vs_resolver, log=self.log)
                        vs_qa_path = os.path.normpath(
                            os.path.join(self._app_base_dir(), "QLA_Migration", "Reports",
                                         "cso_valuation_setup_quikplan_qa.csv")
                        )
                        os.makedirs(os.path.dirname(vs_qa_path), exist_ok=True)
                        with open(vs_qa_path, "w", newline="", encoding="utf-8") as f:
                            w = csv.writer(f)
                            w.writerow(["METRIC", "VALUE"])
                            for k in ("plans_loaded", "cells_updated", "cells_overwritten"):
                                w.writerow([k, vs_qa.get(k, "")])
                            w.writerow([])
                            w.writerow(["PLAN", "FIELD", "OLD_VALUE", "NEW_VALUE"])
                            for d in vs_qa.get("diffs", []):
                                w.writerow([d["PLAN"], d["FIELD"], d["OLD"], d["NEW"]])
                        self.log(f"CSO Valuation Setup QA: {vs_qa_path}")
                    else:
                        self.log(f"CSO Valuation Setup not found at {vs_path}; skipped quikplan overlay.")

                    qdf = apply_ploan_loanint_enrichment(
                        qdf,
                        repo_root=self._app_base_dir(),
                        crosswalk_path=cw_path if cw_path and os.path.exists(cw_path) else None,
                        log=self.log,
                    )

                    qdf, modal_stats = apply_issue21j_modal_factors(qdf, repo_root=self._app_base_dir())
                    self.log(
                        f"Issue 21J: modal premium factors applied to quikplan "
                        f"(updated={modal_stats.get('plans_updated', 0)}, "
                        f"mapping={modal_stats.get('plans_in_mapping', 0)})"
                    )
                    qdf = apply_single_premium_payment_settings(
                        qdf, self._app_base_dir(), log=self.log
                    )
                    qdf = apply_issue_a_plan_setup(qdf, repo_root=self._app_base_dir(), log=self.log)
                    qdf = apply_iswl_product_tags(qdf, log=self.log)
                    # Issue #70: final batch path must restore source-confirmed
                    # arrears after every later normalization/enrichment.
                    qdf = _restore_authoritative_loanintx_from_source(qdf, source)

                    output = qdf[schema].values.tolist()
                    bank_draft_exceptions = None
                else:
                    output = []
                    bank_draft_exceptions = [] if t_id.lower() == "quikmstr" else None
                    nfo_status_exceptions = [] if t_id.lower() == "quikmstr" else None
                    # Safe defaults when table is not quikridr (Issue #21E vars set in quikridr branch).
                    if t_id.lower() != "quikridr":
                        ul_fund_balance_cache = {}
                        ul_fund_mcv0_count = 0
                    base_phase_cache = {} if t_id.lower() == "quikridr" else None
                    pua_pending_rows = [] if t_id.lower() == "quikridr" else None
                    quikridr_valuation_date = datetime.now().date() if t_id.lower() == "quikridr" else None
                    quikridr_mphdob_fix_count = 0
                    if t_id.lower() == "quikridr":
                        self._issue76_payup_adjust_count = 0
                    if quikridr_valuation_date is not None:
                        _vd_env = os.environ.get("QLA_VALUATION_DATE", "").strip()
                        _vd_src = "conversion run date"
                        if _vd_env:
                            _digits = re.sub(r"[^0-9]", "", _vd_env)[:8]
                            if len(_digits) == 8:
                                try:
                                    quikridr_valuation_date = datetime.strptime(_digits, "%Y%m%d").date()
                                    _vd_src = f"QLA_VALUATION_DATE={_digits}"
                                except ValueError:
                                    self.log(
                                        f"QUIKRIDR MLASTANN WARNING: invalid QLA_VALUATION_DATE={_vd_env!r}; "
                                        f"using conversion run date"
                                    )
                        self.log(
                            f"QUIKRIDR MLASTANN: valuation date {quikridr_valuation_date.strftime('%Y%m%d')} "
                            f"({_vd_src}); issue source PPBEN.ISSUE_DATE -> MEFFDATE"
                        )
                    for i, src_row in source.iterrows():
                        if any("---" in str(v) for v in src_row.values[:3]): continue
                        
                        row_data = {h: "" for h in schema}
                        source_plan_code = self.normalize(src_row.get("PLAN_CODE", "")) if t_id.lower() == "quikridr" else ""
                        mplan_resolution = None
                        for _, rule in rules.iterrows():
                            s_f = str(rule.get('Source_Field', '')).strip().upper()
                            t_f = str(rule.get('Target_Field', '')).strip().upper()
                            lt = str(rule.get('Lookup_Table', '')).strip() if 'Lookup_Table' in rule else ""
                            jk = str(rule.get('Join_Key', '')).strip().upper() if 'Join_Key' in rule else ""
                            
                            if s_f in ['NAN', 'NONE', 'NULL']: s_f = ""
                            if t_f in ['NAN', 'NONE', 'NULL']: t_f = ""
                            
                            note = ""
                            if 'Transformation_Note' in rule and pd.notna(rule['Transformation_Note']): note = str(rule['Transformation_Note']).strip().upper()
                            elif 'Notes' in rule and pd.notna(rule['Notes']): note = str(rule['Notes']).strip().upper()
                            
                            if t_f in [h.upper() for h in schema]:
                                actual_h = [h for h in schema if h.upper() == t_f][0]
                                
                                val = ""
                                if lt and jk and lt in lookups and jk in lookups[lt]:
                                    join_val = self.normalize(src_row.get(jk))
                                    if join_val in lookups[lt][jk]:
                                        val = self.normalize(lookups[lt][jk][join_val].get(s_f, ""))
                                    else:
                                        val = self.normalize(rule.get('Default_Value', ''))
                                else:
                                    default_val = str(rule.get('Default_Value', '')).strip()
                                    if not s_f and default_val and default_val.lower() not in ['nan', 'none']:
                                        val = self.normalize(default_val)
                                    else:
                                        val = self.normalize(src_row.get(s_f)) if (s_f and s_f in source.columns) else (self.normalize(src_row.get(t_f)) if t_f in source.columns else self.normalize(default_val))
                                
                                if not val:
                                    val = self.normalize(rule.get('Default_Value', ''))
    
                                if t_id.lower() == "quikmstr" and t_f == "MBANKNO":
                                    raw_pol = self.normalize(src_row.get("POLICY_NUMBER", src_row.get("MPOLICY", "")))
                                    pulled_bank = getattr(self, '_ppach_bank_map', {}).get(raw_pol)
                                    if pulled_bank:
                                        val = pulled_bank
    
                                if t_id.lower() == "quikridr" and t_f == "MPAR":
                                    # Issue #105: MPAR = product quikplan.PAR for this row's MPLAN
                                    mplan_key = self.normalize(row_data.get("MPLAN", ""))
                                    product_par = quikridr_product_par_map.get(mplan_key)
                                    val = product_par if product_par in ("0", "1") else "0"
    
                                # --- POLICY FEE -> MANNLFEE (Issue 21C, base-coverage row only) ---
                                if t_id.lower() == "quikridr" and t_f == "MANNLFEE":
                                    seq_key = self.normalize(src_row.get("BENEFIT_SEQ", ""))
                                    if seq_key in ["1", "01"]:
                                        pol_key = self.normalize(src_row.get("POLICY_NUMBER", ""))
                                        pulled_fee = getattr(self, '_policy_fee_map', {}).get(pol_key)
                                        if pulled_fee:
                                            val = pulled_fee
                                # -----------------------------------------------------------------

                                # --- Issue 26/88/137: ANN -> MPREM; blank => modalized MODE / factor / units ---
                                if t_id.lower() == "quikridr" and t_f == "MPREM":
                                    try:
                                        ann_num = float(str(val).replace(",", "").strip() or 0)
                                    except (ValueError, TypeError):
                                        ann_num = 0.0
                                    if ann_num == 0.0:
                                        # Issue #88/#137: never load full MODE_PREMIUM into Prem/Unit
                                        try:
                                            mode_prem = float(
                                                str(src_row.get("MODE_PREMIUM", "")).replace(",", "").strip() or 0
                                            )
                                        except (ValueError, TypeError):
                                            mode_prem = 0.0
                                        try:
                                            units = float(
                                                str(src_row.get("NUMBER_OF_UNITS", "")).replace(",", "").strip() or 0
                                            )
                                        except (ValueError, TypeError):
                                            units = 0.0
                                        if units > 0.0:
                                            pol_key = self.normalize(src_row.get("POLICY_NUMBER", ""))
                                            bill_mode = getattr(self, "_billing_mode_map", {}).get(pol_key)
                                            bill_form = getattr(self, "_billing_form_map", {}).get(pol_key, "")
                                            mplan_key = self.normalize(row_data.get("MPLAN", ""))
                                            plan_factors = getattr(self, "_modal_factor_map", {}).get(mplan_key)
                                            annual_ppu, _mprem_method = blank_ann_annual_ppu(
                                                mode_prem,
                                                units,
                                                bill_mode,
                                                bill_form,
                                                plan_factors,
                                            )
                                            if _mprem_method == "modal":
                                                self._issue137_modal_mprem = (
                                                    getattr(self, "_issue137_modal_mprem", 0) + 1
                                                )
                                            else:
                                                self._issue137_crude_mprem = (
                                                    getattr(self, "_issue137_crude_mprem", 0) + 1
                                                )
                                            val = format_mprem_ppu(annual_ppu)
                                        else:
                                            val = ""
                                # -----------------------------------------------------------------
    
                                # --- MSTATUS COMPOSITE KEY INTERCEPTOR (Issue #13: T wins; Issue #59 scoped) ---
                                if t_f == 'MSTATUS' and t_id.lower() == "quikmstr":
                                    c_code = self.normalize(src_row.get('CONTRACT_CODE', val))
                                    c_reason = self.normalize(src_row.get('CONTRACT_REASON', ''))
                                    put = self.normalize(src_row.get('PAID_UP_TYPE', ''))
                                    # Issue #59: only the 7 client-cited policies may take the new branches
                                    _i59_lp = self.normalize(src_row.get('POLICY_NUMBER', ''))
                                    _i59_ql = self.normalize(row_data.get('MPOLICY', ''))
                                    _i59_keys = {
                                        '901122D991', '901122D991C', '01122D991C',
                                        '9014FG8217', '9014FG8217C', '014FG8217C',
                                        '9016FG8217', '9016FG8217C', '016FG8217C',
                                        '901ML8171', '901ML8171C', '01ML8171C', '01ML8171',
                                        '901ML8250', '901ML8250C', '01ML8250C',
                                        '901ML8522', '901ML8522C', '01ML8522C',
                                        '9010521213', '9010521213C', '010521213C',
                                    }
                                    _i59 = (_i59_lp in _i59_keys) or (_i59_ql in _i59_keys)
                                    if c_code == 'T':
                                        val = f"{c_code}_{c_reason}" if c_reason else f"{c_code}_"
                                    elif _i59 and c_code == 'S':
                                        # Death Claim Pending / Suspended reason wins over PUT
                                        val = f"{c_code}_{c_reason}" if c_reason else f"{c_code}_"
                                    elif _i59 and c_code == 'A' and put == 'LP':
                                        # Active contract: do not emit Lapsed via PUT_LP
                                        val = 'A_'
                                    elif put in ['PU', 'RU', 'ET', 'LE', 'LP', 'SP']:
                                        # Issue #121: ART (Annual Renewable Term) must not become ETI
                                        # via PUT_LE / PUT_ET → 44. Use contract key instead.
                                        _art_keys = getattr(self, "_issue121_art_lp_policies", None) or set()
                                        _art_lp = self.normalize(src_row.get('POLICY_NUMBER', ''))
                                        if should_suppress_art_put_nfo(put, _art_lp in _art_keys):
                                            val = f"{c_code}_{c_reason}" if c_reason else f"{c_code}_"
                                            self._issue121_art_guard_count = (
                                                getattr(self, "_issue121_art_guard_count", 0) + 1
                                            )
                                        else:
                                            val = f"PUT_{put}"
                                    else:
                                        val = f"{c_code}_{c_reason}" if c_reason else f"{c_code}_"
                                # -----------------------------------------

                                # --- DG-QUIKMSTR-011: MBILLDAY blank/0 → day of issue date (MISSDT) ---
                                if t_id.lower() == "quikmstr" and t_f == "MBILLDAY":
                                    from qla_core.policy_data_transforms import (
                                        apply_mbillday_from_issue_date,
                                        record_policy_transform,
                                    )
                                    bill_day = self.normalize(val)
                                    issue_raw = (
                                        src_row.get("ISSUE_DATE")
                                        or src_row.get("ISSUE_DT")
                                        or row_data.get("MISSDT")
                                        or src_row.get("MISSDT")
                                        or ""
                                    )
                                    new_day, changed = apply_mbillday_from_issue_date(
                                        bill_day, issue_raw
                                    )
                                    if changed:
                                        record_policy_transform(
                                            table="QuikMstr",
                                            record_id=self.normalize(
                                                row_data.get("MPOLICY", "")
                                            ),
                                            field="MBILLDAY",
                                            original=bill_day,
                                            converted=new_day,
                                            reason="Derived from issue date",
                                            rule_id="DG-QUIKMSTR-011",
                                        )
                                        val = new_day
                                # -----------------------------------------------------------------
    
                                if t_f in ['MNFOPT', 'MDIVOPT'] and val in ["", "0", "0.0"] and t_id.lower() == "quikmstr":
                                    pol_id = self.normalize(row_data.get('MPOLICY', ''))
                                    # Issue #108F: the PPBENTYP caches are keyed on the raw
                                    # PPBENTYP.POLICY_NUMBER. Since Issue #2 (v58.29) MPOLICY is
                                    # source + C, so resolving through the retired crosswalk matched
                                    # nothing and the election was dropped fleet-wide. Try the source
                                    # key first, keeping the crosswalk paths as fallbacks.
                                    src_pol_id = self.normalize(src_row.get('POLICY_NUMBER', src_row.get('MPOLICY', src_row.get('POLICY_ID', ''))))

                                    if not pol_id:
                                        pol_id = cw_map.get(src_pol_id, src_pol_id)
                                        
                                    legacy_id = reverse_cw_map.get(pol_id, pol_id) 
    
                                    if t_f == 'MNFOPT' and 'NON_FORFEITURE' in lifepro_extra:
                                        _nfo_cache = lifepro_extra['NON_FORFEITURE']
                                        pulled_val = _nfo_cache.get(src_pol_id)
                                        if pulled_val is None: pulled_val = _nfo_cache.get(legacy_id)
                                        if pulled_val is None: pulled_val = _nfo_cache.get(pol_id, val)
                                        val = self.normalize(pulled_val)
                                        
                                    elif t_f == 'MDIVOPT' and 'DIVIDEND' in lifepro_extra:
                                        # Issue #110: same key repoint as MNFOPT above.
                                        _dv_cache = lifepro_extra['DIVIDEND']
                                        pulled_val = _dv_cache.get(src_pol_id)
                                        if pulled_val is None: pulled_val = _dv_cache.get(legacy_id)
                                        if pulled_val is None: pulled_val = _dv_cache.get(pol_id, val)
                                        val = self.normalize(pulled_val)
    
                                if note == "EXTRACT_DAY": val = self.extract_day(val)
                                elif note == "ROUTE_PAY_YRS":
                                    c_type = str(src_row.get('PREM_CEASE_TYPE', '')).strip().upper()
                                    val = val if c_type == 'D' else '0'
                                elif note == "ROUTE_PAY_AGE":
                                    c_type = str(src_row.get('PREM_CEASE_TYPE', '')).strip().upper()
                                    val = val if c_type == 'A' else '0'
                                elif note == "ROUTE_INS_YRS":
                                    c_type = str(src_row.get('BENEFIT_CEASE_TYPE', '')).strip().upper()
                                    val = val if c_type == 'D' else '0'
                                elif note == "ROUTE_INS_AGE":
                                    c_type = str(src_row.get('BENEFIT_CEASE_TYPE', '')).strip().upper()
                                    val = val if c_type == 'A' else '0'
                                elif t_id.lower() == "quikprmh" and note == "DERIVE_PRMH_RENEWAL":
                                    p_code = self.normalize(src_row.get("PAYMENT_CODE", ""))
                                    p_reason = self.normalize(src_row.get("PAYMENT_REASON", ""))
                                    loan_amt = self.normalize(src_row.get("LOAN_REPMT_AMOUNT", ""))
    
                                    if loan_amt and loan_amt not in ["0", "0.00", ".00"]:
                                        val = "L"
                                    elif p_code == "S":
                                        val = "S"
                                    elif p_code in ["A", "R"]:
                                        val = "2"
                                    elif p_reason in ["PC", "PREM"]:
                                        val = "1"
                                    else:
                                        val = "0"
                                elif t_id.lower() == "quikprmh" and note == "DERIVE_MODE_COUNT":
                                    bill_mode = self.normalize(src_row.get("BILLING_MODE", ""))
                                    mode_count_map = {
                                        "12": "1",
                                        "6": "2",
                                        "3": "4",
                                        "1": "12"
                                    }
                                    val = mode_count_map.get(bill_mode, "0")
                                elif t_id.lower() == "quikprmh" and note == "FORMAT_MONEY":
                                    try:
                                        val = f"{float(str(val).replace(',', '').strip() or 0):.2f}"
                                    except Exception:
                                        val = "0.00"
                                elif t_id.lower() == "quikbenf" and note == "DERIVE_BENF_TYPE":
                                    norm_val = self.normalize(val)
                                    if norm_val in ["B1", "P"]:
                                        val = "P"
                                    elif norm_val in ["B2", "C"]:
                                        val = "C"
                                    else:
                                        val = ""
                                
                                if any(k in t_f for k in ['AGE', 'DUR', 'YRS']) and 'VAL' not in t_f and 'VPU' not in t_f and 'PREM' not in t_f:
                                    if val.isdigit() and len(val) == 1:
                                        val = val.zfill(2)
                                
                                # --- ENTERPRISE DATE SANITIZER (v57.26: handle LifePRO 18000101 sentinel) ---
                                if t_f in ['MDOB']:
                                    _d = re.sub(r'[^0-9]', '', str(val).strip())
                                    # Accept dates >= 19000101; treat 18000101 (LifePRO "unknown" sentinel) as blank
                                    if len(_d) == 8:
                                        if _d == "18000101":
                                            val = ""  # LifePRO sentinel for unknown DOB → blank
                                        elif _d >= "19000101":
                                            val = _d
                                        else:
                                            val = ""
                                    else:
                                        val = ""
                                # ---------------------------------

                                # --- QUIKRIDR HIGH-DATE CEILING (v57.14) ---
                                # QLAdmin valuation =>DATE returns NIL for year >= 2100
                                # (e.g. 21000302 maturity sentinels, 9999 high-date). Cap
                                # expiry/pay-up dates to the platform high-date 20991231.
                                if t_id.lower() == "quikridr" and t_f in ['MEXPRY', 'MPAYUP']:
                                    _hd = re.sub(r'[^0-9]', '', str(val))
                                    if len(_hd) == 8 and _hd[:4].isdigit() and int(_hd[:4]) >= 2100:
                                        val = "20991231"
                                # -------------------------------------------
                                
                                # --- QUIKCLNT NAME OVERRIDES & SHIELD ---
                                if t_f in ['MFNAME', 'MMNAME', 'MLNAME']:
                                    source_row = src_row
                                    # Safely bridge MCLIENTID to NAME_ID lookup
                                    raw_name_id = src_row.get('MCLIENTID', src_row.get('NAME_ID', ''))
                                    norm_name_id = self.normalize(raw_name_id)
                                    cache_matched = False
                                    
                                    if 'INDIVIDUAL_FIRST' not in src_row and rel_name_cache:
                                        if norm_name_id in rel_name_cache:
                                            source_row = rel_name_cache[norm_name_id]
                                            cache_matched = True
                                            
                                    if t_f == 'MFNAME':
                                        if getattr(self, '_diag_name_count', 0) < 5:
                                            self.log(f"DEBUG ROW: raw JOIN_KEY='{raw_name_id}', norm='{norm_name_id}', matched={cache_matched}, FIRST='{source_row.get('INDIVIDUAL_FIRST', '')}', MIDDLE='{source_row.get('INDIVIDUAL_MIDDLE', '')}', LAST='{source_row.get('INDIVIDUAL_LAST', '')}'")
                                            self._diag_name_count += 1
                                            
                                        if not cache_matched:
                                            if not hasattr(self, '_diag_fail_count'):
                                                self._diag_fail_count = 0
                                            if self._diag_fail_count < 10:
                                                # Find first 3 similar keys using a 4-character prefix
                                                prefix_val = norm_name_id[:4] if len(norm_name_id) >= 4 else norm_name_id
                                                similar = [k for k in rel_name_cache.keys() if str(k).startswith(prefix_val)][:3] if prefix_val else []
                                                self.log(f"DEBUG FAILED JOIN: raw MCLIENTID='{raw_name_id}', norm='{norm_name_id}', in_cache={norm_name_id in rel_name_cache}, similar_keys={similar}")
                                                self._diag_fail_count += 1
                                        
                                    if t_f == 'MFNAME':
                                        val = source_row.get('INDIVIDUAL_FIRST', val)
                                    elif t_f == 'MLNAME':
                                        business_name = str(source_row.get('NAME_BUSINESS', '')).strip()
                                        if business_name and business_name.lower() not in ['nan', 'none']:
                                            val = business_name
                                        else:
                                            val = source_row.get('INDIVIDUAL_LAST', val)
                                    elif t_f == 'MMNAME':
                                        temp_val = str(source_row.get('INDIVIDUAL_MIDDLE', val))
                                        # Harden against padded spaces and trailing decimal artifacts
                                        clean_temp = temp_val.replace('.0', '').strip()
                                        
                                        # Safety shield: blank out only if the ENTIRE value is numeric
                                        if clean_temp.isdigit():
                                            val = ""
                                        else:
                                            val = clean_temp
                                # ----------------------------------------
                                
                                if note == "SKIP_TRANSLATION":
                                    pass
                                elif t_f == "MVALID":
                                    if val in ['Y', 'YES', 'TRUE', '1']: val = 'F' if 'INVALID' in s_f else 'T'
                                    elif val in ['N', 'NO', 'FALSE', '0']: val = 'T' if 'INVALID' in s_f else 'F'
                                    if val not in ['T', 'F']: val = 'T' 
                                elif t_f == "MUWCLASS":
                                    # Issue #59: never apply bare status map (S→55/P→41/N→T/T→56)
                                    val = map_rider_uwclass(val)
                                elif t_id.lower() == "quikplan" and t_f == "PAR":
                                    # LifePRO EXHIBIT_PAR_NONPAR (P/N/X/F) → QLAdmin PAR (1=par, 0=non-par)
                                    translated = trans_map.get(f"PAR_{val}", trans_map.get(val, ""))
                                    if translated != "":
                                        val = translated
                                    elif val not in ("0", "1"):
                                        val = "0"
                                else:
                                    prefix = "BF_" if t_f == "MBILLFRM" else ("PM_" if t_f == "MMODE" else ("DV_" if t_f == "MDIVOPT" else ("NF_" if t_f == "MNFOPT" else ("AG_" if (t_f == "MSTATUS" and t_id.lower() == "quikagts") else ("ST_" if t_f == "MSTATUS" else ("PAR_" if t_f == "MPAR" else ""))))))
                                    if not (t_id.lower() == "quikbenf" and t_f == "MTYPE"):
                                        val = trans_map.get(f"{prefix}{val}", trans_map.get(val, val))

                                # --- Issue #49: first active later phase → MSTATUS (after Issue #13 + ST_) ---
                                # Record provisional (pre-override) status for phase-1 MPHSTAT inherit so
                                # QuikMstr-only override does not change phase 1.
                                if t_f == "MSTATUS" and t_id.lower() == "quikmstr":
                                    if not hasattr(self, "_mstatus_provisional_for_phase1_cache"):
                                        self._mstatus_provisional_for_phase1_cache = {}
                                    _prov_pol = self.normalize(row_data.get("MPOLICY", ""))
                                    if not _prov_pol:
                                        _lp = self.normalize(src_row.get("POLICY_NUMBER", ""))
                                        _prov_pol = self.normalize(
                                            self._format_qladmin_mpolicy(cw_map.get(_lp, _lp))
                                        )
                                    if _prov_pol and val not in ["", None]:
                                        self._mstatus_provisional_for_phase1_cache[_prov_pol] = self.normalize(val)
                                    _phase_cache = getattr(self, "_ppben_phase_cache", None) or {}
                                    if _phase_cache:
                                        _lp_pol = self.normalize(src_row.get("POLICY_NUMBER", ""))
                                        _phases = _phase_cache.get(_lp_pol, [])
                                        if _phases:
                                            if not hasattr(self, "_issue49_bare_status_map"):
                                                self._issue49_bare_status_map = bare_status_map_from_trans_map(trans_map)
                                            _new_status, _overridden = select_mstatus_from_active_phase(
                                                val, _phases, self._issue49_bare_status_map
                                            )
                                            # Issue #59: keep Death Claim Pending (50) for the one
                                            # client S/DP policy; #49 later-active-phase must not
                                            # replace it with a later PUA/active phase (22).
                                            _i59_dp_keys = {
                                                "9010521213",
                                                "9010521213C",
                                                "010521213C",
                                            }
                                            _i59_dp = (
                                                _lp_pol in _i59_dp_keys
                                                or _prov_pol in _i59_dp_keys
                                            )
                                            if _overridden and not _i59_dp:
                                                val = _new_status
                                                self._issue49_mstatus_override_count = (
                                                    getattr(self, "_issue49_mstatus_override_count", 0) + 1
                                                )
                                # -----------------------------------------------------------------
                                
                                # --- STRICT NUMERIC SHIELD FOR DIVIDENDS & NFO ---
                                if t_f in ['MDIVOPT', 'MNFOPT'] and not str(val).isdigit():
                                    val = "0"
                                # -------------------------------------------------
                                
                                if t_id.lower() == "quikclid" and t_f == "MPOLICY" and not self.normalize(val):
                                    val = self._derive_rna_policy_from_identifying_alpha(src_row, cw_map)

                                if t_f in ["MPOLICY", "MCLIENTID", "MPRIMID", "MOWNRID", "MPAYRID", "MASGNID", "MBENPID", "MBENCID", "MCID", "MOWNCID", "MRIDRID", "MPLAN", "PLAN"]:
                                    if t_f == "MPOLICY":
                                        # Issue #2: keep source POLICY_NUMBER; do not apply strip-9 crosswalk
                                        pass
                                    elif (
                                        t_id.lower() == "quikridr"
                                        and t_f == "MPLAN"
                                        and self._closed_mplan_authority_enabled()
                                        and mplan_resolver is not None
                                    ):
                                        candidate = cw_map.get(val, val)
                                        mplan_resolution = resolve_authoritative_mplan(
                                            source_plan_code,
                                            candidate,
                                            mplan_resolver,
                                            allow_legacy=self._allow_legacy_mplan_fallback(),
                                        )
                                        val = mplan_resolution.resolved_mplan
                                    else:
                                        val = cw_map.get(val, val)

                                if t_f == "MPOLICY" and val:
                                    val = self._format_qladmin_mpolicy(val)
                                elif t_f in CLIENT_ID_TARGET_FIELDS and val:
                                    val = format_qladmin_mclientid(val)
                                
                                if t_id.lower() == "quikdvdp":
                                    if actual_h in ["MDEPOSIT", "MINTYTD", "MDEPINT"] and val:
                                        try:
                                            val = f"{float(val):.2f}"
                                        except:
                                            val = "0.00"
                                    elif actual_h == "MINTDATE":
                                        if not val or str(val).strip().upper() in ["0", "0.0", "0.00", "POLC.PAID_TO_DATE", "NAN", "NONE"]:
                                            pol_id = self.normalize(row_data.get('MPOLICY', ''))
                                            if pol_id in quikmstr_paid_to:
                                                val = quikmstr_paid_to[pol_id]
                                        if val:
                                            val = re.sub(r'[^0-9]', '', str(val))
    
                                # --- FINAL OUTPUT SANITIZATION ---
                                if actual_h == 'MMNAME':
                                    final_mm = str(val).replace('.0', '').strip()
                                    if final_mm.isdigit():
                                        val = ""
                                        
                                if t_id.lower() == "quikridr" and actual_h == "MPAR":
                                    # Issue #105: force 0/1; product PAR authority already applied above
                                    normalized_mpar = self.normalize(val)
                                    if normalized_mpar == "1":
                                        val = "1"
                                    else:
                                        val = "0"
                                        
                                if t_id.lower() == "quikclid" and actual_h == "MPHASE":
                                    # Phase finalized after MRELATION is known (below).
                                    pass
                                # ---------------------------------
    
                                row_data[actual_h] = val

                        # --- Policy Data Governance: QuikClid phase by relationship ---
                        if t_id.lower() == "quikclid":
                            from qla_core.policy_data_transforms import (
                                apply_quikclid_phase_for_relation,
                                record_policy_transform,
                            )
                            _rel = self.normalize(row_data.get("MRELATION", ""))
                            _ph_orig = self.normalize(row_data.get("MPHASE", ""))
                            _ph_new, _ph_chg, _ph_rule = apply_quikclid_phase_for_relation(
                                _ph_orig, _rel
                            )
                            if _ph_chg or row_data.get("MPHASE") != _ph_new:
                                if _ph_chg:
                                    record_policy_transform(
                                        table="QuikClid",
                                        record_id=(
                                            f"{self.normalize(row_data.get('MPOLICY', ''))} / "
                                            f"{self.normalize(row_data.get('MCLIENTID', ''))} / "
                                            f"{_rel}"
                                        ),
                                        field="MPHASE",
                                        original=_ph_orig,
                                        converted=_ph_new,
                                        reason=(
                                            "Policy-level relationship uses phase zero"
                                            if _rel.upper() != "INSD"
                                            else "Insured blank phase defaulted to base phase 1"
                                        ),
                                        rule_id=_ph_rule,
                                    )
                                row_data["MPHASE"] = _ph_new
                        # ---------------------------------------------------------------
    
                        tp = self.normalize(row_data.get('MPOLICY', ''))
                        tphase = self.normalize(row_data.get('MPHASE', ''))
                        if not tphase: tphase = "1"

                        # --- v57.28: PRIMARY_PERSON type flags must not become MPRIMID ---
                        if t_id.lower() == "quikmstr" and "MPRIMID" in row_data:
                            _prim = self.normalize(row_data.get("MPRIMID", ""))
                            if len(_prim) == 1 and _prim.isalpha():
                                row_data["MPRIMID"] = ""
                        # ---------------------------------------------------------------
    
                        if t_id.lower() == "quikmstr" and tp in rel_map:
                            if "1" in rel_map[tp]:
                                p_rel = rel_map[tp]["1"]
                                # Includes raw LifePRO source codes alongside standard QLAdmin roles
                                # Beneficiaries stay on QuikClid only (DG-QUIKMSTR-021/022).
                                for r, f in {'IN':'MPRIMID', 'INSD':'MPRIMID', 'PO':'MOWNRID', 'OWNR':'MOWNRID', 'PA':'MPAYRID', 'PAYR':'MPAYRID', 'ASGN':'MASGNID'}.items():
                                    if r in p_rel and f in row_data: 
                                        row_data[f] = format_qladmin_mclientid(cw_map.get(p_rel[r], p_rel[r]))
                            # Force blank beneficiary IDs on Policy Master
                            from qla_core.policy_data_transforms import record_policy_transform
                            for _bf in ("MBENPID", "MBENCID"):
                                if _bf in row_data:
                                    _borig = self.normalize(row_data.get(_bf, ""))
                                    if _borig:
                                        record_policy_transform(
                                            table="QuikMstr",
                                            record_id=tp,
                                            field=_bf,
                                            original=_borig,
                                            converted="",
                                            reason="Beneficiary relationships are stored separately",
                                            rule_id=(
                                                "DG-QUIKMSTR-021"
                                                if _bf == "MBENPID"
                                                else "DG-QUIKMSTR-022"
                                            ),
                                        )
                                    row_data[_bf] = ""
                        elif t_id.lower() == "quikmstr":
                            for _bf in ("MBENPID", "MBENCID"):
                                if _bf in row_data:
                                    row_data[_bf] = ""

                        # --- Policy Data Governance: uppercase state/sex codes ---
                        if t_id.lower() == "quikmstr" and "MISSUEST" in row_data:
                            from qla_core.policy_data_transforms import (
                                record_policy_transform,
                                uppercase_alpha_field,
                            )
                            _st_orig = self.normalize(row_data.get("MISSUEST", ""))
                            _st_new, _st_chg = uppercase_alpha_field(_st_orig)
                            if _st_chg:
                                record_policy_transform(
                                    table="QuikMstr",
                                    record_id=tp,
                                    field="MISSUEST",
                                    original=_st_orig,
                                    converted=_st_new,
                                    reason="Uppercased issue state",
                                    rule_id="DG-QUIKMSTR-014",
                                )
                                row_data["MISSUEST"] = _st_new
                        if t_id.lower() == "quikclnt":
                            from qla_core.policy_data_transforms import (
                                record_policy_transform,
                                uppercase_alpha_field,
                            )
                            _cid = self.normalize(row_data.get("MCLIENTID", ""))
                            for _fld, _rule in (("MSEX", "DG-QUIKCLNT-007"), ("MSTATE", "DG-QUIKCLNT-005")):
                                if _fld not in row_data:
                                    continue
                                _o = self.normalize(row_data.get(_fld, ""))
                                _n, _c = uppercase_alpha_field(_o)
                                if _c:
                                    record_policy_transform(
                                        table="QuikClnt",
                                        record_id=_cid,
                                        field=_fld,
                                        original=_o,
                                        converted=_n,
                                        reason=f"Uppercased {_fld}",
                                        rule_id=_rule,
                                    )
                                    row_data[_fld] = _n
                        # ---------------------------------------------------------------
                            
                        if t_id.lower() == "quikridr" and 'MRIDRID' in row_data and tp in rel_map:
                            rel_id = None
                            rel_source = None
                            
                            # Phase-level rider insured priority, if that phase exists
                            phase_rel = rel_map[tp].get(tphase, {})
                            
                            if 'RU' in phase_rel:
                                rel_id = phase_rel['RU']
                                rel_source = f"phase {tphase} RU"
                            elif 'IN' in phase_rel:
                                rel_id = phase_rel['IN']
                                rel_source = f"phase {tphase} IN"
                            elif 'INSD' in phase_rel:
                                rel_id = phase_rel['INSD']
                                rel_source = f"phase {tphase} INSD"
                            
                            # Fallback to phase 1 insured even when rider phase is missing
                            if not rel_id and "1" in rel_map[tp]:
                                base_rel = rel_map[tp]["1"]
                                if 'IN' in base_rel:
                                    rel_id = base_rel['IN']
                                    rel_source = f"fallback phase 1 IN (requested phase {tphase})"
                                elif 'INSD' in base_rel:
                                    rel_id = base_rel['INSD']
                                    rel_source = f"fallback phase 1 INSD (requested phase {tphase})"
                            
                            if rel_id:
                                row_data['MRIDRID'] = format_qladmin_mclientid(cw_map.get(rel_id, rel_id))
                            
                            if self.debug_rel_fallback and self._diag_rel_fallback_count < 25:
                                if rel_id:
                                    self.log(
                                        f"DEBUG REL: MPOLICY={tp} MPHASE={tphase} "
                                        f"MRIDRID={row_data.get('MRIDRID', '')} via {rel_source}"
                                    )
                                else:
                                    phase_keys = sorted(rel_map[tp].keys())
                                    phase_roles = sorted(phase_rel.keys()) if phase_rel else []
                                    self.log(
                                        f"DEBUG REL: MPOLICY={tp} MPHASE={tphase} MRIDRID=UNRESOLVED "
                                        f"policy_phases={phase_keys} phase_roles={phase_roles}"
                                    )
                                self._diag_rel_fallback_count += 1
                            
                        # --- BASE PHASE TERMINAL STATUS SYNCHRONIZATION ---
                        if t_id.lower() == "quikridr" and tphase == "1":
                            if getattr(self, '_qm_sync_table', None) != t_id:
                                self._qm_sync_table = t_id
                                self._qm_status_cache = None
                                self._qm_paidto_cache = None
                                
                            if self._qm_status_cache is None:
                                self._qm_status_cache = {}
                                self._qm_paidto_cache = {}
                                try:
                                    qm_path = os.path.normpath(os.path.join(self.path_vars["Out"][0].get(), "quikmstr.csv"))
                                    if os.path.exists(qm_path):
                                        qdf = pd.read_csv(qm_path, dtype=str).fillna("")
                                        qdf.columns = [str(c).strip().upper() for c in qdf.columns]
                                        if 'MPOLICY' in qdf.columns and 'MSTATUS' in qdf.columns:
                                            self._qm_status_cache = {self.normalize(k): self.normalize(v) for k, v in zip(qdf['MPOLICY'], qdf['MSTATUS'])}
                                        if 'MPOLICY' in qdf.columns and 'MPAIDTO' in qdf.columns:
                                            self._qm_paidto_cache = {
                                                self.normalize(k): self.normalize(v)
                                                for k, v in zip(qdf['MPOLICY'], qdf['MPAIDTO'])
                                                if self.normalize(v) not in ("", "NAN", "NONE", "NULL")
                                            }
                                except Exception:
                                    pass
                                # Issue #49: load provisional (pre-override) statuses for phase-1 inherit
                                if not getattr(self, "_mstatus_provisional_for_phase1_cache", None):
                                    self._mstatus_provisional_for_phase1_cache = {}
                                    try:
                                        _prov_path = os.path.normpath(os.path.join(
                                            os.path.dirname(os.path.abspath(__file__)),
                                            "QLA_Migration", "Reports", "quikmstr_phase1_inherit_mstatus.csv",
                                        ))
                                        if not os.path.isfile(_prov_path):
                                            _out = self.path_vars["Out"][0].get()
                                            _prov_path = os.path.normpath(os.path.join(
                                                os.path.dirname(_out), "Reports", "quikmstr_phase1_inherit_mstatus.csv",
                                            ))
                                        if os.path.isfile(_prov_path):
                                            _pdf = pd.read_csv(_prov_path, dtype=str).fillna("")
                                            _pdf.columns = [str(c).strip().upper() for c in _pdf.columns]
                                            if "MPOLICY" in _pdf.columns and "MSTATUS_PROVISIONAL" in _pdf.columns:
                                                self._mstatus_provisional_for_phase1_cache = {
                                                    self.normalize(k): self.normalize(v)
                                                    for k, v in zip(_pdf["MPOLICY"], _pdf["MSTATUS_PROVISIONAL"])
                                                }
                                    except Exception:
                                        pass
                                    
                            # Prefer Issue #13 provisional status so #49 QuikMstr override does not change phase 1
                            _prov_map = getattr(self, "_mstatus_provisional_for_phase1_cache", None) or {}
                            qm_status = _prov_map.get(tp) or self._qm_status_cache.get(tp)
                            # Inherit meaningful policy-level terminal status; block active statuses
                            if qm_status and qm_status not in ["", "11", "22", "ACTIVE"]:
                                row_data['MPHSTAT'] = qm_status
                        # --------------------------------------------

                        # --- Issue #21E: UL fund balance -> MCV0 (phase-1 only) ---
                        # Cache is keyed by LifePRO POLICY_NUMBER (not crosswalked MPOLICY).
                        if t_id.lower() == "quikridr" and ul_fund_balance_cache:
                            _lp_pol = self.normalize(src_row.get("POLICY_NUMBER", ""))
                            if apply_ul_fund_balance_to_quikridr_row(
                                row_data, _lp_pol, tphase, ul_fund_balance_cache
                            ):
                                ul_fund_mcv0_count += 1
                        # --------------------------------------------------------
    
                        # --- QUIKDVDP ENRICHMENT (Issue #38) ---
                        # MDEPOSIT: preserve rulebook PPBENTYP ACCUM_DIVIDENDS — never zero on cache miss.
                        # MINTYTD/MINTDATE: optional PACTG 641 enrichment when cache hit.
                        if t_id.lower() == "quikdvdp":
                            if tp in quikdvdp_tx_cache:
                                tx_data = quikdvdp_tx_cache[tp]
                                row_data['MINTYTD'] = f"{tx_data['MINTYTD']:.2f}"
                                mdt = tx_data['MINTDATE']
                                if mdt:
                                    row_data['MINTDATE'] = re.sub(r'[^0-9]', '', str(mdt))
                                if not getattr(self, '_quikdvdp_641_hits', 0):
                                    self.log(
                                        f"Issue #116: quikdvdp 641 enrichment matched "
                                        f"(first hit {tp} MINTDATE={row_data.get('MINTDATE')})"
                                    )
                                self._quikdvdp_641_hits = getattr(self, '_quikdvdp_641_hits', 0) + 1
                            # Issue #21D Track A: ISWL-scoped MDEPINT from MPLAN allowlist (not fleet-wide).
                            _mplan = quikridr_mplan_cache.get(tp, "")
                            if is_iswl_mplan(_mplan):
                                row_data['MDEPINT'] = iswl_mdepint_percent()
                        # ---------------------------
    
                        # --- QUIKAGTS ENRICHMENT ---
                        if t_id.lower() == "quikagts":
                            name_id = self.normalize(src_row.get("NAME_ID", ""))
                            if not name_id: name_id = self.normalize(src_row.get("CLIENT_ID", ""))
                            
                            magent = self.normalize(src_row.get("AGENT_NUMBER", row_data.get("MAGENT", "")))
                            row_data["MAGENT"] = magent
                            
                            if not row_data.get("MSUPPRESS"):
                                row_data["MSUPPRESS"] = "F"
                                
                            clnt = quikagts_clnt_cache.get(name_id, {})
                            if clnt:
                                fname = self.normalize(clnt.get("MFNAME", ""))
                                lname = self.normalize(clnt.get("MLNAME", ""))
                                if fname or lname:
                                    row_data["MAGTNAME"] = f"{fname} {lname}".strip()
                                    
                                mapping = {
                                    "MADDR1": "MAGTADDR1", "MADDR2": "MAGTADDR2",
                                    "MCITY": "MAGTCITY", "MSTATE": "MAGTST",
                                    "MZIP": "MAGTZIP", "MZIP2": "MAGTZIP2",
                                    "MEMAIL": "MAGTEMAIL", "MTAXIDTYPE": "MTAXIDTYPE"
                                }
                                for c_key, a_key in mapping.items():
                                    val = self.normalize(clnt.get(c_key, ""))
                                    if val: row_data[a_key] = val
                                    
                                tax_id = self.normalize(clnt.get("MTAXID", ""))
                                tax_type = self.normalize(clnt.get("MTAXIDTYPE", ""))
                                if tax_type == "S":
                                    row_data["MAGTSSN"] = tax_id
                                    row_data["MAGTFEIN"] = ""
                                elif tax_type == "E":
                                    row_data["MAGTSSN"] = ""
                                    row_data["MAGTFEIN"] = tax_id
                                    
                                ofc = self.normalize(clnt.get("MPHONEOFC", ""))
                                cell = self.normalize(clnt.get("MPHONECELL", ""))
                                home = self.normalize(clnt.get("MPHONEHOME", ""))
                                
                                row_data["MAGTOFCE"] = ofc
                                row_data["MAGTCELL"] = cell
                                if ofc:
                                    row_data["MAGTPHONE"] = ofc
                                elif cell:
                                    row_data["MAGTPHONE"] = cell
                                elif home:
                                    row_data["MAGTPHONE"] = home
                        # ---------------------------
    
                        if (
                            t_id.lower() == "quikridr"
                            and self._closed_mplan_authority_enabled()
                            and mplan_resolver is not None
                            and mplan_resolution is not None
                        ):
                            mplan_trace_rows.append(resolution_to_trace_row(
                                mplan_resolution,
                                source_file=mplan_src_file,
                                source_row_number=int(i) + 2,
                                mpolicy=row_data.get("MPOLICY", ""),
                                mphase=row_data.get("MPHASE", ""),
                                row_data=row_data,
                                quikplan_plan_set=quikplan_plan_set,
                                allow_legacy=self._allow_legacy_mplan_fallback(),
                                source_benefit_type=str(src_row.get("BENEFIT_TYPE", "")),
                            ))
                            row_data["MPLAN"] = mplan_resolution.resolved_mplan

                        if t_id.lower() == "quikridr":
                            if tphase == "1" and tp:
                                self._cache_quikridr_base_phase(base_phase_cache, tp, row_data)
                            if self._is_paid_up_addition_product(source_plan_code, cw_map):
                                pua_pending_rows.append((dict(row_data), tp, source_plan_code))
                                if i % 1000 == 0:
                                    self.progress["value"] = (i / len(source)) * 100
                                    self.root.update_idletasks()
                                continue

                        if t_id.lower() == "quikridr":
                            if self._resolve_quikridr_mphdob(row_data, src_row, rel_name_cache):
                                quikridr_mphdob_fix_count += 1
                            self._apply_quikridr_mlastann(row_data, src_row, quikridr_valuation_date)
                            _nfo_phase1 = False
                            if tphase == "1":
                                _qm_st = (getattr(self, "_qm_status_cache", None) or {}).get(tp, "")
                                _qm_pd = (getattr(self, "_qm_paidto_cache", None) or {}).get(tp, "")
                                self._apply_issue76_eti_rpu_phase1_payup_mlastann(
                                    row_data, _qm_st, _qm_pd, quikridr_valuation_date,
                                )
                                # Issue #108B/#108C: NFO attained age + ETI premium.
                                # Runs after MPHDOB resolution above — that derivation reads MAGE.
                                self._apply_issue108_nfo_phase1_fields(row_data, _qm_st, _qm_pd)
                                _nfo_phase1 = self.normalize(_qm_st) in ("44", "45")
                            apply_quikridr_decimal_emit(row_data)
                            # v57.96: blank MSAVE* mirror final live fields; MRRULE default A
                            # Issue #108A: mirror suppressed on ETI/RPU phase 1
                            self._apply_quikridr_v5796_defaults(row_data, nfo_phase1=_nfo_phase1)
                        # Issue #72: ETI/RPU status vs NFO election — report only (after final MSTATUS)
                        if t_id.lower() == "quikmstr":
                            self._check_issue72_mnfopt_status(row_data, nfo_status_exceptions)
                        # Issue #45: bank-draft missing account → blank MBANKNO + exception (MBILLFRM unchanged)
                        if t_id.lower() == "quikmstr":
                            self._apply_issue45_bank_draft_gate(row_data, src_row, bank_draft_exceptions)
                        # v57.96: MBILLTO 0 → MPAIDTO; MORIGBILL/MORIGMODE copies
                        if t_id.lower() == "quikmstr":
                            self._apply_quikmstr_v5796_defaults(row_data)
                        output.append([row_data[h] for h in schema])
                        if i % 1000 == 0: self.progress["value"] = (i/len(source))*100; self.root.update_idletasks()

                    if t_id.lower() == "quikridr" and pua_pending_rows:
                        for pua_row, pua_pol, pua_plan_code in pua_pending_rows:
                            self._apply_pua_rider_inheritance(
                                pua_row, pua_pol, pua_plan_code, base_phase_cache, cw_map,
                            )
                            if self._resolve_quikridr_mphdob(pua_row, {}, rel_name_cache):
                                quikridr_mphdob_fix_count += 1
                            self._apply_quikridr_mlastann(pua_row, {}, quikridr_valuation_date)
                            apply_quikridr_decimal_emit(pua_row)
                            # v57.96: blank MSAVE* mirror final live fields (after PUA inheritance)
                            self._apply_quikridr_v5796_defaults(pua_row)
                            output.append([pua_row[h] for h in schema])
                    if t_id.lower() == "quikridr" and quikridr_mphdob_fix_count:
                        self.log(f"QUIKRIDR MPHDOB: corrected {quikridr_mphdob_fix_count} invalid DOB row(s)")
                    if t_id.lower() == "quikridr" and ul_fund_mcv0_count:
                        self.log(
                            f"Issue #21E: populated MCV0 from FV_BALANCE2 on "
                            f"{ul_fund_mcv0_count} phase-1 UL/fund-value row(s)"
                        )
                    if t_id.lower() == "quikridr":
                        _i76 = getattr(self, "_issue76_payup_adjust_count", 0)
                        if _i76:
                            self.log(
                                f"Issue #76: adjusted phase-1 MPAYUP/MLASTANN on "
                                f"{_i76} ETI/RPU polic(ies)"
                            )
                    if t_id.lower() == "quikmstr":
                        _i121 = getattr(self, "_issue121_art_guard_count", 0)
                        if _i121:
                            self.log(
                                f"Issue #121: suppressed PUT LE/ET→ETI on {_i121} ART polic(ies)"
                            )
                    if t_id.lower() == "quikmstr" and nfo_status_exceptions:
                        self.log(
                            f"Issue #72: {len(nfo_status_exceptions)} ETI/RPU polic(ies) where the "
                            f"NFO election does not match the policy status (see Reports/)"
                        )
                        _v5796 = getattr(self, "_v5796_mbillto_fix_count", 0)
                        if _v5796:
                            self.log(
                                f"v57.96: MBILLTO 0/blank replaced with MPAIDTO on {_v5796} polic(ies)"
                            )
                        _i49 = getattr(self, "_issue49_mstatus_override_count", 0)
                        if _i49:
                            self.log(
                                f"Issue #49: overridden MSTATUS from first active later phase on {_i49} polic(ies)"
                            )
                        # Persist provisional MSTATUS for phase-1 inherit (Reports/, not Output/)
                        _prov = getattr(self, "_mstatus_provisional_for_phase1_cache", None) or {}
                        if _prov:
                            try:
                                _out = self.path_vars["Out"][0].get()
                                _rep = os.path.normpath(os.path.join(os.path.dirname(_out), "Reports"))
                                os.makedirs(_rep, exist_ok=True)
                                _prov_path = os.path.join(_rep, "quikmstr_phase1_inherit_mstatus.csv")
                                pd.DataFrame(
                                    [{"MPOLICY": k, "MSTATUS_PROVISIONAL": v} for k, v in sorted(_prov.items())]
                                ).to_csv(_prov_path, index=False)
                                self.log(
                                    f"Issue #49: wrote phase-1 inherit provisional MSTATUS cache "
                                    f"({len(_prov)} policies) → {_prov_path}"
                                )
                            except Exception as e:
                                self.log(f"Warning: could not write phase-1 inherit MSTATUS cache - {e}")
                    if t_id.lower() == "quikbenf" and output:
                        output, benf_stats = self._apply_quikbenf_dedupe_and_equal_split(output, schema)
                        self.log(
                            f"QUIKBENF Issue 21I: deduped {benf_stats['dedupe_removed']} row(s), "
                            f"recalculated MSPLIT for {benf_stats['groups_recalculated']} "
                            f"(MPOLICY, MTYPE) group(s)"
                        )
                    if t_id.lower() == "quikclid" and output:
                        output, clid_stats = self._apply_quikclid_exact_dedupe(output, schema)
                        self.log(
                            f"QUIKCLID Issue 30: deduped {clid_stats['dedupe_removed']} exact relationship row(s)"
                        )

                out_dir = self.path_vars["Out"][0].get()
                if t_id.lower() == "quikridr" and self._closed_mplan_authority_enabled() and mplan_trace_rows:
                    trace_df = pd.DataFrame(mplan_trace_rows)
                    quarantine = os.environ.get("QLA_PRODUCT_AUTHORITY_QUARANTINE", "0").strip().lower() in ("1", "true", "yes")
                    if quarantine:
                        output, _ = apply_mplan_emit_filter(output, schema, trace_df, quarantine=True)
                    aligned_df = pd.DataFrame(output, columns=schema)
                    passed, val_stats = validate_emitted_quikridr(aligned_df, quikplan_plan_set)
                    p3e_dir = os.path.normpath(os.path.join(self._app_base_dir(), "plan_analysis", "phase_p3e_quikridr_authority_alignment"))
                    write_p3e_governance_outputs(
                        p3e_dir,
                        trace_df,
                        closed_enabled=True,
                        allow_legacy=self._allow_legacy_mplan_fallback(),
                        emitted_rows=len(output),
                        validation_passed=passed,
                    )
                    self.log(f"P3E MPLAN AUTHORITY: validation={'PASSED' if passed else 'FAILED'} stats={val_stats}")
                    self.log(f"P3E governance outputs: {p3e_dir}")
                aligned_out_df = pd.DataFrame(output, columns=schema)
                out_csv = os.path.normpath(os.path.join(out_dir, f"{t_id}.csv"))
                if t_id.lower() == "quikclnt":
                    from qla_core.quikclnt_highwater import apply_quikclnt_highwater

                    aligned_out_df, _hw_stats = apply_quikclnt_highwater(aligned_out_df)
                    if _hw_stats.get("applied"):
                        self.log(
                            f"TEMP quikclnt high-water: id={_hw_stats.get('highwater_id')} "
                            f"(max_prior={_hw_stats.get('max_prior')}; "
                            f"disable QLA_QUIKCLNT_HIGHWATER=0)"
                        )
                        output = aligned_out_df.to_dict("records")
                aligned_out_df.to_csv(out_csv, index=False)
                self.log(f"Success: {t_id}.csv - {len(aligned_out_df)} records.")
                self._cut_record(
                    str(t_id).lower(),
                    "WRITTEN",
                    source_path=src_path if "src_path" in locals() else None,
                    output_relpath=f"{t_id}.csv",
                    row_count=len(aligned_out_df),
                )

                if t_id.lower() == "quikmstr" and bank_draft_exceptions is not None:
                    self._write_bank_draft_account_exceptions(bank_draft_exceptions)

                if t_id.lower() == "quikmstr" and nfo_status_exceptions is not None:
                    self._write_issue72_mnfopt_status_exceptions(nfo_status_exceptions)

                if t_id.lower() == "quikridr":
                    mstr_path = os.path.normpath(os.path.join(out_dir, "quikmstr.csv"))
                    if os.path.isfile(mstr_path):
                        mstr_df = pd.read_csv(
                            mstr_path, dtype=str, encoding="latin1", low_memory=False,
                        ).fillna("")
                        mstr_df.columns = [str(c).strip().upper() for c in mstr_df.columns]
                        quikplan_path = os.path.normpath(os.path.join(out_dir, "quikplan.csv"))
                        mstr_df, plan_modal_stats = apply_plan_modal_factors_to_quikmstr(
                            mstr_df,
                            quikridr_df=aligned_out_df,
                            quikplan_path=quikplan_path if os.path.isfile(quikplan_path) else None,
                        )
                        mstr_df, pac_stats = apply_pac_gl85_modal_overrides(
                            mstr_df, quikridr_df=aligned_out_df,
                        )
                        mstr_df.to_csv(mstr_path, index=False)
                        aligned_out_df, fee_stats = apply_modal_policy_fees_to_quikridr(
                            aligned_out_df, mstr_df,
                        )
                        # Issue #89: fail-closed if fee cache populated but MANNLFEE wiped on base rows
                        _fee_cache_n = len(getattr(self, "_policy_fee_map", {}) or {})
                        if _fee_cache_n >= 1000:
                            _mann_pop = 0
                            for _, _fr in aligned_out_df.iterrows():
                                if str(_fr.get("MPHASE", "")).strip() not in ("1", "01"):
                                    continue
                                try:
                                    if float(str(_fr.get("MANNLFEE", "")).strip() or 0) > 0:
                                        _mann_pop += 1
                                except ValueError:
                                    pass
                            if _mann_pop == 0:
                                _i89_msg = (
                                    f"Issue #89 FATAL: PPOLC fee cache has {_fee_cache_n} policies but "
                                    f"quikridr MANNLFEE populated on 0 base rows — fee wipe detected; aborting."
                                )
                                self.log(_i89_msg)
                                raise RuntimeError(_i89_msg)
                        aligned_out_df.to_csv(out_csv, index=False)
                        self.log(
                            f"Issue 36: plan modal factors copied to quikmstr "
                            f"(updated={plan_modal_stats.get('policies_updated', 0)}, "
                            f"missing_plan={plan_modal_stats.get('policies_missing_plan', 0)}, "
                            f"missing_factors={plan_modal_stats.get('policies_missing_factors', 0)})"
                        )
                        self.log(
                            f"Issue 21J: PAC GL85 modal overrides on quikmstr "
                            f"(quarterly={pac_stats.get('qtr_overrides', 0)}, "
                            f"semiannual={pac_stats.get('semi_overrides', 0)})"
                        )
                        self.log(
                            f"Issue 58: modal policy fees on quikridr "
                            f"(updated={fee_stats.get('rows_updated', 0)}, "
                            f"zero_fee={fee_stats.get('skipped_zero_fee', 0)}, "
                            f"missing_factors={fee_stats.get('skipped_missing_factors', 0)})"
                        )

                if is_batch and t_id.lower() == "quikplan" and self._closed_mplan_authority_enabled():
                    mplan_resolver, quikplan_plan_set, _ = self._init_mplan_authority(out_dir, cw_path)
                    self.log(
                        f"P3E MPLAN AUTHORITY: refreshed resolver after quikplan emit "
                        f"(quikplan PLAN universe={len(quikplan_plan_set)})"
                    )
                
                audit_path = os.path.normpath(os.path.join(self._logs_dir(), "Migration_Audit_Log.txt"))
                is_new_log = not os.path.exists(audit_path)
                
                source_count = len(source)
                output_count = len(output)
                variance = source_count - output_count
                
                audit_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] TABLE: {t_id.upper():<10} | SOURCE RECORDS: {source_count:<8} | QLA OUTPUT: {output_count:<8} | VARIANCE: {variance} (Skipped/Dashed)\n"
                
                with open(audit_path, "a") as f:
                    if is_new_log:
                        f.write("=== QLADMIN ENTERPRISE MIGRATION AUDIT LOG ===\n")
                        f.write("Tracks 1:1 record translation matching to guarantee zero data loss.\n\n")
                    f.write(audit_msg)
                
                self.log(f"Audit Verified: {source_count} Source -> {output_count} Output. Saved to Audit Log.")

                if is_batch and t_id.lower() == "quikclid":
                    fresh_rel = os.path.normpath(os.path.join(out_dir, "quikclid.csv"))
                    if os.path.isfile(fresh_rel):
                        clnt_path = os.path.normpath(os.path.join(out_dir, "quikclnt.csv"))
                        name_lookup = self._build_client_name_lookup(
                            rel_name_cache=rel_name_cache if rel_name_cache else None,
                            quikclnt_path=clnt_path if os.path.isfile(clnt_path) else None,
                        )
                        rel_map = self._load_rel_map(
                            fresh_rel, trans_map, log_label="batch relational map", name_lookup=name_lookup,
                        )
                        self.path_vars["Rel"][0].set(fresh_rel)

            # --- Issue #21G: stage premium/basis totals (informational until QLAdmin target named) ---
            if is_batch:
                try:
                    src_dir = self._resolve_source_dir() if hasattr(self, "_resolve_source_dir") else self._migration_root()
                    # Prefer QLA_Migration/Source
                    src_dir = os.path.normpath(os.path.join(self._app_base_dir(), "QLA_Migration", "Source"))
                    _ppben = resolve_ppben_path(src_dir)
                    _ppbentyp = resolve_ppbentyp_extract_path(src_dir)
                    if _ppben or _ppbentyp:
                        _21g_rows = build_premium_basis_totals(
                            _ppbentyp, _ppben, normalize_fn=self.normalize, crosswalk=cw_map
                        )
                        _reports_dir = os.path.normpath(
                            os.path.join(self._app_base_dir(), "QLA_Migration", "Reports")
                        )
                        _21g_path, _21g_n = write_premium_basis_report(_21g_rows, _reports_dir)
                        self.log(
                            f"Issue #21G: staged premium/basis totals ({_21g_n} policies) → {_21g_path}"
                        )
                    else:
                        self.log("Issue #21G: skipped — PPBEN/PPBENTYP extracts not found for staging report")
                except Exception as e:
                    self.log(f"Warning: Issue #21G premium/basis staging failed - {e}")
            # ---------------------------------------------------------------------------------------

            # --- Issue #86 / DG-R-003: QuikDate full rebuild (PME dates + screenshot defaults) ---
            if is_batch:
                try:
                    out_dir = self.path_vars["Out"][0].get()
                    qd_info = emit_quikdate_csv(out_dir)
                    self.log(
                        f"Success: quikdate.csv - {qd_info.get('row_count', 1)} record "
                        f"(full rebuild; PME={qd_info.get('prior_month_end')}; "
                        f"VERSION={qd_info.get('VERSION')}; "
                        f"ACHFILEID={qd_info.get('ACHFILEID')}; ACHFILEID2={qd_info.get('ACHFILEID2')})."
                    )
                    self._cut_record(
                        "quikdate",
                        "WRITTEN",
                        output_relpath="quikdate.csv",
                        row_count=qd_info.get("row_count", 1),
                    )
                except Exception as e:
                    self.log(f"Warning: QuikDate governance emit failed - {e}")
                    self._cut_record("quikdate", "FAILED", reason=str(e), output_relpath="quikdate.csv")
            # ---------------------------------------------------------------------------------------

            # --- Issue #120: QuikList group bill master (active six LST groups) ---
            if is_batch:
                try:
                    out_dir = self.path_vars["Out"][0].get()
                    src_dir = self._migration_source_dir()
                    ql_info = emit_quiklist_csv(src_dir, out_dir)
                    self.log(
                        f"Success: quiklist.csv - {ql_info.get('row_count', 0)} records "
                        f"(groups={', '.join(ql_info.get('groups', []))})."
                    )
                    self._cut_record(
                        "quiklist",
                        "WRITTEN",
                        output_relpath="quiklist.csv",
                        row_count=ql_info.get("row_count", 0),
                    )
                except Exception as e:
                    self.log(f"Warning: QuikList group bill emit failed - {e}")
                    self._cut_record("quiklist", "FAILED", reason=str(e), output_relpath="quiklist.csv")
            # ---------------------------------------------------------------------------------------

            # --- Policy Data Governance: internal transformation audit (Reports only) ---
            try:
                from qla_core.policy_data_transforms import write_policy_transform_audit
                _pda_path = write_policy_transform_audit(
                    os.path.normpath(
                        os.path.join(self._app_base_dir(), "QLA_Migration", "Reports")
                    )
                )
                if _pda_path:
                    self.log(f"Policy data transformation audit → {_pda_path}")
            except Exception as e:
                self.log(f"Warning: policy data transformation audit failed - {e}")
            # ---------------------------------------------------------------------------------------

            current_stage = "Running claims / payment outputs"
            batch_claims_result = None
            batch_quikisrr_result = None
            batch_quikiswl_result = None
            if is_batch:
                batch_quikiswl_result = self._execute_batch_quikiswl_seed()
                if batch_quikiswl_result and batch_quikiswl_result.get("status") == "SUCCESS":
                    self._cut_record(
                        "QuikIswl",
                        "WRITTEN",
                        output_relpath="QuikIswl.csv",
                        row_count=(batch_quikiswl_result.get("summary") or {}).get("rows"),
                    )
                elif batch_quikiswl_result and batch_quikiswl_result.get("status") == "SKIPPED":
                    self._cut_record(
                        "QuikIswl",
                        "SKIPPED",
                        reason=str(batch_quikiswl_result.get("reason") or "QUIKISWL_SKIPPED"),
                        output_relpath="QuikIswl.csv",
                    )
                batch_claims_result = self._execute_batch_claims_uat_finale()
                if batch_claims_result and batch_claims_result.get("emit_result"):
                    emit_info = batch_claims_result["emit_result"]
                    self._cut_record(
                        "quikclms",
                        "WRITTEN",
                        output_relpath="quikclms.csv",
                        row_count=emit_info.get("clms_rows") or emit_info.get("rows"),
                    )
                    self._cut_record(
                        "quikclmp",
                        "WRITTEN",
                        output_relpath="quikclmp.csv",
                        row_count=emit_info.get("clmp_rows"),
                    )
                elif is_batch:
                    self._cut_record(
                        "quikclms",
                        "SKIPPED",
                        reason="CLAIMS_UAT_NOT_EMITTED",
                        output_relpath="quikclms.csv",
                    )
                    self._cut_record(
                        "quikclmp",
                        "SKIPPED",
                        reason="CLAIMS_UAT_NOT_EMITTED",
                        output_relpath="quikclmp.csv",
                    )
                batch_quikisrr_result = self._execute_batch_quikisrr_finale(batch_claims_result)
                if batch_quikisrr_result and batch_quikisrr_result.get("status") == "SUCCESS":
                    isrr_summary = batch_quikisrr_result.get("summary") or {}
                    isrr_emitted = isrr_summary.get("emitted") or {}
                    self._cut_record(
                        "QuikIsrr",
                        "WRITTEN",
                        output_relpath="QuikIsrr.csv",
                        row_count=isrr_emitted.get("rows"),
                    )
                elif batch_quikisrr_result and batch_quikisrr_result.get("status") == "SKIPPED":
                    self._cut_record(
                        "QuikIsrr",
                        "SKIPPED",
                        reason=str(batch_quikisrr_result.get("reason") or "QUIKISRR_SKIPPED"),
                        output_relpath="QuikIsrr.csv",
                    )

            if is_batch and hasattr(self, "rate_include_batch_var") and self.rate_include_batch_var.get():
                if self.rate_emit_csv_var.get() or self.rate_emit_dbf_var.get():
                    current_stage = "Generating rate tables"
                    self.update_run_progress(7, detail="factors, keys, member tables")
                    self.log("RATE TABLE GENERATION (Phase R5): batch finale — starting...")
                    self._last_rate_loader_result = self._invoke_rate_loader_runner()
                    self._refresh_rate_loader_visibility()
                    br = self._last_rate_loader_result
                    self.log(
                        f"RATE LOADER (batch finale): status={br.get('status', '?')} "
                        f"blockers={br.get('blockers', '?')} tables={br.get('tables', '?')}"
                    )
                    if br.get("status") in ("SUCCESS", "PARTIAL") or br.get("partial_emit"):
                        rates_dir = os.path.normpath(os.path.join(self.path_vars["Out"][0].get(), "rates"))
                        if os.path.isdir(rates_dir):
                            for fn in sorted(os.listdir(rates_dir)):
                                if not fn.lower().endswith(".csv"):
                                    continue
                                stem = os.path.splitext(fn)[0]
                                self._cut_record(
                                    f"rates/{stem}",
                                    "WRITTEN",
                                    output_relpath=f"rates/{fn}",
                                )
                        # Issue #96 / A7: batch finale must re-apply R7B after rates exist
                        # (same as rate-only path). Without this, VARGP/VARDB stay at the
                        # pre-rate quikplan values (A8b can force annuity VARDB=0).
                        try:
                            from qla_core.quikplan_rate_variation_flags import integrate_quikplan_file
                            qp_path = os.path.normpath(
                                os.path.join(self.path_vars["Out"][0].get(), "quikplan.csv")
                            )
                            if os.path.isfile(qp_path):
                                r7 = integrate_quikplan_file(qp_path, repo_root=self._repo_root())
                                self.log(
                                    f"Issue #96/A7: post-rate quikplan refresh (batch) — "
                                    f"PLANVALOPT=Y plans={r7.planvalopt_y} "
                                    f"blockers={r7.validation_blockers}"
                                )
                        except Exception as exc:
                            self.log(f"Issue #96/A7: post-rate quikplan refresh skipped: {exc}")
                    else:
                        self._cut_record(
                            "rates/QuikUint",
                            "FAILED",
                            reason=f"RATE_LOADER_{br.get('status')}",
                            output_relpath="rates/QuikUint.csv",
                        )
                else:
                    self.log("RATE LOADER (batch finale): skipped — enable CSV or DBF emit in Rate Table Generation panel.")
                    self._cut_record(
                        "rates/QuikUint",
                        "SKIPPED",
                        reason="RATE_EMIT_FORMAT_OFF",
                        output_relpath="rates/QuikUint.csv",
                    )

            val_note = ""
            if is_batch:
                current_stage = "Running data governance audit"
                self.update_run_progress(8, detail="data_governance audit (report-only)")
                self._last_governance_summary = self._run_post_conversion_governance(run_error_log)
                vr = self._last_governance_summary or {}
                if vr.get("status"):
                    self._ui_record_governance_timestamp()
                if vr.get("status") == "PASS":
                    val_note = "\n\nData governance: PASS (see QLA_Migration/Reports/data_governance/)"
                elif vr.get("status") in ("FAIL", "FINDINGS"):
                    val_note = (
                        f"\n\nData governance: {vr.get('total', 0)} finding(s) — "
                        f"Failed={vr.get('failed', vr.get('critical', 0))}, "
                        f"Errors={vr.get('errors', 0)}.\n"
                        f"Report: {vr.get('report_dir', 'Reports/data_governance')}"
                    )
                elif vr.get("status") == "SKIPPED":
                    val_note = "\n\nData governance: skipped."
                elif vr.get("status") == "ERROR":
                    val_note = f"\n\nData governance: error — {vr.get('error', 'see log')}"

            current_stage = "Writing final CSV outputs and summaries"
            self.update_run_progress(9, detail="finalizing")
            package_ok = self._run_output_hygiene(run_error_log)
            cut_ok = True
            if is_batch:
                current_stage = "Cut Completeness Gate"
                self.update_run_progress(9, detail="cut completeness manifest")
                cut_ok = self._evaluate_cut_completeness_gate(package_ok, run_error_log)
            handoff_ok = bool(package_ok and cut_ok)
            if handoff_ok:
                self._launch_dbf_append_tool()
            else:
                if not cut_ok:
                    self.log("DBF Append Tool: launch skipped — Cut Completeness Gate failed")
                else:
                    self.log("DBF Append Tool: launch skipped — Append package gate failed")

            if is_batch and not cut_ok:
                self.fail_run_progress(
                    "Cut Completeness Gate",
                    "Cut manifest FAIL — see QLA_Migration/Reports/cut_manifest_*.json",
                    run_error_log.folder,
                )
                manifest = getattr(self, "_last_cut_manifest", {}) or {}
                findings = manifest.get("findings") or []
                preview = "\n".join(
                    f"- {f.get('code')}: {f.get('detail')}" for f in findings[:12]
                ) or "(see Reports manifest)"
                messagebox.showerror(
                    "Cut Completeness Failed",
                    "Batch tables were written, but the Cut Completeness Gate failed.\n\n"
                    "Complete/Append handoff is blocked.\n\n"
                    f"{preview}\n\n"
                    "Manifest: QLA_Migration/Reports/cut_manifest_latest.json\n"
                    f"Details:\n{run_error_log.folder}",
                )
            elif not package_ok:
                self.fail_run_progress(
                    "Append Tool packaging",
                    "Claims/memo Append package gate failed — see console",
                    run_error_log.folder,
                )
                messagebox.showerror(
                    "Append Package Failed",
                    "Conversion tables were written, but the DBF Append Tool package "
                    "failed validation (claims/memo/payee join).\n\n"
                    "Do not load Append Tool output until this is fixed.\n\n"
                    f"Details:\n{run_error_log.folder}",
                )
            elif is_batch and batch_claims_result and batch_claims_result.get("emit_result"):
                emit_info = batch_claims_result["emit_result"]
                dbf_info = batch_claims_result.get("dbf_result")
                dbf_note = ""
                if dbf_info and dbf_info.get("status") == "SUCCESS":
                    dbf_note = f"\nUAT prototype DBFs generated in:\n{dbf_info.get('dbf_dir', '')}"
                elif self._claims_uat_dbf_generation_enabled():
                    dbf_note = "\nUAT DBF generation attempted — see console for status."
                isrr_note = ""
                if batch_quikisrr_result and batch_quikisrr_result.get("status") == "SUCCESS":
                    isrr_summary = batch_quikisrr_result.get("summary") or {}
                    isrr_emitted = isrr_summary.get("emitted") or {}
                    isrr_note = (
                        f"\n\nQuikIsrr partial-surrender package appended "
                        f"({isrr_emitted.get('rows', '?')} events)."
                    )
                rate_note = ""
                br = getattr(self, "_last_rate_loader_result", None) or {}
                if br.get("status") == "SUCCESS":
                    rate_note = f"\n\nRate tables: {br.get('tables', '?')} tables written to Output/rates/."
                messagebox.showinfo(
                    "Complete",
                    "Batch conversion finished.\n\n"
                    "UAT claims (quikclms/quikclmp) emitted to main output.\n"
                    f"Review holds: {emit_info.get('hold_count', 0)} records "
                    "(claims_review_hold_manifest.csv relocated to QLA_Migration/Reports)."
                    f"{isrr_note}{dbf_note}{rate_note}{val_note}\n\n"
                    "Cut Completeness PASS + Append Tool package validated.",
                )
                self.complete_run_progress()
            else:
                done_msg = "Conversion Finished."
                if is_batch and val_note:
                    done_msg += val_note
                done_msg += "\n\nAppend Tool package validated."
                messagebox.showinfo("Complete", done_msg)
                self.complete_run_progress()
        except Exception as e:
            self.log(f"!!! ERROR: {str(e)}")
            run_error_log.write_exception(current_stage, e)
            run_error_log.write_summary("full_batch" if is_batch else "single_table", "FAILED",
                                        [f"Failed at stage: {current_stage}", f"Error: {e}"])
            self._run_output_hygiene(run_error_log)
            self.fail_run_progress(current_stage, str(e), run_error_log.folder)
            self.log(f"Error details written to: {run_error_log.folder}")
            messagebox.showerror("Conversion Failed",
                                 f"Failed at: {current_stage}\n\nDetails:\n{run_error_log.folder}")
        finally: self.is_running = False

if __name__ == "__main__":
    root = tk.Tk(); app = QLAdminEnterpriseIntegrationSuite(root); root.mainloop()