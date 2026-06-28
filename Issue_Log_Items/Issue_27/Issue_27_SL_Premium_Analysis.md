# Issue #27 — SL Premium Analysis

**Issue:** SL Phase of Insurance — Premium-bearing SL rows  
**Date:** 2026-06-28  
**Population:** 28 of 68 SL rows with `MODE_PREMIUM` and/or `ANN_PREM_PER_UNIT` > 0  
**Detail file:** `Issue_27_SL_Premium_Population.csv`

---

## 1. Executive summary

SL row premium is **not** a separate rider premium in the LifePRO model for most policies. It is the **substandard / table-rating extra premium component** that LifePRO stores on the SL benefit row. **`PPOLC.MODE_PREMIUM` (and `quikmstr.MMODEPREM`) already equals base premium + SL premium** for **21 of 28** policies.

**Suppressing SL quikridr rows would NOT remove total policy premium** from `quikmstr`. It **would** remove duplicate face amount and may affect per-phase `MPREM` display on a phantom SL phase.

---

## 2. Pattern analysis (28 rows)

| Pattern | Count | Description |
|---------|------:|-------------|
| **Additive (Y)** | **21** | `BASE_MODE_PREM + SL_MODE_PREM ≈ PPOLC_MODE_PREM` (±$0.10) |
| **Partial** | **7** | Mismatch — base zero, paid-up context, or rounding |
| **Zero-face extra premium** | **2** | SL amount = 0, SL premium > 0 (clear table extra only) |

---

## 3. Example — additive pattern (table extra mortality)

**010799083C**

| Source | MODE_PREM | Face |
|--------|-----------|------|
| Base (seq 1) | 88.97 | 25,000 |
| SL (seq 2) | 86.77 | 25,000 (duplicate) |
| PPOLC total | **175.73** | — |
| Check | 88.97 + 86.77 = **175.74** ✓ | |

**Interpretation:** SL premium is **additional mortality charge**, not independent coverage premium.

---

## 4. Example — zero-face table extra (ISWL family)

**010770580C / 010782078C**

| | SL amount | SL MODE_PREM | Base MODE_PREM | PPOLC MODE_PREM |
|---|-----------|--------------|----------------|-----------------|
| 010770580C | 0 | 18.91 | 65.09 | 65.09 |
| 010782078C | 0 | 8.05 | 37.99 | 37.99 |

**Note:** For 010770580C, SL premium (18.91) does **not** add to PPOLC total — PPOLC equals base only. Classified **PARTIAL** — possible timing, billing mode, or LifePRO billing allocation difference.

**Interpretation:** When face = 0, SL row carries **rating/premium metadata only** — strongest evidence SL is not death benefit.

---

## 5. Example — client trace policy (no SL premium)

**010448806C**

| Seq | Type | MODE_PREM | ANN_PPU |
|-----|------|-----------|---------|
| 1 BA | 62.40 | 18.96 |
| 2 PU | 0.00 | 0.00 |
| 3 SL | **0.00** | 0.00 |

PPBENTYP: `SL_TABLE_CODE = 32`, `SL_PREMIUMS_PAID = 0`

**Suppressing SL row:** No premium loss. Removes duplicate 5,778 face only.

---

## 6. Partial pattern cases (7) — need client review

| Policy | Notes |
|--------|-------|
| 010770580C, 010782078C | SL prem present, not additive to PPOLC |
| 010987095C | SL prem 1.22, PPOLC equals base exactly |
| 011104570C, 011182954C | Base MODE_PREM = 0 |
| 011208333C, 011208334C | Base MODE_PREM = 0, SL prem small |

These may involve paid-up, lapsed, or billing-allocation edge cases — **not blockers** for suppressing duplicate face, but **premium display rules** need client sign-off.

---

## 7. Would suppressing SL incorrectly remove premium?

| Layer | Impact if SL row suppressed |
|-------|----------------------------|
| **quikmstr.MMODEPREM** | **No change** — sourced from PPOLC, not SL row |
| **quikprmh payment history** | **No change** — from PACTG |
| **quikridr SL phase MPREM** | **Removed** — extra per-unit rate no longer on phantom phase |
| **QLAdmin Coverage tab prem/unit on SL row** | **Removed** — desired if row should not exist |

**Risk:** If QLAdmin derives modal breakdown from **sum of phase premiums** rather than `MMODEPREM`, suppressing SL could change **displayed** modal breakdown — **requires QLAdmin SME confirmation**. Evidence favors `MMODEPREM` as authoritative policy total (#26 field definition work).

---

## 8. SL_TABLE_CODE vs premium

| SL_TABLE_CODE | Rows (28 prem) | Typical role |
|---------------|----------------|--------------|
| `00` | 10 | Table rating code present; often high extra prem |
| `01`–`08` | 14 | Numeric table identifiers |
| `04`, `02`, etc. | mixed | Legacy GL/term plans |

Premium magnitude correlates with **table extra / mortality charge**, not separate product pricing.

---

## 9. Conclusions

1. **28 SL premium rows are NOT independent rider premiums** in the majority case — they are **substandard extra premium components**.
2. **Total policy premium is already on quikmstr** via PPOLC for most policies.
3. **Suppressing SL quikridr rows does not inherently break MODE_PREMIUM conversion.**
4. **7 partial cases** need client confirmation on edge-case billing — do not block duplicate-face fix.
5. **Optional enhancement:** fold SL `ANN_PREM_PER_UNIT` into base phase `MPREM` for display — **separate decision**, not required to fix duplicate face.

---

**Premium analysis status:** ✅ COMPLETE
