# PAAGERAT Precedence Questions

**Status:** Business-rule questions only  
**Relationship to non-CV inheritance:** Separate workstream  
**Code status:** Not implemented

---

## Summary

The prior validation found **301 PAAGERAT source/output conflicts**.

These are not missing inherited-rate rows. They are cases where:

- PAAGERAT segment resolution finds a source row,
- the target QLAdmin key already has a value from another source path,
- current grid logic keeps the existing value rather than replacing it with the PAAGERAT value.

This must not be mixed with the non-CV inherited-rate fix.

---

## Conflict Counts

By plan:

| Plan | Conflict Count |
|------|---------------:|
| `1L10SO` | 175 |
| `7687J3` | 62 |
| `1L16GD` | 42 |
| `1679CS` | 12 |
| `5667AT` | 5 |
| `1658CS` | 4 |
| `57ATCR` | 1 |

By type:

| Type | Conflict Count |
|------|---------------:|
| `PR` | 285 |
| `U6` | 8 |
| `BP` | 6 |
| `U5` | 2 |

---

## Examples

| Plan | Type | Segment / Parent | Age | Gender | Band | UW | PAAGERAT Value | Emitted Value |
|------|------|------------------|----:|--------|------|----|---------------:|--------------:|
| `5667AT` | PR | `667 ART` | 99 | M | 02 | PR | 533.17 | 501.23 |
| `5667AT` | PR | `667 ART` | 99 | M | 02 | SM | 637.24 | 593.20 |
| `7687J3` | PR | `686S 30MRG` / `687J 30MRG` | 21 | M | 01 | NS | 2.18 | 3.76 |
| `7687J3` | PR | `686S 30MRG` / `687J 30MRG` | 22 | M | 01 | NS | 2.19 | 3.77 |

Full detail remains in:

`Issue_Log_Items/Issue_Rates_Inheritance_Validation/rate_source_trace_matrix.csv`

---

## Why This Should Be Handled Separately

Non-CV inheritance gaps:

- no issuing-plan output exists,
- PCOVRSGT points to a source owner,
- likely fix is to emit approved inherited rows.

PAAGERAT conflicts:

- output already exists,
- source values disagree,
- likely fix is source precedence, not inherited-row generation.

Combining these would create two risks:

1. A missing-row fix could accidentally overwrite established premium/COI outputs.
2. A source precedence fix could be misrepresented as inherited-rate support.

Therefore:

- Include `NP`, `RV`, `DV`, `DB` in inherited-rate analysis only after business approval.
- Keep `PR` out of first inherited-rate implementation.
- Resolve PAAGERAT precedence as a separate issue/gate.

---

## Current Code Behavior

`qla_core/rate_factor_loader.build_factor_grid()` treats PAAGERAT rows specially when a target cell already exists:

- if PAAGERAT tier is lower than prior tier, PAAGERAT can replace prior,
- if tier is higher, it is ignored,
- if same tier and same value, no issue,
- if same tier and different value, first row wins by stream order.

Current stream order in `qla_core/rate_pipeline.py`:

1. Direct `Rate_Table` transform
2. Issue #40 inherited CV
3. PAAGERAT PR/BP/U5/U6 streams

That means many PAAGERAT conflicts are not duplicate-cell blockers; they are quietly resolved by current precedence rules.

---

## Business Rule Questions Needed

1. For `PR` / gross premium, which source is authoritative when both direct `Rate_Table` and PAAGERAT produce the same target key?
   - Direct `Rate_Table`
   - PAAGERAT
   - Product-specific rule
   - Segment-tier rule

2. Should PAAGERAT `PR` ever overwrite direct `Rate_Table` `PR`?

3. Should PAAGERAT `BP` be treated differently from `PR`?

4. For `U5` / `U6`, should PAAGERAT COI/GCOI override existing output when the same key already exists?

5. Are conflicts on `1L10SO`, `7687J3`, and `1L16GD` expected because of multiple premium segment sources?

6. Should conflicts become validation warnings or blockers?

7. Should the output preserve both sources in separate QLAdmin structures, or must one value win?

8. Should source precedence vary by:
   - plan,
   - rate type,
   - segment ID,
   - PCOVRSGT slot order,
   - segment tier,
   - product family?

---

## Recommended Next Step

Create a separate PAAGERAT precedence issue before changing code.

That issue should:

1. Pick one representative conflict plan from each pattern:
   - `1L10SO`
   - `7687J3`
   - `1L16GD`
   - `1679CS`
2. Pull LifePRO screenshots or source documentation for those premium/COI screens.
3. Confirm authoritative source.
4. Encode precedence rules only after approval.

---

## Clear Statement

No PAAGERAT precedence code was changed during this analysis.

