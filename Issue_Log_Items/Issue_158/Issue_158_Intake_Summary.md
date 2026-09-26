# Issue #158 — Intake Summary

**Issue:** #158 — PR rates attributed to the wrong QLAdmin plan
**Framework stage:** Intake Agent (G0)
**Status recommendation:** Intake Complete → Planning → Dependency Gate → Risk
**Generated:** 2026-08-29
**Owner:** Conversion
**Priority:** High — premium rate grids display on plans that do not own them; 18 plans that
should carry rates show "Values Not on File"

---

## Symptom (normalized)

QLAdmin `QuikGps` premium grids are attached to the wrong plan. A coverage that merely
*references* a rate segment in a non-premium slot captures that segment's premium grid, while
the coverage that actually owns the segment gets nothing and is flagged `VARGP=4`
("Values Not on File").

Confirmed against 12 LifePRO Attained Age screenshots supplied by Warren
(`docs/Rate_Validation/`). All 12 match `PAAGERAT` exactly; none is on the correct plan.

## Example segments

| Segment | Lands on today | Should be on | Policies on correct plan (total / active) |
|---|---|---|---|
| `961 ME65` | `261PUA` | `2961ME` | 1 / 0 |
| `980 END65` | `280PUA` | `280END` | 6 / 2 |
| `1576 659` | `1669SR` | `976659` | 206 / 18 |
| `1576 658` | `1658CS` | `976658` | 108 / 12 |
| `1578 FTR` | `578STR` | `778FTR` | 32 / 2 |
| `619 DT SP` | `7619PU` | `719SDT` | 10 / 1 |
| `686S 30MRG` | `7687J3` | `7686S3` | 3 / 0 |
| `L15` | `1L16GD` | `1L15GD` | 11 / 5 |
| `620 END85` | `222END` | `221END` | 13 / 8 |
| `8286 GI` | `9JPO10` | `986JPO` | 4 / 4 |
| `L10 LP95` / `L10 LP95SR` / `L10 PRE97` | all three on `1L10SO` | `1L1095` / `1L10SR` / `1L10OD` | — |
| `L17` | `1L17SP` | `10L171` + `117JPO` | 11 / 11 |

Largest business impact is **not** in the screenshots. The L10 family dominates: `L10 LP95`
(1,236 source cells, **382 policies / 259 active**) belongs on `1L1095` but sits on `1L10SO`,
and `L10 PRE97` (1,236 cells, **143 / 101**) belongs on `1L10OD`. `GL LP85` (**509 / 249**)
should also feed `170858` and `170588`, which have no grid today.

## Suspected domain

`qla_core/rate_segment_resolution.py` — `SegmentResolver` builds `segment → parent coverage`
from `PCOVRSGT` using only `SEGT_FLAG=Y`, discarding `SEQ`, and stores one parent per segment
(last row wins). `SEQ` is the rate-type slot: **1=PR, 2=CV, 12=RV, 13=NP**.

Two consequences:

1. **Wrong-slot capture** — a rider at SEQ 7 or a PUA at SEQ 10 outranks the SEQ 1 owner.
2. **Silent overwrite** — one parent per segment means a segment legitimately shared by two
   coverages at SEQ 1 emits to only one of them.

## In scope (first pass — PR only, Warren 2026-08-29)

- Make PR segment resolution read `PCOVRSGT` **SEQ 1** rows only.
- Allow one-to-many: emit a PR grid to every coverage that carries the segment at SEQ 1.
- Let `VARGP` fall out of the Issue A7 derivation from the emitted grid; do not hand-set it.
- Emit `QuikPlGp` key rows for newly-populated plans under the Issue #83 companion-gender rule.

## Out of scope (first pass)

- CV / RV / NP resolution, which share the same resolver and the same defect
  (7 / 10 / 9 multi-owner segments respectively) — follow-up issue.
- PSUBSSEG issue-date substitution — separate issue, separate root cause.
- Rate values, the Issue #138 SEQ offset, the Issue #140 slot axis, Issue #71 band collapse.
- ISWL BP path for `1658CS` / `1659CS` / `1669SR` / `1679CS`.

## Related issues

| ID | Relationship |
|----|---|
| **#138** | PR `SEQ = attained age + 1` offset — values are correct, attribution is not; preserve |
| **#140** | Attained-age slot axis (`AGE=00`, slot = attained age) — preserve |
| **#71** | Band collapse to `00` + collapse priority — preserve, not a defect |
| **#83** | Companion gender keys — newly-populated plans need `QuikPlGp` keys under this rule |
| **#106 / #42 / DV-NATIVE / PUA-CV** | Closed rate rows on adjacent tables — regression surface |
| **#107** | Held — L10 family multi-segment; `1L10SO` is a 4-way collision here |
| **#118** | Form-aware UWCLASS including L10/L14 — plans moving must keep correct UW keys |
| PSUBSSEG | Sibling issue; confirms the SEQ slot semantics but does not fix this |

## Immediate blockers at intake

None. Client confirmation of the SEQ-slot rule is desirable but Planning found a second
independent LifePRO source that already evidences it (see Planning Report).

## Artifact inventory

| Artifact | Status |
|---|---|
| LifePRO screenshots (12) | `docs/Rate_Validation/_extracted/` |
| Screenshot vs PAAGERAT comparison | `docs/Rate_Validation/_compare_pr_screenshots.py` |
| Owner / emit trace | `docs/Rate_Validation/_pr_owner_and_emit_check.py` |
| Slot-rule impact simulation | `Issue_158/_sim_slot_aware_resolution.py` + `evidence/` |
| PSUBSSEG corroboration probe | `Issue_158/_probe_at_risk_plans.py` |

## Severity / owner

- **Severity:** High — wrong premium rates displayed against real in-force policies, and
  correct plans suppressed as "Values Not on File".
- **Owner:** Conversion (surgical change to `rate_segment_resolution.py` + PR loader).
- **Not** a source-extract defect and **not** a PSUBSSEG defect.
