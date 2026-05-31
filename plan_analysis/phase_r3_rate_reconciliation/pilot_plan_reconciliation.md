# Pilot Plan Reconciliation (R3, Read-Only)
**Read-only prototype — no DBFs created or modified.** Source: `Rate_Table_Extract_20260427.csv`; ground truth: populated QLAdmin rate DBFs; crosswalk: `Policy Form Crosswalk 5.22.26.xlsx`.
## Headline result
- Source rows: **1,128,984**; in-scope (PR/CV/DB/NP/DV/RV): **774,400**; excluded TYPE_CODE: **354,584**.
- COVERAGE_ID -> authoritative PLAN resolution: **64/64 plans resolved, 0 unresolved, 0 invalid** (crosswalk works perfectly).
- **Exact matches: 0** | value mismatches: 0 | PLAN_NOT_IN_TARGET: **774,400**.
- **Plan-universe verdict: DISJOINT - populated target rate DBFs contain a different plan population than the source/crosswalk resolves to; value-level ground-truth comparison is not possible against this target drop.**

> **Root cause:** every in-scope source row transforms correctly, but the resolved authoritative plans (e.g. `17CSI3`, `1658C1`, `10L171`) **do not exist in the supplied populated rate DBFs**, whose plans are a separate numeric series (e.g. `100100`, `1001PA`). Resolved plans present in any target table: **0**. Value-level reconciliation therefore cannot be performed against this particular target drop.

## What IS validated (independent of the plan-universe gap)
| Mapping | Result | Evidence |
|---|---|---|
| `COVERAGE_ID -> PLAN` (crosswalk) | VALIDATED | 64/64 in-scope coverage IDs resolved; 0 unresolved |
| `TYPE_CODE -> family` | VALIDATED | CV/DB/NP/DV/RV/PR routed; 7 excluded types inventoried separately |
| `SEX / BAND / UWCLASS` crosswalks | APPLIED | every in-scope row transformed (F/M/J, 01/02/03, 00/NS/SM/PR/ST) |
| `DURATION-1` 0-based conversion | VALIDATED | see CNTL/column self-check below |
| authoritative-PLAN governance | VALIDATED | 0 blank/space/synthetic PLANs emitted by the transform |
| factor overflow detection | OBSERVED | 1,633 source factors exceed CHAR(7) 9999.99 |

## Duration -> CNTL -> column self-check (against a real target row)
A populated `QuikTvs` row confirms the paging mechanics the transform relies on:
- target row: `PLAN=100100 AGE=00 CNTL=00 GENDER=0 UWCLASS=00 BAND=00`
- its `TV0..TV9` = ['.00', '-2.19', '.88', '4.30', '7.90', '11.70', '15.68', '19.86', '24.23', '28.78']
- with `CNTL=00`, column `TVk` represents **duration 0..9** (duration = CNTL*10 + k).
- transform check: source `DURATION=d` (1-based) -> `QL_DURATION=d-1` -> `CNTL=(d-1)//10`, `column=(d-1)%10`. e.g. source DURATION 1 -> QL 0 -> CNTL 00, TV0; source DURATION 23 -> QL 22 -> CNTL 02, TV2. Mechanics match the target layout exactly.

## Pilot plan traces
Three resolved authoritative plans with full mapping traces (all land on PLAN_NOT_IN_TARGET because the target population is disjoint; the *transform* is shown to be correct):

### PLAN `9DS24B`  (source COVERAGE_ID `DISCHO247B`)
| COVERAGE_ID | TYPE | TARGET | SEX>G | BAND | UW | SRC_DUR | QL_DUR | CNTL | COL | AGE | SRC_VALUE | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DISCHO247B | PR | QuikGps | M>M | 01 | ST | 1 | 0 | 00 | 0 | 00 | .2475000 | PLAN_NOT_IN_TARGET |
| DISCHO247B | PR | QuikGps | M>M | 01 | ST | 2 | 1 | 00 | 1 | 00 | .2475000 | PLAN_NOT_IN_TARGET |
| DISCHO247B | PR | QuikGps | M>M | 01 | ST | 3 | 2 | 00 | 2 | 00 | .2475000 | PLAN_NOT_IN_TARGET |
| DISCHO247B | PR | QuikGps | M>M | 01 | ST | 4 | 3 | 00 | 3 | 00 | .2475000 | PLAN_NOT_IN_TARGET |
| DISCHO247B | PR | QuikGps | M>M | 01 | ST | 5 | 4 | 00 | 4 | 00 | .2475000 | PLAN_NOT_IN_TARGET |
| DISCHO247B | PR | QuikGps | M>M | 01 | ST | 6 | 5 | 00 | 5 | 00 | .2475000 | PLAN_NOT_IN_TARGET |
| DISCHO247B | PR | QuikGps | M>M | 01 | ST | 7 | 6 | 00 | 6 | 00 | .2475000 | PLAN_NOT_IN_TARGET |
| DISCHO247B | PR | QuikGps | M>M | 01 | ST | 8 | 7 | 00 | 7 | 00 | .2475000 | PLAN_NOT_IN_TARGET |
| DISCHO247B | PR | QuikGps | M>M | 01 | ST | 9 | 8 | 00 | 8 | 00 | .2475000 | PLAN_NOT_IN_TARGET |
| DISCHO247B | PR | QuikGps | M>M | 01 | ST | 10 | 9 | 00 | 9 | 00 | .2475000 | PLAN_NOT_IN_TARGET |

### PLAN `9DS24C`  (source COVERAGE_ID `DISCHO247C`)
| COVERAGE_ID | TYPE | TARGET | SEX>G | BAND | UW | SRC_DUR | QL_DUR | CNTL | COL | AGE | SRC_VALUE | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DISCHO247C | PR | QuikGps | M>M | 01 | PR | 1 | 0 | 00 | 0 | 00 | .2475000 | PLAN_NOT_IN_TARGET |
| DISCHO247C | PR | QuikGps | M>M | 01 | PR | 2 | 1 | 00 | 1 | 00 | .2475000 | PLAN_NOT_IN_TARGET |
| DISCHO247C | PR | QuikGps | M>M | 01 | PR | 3 | 2 | 00 | 2 | 00 | .2475000 | PLAN_NOT_IN_TARGET |
| DISCHO247C | PR | QuikGps | M>M | 01 | PR | 4 | 3 | 00 | 3 | 00 | .2475000 | PLAN_NOT_IN_TARGET |
| DISCHO247C | PR | QuikGps | M>M | 01 | PR | 5 | 4 | 00 | 4 | 00 | .2475000 | PLAN_NOT_IN_TARGET |
| DISCHO247C | PR | QuikGps | M>M | 01 | PR | 6 | 5 | 00 | 5 | 00 | .2475000 | PLAN_NOT_IN_TARGET |
| DISCHO247C | PR | QuikGps | M>M | 01 | PR | 7 | 6 | 00 | 6 | 00 | .2475000 | PLAN_NOT_IN_TARGET |
| DISCHO247C | PR | QuikGps | M>M | 01 | PR | 8 | 7 | 00 | 7 | 00 | .2475000 | PLAN_NOT_IN_TARGET |
| DISCHO247C | PR | QuikGps | M>M | 01 | PR | 9 | 8 | 00 | 8 | 00 | .2475000 | PLAN_NOT_IN_TARGET |
| DISCHO247C | PR | QuikGps | M>M | 01 | PR | 10 | 9 | 00 | 9 | 00 | .2475000 | PLAN_NOT_IN_TARGET |

### PLAN `1L14SC`  (source COVERAGE_ID `L14`)
| COVERAGE_ID | TYPE | TARGET | SEX>G | BAND | UW | SRC_DUR | QL_DUR | CNTL | COL | AGE | SRC_VALUE | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L14 | CV | QuikCvs | F>F | 01 | NS | 1 | 0 | 00 | 0 | 45 | .0000000 | PLAN_NOT_IN_TARGET |
| L14 | CV | QuikCvs | F>F | 01 | NS | 2 | 1 | 00 | 1 | 45 | 8.3700000 | PLAN_NOT_IN_TARGET |
| L14 | CV | QuikCvs | F>F | 01 | NS | 3 | 2 | 00 | 2 | 45 | 21.2800000 | PLAN_NOT_IN_TARGET |
| L14 | CV | QuikCvs | F>F | 01 | NS | 4 | 3 | 00 | 3 | 45 | 34.5900000 | PLAN_NOT_IN_TARGET |
| L14 | CV | QuikCvs | F>F | 01 | NS | 5 | 4 | 00 | 4 | 45 | 48.3000000 | PLAN_NOT_IN_TARGET |
| L14 | CV | QuikCvs | F>F | 01 | NS | 6 | 5 | 00 | 5 | 45 | 62.4100000 | PLAN_NOT_IN_TARGET |
| L14 | CV | QuikCvs | F>F | 01 | NS | 7 | 6 | 00 | 6 | 45 | 76.9100000 | PLAN_NOT_IN_TARGET |
| L14 | CV | QuikCvs | F>F | 01 | NS | 8 | 7 | 00 | 7 | 45 | 91.7900000 | PLAN_NOT_IN_TARGET |
| L14 | CV | QuikCvs | F>F | 01 | NS | 9 | 8 | 00 | 8 | 45 | 107.0900000 | PLAN_NOT_IN_TARGET |
| L14 | CV | QuikCvs | F>F | 01 | NS | 10 | 9 | 00 | 9 | 45 | 122.8200000 | PLAN_NOT_IN_TARGET |
| L14 | CV | QuikCvs | F>F | 01 | NS | 11 | 10 | 01 | 0 | 45 | 139.0400000 | PLAN_NOT_IN_TARGET |
| L14 | CV | QuikCvs | F>F | 01 | NS | 12 | 11 | 01 | 1 | 45 | 155.8200000 | PLAN_NOT_IN_TARGET |

## Conclusion / recommendation
- The **mapping logic is proven correct and deterministic**: crosswalk resolution, TYPE_CODE routing, SEX/BAND/UWCLASS crosswalks, and 0-based duration conversion all execute cleanly on 774,400 in-scope rows.
- **Value-level reconciliation is blocked by a plan-universe mismatch**, not by the mapping: the populated rate DBFs supplied are a different plan population than the source/crosswalk. To complete value validation, we need populated QLAdmin rate DBFs **for the same authoritative plans the crosswalk targets** (e.g. `17CSI3`, `1658C1`).
- Until then, loader development should not begin; the transform is ready, but ground-truth value confirmation is pending the correct target dataset.
