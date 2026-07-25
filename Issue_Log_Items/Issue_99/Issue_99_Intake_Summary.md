# Issue #99 — Intake Summary

**Issue:** #99 — ISWL QuikPlan MKTG / PRODUCT / HLOB = ISWLFE  
**Date:** 2026-07-23  
**Framework stage:** Intake complete (G0)  
**Status:** Proceed to Planning  
**Owner:** Conversion (Warren) · Client reporter: Sujitha Challa  
**Business status:** Go (client direction — set all three fields to ISWLFE)

---

## Client / business symptom (verbatim)

> Also, I observed that QUIKPLAN:PRODUCT isn’t “ISWLFE” for any of the ISWL Plans. This should be updated so QL knows to pickup these plans as ISWL.  
> This should be done in Plan Information-> “MKTG filed”. For PFSA we made both “LOB” and “MKTG” fields as “ISWLFE”, I’m not sure if LOB field is mandatory, just letting you know.

**Warren direction (2026-07-23):** Change **everything** to `ISWLFE` (MKTG + PRODUCT + LOB/HLOB).

---

## Normalized finding

QLAdmin uses a plan-level product tag (`ISWLFE`) so interest-sensitive whole life plans are recognized as ISWL. Current full `QLA_Migration/Output/quikplan.csv` for the 8 ISWL MPLANs:

| Field | Current | Expected |
|-------|---------|----------|
| MKTG | blank | `ISWLFE` |
| PRODUCT | LifePRO `PRODUCT_TYPE` (`05` / `06` / `16`) | `ISWLFE` |
| HLOB (UI “LOB”) | blank | `ISWLFE` |

Rulebook today:

- `PRODUCT` ← LifePRO `PRODUCT_TYPE`
- `MKTG` / `HLOB` ← no source (always blank)

---

## Example plans (no policy-level examples from client)

| PLAN | DESCR | PRODUCT (now) | MKTG | HLOB |
|------|-------|---------------|------|------|
| 1658C1 | INTEREST-SENSITIVE WHOLE LIFE | 06 | (blank) | (blank) |
| 1658CS | INTEREST-SENSITIVE WHOLE LIFE | 06 | (blank) | (blank) |
| 1659C2 | INTEREST-SENSITIVE WHOLE LIFE | 05 | (blank) | (blank) |
| 1659CS | INTEREST-SENSITIVE WHOLE LIFE | 05 | (blank) | (blank) |
| 1659CR | INTEREST-SENSITIVE WHOLE LIFE | 16 | (blank) | (blank) |
| 1659SR | INTEREST-SENSITIVE WHOLE LIFE | 16 | (blank) | (blank) |
| 1669SR | INTEREST-SENSITIVE WHOLE LIFE | 16 | (blank) | (blank) |
| 1679CS | INTEREST-SENSITIVE WHOLE LIFE | 06 | (blank) | (blank) |

Allowlist authority: `qla_core/cso_mortality_crosswalk.py` → `ISWL_MPLAN_ALLOWLIST` (same 8 codes used by #21D / ISWL rate work).

---

## Suspected domain

**Plan setup — `quikplan`** fields `MKTG`, `PRODUCT`, `HLOB`.

Not: rates, policy fees, claims, memo, quikridr.

---

## Related issues

| Issue | Relationship |
|-------|--------------|
| **#23 / #43** | ISWL expense / plan setup — related product family, different fields |
| **#21D** | Same ISWL MPLAN allowlist |
| **#74** | Prior quikplan field override pattern (VARDB) — similar surgical style |
| **Issue A** | Plan-setup checklist — may add A-check that ISWL plans carry `ISWLFE` |

---

## In scope / out of scope

| In scope | Out of scope |
|----------|--------------|
| Set MKTG / PRODUCT / HLOB = `ISWLFE` on 8 ISWL plans | Non-ISWL plans |
| Durable emit so next batch keeps the tag | Changing LifePRO `PRODUCT_TYPE` source |
| Validator + `Test_Validation/quikplan.csv` | ISWL rate tables, COI, expense charges |
| Confirm UI LOB = `HLOB` | PFSA annuity plan tagging (reference only) |

---

## Immediate blockers

None for Intake. Confirm in Planning that `ISWLFE` is accepted by QuikList / plan load (client used it on PFSA).

---

## Artifact inventory

| Artifact | Status |
|----------|--------|
| Sujitha email direction | Provided |
| Warren “change everything to ISWLFE” | Provided |
| Example policy numbers | Not provided (plan-level issue) |
| Current Output `quikplan.csv` | Available |
| Sync rulebook quikplan | Available |

---

## Gate G0

- [x] Issue folder created
- [x] Intake summary written
- [x] Example plans listed
- [x] Owner / priority assigned
- [x] No code or rulebook changes
