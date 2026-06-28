# Issue #27 — Root Cause Analysis

**Issue:** SL Phase of Insurance  
**Date:** 2026-06-28  
**Version:** v57.38 (analysis only)  
**Primary evidence policy:** `010448806C`

---

## 1. Executive finding

**Root cause: CONFIRMED — converter issue (benefit-type mapping gap).**

The converter emits LifePRO `BENEFIT_TYPE = SL` rows as **full `quikridr` coverage phases**, mapping `NUMBER_OF_UNITS` and `VALUE_PER_UNIT` to `MUNIT` and `MVPU`. LifePRO carries the **same face amount** on the SL row as the base benefit for **substandard table-rating context**, not as an additive death benefit. QLAdmin correctly displays what was converted — a **separate coverage row with duplicate amount insured**.

This is **not** a QLAdmin product-setup defect and **not** a source extract omission. It is **incorrect semantic treatment of SL at conversion time**.

---

## 2. Evidence — policy `010448806C`

### 2.1 LifePRO PPBEN source rows

| BENEFIT_SEQ | BENEFIT_TYPE | PLAN_CODE | UNITS | VPU | Amount Ins | ANN_PREM/UNIT | MODE_PREM | ISSUE_AGE |
|-------------|--------------|-----------|-------|-----|------------|---------------|-----------|-----------|
| 1 | **BA** | 670 GL85-8 | 5.77800 | 1000.00 | **5,778.00** | 18.96000 | 62.40 | 32 |
| 2 | **PU** | 670 PUA | 5.75296 | 1000.00 | 5,752.96 | 0.00 | 0.00 | 34 |
| 3 | **SL** | 670 GL85-8 | 5.77800 | 1000.00 | **5,778.00** | 0.00 | 0.00 | 32 |

**Observations:**
- SL row uses **same plan and same units/VPU as base BA row** → duplicate face amount in source.
- SL row has **zero premium** on this policy — consistent with rating-only row.
- `UNDERWRITING_CLASS` = 0 on all rows (rating not in PPBEN UW class field).

### 2.2 LifePRO PPBENTYP (substandard metadata)

| BENEFIT_SEQ | TYPE_CODE | SL_TABLE_CODE | SL_2ND_TABLE_CODE | SL_PREMIUMS_PAID |
|-------------|-----------|---------------|-------------------|------------------|
| 1 | BA | — | — | — |
| 2 | PU | — | — | — |
| 3 | **SL** | **32** | (blank) | 0.00 |

**Observation:** Substandard **table rating (32)** lives in PPBENTYP, **not** currently mapped to QLAdmin.

### 2.3 Converted QUIKRIDR output

| MPHASE | MPLAN | MUNIT | MVPU | Amount Ins | MPREM | MEFFDATE |
|--------|-------|-------|------|------------|-------|----------|
| 1 | 170858 | 5.77800 | 1000.00 | **5,778.00** | 18.96000 | 19740215 |
| 2 | 1708PA | 5.75296 | 1000.00 | 5,752.96 | 0.00 | 19760215 |
| 3 | 170858 | 5.77800 | 1000.00 | **5,778.00** | 0.00 | 19740215 |

**Matches client screenshot:** Phase 1 and Phase 3 both show plan `170858` with **5,778.00** amount insured. Phase 2 is PUA (`1708PA`).

### 2.4 QLAdmin display vs converted data

QLAdmin Coverage tab is displaying converted `quikridr` rows faithfully. The **duplicate face amount is present in conversion output**, not introduced by QLAdmin UI alone.

---

## 3. Current converter behavior

### 3.1 QUIKRIDR source filtering (`app.py`)

Only **`UV`** and **`FV`** benefit types are removed from PPBEN before quikridr conversion:

```5042:5050:app.py
                    if 'BENEFIT_TYPE' in source.columns:
                        _qr_bt = source['BENEFIT_TYPE'].astype(str).str.strip().str.upper()
                        _qr_uv_removed = int((_qr_bt == 'UV').sum())
                        _qr_fv_removed = int((_qr_bt == 'FV').sum())
                        source = source[~_qr_bt.isin(['UV', 'FV'])]
```

**`SL` is not filtered** — passes through as a normal benefit row.

### 3.2 Phase mapping (`Sync_Rulebook_quikridr.csv`)

| Source | Target | Effect |
|--------|--------|--------|
| `BENEFIT_SEQ` | `MPHASE` | SL seq 3 → MPHASE 3 |
| `NUMBER_OF_UNITS` | `MUNIT` | Full face units copied |
| `VALUE_PER_UNIT` | `MVPU` | 1000.00 copied |
| `PLAN_CODE` | `MPLAN` (via resolver) | Same base plan code → 170858 |
| `UNDERWRITING_CLASS` | `MUWCLASS` | 0 (SL table rating **not** mapped) |

### 3.3 Related patterns already handled differently

| Type | Treatment |
|------|-----------|
| **PU** | PUA product detection → separate plan (`1708PA`), deferred inheritance |
| **UV / FV** | Filtered out of quikridr |
| **SL** | **No special handling** — emitted as coverage |

---

## 4. Hypothesis test result

| Hypothesis | Result |
|------------|--------|
| SL is substandard rating, not additive death benefit | **Supported** — PPBENTYP `SL_TABLE_CODE` populated; SL premium often zero; same face as base |
| Converter treats SL as normal coverage | **Confirmed** |
| QLAdmin mis-display without conversion fault | **Rejected** for duplicate face — data is in quikridr |
| SL should be ignored entirely | **Partially** — row should not create coverage; rating data may need mapping elsewhere |

---

## 5. Expected QLAdmin representation (planning view)

| Data element | Expected handling |
|--------------|-------------------|
| Base death benefit | Single BA/BF phase with `MUNIT` × `MVPU` |
| Substandard table rating | **`SL_TABLE_CODE`** → QLAdmin UW / table rating field (e.g. `MUWCLASS` or client-approved field) on **base phase** |
| SL extra premium (when present) | Fold into base premium or dedicated extra-premium field — **requires client decision** |
| SL as separate coverage phase | **Should NOT appear** with duplicate face amount |

---

## 6. Root cause statement

> LifePRO `SL` benefit rows are **substandard rating segments** that mirror base face amount in PPBEN for rating purposes. The converter **does not classify SL as non-coverage** and maps units/VPU into `quikridr`, producing an extra phase that QLAdmin displays as **duplicate amount insured**.

**Classification:** Converter / benefit-type semantic mapping issue.  
**Confidence:** **High** (trace policy + fleet pattern + code path).

---

## 7. Files likely requiring modification (future Development — not now)

| File | Likely change |
|------|---------------|
| `app.py` / `QLA_Migration/app.py` | SL filter or SL-specific emit rules in quikridr batch |
| `qla_core/non_product_row_governance.py` (or new helper) | SL governance classification |
| `Sync_Rulebook_quikridr.csv` | Possible UW/table-rating mapping from PPBENTYP cache |
| `tools/validators/validate_issue27_sl_quikridr.py` | **New** — fleet SL regression validator |

**Not expected:** quikplan, crosswalk, quikmstr, DBF generator changes.

---

## 8. Regression risks (future fix)

- Removing 68 quikridr rows → row count 7,002 → **6,934**
- `MPHASE` renumbering if downstream expects gapless phases — **verify quikclid / claims links**
- 28 SL rows with non-zero premium — premium must not be lost if SL row suppressed
- Protected issues #21K (MRIDRID width), #26 (MPREM), #28 (MPLAN authority)

---

**Analysis status:** ✅ COMPLETE
