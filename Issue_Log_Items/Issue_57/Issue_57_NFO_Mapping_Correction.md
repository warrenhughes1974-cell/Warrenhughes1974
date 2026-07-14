# Issue #57 — NFO Mapping Correction (Eric + Product Book)

**Date:** 2026-07-13  
**Authority:** LifePRO Product Book §12 / 6.167 — NB New Business Defaults (NFO field) + Eric email/examples  
**Framework:** Planning addendum (no code)  

---

## LifePRO NFO codes (Product Book — definitive)

| Code | Name | Description |
|:---:|------|-------------|
| **0** | Lapse | Policy lapses |
| **1** | APL/ETI | APL attempted; if not possible → ETI |
| **2** | APL/RPU | APL attempted; if not possible → RPU |
| **3** | **APL** | Automatic premium loan is processed |
| **4** | **ETI** | Extended term insurance is purchased |
| **5** | **RPU** | Reduced paid-up insurance is purchased |
| **6** | APL/AR | APL attempted; else annuity rider pays premium |
| **7** | AR | Annuity rider pays premium (even if taxable) |
| **8** | Process NFO | Process nonforfeiture options in specified order |
| **9** | Special | Pay from dividend accumulations (then further rules) |

## QLAdmin `MNFOPT` domain (only four values)

| QLA | Name |
|:---:|------|
| **0** | None / Lapse |
| **1** | APL |
| **2** | ETI |
| **3** | RPU |

**Critical:** LifePRO numbers ≠ QLA numbers. Especially **LifePRO 3 = APL** but **QLA 3 = RPU**.

---

## Correct mapping (what conversion should do)

| LifePRO | Meaning | → QLA `MNFOPT` | Why |
|:---:|------|:---:|------|
| 0 | Lapse | **0** | Same concept |
| 1 | APL/ETI | **1 APL** | Eric/SME: APL attempted first |
| 2 | APL/RPU | **1 APL** | Eric/SME: APL attempted first |
| **3** | **APL** | **1 APL** | Same primary action; **must not passthrough as 3** |
| **4** | **ETI** | **2 ETI** | Same election; LP 4 ≠ QLA 2 |
| **5** | **RPU** | **3 RPU** | Same election; LP 5 ≠ QLA 3 |
| 6 | APL/AR | **0** or **1**? | No AR in QLA; recommend **1 APL** if APL-first, else **0** — confirm with Eric |
| 7 | AR | **0** | No QLA AR option |
| 8 | Process | **0** | No QLA equivalent |
| 9 | Special | **0** | Already `NF_9→0` |

---

## What is wrong today (not primarily the rulebook)

Rulebook `Sync_Rulebook_quikmstr.csv` has:

- `NFO_OPT → MNFOPT` default **0** (PPOLC often blank)
- Engine then **enriches from PPBENTYP** `NON_FORFEITURE` / `BF_NON_FORFEITURE` when value is 0
- Values are translated via `Master_Value_Translation.csv` with prefix **`NF_`**

| LifePRO | Current translation / behavior | Result in QLA | Correct |
|:---:|------|------|------|
| 1 | `NF_1→1` (#21A) | APL ✓ | APL |
| 2 | `NF_2→1` (#21A) | APL ✓ | APL |
| **3** | **No `NF_3`** → **numeric passthrough `3`** | Shows as **RPU** ✗ | **APL (1)** |
| **4** | **`NF_4→0` / `NFO_4→0`** | None ✗ | **ETI (2)** |
| **5** | **`NF_5→0` / `NFO_5→0`** | None ✗ | **RPU (3)** |
| 9 | `NF_9→0` | None ✓ | None |

**Root cause:** Wrong / missing entries in **`Master_Value_Translation.csv`** (both repo root and `QLA_Migration/Mapping/`), left that way under the #21A “codes 3–6 unchanged” scope lock — which we now know was incorrect for **3, 4, and 5**.

The rulebook default of 0 is fine; the PPBENTYP cache path is fine. The **translation table** is what needs updating.

---

## Eric’s examples — verified against current Output

| Policy | LifePRO code | Should be (QLA) | Current `MNFOPT` | Display today | Verdict |
|--------|:---:|:---:|:---:|------|------|
| **010367131C** | 4 ETI | **2 ETI** | **0** | None | Wrong — `NF_4→0` |
| **010148272C** | 4 ETI | **2 ETI** | **0** | None | Wrong |
| **010143726C** | 4 ETI | **2 ETI** | **0** | None | Wrong |
| **010392763C** | 5 RPU | **3 RPU** | **0** | None | Wrong — `NF_5→0` |
| **011221309C** | 3 APL | **1 APL** | **3** | **RPU** | Wrong — passthrough; QLA 3 means RPU |

---

## Fleet impact (if translation fixed)

| Change | Policies affected (approx.) |
|--------|----------------------------:|
| Code 4 @0 → **2** | **2,014** |
| Code 5 @0 → **3** | **41** |
| Code 3 @3 → **1** | **~106** (need force remap, not only enrich-on-zero) |
| Codes 1–2 | Already mostly correct (#21A) |

**Important for code 3:** enrich-on-zero **will not fix** `011221309C` because current value is already **3** (non-zero). Development must either:
- Add `NF_3→1` **and** ensure translation runs on the passthrough value (it already does via `NF_` prefix — adding `NF_3,1` is enough if value is still `"3"` before translate), or  
- Explicitly remap after cache pull.

When value is `"3"`, engine does `trans_map.get("NF_3", …)` — **adding `NF_3,1` fixes it** without needing enrich-on-zero.

---

## Recommended Development changes (do not implement until Risk + approval)

1. Update **both** `Master_Value_Translation.csv` files:
   - `NF_3,1` and `NFO_3,1` (**new**)
   - `NF_4,0` → `NF_4,2` ; `NFO_4,0` → `NFO_4,2`
   - `NF_5,0` → `NF_5,3` ; `NFO_5,0` → `NFO_5,3`
   - Leave `NF_1`, `NF_2`, `NF_9` as-is
2. Confirm with Eric: codes **6 / 7 / 8** → **0** (no QLA AR / Process)
3. Validator: Eric’s five policies + fleet counts
4. Regression: do not break #21A APL for codes 1–2; do not touch MPREM / MPOLICY

---

## Prior wrong assumption (corrected)

Earlier #21A/#57 planning treated LifePRO **code 3 as RPU-like passthrough**. Product Book + Eric prove **code 3 = APL**. That is why `011221309C` shows **RPU** in QLAdmin today.
