# Open Questions & Unknowns

Items requiring **real DBF layouts**, **deeper manual sections**, or **business/SME validation** before any rate
loader is designed. Grouped by severity. Each item notes how to resolve it.

---

## A. BLOCKING — must resolve before R2/R3 design

1. **Physical layout of `QUIKxxS` factor tables.**
   The actual column list, types, widths, and precision of `QuikGps/QuikDbs/QuikCvs/QuikTvs/QuikNps/QuikDvs` are
   **not in the repo**. The user described them in conversation only; no DBF headers were inspected.
   *Resolve:* obtain the real DBFs (or QLAdmin export/DDL) and read headers.

2. **`CNTL` semantics.** Not found anywhere in `QLAdmin_Help.pdf`. The "duration decade page" interpretation
   (`CNTL=0 → 0–9`, `CNTL=1 → 10–19`) is a **user hypothesis only**.
   *Resolve:* inspect a populated rate DBF and confirm against a known plan's rate schedule; or ask QLAdmin SME.

3. **`xx0–xx9` column meaning.** Whether these are durations, policy years, attained-age offsets, or something
   else, and how they interact with `VARGP`/`VARDB` codes 0–4.
   *Resolve:* same as #2.

4. **`STOREMEANS` and `CALCMIDS`.** Not in the manual extract. Best guess: mean-reserve storage flag and
   mid-terminal/interpolated reserve calc flag — **unconfirmed**.
   *Resolve:* QLAdmin reserve-setup SME or full Reserves-button documentation.

5. **Where reserve assumptions physically live.** The manual confirms reserve interest rate / method / interest
   method / mortality / ETI mortality live **behind the Plan Values Options Reserves & Cash Values buttons** — but
   whether that is a column on `QUIKPLxx`, on `QuikPlan`, or in a separate option record is **UNKNOWN**. Several of
   these (`RSVINT`, `RSVMETH`, `MORT`, `ETIMORT`) are **absent from the live `QUIKPLAN_SCHEMA`**.
   *Resolve:* inspect `QUIKPLxx` DBF headers and the V5 plan-values option record.

---

## B. HIGH — affects uniqueness key and row counts

6. **Exact uniqueness key for `QUIKxxS` and `QUIKPLxx`.** Proposed (LIKELY):
   `PLAN + GENDER + UWCLASS + BAND + ISSCNTRY + ISSUEST + EFFDATE [+ AGE + CNTL for values]`. Needs confirmation,
   especially whether AGE or AGE+CNTL is the value key and whether EFFDATE sits on key, value, or both.

7. **`ISSCNTRY` vs `ISSUEST` storage.** Manual treats "Country/State" as one Plan Values Option. Are they two
   columns or one combined code in the rate tables?

8. **Target QLAdmin version (V4 vs V5).** Determines whether reserve/NP factors are **per-plan (V5)** or **shared by
   basis+subplan (V4)** — a major driver of row counts and replication logic. **Business decision required.**

9. **`QUIKPLNP` existence.** Manual folds Net Premiums under the Reserves (TV) option. Is there a separate net-
   premium key table, or do NP factors share the TV key? The user listed `QUIKPLTV` but not `QUIKPLNP`.

10. **Default-member handling.** When a `*VARY*` flag is `N`, is the segmentation column written as `0`/`00`
    (default member) or left blank? Affects key matching and validation.

---

## C. MEDIUM — affects loader behavior / mapping

11. **Mortality code mapping.** Need the LifePRO → QLAdmin mortality-code crosswalk. QLAdmin's code list is
    confirmed (Appendix 6.9: 1980 CSO, 2001 CSO, 2017 CSO, CET, joint, ALB, NS/SM variants), but the **source
    basis values and their mapping are not yet defined.**

12. **Reserve method / interest method mapping.** QLAdmin enums confirmed (method 1–4; interest 0 Curtate /
    1 Continuous). Need the LifePRO source values and their mapping.

13. **Attained-age vs issue-age grids.** `VARGP`/`VARDB` code `3` = "Vary by Attained Age." How does an attained-
    age grid differ structurally from issue-age + duration in the `QUIKxxS` layout?

14. **Dividend gating.** `QuikDvs`/dividend rates are enabled only when `PAR = 1`. Confirm conversion skips DV
    entirely for non-par plans and that PAR is reliably populated.

15. **Supplemental / WVP percent-of-premium rates.** Manual note: for `WVP` waiver riders, gross premium rate
    tables store the **percent of total premium** (e.g. `0.10` for 10%). Confirm whether any in-scope products use
    this convention so factors aren't misinterpreted as dollar amounts.

---

## D. LOW — nice to confirm, not blocking

16. **`PLANVALOPT` field** — confirm it is the PVO `Y/N` indicator and that current conversion populates it
    correctly for new plans.
17. **`INITVAL` / Initial Val/Unit** interaction with DB code `0` (Level) — whether level-DB plans even need a
    `QuikDbs` grid or rely on `INITVAL` alone.
18. **EFFDATE granularity** — date vs year; how QLAdmin picks the generation when a policy effective date falls
    between two generations.
19. **`QuikQxs` physical layout** — exact qx storage (per-age rows, select/ultimate split?).

---

## E. How each unknown gets resolved

| Source of truth | Resolves |
|---|---|
| **Real `QUIKxxS`/`QUIKPLxx` DBF headers** | A1, A3, B6, B7, B9, B10, C13, D19 |
| **Full QLAdmin Reserves/Cash-Values button docs** | A4, A5, C13 |
| **QLAdmin SME / actuary** | A2, A3, B8, C11, C12, C15 |
| **Business decision** | B8 (target version), C14 scope |
| **Existing quikplan conversion review** | D16, D17 |

> **Recommendation:** Phase R2 should be a short, evidence-gathering phase that resolves Section A (and ideally B)
> by reading the actual DBF headers — *before* any loader or schema is designed.
