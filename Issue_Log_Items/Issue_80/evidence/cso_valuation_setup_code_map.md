# Issue #80 — QLAdmin code map for CSO Valuation Setup

**Authority rates/methods:** `docs/Valuation_Setup.xlsx`  
**Code semantics:** `docs/claims_conversion_reference/QLAdmin_Help.pdf`  
**Blank rule (CSO / user 2026-07-17):** If Valuation_Setup leaves a cell blank, that assumption **does not apply** to the plan. Emit blank. Do not invent a value.

---

## 1. Interest rate codes (NFOINT and RSVINT)

Source: QLAdmin Help §6.10 **Reserve Interest Rate Chart** (Help PDF ~p.644).  
NFOINT and RSVINT use this same one-character chart (matches prior CSO mortality crosswalk usage).

| Rate in Valuation_Setup | Code |
|-------------------------|:----:|
| 2.50% (0.025) | `2` |
| 3.00% (0.030) | `4` |
| 3.50% (0.035) | `6` |
| 4.50% (0.045) | `A` |
| 5.00% (0.050) | `C` |
| 5.50% (0.055) | `E` |
| 6.00% (0.060) | `G` |

(Full chart also defines 2.25%→`1` through 10.75%→`Z`; only rates above appear in Valuation_Setup.)

---

## 2. Interest method (INTMETHCV / INTMETHTV)

Source: QLAdmin Help Plan Information / Reserves (Help PDF ~p.546) and QuikPlan field text (~p.849).

| Valuation_Setup text | Code | Meaning |
|----------------------|:----:|---------|
| Curtate | `0` | Curtate (point-in-time compounding at end of year) |
| Continuous | `1` | Continuous compounding |

All 65 Valuation_Setup rows say Curtate → emit `0`.

---

## 3. Reserve method (RSVMETH)

Source: QLAdmin Help Reserves settings (Help PDF ~p.546).

| Valuation_Setup text | Code | Meaning |
|----------------------|:----:|---------|
| NLP | `1` | Net Level |
| Full Preliminary Term | `2` | Full Preliminary Term |
| CRVM | `3` | Commissioners Reserve Valuation Method |
| Modified RVM | `4` | Modified Reserve Valuation Method |

Valuation_Setup uses only NLP and CRVM.

---

## 4. STOREMEANS / CALCMIDS (logical)

Source: QLAdmin Help QuikPltv field descriptions (Help PDF ~p.864):

| Field | Help meaning |
|-------|----------------|
| STOREMEANS | Plan reserve factors are **mean** factors; **default FALSE = terminal factors** |
| CALCMIDS | Calculate **mid-terminal** reserves; **default FALSE = mean reserves** |

| Valuation_Setup text | Emit |
|----------------------|------|
| Store Means: Default (Terminal) | STOREMEANS = **False** (terminal factors) |
| Calc Mids: Default (Mean) | CALCMIDS = **False** (mean reserves, not mid-terminal) |

---

## 5. Mortality codes already present as codes in the workbook

Source: QLAdmin Help §6.9 Mortality Table Codes.

| Workbook value | Help meaning |
|----------------|--------------|
| A1 | 1980 CSO Male |
| C1 | 1980 CET Male |
| N1 | 1941 CSO |
| O1 | 1958 CSO |
| Q1 | 1958 CET |

These load as written when the cell is already a two-character code.

---

## 6. ETIMORT for END85 (locked 2026-07-17)

Workbook text for `221END` / `222END` was `1941 CET 2.5% NLP`. Help has no 1941 CET code.  
**User direction:** use **1941 CSO** → ETIMORT = **`N1`**.

---

## 7. Blank cells

Blank MORT / ETIMORT / NFOINT in Valuation_Setup → leave the corresponding QuikPlCv / QuikPlTv / quikplan field blank. Those assumptions do not apply.
