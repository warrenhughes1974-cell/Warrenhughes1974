# Issue 21K — PUA Amount Precision — Intake Report

**Issue ID:** 21K  
**Title:** PUA Amount Precision  
**Framework stage:** Intake Agent (Stage 1)  
**Generated:** 2026-06-26  
**Engine version at review:** v57.33  
**Code changes:** None

---

## 1. Issue Summary

Paid-Up Addition (PUA) **face amount loses cents** in QLAdmin. LifePRO shows accumulated PUA face **$5,752.96** for policy **010448806C**; QLAdmin displays **$5,752.00**.

The conversion pipeline emits **`quikridr.MUNIT = 5.75296`** and **`MVPU = 1000.00`**, which correctly yields **$5,752.96** (`MUNIT × MVPU`). The cent loss is **not reproduced in `quikridr.csv`**. It aligns with **downstream storage/display** truncating **`MUNIT` to three decimal places** (5.75296 → 5.752 → $5,752.00).

**Severity:** Low–Medium (per-policy dollar accuracy)  
**Owner:** Conversion + Client (New Era) — QLAdmin `MUNIT` precision confirmation  
**Status after intake:** Ready for **Planning Agent** review (pending intake sign-off)

---

## 2. Evidence Reviewed

| Artifact | Location | Role |
|----------|----------|------|
| Issue #21 Final Analysis | `Issue_Log_Items/Issue_21/Issue_21_Final_Analysis.md` | Screenshot confirmation (C11); Issue K rated **High** confidence |
| Issue #21 Remediation Plan | `Issue_Log_Items/Issue_21/Issue_21_Remediation_Plan.md` | 21K listed Phase 1 ready; precision / formatting |
| Issue #21 Tracking Sheet | `Issue_Log_Items/Issue_21/Issue_21_Tracking_Sheet.md` | AWAITING CLIENT (New Era) on `MUNIT` DBF decimal support |
| Master tracking | `Issue_Log_Items/Issue_Log_Master_Tracking_Sheet.md` | 21K open |
| LifePRO evidence packet | `Issue_Log_Items/Issue_21/010448806C - LifePRO.docx` | PUA face $5,752.96 (screenshot) |
| PPBEN extract | `QLA_Migration/Source/PPBEN_PolicyBenefit_Extract_20260530.csv` | Source `NUMBER_OF_UNITS` |
| Converted output | `QLA_Migration/Output/quikridr.csv` | `MUNIT`, `MVPU` |
| Rulebook | `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv` | `NUMBER_OF_UNITS → MUNIT` |
| Issue #26 field defs | `Issue_Log_Items/Issue_26/Issue_26_Field_Definition_Report.md` | QLAdmin Help: `MUNIT` = units; `MVPU` = value per unit |
| Dedicated 21K folder / prior code | — | **None found** |

---

## 3. Trace — Policy 010448806C

### LifePRO source (PPBEN)

| Field | Value | Notes |
|-------|------:|-------|
| LifePRO policy | `9010448806` | Crosswalk → `010448806C` |
| `BENEFIT_SEQ` | **2** | PUA rider |
| `BENEFIT_TYPE` | **PU** | Paid-Up Addition |
| `NUMBER_OF_UNITS` | **5.75296** | Matches client LifePRO units |
| `VALUE_PER_UNIT` | **1000.00** | $1,000 per unit |

**Expected face:** `5.75296 × 1000 = **$5,752.96**`

### Converted CSV (`quikridr.csv`)

| MPHASE | MPLAN | MUNIT | MVPU | MUNIT × MVPU | Match? |
|-------:|-------|------:|-----:|-------------:|:------:|
| 1 | 170858 | 5.77800 | 1000.00 | $5,778.00 | Base coverage |
| 2 | **1708PA** | **5.75296** | **1000.00** | **$5,752.96** | **PUA row** |
| 3 | 170858 | 5.77800 | 1000.00 | $5,778.00 | Duplicate phase row |

**CSV verdict:** **Correct** — PUA row preserves full source precision.

### QUIKRIDR.DBF (post-generation)

| Check | Result |
|-------|--------|
| `quikridr.dbf` in repo / `QLA_Migration/Output/` | **Not present** — policy batch emits **CSV** for `quikridr`; no in-repo QUIKRIDR DBF from conversion |
| DBF generation in conversion pipeline | **Not found** for `quikridr` (unlike `quikmemo_uat_dbf`) |
| Intake DBF read for 010448806C | **Blocked** — no conversion-produced `QUIKRIDR.DBF` available locally |

**Planning will need:** client-supplied `QUIKRIDR.DBF` after QLAdmin load, or documented QLAdmin import path, to confirm stored `MUNIT` decimals.

### QLAdmin observed (client UAT)

| Display | Value |
|---------|------:|
| Accumulated PUA face | **$5,752.00** |
| Implied `MUNIT` if `MVPU=1000` | **5.752** (exactly) |

**Truncation hypothesis (matches observation):**

| Step | MUNIT | Face (×1000) |
|------|------:|-------------:|
| Source / CSV | 5.75296 | $5,752.96 |
| Truncate to **3** decimals | **5.752** | **$5,752.00** ✓ |
| Round to 3 decimals | 5.753 | $5,753.00 ✗ |
| Truncate to 2 decimals | 5.75 | $5,750.00 ✗ |

Cent loss is **consistent with 3-decimal `MUNIT` storage or display**, not CSV rounding.

---

## 4. Affected Field(s)

| Table | Field | Role |
|-------|-------|------|
| **QUIKRIDR** | **MUNIT** | Number of units (`PPBEN.NUMBER_OF_UNITS`) — **primary suspect** |
| **QUIKRIDR** | **MVPU** | Value per unit ($1,000) — **correct at 1000.00** |
| Derived | `MUNIT × MVPU` | PUA face amount shown in QLAdmin |

**Not implicated at CSV layer:** `MPREM`, `MMODEPREM`, fee fields (Issue #26 scope).

---

## 5. Fleet Population (read-only)

Analysis on current `quikridr.csv` (7,002 rows):

| Metric | Count | Notes |
|--------|------:|-------|
| Rows with `MUNIT` **>3** decimal places | **6,262** (89%) | Conversion preserves up to **5** dp |
| Rows with exactly **5** dp | 6,172 | Typical LifePRO precision |
| Rows with `MPLAN` ending **`PA`** (PUA-style) | **494** | Includes `1708PA` pattern |
| PUA-type rows (`MPLAN` ends `PA`) with >3 dp | **488** | Nearly all PUA rows |
| Rows where `MUNIT × MVPU` has **non-zero cents** | **1,070** | Any rider/base with fractional face |
| PPBEN `BENEFIT_TYPE = PU` | **495** | Source PUA benefits |

**Scope conclusion:** Issue is **not isolated to PUA** in conversion output — most `MUNIT` values use **5** decimal places. **PUA is the visible client example** because fractional face amounts are common on PU riders. Any fix must consider **fleet-wide `MUNIT` precision**, not PUA-only formatting.

---

## 6. Suspected Failure Point

| Stage | Cent loss observed? | Assessment |
|-------|:-------------------:|------------|
| LifePRO PPBEN | No | `5.75296` confirmed |
| Crosswalk / rulebook | No | Direct map `NUMBER_OF_UNITS → MUNIT` |
| **`quikridr.csv`** | **No** | `5.75296` preserved |
| CSV → DBF creation (conversion) | **Unknown** | No `quikridr.dbf` emitted by engine |
| **QLAdmin DBF / load** | **Likely** | Tracking sheet cites ~**3** dp truncation |
| **QLAdmin display** | **Likely** | $5,752.00 matches `5.752 × 1000` |

**Primary hypothesis:** QLAdmin **`QUIKRIDR.MUNIT` field definition or load path supports only three decimal places** (truncate), while LifePRO and conversion CSV carry **five**.

**Secondary hypotheses (Planning to rule out):**

- Separate client DBF rebuild with `N(10,3)` vs `N(15,5)`
- Display rounding to whole dollars only (less likely — implied units are 5.752)
- Wrong row loaded (phase/plan mismatch) — **ruled out** for CSV; PUA row is MPHASE 2 / `1708PA`

---

## 7. Initial Scope

### In scope (Planning / future Development)

- Confirm QLAdmin **`MUNIT` DBF type** (length, decimals) from Help or sample DBF
- Confirm client load path: CSV import vs external DBF creation
- Evaluate remediation options if 3 dp is QLAdmin limit:
  - Store scaled units (e.g., thousandths as integer in another field) — **unlikely without client approval**
  - Round/truncate policy for display parity
  - QLAdmin configuration / vendor change
- Fleet impact: **1,070+** rows with fractional dollar face; **6,262** rows with >3 dp `MUNIT`

### Out of scope (intake guardrails)

- No changes to `quikridr` converter, DBF writer, rulebooks, `app.py`, packaging
- No changes to Issue #25 MPOLICY or Issue #26 MPREM
- No PUA-only hack without fleet precision analysis

### Open client question (from tracking sheet)

> Does **QUIKRIDR.MUNIT** support **5** decimal places on DBF load, or is it truncated to **3**? If truncated, how should PUA face amounts with cents be carried?

---

## 8. Where Cents Are Lost — Summary Table

| Layer | 010448806C PUA `MUNIT` | Face amount |
|-------|------------------------|------------:|
| LifePRO | 5.75296 | $5,752.96 |
| `quikridr.csv` | **5.75296** | **$5,752.96** |
| If DBF/QLAdmin 3 dp truncate | 5.752 | **$5,752.00** |
| QLAdmin (client) | (implied 5.752) | **$5,752.00** |

---

## 9. Recommendation for Planning Agent

1. **Do not change conversion CSV emission** until QLAdmin `MUNIT` precision is confirmed — current CSV appears **correct**.
2. **Obtain from client (New Era):**
   - QLAdmin Help or schema extract for **`QuikRidr.MUNIT`** numeric definition (`N(?,?)`)
   - Post-load **`QUIKRIDR.DBF`** row for `010448806C` MPHASE 2 / plan `1708PA`
   - Confirmation of load method (CSV vs DBF)
3. **Planning tasks:**
   - Compare production/working `QUIKRIDR.DBF` `MUNIT` storage to conversion CSV
   - Quantify policies where 3 dp truncation changes face by ≥ $0.01
   - Document remediation options with Risk Agent (format change vs QLAdmin config vs accept rounding)
4. **Trace set for Planning:** `010448806C` (required) + sample from 1,070 fractional-face rows + PUA `1708PA` cohort

**Intake gate G0:** Complete — proceed to Planning after review.

---

## 10. Artifacts to Create in Planning (not done here)

| Artifact | Purpose |
|----------|---------|
| `Issue_21K_Planning_Report.md` | QLAdmin field def, remediation options |
| `Issue_21K_MUNIT_Precision_Trace.csv` | Fleet sample trace |
| Optional `_research_issue21k_munit.py` | Read-only population script |

---

## Related References

- `Issue_Log_Items/Issue_21/Issue_21_Final_Analysis.md` — § Issue K (CONFIRMED)
- `Issue_Log_Items/Issue_21/Issue_21_Tracking_Sheet.md` — row 21K
- `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv` — line 14 `NUMBER_OF_UNITS,MUNIT`

**Stop point:** Intake Agent complete. **Do not proceed to Planning** until intake findings are reviewed.
