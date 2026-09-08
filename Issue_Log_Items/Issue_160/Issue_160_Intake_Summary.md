# Issue #160 — Intake Summary

**Issue:** #160 — PUA phase stays Expired (56) instead of Surrendered (55) when base surrenders
**Framework stage:** Intake Agent (G0)
**Status recommendation:** Intake Complete → Planning → Dependency Gate → Risk
**Generated:** 2026-09-07
**Owner:** Conversion
**Priority:** Go-No Go — client-reported (Brianna) status accuracy defect on Surrendered policies with Paid Up Additions

---

## Client symptom (verbatim)

> I think it was for surrenders (55) the PUA phase should also be surrendered and not expired (56). On policies with paid up additions, we need to make sure when we have a policy with a PUA the PUA phase should also be surrendered and not expired.

## Symptom (normalized)

When the base coverage (phase 1) converts to Surrendered (`quikridr.MPHSTAT=55`), the PUA phase (phase 2+, synthetic `MPLAN` ending `PA`) on the same policy should also emit **55**, but currently keeps its own PPBEN-derived status, landing on **56 (Expired)**.

## Example policies

| Policy | Base MPHSTAT | PUA MPLAN | PUA MPHSTAT (current) | PUA MPHSTAT (desired) |
|---|---|---|---|---|
| 9010360289C | 55 | 1708PA | **56** | 55 |
| 9010367705C | 55 | 1708PA | **56** | 55 |
| 9010376522C | 55 | 1960PA | **56** | 55 |
| 9010379405C | 55 | 1960PA | **56** | 55 |
| 9010391228C | 55 | 1970PA | **56** | 55 |

Fleet scope (current `QLA_Migration/Output/quikridr.csv`): of **692** policies with base phase 1 at Surrendered (55), **71** have a PUA phase, and **100% of those 71 (71/71)** are currently stuck at 56. There is no case in the current Output where a base=55 policy's PUA already correctly shows 55.

## Suspected domain

Phase/coverage status — `quikridr.MPHSTAT` on PUA rider rows. Converter path: PPBEN `STATUS_CODE` via `Sync_Rulebook_quikridr.csv`, then `_apply_pua_rider_inheritance` in `app.py`, which only overrides PUA status when base is active (<50) or ETI/RPU (44/45) — never when base is Surrendered (55).

## In scope (first pass)

- When base phase 1 `MPHSTAT == 55` (Surrendered), force PUA phase `MPHSTAT = 55` — same override point (`_apply_pua_rider_inheritance`) and same pattern already used for Issue #108D (base 44/45 → PUA 54).
- Re-emit `quikridr` from the current PUA inheritance path (full batch or scoped remap).
- Fail-closed validator: base=55 policies with a PUA phase must show PUA=55, zero remaining at 56.
- Publish `Output/Test_Validation/quikridr.csv` on PASS.

## Out of scope (first pass — flagged, not decided)

- Generalizing to **all** terminal base statuses ≥50 (this repo's other terminal-base/PUA gaps found during Discovery: base **53** Terminated/Death → 163 PUA rows stuck at 56; base **57** Matured → 4 PUA rows stuck at 56; base **50** Suspended → 1 PUA row at 22, this is the #133 discovery case). Client asked specifically about **surrenders (55)**. Broadening scope is a separate decision — see Open Client Questions.
- Any change to base phase 1 status itself (already correct per Discovery).
- Any change to non-PUA riders (ADB, WP, term, etc.) — SD-60-11 already restricts PUA-only overrides to `_apply_pua_rider_inheritance`.
- Rate tables, PVO, premiums, MPAR (already 0 per Issue #119), MPOLICY padding.

## Related issues

| Issue | Relationship |
|---|---|
| **#60** | Direct precedent/conflict. **SD-60-12** (locked): "MPHSTAT=41 only when base phase MPHSTAT < 50; terminated-base PUA keep current status." This is the rule that currently leaves base=55 PUA untouched. A #160 fix extends/carves out an exception to this locked decision — **requires Warren's written approval**, per the Completed Issues guide conflict rule. |
| **#108D** | Closed. Precedent pattern: base 44/45 (ETI/RPU) forces PUA to a specific terminal code (54). #160 proposes the same pattern for base 55 → PUA 55. |
| **#133 (discovery notes only, never formally opened as a fix)** | Same defect class, base=50 (Death Claim Pending) instead of base=55. Confirms this is a recurring, known gap — not isolated to surrender. |
| **#119** | Closed. PUA `MPAR=0` always — untouched by #160. |

## Immediate blockers

None for Intake — no new source extract needed; PPBEN `STATUS_CODE` is already read for every PUA row via the existing rulebook, and the override point (`_apply_pua_rider_inheritance`) already exists and already has a base-status branch to extend. The only blocker is the SD-60-12 conflict, which is a Development-approval question, not a data/source blocker.

## Artifact inventory

| Have | Missing |
|---|---|
| Current `quikridr.csv` (692 base=55 policies, 71 with PUA) | — |
| `_apply_pua_rider_inheritance` override point + existing 44/45 → 54 pattern (#108D) to mirror | — |
| SD-60-12 locked scope decision text (`Issue_Log_Items/Issue_60/Issue_60_Scope_Decisions.md`) | — |
| Example/UAT policies (71 candidates, sample above) | — |

## Owner / priority

Conversion. Go-No Go. No client data request — this is emit-logic only.
