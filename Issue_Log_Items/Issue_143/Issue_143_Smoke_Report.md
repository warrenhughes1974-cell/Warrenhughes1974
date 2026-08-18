# Issue #143 — Final Release Smoke Report

**Generated:** 2026-08-18T13:44:00Z  
**Overall:** **PASS** (9 / 9)  
**Recommendation:** **FINAL SIGN-OFF COMPLETE — CLOSED**

A FAIL on any condition blocks final release sign-off.

---

## Authorized reseed confirmation

| Item | Result |
|------|--------|
| Action | Existing Issue #124 emit only — `python Issue_Log_Items/Issue_124/tools/quikiswl_emit.py` |
| Rule used | Unchanged `MDB = MUNIT × 1000` |
| #143 / #124 / smoke validator code | **Not modified** |
| Production / conversion logic | **Not modified** |
| Emit status | SUCCESS |
| QuikIswl rows | **2,268** (same as pre-reseed) |
| Skipped missing issue / bad unit / orphan | 0 / 0 / 0 |
| Unrelated rows with `MDB ≠ current MUNIT × 1000` | **0** |

Pre-reseed stored MDB for the 23 came from the prior smoke snapshot (`evidence/issue143_smoke_summary.json` mismatches). Post-reseed values are from current `QLA_Migration/Output/QuikIswl.csv`.

---

## Gold-policy trace — `9010757606C`

| Field | Value |
|-------|------:|
| Corrected `MUNIT` | **19.10196** |
| `MVPU` | **1000.00** |
| Amount Ins | **19101.96** |
| Pre-reseed stored `MDB` | 25000.00 |
| Post-reseed stored `MDB` | **19101.96** |
| Expected `MUNIT × 1000` | **19101.96** |

---

## Pre/post MDB for all 23 affected records

| Policy | Pre MDB | Post MDB | Expected (`MUNIT × 1000`) | Match |
|--------|--------:|---------:|--------------------------:|:-----:|
| 9010757606C | 25000.00 | 19101.96 | 19101.96 | Yes |
| 9010760069C | 25000.00 | 20367.07 | 20367.07 | Yes |
| 9010766847C | 25000.00 | 5163.41 | 5163.41 | Yes |
| 9010774868C | 25000.00 | 22995.64 | 22995.64 | Yes |
| 9010780870C | 25000.00 | 21457.07 | 21457.07 | Yes |
| 9010786243C | 25000.00 | 21899.80 | 21899.80 | Yes |
| 9010796917C | 25000.00 | 20860.18 | 20860.18 | Yes |
| 9010805394C | 25000.00 | 18394.00 | 18394.00 | Yes |
| 9010812930C | 30000.00 | 12506.02 | 12506.02 | Yes |
| 9010823867C | 25000.00 | 4572.08 | 4572.08 | Yes |
| 9010823868C | 25000.00 | 6384.28 | 6384.28 | Yes |
| 9010823869C | 25000.00 | 9320.78 | 9320.78 | Yes |
| 9010823870C | 25000.00 | 6869.97 | 6869.97 | Yes |
| 9010826422C | 50000.00 | 9655.90 | 9655.90 | Yes |
| 9010835334C | 10000.00 | 4509.17 | 4509.17 | Yes |
| 9010847463C | 25000.00 | 20295.98 | 20295.98 | Yes |
| 9010885442C | 25000.00 | 20961.55 | 20961.55 | Yes |
| 9010933370C | 25000.00 | 19216.77 | 19216.77 | Yes |
| 9011001627C | 30000.00 | 3044.64 | 3044.64 | Yes |
| 9011025612C | 5000.00 | 2742.60 | 2742.60 | Yes |
| 9011044907C | 35000.00 | 21084.59 | 21084.59 | Yes |
| 9011069977C | 25000.00 | 12625.25 | 12625.25 | Yes |
| 9011154856C | 25000.00 | 6104.75 | 6104.75 | Yes |

**Unexpected QuikIswl differences:** none. Non-#143 ISWL rows still satisfy `MDB = current MUNIT × 1000`. Row count unchanged at 2,268.

---

## Final 9-condition smoke result

Command: `python tools/validators/validate_issue143_smoke.py` → **PASS 9/9**  
Release smoke (captured live 2026-08-18T08:48:36, not assumed): `python tools/validators/validate_release_closed_issues.py --smoke-only` → **OVERALL: RELEASE_OK** (includes `#143 BF RPU MUNIT` **PASS**)

| # | Condition | Result |
|---|-----------|--------|
| 1 | 23 authorized BF RPU still have corrected MUNIT | **PASS** |
| 2 | Gold 9010757606C MUNIT=19.10196 MVPU=1000 Amount Ins=19101.96 | **PASS** |
| 3 | 23 rows MUNIT×MVPU = BF_CURRENT_DB / Column DD | **PASS** |
| 4 | 82 aligned BF RPU unchanged | **PASS** |
| 5 | 199 BA RPU receive no #143 remap | **PASS** |
| 6 | MPREM / MVPU / MSAVEUNIT / MPOLICY unaffected | **PASS** |
| 7 | Issue #55 and #108A protections pass | **PASS** |
| 8 | After authorized #124 reseed, MDB = corrected MUNIT×1000 | **PASS** |
| 9 | No unauthorized MUNIT changes outside the 23 | **PASS** |

**Issue #143 Smoke: PASS**

---

## Final recommendation

**FINAL SIGN-OFF COMPLETE — CLOSED**
