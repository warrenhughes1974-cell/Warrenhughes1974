# Client Follow-Up Analysis — L10 LP95 / L01 10Y Rate Documents

**Date:** 2026-07-07  
**Mode:** Analysis only  
**Code status:** No converter code changed  
**Client documents reviewed:**

- `docs/L10 LP95 Age Duration.docx`
- `docs/L01 10Y LT - LifePRO Product Rate Informaiton (003).docx`

---

## Summary

The client follow-up documents expose two separate issues that were not fully answered by the first-pass inherited non-CV implementation:

1. **L10 LP95 / L10 LP9595 source distinction**
   - `PCOVRSGT.csv` has active `L10 LP95` segment slots pointing to `L10 LP9595`.
   - `L10 LP9595` is **not present** in the delivered `Rate_Table_Extract_20260427.csv`.
   - `L10 LP9595` is **not present** in `PAAGERAT_AttainedAge_Rates_Extract_20260428.csv`.
   - `L10 LP9595` is **not present** as a `PCOVR.csv` coverage row or policy-form crosswalk row.
   - Therefore the current converter cannot load rates directly from `L10 LP9595`; the extract does not contain rate rows for it.

2. **L01 10Y NP screenshots are not represented in the current rate extract/output**
   - The new L01 document includes `Type = NP`, `Coverage ID = L01 10Y`, age/duration screenshots.
   - The delivered `Rate_Table_Extract_20260427.csv` does **not** contain `L01 10Y` or `L01 10Y LT` NP rows.
   - Current pipeline output has **0 `QuikNps` keys** for `5L0110` (`L01 10Y LT`).
   - This appears to be a source-extract coverage gap or unmodeled segment inheritance, not a fixed first-pass non-CV manifest item.

The earlier first-pass inherited non-CV work is still valid for its approved manifest, but it did **not** include these newly surfaced source IDs:

- `L10 LP9595`
- `L01 10Y` NP source segment / coverage

---

## Client Email Point Reviewed

Eric wrote:

> I believe most are correct, but I have concerns about the L10s not having a CV with them. The attached contains screenshots for L10 LP95 for CV and RV. There is a Coverage ID in LifePRO of L10 LP9595 that is limited to NP and RV.

This aligns with repository evidence in part:

- The screenshots do show `L10 LP95` CV and RV.
- `PCOVRSGT.csv` does show `L10 LP95` active segment references to `L10 LP9595`.
- The current delivered rate extracts do **not** include `L10 LP9595` as a rate-bearing `COVERAGE_ID`.

---

## Documents Extracted

The DOCX files are mostly image-based. Screenshots were extracted to:

- `Issue_Log_Items/Issue_Rates_Inheritance_Validation/extracted_screenshots/L10_LP95_Age_Duration/`
- `Issue_Log_Items/Issue_Rates_Inheritance_Validation/extracted_screenshots/L01_10Y_LT_003/`

Image counts:

| Document | Extracted Screenshots | Observations |
|---|---:|---|
| `L10 LP95 Age Duration.docx` | 12 | CV and RV age/duration screenshots for `Coverage ID = L10 LP95`; text note `NF, NN, NP, PN` |
| `L01 10Y LT - LifePRO Product Rate Informaiton (003).docx` | 22 | PR attained-age screenshots for `Segment ID = L01 10Y LT`; NP age/duration screenshots for `Coverage ID = L01 10Y` |

---

## L10 Findings

### Source setup

`PCOVRSGT.csv` active slots for `L10 LP95` include:

| Coverage | Slot | Segment |
|---|---:|---|
| `L10 LP95` | 1 | `L10 LP95` |
| `L10 LP95` | 2 | `L10 LP95` |
| `L10 LP95` | 6 | `L10 PRE97` |
| `L10 LP95` | 10 | `L10 PRE97` |
| `L10 LP95` | 12 | `L10 LP9595` |
| `L10 LP95` | 13 | `L10 LP9595` |
| `L10 LP95` | 18 | `AGE 95` |
| `L10 LP95` | 19 | `BA2` |
| `L10 LP95` | 22 | `L10 PRE97` |
| `L10 LP95` | 27 | `L10 LP95` |
| `L10 LP95` | 28 | `L10 PRE97` |
| `L10 LP95` | 29 | `L10 LP95` |
| `L10 LP95` | 31 | `LIFEWCV` |
| `L10 LP95` | 32 | `L10 LP95` |
| `L10 LP95` | 33 | `L10 LP95` |
| `L10 LP95` | 38 | `LIFE` |

### Delivered source rows

`Rate_Table_Extract_20260427.csv` contains:

| Coverage ID | Type | Source Rows |
|---|---:|---:|
| `L10 LP95` | CV | 29,599 |
| `L10 LP95` | NF | 27,090 |
| `L10 LP95` | NN | 23,964 |
| `L10 LP95` | NP | 27,606 |
| `L10 LP95` | PN | 24,475 |
| `L10 LP95` | RV | 28,908 |
| `L10 LP95SR` | NP | 9,202 |
| `L10 LP95SR` | RV | 9,202 |
| `L10 LP9595` | Any | **0** |

`PAAGERAT_AttainedAge_Rates_Extract_20260428.csv` contains:

| Coverage / Segment ID | Type | Source Rows |
|---|---:|---:|
| `L10 LP95` | PR | 1,832 |
| `L10 LP95SR` | PR | 172 |
| `L10 LP9595` | Any | **0** |

### Current pipeline output

Current in-memory pipeline grid counts:

| Plan | Source Coverage / Meaning | QuikCvs | QuikNps | QuikTvs | QuikGps |
|---|---|---:|---:|---:|---:|
| `1L1095` | `L10 LP95` | 3,246 | 3,000 | 3,096 | 0 |
| `1L10SR` | `L10 LP95SR` | 3,246 | 1,000 | 1,000 | 0 |
| `1L10OD` | `L10 PRE97` | 3,285 | 3,000 | 3,096 | 0 |
| `1L10PR` | `L10 PREUNI` | 1,623 | 3,000 | 3,096 | 582 |
| `1L10SO` | `L10 SR OLD` | 3,285 | 3,000 | 3,096 | 1,164 |

### L10 RV screenshot vs delivered extract

The L10 screenshots show RV for `Coverage ID = L10 LP95`, `Age = 35`, `Gender = M`, `Band = 1`, underwriting classes `S`, `P`, and `B`.

For the same slice, the delivered `Rate_Table_Extract_20260427.csv` has terminal `1000.00` at **source duration 62** for `S`, `P`, and `B`.

The screenshot image appears to show terminal `1000.00` later in the displayed duration range. This should be treated as a **source extract vs LifePRO screen reconciliation issue** before code changes.

---

## L01 Findings

### Source setup

`PCOVRSGT.csv` active slots for `L01 10Y LT` include:

| Coverage | Slot | Segment |
|---|---:|---|
| `L01 10Y LT` | 1 | `L01 10Y LT` |
| `L01 10Y LT` | 12 | `L01 10Y` |
| `L01 10Y LT` | 13 | `L01 10Y` |
| `L01 10Y LT` | 18 | `10YR LV TM` |
| `L01 10Y LT` | 19 | `DA9` |
| `L01 10Y LT` | 32 | `L01 10Y` |
| `L01 10Y LT` | 33 | `L01 10Y` |

### Delivered source rows

`Rate_Table_Extract_20260427.csv` contains `L01 10Y MA`, but not `L01 10Y` or `L01 10Y LT` NP rows:

| Coverage ID | Type | Source Rows |
|---|---:|---:|
| `L01 10Y MA` | NN | 1,425 |
| `L01 10Y MA` | NP | 134 |
| `L01 10Y MA` | PN | 1,720 |
| `L01 10Y MA` | PR | 9,720 |
| `L01 10Y MA` | RV | 2 |
| `L01 10Y` | NP | **0** |
| `L01 10Y LT` | NP | **0** |

`PAAGERAT_AttainedAge_Rates_Extract_20260428.csv` contains:

| Segment ID | Type | Source Rows |
|---|---:|---:|
| `L01 10Y LT` | PR | 924 |

### Current pipeline output

Current in-memory pipeline grid counts:

| Plan | Coverage / Meaning | QuikNps | QuikTvs | QuikGps |
|---|---|---:|---:|---:|
| `5L0110` | `L01 10Y LT` | 0 | 0 | 924 |
| `5L01MA` | `L01 10Y MA` | 14 | 2 | 1,080 |

### L01 screenshot evidence

The L01 document contains:

- `Segment ID = L01 10Y LT`, `Type = PR` attained-age screenshots.
- `Coverage ID = L01 10Y`, `Type = NP`, age/duration screenshots.

The current pipeline loads `L01 10Y LT` PR to `5L0110` / `QuikGps`, but does **not** load the `L01 10Y` NP screenshots to `5L0110` because the current `Rate_Table` extract does not include `L01 10Y` NP rows.

---

## What We Were Missing

The prior inherited-rate analysis was based on source rows present in the delivered extracts and rate-owner candidates found from those rows. It did not identify:

1. `L10 LP9595`, because that ID exists in `PCOVRSGT.csv` but not in the delivered rate extracts or `PCOVR.csv`.
2. `L01 10Y` NP, because the screenshots show it, but the delivered `Rate_Table` extract does not contain those rows.
3. L10 RV terminal placement discrepancy, because the delivered extract places `1000.00` at duration 62 while the screenshot display appears later.

These are not covered by the closed first-pass non-CV inheritance manifest.

---

## Current Assessment

| Item | Assessment | Code Change Needed Now? |
|---|---|---|
| `L10 LP95` CV direct load | Present in source and output for `1L1095`; inherited CV exists for selected older L10 plans | No, pending exact client expectation for `1L10OD` / `1L10PR` CV |
| `L10 LP95` NP/RV direct load | Present in source and output for `1L1095` | No |
| `L10 LP9595` NP/RV | Segment exists in PCOVRSGT but no extract rows exist | No code change until source extract or business rule supplied |
| `1L10OD` / `1L10PR` CV | `1L10OD` has CV via Issue #40 selected owner; `1L10PR` has direct CV from `L10 PREUNI`; confirm client expectation | Analysis follow-up |
| `L01 10Y LT` PR | Present in PAAGERAT and output `QuikGps` for `5L0110` | No |
| `L01 10Y` NP | Screenshot evidence exists; current source extract lacks rows and output has 0 `QuikNps` for `5L0110` | Source/extract or new inheritance issue likely |
| L10 RV duration endpoint | Screenshot appears inconsistent with delivered extract | Source-vs-screen validation required |

---

## Recommended Next Steps

1. Ask client / source team for the **actual extract rows or DBF table** behind `L10 LP9595`.
   - Specifically confirm whether `L10 LP9595` is a rate-bearing coverage ID in LifePRO or a segment alias that should resolve to `L10 LP95` rows.
2. Ask client / source team for `L01 10Y` NP source rows.
   - The screenshot shows `Coverage ID = L01 10Y`, `Type = NP`; the current extract does not include it.
3. Create a new tracked issue for **L01 / L10 source-extract reconciliation** before changing loader logic.
4. Do not reopen the closed first-pass non-CV inheritance issue until the source IDs are resolved.
5. Do not add `PR` / `QuikGps` to the inherited-rate loader; L01 PR is already handled through PAAGERAT.
6. Do not add PUA non-CV or PAAGERAT precedence work as part of this L10/L01 follow-up.

---

## Final Status

This pass found evidence of **new source/extract gaps**, not just a bug in the just-implemented inherited-rate loader.

**Most important finding:** `L10 LP9595` and `L01 10Y` are visible in LifePRO setup/screenshots but are not present as rate-bearing rows in the delivered extracts used by the converter. The converter cannot load what is not present unless we define and approve a new segment-alias/inheritance rule backed by source evidence.

