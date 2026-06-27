# Issue #28 — Client UAT Package

**Version:** v57.35  
**Issue:** Incorrect Plan Number Mapping  
**Prepared for:** Client product catalog / conversion UAT  
**Date:** 2026-06-27

---

## Executive summary for client

LifePRO → QLAdmin conversion **v57.35** corrects **33 product catalog PLAN codes** that were previously emitted as LifePRO passthrough values instead of the client-approved QLAdmin plan numbers from the **Policy Form Crosswalk (5/22/2026)**. A missing **DISCHO25** catalog entry was also added.

**What changed:** Only the `PLAN` field in `quikplan.csv` (33 rows) and corresponding `MPLAN` values in `quikridr.csv` (~262 rider rows). **FORM and DESCR fields are unchanged.**

**What did not change:** Policy master, client, memo, premium history, beneficiary, and claims outputs (row counts identical to v57.34).

---

## Corrected behavior (before → after)

| LifePRO Coverage ID | v57.34 (incorrect) | v57.35 (approved) | Product |
|---------------------|--------------------|--------------------|---------|
| 10827 MN5K | 10827 MN5K | **1CSIMN** | CSI Life MN $5000 |
| 0823 960CH | 0823 960CH | **960CWP** | Waiver of Premium - Child |
| 0824 P DIS | 0824 P DIS | **94PDIS** | Payor Disability Rider |

Full list of 33 mappings: `Issue_28_PLAN_Comparison_Report.md` or `evidence/v57.35_quikplan_plan_diff.csv`.

---

## Primary acceptance tests (required)

### Test 1 — CSI Minnesota product

1. Open `quikplan.csv`
2. Locate row with description *CSI Life MN $5000*
3. **Expected PLAN:** `1CSIMN` (not `10827 MN5K`)

### Test 2 — Child waiver product

1. Locate *Waiver of Premium - Child* plan row
2. **Expected PLAN:** `960CWP` (not `0823 960CH`)
3. On a policy with this rider (e.g. 010488878C), verify `quikridr.csv` MPLAN = `960CWP`

### Test 3 — Payor disability rider

1. Locate *Payor Disability Rider* plan row
2. **Expected PLAN:** `94PDIS` (not `0824 P DIS`)
3. On a policy with this rider (e.g. 010521756C), verify MPLAN = `94PDIS`

### Test 4 — DISCHO25 discount product

1. Locate *Home Office Discount - 25%-10Yr*
2. **Expected PLAN:** `9DIS25`
3. Confirm DISCHO247C remains separate at PLAN `9DS24C`

---

## Recommended spot-check scenarios

| # | Scenario | What to verify |
|---|----------|----------------|
| 5 | Spot-check 5 additional rows from the 33-mapping list | PLAN matches crosswalk xlsx |
| 6 | Policy with multiple riders (8046 JPO — 10+ rows in population) | MPLAN aligns to corrected PLAN |
| 7 | PUA rider policy (621 PUA / 961 PUA / 970 PUA) | MPLAN = 121PUA / 261PUA / 1970PA |
| 8 | DISCHO family policies | DISCHO25→9DIS25; DISCHO247C→9DS24C; DISCHO2475→9DIS24 |
| 9 | Confirm unchanged product (e.g. 0823 960OL) | PLAN still `90OLWP` — no drift |
| 10 | quikplan row count | Still 141 product rows |

---

## Business impact

| Area | Impact |
|------|--------|
| Product catalog review | **Full re-review** of 33 changed PLAN codes recommended |
| Policies affected | ~219 policies / ~239 PPBEN rows / ~262 quikridr MPLAN updates |
| Rate tables | Some corrected rider PLANs may not have rate table entries (94PDIS, 960CWP) — rate team review required before production |
| CSO / mortality assumptions | 1CSIMN and other plans may appear in CSO missing-plan list — review `cso_mortality_crosswalk_qa.csv` |
| Claims UAT | No direct impact |
| Memo tab (#21M) | No change expected |

---

## Client observations requiring awareness

1. **33 PLAN codes change** in quikplan — any client-side product references keyed on old passthrough values must be updated.
2. **quikridr MPLAN** updates automatically via P3E alignment — policies with riders will show new MPLAN values on affected phases.
3. **Rate table coverage** for some rider PLANs is incomplete — this is a known downstream item, not a conversion defect.
4. **FORM numbers unchanged** — only QLAdmin internal PLAN codes corrected.

---

## UAT acceptance criteria

| Criterion | Required |
|-----------|----------|
| 3 client examples PASS | **Mandatory** |
| 33-mapping spot sample (≥5) PASS | **Mandatory** |
| No unexpected PLAN changes beyond 33 | **Mandatory** |
| DISCHO25 / DISCHO247C separation confirmed | **Mandatory** |
| Client sign-off on re-UAT scope (B-02) | **Mandatory for production** |
| Rate team review complete | **Mandatory for production** |

---

## UAT output location

```text
QLA_Migration/Output/
  quikplan.csv
  quikridr.csv
  variation_code_audit.csv
  cso_mortality_crosswalk_qa.csv
```

Supporting evidence:

```text
Issue_Log_Items/Issue_28/evidence/
Issue_Log_Items/Issue_28/Issue_28_PLAN_Comparison_Report.md
```

---

## UAT fail actions

| Fail type | Action |
|-----------|--------|
| Client example mismatch | Escalate — do not deploy |
| Unexpected PLAN change | Rollback per `Issue_28_Rollback_Checklist.md` |
| Client rejects scope | Hold production; revert to v57.34 if required |
