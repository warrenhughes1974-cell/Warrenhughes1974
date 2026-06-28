# Issue #21D — Dependency Checklist

**Date:** 2026-06-27  
**Converter version:** v57.35  
**Gate stage:** Dependency Gate

---

## Track A — Interest crediting rate (MDEPINT)

| # | Dependency | Status | Evidence |
|---|------------|--------|----------|
| A1 | `CSO_Mortiality_Crosswalk.csv` present in repo | ✅ SATISFIED | `plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv` |
| A2 | All 8 ISWL QL plan codes in CSO crosswalk | ✅ SATISFIED | 1658C1, 1658CS, 1659C2, 1659CR, 1659CS, 1659SR, 1669SR, 1679CS — each `nfo_interest_source = 4.50%` |
| A3 | All 8 ISWL plans in batch fleet | ✅ SATISFIED | 2,268 policies; batch MPLAN set = CSO set (no orphans) |
| A4 | Client business rule (4.50% ISWL) | ✅ SATISFIED | Intake client confirmation |
| A5 | `qla_core/cso_mortality_crosswalk.py` loader | ✅ SATISFIED | Used by quikplan NFOINT today; extensible for rate percent |
| A6 | Product catalog ISWL identification | ✅ SATISFIED | `product_catalog_crosswalk.csv` lists all 8 ISWL plans |
| A7 | quikdvdp rulebook + emit path | ✅ SATISFIED | `Sync_Rulebook_quikdvdp.csv`; `app.py` quikdvdp branch |
| A8 | MPLAN available at quikdvdp emit | ⚠️ CONDITIONAL | Batch order: **quikridr before quikdvdp**; Development must load `quikridr.csv` from output (pattern exists for quikmstr cache) |
| A9 | PPBENTYP extract for quikdvdp source | ✅ SATISFIED | `PPBENTYP_BenefitType_Extract_20260530.csv` — no PLAN column; MPLAN via quikridr only |
| A10 | Non-ISWL 4.00% preservation | ⚠️ CONDITION | CSO has numeric rates for **25 other plan codes (1,688 policies)** — enrichment **must gate on ISWL allowlist**, not blanket CSO numeric apply |
| A11 | No conflicting rate authority for ISWL | ✅ SATISFIED | CSO `4.50%` / code `A` aligns with `quikplan.NFOINT = A` |
| A12 | Client non-ISWL 4.00% confirmation | ⏳ RECOMMENDED | Not blocking Development if ISWL-scoped implementation |

**Track A checklist result:** **9/12 satisfied · 2 conditional · 1 recommended**

---

## Track B — Blank owner / insured names

| # | Dependency | Status | Evidence |
|---|------------|--------|----------|
| B1 | RNA extract in Source | ✅ SATISFIED | `RelationshipNameAddress_Extract_20260530.csv` |
| B2 | PPOLC extract | ✅ SATISFIED | `PPOLC_PolicyMaster_Extract_20260530.csv` |
| B3 | quikclnt / quikclid / quikmstr rulebooks | ✅ SATISFIED | Configs present; intake found no mapping defect |
| B4 | v57.28 MPRIMID guard | ✅ SATISFIED | 0 `MPRIMID='I'` in v57.35 batch |
| B5 | RNA fleet health (IN/PO globally) | ✅ SATISFIED | 6,387 IN rows; 6,125 PO rows |
| B6 | quikclnt referential gap quantified | ✅ SATISFIED | 14 RNA NAME_IDs missing from quikclnt (13 valid + 1 separator `-----------`) |
| B7 | NULL ADDRESS_ID root cause | ✅ SATISFIED | 12/13 missing IDs have all-null ADDRESS_ID; names present in RNA |
| B8 | B1 fix feasibility (converter-only) | ✅ SATISFIED | ~7 policies recoverable via quikclnt emit fix |
| B9 | B2 RNA re-extract for IN/PO gaps | ❌ EXTERNAL | 18 policies need IN and/or PO in RNA/quikclid |
| B10 | Converter alone resolves all 25 | ❌ NOT FEASIBLE | Max ~7–8 from B1; remainder require extract or role rows |
| B11 | Batch order quikclnt → quikclid → quikmstr | ✅ SATISFIED | Priority queue in `app.py` ~4340–4341 |
| B12 | Golden validator harness | ✅ SATISFIED | `validate_insured_owner_golden.py` exists |

**Track B checklist result:** **9/12 satisfied · 1 external · 2 not feasible without extract**

---

## Cross-issue dependency checklist

| Issue | Shared component | Impact from #21D | Status |
|-------|------------------|------------------|--------|
| **#21E** Cash Value | NFOINT, rate assumptions | Track A may affect CV path; **joint UAT required** | ⚠️ COORDINATE |
| **#21M** QUIKMEMO | None | No shared tables | ✅ NO IMPACT |
| **#21M-FU** MEMOKEY grain | None | No shared tables | ✅ NO IMPACT |
| **#21K** MUNIT precision | quikridr | No planned quikridr schema change | ✅ NO IMPACT |
| **#25** MPOLICY width | quikmstr | No MPOLICY change | ✅ NO IMPACT |
| **#26** MPREM | quikridr | No MPREM change | ✅ NO IMPACT |
| **#28** Plan mapping | MPLAN authority | MDEPINT uses MPLAN read-only; no crosswalk change | ✅ NO IMPACT |

---

## Validation dependency checklist (post-Development)

| Validator | Track | Status |
|-----------|-------|--------|
| `validate_issue21d_mdepint.py` | A | 🔲 TO CREATE |
| `validate_issue21d_blank_names.py` | B | 🔲 TO CREATE |
| `validate_insured_owner_golden.py` (extend) | B | 🔲 TO EXTEND |
| Full batch regression | Both | 🔲 REQUIRED |
| Client UAT samples | Both | 🔲 REQUIRED |

---

## Gate readiness summary

| Stream | Development ready? | Release ready? | Production ready? |
|--------|-------------------|----------------|-----------------|
| **Track A** | ✅ Yes (with conditions) | ⏳ After validation + UAT | ⏳ After client UAT |
| **Track B1** | ✅ Yes | ⏳ After validation | ⏳ Partial fix only |
| **Track B2** | ❌ Blocked on RNA | ❌ Blocked | ❌ Blocked |
| **Combined #21D close** | — | ❌ Until B2 + UAT | ❌ Until B2 + UAT |
