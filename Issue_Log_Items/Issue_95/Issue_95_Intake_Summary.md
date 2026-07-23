# Issue #95 — Intake Summary

**Issue:** #95 — Declared Interest Rates Incorrect  
**Framework stage:** Intake Agent (G0)  
**Status recommendation:** Intake Complete → Planning  
**Generated:** 2026-07-22  
**Owner:** Conversion (Warren)  
**Reporter / UAT:** Eric  
**Business status:** No-Go  
**Priority:** High (rate/interest UAT blocker)  
**Model:** Cursor Grok 4.5 (locked Intake stage)

---

## Client symptom (verbatim)

> The declared interest rates should match the rates in the PDINTTBL_DeclaredInterestRates_Extract. The rates are DAR01, DIV01, IBA01, and L1001 with a rate of 3.50% (Everything but SAL and ISWL) and SAL01 (SAL OL and SAL ML) with a rate of 2.00%. Note the ISWL rates for 658, 659, 668, and 679 are all 4.50%.

## Client symptom (normalized)

QLAdmin declared interest rates do not match LifePRO `PDINTTBL` current declared rates by IDENT family:

| PDINT IDENT | Expected current rate | Product scope (Eric) |
|-------------|----------------------:|----------------------|
| DAR01, DIV01, IBA01, L1001 | **3.50%** | Everything **except** SAL and ISWL |
| SAL01 | **2.00%** | SAL OL and SAL ML |
| CENII (ISWL) | **4.50%** | LifePRO coverages 658, 659, 668, 679 |

Dated 7/21/2026; Status **No-Go**.

## Example policies

**None provided.** Product/IDENT families only. Planning will use plan codes / IDENT current tiers until Eric supplies sample policies or screenshots.

## Suspected domain

**Rates / plan-level declared interest** — LifePRO `PDINT` / `PDINTTBL` → QLAdmin **`QuikUint`** (Help §7.223; same path as Issue #32 ISWL Phase 5).

Not primarily:

- `quikdvdp.MDEPINT` (Issue #21D dividend accum int — separate screen)
- `QuikAint` annuity interest (Issue #51 A60MIR/A96DAR)
- `quikplan.NFOINT` CSO codes (Issue #80)

## In scope (first pass)

- Confirm PDINTTBL current tiers vs Eric’s expected rates (source truth check).
- Confirm what Output currently emits for declared interest (`QuikUint` and related).
- Define IDENT → QLA `MPLAN` emit scope for SAL / ISWL / residual 3.50% bucket.
- Surgical expand or correct rate emit so declared rates match PDINTTBL (Development later).

## Out of scope (first pass)

- Annuity `QuikAint` / PFSA interest rebuild (unless Eric confirms that screen).
- Issue #21D MDEPINT 4.00/4.50 dividend-deposit path (unless Eric confirms that is the wrong screen).
- Loan interest (`LOANINT` / QuikPlSt).
- Changing CV/GP/COI rate factors.

## Related issues

| ID | Relationship |
|----|----------------|
| **#32** | ISWL QuikUint from PDINTTBL CENII/A1 — implemented; current ISWL 4.50% present |
| **#31** | PSEGT/PDINT/PDINTTBL delivery; IDENT catalog documented |
| **#21D** | MDEPINT ISWL 4.50 / non-ISWL 4.00 — **different field**; do not conflate without Eric confirm |
| **#51** | QuikAint stubs for A60MIR/A96DAR — annuity table, not PDINT declared |

## Immediate blockers visible at intake

1. No example policies / screenshots of the wrong QLAdmin field.
2. LifePRO product **668** vs catalog **669** (`1669SR`) / **1668SP** (SPWL) needs clarification.
3. Full IDENT → MPLAN membership for the “everything but SAL and ISWL” 3.50% bucket not yet listed by Eric.

## Artifact inventory

| Artifact | Status |
|----------|--------|
| Client issue-log row (rates + IDENTs) | Provided |
| `PDINTTBL_DeclaredInterestRates_Extract_20260630.csv` | Present in `QLA_Migration/Source/` |
| `PDINT_DeclaredInterestRates_Extract_20260630.csv` | Present |
| Current `Output/rates/QuikUint.csv` | Present (ISWL-only, 32 rows) |
| Example policies / screenshots | **Missing** |

## Severity / owner

- **Severity:** High — Eric No-Go on declared interest vs LifePRO extract.
- **Owner:** Conversion (rate loader / QuikUint path).
- **Source data:** Available (PDINTTBL midyear extract).
