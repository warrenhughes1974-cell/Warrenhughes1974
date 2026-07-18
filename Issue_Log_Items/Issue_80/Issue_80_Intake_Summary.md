# Issue #80 — Intake Summary

**Issue:** #80 — CSO Valuation Setup → exact QuikPlCv / QuikPlTv (plan + rate keys)  
**Framework stage:** Intake Agent (G0)  
**Status after intake:** Planning (Pre-Risk Auto-Chain)  
**Generated:** 2026-07-17  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Conversion (primary) — CSO-authoritative valuation assumptions into plan/rate emit  
**Priority:** High — unblocks #60 Track B (base interest) and #77 OBQ-5 (QuikPlTv assumptions); client requires exact match  
**Reporter / authority:** CSO deliverable `docs/Valuation_Setup.xlsx` (2026-07-17)

---

## Client symptom (normalized)

CSO delivered a valuation setup workbook that defines, plan-by-plan, the Cash Value and Reserve assumption values that must be written into our **plan and rate files**. This is **not** Citizens rate work (`Citizens_Product_Rate_Conversion/` is out of scope).

Authority file columns (Sheet1):

| Col | Header | Target surface |
|-----|--------|----------------|
| A | LifePRO Plan | Source plan identity |
| B | QLA Plan | `PLAN` key |
| C | Description | Reference only |
| D | QuikPlCv MORT | `QuikPlCv.MORT` (also drives `QuikPlTv.MORT`) |
| E | QuikPlCv ETIMORT | `QuikPlCv.ETIMORT` |
| F | QuikPlCv NFOINT | `QuikPlCv.NFOINT` (+ `quikplan.NFOINT` via existing CSO path) |
| G | QuikPlCv INTMETHCV | `QuikPlCv.INTMETHCV` (+ `quikplan.INTMETHCV`) |
| H | QuikPlTv (all 5 fields) | Prose for the five QuikPlTv reserve fields |

**Exactness requirement (user):** emitted values must match this file — not the older `CSO_Mortiality_Crosswalk.csv` where they conflict.

---

## Example plans (from workbook)

| LifePRO Plan | QLA Plan | Notes |
|--------------|----------|-------|
| `960 PO` | `1960PO` | Directly unblocks #60 Track B / Chris interest gap |
| `658 CEN I` | `1658C1` | ISWL family; NFOINT 0.045 |
| `L10 LP95` | `1L1095` | NFOINT revised vs prior crosswalk (4.50% vs 5.00%) |
| `10827 CSI3` | `17CSI3` | NFOINT revised (4.50% vs prior 5.75%) |
| `621 END85` | `221END` | ETIMORT = `1941 CET 2.5% NLP` (not a C2 code as written) |

Example policies: none cited in this delivery. UAT should reuse #60 pilot `010310404C` (base `1960PO`) plus ISWL/term samples after Development.

---

## Suspected domain

**Rates / plan setup** — QuikPlCv, QuikPlTv, and quikplan CV assumption columns.  
Not policy conversion fields (`quikmstr` / `quikridr` premiums, status, etc.).

---

## In scope (first pass)

1. Treat `docs/Valuation_Setup.xlsx` as **CSO authority** for the listed plans.
2. Map workbook values → loadable QLAdmin codes for:
   - QuikPlCv: `MORT`, `ETIMORT`, `NFOINT`, `INTMETHCV`
   - QuikPlTv: `RSVINT`, `RSVMETH`, `INTMETHTV`, `STOREMEANS`, `CALCMIDS` (+ `MORT` from col D)
   - quikplan: `NFOINT`, `INTMETHCV` where the existing CSO apply path already runs
3. Replace / supersede conflicting values from `plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv` for overlapping plans (many NFOINT rates differ).
4. Leave blank where the workbook is blank (do not invent).
5. Validation: cell-level exact match to workbook for every in-scope PLAN/field.

## Out of scope (first pass)

- `Citizens_Product_Rate_Conversion/` and CFIC / Issue #18 Citizens FoxPro rates
- Inventing factor grids (QuikCvs / QuikTvs numeric values) — assumptions only
- Adding PA plans to `quikplan` contrary to #60 SD-60-1 (PUA `*PA` MPLAN remains synthetic) — unless CSO explicitly requires QuikPl* rows for listed PUA QLA codes (open question)
- `#70` LOANINTX Advance/Arrears list (separate CSO ask)
- QuikUint / PDINTTBL restore

---

## Related issues

| Issue | Relationship |
|-------|----------------|
| **#60 Track B** | Blocked on base-plan interest; this file supplies `1960PO` NFOINT 0.035 + QuikPlTv 3.50%/CRVM/Curtate |
| **#77 OBQ-5 / OBQ-7** | QuikPlTv assumptions were deferred; this is the CSO authority to fill them |
| **#56** | Withdrawn; do not resurrect separate PA plan file without CSO reason |
| Existing `CSO_Mortiality_Crosswalk` / `qla_core/cso_mortality_crosswalk.py` | Current partial CV path; **must be reconciled** to Valuation_Setup (not Citizens) |

---

## Artifact inventory

| Artifact | Status |
|----------|--------|
| `docs/Valuation_Setup.xlsx` | **Present** (65 plan rows) |
| Normalized extract | `Issue_80/evidence/cso_valuation_setup_as_delivered.csv` |
| Prior CSO mortality crosswalk | Present — **conflicts** with new NFOINT on many plans |
| QLAdmin QuikPlCv/Tv schema | Present in `qla_core/rate_dbf_schema.py` |
| CSO legend: rate% → 1-char NFOINT/RSVINT | **Partial** in old crosswalk only; gaps for 3.50%, 5.50%, etc. |
| CSO legend: RSVMETH / STOREMEANS / CALCMIDS codes | **Missing** |
| Screenshots / sample policies for this delivery | **None provided** |

### Workbook completeness (intake count)

| Check | Count |
|-------|------:|
| Plan rows | 65 |
| Missing QLA Plan | 4 (`622 PUA`, `675 61 PUA`, `675 AD PUA`, `991 PUA`) |
| Missing ETIMORT | 21 |
| Missing NFOINT | 22 |
| INTMETHCV = Curtate | 65 / 65 |
| QuikPlTv prose present | 65 / 65 |

---

## Immediate blockers visible at intake

*(Updated after Help lookup 2026-07-17.)*

1. **Resolved:** Interest, method, and logical codes looked up in QLAdmin Help; blank cells mean the assumption does not apply.
2. **Open:** `ETIMORT = 1941 CET 2.5% NLP` is not a Help mortality code (no 1941 CET in §6.9).
3. **Open:** Four PUA rows lack QLA Plan codes.
4. Prior crosswalk NFOINT sources conflict with this file — Valuation_Setup wins.

---

## Severity / owner

| Item | Value |
|------|-------|
| Severity | High |
| Owner | Conversion + CSO (code legends / missing QLA plans) |
| Gate path | Intake → Planning → Dependency Gate (this session); **stop before Risk** |

---

## Gate Criteria (G0)

- [x] Issue folder created under `Issue_Log_Items/Issue_80/`
- [x] Intake summary written
- [x] Example plans listed (policies: none in delivery — marked)
- [x] Owner and priority assigned
- [x] No code or rulebook changes made
