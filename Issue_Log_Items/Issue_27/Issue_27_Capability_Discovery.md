# Issue #27 — Capability Discovery

**Issue:** SL Phase of Insurance — QLAdmin Substandard Life Support  
**Date:** 2026-06-28  
**Version:** v57.38 (research only)

---

## 1. Research objective

Determine whether QLAdmin already provides a **native** representation for LifePRO Substandard Life (`SL`) / table rating **before** asking the client to invent a destination field.

**Conclusion:** QLAdmin has **related underwriting fields** on coverage and policy master, but **no confirmed native home for LifePRO `SL_TABLE_CODE` table ratings** in the current conversion pipeline. Substandard Life is **not** implemented as a separate product feature in this repository.

---

## 2. Repository search summary

| Search area | Finding |
|-------------|---------|
| `SL_TABLE_CODE` / `PPBENTYP` | Present in LifePRO source only — **zero conversion mappings** |
| Substandard / table rating / flat extra | Issue #27 planning docs only; no converter logic |
| `MUWCLASS` | QUIKRIDR field — mapped from PPBEN `UNDERWRITING_CLASS`, **not** `SL_TABLE_CODE` |
| `MSPCODE` | QUIKRIDR + QUIKMSTR schema field — **unmapped**, **blank fleet-wide** |
| `MISSCLASS` | QUIKMSTR schema field — governance default `00`, **unmapped**, **blank fleet-wide** |
| `QuikUndw` / Underwriting tab | QLAdmin Help — pending UW **reasons** (new business); **not converted** in batch |
| `QuikPlUw` | Product setup UW **class members** (PR, NS, SM, ST) for **rate tables** — not policy table rating |
| `QuikBene` | QLAdmin Help references policy benefits table — **not in converter `TABLE_SCHEMAS`** |
| Rate loader `TYPE_CODE = SL` | **Excluded** from rate import (actuarial grid type code — unrelated to PPBEN benefit type SL) |
| `non_product_row_governance.py` | UV/FV/seq 99 only — **SL not classified** |
| PUA / rate-up validation | `Data_Goverence.txt` line 214: *"Look at validations for quikridr MPLAN add logic PUA's and rateups"* — **acknowledged, not implemented** |

---

## 3. QLAdmin schema — policy conversion outputs

### 3.1 QUIKRIDR (Coverage Information Master)

From `qladmin_core/qladmin_units_schema.py` (QLAdmin Help §7.203):

| Field | Type | Length | Current conversion use |
|-------|------|--------|------------------------|
| **MUWCLASS** | CHARACTER | 2 | Mapped: PPBEN `UNDERWRITING_CLASS` via rulebook |
| **MBAND** | CHARACTER | 2 | Default `01` (rate band) |
| **MSPCODE** | CHARACTER | 4 | **Not mapped** — empty all rows |
| MUNIT / MVPU / MPREM | numeric | — | Face + rate from **every** benefit row including SL |

**Fleet `MUWCLASS` values:** `41`, `55`, `0`, `B`, `Q`, `T`, etc. — standard underwriting class codes from LifePRO, **not** table numbers like `32`.

**SL policies (67):** predominantly `MUWCLASS = 0` (94 phase rows), also `55`, `B`, `41` — none match `SL_TABLE_CODE` values (`32`, `04`, `02`, …).

### 3.2 QUIKMSTR (Policy Master)

| Field | Governance note | Conversion |
|-------|-----------------|------------|
| **MISSCLASS** | Default `00` (`Data_Goverence.txt`) | **Not mapped** — empty |
| **MSPCODE** | In schema | **Not mapped** — empty |
| **MMODEPREM** | Policy modal premium | PPOLC `MODE_PREMIUM` (total premium) |

### 3.3 QLAdmin Help (extracted)

| Feature | Purpose | Converted? |
|---------|---------|------------|
| **Coverage tab** | Displays `quikridr` phases — amount insured = MUNIT × MVPU | ✅ via quikridr.csv |
| **Underwriting tab** | Pending reasons, memos (`QuikUndw`, `QuikUwcd`, `QuikUwmm`) | ❌ |
| **Premium History** | References *"Extra premium amounts"* to over/short accounts | Runtime — not quikridr phase |
| **Mortality Table Codes** | Help section 9 — product/reference codes | Product setup (QUIKQXS), not policy SL |

### 3.4 Product setup (quikplan / rate loader)

| Artifact | Role vs SL |
|----------|------------|
| `QuikPlUw` | UW class **dimension** for gross premium rate segmentation (PR, NS, ST, …) |
| `UWVARY*` flags on quikplan | Vary rates by underwriting class — **actuarial**, not per-policy table rating storage |
| Rate table `UNDERWRITING_CLASS` column | Pricing grid dimension — **not** policy substandard table code |

---

## 4. Answers to required questions

### 4.1 Does QLAdmin already support Substandard Life?

**Partially — not as implemented today.**

| Capability | Supported in QLAdmin? | Supported in conversion? |
|------------|----------------------|--------------------------|
| Separate SL coverage phase with face amount | QLAdmin **displays** quikridr rows | ✅ **Incorrectly** — creates duplicate |
| Table rating / substandard code on coverage | **Unknown** — candidate fields exist (`MUWCLASS`, `MSPCODE`) but semantics unverified | ❌ |
| Table rating on policy master | **Unknown** — `MISSCLASS` exists, unused | ❌ |
| Underwriting pending reasons | Yes (Underwriting tab) | ❌ Not converted |
| Total premium incl. substandard extra | Yes (`quikmstr.MMODEPREM`) | ✅ PPOLC total |

### 4.2 Where would it be stored (if native)?

**Best-effort candidates from schema only — NOT validated with QLAdmin SME:**

| Candidate | Fit for `SL_TABLE_CODE` | Risk |
|-----------|-------------------------|------|
| `quikridr.MUWCLASS` (2 char) | Poor — already used for `UNDERWRITING_CLASS`; values don't match table codes | Semantic collision |
| `quikridr.MSPCODE` (4 char) | Possible — length fits `32`, `04`; **unused** | **Requires client confirmation** |
| `quikmstr.MISSCLASS` (2 char) | Possible for policy-level class | **Requires client confirmation** |
| Separate `QuikBene` / Underwriting tables | Help references exist | **Not in conversion scope today** |

### 4.3 Can `SL_TABLE_CODE` map directly?

**Not without client QLAdmin SME sign-off.**

- `SL_TABLE_CODE` is **authoritative in LifePRO** (`PPBENTYP`) for 66/68 SL rows.
- No existing crosswalk or value translation maps table codes to QLAdmin fields.
- **`MUWCLASS` direct map is NOT supported by evidence** — different code systems (example: `010448806C` has `UNDERWRITING_CLASS=0` but `SL_TABLE_CODE=32`).

### 4.4 If no native representation?

**Confirmed for conversion scope:** No implemented path stores Substandard Life table rating. Current behavior incorrectly uses **an extra quikridr coverage phase** as the representation.

---

## 5. LifePRO vs QLAdmin model gap

```
LifePRO                          Current conversion           QLAdmin display
─────────────────────────────────────────────────────────────────────────────
BA row  → base face + base prem  → quikridr phase 1           Coverage row 1
PU row  → PUA face               → quikridr phase 2 (PUA)     Coverage row 2
SL row  → same face (rating ctx) → quikridr phase 3 (dup!)    Coverage row 3 DUPLICATE
         table code in PPBENTYP  → (not mapped)                (not visible)
         extra prem on SL row    → MPREM on SL phase           Prem/Unit on dup row
PPOLC   → total MODE_PREMIUM    → quikmstr.MMODEPREM          Mode Prem (correct)
```

---

## 6. Recommendation for client discussion

1. **Do not** represent SL as a quikridr coverage phase (converter fix — suppress SL emit).
2. **Ask QLAdmin SME** which field displays **table rating** on Coverage or Policy (if any): `MSPCODE`, `MISSCLASS`, other.
3. If no field exists → **QLAdmin enhancement** or **memo/audit-only** documentation — client decision.
4. **Policy premium** (`MMODEPREM`) is already correct at policy level for most policies — SL row suppression does not remove total premium.

---

**Capability discovery status:** ✅ COMPLETE
