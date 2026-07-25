# Issue #109 — Planning Report

**Issue:** #109 — Issue #71 phase-1 provisional status cache is inert
**Framework stage:** Planning (G1)
**Date:** 2026-07-25
**Baseline:** `QLA_Migration/Output/` at app `v58.34`
**Result:** **NOT A DEFECT — no code change recommended.** Issue #71 is working as designed.

---

## 1. Finding

The Intake premise does not hold. Measured against the current batch, the provisional
status cache is fully populated and correctly keyed, and the phase-1 inherit is using it.

| Measure | Intake claim (v58.31) | Measured (v58.34) |
|---|---:|---:|
| Provisional-cache keys built | 5,194 | 5,083 |
| Overlap with emitted `MPOLICY` | **0** | **5,083 (100%)** |

Source: `QLA_Migration/Reports/quikmstr_phase1_inherit_mstatus.csv`, written 2026-07-25
09:35 by the v58.34 batch. Keys are the current 11-character form (`9010143726C`), matching
`quikmstr.MPOLICY` exactly.

## 2. Issue #71 is achieving its purpose

Issue #71 exists so that the Issue #49 QuikMstr active-phase override does not drag phase-1
`MPHSTAT` along with it. Phase 1 should keep the **pre-override** (provisional) status.

36 policies have a provisional status that differs from the final emitted `MSTATUS` — these
are exactly the policies Issue #49 overrode:

| Provisional | Final `MSTATUS` | Policies |
|---|---|---:|
| 54 | 22 | 35 |
| 50 | 22 | 1 |

On all 36, phase-1 `MPHSTAT` carries the **provisional** value:

| Phase-1 `MPHSTAT` equals | Policies |
|---|---:|
| provisional status (Issue #71 working) | **36** |
| final `MSTATUS` (Issue #71 defeated) | 0 |
| neither | 0 |

All 36 provisional values are outside the inherit block-list (`""`, `11`, `22`, `ACTIVE`),
so the inherit did fire on every one of them and chose correctly. If the cache were inert
these 36 rows would read 22.

## 3. Why Intake reached the opposite conclusion

Intake analysed the wrong branch. The cache key is built with a preference, not a single
expression:

```7974:7979:app.py
                                    _prov_pol = self.normalize(row_data.get("MPOLICY", ""))
                                    if not _prov_pol:
                                        _lp = self.normalize(src_row.get("POLICY_NUMBER", ""))
                                        _prov_pol = self.normalize(
                                            self._format_qladmin_mpolicy(cw_map.get(_lp, _lp))
                                        )
```

Intake quoted only the fallback and correctly observed that it produces `010143726CC` — the
retired crosswalk value with a second `C` appended. What it missed is that the fallback is
unreachable. `MPOLICY` is the first field in the `quikmstr` schema, so `row_data["MPOLICY"]`
is always populated by the time `MSTATUS` is processed, and the primary branch takes the
already-correct 11-character key.

This is a genuinely easy mistake to make from a static read — the fallback is the only line
that mentions the crosswalk, and the same crosswalk really was the root cause of #108F and
#110. The difference is that those two paths had no correct primary branch to fall back
from.

## 4. Regression check

The block has not changed since **v58.12** (`git log -L 7968,7982:app.py`) and is not in the
uncommitted v58.32–v58.34 diff. Nothing in the Issue #108 or #110 work fixed this
incidentally — it was never broken.

`_format_qladmin_mpolicy(cw_map...)` appears exactly once in the repo (plus its mirror in
`QLA_Migration/app.py`), so there is no second consumer of the stale pattern.

## 5. Latent code hygiene — deliberately not fixed

The fallback branch does encode a retired key convention and would produce a bad key if it
ever became reachable. It is left alone on purpose:

- It has zero runtime effect today, so a change delivers no data improvement.
- Touching `app.py` requires a version bump and a full batch to prove nothing moved, which
  costs a batch cycle immediately before the Omaha deadline.
- Enterprise rules call for surgical edits and minimum blast radius; editing unreachable
  code fails that test.

Recommend correcting it opportunistically the next time this function is opened for another
reason, and noting it in that release's implementation notes.

## 6. Disposition

**Close as Not a Defect.** No Dependency Gate or Risk review is required — the chain stops
here because there is no code change to gate.

Issue #71 does **not** need to be re-validated as a closed-issue regression; the evidence
above re-verifies its original assertion directly.

### Consequence for 108G

This removes the ordering dependency flagged earlier. 108G was held partly so the phase-1
inherit would be in a known-good state before anyone considered retiring it. It already is.
108G can proceed without waiting on #109.

Note that the inherit still masks Robert's check 2a, and that remains true and unaffected by
this finding: the inherit sets phase-1 `MPHSTAT` from the policy status for any terminal
status, and NFO statuses 44/45 are terminal, so phase-1 and policy status are forced into
agreement on all 400 NFO policies. Check 2a cannot fire until that force is retired. What
this report changes is only that the inherit is choosing the *correct* status when it fires.

---

## Appendix

- Intake: `Issue_109_Intake_Summary.md`
- Cache evidence: `QLA_Migration/Reports/quikmstr_phase1_inherit_mstatus.csv`
- Related: #49 (override), #71 (the fix being verified), #108F / #110 (real instances of the
  crosswalk key regression)
