# Issue #105 — Intake Summary

**Issue:** #105 — QuikRidr MPAR must be True for participating products  
**Date:** 2026-07-24  
**Framework stage:** Intake complete (G0)  
**Status:** Proceed to Planning  
**Owner:** Conversion (Warren)  
**Business status:** Go (direction clear — product participating → MPAR on)

---

## Client / business symptom (verbatim)

> Is the policy in QLAdmin participating? There is a flag in QuikRidr:MPAR that should be true if it’s participating. We need participating policies to have the MPAR field flagged flipped to True if the product is a participating one.

---

## Normalized finding

QLAdmin shows whether a coverage/policy is participating via **`quikridr.MPAR`** (`1` = participating / True, `0` = non-par).

Today’s full Output:

| Check | Result |
|-------|--------|
| `quikridr` rows | 6,934 |
| `MPAR = 1` | **0** (all rows `MPAR = 0`) |
| `quikplan` plans with `PAR = 1` | **56** (product-level participating already fixed v57.57 from LifePRO `EXHIBIT_PAR_NONPAR`) |
| Rider rows whose `MPLAN` has `quikplan.PAR = 1` but `MPAR = 0` | **2,895** (2,683 distinct policies) |

So product setup already knows which plans are participating, but the **policy/rider flag `MPAR` never turns on**.

Current emit path pulls `MPAR` from LifePRO **`PPBENTYP.PAR_TYPE`** (rulebook `PAR_TYPE → MPAR`), with cache-miss / blank → `"0"`. That is **not** product participating status. Example conflict: policy `9010143726` / plan `221END` has product `PAR=1`, but historical PPBENTYP sample shows `PAR_TYPE=N` → would keep `MPAR=0`.

---

## Example policies (from current Output — none supplied by client)

| MPOLICY | MPHASE | MPLAN | MPAR (now) | QuikPlan PAR | Expected MPAR |
|---------|--------|-------|------------|--------------|---------------|
| 9010143726C | 1 | 221END | 0 | 1 | **1** |
| 9010148272C | 1 | 221END | 0 | 1 | **1** |
| 9010148856C | 1 | 221END | 0 | 1 | **1** |
| 9010391228C | 1 | 1970JB | 0 | 0 | 0 (control) |

---

## Suspected domain

**Policy / rider — `quikridr.MPAR`**, driven by **product participating** (`quikplan.PAR` / LifePRO exhibit par-nonpar).

Not: rates, claims, memos, premium amounts.

---

## Related issues

| Issue | Relationship |
|-------|--------------|
| **v57.57 / QuikPlan PAR** | Product `PAR` from `EXHIBIT_PAR_NONPAR` (P→1, N→0) — authority #105 should align to |
| **Issue A — A8a / A9b** | Annuity + prefix-`9*` forced `PAR=0` at plan level — inheriting plan PAR keeps those non-par |
| **#38** | PPBENTYP used for dividends/deposit — different fields; do not redefine PAR_TYPE semantics for #38 |

---

## In scope / out of scope

| In scope | Out of scope |
|----------|--------------|
| Set `quikridr.MPAR = 1` when the row’s `MPLAN` is a participating product (`quikplan.PAR = 1`) | Changing `quikplan.PAR` rules |
| Keep `MPAR = 0` for non-participating products | Recalculating dividends / QuikDvdp |
| Durable emit + validator on full Output | UI-only / manual QLAdmin edits |
| Publish `Test_Validation/quikridr.csv` on PASS | Claims, rates, #25/#26 fields |

---

## Immediate blockers visible at intake

None for framing. One design assumption to lock in Planning: **product `PAR` wins over `PPBENTYP.PAR_TYPE`** (matches client wording).

---

## Artifact inventory

| Provided | Missing |
|----------|---------|
| Symptom + target field (`QuikRidr.MPAR`) | Named client example policies / screenshots |
| Measurable before-state in current Output | Explicit “riders too vs base only” (default: all phases by MPLAN) |

---

## Severity / owner

| Item | Value |
|------|-------|
| Severity | Medium-High — participating flag wrong fleet-wide for par products |
| Owner | Conversion |
| Priority | Go |
| Recommended tracking status | **Intake → Planning** (Pre-Dev chain) |
