# Issue #111 — Resolution Summary

**Issue:** #111 — PUA rider plans absent from `quikplan`; `MPAR` inherited rather than resolved
**Date:** 2026-07-25
**Disposition:** **Closed — Not a Defect.** The missing plan rows are by design.
**Authority:** Warren, 2026-07-25 — "We do not create plans in QLA for PUA's so they will not have plans."
**Production conversion code touched:** none — `app.py` and `qla_core/` unchanged, no version bump

---

## 1. The premise was wrong

Intake framed this as a product-row orphan: a plan code emitted on `quikridr` with no
`quikplan` entry, which the Issue A checklist prohibits. That framing assumed PUA coverages
are supposed to have plan rows. They are not. QLAdmin does not create plans for paid-up
additions, so `1708PA` having no `quikplan` row is the intended structure, not a gap.

Of the three options Intake put forward, this selects the third — accept the data and amend
the validator. The first two (emitting PUA plans, or resolving `MPAR` after the rename) would
have introduced rows and behaviour QLAdmin does not want.

## 2. The emitted data was already correct

Measured against `QLA_Migration/Output/` at v58.34:

| Measure | Result |
|---|---:|
| Distinct `quikridr` `MPLAN` values with no `quikplan` row | 6 |
| Of those, PUA codes (`...PA`) | **6 of 6** |
| Non-PUA plan codes with no product row | **0** |
| Rows flagged by the v1.0 validator | 493 |
| Flagged rows that are PUA | **493 of 493** |
| PUA rows whose `MPAR` equals their base plan's `PAR` | **493 of 493** |
| PUA rows that disagree with the base plan | **0** |

The six codes are `1708PA` (415 rows), `1960PA` (71), `280EPA` (3), `1705PA` (2), `221EPA` (1)
and `2665PA` (1).

Two things matter here. First, there is no genuine orphan hiding behind the failure — every
unmatched code is a PUA, so amending the validator conceals nothing. Second, `MPAR` on every
PUA row already equals the participation of the base plan it inherits from, with zero
exceptions. The inheritance is correct rather than accidentally correct, which is what makes
this closable as-is rather than needing a code change.

## 3. What changed — validators only

`MPAR` on a PUA row is now compared against the policy's phase 1 base plan instead of being
looked up under a plan code that intentionally does not exist. This keeps a real assertion:
a PUA over a participating base must carry `MPAR=1`, and one over a non-par base must carry
`0`. A blanket skip would have retired the check entirely.

| File | Change |
|---|---|
| `tools/validators/validate_issue105_mpar.py` | v1.0 → **v1.1**. PUA codes resolve `PAR` through the phase 1 base plan; non-PUA codes with no product row remain an error; reports `pua_resolved` and `orphan_nonpua` counts |
| `tools/validators/validate_issue_log_accountability.py` | `#105` spot check given the same base-plan resolution (it duplicated the direct lookup inline) |

PUA detection is deliberately narrow — `len(mplan) == 6 and endswith("PA")`, matching the
`base_mplan[:4] + "PA"` synthesis in `_apply_pua_rider_inheritance`. The genuine `...PUA`
plans that do exist in `quikplan` (`121PUA`, `165PUA`, `170PUA`) end in `UA`, so they are
untouched, and the direct `quikplan` lookup is always tried first.

This is consistent with a rule the accountability harness already encoded correctly:

```439:439:tools/validators/validate_issue_log_accountability.py
    add("#56/60 plan", "IN_DATA" if "1960PA" not in plans else "GAP", "1960PA absent from quikplan (Chris)")
```

That check has been asserting the *absence* of `1960PA` from `quikplan` all along. The #105
check contradicted it.

## 4. Verification

```text
python tools/validators/validate_issue105_mpar.py
quikridr rows: 6934
MPAR value counts: {'1': 3388, '0': 3546}
rows with plan PAR=1 (expect MPAR=1): 3388
rows with plan PAR!=1 (expect MPAR=0): 3546
PUA rows resolved via phase-1 base plan (Issue #111): 493
non-PUA rows with no quikplan row (must be 0): 0
PASS
```

All 6,934 rows are now accounted for (3,388 + 3,546), with none silently excluded.

Accountability across the session:

| Stage | IN_DATA | WARN | GAP |
|---|---:|---:|---:|
| Before this issue | 36 | 13 | 11 |
| After validator v1.1 | 37 | 13 | 10 |
| After accountability spot check | **38** | 13 | **9** |

Both `#105` entries are now IN_DATA. #111 was the last accountability GAP belonging to an
open issue. The remaining nine are all the stale-key and retired-extract class tracked under
#112 — seven are the Issue #59 allowlist policies looked up under pre-Issue-#2 keys, plus #54
and #55 trace policies in the same old format. None are conversion defects.

## 5. Known related flag, deliberately not changed

The batch logs `P3E MPLAN AUTHORITY: validation=FAILED` for the same 493 rows.
`validate_emitted_mplan` in `qla_core/mplan_authority.py` counts `outside_quikplan` — every
`MPLAN` not present in `quikplan` — which encodes the same assumption the validator just shed.

Left alone on purpose:

- It is **report-only**. `passed` feeds a log line and `write_p3e_governance_outputs`; the
  `to_csv` emit happens regardless, so no output is gated or quarantined by it.
- It sits in the batch code path and is shared with `quikactg`, so changing it needs a full
  batch and regression pass to prove nothing moved.
- It was already classified a known pre-existing flag in the Issue A run log, not a new
  regression.

Recommend bundling the same PUA carve-out into 108G part two, which already requires a
release, batch and regression cycle. Until then the FAILED flag is expected and explained
here rather than being an open question.

## 6. Closure gate (G7)

| Requirement | Status |
|---|---|
| Issue validator PASS on full `QLA_Migration/Output/` | PASS — `validate_issue105_mpar.py` v1.1 |
| Accountability IN_DATA for this issue | IN_DATA — both `#105` rows |
| Affected tables published to `Output/Test_Validation/` | Not applicable — no output changed |

No conversion output was modified, so there is nothing to publish and no re-batch is required.

## Related

- `Issue_111_Intake_Summary.md` — the original three options
- `Issue_Log_Items/Issue_A/Issue_A_Conversion_Checklist.md` — the P3E note at the run log
- `Issue_Log_Items/Issue_112/Issue_112_Implementation_Notes.md` — the stale-key validator class
