# Issue #42 — Intake Summary

**Issue:** #42 — Missing Rate Extract Rows (L01/L10)  
**Date:** 2026-07-08  
**Framework stage:** Intake complete — awaiting CSO source extract  
**Status:** Awaiting Client / CSO Source Extract  
**Owner:** Warren · **Assigned:** CSO (Eric Scow) / Source Extract Team  
**Priority:** No Go (for L01 NP and L10 LP9595 load until source received)

---

## Client / business symptom

Client-provided LifePRO screenshots show rate tables that are not present in the delivered source extract files QLA received from CSO.

| Gap | LifePRO ID | Rate type | Expected QLAdmin impact |
|-----|------------|-----------|-------------------------|
| L01 | `L01 10Y` / segment `L01 10Y LT` | `NP` (net premiums) | Plan `5L0110` — NP cannot load |
| L10 | `L10 LP9595` under `L10 LP95` | `NP` / `RV` | L10 family plans — NP/RV cannot load |

`PCOVRSGT` may show that these products point to segments, but **segment setup does not contain rate values**. The converter requires actual rows in `Rate_Table` or `PAAGERAT`.

---

## Proof result

Exhaustive converter-side search confirms missing rows:

- `L01 10Y` `NP`: 0 exact rows in `Rate_Table` and `PAAGERAT`
- `L10 LP9595` (any rate type): 0 exact rows in `Rate_Table` and `PAAGERAT`

Evidence: `Issue_Log_Items/Issue_Rates_Inheritance_Validation/client_l10_l01_followup/source_gap_proof/`

---

## Required CSO action

Resend or regenerate LifePRO rate extracts that include:

1. `L01 10Y` `NP` age/duration rows (under `L01 10Y LT`)
2. `L10 LP9595` `NP` and `RV` rows (as shown in client screenshots)

Once delivered, QLA will re-run rate completeness inventory and load to `QuikNps` / `QuikTvs` as applicable.

---

## Not in scope

- Converter mapping logic change (proof confirms source absence, not loader defect)
- Issue #40 CV inheritance (separate closed implementation)
- Issue #41 CV endpoint (separate closed implementation)
