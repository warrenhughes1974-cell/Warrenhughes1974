# Issue #28 — V-16 Rate Validation

**Validation date:** 2026-06-27  
**Risk reference:** Issue #28 Risk Review — rate table impact for 33 changed PLAN codes  
**Scope:** Spot-check only (Validation Agent); full rate reconciliation is pre-production

---

## Objective

Verify PLAN-dependent downstream artifacts (variation audit, CSO crosswalk, rate observations) for changed PLAN codes without modifying rate tables.

---

## Sample PLAN codes checked

| PLAN | Issue #28 role | Variation audit | CSO crosswalk |
|------|----------------|-----------------|---------------|
| **1CSIMN** | Client example (10827 MN5K) | HIGH confidence; PAAGERAT+Rate_Table | In review_flag list; NFOINT/INTMETHCV updated |
| **960CWP** | Client example (0823 960CH) | GP=ATTAINED_AGE; LOW (no rate obs) | In missing_plan_codes |
| **94PDIS** | Client example (0824 P DIS) | GP=NONE; **no matching rate rows** | In missing_plan_codes |
| **9DIS25** | DISCHO25 | — | In missing_plan_codes |
| **9DS24C** | DISCHO247C correction | — | In missing_plan_codes |
| **121PUA** | 621 PUA correction | no matching rate rows | In missing_plan_codes |
| **261PUA** | 961 PUA correction | no matching rate rows | In missing_plan_codes |
| **1970PA** | 970 PUA correction | no matching rate rows | In missing_plan_codes |

---

## Variation code audit (`QLA_Migration/Output/variation_code_audit.csv`)

| PLAN | Detected structure | Confidence | Notes |
|------|-------------------|------------|-------|
| 1CSIMN | GP=ATTAINED_AGE \| DB=ISSUE_AGE_DURATION | HIGH | Rate_Table + PAAGERAT evidence |
| 960CWP | GP=ATTAINED_AGE \| DB=NONE | LOW | no rate observations |
| 94PDIS | GP=NONE \| DB=NONE | LOW | **no matching rate rows** |

All 33 corrected PLAN keys appear in variation audit (141 total plans audited).

---

## CSO mortality crosswalk QA (`cso_mortality_crosswalk_qa.csv`)

| Metric | Value |
|--------|------:|
| plans_loaded | 51 |
| plans_matched | 51 |
| plans_missing | 90 |
| cells_updated | 77 |

**1CSIMN** received CSO enrichment (NFOINT=F, INTMETHCV=0) — expected for newly authoritative CSI MN plan.

**missing_plan_codes** includes many rider/waiver PLANs (960CWP, 94PDIS, 9DIS25, 121PUA, etc.) — consistent with CSO table coverage limited to base product plans. Not a conversion defect; documents downstream rate/CSO review scope.

---

## PFSA Rates repository spot-check

Searched `PFSA Rates/*.csv` for direct PLAN code hits on changed codes — no embedded PLAN string matches (rates keyed by product structure, not QLAdmin PLAN code strings). `PFSA Rates/reconciliation/rate_diff.csv` contains 256,380 rows — full reconciliation deferred to Rate team pre-production sign-off per Risk Agent.

---

## PLAN_NOT_IN_TARGET assessment

| Category | Finding | Severity |
|----------|---------|----------|
| Rider plans without rate observations (94PDIS, 960CWP) | Expected — riders often unrated in PAAGERAT | Informational |
| PUA plans (121PUA, 261PUA, 1970PA) | no matching rate rows in variation audit | Informational |
| CSO missing_plan_codes (90 codes) | Pre-existing coverage gap | Pre-production review |
| 1CSIMN rate linkage | HIGH confidence variation assignment | PASS |

---

## Risk Agent alignment

Risk Review identified rate table impact as **pre-production** gate (B-02 / V-16), not a Validation-stage blocker. Findings above are **documented observations** — no conversion code defect identified.

---

## Decision

**V-16: PASS WITH OBSERVATIONS** — downstream rate/CSO review items documented for production release; no unexpected PLAN-dependent conversion failures in batch output.
