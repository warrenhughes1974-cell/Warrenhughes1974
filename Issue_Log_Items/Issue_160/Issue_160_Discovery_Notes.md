# Issue #160 — Discovery Notes (Search & Discuss)

**Issue:** #160 — PUA phase stays Expired (56) instead of Surrendered (55) when base surrenders
**Date:** 2026-09-07
**Framework stage:** Stage 0 Discovery (G-D)
**Code:** None
**Reported by:** Brianna (via Warren)

---

## Client ask (verbatim + normalized)

> I think it was for surrenders (55) the PUA phase should also be surrendered and not expired (56). On policies with paid up additions, we need to make sure when we have a policy with a PUA the PUA phase should also be surrendered and not expired.

**Normalized:** When the base coverage (phase 1) converts to Surrendered (`quikridr.MPHSTAT=55`), the PUA phase (phase 2+, `MPLAN` ending `PA`) on the same policy should also emit **55**, but currently keeps its own PPBEN-derived status, which lands on **56 (Expired)**.

---

## Source findings — current `QLA_Migration/Output/quikridr.csv`

Query: join phase 1 (`MPHASE=1`) per `MPOLICY` against every other phase whose `MPLAN` ends in `PA` (PUA convention).

| Metric | Count |
|---|---:|
| Policies with base phase `MPHSTAT=55` (Surrendered) | 692 |
| Of those, policies where a PUA phase is `MPHSTAT=56` (Expired) | **71** |
| Affected PUA phase rows | 71 (one PUA phase per affected policy) |

Sample affected policies (base=55, PUA=56):

`9010360289C` (PUA `1708PA`), `9010360290C` (`1708PA`), `9010367705C` (`1708PA`), `9010373918C` (`1708PA`), `9010376522C` (`1960PA`), `9010376529C` (`1708PA`), `9010377918C` (`1708PA`), `9010379405C` (`1960PA`), `9010381745C` (`1708PA`), `9010385636C` (`1960PA`), `9010389802C` (`1960PA`), `9010391228C` (`1970PA`) — 59 more in the full query result set.

---

## Current conversion path

| Layer | Path | Role |
|---|---|---|
| Rulebook | `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv` | Maps PPBEN `STATUS_CODE` → `MPHSTAT` (no `STATUS_REASON`) |
| Translation | `QLA_Migration/Mapping/Master_Value_Translation.csv` (lines ~101–124) | `ST_T_SR` → **55**, `ST_T_EX` → **56** |
| PUA inheritance | `QLA_Migration/app.py` `_apply_pua_rider_inheritance` (~lines 3608–3644) | Only override point for PUA `MPHSTAT` relative to base |

```3630:3637:C:\Users\warren\Documents\GitHub\Warrenhughes1974\QLA_Migration\app.py
base_status = self._quikridr_status_code_int(entry.get("MPHSTAT", ""))
if base_status in (44, 45):
    # Issue #108D: base on ETI/RPU terminates every other coverage (spec 54).
    row_data["MPHSTAT"] = "54"
elif base_status < 50:
    row_data["MPHSTAT"] = "41"
```

- Base **44/45** (ETI/RPU) → PUA forced to **54** (#108D).
- Base **< 50** (active) → PUA forced to **41** (Paid Up, #60 / SD-60-12).
- Base **≥ 50 and not 44/45** (includes **55**, **50**, **53**) → **no override** — PUA keeps its own PPBEN-mapped status, which is frequently **56**.

That third bucket is the direct cause of this defect.

---

## Current vs desired

| | Current | Desired (client) |
|---|---|---|
| Base phase 1 `MPHSTAT` | 55 (Surrendered) | 55 |
| PUA phase `MPHSTAT` | 56 (Expired) | 55 |

---

## Related issues (Closed-row conflict check)

| Issue | Relationship |
|---|---|
| **#60** | Directly relevant. Scope decision **SD-60-12** (`Issue_Log_Items/Issue_60/Issue_60_Scope_Decisions.md` line 22): *"MPHSTAT=41 only when base phase MPHSTAT < 50; terminated-base PUA keep current status."* This is the locked rule that leaves base=55 PUA untouched. **A fix for #160 would need to extend or amend this decision** — flagged per the Completed Issues guide conflict rule; do not implement without Warren's written OK. |
| **#133 (discovery notes)** | Same defect class, different status code: base=50 (Death Claim Pending) with PUA staying Active instead of inheriting 50. Discovery-only, never formally fixed. Confirms this is a known, recurring gap in PUA inheritance for terminal base statuses ≥50, not isolated to surrender. |
| **#108D** | Closed. Established the pattern of forcing PUA to a specific terminal code (54) when base is ETI/RPU (44/45) — precedent for doing the same for base=55 → PUA=55. |
| **#108 / #108G** | Governance: terminated policy should not carry an in-force coverage. Does not flag this case because 56 is itself terminal (≥50), so existing DG-QUIKMSTR-027 checks pass silently. |

**No existing issue is tracked for base=55 → PUA=55 propagation.** #160 is a new, distinct issue from #133 (different status code, not a duplicate).

---

## Suspected target

| Layer | Table / field | Desired |
|---|---|---|
| Phase | `quikridr.MPHSTAT` on PUA rows (`MPLAN` ending `PA`) | **55** when base phase is Surrendered (55) |

UI: Policy coverage / phase status tab.

---

## Proposed work list (Planning will refine — no code yet)

1. Extend `_apply_pua_rider_inheritance` (or add a parallel rule) so that when base `MPHSTAT == 55`, PUA `MPHSTAT` is forced to **55** — mirroring the #108D pattern (base 44/45 → PUA 54).
2. Decide scope: only base=55, or generalize to "PUA inherits any terminal base status ≥50" (which would also resolve #133's status-50 case in one pass). Needs Warren decision — broader scope touches more Closed-row precedent.
3. Confirm with Warren whether this amends SD-60-12 directly or is layered on top as a narrower carve-out (like #108D was for ETI/RPU).
4. Full-batch re-emit `quikridr.csv`; re-run the base=55/PUA=56 query as the validator baseline (currently 71 affected policies).
5. Build fail-closed validator + register in `SMOKE_JOBS` before Closure (per `.cursor/rules/closed-issue-smoke-test.mdc`).

---

## Open questions / defaults locked at Discovery

1. Scope: base=55 only, or all terminal base codes ≥50 (55, 50, 53) generalized into one inheritance rule? Affects whether this also closes out #133.
2. Does this require formally reopening #60 / amending SD-60-12, or is it a standalone new rule referencing #60 as precedent?
3. Any exceptions — e.g., does a PUA that lapsed independently *before* the base surrendered still need to show 55, or should its own earlier terminal status stand? (Not observed in the 71-policy sample, but worth confirming with Warren/Brianna.)

---

## Stop

Discovery complete. Awaiting **"Proceed to Intake"**.
