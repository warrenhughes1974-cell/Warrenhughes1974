# Issue #145B — Analysis Report (proof before code)

**Issue:** #145B — Vanish 0561s Out of ISRR  
**Date:** 2026-08-20  
**Mode:** Analysis only. No conversion code, rulebook, or emit change.  
**Cut:** LifePRO 2026-06-30 / current `QLA_Migration/Output/`  
**Parent:** #145 Vanish Flag (VB) — flag only; Ready for Client UAT  

LifePRO PACTG was read, not modified. QuikIsrr was inspected, not rewritten.

---

## 1. Executive conclusion

**YES — strongly supported, QLA controlled test required.**

The conversion **does** put every unreversed VB 0561 into QuikIsrr as a dollar surrender (`MSURRAMT`). LifePRO **does not** reduce units for those same rows. Conversion Output **still holds LifePRO units** (`MUNIT` = `NUMBER_OF_UNITS` on all 636 VB policies). The unit drop Eric saw in QLAdmin is therefore **not in the CSV we emit**. It is the expected result of QLAdmin anniversary treating QuikIsrr dollars as a face reduction:

```text
QLA units after anniversary  ≈  LifePRO units  −  Σ(unreversed 0561 amount) / VALUE_PER_UNIT
VALUE_PER_UNIT = 1000 on every VB policy
```

That formula reproduces Eric’s live QLAdmin number on **9011050114** exactly (25 − 136/1000 = **24.864**).

**Proven on a live listing (2026-08-20):** `docs/VaxLife_QLAdmin_VPUNITDIFFERENCES.txt` is ValxLife units vs **post-anniversary QLAdmin units** (not conversion `MUNIT`). All three 145B golds match the formula. A controlled load (keep vs drop VB 0561s) is still required before changing emit — this listing is one live run, not an A/B.

**Do not implement yet.**

---

## 1A. Live listing `docs/VaxLife_QLAdmin_VPUNITDIFFERENCES.txt`

345 ISWL rows. Columns: policy, ValxLife units, QLAdmin live units, Diff.

| Policy | Scope | Valx | Live QLA | Diff | Unrev 0561 | Formula units |
|---|---|---:|---:|---:|---:|---:|
| 9011050114 | 145B gold | 25.000 | **24.864** | 0.136 | $136.00 | **24.864** |
| 9011069610 | 145B gold | 50.000 | **49.594** | 0.406 | $406.00 | **49.594** |
| 9010815236 | 145B gold | 24.30594 | **23.597** | 0.70894 | $1,402.56 | **23.59744** |
| 9010761639 | #146 | 25.000 | **24.729** | 0.271 | $271.00 | **24.729** |
| 9010760840 | #146 | 35.000 | **34.284** | 0.716 | $716.40 | **34.2836** |

9010815236 Valx is already `BF_CURRENT_DB / 1000` (24.30594), not LifePRO 25. Live QLA still equals 25 − 1,402.56/1000. Diff on that row is Valx − QLA, not 0561/1000.

Book-level on this differences file (not the whole 636 VB book):

- 288 / 345 live QLA units = seed units − Σ0561/1000 (tol 0.002)
- 28 more match if the latest 0561 is left off (current policy year not anniversary-processed yet)
- 29 leftover rows sit in a ~30-unit staircase at the bottom of the file and do not look like real QLA unit calcs

Join evidence: `Issue_Log_Items/Issue_145B/evidence/issue145b_vpunit_listing_join.csv`

The earlier workbook `docs/Valuation/QLReports/QLAdmin-ValxLife 6-2026 run at 6-2026.xlsx` compared Valx to **conversion** units (still 25/25/50 on the golds). This text file is the live side.

---

## 2. VB identification

**Authoritative source (Issue #145 lock):**

| Item | Value |
|---|---|
| File | `QLA_Migration/Source/PPOLC_PolicyMaster_Extract_20260630.csv` |
| Field | `BILLING_REASON` |
| Code | **VB** |
| Meaning used | On vanish / vanish billing |
| VB policies | **636** |

Billing-reason distribution on the same extract:

| BILLING_REASON | Policies | 145B? |
|---|---:|---|
| (blank) | 3,322 | No — #146 if they have 0561 |
| **VB** | **636** | **Yes** |
| PU | 344 | No |
| RU | 304 | No |
| ET | 291 | No |
| PC | 169 | No |
| WD | 17 | No |

**Not used (and not usable):**

| Candidate | Finding |
|---|---|
| `PPBENTYP.BA_OR_VANISH_FLAG` | Blank on the extract (not a policy-level on-vanish flag) |
| Plan 659 / “eligible to vanish” | Issue #22 trap. Eligibility ≠ on vanish |
| Presence of 0561 | 52 non-VB policies also have 0561 → **#146**, out of scope |

All three golds are VB. #145 already set `quikspec.VANISH=T` on all 636. `VANISHDT` is blank.

---

## 3. Gold policy reconciliation

### 3.1 9010815236

| Item | Value |
|---|---|
| VB | Yes (`BILLING_REASON=VB`, `VANISH=T`) |
| Plan | 659 CEN II → 1659C2 |
| LifePRO units (PPBEN BF seq 1) | **25.00000** |
| VALUE_PER_UNIT | **1000** |
| `ORIGINAL_UNITS` | 0 (not populated — cannot prove a pre-0561 unit field) |
| `BF_CURRENT_DB` | 24,305.94 (not equal to 25,000 − 1,402.56; not the unit story) |
| Conversion `quikridr.MUNIT` | **25.00000** |
| Conversion `QuikIswl.MDB` | **25,000.00** (month 0 seed; anniversary not applied in Output) |
| Billed premium now | 176.67 |

**PACTG 0561:** 9 rows. **8 unreversed**, 1 reversed (2022-10-02, $174.51, already excluded by #34). Unreversed total **$1,402.56**.

All 8 unreversed rows are **Exact Match** in QuikIsrr (same date, same amount). QuikIsrr has no unit column — dollars only.

| Eff date | Amount | Credit | Reversal | QuikIsrr | Match |
|---|---:|---|---|---|---|
| 2018-10-02 | 174.51 | 13 | | 2018-10-02 / 174.51 | Exact |
| 2019-10-02 | 174.51 | 13 | | Exact | Exact |
| 2020-10-02 | 174.51 | 13 | | Exact | Exact |
| 2021-10-02 | 174.51 | 13 | | Exact | Exact |
| 2022-10-02 | 174.51 | 13 | | Exact | Exact |
| 2023-12-12 | 176.67 | 12 | | Exact | Exact |
| 2024-10-02 | 176.67 | 13 | | Exact | Exact |
| 2025-10-02 | 176.67 | 13 | | Exact | Exact |
| 2022-10-02 | 174.51 | 13 | **Y** | not emitted | Reversal excluded |

LifePRO still shows **25 units** after eight years of these 0561s. That is the proof that LifePRO did not treat them as unit surrenders.

**Calculated 0561 unit impact:** 1,402.56 / 1,000 = **1.40256**  
**Counterfactual QLA units if anniversary subtracts face:** 25 − 1.40256 = **23.59744**  
**Output unit difference today:** 25 − 25 = **0**

Eric’s call said “subtracts 1,532 from 25,000.” Source unreversed total is **1,402.56**, not 1,532. The 1,532 figure is **not** reproduced. Do not force it. The 8-row / $1,402.56 / ninth-reversed story from the same call **does** match source.

### 3.2 9011050114

| Item | Value |
|---|---|
| VB | Yes |
| LifePRO units | **25** |
| VPU | **1000** |
| `MUNIT` / `MDB` | 25 / 25,000 |
| 0561 | **1** unreversed, 2017-12-26, **$136.00**, credit 13 |
| QuikIsrr | Exact Match 2017-12-26 / 136.00 |
| Billed premium now | 121.00 (0561 ≠ *today’s* premium; still one no-payee 0561) |

**Impact:** 136 / 1,000 = **0.136**  
**Counterfactual:** 25 − 0.136 = **24.864**  
**Eric’s QLAdmin observation on the call:** 24.864  

This gold **reconciles to the observed QLAdmin unit** under the face-reduction formula. Conversion Output still shows 25.

### 3.3 9011069610

| Item | Value |
|---|---|
| VB | Yes |
| LifePRO units | **50** |
| VPU | **1000** |
| `MUNIT` / `MDB` | 50 / 50,000 |
| 0561 | **1** unreversed, 2026-03-04, **$406.00**, credit 13 |
| QuikIsrr | Exact Match 2026-03-04 / 406.00 |
| Billed premium | 406.00 (amount = current premium) |

**Impact:** 406 / 1,000 = **0.406**  
**Counterfactual:** 50 − 0.406 = **49.594**  
**Output unit difference today:** 0

---

## 4. 0561 → QuikIsrr traceability

Issue #34 emit (`qla_core/quikisrr_loader.py`):

- Source: PACTG debit **0561 / 561**, `REVERSAL_CODE ≠ Y`, ISWL plan allowlist
- Target: `QuikIsrr.csv` columns **MPOLICY, MSURRDATE, MSURRAMT** only  
- `MSURRDATE` = `EFFECTIVE_DATE`  
- `MSURRAMT` = gross `TRANS_AMOUNT`  
- No unit field is converted. No vanish exclusion exists.

Gold match rate: **10 / 10 unreversed = Exact Match**. Reversed row not emitted (correct #34 behavior).

Fleet VB: **3,452** unreversed 0561s and **3,452** QuikIsrr rows on the same 587 policies. **0** VB policies with an unreversed 0561 missing from QuikIsrr.

QuikIsrr does not carry units. The unit effect, if any, is a QLAdmin interpretation of `MSURRAMT` against face (`MUNIT × MVPU`).

---

## 5. Unit reconciliation

**In conversion Output (before QLAdmin anniversary):**

| Policy | VB | LifePRO units | QLA `MUNIT` | Output diff | Unrev 0561s | 0561 $ | 0561 unit impact | Counterfactual after anniv | Reconciles to Eric / formula? |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 9010815236 | Yes | 25 | 25 | 0 | 8 | 1,402.56 | 1.40256 | 23.59744 | Formula yes. Live “1,532” no. |
| 9011050114 | Yes | 25 | 25 | 0 | 1 | 136.00 | 0.136 | **24.864** | **Yes — matches Eric 24.864** |
| 9011069610 | Yes | 50 | 50 | 0 | 1 | 406.00 | 0.406 | 49.594 | Formula yes. Live QLA not in repo. |

**Full VB book (636):** `MUNIT` equals LifePRO `NUMBER_OF_UNITS` on **every** VB policy (0 already-reduced in Output).

---

## 6. Population (recalculated, not assumed)

| Metric | Count |
|---|---:|
| VB policies (`BILLING_REASON=VB`) | **636** |
| VB with any unreversed 0561 | **587** |
| VB with no 0561 | **49** |
| Unreversed VB 0561 rows | **3,452** |
| Reversed VB 0561 rows | 43 |
| Those 3,452 in QuikIsrr | **3,452** (587 policies) |
| VB Output `MUNIT` ≠ LifePRO units | **0** |
| VB `VALUE_PER_UNIT` ≠ 1000 | **0** |
| Non-VB unreversed 0561 policies | 52 / 209 rows → **#146 only** |

The prior “587 / 3,452” counts **confirm** on this cut.

`ORIGINAL_UNITS` is 0 on all 636 VB BA/BF rows. We cannot show a LifePRO “units before first 0561” column. We **can** show current LifePRO units after years of 0561s are still the issue-size counts (25, 50, etc.).

---

## 7. Exceptions / outliers

1. **Output does not yet show the unit drop.** Hypothesis is anniversary-in-QLAdmin, not converter math. Without a post-anniversary extract, fleet “QLA units vs 0561 impact” cannot be scored policy-by-policy from Output.
2. **9010815236 “$1,532”** from the call does not match source **$1,402.56**. Use source.
3. **9011050114 $136 ≠ current premium $121.** Still a single no-payee 0561. Warren’s lock for 145B is **all** 0561s on VB, not only amount=today’s premium.
4. **9010815236 one 0561 credits 0012** (2023-12-12, $176.67 = then/now premium). Still no payee. Included in the “all VB 0561s” rule.
5. **`BF_CURRENT_DB` 24,305.94** on 9010815236 is **not** 25,000 − 1,402.56 (= 23,597.44). Do not use current DB as the 0561 unit proof.
6. **49 VB policies have no 0561.** Exclusion is a no-op for them. Vanish flag (#145) still applies.
7. **#146 leftovers** (9010761639 $271 / 25 units; 9010760840 2×$358.20 / 35 units) are the same transaction type and are **out of scope**.

---

## 8. Root-cause assessment

The evidence supports this chain:

```text
LifePRO PACTG 0561 (premium-from-values, units unchanged)
    → Issue #34 emit
    → QuikIsrr MSURRAMT = 0561 dollars (no units)
    → QLAdmin anniversary (not in conversion Output)
    → face' = MUNIT × 1000 − Σ MSURRAMT
    → units' = face' / 1000
```

**Where it happens:** after load, in QLAdmin processing of QuikIsrr — **not** in LifePRO units, **not** in `quikridr.MUNIT` at emit.

Issue #145 (`VANISH=T`) is already on these policies. It has not been proven in this repo to block that anniversary reduction. #145B is the history exclusion if the flag is not enough.

---

## 9. Implementation recommendation

**Proceed to controlled UAT exclusion test. Do not implement conversion change yet.**

Reasons:

- PACTG → QuikIsrr lineage is exact.
- LifePRO units are proven unchanged.
- Dollar → unit math is identified (`amount / 1000`) and matches one live QLAdmin observation.
- Post-anniversary QLA units are not in Output, so a controlled QLAdmin run is the missing proof.
- Do not delete LifePRO PACTG. Future change is emit-only.

If the test fails (units still drop with empty QuikIsrr), the cause is not 0561 history and #145B should not ship.

---

## 10. Controlled UAT test design (do not execute)

**Population:** 9010815236C, 9011050114C, 9011069610C only.

| Leg | QuikIsrr |
|---|---|
| **Control** | Current file (0561s present) |
| **Test** | Same conversion; **only** these three policies’ QuikIsrr rows removed. PACTG untouched. `quikridr.MUNIT` / `quikspec.VANISH` unchanged. |

Load both packages the same way. Run anniversary / ISWL processing on both.

Compare per policy:

| Check | Expected if hypothesis is true |
|---|---|
| Loaded `MUNIT` before anniversary | 25 / 25 / 50 on both legs |
| Units after anniversary | Control ≈ 23.59744 / 24.864 / 49.594; Test = 25 / 25 / 50 |
| `MDB` / Amount Ins | Control reduced; Test = 25,000 / 25,000 / 50,000 |
| Premium history / billed premium | No change |
| Cash / fund values | Watch; must not invent a new break |
| Non-gold policies | Unchanged (test file only strips the three) |

**Pass:** Test preserves LifePRO units; Control reproduces the drop; nothing else material moves.  
**Fail:** Test still drops units, or Control does not drop — then 0561-out-of-ISRR is the wrong lever.

---

## Confidence by gold

| Policy | Classification | Why |
|---|---|---|
| 9011050114 | **STRONGLY SUPPORTED** | Exact emit + formula = Eric’s 24.864. Output still 25. |
| 9011069610 | **STRONGLY SUPPORTED** | Exact emit + amount = premium + formula 49.594. No live QLA number in repo. |
| 9010815236 | **STRONGLY SUPPORTED** (source); live “1,532” **not** confirmed | Exact 8-row emit; LP units 25; formula 23.59744. Call’s 1,532 does not match. |

**Fleet:** STRONGLY SUPPORTED for emit + LifePRO units. INCONCLUSIVE for actual post-anniversary QLA units until the UAT test.

---

## Artifacts

| File | Content |
|---|---|
| `evidence/issue145b_analysis_summary.json` | Population and VB ID |
| `evidence/issue145b_gold_detail.json` | Full gold traces |
| `evidence/issue145b_gold_pactg_isrr_trace.csv` | PACTG ↔ QuikIsrr line matches |
| `evidence/issue145b_vb_population_recon.csv` | 636 VB rows: LP units, MUNIT, 0561 impact |

Read-only probe used to build the package: `_analyze_145b_0561_units.py`. It does not change emit.

---

## What this analysis did not do

- Did not change `app.py`, QuikIsrr emit, or PACTG.
- Did not mix #146.
- Did not treat 0561-on-VB as automatically excluded in production.
- Did not run the UAT test.
