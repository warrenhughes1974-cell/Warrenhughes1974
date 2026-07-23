# Issue Log Data Accountability

**Generated:** 2026-07-22T20:40:39  
**Engine batch:** v57.85 full UAT Output  
**Script:** `tools/validators/validate_issue_log_accountability.py` v1.0

## Roll-up

| Status | Count |
|--------|------:|
| IN_DATA (confirmed in Output) | 42 |
| WARN (env / known caveat) | 7 |
| GAP (not confirmed) | 2 |
| SKIP (no validator) | 0 |

## Verdict

**ATTENTION — 2 GAP(s)** must be reviewed before training.

## Detail

| Issue | Status | Evidence |
|-------|--------|----------|
| #25 | **IN_DATA** | validator PASS |
| #13 | **WARN** | validator blocked on missing dated extract (environmental) |
| #26 | **WARN** | validator blocked on missing dated extract (environmental) |
| #28 | **IN_DATA** | validator PASS |
| #36 | **IN_DATA** | validator PASS |
| #38 | **WARN** | validator blocked on missing dated extract (environmental) |
| #49 | **IN_DATA** | PASS functional gates; 7 #59 deltas expected |
| #50 | **IN_DATA** | validator PASS |
| #51 | **IN_DATA** | validator PASS |
| #54 | **IN_DATA** | validator PASS |
| #55 | **IN_DATA** | validator PASS |
| #57 | **IN_DATA** | validator PASS |
| #58 | **IN_DATA** | validator PASS |
| #59 | **WARN** | validator vs Output may show #49 override; check patched MSTATUS below |
| #60 | **GAP** | validate_issue60_pua_phase.py 1.0 / PUA rows checked: 494 / Other later-phase rows checked: 1357 / FAIL /   PUA 010391355C: MLASTANN != base /   PUA 010391876C: |
| #21F | **IN_DATA** | validator PASS |
| #21A | **WARN** | validator blocked on missing dated extract (environmental) |
| #21J | **WARN** | MTHB: expected 8.3298, got 0 /   quikplan 10L172 SEMI: expected 50.0000, got 0 /   quikplan 10L172 QTRL: expected 25.0035, got 0 /   quikplan 10L172 MTHD: expec |
| #21M | **WARN** | validator blocked on missing dated extract (environmental) |
| #13 | **IN_DATA** | termination samples 54/56 |
| #25 | **IN_DATA** | quikmstr MPOLICY width violations=0 |
| #36 | **IN_DATA** | 010367131C modal factors present |
| #38 | **IN_DATA** | quikdvdp MDEPOSIT non-zero=59/5083 |
| #40/#41 | **IN_DATA** | QuikCvs rows=37999 |
| #41 | **IN_DATA** | 1960PO QuikCvs rows=1000 |
| #98 | **IN_DATA** | 17085M M/14 anchors dur3=.06 dur85=975.61 dur86=1000 |
| #44 | **IN_DATA** | quikloan rows=356 |
| #45 | **IN_DATA** | MBANKNO populated=1824 |
| #47 | **IN_DATA** | MBILLDAY non-zero=5083 |
| #49 | **IN_DATA** | override/preserve traces OK |
| #50 | **IN_DATA** | memo rows=5083; sample hits={'018495BC': True, '01159D276C': True, '01ML8522C': True, '010335038C': True} |
| #51 | **IN_DATA** | QuikAint plans=['A60MIR', 'A96DAR'] |
| #54 | **IN_DATA** | quikbenh=41066 types={'10': 4118, '11': 14156, '12': 19135, '8': 3657} |
| #55 | **IN_DATA** | sub-floor MUNIT=0 |
| #57:010367131C | **IN_DATA** | MNFOPT=2 |
| #57:010392763C | **IN_DATA** | MNFOPT=3 |
| #57:011221309C | **IN_DATA** | MNFOPT=1 |
| #58 | **IN_DATA** | 010367131C MANNLFEE=10.4400 MSEMIFEE=5.4288 |
| #59:01122D991C | **IN_DATA** | MSTATUS=22 |
| #59:014FG8217C | **IN_DATA** | MSTATUS=22 |
| #59:016FG8217C | **IN_DATA** | MSTATUS=22 |
| #59:01ML8171C | **IN_DATA** | MSTATUS=22 |
| #59:01ML8250C | **IN_DATA** | MSTATUS=22 |
| #59:01ML8522C | **IN_DATA** | MSTATUS=22 |
| #59:010521213C | **GAP** | MSTATUS=22 (Death Claim Pending) |
| #60 | **IN_DATA** | 010310404C PUA phase Chris rules |
| #60:other-rider | **IN_DATA** | 920ADB dates unchanged |
| #56/60 plan | **IN_DATA** | 1960PA absent from quikplan (Chris) |
| #21F | **IN_DATA** | quikprmh CONV_ADJ-like rows=2609 |
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

