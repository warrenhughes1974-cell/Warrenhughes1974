# Issue 21F — Business Decisions (Locked 2026-07-11)

**Issue:** Truncated Premium History — conversion premium adjustment  
**Authority:** Eric (business) confirmed all recommendations · Conversion (Warren)  
**Status:** **DECIDED** — ready for Risk / Development Authorization  
**Supersedes:** 2026-07-09 “accept ~2017 floor only / no engine change” ruling for 21F

---

## Decision summary

| # | Topic | Decision | Status |
|---|---|---|---|
| 1 | Adjustment approach | Single conversion adjustment row when LifePRO lifetime premiums paid > converted `quikprmh` total | **AGREED** |
| 2 | LifePRO total components | Base + PUA + Supplemental + Substandard | **AGREED** |
| 3 | Adjustment date | **12/31/2017** for all adjustment rows | **AGREED** |
| 4 | Row classification | Mark as **Conversion Adjustment** (not a customer payment) | **AGREED** |
| 5 | Negative adjustments | Exception report only — **do not load** | **AGREED** |
| 6 | ISWL | **Exclude** from this first implementation (separate analysis later) | **AGREED** |
| 7 | Validation report | Before / adjustment / after / remaining variance + exception status | **AGREED** |

---

## 1. Conversion Premium Adjustment Approach — AGREED

Create **one** conversion adjustment entry per eligible non-ISWL policy when:

```
LifePRO_Total_Premiums_Paid  >  Sum(quikprmh.PREMIUM for policy)
```

Adjustment amount:

```
Adjustment = LifePRO_Total − Current_QLAdmin_Premium_History_Total
```

**Example (workbook policy 010310404C):**

| Item | Amount |
|---|---:|
| LifePRO Total Premiums Paid | $17,040.05 |
| Current QLAdmin premium-history total | $1,846.20 |
| Conversion Adjustment | $15,193.85 |

Existing converted premium-history rows are **preserved**; the adjustment brings the QLAdmin cumulative total into alignment with LifePRO.

---

## 2. LifePRO total components — AGREED (all four)

| Component | PPBENTYP field | Notes |
|---|---|---|
| Base premiums paid | `PREMIUMS_PAID` | Traditional BA (and BF where applicable) |
| Paid-Up Additions (PUA) | `PU_PREMIUMS_PAID` | |
| Supplemental premiums | `SU_PREMIUMS_PAID` | |
| Substandard-life premiums | `SL_PREMIUMS_PAID` | |

```
LifePRO_Total = PREMIUMS_PAID + PU_PREMIUMS_PAID + SU_PREMIUMS_PAID + SL_PREMIUMS_PAID
```

Validation report must show **each component** for UAT review.

**Workbook note:** Client Non-ISWL sheet Totals for samples (e.g. 010310404C) are BA+PU; SU/SL are included in the engine formula even when zero on a given policy.

---

## 3. Adjustment date — AGREED

- **`DATEPAID` = 2017-12-31** for every conversion adjustment row.
- Identifies the row as a conversion opening-balance adjustment (premiums paid before converted history begins), not a customer payment.

---

## 4. Conversion Adjustment classification — AGREED

The row is **not** a real payment transaction. Implementation must identify it as a **Conversion Adjustment** so it is distinguishable in policy review, reconciliation, and audit.

**Development mapping (to confirm in Risk / Dev):** use a dedicated identifier on loadable fields that remain within `quikprmh` schema — candidates: `MSOURCE`, `MBATCH`, and/or `USER_ID` (exact codes locked at Development). Existing payment rows unchanged.

---

## 5. Negative adjustments — AGREED (exceptions only)

If `Adjustment < 0` (QLAdmin history already exceeds LifePRO total):

- **Do not** emit a negative premium-history row.
- Report on an **exception** list for business review.
- No automatic load of negative adjustments without separate approval.

---

## 6. ISWL exclusion — AGREED (phase 1)

- **In scope (phase 1):** non-ISWL / traditional policies using PPBENTYP premium-paid fields.
- **Out of scope (phase 1):** ISWL / UL (deposit / basis via `FV_GUAR_DEPOSITS` / `FV_BASIS2`) — separate analysis after non-ISWL ships.

---

## 7. Validation report — AGREED

UAT/audit report (under `QLA_Migration/Reports/`, not Output) must include per policy:

| Column | Meaning |
|---|---|
| LifePRO total premiums paid | Sum of four components |
| Component amounts | Base / PUA / SU / SL |
| Current QLAdmin `quikprmh` total | Pre-adjustment |
| Adjustment amount | Loaded amount (or blank if exception) |
| Final QLAdmin premium-history total | After adjustment |
| Remaining variance | Should be ~0 for loaded rows |
| Exception status | e.g. LOADED / NEGATIVE_EXCEPTION / ISWL_EXCLUDED / ZERO_OR_NO_GAP |

---

## Relationship to prior 21F / 21G decisions

| Prior ruling | New ruling |
|---|---|
| Accept ~2017 source floor; no engine change | Still accept that detailed history before the extract floor is **not** replayed transaction-by-transaction |
| Full history requires re-extract | Unchanged — adjustment is the approved **reconciliation** path instead of re-extract |
| 21G stages BA+PU (+ FV for ISWL) informationally | 21F **loads** a reconciling `quikprmh` row for non-ISWL; 21G tax-basis / target-field question remains separate |

---

*Locked 2026-07-11 from Eric confirmation of Warren’s planning Q&A.*
