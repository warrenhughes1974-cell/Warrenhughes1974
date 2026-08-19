# Issue #141 — Discovery Notes (Search & Discuss)

**Issue:** #141 — Reserve Category  
**Date:** 2026-08-19  
**Framework stage:** Stage 0 Discovery (G-D)  
**Code:** None  

---

## Client ask (verbatim)

Put the reserve category on the User Defined field on the policy. New QuikSpec field `RESRVCAT` (char). Reserve category used to be the LOB on the plan. Crosswalk plan LOB to policies. Plans we populated with items like ISWL need to stay; LifePRO reserve category goes on the policy in QuikSpec.

Screenshot: Plan Information `A96DAR` / Deposit Annuity Rider shows **LOB = 03**, NAIC LOB = NAPLAN.

---

## Verdict

This is a **QuikSpec add-column**, not a QuikPlan change.

- **Keep** Issue #99 plan tags: 8 ISWL plans stay `MKTG` / `PRODUCT` / `HLOB` = `ISWLFE`.
- **Do not** copy current `quikplan.PRODUCT` or `HLOB` onto the policy (2,268 policies would get `ISWLFE`).
- **Source** for reserve category is LifePRO **`PCOVR.PRODUCT_TYPE`** (what used to show as plan LOB / what we emit as `quikplan.PRODUCT` before the ISWL overlay).
- **Target:** `quikspec.RESRVCAT` on every converted policy, via the policy’s **base** plan (`quikridr` MPHASE=1).

**Field width locked 2026-08-19 (Warren):** `RESRVCAT` is **char 2**. That fits LifePRO codes (`03`, `12`, `05`, `CF`, `70`). Desktop Append Tool master `templates\QUIKSPEC.DBF` has the same char-2 field (Warren confirmed same day).

---

## Source findings

**File:** `QLA_Migration/Source/PCOVR_Coverage_Extract_20260630.csv`  
**Field:** `PRODUCT_TYPE` (141 coverages)

| PRODUCT_TYPE | Coverages | Notes |
|---|---:|---|
| 03 | 51 | Includes `896 DAR` → QLA `A96DAR` (screenshot LOB=03) |
| 12 | 16 | |
| 10 / 07 | 10 each | |
| 08 | 8 | |
| L | 7 | 1-character; also has VAL_CODE=03 on some disability/term |
| 06 / 05 / 16 | ISWL LifePRO values | Overlayed to ISWLFE on plan by #99 |
| CF, 13, 09, 19, 70, 11, 0 | remainder | |

Code width: **133 of 141** coverages are 2 characters.

`PCOVR.VAL_CODE` is almost empty (7 × `03`, 1 × `5%`). Not the screenshot match. `A96DAR` Output today: `PRODUCT=03`, `HLOB` blank, `MKTG` blank. UI LOB=03 is the LifePRO product/reserve code, not the ISWL tag.

**PPOLC** has no reserve-category column. `PPBEN.CATEGORY_CODE` is blank on the extract.

### Policy join (current Output, phase-1 plan)

If we wrongly used **current** `quikplan.PRODUCT`:

| Value | Policies |
|---:|---:|
| ISWLFE | 2,268 |
| 13 | 845 |
| 03 | 677 |
| 12 | 541 |
| others | rest of 5,083 |

Correct path uses **pre-#99** `PRODUCT_TYPE` so ISWL policies get `05` / `06` / `16`, not `ISWLFE`.

Examples:

| Policy | Base plan | Plan HLOB (keep) | RESRVCAT (LifePRO PRODUCT_TYPE) |
|---|---|---|---|
| 9010143726C | 221END | (blank) | 03 |
| 9010148272C | 221END | (blank) | 03 |
| 9010713704C | 1659C2 | ISWLFE | 05 (not ISWLFE) |

---

## Current conversion vs desired

| Area | Current | Desired |
|---|---|---|
| `quikspec` emit | MPOLICY, VANISH, VANISHDT, RESSTATE | Add `RESRVCAT` |
| `quikspec.RESRVCAT` | Field does not exist in converter schema | LifePRO `PRODUCT_TYPE` for base plan |
| `quikplan` HLOB / MKTG / PRODUCT on ISWL | `ISWLFE` (#99) | **Unchanged** |
| Non-ISWL `quikplan.PRODUCT` | `PCOVR.PRODUCT_TYPE` | Unchanged; copy that value to the **policy**, not the plan again |
| Append / DBF | Working QUIKSPEC.DBF has `RESRVCAT` char 2 | Append Tool master template also has `RESRVCAT` char 2 (Warren 2026-08-19) |

---

## Suspected target

- **Table:** `quikspec` (Policy User Defined Tab, Help §7.209)
- **Field:** `RESRVCAT` (client-added; Help stock schema only lists `MPOLICY`)
- **UI:** Policy → User Defined
- **Not:** QuikPlan LOB, NAIC LOB (`MNAICLOB` stays NAPLAN), QuikIswl `MLOB` (I/U)

---

## Related issues

| Issue | Relationship |
|---|---|
| **#99** | ISWL `MKTG`/`PRODUCT`/`HLOB`=`ISWLFE`. Preserve. Do not overwrite. |
| **#124** | QuikIswl `MLOB=I` — different table/field. Do not touch. |
| **#132** | Residence on policy (`RESSTATE` / `MRESSTATE`). Same QuikSpec row; do not disturb. |
| **#145** | Vanish flag on QuikSpec. Same table; do not disturb `VANISH`. |
| **DG-R-004** | `MNAICLOB=NAPLAN`. Not this field. |

---

## Proposed work list (Planning will refine)

1. Append Tool master template already has `RESRVCAT` char 2 (Warren 2026-08-19).
2. Add `RESRVCAT` to converter schema, `Sync_Rulebook_quikspec.csv`, `schema_manifest.json`.
3. For each `quikspec` row: base `quikridr.MPLAN` → LifePRO `PCOVR.PRODUCT_TYPE` (not current ISWL-overlaid PRODUCT).
4. Leave `quikplan` ISWLFE tags and `#145` VANISH / `#132` RESSTATE alone.
5. Validator: schema includes `RESRVCAT`; `221END` policies = `03`; `1659C2` = LifePRO `05` not `ISWLFE`; no plan HLOB change.

---

## Open questions

1. **Field width** — **locked char 2** (Warren 2026-08-19).
2. Confirm `PCOVR.PRODUCT_TYPE` is the reserve category Eric wants (matches A96DAR LOB=03). Alternative `VAL_CODE` is not populated on that plan.
3. Multi-coverage policies: lock **base phase only**, or a rider-priority rule?
4. Blank / `0` / `L` PRODUCT_TYPE: emit as-is or hold?
5. Append Tool master template — **locked** same `RESRVCAT` char 2 (Warren 2026-08-19).

---

## Stop

Discovery complete. Awaiting **Proceed to Intake**.
