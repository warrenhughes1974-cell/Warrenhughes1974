# Controlled Plan Count Recommendation

**Stage:** 4A  
**Date:** 2026-07-12  
**Status:** PROPOSED (not client-approved)

## Do Not Use a Single Unexplained Number

The project must not report only “308 plans” or “301 plans” without stating which population is meant.

## Observed Counts (Stage 4A)

| Population | Count | Meaning |
|------------|------:|---------|
| Distinct raw source plan codes (union) | **340** | Any code in tracker ∪ DBF ∪ crosswalk ∪ requirements ∪ reserve ∪ draft |
| Normalized plan codes | **340** | Uppercase/trim; no merges applied |
| Tracker | **308** | Rate-requirement tracking population |
| Plans DBF | **301** | Plan-master extract |
| Tracker ∩ DBF | **285** | Identity match both sources |
| Tracker-only | **23** | In tracker, not in DBF |
| DBF-only | **16** | In DBF, not in tracker |
| Crosswalk expanded CFIC codes | **156** | Working mapping subset (111 spreadsheet rows) |
| Reserve staging / draft Quik plans | **138** | Reserve wave successfully staged/emitted historically |
| Proposed in-scope base plans | **288** | Governance proposal from catalog/tracker classification |
| Proposed in-scope riders | **36** | Governance proposal |
| In-scope pending source | **15** | Mostly reserve-staging-only |
| Requires review | **1** | Crosswalk-only residual |
| Unresolved (pending source + requires review) | **16** | Needs classification |
| In-scope missing QLAdmin mapping | **184** | Working gap |
| In-scope missing identified rate source | **199** | No reserve staging and no CV zip family match |

## Recommended Count Usage

| Use case | Recommended count to cite | Rationale |
|----------|---------------------------|-----------|
| **Executive project reporting** | “**340 codes under reconciliation**; **285 matched** in tracker∩DBF; **308** on requirements tracker; **301** on plan master” | Transparent; avoids false precision |
| **Conversion scope (working)** | Proposed **288 base + 36 riders** subject to CIT-DEC-001/002/003/006 | Explicit scope hypothesis |
| **Plan-mapping work** | All codes with `HAS_QLADMIN_MAPPING=N` in-scope (**~184**) as backlog; crosswalk **156** as working coverage | Mapping is incomplete by design today |
| **Rate-requirement tracking** | **308** tracker plans (and catalog) | That is what the tracker measures |
| **Client review packets** | Tracker-only **23** + DBF-only **16** + sample matched set | Focus decisions |
| **QLAdmin product setup** | Distinct **QLPlan** values from approved crosswalk (not yet approved); do not use 308 | Destinations ≠ source codes |
| **Release completion** | Only plans with approved mapping + approved authority + validated rates — **0 today** | Honesty |

## Bridge: 308 → 301

```
308 tracker
− 23 tracker-only
+ 16 DBF-only
= 301 DBF
```

Residual after this arithmetic: **0** (bridge closes). Unresolved items remain **inside** the 23 and 16 lists (classification unknown), not as a hidden “other” bucket.

## Crosswalk 156

Interpreted as a **partial working mapping**, often collapsing sex/smoker variants to one QLPlan — **not** a claim that only 156 plans exist.

## Reserve 138

Interpreted as the **reserve extract/emit wave subset** (aligned with draft `emit_summary.json`), not as “only 138 plans need rates.”
