# Issue Log Data Accountability

**Generated:** 2026-07-25T17:53:31  
**Engine batch:** v57.85 full UAT Output  
**Script:** `tools/validators/validate_issue_log_accountability.py` v1.1

## Roll-up

| Status | Count |
|--------|------:|
| IN_DATA (confirmed in Output) | 41 |
| WARN (env / known caveat) | 13 |
| GAP (not confirmed) | 9 |
| SKIP (no validator) | 0 |

## Verdict

**ATTENTION — 9 GAP(s)** must be reviewed before training.

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
| #49 | **WARN** | ch may be required) / WARN: 01ML8515C: output MSTATUS= expected 22 (rebatch may be required) / WARN: 01ML8535C: output MSTATUS= expected 22 (rebatch may be requ |
| #50 | **WARN** | review:  /   010335038C len: 0 / ------------------------------------------------------------------------ / WARNINGS /   WARN: Batch quikmemo.csv missing 018495 |
| #51 | **IN_DATA** | validator PASS |
| #54 | **GAP** | 5, '10': 3562, '2': 37, '8': 3657} / OK: MBENTYP=8 preserved (3657 rows) / OK: loan-history policies=665 / OK: no MBENTYP=20 rows (deferred) / OK: MDATE YYYYMMD |
| #55 | **GAP** | s): 0 / Trace policies: /   018495BC P1: MISSING /   018495BC P2: MISSING /   018499CC P1: MISSING /   018499CC P2: MISSING /   018510C P1: MISSING /   018510C  |
| #57 | **IN_DATA** | validator PASS |
| #58 | **WARN** | base rows=5083 MANNLFEE>0=4457 modal_fees_populated=4457 / FAIL /   trace policy missing: 010367131C /   trace policy missing: 010560185C /   trace policy missi |
| #59 | **WARN** | validator vs Output may show #49 override; check patched MSTATUS below |
| #60 | **IN_DATA** | validator PASS |
| #72 | **IN_DATA** | validator PASS |
| #75 | **IN_DATA** | validator PASS |
| #76 | **IN_DATA** | validator PASS |
| #110 | **IN_DATA** | validator PASS |
| #114 | **IN_DATA** | validator PASS |
| #21F | **WARN** | =============================================================== /  / quikprmh rows: 209480 /   schema order: PASS /  / [Golden] 010310404C CONV_ADJ rows: 0 /  / |
| #21A | **WARN** | validator blocked on missing dated extract (environmental) |
| #21J | **WARN** | MTHB: expected 8.3298, got 0 /   quikplan 10L172 SEMI: expected 50.0000, got 0 /   quikplan 10L172 QTRL: expected 25.0035, got 0 /   quikplan 10L172 MTHD: expec |
| #21M | **WARN** | validator blocked on missing dated extract (environmental) |
| #105 | **IN_DATA** | validator PASS |
| #13 | **IN_DATA** | termination samples 54/56 |
| #2 | **IN_DATA** | quikmstr width11 violations=0; start90=5083/5083; sample 9010143726C present=True |
| #25 | **WARN** | superseded by #2 width-11; legacy width-10 violations=5083 |
| #36 | **IN_DATA** | 010367131C modal factors present |
| #38 | **IN_DATA** | quikdvdp MDEPOSIT non-zero=59/5083 |
| #40/#41 | **IN_DATA** | QuikCvs rows=38359 |
| #41 | **IN_DATA** | 1960PO QuikCvs rows=1000 |
| #98 | **IN_DATA** | 17085M M/14 anchors dur3=.06 dur85=975.61 dur86=1000 |
| #106 | **IN_DATA** | 170858 M/17 Dur2=8.76 Dur83=1000; 1659C2 M/17 SM Dur1=1 Dur83=978 |
| #96 | **IN_DATA** | 1SALMI PVO=Y PlCv=['F', 'M'] PlTv=['F', 'M'] QuikTvs=516; 1L17SP QuikTvs=56 |
| #44 | **IN_DATA** | quikloan rows=356 |
| #45 | **IN_DATA** | MBANKNO populated=2703 |
| #75 | **IN_DATA** | draft MBANKNO filled=2078/2132 invalid=0; 9010161748C=091303855/0000002000581 |
| #47 | **IN_DATA** | MBILLDAY non-zero=5083 |
| #49 | **IN_DATA** | override/preserve traces OK |
| #50 | **IN_DATA** | memo rows=5083; sample hits={'018495BC': True, '01159D276C': True, '01ML8522C': True, '010335038C': True} |
| #51 | **IN_DATA** | QuikAint plans=['A60MIR', 'A96DAR'] |
| #54 | **IN_DATA** | quikbenh=43589 types={'1': 209, '3': 264, '4': 2569, '11': 14156, '12': 19135, '10': 3562, '2': 37, '8': 3657} |
| #55 | **IN_DATA** | sub-floor MUNIT=0 |
| #57:010367131C | **IN_DATA** | MNFOPT=2 |
| #57:010392763C | **IN_DATA** | MNFOPT=3 |
| #57:011221309C | **IN_DATA** | MNFOPT=1 |
| #58 | **IN_DATA** | 010367131C MANNLFEE=10.4400 MSEMIFEE=5.4288 |
| #59:01122D991C | **GAP** | MSTATUS=None |
| #59:014FG8217C | **GAP** | MSTATUS=None |
| #59:016FG8217C | **GAP** | MSTATUS=None |
| #59:01ML8171C | **GAP** | MSTATUS=None |
| #59:01ML8250C | **GAP** | MSTATUS=None |
| #59:01ML8522C | **GAP** | MSTATUS=None |
| #59:010521213C | **GAP** | MSTATUS=22 (Death Claim Pending) |
| #60 | **IN_DATA** | 010310404C PUA phase Chris rules |
| #60:other-rider | **IN_DATA** | 920ADB dates unchanged |
| #56/60 plan | **IN_DATA** | 1960PA absent from quikplan (Chris) |
| #21F | **IN_DATA** | quikprmh CONV_ADJ-like rows=2619 |
| Claims 14-19 | **IN_DATA** | clms=5594 clmp=6422 |
| #105 | **IN_DATA** | MPAR=1 rows=3388; mismatches vs plan PAR=0; PUA via base plan=493; unresolvable plans=0 |
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

