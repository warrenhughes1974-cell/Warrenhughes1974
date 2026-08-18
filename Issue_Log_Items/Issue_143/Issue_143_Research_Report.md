# Issue #143 — Units Incorrect (RPU) — Research Report

**Date:** 2026-08-18  
**Type:** Investigation / root-cause research (no conversion-code change)  
**Source cut measured:** `QLA_Migration/Source/*_20260630.csv` (304 RPU policies, `PAID_UP_TYPE=RU`)  
**Status after this report:** Discovery complete — **SME rule locked 2026-08-18** (Warren): on BF RPU where units ≠ Column DD / VPU, QLAdmin `MUNIT` must be recalculated so Amount Ins equals LifePRO death benefit. Do not implement until Intake → Risk and Development approval.  

Evidence files:

- `Issue_Log_Items/Issue_143/evidence/issue143_rpu_units_research.json`
- `Issue_Log_Items/Issue_143/evidence/issue143_bf_rpu_mismatch.json`

---

## 1. Executive Summary

Eric’s statement is correct: **Reduced Paid-Up status does not mean LifePRO always reduced units.**

On the 2026-06-30 extract there are **304** RPU policies (`PPOLC.PAID_UP_TYPE = RU`). They fall into three LifePRO behaviors:

| Pattern | Count | What LifePRO did | Column DD (`BF_CURRENT_DB`) |
|---|---:|---|---|
| Traditional BA | 199 | Death benefit lives in `NUMBER_OF_UNITS × VALUE_PER_UNIT` | Always **0.00** — DD is not the death-benefit field |
| BF / ISWL — units already aligned | 82 | Units **were** reduced; `units × $1,000 = BF_CURRENT_DB = BF_SPECIFIED_AMT` | Matches units |
| BF / ISWL — units **not** reduced | **23** | Units stay at original whole-face (5, 10, 25, 30, 35, 50); specified / current DB **was** reduced | **Does not** match units |

**PPBENTYP Column DD is `BF_CURRENT_DB`** — current death benefit on **BF** (interest-sensitive / UL-family) benefit-type rows. That is proven by Excel column 108 on the live extract and by the same client column map used in Issue #21.

The comparison Eric asked for is:

```text
Expected units  =  BF_CURRENT_DB  ÷  VALUE_PER_UNIT
```

on **BF** RPU rows only.

- If that equals LifePRO `NUMBER_OF_UNITS`, the units are already the paid-up amount. QLAdmin should receive those units.
- If it does not, LifePRO left original units in place and stored the paid-up death benefit in Column DD (and Column DC `BF_SPECIFIED_AMT`). QLAdmin face is `MUNIT × MVPU`, so copying LifePRO units on those 23 policies would convert the **original** face, not the **RPU** death benefit.

Do **not** reduce units on all RPU policies. Traditional BA and the 82 aligned BF policies would be damaged by a blanket rule.

### SME decision (locked 2026-08-18)

Warren confirmed **Yes**: on `9010757606`, QLAdmin units must become **19.10196** so Amount Ins equals LifePRO Column DD / specified **$19,101.96**, not the unreduced LifePRO units of 25 ($25,000).

That locks the BF unaligned rule for the rest of the 23: `MUNIT = BF_CURRENT_DB / VALUE_PER_UNIT`. Original LifePRO units stay in source; they are not the converted death-benefit quantity.

---

## 2. Restatement of the Business Problem

Client (Eric, 2026-08-12):

> Some policies in Reduced Paid Up Status did not have their units reduced in LifePRO. The death benefit amount comparison should occur with Column DD of the PPBENTYP_BenefitType_Extract to determine accuracy of the units versus death benefit.

The conversion risk is not “RPU units are always wrong.” It is:

1. LifePRO has two BF RPU storage styles.
2. QLAdmin has only one face construct on coverage: `MUNIT × MVPU`.
3. If we copy LifePRO units on the 23 unreduced BF policies, QLAdmin will display and value the pre-RPU face.
4. If we recalculate units on every RPU policy, we will invent a reduction that LifePRO never made on BA and on the 82 already-aligned BF policies.

Related closed work that is **not** this issue:

- **Issue #55** — tiny `0.00001` base units / leading-dot DBF packing on SAL-style RPU. Mapping `NUMBER_OF_UNITS → MUNIT` was already correct; that issue floored sub-mill units and fixed emit format.
- **Issue #108** — QLAdmin *transaction* RPU updates `MUNIT` to a calculated reduced amount. That is what QLAdmin does when it processes RPU. It does not answer what LifePRO already stored.

---

## 3. LifePRO Units — Business Definition

### PROVEN

| Term | LifePRO field | Meaning |
|---|---|---|
| Units | `PPBEN.NUMBER_OF_UNITS` (Excel **AC**) | Quantity of coverage on the benefit |
| Value per unit | `PPBEN.VALUE_PER_UNIT` (Excel **AB**) | Dollar value of one unit; **$1,000.00** on every RPU row measured |
| Face / amount of insurance (traditional) | computed | `NUMBER_OF_UNITS × VALUE_PER_UNIT` |
| QLAdmin units | `quikridr.MUNIT` | “Number of units of coverage” (QLAdmin Help, QuikRidr) |
| QLAdmin value per unit | `quikridr.MVPU` | “Value per unit” |

Units are **not** a rating class, not a premium rate, and not a death-benefit option code. They are a **benefit quantity**. Premium per unit (`ANN_PREM_PER_UNIT`) is a separate rate field (Issue #26).

On traditional **BA** benefits, death benefit **is** units × VPU. There is no separate current-DB column that overrides face.

On **BF** benefits (ISWL / UL-family), LifePRO also stores:

| Field | Excel | Role |
|---|---|---|
| `BF_SPECIFIED_AMT` | DC | Specified / target amount |
| `BF_CURRENT_DB` | **DD** | Current death benefit |
| `BF_DB_OPTION` | DE | Death-benefit option; **A** on all 105 BF RPU rows |

Issue #21 imaged this split on an active UL policy (`010713704C`): Specified **$25,000**, Fund **$45,567.58**, Death Benefit **$47,845.95**. That policy is not the RPU population, but it proves current death benefit is a **separate stored amount**, not automatically `units × $1,000`.

### STRONG INFERENCE

`TYPE_CODE = BF` is the interest-sensitive / flexible benefit segment (ISWL / UL family). `TYPE_CODE = BA` is traditional base amount. This is the working conversion convention (Issues #21A, #57, Product Book addendum). A published LifePRO data-dictionary definition of BA/BF was **not** found in the Product Book extract or public EXL material.

### HYPOTHESIS

`BF_DB_OPTION = A` is level / option-1 death benefit (specified amount, subject to corridor). All 105 BF RPU rows are A, so option does **not** explain the 23 vs 82 split.

---

## 4. Reduced Paid-Up Processing in LifePRO

### Actuarial / QLAdmin (PROVEN from Robert’s spec)

`docs/research/Conversion - Statuses, NFO/QLAdmin_ETI_RPU.docx`:

- RPU uses net cash value (CV − loans + dividend accumulations / PUA) as a **net single premium**.
- That premium buys a **smaller permanent face** through the original expiry.
- QLAdmin, when *it* processes RPU, **updates `MUNIT` to the reduced amount** (including PUA if applicable) and saves the pre-RPU units in `MSAVEUNIT`.
- Worked example `010367133C`: active units 4.976 → RPU units **8.668** (calculated; PUA folded in). That is QLAdmin’s transaction, not a LifePRO extract proof.

Standard nonforfeiture (secondary sources; not LifePRO-specific): RPU converts cash value into a reduced paid-up death benefit; premiums stop; coverage remains permanent.

### What LifePRO actually stores after RPU (PROVEN from extract)

When a policy is already RPU in LifePRO (`PAID_UP_TYPE=RU`):

| Field | Observed on RPU |
|---|---|
| `PPOLC.PAID_UP_TYPE` | `RU` (304) |
| `PPBEN.STATUS_REASON` | Mostly `CR` (contract/RPU) on in-force benefits |
| `PPBEN.NUMBER_OF_UNITS` | Sometimes reduced (fractional), sometimes original integers |
| `PPBENTYP.ORIGINAL_UNITS` | **Unused** — 0.00 on 303 of 304 RPU benefit-type rows |
| `PPBENTYP.ETI_RPU_ENDOWMENT` | **Unused** — all 0 |
| `PPBENTYP.ETI_RPU_PATTERN` | **Unused** — all blank |
| `PPBENTYP.BF_CURRENT_DB` / `BF_SPECIFIED_AMT` | Populated **only** on BF rows (105/105); always equal to each other on this RPU cut |
| Riders (SU) | Often terminated; SAL-style book keeps SU as the in-force face |

**LifePRO does not always reduce units when a policy becomes RPU.** That is no longer a hypothesis. It is measured.

---

## 5. PPBENTYP Column DD — Exact Definition

Live header on `PPBENTYP_BenefitType_Extract_20260630.csv` (133 columns):

| Excel | # | Field |
|---|---:|---|
| V | 22 | `ORIGINAL_UNITS` |
| AE | 31 | `ETI_RPU_ENDOWMENT` |
| AF | 32 | `ETI_RPU_PATTERN` |
| **DB** | **106** | **`BF_NON_FORFEITURE`** (Issue #21A client “Col DB”) |
| **DC** | **107** | **`BF_SPECIFIED_AMT`** |
| **DD** | **108** | **`BF_CURRENT_DB`** |
| DE | 109 | `BF_DB_OPTION` |

### PROVEN

1. Column DD **is** `BF_CURRENT_DB`.
2. Name and Issue #21 client map both say **current death benefit** on the BF segment.
3. Data type in the extract: numeric money, two decimals (examples `19101.96`, `14083.77`, `.00`).
4. Populated when `TYPE_CODE=BF`; **0.00** on BA / SU / PU / SL / OR rows in the RPU set.
5. On this RPU BF population, `BF_CURRENT_DB = BF_SPECIFIED_AMT` on **105 of 105** rows (fund extinguished / paid-up amount written to both).

### Not established from a LifePRO manual page

No Product Book paragraph was extracted that says “BF_CURRENT_DB is the death benefit used for RPU unit validation.” The **field identity** is proven from the extract + prior client column map. The **use Eric wants** is proven by his instruction plus the 23-policy mismatch pattern.

---

## 6. Relationship Between Units and Death Benefit

### Traditional BA

```text
Death benefit  =  NUMBER_OF_UNITS  ×  VALUE_PER_UNIT
```

Column DD is 0. Eric’s DD test **does not apply**.

### BF / ISWL — two observed identities

**Aligned (82):**

```text
NUMBER_OF_UNITS  ×  VALUE_PER_UNIT
        =  BF_SPECIFIED_AMT
        =  BF_CURRENT_DB          (Column DD)
```

**Not aligned (23):**

```text
NUMBER_OF_UNITS  ×  VALUE_PER_UNIT     =  original issue face (whole thousands)
BF_SPECIFIED_AMT  =  BF_CURRENT_DB     =  reduced RPU death benefit
```

So the intended check is **not** “always recompute units” and **not** “always keep units.” It is:

```text
On BF RPU:
    expected_units = BF_CURRENT_DB / VALUE_PER_UNIT
    if NUMBER_OF_UNITS ≈ expected_units  →  LifePRO units are the death-benefit units
    if NUMBER_OF_UNITS ≠ expected_units  →  LifePRO units are the original face;
                                           Column DD is the death benefit
```

On this cut, `VALUE_PER_UNIT` is always 1000, so `expected_units = BF_CURRENT_DB / 1000`.

---

## 7. Why Some RPU Policies Retain Units

### PROVEN

The 23 BF mismatches **all** have integer units `{5, 10, 25, 30, 35, 50}` and a **lower** `BF_CURRENT_DB` that equals `BF_SPECIFIED_AMT`. Example:

| Policy | LifePRO units | Units × $1,000 | Column DD / specified | Implied units from DD |
|---|---:|---:|---:|---:|
| `9010757606` | 25.00000 | $25,000.00 | $19,101.96 | 19.10196 |
| `9010766847` | 25.00000 | $25,000.00 | $5,163.41 | 5.16341 |
| `9010826422` | 50.00000 | $50,000.00 | $9,655.90 | 9.65590 |
| `9011001627` | 30.00000 | $30,000.00 | $3,044.64 | 3.04464 |

This is Eric’s exception, measured.

### STRONG INFERENCE

LifePRO’s RPU process on these BF policies **did** write the paid-up amount into specified / current DB, and **did not** overwrite `NUMBER_OF_UNITS`. Units remain the issue-quantity (face / 1000).

### HYPOTHESIS (why this path was taken)

Not explained by NFO election (1 and 4 appear in both cohorts), DB option (all A), product type (05/06/16 in both), or in-force vs death (`A/CR` and `T/DC` in both). Possible causes still unproven:

- Different LifePRO RPU / conversion programs (some update units, some only specified amount)
- Plan-level “units control” / face stored as specified amount
- Historical conversion onto LifePRO that reduced specified/DB but left units
- Manual specified-amount change after RPU without a unit change

`ORIGINAL_UNITS` cannot be used as the “before” picture — it is blank.

---

## 8. Why Other RPU Policies May Have Reduced Units

### PROVEN

**82 BF RPU** rows have **zero** integer unit values. Units look like calculated paid-up amounts (`14.08377`, `11.18136`, `5.11753`, …) and already equal Column DD / $1,000.

**199 BA RPU** rows typically also show fractional units (`1.69072`, `8.23694`, …). On BA that *is* the death benefit.

**94 BA RPU** use the SAL-style structure already documented in Issues #55 and #108: phase 1 units `0.00001`, phase 2 SU holds the paid-up face (`0.53` → $530, etc.). Base units were not “kept at original 100”; they were parked at a near-zero stub.

### STRONG INFERENCE

On the 82 BF policies, LifePRO’s RPU process updated **units and specified/current DB together**. That is Scenario B. Copying `NUMBER_OF_UNITS` already reproduces Column DD.

---

## 9. Generalized Business Decision Rule

Draft rule for **validation and, if approved, conversion**. Not implemented.

```text
Identify RPU: PPOLC.PAID_UP_TYPE = RU  (or converted MSTATUS = 45)

Join PPBEN seq 1 + PPBENTYP seq 1 on POLICY_NUMBER.

IF TYPE_CODE = BA (or BF_CURRENT_DB is 0 / blank):
    Treat NUMBER_OF_UNITS as the LifePRO death-benefit units.
    Do not recompute from Column DD.
    If 0 < units < 0.001, economic face is likely on a later SU benefit (Issue #55 pattern).

IF TYPE_CODE = BF AND BF_CURRENT_DB > 0:
    expected_units = BF_CURRENT_DB / VALUE_PER_UNIT
    IF |NUMBER_OF_UNITS − expected_units| ≤ tolerance (e.g. 0.01):
        Keep NUMBER_OF_UNITS. Already the RPU death benefit.
    ELSE:
        LifePRO units were not reduced.
        The economic death benefit is BF_CURRENT_DB.
        QLAdmin MUNIT should be expected_units so that MUNIT × MVPU = Column DD.
        (MSAVEUNIT, if populated, would be the unreduced NUMBER_OF_UNITS.)
```

**Locked 2026-08-18:** QLAdmin should show Column DD (not unreduced LifePRO units) on the 23. BA remains out of the DD test.

---

## 10. Mathematical Formula(s)

Supported on **this book’s BF RPU rows** (`VPU = 1000`):

```text
expected_units     = BF_CURRENT_DB / VALUE_PER_UNIT
units_are_correct  ⇔  |NUMBER_OF_UNITS − expected_units| ≤ ε
QLAdmin face       = MUNIT × MVPU
target identity    = MUNIT × MVPU = BF_CURRENT_DB     (BF RPU only)
```

QLAdmin RPU *transaction* formula (Robert; not re-derived from LifePRO source):

```text
RPU face  =  net cash value  /  net single premium per 1 of insurance
MUNIT     =  RPU face / MVPU     (plus PUA units if folded in)
```

We did **not** recompute NSP from cash value on the 23. Column DD already holds LifePRO’s resulting death benefit. Re-deriving RPU from first principles is unnecessary if DD is accepted as authority.

---

## 11. Worked Examples

### Scenario A — units retained, DD reduced (the defect Eric described)

`9010757606` (RPU, BF, option A, in force):

| Item | Value |
|---|---|
| LifePRO units | 25.00000 |
| VPU | 1,000.00 |
| Units × VPU | **$25,000.00** |
| Column DD `BF_CURRENT_DB` | **$19,101.96** |
| Column DC specified | $19,101.96 |
| Expected units from DD | **19.10196** |

**Locked:** conversion must emit `MUNIT = 19.10196` so Amount Ins = $19,101.96. Copying 25.00000 is the defect.

`9010826422`: units 50 → $50,000 vs DD $9,655.90 → expected units **9.65590**.

### Scenario B — units already reduced

`9010732975` (RPU, BF, in force):

| Item | Value |
|---|---|
| LifePRO units | 14.08377 |
| Units × VPU | $14,083.77 |
| Column DD | $14,083.77 |
| Expected units from DD | 14.08377 |

Copy units. Do not “reduce” again.

### Traditional BA — DD not in play

`9010165095`: units 1.69072 × 1000 = $1,690.72 death benefit. `BF_CURRENT_DB = 0`. A DD-based recalculation would wrongly drive units to 0.

### SAL stub (Issue #55 pattern, still present)

`901353D732`: phase 1 units `0.00001`; phase 2 SU units `0.297` → $297. Economic RPU face is the rider, not a BF Column DD.

---

## 12. Benefit-Type / Product Dependencies

| Dependency | Finding |
|---|---|
| Benefit type BA vs BF | **Controls whether Column DD exists.** Universal rule is false. |
| Base vs rider | SAL RPU parks face on SU phase 2. BF issue is on seq-1 BF. |
| `BF_DB_OPTION` | All A — does not split 23 vs 82 |
| NFO election `BF_NON_FORFEITURE` | 1 and 4 in both cohorts — not the switch |
| Product type 05 / 06 / 16 | Mixed in both — not the switch |
| Plan code on PPBEN | Blank on all 105 BF RPU seq-1 rows |
| PPBENTYP configuration | `ORIGINAL_UNITS`, `ETI_RPU_*` unused; specified/current DB **are** the configured money fields |

This is **PPBENTYP-controlled for BF**, not a universal LifePRO RPU unit rewrite.

---

## 13. Edge Cases

| Case | Handling |
|---|---|
| RPU units unchanged (23 BF) | DD is authority for death benefit |
| RPU units already reduced (82 BF, most BA) | Pass through `NUMBER_OF_UNITS` |
| Multiple benefits | Test seq-1 BF/BA; do not apply DD to SU/PU/SL |
| PUA (PU) | Robert folds PUA into RPU units in QLAdmin; LifePRO may already include or keep a separate PU row. Still an open Issue #108 question. |
| Zero / tiny units | Issue #55 floor `< 0.001 → 0`; face on later SU |
| Fractional units | Normal for calculated RPU; preserve precision |
| Death claims (`T`/`DC`) | 10 of 23 mismatches are terminated death — still show the same units-vs-DD split |
| Reinstatement | QLAdmin `MSAVEUNIT` should be pre-RPU units if we overwrite `MUNIT` |
| Missing PPBENTYP BF row | Cannot run DD test; fall back to PPBEN units |
| Active UL corridor (Issue #21 style) | DD can **exceed** specified / units×VPU. **Not observed** on this RPU cut (FV=0, spec=DD). Do not assume RPU DD is always less than units×VPU on non-RPU UL. |
| Legacy / conversion-era | 23 policies’ paid-to dates cluster 2004–2012 — **hypothesis only** that an older processor left units |

---

## 14. Proposed Validation Method

For each RPU policy:

```text
Policy
 → PPOLC PAID_UP_TYPE = RU
 → PPBEN seq 1: STATUS, NUMBER_OF_UNITS, VALUE_PER_UNIT, BENEFIT_TYPE
 → PPBENTYP seq 1: TYPE_CODE, BF_CURRENT_DB (DD), BF_SPECIFIED_AMT (DC)
 → expected_units = DD / VPU   (only if TYPE_CODE=BF and DD>0)
 → converted MUNIT
 → PASS / FAIL
```

Checks:

1. **BA / DD=0:** `MUNIT` (after #55 floor) equals `NUMBER_OF_UNITS` (or 0 if source `< 0.001`). Face = `MUNIT × MVPU`.
2. **BF aligned:** `|NUMBER_OF_UNITS − DD/VPU| ≤ 0.01` and `MUNIT` equals source units.
3. **BF unaligned:** `|NUMBER_OF_UNITS − DD/VPU| > 0.01`. Today this is a **FAIL if MUNIT still equals unreduced units**. After an approved fix, PASS when `MUNIT = DD/VPU` and `MUNIT × MVPU = DD`.
4. **SAL:** phase 1 tiny units + phase 2 SU face; do not require DD.
5. **Non-RPU control:** units unchanged.

Fleet anchors for the unaligned class: `9010757606`, `9010766847`, `9010826422`, `9011001627`.

---

## 15. Conversion Implications for QLAdmin

Conceptual requirement only — **no code in this pass**.

QLAdmin must reproduce the **LifePRO economic death benefit**, not the raw unit field when those disagree.

| Population | Business requirement |
|---|---|
| BA RPU | Keep LifePRO units (and SAL phase-2 face). Ignore Column DD. |
| BF RPU, units = DD/VPU | Keep LifePRO units. |
| BF RPU, units ≠ DD/VPU | **Locked 2026-08-18.** Do **not** keep 25.00000 when DD is $19,101.96. `MUNIT` must be the DD-implied units so Coverage Amount Ins / valuation face equals LifePRO current death benefit. Preserve original units in `MSAVEUNIT` if RPU save-fields are in scope. |

A blanket “reduce all RPU units” rule is **wrong**.  
A blanket “always trust LifePRO units” rule is **wrong for the 23**.

Current mapping `NUMBER_OF_UNITS → MUNIT` is the reason the 23 would fail Eric’s comparison.

---

## 16. Proven Facts vs Inferences vs Hypotheses

### PROVEN

- Column DD = `BF_CURRENT_DB` (extract column 108; Issue #21 client map).
- Column DC = `BF_SPECIFIED_AMT`; Column DB = `BF_NON_FORFEITURE`.
- Units = `PPBEN.NUMBER_OF_UNITS`; VPU = $1,000 on RPU rows.
- RPU ≠ automatic unit reduction.
- 304 RU policies; 199 BA + 105 BF.
- 82 BF: units × 1000 = DD = specified.
- 23 BF: integer original units; DD = specified < units × 1000.
- `ORIGINAL_UNITS` / `ETI_RPU_*` unused on this book.
- QLAdmin RPU transaction reduces `MUNIT` (Robert spec).
- Issue #55 is a different units defect (tiny/format).

### STRONG INFERENCE

- BA vs BF is the switch for whether DD is the death-benefit authority.
- On the 23, LifePRO stored RPU face in specified/current DB and left issue units.
- QLAdmin will overstate face on those 23 if units are copied.
- `expected_units = DD / VPU` is the comparison Eric described.

### HYPOTHESIS

- Why LifePRO used two BF processors (23 vs 82).
- `BF_DB_OPTION=A` means level specified-amount DB.
- Older LifePRO conversion left units unreduced.
- PUA fold-in already inside BF units on the 82.

---

## 17. Remaining Unknowns

1. Why 23 BF RPU rows were not unit-updated (plan rule, program, era, manual change).
2. Official Product Book sentence for `BF_CURRENT_DB` / `BF_SPECIFIED_AMT` / `BF_DB_OPTION`.
3. ~~Whether QLAdmin `MUNIT` is overwritten to DD/VPU~~ **Resolved 2026-08-18 — Yes.**
4. Whether PUA should be added again on already-RPU LifePRO units (Issue #108 Q1, still open).
5. July-31 extract parity (this study used 6/30).
6. Plan codes for the 23 (PPBEN plan blank).
7. Benefit-history proof of the unit-change date.

---

## 18. Additional Data Needed

1. Eric confirmation on 2–3 of the 23 (e.g. `9010757606`, `9010826422`): LifePRO screen units vs Death Benefit vs Specified Amount.
2. LifePRO Benefit Detail / Death Benefit Values screenshots for one aligned BF (`9010732975`) and one unaligned BF.
3. Product Book or SME definition of `BF_CURRENT_DB`, `BF_SPECIFIED_AMT`, option A.
4. ~~Should QLAdmin Coverage units be recalculated from DD on the 23 only?~~ **Yes (2026-08-18).**
5. PUA treatment on BF RPU.
6. Optional: PPHST / benefit history for one unaligned policy to see whether units ever moved.

---

## 19. Confidence Level

| Question | Confidence |
|---|---|
| What Column DD is | **High** (extract + prior client map) |
| Units are a face quantity | **High** |
| RPU does not always reduce units | **High** (23 measured) |
| `expected_units = DD / VPU` is Eric’s comparison | **High** on BF; **N/A** on BA |
| QLAdmin must use DD-implied units on the 23 | **High** — locked 2026-08-18 |
| Why 23 vs 82 | **Low** (does not block the rule) |
| Safe to code a fleet rewrite today | **No** — Intake → Risk and Development approval still required |

---

## 20. Recommended Next Investigation Step

1. ~~SME question on `9010757606`~~ **Answered Yes 2026-08-18.**
2. **Proceed to Intake** when ready — lock BA-exclusion + BF-only recalculation (`MUNIT = DD / VPU` when they differ).
3. Do not start Development on a blanket RPU unit reduction. Do not touch the 82 aligned BF or 199 BA rows.

---

## Most Important Question

> Given a LifePRO policy in Reduced Paid-Up status, its current units, its death benefit amount, and the applicable PPBENTYP Column DD value, how can we determine whether the LifePRO units are correct and what units QLAdmin should receive?

**Answer from evidence (BF only):**

Column DD is `BF_CURRENT_DB`. On BF RPU it is the stored current death benefit (and, on this cut, equals specified amount).

```text
expected_units = BF_CURRENT_DB / VALUE_PER_UNIT
```

- If `NUMBER_OF_UNITS ≈ expected_units`, LifePRO already reduced (or never needed to reduce) units. QLAdmin should receive `NUMBER_OF_UNITS`.
- If `NUMBER_OF_UNITS ≠ expected_units` (the 23 integer-unit cases), LifePRO units are the **original face quantity** and are **not** the RPU death benefit. The correct QLAdmin units, if the conversion must match LifePRO death benefit, are `expected_units`.

**Answer for traditional BA:**

Column DD is 0.00. It cannot be used. LifePRO units × VPU **are** the death benefit. Keep those units (including the SAL near-zero base + SU face pattern).

**SME locked 2026-08-18:** QLAdmin **is** allowed to overwrite LifePRO units on the 23 so converted face equals Column DD. Example: `9010757606` `MUNIT = 19.10196`, Amount Ins = $19,101.96.
