# Issue #118 — Intake Summary

**Issue:** #118 — Align QLAdmin underwriting class codes/labels to client "Underwriting Classes by Form"
**Date:** 2026-07-26
**Framework stage:** Intake (Stage 1 of 8)
**Status:** Intake → Planning → Dependency Gate
**Owner:** Warren
**Assigned:** Warren
**Priority:** Go-No Go
**Raised by:** Warren, 2026-07-26, from client request referencing docs drive spreadsheet
**Related:** Issue A A10 (QuikUwpo master), Issue #59 MUWCLASS rate-key mapping (`RIDER_UWCLASS_MAP`), CSO mortality crosswalk UW columns, rate pipeline keying

---

## Symptom (verbatim)

Client requests we change the UW classes to what is shown in the docs drive spreadsheet **Underwriting Classes by Form**. We need to change the keys, and all of the rates in the rate tables and anywhere else underwriting classes are used.

## Symptom (normalized)

Current conversion emits a fixed LifePRO-letter → QLAdmin-code map and labels:

| LifePRO | Current QLA code | Current label |
|---------|------------------|---------------|
| `0` | `00` | NOT APPLICABLE |
| `N` | `NS` | NON-SMOKER |
| `S` | `SM` | SMOKER |
| `P` | `PR` | PREFERRED |
| `B` | `ST` | STANDARD |
| `Q` | `NS` (riders) | (same as N) |

Client spreadsheet (`docs/Underwriting Classes by Form.xlsx`) defines **form-specific** allowed classes and new codes/labels:

| Client code | Client label (from sheet) | Forms (examples) |
|-------------|---------------------------|------------------|
| `ST` | Standard | Most single-class forms; also L01/L05/L07/667/658/659 with Preferred |
| `PR` | Preferred / Preferred Non-Smoker | L10 family, L01/L05/L07/667/658/659, L14 |
| `SM` | Standard Smoker | L10 LP95 / L10 OLD only |
| `BL` | Blended / Standard-Blend | L10 LP95, L10 OLD, L10 SR OLD, L10 LP95SR |
| `NT` | Standard, Non-Tobacco | L14 only |
| `PQ` | Preferred, Non-Tobacco | L14 only |

**Critical intake finding:** LifePRO letter `S` cannot keep a single global meaning. On L10 it is Smoker (`SM`); on Preferred/Standard forms it is Standard (`ST`). Likewise current `B→ST` collides with client `ST = Standard` — Blended must become `BL`.

---

## Example policies

None provided by client at open. Fleet evidence available from current Output:

| Plan (QLA) | Form (sheet) | Current QuikPlUw codes | Client target codes |
|------------|--------------|------------------------|---------------------|
| `1L1095` | L10 LP95 | PR, SM, ST | PR, SM, **BL** |
| `1L10SR` / `1L10SO` | L10 SR / OLD family | PR, SM, ST | BL-only or PR/SM/BL |
| `1L14SC` | L14 | NS only | **NT, ST, PQ, PR** |
| `5L0110` | L01 10Y LT | PR, SM | ST, PR |
| `1658C1` / `1659C2` | (ISWL — **not on sheet**) | NS, PR, SM | **unknown** |

---

## Suspected domain

**Rates + plan setup + policy/rider keys** (cross-cutting):

1. Rate factor / key tables (`UWCLASS` on every rate grid)
2. Plan member tables (`QuikPlUw`, master `QuikUwpo`)
3. Policy/rider UW key (`quikridr.MUWCLASS`)
4. Downstream consumers of the same codes (CSO MORT resolution, variation flags, validators, reinsurance)

---

## In scope (first pass)

- Replace / extend `UWCLASS_MAP`, `RIDER_UWCLASS_MAP`, `UWCLASS_LABEL`, validator domains
- Re-emit all rate tables keyed by `UWCLASS`
- Rebuild `QuikPlUw` per plan from client form membership
- Rebuild `QuikUwpo` master dropdown (Issue A A10 contract)
- Remap `quikridr.MUWCLASS` so policies still join rate keys
- Update CSO crosswalk UW-token resolution if new codes must select gender×UW MORT columns
- Issue A checklist A10 expectation update after codes change

## Out of scope (first pass)

- Changing rate **values** (factors) except re-keying the UW dimension
- Gender / band / state key redesign
- New LifePRO extracts
- ISWL product redesign (unless client adds those forms to the sheet)
- QuikPlan schema / #25 MPOLICY / #26 MPREM

---

## Artifact inventory

| Artifact | Status |
|----------|--------|
| `docs/Underwriting Classes by Form.xlsx` | **Present** (42 forms, codes ST/PR/SM/BL/NT/PQ) |
| Current `Output/rates/*` UWCLASS distribution | **Present** (00/NS/SM/PR/ST) |
| Current `Output/rates/QuikUwpo.csv` | **Present** (5 rows: 00/NS/PR/SM/ST) |
| Current `Output/quikridr.csv` MUWCLASS | **Present** |
| Explicit LifePRO letter → client code matrix by form | **Missing** (must infer or confirm) |
| L14 rate grids for ST/PQ/PR | **Missing in Rate_Table** (only `N` observed) |
| Example UAT policies | **Missing** |

---

## Immediate blockers visible at intake

1. Form-dependent mapping for LifePRO `S` (and possibly `N`/`Q`/`P` labels).
2. L14 client lists four classes; Rate_Table extract only shows `N` for coverage `L14`.
3. Global `QuikUwpo` allows **one label per UWCODE** — sheet uses `PR` as both "Preferred Non-Smoker" and "Preferred".
4. Plans not on the sheet (ISWL 1658/1659, many riders) have no client target.

---

## Owner / severity

| Item | Value |
|------|-------|
| Owner | Conversion (Warren) with Client clarification on mapping |
| Severity | Go-No Go — rate package and policy UW keys must stay aligned |
| Regression risk | High — every rate row and most quikridr rows touch UWCLASS |

---

## Gate (G0)

- [x] Issue folder created
- [x] Intake summary written
- [x] Example policies listed (fleet proxies; none client-named)
- [x] Owner and priority assigned
- [x] No code or rulebook changes made
