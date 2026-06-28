# Release Note — v57.37 / Issue #21J

> **⚠️ SUPERSEDED — ROLLED BACK in v57.38**  
> See `Issue_21J_Rollback_Release_Note.md`. This document is retained for audit trail only.

**Version:** v57.37  
**Issue:** #21J — Modal Premium Factors (Conversion Governance Memo)

---

## Status: WITHDRAWN

This release was rolled back. Do not deploy v57.37 memo behavior.

---

## What's new

Each converted policy now receives a **QUIKMEMO conversion governance memo** documenting the QLAdmin standard plan-level modal premium factors in effect at conversion time.

Memo content includes:

- Conversion version (v57.37)
- Product plan (phase-1 MPLAN)
- Standard modal factors: Annual=100, Semi-Annual=51, Quarterly=26.5, Monthly Draft=9.25, Monthly Billing=9.25
- Disclaimer that runtime premium quotes may differ from product setup
- Operational warning to recalculate premiums if plan-level factors are changed post-conversion

---

## What did NOT change

- Premium calculations
- Rating engine / runtime Premium Quotes
- MODE_PREMIUM conversion
- QUIKPLAN modal factor defaults
- Rulebooks and crosswalks

---

## Operator note

If modal premium factors are changed after conversion, existing policy premiums will **not** automatically update. Perform premium recalculation after any modal factor changes. See `QLA_Migration/RUN_GUIDE.md`.

---

## Output impact

| Output | v57.36 | v57.37 |
|--------|--------|--------|
| quikmemo.csv rows | 4,380 | 5,083 |

Policies without LifePRO PNOTE/PENSE notes now have a conversion-only memo row. Policies with existing notes have the conversion segment prepended.

---

## Upgrade path

Run full batch migration at v57.37. No manual data migration required.
