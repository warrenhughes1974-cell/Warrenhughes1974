# Issue #145B — Controlled UAT Plan (A/B)

**Issue:** #145B — Vanish 0561s Out of ISRR  
**Date:** 2026-08-20  
**Mode:** UAT preparation only. **No converter change. No APP_VERSION bump. Output root not modified.**

This package proves or disproves whether QuikIsrr 0561 dollars cause QLAdmin anniversary to reduce units on three VB golds. It is **not** an implementation of the fleet emit exclusion.

---

## Hypothesis

Unreversed PACT 0561s on VB policies emit to QuikIsrr as `MSURRAMT`. After anniversary:

`Expected Control units ≈ LifePRO units − Σ(unreversed 0561) / 1000`

VPU = $1,000 on the VB book. Test removes only those QuikIsrr rows; starting `MUNIT` stays at LifePRO units. If Test keeps 25 / 25 / 50 and Control drops, #145B emit exclusion is supported.

---

## What was not changed

| Item | Status |
|---|---|
| `app.py` / `QLA_Migration/app.py` | Unchanged |
| APP_VERSION | Unchanged |
| Rulebooks / crosswalks | Unchanged |
| PACTG source | Unchanged |
| `QLA_Migration/Output/` (all tables) | Unchanged — this **is** Control |
| Issue #146 leftovers | Unchanged (still in both QuikIsrr files) |
| Issue #34 emit logic | Unchanged |

---

## Packages

| Leg | QuikIsrr file | Everything else |
|---|---|---|
| **CONTROL** | `uat/CONTROL/QuikIsrr.csv` (byte-identical to `QLA_Migration/Output/QuikIsrr.csv`) | Current `QLA_Migration/Output/` |
| **TEST** | `uat/TEST/QuikIsrr.csv` (10 gold 0561 rows removed) | **Same** `QLA_Migration/Output/` tables — do not swap mstr/ridr/iswl/spec/clnt |

SHA-256:

| File | Hash |
|---|---|
| Control / Output `QuikIsrr.csv` | `667d73c79889bf6dd81bcf201ce25928b89004b99d38ff8340e9dd92cad0c6d0` |
| Test `QuikIsrr.csv` | `ac6e1c4b01d7be2d8b3dbc01482827a6876a21a91a9965819fb7055bf6893919` |

Other Output hashes (must be identical on both legs): see `uat/comparison/issue145b_control_vs_test.json` → `output_sha256`.

**Load rule:** two equivalent QLAdmin environments. Same DBF append of current Output, except Test replaces only QuikIsrr with the Test file. Then run the same anniversary / ISWL processing on both.

Do not publish Test QuikIsrr to `Output/` or `Output/Test_Validation/`. That would look like a shipped fix.

---

## Gold evidence (pre-load)

| Policy | VB | Unrev 0561 in QuikIsrr | Dates | Amounts | Total $ | Reversal | LP units | Output MUNIT | Expected Control | Expected Test |
|---|---|---:|---|---|---:|---|---:|---:|---:|---:|
| 9010815236C | Yes | 8 | 20181002; 20191002; 20201002; 20211002; 20221002; 20231212; 20241002; 20251002 | 174.51 ×5; 176.67 ×3 | 1,402.56 | Unreversed (2022 reverse already out) | 25 | 25 | **23.59744** | **25** |
| 9011050114C | Yes | 1 | 20171226 | 136.00 | 136.00 | Unreversed | 25 | 25 | **24.864** | **25** |
| 9011069610C | Yes | 1 | 20260304 | 406.00 | 406.00 | Unreversed | 50 | 50 | **49.594** | **50** |

9011050114C is the anchor: 24.864 already matched Eric’s QLAdmin screen.

Removed-row list: `uat/comparison/issue145b_removed_quikisrr_rows.csv` (exactly **10** rows, **$1,944.56**).

---

## Comparison validation (package build)

| Check | Result |
|---|---|
| Rows removed | **10** |
| Policies affected | 9010815236C, 9011050114C, 9011069610C only |
| Gold rows left in Test | **0** |
| Non-gold QuikIsrr tuples Control vs Test | **Identical** |
| #146 examples still in Test | 9010761639C + 9010760840C (3 rows) |
| PACTG / MUNIT / QuikIswl / other tables | Not copied, not edited |
| Control QuikIsrr vs Output | SHA identical |

---

## After anniversary — decision rule

### PASS / supports #145B emit exclusion

Control ≈ 23.59744 / 24.864 / 49.594 **and** Test = 25 / 25 / 50.

Then a VB-only QuikIsrr 0561 exclusion is justified. Implementation is a **later** approval, not this package.

### FAIL / do not implement

Test still loses units after those 10 rows are gone. 0561 history is not the lever. Do not code the exclusion.

Record actuals in `Issue_145B_UAT_Result_Capture.md`.

---

## Rollback

1. Discard the Test QuikIsrr file. Do not append it to production templates.  
2. Control is current Output — no restore needed if Output was never overwritten.  
3. If someone copied Test into `QLA_Migration/Output/QuikIsrr.csv`, restore from `uat/CONTROL/QuikIsrr.csv` (same SHA as the build-time Output hash above).  
4. No git revert of converter code is required; none was changed.

---

## Scope

#145B = `PPOLC.BILLING_REASON=VB` only. This UAT is **three golds**, not the 587-policy book. The 52 non-VB 0561 policies stay on **#146**.
