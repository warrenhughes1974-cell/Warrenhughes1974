# Open Questions for Business / Actuarial (Phase R2)

Items that physical DBF inspection **could not** resolve and that require a business, actuarial, or QLAdmin SME
decision before loaders are built. Grouped by severity. **V5 only.**

---

## A. BLOCKING — source→target mapping decisions (data is now complete)

> **Update (third drop):** populated `quiktvs` (639k rows), `quiknps` (458k), `QuikDvs` (712k), the band member
> table `quikplbd`, and the two **LifePRO source extracts** (`Rate_Table_Extract_20260427.csv` ~1.13M rows,
> `PAAGERAT_AttainedAge_Rates_Extract_20260428.csv` ~24k rows) are now supplied. NP↔TV key sharing is **confirmed
> by business**. The earlier "missing table" blockers are RESOLVED (Section E). The remaining blockers are now
> **mapping decisions**, not missing data.

1. **`COVERAGE_ID` → authoritative QLAdmin `PLAN` crosswalk.**
   Source `COVERAGE_ID` values contain spaces and are not QLAdmin plan codes (e.g. `10827 CSI3`, `1578 FTR`,
   `0822 620`); target plans are 6-char (e.g. `100100`). A governed crosswalk to **authoritative P3C/P3E PLAN
   codes** is the foundational transform. *Need:* the COVERAGE_ID→PLAN mapping (Policy Form Crosswalk?).

2. **`TYPE_CODE` → QLAdmin rate-family crosswalk.**
   The source has **13 type codes** (`CV, DB, NP, DV, RV, NN, PN, TP, TX, UF, PR, NF, SL`) but QLAdmin has only 6
   families (GP/CV/DB/DV/NP/TV). Likely: `CV→QuikCvs`, `DB→QuikDbs`, `NP→QuikNps`, `DV→QuikDvs`, `RV→QuikTvs`
   (reserve value→terminal reserve). **UNKNOWN:** which type maps to **GP (gross premium)** (source `PR`?), and
   whether `NN/PN/TP/TX/UF/NF/SL` are in-scope or excluded. *Need:* business confirmation of the type-code map +
   out-of-scope list.

3. **`SEX = J` (joint) handling.** Source gender values are `F/M/J`. QLAdmin `GENDER` observed as `0/F/M`. *Need:*
   the mapping for joint (`J`) — to a QLAdmin gender code or a joint mortality basis.

4. **Duration base offset.** Source `DURATION` is **1-based (1–117)**; QLAdmin stores durations **0-based** in
   `CNTL`/`xxN` (duration = CNTL*10 + N). *Need:* confirm `source DURATION d → QLAdmin duration d-1` (i.e. dur 1 →
   CNTL 00 / col 0).

5. **BAND and UWCLASS code mapping.** Source `BAND ∈ {1,2,3}` vs QLAdmin `BAND` C2 (`00/01/…`); source
   `UWCLASS ∈ {0,B,N,P,S}` vs QLAdmin C2 (`00/NT/TB/…`). *Need:* the band and UW-class code crosswalks (the new
   `quikplbd` + a UW member table define the legal targets).

---

## B. HIGH — affects key construction and correctness

5. **`STOREMEANS` and `CALCMIDS` (logical) operational rules.**
   Confirmed as logical fields on `QuikPlTv`, but **empty in the supplied data**. Exact meaning (store mean
   reserves? calculate mid-terminal/interpolated reserves?) and when each should be `T` is **UNKNOWN**.
   *Need:* actuarial definition + the source rule that sets them.

6. **Assumption code vocabularies are unpopulated in the template.**
   `MORT`, `RSVINT`, `RSVMETH`, `INTMETHTV`, `ETIMORT`, `NFOINT`, `INTMETHCV` are present but blank/`0` in the
   supplied rows (only `INTMETHxx='0'` on default rows). The enum *meanings* come from the manual (reserve method
   1–4; interest method 0/1) but the **actual codes in use for these products** are not yet evidenced.
   *Need:* the populated assumption set per plan/segment from the actuary.

7. **Orphan factors & empty keys exist in QLAdmin's own template data.**
   GP reconciliation found **4 factor segments with no key** and **4 keys with no factors**.
   *Decision:* are these expected (work-in-progress reference data) or defects to exclude? The conversion should
   **never emit orphan factors**; please confirm empty keys are acceptable to carry or should be pruned.

8. **Blank `PLAN` rows in key/member tables.**
   A `PLAN = ''` row exists (e.g. in `QuikPlGd`, `QuikPlTv`, `QuikPlCv`).
   *Decision:* confirm these are non-authoritative template artifacts to be **excluded** (consistent with the
   "no spaces/synthetic PLAN" rule). Conversion will reject them by default.

---

## C. MEDIUM — affects mapping / scaling

9. **Factor unit basis & C7 overflow.**
   Factor columns are `CHAR(7)` → max `9999.99`. Cash-value/death-benefit samples show values like `1000.00`.
   *Need:* confirm whether factors are **per unit / per $1,000 / per $1** so the loader scales correctly and never
   overflows CHAR(7). What is the rule when a true value would exceed `9999.99`?

10. **`AGE` semantics per grid type.**
    `QuikCvs` uses real issue ages (41,46); `QuikDbs` uses `AGE=00` (duration-only). Confirm the mapping:
    Var-code `0` Level / `1` by-Policy-Year / `2` by-IssueAge+Year / `3` by-Attained-Age → which use `AGE=00`?

11. **`ISSCNTRY` (C4) vs `ISSUEST` (C2) usage.**
    Both default to `0000`/`00` in the sample. Confirm the code sets (country list, state list) and whether
    state-varying rates are in scope for this conversion.

12. **EFFDATE generations.**
    All sample rows are `19000101` (single default generation). Confirm whether **historical rate generations**
    must be converted, or only the current generation, and how to derive `EFFDATE` from LifePRO source.

13. **Dividend scope.**
    `QuikDvs` is empty and only relevant for `PAR=1` plans. Confirm which in-scope plans are participating and
    require dividend loading.

---

## D. LOW — confirm and proceed

14. **`QuikPlNb` key** — is it keyed by `PLAN+ISSCNTRY+ISSUEST+EFFDATE`, and is `TERMDATE` used to expire
    availability? (`TERMDATE` empty in sample.)
15. **`QuikPlGd` gender codes** — confirm canonical set (`0`=N/A, `M`, `F`; any `U`/`J` for unisex/joint?).
16. **Whether CV/DB/DV also carry assumption sidecars** elsewhere (only CV `QuikPlCv` and TV `QuikPlTv` carry
    assumptions in the supplied set; GP/DB/DV keys are pure segmentation).

---

## E. Decisions explicitly CLOSED by this phase

- **Target version = V5 only** (business decision). V4 basis+subplan sharing is out of scope.
- **`CNTL` = duration page** — CONFIRMED from data (no longer an open question).
- **Where reserve/CV assumptions live** — CONFIRMED on `QuikPlTv` / `QuikPlCv` (no longer open).
- **Uniqueness keys for populated tables** — CONFIRMED from physical layout (see `v5_rate_uniqueness_key_matrix.csv`).
- **`QuikTvs` layout** — CONFIRMED (supplied; 19-field grid identical to the factor family; empty data).
- **`QuikQxs` mortality** — CONFIRMED: shared global library keyed by `MORT` (no PLAN), qx NUMERIC `Q000..Q121`,
  codes match manual appendix. Mortality is loaded once globally, not per plan.
- **State/country PVO members** — CONFIRMED: `QuikPlSt` supplies members + state loan-rate override (`MLOANINT`).
- **Band PVO members** — CONFIRMED: `quikplbd` supplied (`PLAN, BDCODE C2, BDDESCR C20, BDLOWVAL N10.3`; BDLOWVAL =
  band lower bound). Only a **UW-class member table** is still outstanding.
- **TV / NP / DV factor data** — SUPPLIED and populated (639k / 458k / 712k rows). Reserve workstream is now
  data-complete.
- **NP shares the `QuikPlTv` reserve key** — CONFIRMED by business (no separate NP key table).
- **Source extracts identified** — `Rate_Table_Extract` (issue-age × duration, ~1.13M rows) and `PAAGERAT`
  (attained-age, ~24k rows) are the two LifePRO rate sources.

> **Recommendation:** all rate DATA is now present. The remaining work is **mapping/governance**: the
> `COVERAGE_ID→PLAN` and `TYPE_CODE→family` crosswalks (Section A) plus a UW-class member table. These are the
> gating items for R3.
