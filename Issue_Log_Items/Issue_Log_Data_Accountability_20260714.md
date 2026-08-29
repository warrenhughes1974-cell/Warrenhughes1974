# Issue Log Data Accountability

**Generated:** 2026-08-29T12:40:03  
**Engine batch:** v57.85 full UAT Output  
**Script:** `tools/validators/validate_issue_log_accountability.py` v1.12

## Roll-up

| Status | Count |
|--------|------:|
| IN_DATA (confirmed in Output) | 70 |
| WARN (env / known caveat) | 14 |
| GAP (not confirmed) | 4 |
| SKIP (no validator) | 0 |

## Verdict

**ATTENTION — 4 GAP(s)** must be reviewed before training.

## Detail

| Issue | Status | Evidence |
|-------|--------|----------|
| #2 | **IN_DATA** | validator PASS |
| #25 | **IN_DATA** | validator PASS |
| #13 | **WARN** | validator blocked on missing dated extract (environmental) |
| #26 | **WARN** | validator blocked on missing dated extract (environmental) |
| #28 | **IN_DATA** | validator PASS |
| #36 | **WARN** | MSEMI: non-blank 5083/5083 (100.0%) / MQTRL: non-blank 5083/5083 (100.0%) / MMTHD: non-blank 5083/5083 (100.0%) / MMTHB: non-blank 5083/5083 (100.0%) / PAC spec |
| #38 | **WARN** | validator blocked on missing dated extract (environmental) |
| #49 | **WARN** | atch may be required) / WARN: 01ML8515C: output MSTATUS= expected 22 (rebatch may be required) / WARN: 01ML8535C: output MSTATUS= expected 22 (rebatch may be re |
| #50 | **WARN** | - / WARNINGS /   WARN: Batch quikmemo.csv missing 018495BC /   WARN: No UAT DBF at C:\Users\warren\Documents\GitHub\Warrenhughes1974\QLA_Migration\Output\quikme |
| #51 | **IN_DATA** | validator PASS |
| #54 | **IN_DATA** | validator PASS |
| #55 | **IN_DATA** | validator PASS |
| #57 | **IN_DATA** | validator PASS |
| #58 | **IN_DATA** | validator PASS |
| #59 | **WARN** | 9010803420C: 22 -> 50 /     9010813163C: 44 -> 22 /     9010816990C: 22 -> 53 /     9010882416C: 22 -> 50 /     9010891087C: 22 -> 55 /     9010901657C: 44 -> 2 |
| #60 | **WARN** | 9 / Baseline drift (midyear v57.85 (not same-cut)): date/age/status=112 valuation-sensitive=1758 -> issue60_cross_release_drift.csv / WARN: source-baseline unav |
| #70 | **IN_DATA** | validator PASS |
| #72 | **IN_DATA** | validator PASS |
| #75 | **IN_DATA** | validator PASS |
| #76 | **GAP** | validate_issue76_eti_rpu_payup v2.1 /   valuation date: 2026-06-30 (QLA_VALUATION_DATE=20260630) /   candidates=311 payup_fail=0 mlast_fail=38 / WARN: no same-c |
| #95 | **IN_DATA** | validator PASS |
| #110 | **IN_DATA** | validator PASS |
| #114 | **GAP** | olicies) / OK: dividend-history policies=586 / OK: PPBENTYP lifetime source = 20260630 PPBENTYP_BenefitType_Extract_20260630.csv (593 policies) / WARN: MBENTYP= |
| #116 | **WARN** | rows after=5083 / future MINTDATE with a balance (after): 0 / future MINTDATE on zero-balance rows: 931 (no accrual, not a defect) / WARN: missing-archive: C:\U |
| #117 | **WARN** | 740C  bal   1664.37  3=   543.21 6=  2825.21 7=  1704.05  ->   1664.37  FOOTS /   9010154425C  bal   1100.42  3=   358.99 6=  1841.85 7=  1100.42  ->   1100.42  |
| #120 | **IN_DATA** | validator PASS |
| #21F | **IN_DATA** | validator PASS |
| #21A | **WARN** | validator blocked on missing dated extract (environmental) |
| #21J | **WARN** | MTHB: expected 8.3298, got 0 /   quikplan 10L172 SEMI: expected 50.0000, got 0 /   quikplan 10L172 QTRL: expected 25.0035, got 0 /   quikplan 10L172 MTHD: expec |
| #21M | **WARN** | validator blocked on missing dated extract (environmental) |
| #105 | **IN_DATA** | validator PASS |
| #119 | **IN_DATA** | validator PASS |
| #121 | **IN_DATA** | validator PASS |
| #124 | **IN_DATA** | validator PASS |
| #143 | **IN_DATA** | validator PASS |
| #141 | **IN_DATA** | validator PASS |
| #139 | **IN_DATA** | validator PASS |
| #145B | **IN_DATA** | validator PASS |
| #156 | **IN_DATA** | validator PASS |
| #146 | **IN_DATA** | validator PASS |
| #142 | **IN_DATA** | validator PASS |
| #134 | **IN_DATA** | validator PASS |
| #135 | **IN_DATA** | validator PASS |
| #136 | **IN_DATA** | validator PASS |
| #120 | **IN_DATA** | quiklist rows=6; six active MGROUPs; MCOMP=C; names populated |
| #13 | **IN_DATA** | termination samples 54/56 |
| #2 | **IN_DATA** | quikmstr width11 violations=0; start90=5083/5083; sample 9010143726C present=True |
| #25 | **WARN** | superseded by #2 width-11; legacy width-10 violations=5083 |
| #36 | **IN_DATA** | 010367131C modal factors present |
| #38 | **IN_DATA** | quikdvdp MDEPOSIT non-zero=59/5083 |
| #40/#41 | **IN_DATA** | QuikCvs rows=38490 |
| #41 | **IN_DATA** | 1960PO QuikCvs rows=1002 |
| #98 | **IN_DATA** | 17085M M/14 anchors dur3=.06 dur85=975.61 dur86=1000 |
| #106 | **IN_DATA** | 170858 M/17 Dur2=8.76 Dur83=1000; 1659C2 M/17 ST Dur1=1 Dur83=978 |
| #96 | **IN_DATA** | 1SALMI PVO=Y PlCv=['F', 'M'] PlTv=['F', 'M'] QuikTvs=516; 1L17SP QuikTvs=398 |
| #44 | **IN_DATA** | quikloan rows=353 |
| #45 | **IN_DATA** | MBANKNO populated=2703 |
| #75 | **IN_DATA** | draft MBANKNO filled=2075/2129 invalid=0; 9010161748C=091303855/0000002000581 |
| #47 | **IN_DATA** | MBILLDAY non-zero=5083 |
| #49 | **IN_DATA** | override/preserve traces OK |
| #50 | **IN_DATA** | memo rows=5083; sample hits={'018495BC': True, '01159D276C': True, '01ML8522C': True, '010335038C': True} |
| #51 | **IN_DATA** | QuikAint plans=['A60MIR', 'A96DAR'] |
| #54 | **IN_DATA** | quikbenh=41764 types={'1': 209, '3': 265, '6': 843, '7': 25, '4': 2582, '10': 4141, '11': 14260, '12': 19301, '2': 37, '8': 101} |
| #55 | **IN_DATA** | sub-floor MUNIT=0 |
| #57:010367131C | **IN_DATA** | MNFOPT=2 |
| #57:010392763C | **IN_DATA** | MNFOPT=3 |
| #57:011221309C | **IN_DATA** | MNFOPT=1 |
| #58 | **IN_DATA** | 010367131C non-ISWL fees retained MANNLFEE=10.4400 MSEMIFEE=5.4288 |
| #139 | **IN_DATA** | ISWL 9010713704C fees withheld (0) |
| #58-ISWL | **IN_DATA** | ISWL 9010713704C fees suppressed (0) |
| #59:901122D991C | **IN_DATA** | MSTATUS=22 |
| #59:9014FG8217C | **IN_DATA** | MSTATUS=22 |
| #59:9016FG8217C | **IN_DATA** | MSTATUS=22 |
| #59:901ML8171C | **IN_DATA** | MSTATUS=22 |
| #59:901ML8250C | **IN_DATA** | MSTATUS=22 |
| #59:901ML8522C | **IN_DATA** | MSTATUS=22 |
| #59:010521213C | **GAP** | MSTATUS=53 (expected 50; 20260630 PPOLC_PolicyMaster_Extract_20260630.csv CONTRACT=S/DP -> ST_S_DP=50) |
| #60 | **IN_DATA** | 010310404C PUA phase Chris rules |
| #60:other-rider | **IN_DATA** | 920ADB dates unchanged |
| #56/60 plan | **IN_DATA** | 1960PA absent from quikplan (Chris) |
| #21F | **IN_DATA** | quikprmh CONV_ADJ-like rows=4848 |
| Claims 14-19 | **IN_DATA** | clms=2488 clmp=2981 |
| #105 | **IN_DATA** | MPAR=1 rows=660; mismatches vs plan PAR=0; unresolvable non-PUA plans=0 |
| #119 | **IN_DATA** | PUA rows=494; PUA MPAR!=0=0 |
| #121 | **IN_DATA** | ART policies=197; MSTATUS=44=0; MPHSTAT=44=0 |
| #135 | **GAP** | clms=2488 clmp=2981; MINTAMT_nz=0; marker_308=308; marker_with_payee=0 |
| #136 | **IN_DATA** | 1658C1 BDVARYGP=N STVARYGP=N GDVARYDV=N GDVARYGP=Y; fleet_BDY=0 fleet_STY=0 |
| Engine | **IN_DATA** | expect v57.85 (batch completed) |

## Intentionally not in conversion data

| Issue | Why |
|-------|-----|
| #56 | WITHDRAWN — superseded by #60 |
| #60 Track B (NFOINT) | Blocked — awaiting Chris actuarial rates |
| #23 / #43 | Plan setup (Sujitha) — not app.py emit |
| #18 CFIC rates | Awaiting source tables |
| #21K | Awaiting New Era client |

## Training load

`QLA_Migration/Output/Test_Validation/` (+ `rates/`)

