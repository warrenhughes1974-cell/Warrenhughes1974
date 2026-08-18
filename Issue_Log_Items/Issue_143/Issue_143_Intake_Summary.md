# Issue #143 — Intake Summary

**Issue:** #143 — Units Incorrect (RPU)  
**Framework stage:** Stage 1 Intake  
**Date:** 2026-08-18  
**Code changed:** None  
**Engine at intake:** v58.95  
**Owner:** Eric (issue) / Warren (assigned)  
**Priority:** Go-No Go  

---

## Client symptom (verbatim)

> Some policies in Reduced Paid Up Status did not have their units reduced in LifePRO. The death benefit amount comparison should occur with Column DD of the PPBENTYP_BenefitType_Extract to determine accuracy of the units versus death benefit.

## Normalized symptom

On some Reduced Paid-Up policies LifePRO left `PPBEN.NUMBER_OF_UNITS` at the original issue quantity (whole units such as 25) while the paid-up death benefit was written to PPBENTYP Column DD (`BF_CURRENT_DB`). The converter copies units into `quikridr.MUNIT`, so QLAdmin Amount Ins (`MUNIT × MVPU`) shows the original face, not the RPU death benefit.

SME locked 2026-08-18: QLAdmin units **must** become `BF_CURRENT_DB / VALUE_PER_UNIT` in that case. Anchor: `9010757606` units 25 / $25,000 → **19.10196 / $19,101.96**.

## Example policies

| LifePRO | QLAdmin | Class | Source units | Column DD | Proposed MUNIT |
|---|---|---|---:|---:|---:|
| `9010757606` | `9010757606C` | BF unaligned | 25.00000 | $19,101.96 | **19.10196** |
| `9010766847` | `9010766847C` | BF unaligned | 25.00000 | $5,163.41 | **5.16341** |
| `9010826422` | `9010826422C` | BF unaligned | 50.00000 | $9,655.90 | **9.65590** |
| `9010732975` | `9010732975C` | BF aligned (control) | 14.08377 | $14,083.77 | 14.08377 (no change) |
| `9010165095` | `9010165095C` | BA traditional (control) | 1.69072 | $0.00 | 1.69072 (no change) |

## Suspected domain

Policy / rider **units** — `quikridr.MUNIT` (Amount Ins). Not premiums, status, rates, or claims.

## In scope (first pass)

- BF (`TYPE_CODE=BF`) RPU (`PAID_UP_TYPE=RU`) benefits where `|NUMBER_OF_UNITS − BF_CURRENT_DB / VALUE_PER_UNIT| > 0.01`
- Phase-1 `MUNIT` only, so `MUNIT × MVPU = BF_CURRENT_DB`
- Preserve #55 floor / leading-zero emit **after** the remap

## Out of scope (first pass)

- Blanket RPU unit reduction on traditional BA
- Recalculating the 82 BF RPU rows that already match DD
- SAL near-zero base + SU face (Issue #55)
- `MPREM` / `MMODEPREM` (#26 / #88 / #137)
- `MSAVEUNIT` on ETI/RPU (Issue #108A leaves blank)
- Re-deriving RPU from cash value / NSP
- PUA fold-in (Issue #108 residual)

## Related issues

| Issue | Relevance |
|---|---|
| **#55 CLOSED** | Tiny-unit floor + decimal emit — do not regress; remap values are all ≫ 0.001 |
| **#108 CLOSED** | RPU field set; `MSAVE*` blank on 44/45; do not write original units into `MSAVEUNIT` |
| **#21 / #21A CLOSED** | Client Column DD = `BF_CURRENT_DB`; Column DB = `BF_NON_FORFEITURE` |
| **#124 CLOSED** | QuikIswl `MDB = MUNIT × 1000` — will follow corrected units on next ISWL seed (not an override) |
| **#76 / #72** | ETI/RPU status / pay-up — do not touch |

## Artifact inventory

| Artifact | Present? |
|---|---|
| Client narrative | Yes |
| SME unit-recalc confirmation | Yes (2026-08-18) |
| Research report | Yes — `Issue_143_Research_Report.md` |
| Source PPOLC / PPBEN / PPBENTYP 20260630 | Yes |
| Current `Output/quikridr.csv` | Yes — 23 still emit unreduced units |
| Screenshots | No (source + Output measurable without them) |

## Immediate blockers

None. SME rule is locked. Source and Output are present.

## Severity / owner

| Field | Value |
|---|---|
| Severity | High on the 13 in-force RPU (MSTATUS 45) — Amount Ins overstated |
| Owner | Conversion |
| AGENTS.md | Surgical `MUNIT` remap only; no rulebook rewrite |

## Gate G0 checklist

- [x] Issue folder `Issue_Log_Items/Issue_143/`
- [x] Intake summary written
- [x] Example policies listed
- [x] Owner and priority assigned
- [x] No code or rulebook changes
