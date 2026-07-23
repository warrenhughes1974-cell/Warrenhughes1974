# Issue Log Data Accountability

**Generated:** 2026-07-23T10:11:20  
**Engine batch:** v57.85 full UAT Output  
**Script:** `tools/validators/validate_issue_log_accountability.py` v1.0

## Roll-up

| Status | Count |
|--------|------:|
| IN_DATA (confirmed in Output) | 20 |
| WARN (env / known caveat) | 12 |
| GAP (not confirmed) | 20 |
| SKIP (no validator) | 0 |

## Verdict

**ATTENTION — 20 GAP(s)** must be reviewed before training.

## Detail

| Issue | Status | Evidence |
|-------|--------|----------|
| #25 | **IN_DATA** | validator PASS |
| #13 | **WARN** | validator blocked on missing dated extract (environmental) |
| #26 | **WARN** | validator blocked on missing dated extract (environmental) |
| #28 | **IN_DATA** | validator PASS |
| #36 | **WARN** | MSEMI: non-blank 5083/5083 (100.0%) / MQTRL: non-blank 5083/5083 (100.0%) / MMTHD: non-blank 5083/5083 (100.0%) / MMTHB: non-blank 5083/5083 (100.0%) / PAC spec |
| #38 | **WARN** | validator blocked on missing dated extract (environmental) |
| #49 | **WARN** | atch may be required) / WARN: 01ML8515C: output MSTATUS= expected 22 (rebatch may be required) / WARN: 01ML8535C: output MSTATUS= expected 22 (rebatch may be re |
| #50 | **WARN** | preview:  /   010335038C len: 0 / ------------------------------------------------------------------------ / WARNINGS /   WARN: Batch quikmemo.csv missing 01849 |
| #51 | **IN_DATA** | validator PASS |
| #54 | **GAP** | 6, '12': 19135, '10': 3562, '8': 3657} / OK: MBENTYP=8 preserved (3657 rows) / OK: loan-history policies=665 / OK: no MBENTYP=20 rows (deferred) / OK: MDATE YYY |
| #55 | **GAP** | its): 0 / Trace policies: /   018495BC P1: MISSING /   018495BC P2: MISSING /   018499CC P1: MISSING /   018499CC P2: MISSING /   018510C P1: MISSING /   018510 |
| #57 | **GAP** | TRACE ERIC 010148272C: MNFOPT=0 expected=2 / TRACE ERIC 010143726C: MNFOPT=0 expected=2 / TRACE ERIC 010392763C: MNFOPT=0 expected=3 / TRACE ERIC 011221309C: MN |
| #58 | **WARN** | base rows=5083 MANNLFEE>0=4457 modal_fees_populated=4457 / FAIL /   trace policy missing: 010367131C /   trace policy missing: 010560185C /   trace policy missi |
| #59 | **WARN** | validator vs Output may show #49 override; check patched MSTATUS below |
| #60 | **GAP** | validate_issue60_pua_phase.py 1.0 / PUA rows checked: 494 / Other later-phase rows checked: 1357 / FAIL /   TRACE missing golden policy 010310404C /   PUA 90103 |
| #21F | **WARN** | =============================================================== /  / quikprmh rows: 209480 /   schema order: PASS /  / [Golden] 010310404C CONV_ADJ rows: 0 /  / |
| #21A | **WARN** | validator blocked on missing dated extract (environmental) |
| #21J | **WARN** | MTHB: expected 8.3298, got 0 /   quikplan 10L172 SEMI: expected 50.0000, got 0 /   quikplan 10L172 QTRL: expected 25.0035, got 0 /   quikplan 10L172 MTHD: expec |
| #21M | **WARN** | validator blocked on missing dated extract (environmental) |
| #13 | **GAP** | termination samples mismatch |
| #25 | **GAP** | quikmstr MPOLICY width violations=5083 |
| #36 | **IN_DATA** | policies with modal factors=4983 |
| #38 | **IN_DATA** | quikdvdp MDEPOSIT non-zero=59/5083 |
| #40/#41 | **IN_DATA** | QuikCvs rows=37999 |
| #41 | **IN_DATA** | 1960PO QuikCvs rows=1000 |
| #98 | **IN_DATA** | 17085M M/14 anchors dur3=.06 dur85=975.61 dur86=1000 |
| #96 | **IN_DATA** | 1SALMI PVO=Y PlCv=['F', 'M'] PlTv=['F', 'M'] QuikTvs=508; 1L17SP QuikTvs=38 |
| #44 | **IN_DATA** | quikloan rows=356 |
| #45 | **IN_DATA** | MBANKNO populated=1824 |
| #47 | **IN_DATA** | MBILLDAY non-zero=5083 |
| #49 | **GAP** | 018252C= 018187C= |
| #50 | **IN_DATA** | memo rows=5083; sample hits={'018495BC': True, '01159D276C': True, '01ML8522C': True, '010335038C': True} |
| #51 | **IN_DATA** | QuikAint plans=['A60MIR', 'A96DAR'] |
| #54 | **IN_DATA** | quikbenh=40510 types={'11': 14156, '12': 19135, '10': 3562, '8': 3657} |
| #55 | **IN_DATA** | sub-floor MUNIT=0 |
| #57:010367131C | **GAP** | MNFOPT= expected 2 |
| #57:010392763C | **GAP** | MNFOPT= expected 3 |
| #57:011221309C | **GAP** | MNFOPT= expected 1 |
| #58 | **GAP** | 010367131C modal fees missing |
| #59:01122D991C | **GAP** | MSTATUS=None |
| #59:014FG8217C | **GAP** | MSTATUS=None |
| #59:016FG8217C | **GAP** | MSTATUS=None |
| #59:01ML8171C | **GAP** | MSTATUS=None |
| #59:01ML8250C | **GAP** | MSTATUS=None |
| #59:01ML8522C | **GAP** | MSTATUS=None |
| #59:010521213C | **GAP** | MSTATUS= (Death Claim Pending) |
| #60 | **GAP** | golden PUA=None |
| #60:other-rider | **GAP** | ADB=None |
| #56/60 plan | **IN_DATA** | 1960PA absent from quikplan (Chris) |
| #21F | **IN_DATA** | quikprmh CONV_ADJ-like rows=2619 |
| Claims 14-19 | **IN_DATA** | clms=5594 clmp=6422 |
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

