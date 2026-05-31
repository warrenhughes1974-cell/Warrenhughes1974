# Rate Lookup Flow — Likely Runtime Resolution

**Purpose:** describe, step by step, how QLAdmin is believed to resolve an actuarial factor for a single policy at
runtime, so the conversion can guarantee that **every active policy resolves to a populated factor**.

**Labels:** **CONFIRMED** / **LIKELY** / **UNKNOWN**. The end-to-end *chain* is **LIKELY**; individual anchors are
**CONFIRMED** where the manual supports them (valuation sorts by plan→duration→issue age; missing factors raise a
valuation error).

---

## 1. End-to-end resolution chain (LIKELY)

```
            ┌─────────────────────────────────────────────────────────────┐
            │ POLICY (QuikMstr) + COVERAGE/PHASE (QuikRidr)                 │
            │   carries: PLAN, gender, UW class, band, issue state/country, │
            │            issue age, issue/effective date, duration          │
            └───────────────────────────┬─────────────────────────────────┘
                                        │ (1) PLAN from coverage
                                        ▼
            ┌─────────────────────────────────────────────────────────────┐
            │ QuikPlan (Plan Information File)                              │
            │   PVO = Y?  ── N ─► legacy single rate set (no segmentation)  │
            │   *VARY* matrix: which dimensions segment each rate family    │
            │   assumption pointers: mortality / reserve method / interest  │
            └───────────────────────────┬─────────────────────────────────┘
                                        │ (2) choose rate FAMILY for the calc
                                        │     GP=premium  DB=death ben  CV=cash val
                                        │     TV=reserve  NP=net prem   DV=dividend
                                        ▼
            ┌─────────────────────────────────────────────────────────────┐
            │ Build SEGMENTATION KEY (only dims whose VARY flag = Y)        │
            │   Gender?   → policy gender   else default 0                  │
            │   UW class? → policy UW class else default 00                 │
            │   Band?     → policy band     else default 00                 │
            │   State?    → policy iss st   else default 00                 │
            └───────────────────────────┬─────────────────────────────────┘
                                        │ (3) match key row
                                        ▼
            ┌─────────────────────────────────────────────────────────────┐
            │ QUIKPLxx  (Rate File Option KEY for this family)             │
            │   match: PLAN + segmentation key + EFFDATE generation         │
            │   Values = Y?  ── N ─► VALUATION ERROR (no factors) [CONFIRMED]│
            └───────────────────────────┬─────────────────────────────────┘
                                        │ (4) select EFFDATE generation
                                        ▼
            ┌─────────────────────────────────────────────────────────────┐
            │ QUIKxxS  (factor grid for the matched key)                   │
            │   (5) AGE row   ← issue age (or attained age if VAR code = 3) │
            │   (6) CNTL page ← duration decade  [UNKNOWN paging rule]      │
            │   (7) column    ← xx0..xx9 offset within the CNTL decade      │
            └───────────────────────────┬─────────────────────────────────┘
                                        │ (8) factor
                                        ▼
            ┌─────────────────────────────────────────────────────────────┐
            │ FACTOR  → premium / cash value / DB / reserve / NP / dividend │
            │   reserve & deficiency calcs also pull qx from QuikQxs via    │
            │   the plan's mortality code + reserve method/interest method  │
            └─────────────────────────────────────────────────────────────┘
```

---

## 2. Step detail

| # | Step | Confidence | Basis |
|---|---|---|---|
| 1 | Coverage → PLAN | CONFIRMED | `QuikRidr` is the Coverage Master File linking policy to plan |
| 2 | Pick rate family for the calculation in progress | CONFIRMED | Five Rate File Options GP/DB/CV/TV/DV (+NP under reserves) |
| 3 | Build segmentation key from enabled dimensions only | CONFIRMED mechanism | VARY matrix + "rates will vary by gender, band, UW class" example |
| 4 | Match the plan rate-file-option key | LIKELY | "Plan Rate File Options window" lists defined key combinations |
| 5 | Select EFFDATE generation | LIKELY | "Countries and states can have rate files with different effective dates" |
| 6 | AGE row | CONFIRMED anchor | Reserve Valuation sorted by plan, duration, then **issue age** |
| 7 | Duration page (CNTL) | UNKNOWN | `CNTL`/`xx0–xx9` not in manual; user hypothesis only |
| 8 | Missing factor → valuation error | CONFIRMED | Error Valuation lists policies "for which reserve factors were not available" |

---

## 3. Reserve / deficiency sub-flow (CONFIRMED behavior)

For valuation specifically, the factor lookup is only half the story — reserves combine **factors + assumptions**:

```
QuikPlan (Reserves button assumptions)
   mortality code ─► QuikQxs (qx)
   reserve method  (1 NetLevel | 2 FullPrelimTerm | 3 CRVM | 4 ModifiedRVM)
   reserve interest rate
   reserve interest method (0 Curtate | 1 Continuous)
           │
           ▼
   Terminal reserve (QuikTvs factor) + Net premium (QuikNps factor)
           │
           ▼
   Deficiency check: if statutory NET PREMIUM > GROSS PREMIUM (QuikGps) and Calc Dfcy ON
           │
           ▼
   Deficiency reserve (shown by plan code in Deficiency Valuation)
```

This sub-flow is why **GP, NP, TV, mortality, and the reserve assumptions must all be present and internally
consistent** before statutory valuation will run clean.

---

## 4. Conversion correctness target (derived)

The flow makes the **acceptance test for any future loader** obvious and measurable:

> **For every active policy in QuikMstr/QuikRidr, the (PLAN + segmentation + EFFDATE + AGE + duration) it resolves
> to must exist in the corresponding `QUIKxxS` table, and its `QUIKPLxx` key must show `Values = Y`.**

Equivalently: **a successful statutory valuation with an empty Error Valuation report is the gold-standard
end-to-end validation** of a rate conversion (CONFIRMED that QLAdmin produces this error report only when factors
are missing).
