# Issue A / A10 — Intake Summary

**Issue ID:** A10 (sub-item of Internal Issue A)  
**Title:** QuikUwpo missing underwriting class codes used on plans  
**Framework stage:** Intake  
**Opened:** 2026-07-20  
**Reporter:** Robert (CSO UAT)  
**Owner:** Conversion  
**Track:** **Internal only** — not client-facing  
**Priority:** High — UW class cannot be selected in Plan Information dropdown without QuikUwpo rows

---

## Client symptom (verbatim)

> Also forgot to mention, QuikUwpo has only the default record. This stores any uw class used on any plan. If there is an uw code on a plan, it should be in this table. The key is on UWCODE, there should be one record per code (i.e. no dupes on UWCODE).
>
> Uw codes need to be in this table for it to be in the drop-down list when adding an uw class to a plan.

---

## Normalized symptom

`QuikUwpo` (Underwriting Class Codes) currently contains only the default row (`UWCODE=00` / NOT APPLICABLE). Distinct UW codes used on plan member/rate setup (`QuikPlUw` / rate keys) are missing from this master lookup, so they do not appear in the QLAdmin dropdown when adding a UW class to a plan.

---

## Evidence (research 2026-07-20)

| Source | Finding |
|--------|---------|
| QLAdmin Help §7.230 | `QuikUwpo` — Underwriting Class Codes; key `UWCODE` |
| Schema | `UWCODE` C(2); `UWDESCR` C(20) |
| `Q:\CSO\CSO_Test_6_30_2026\quikuwpo.dbf` | **1** row: `00` / NOT APPLICABLE |
| `Q:\CSO\CSO_Test_6_30_2026_Robert\quikuwpo.dbf` | Same — **1** row only |
| Conversion emit | **No** `QuikUwpo` writer/path exists in `qla_core` / rate emit |
| `QLA_Migration/Output/rates/QuikPlUw.csv` | Distinct codes: **`00`, `NS`, `PR`, `SM`, `ST`** |
| Inventory | `Issue_Log_Items/Issue_A/Reports/A10_quikuwpo_inventory.csv` |

Missing from CSO QuikUwpo today (used on plans): **NS, PR, SM, ST**.

---

## Suspected domain

**Primary:** Rate / product setup emit — new `QuikUwpo.csv` (and DBF when emit-dbf on)  
**Source of codes:** Distinct `UWCODE` from `QuikPlUw` (and/or distinct `UWCLASS` from rate-key tables)  
**Descriptions:** Align with existing `UWCLASS_LABEL` in `qla_core/rate_dbf_schema.py` (`00`, `NS`, `SM`, `PR`, `ST`)

---

## In scope

1. Emit `QuikUwpo` with **one row per distinct UWCODE** used on any plan in the conversion fleet  
2. Always include default `00` / NOT APPLICABLE  
3. No duplicate `UWCODE`  
4. Populate `UWDESCR` from known labels  
5. Checklist check **A10** on every conversion

## Out of scope

- Changing plan-level `QuikPlUw` membership (separate A3)  
- QuikUwcd / QuikUwmm / policy-level underwriting  
- Renaming PR→PF (WPA sample uses PF; our fleet uses **PR** — keep PR)

---

## Next

Planning → Dependency Gate (auto-chain). No code until Approved for Development.
