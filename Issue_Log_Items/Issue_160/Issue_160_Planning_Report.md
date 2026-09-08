# Issue #160 — Planning Report

**Issue:** #160 — PUA phase stays Expired (56) instead of Surrendered (55) when base surrenders
**Framework stage:** Planning Agent (G1)
**Status:** Planning complete
**Generated:** 2026-09-07
**Agent/script:** read-only counts against current `QLA_Migration/Output/quikridr.csv`

**Status note:** Planning analysis only — no production code changes.

---

## 1. Executive Finding

`_apply_pua_rider_inheritance` in `QLA_Migration/app.py` (and root `app.py`) only overrides a PUA rider's `MPHSTAT` in two cases: base phase 1 is ETI/RPU (44/45 → PUA forced to 54, Issue #108D) or base is active (<50 → PUA forced to 41, Issue #60 / SD-60-3). For every other base status — including **55 (Surrendered)** — the branch falls through and the PUA row keeps whatever `MPHSTAT` its own PPBEN `STATUS_CODE` mapped to earlier in the same row build. On a surrendered contract, LifePRO's benefit-level status commonly comes through as terminated/expired, so the PUA lands on **56**.

This is a **locked, intentional gap**, not an accidental regression: **SD-60-12** in `Issue_Log_Items/Issue_60/Issue_60_Scope_Decisions.md` states *"MPHSTAT=41 only when base phase MPHSTAT < 50; terminated-base PUA keep current status."* Direction: add a third branch mirroring the existing #108D pattern — `elif base_status == 55: row_data["MPHSTAT"] = "55"` — inside the same function, using the base phase cache that is already populated correctly (the phase-1 terminal-status sync at ~line 9598 runs and caches the terminal MPHSTAT into `base_phase_cache` **before** the PUA branch executes, so `entry.get("MPHSTAT")` is reliably 55 when the base is surrendered). Ready for Dependency Gate, pending Warren's sign-off on the SD-60-12 conflict.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|---|---|---|---:|
| PPBEN | `STATUS_CODE` (benefit level) via `Sync_Rulebook_quikridr.csv` | Used at batch time (gitignored extract; rulebook on file) | 6,956 current `quikridr` rows |
| PPOLC | `CONTRACT_CODE` / `CONTRACT_REASON` (policy level, drives base phase 1 via terminal sync) | Same | — |

### Available source fields

| Field | Column / source | Notes |
|---|---|---|
| Policy number | PPBEN `POLICY_NUMBER` | #2 / #25: source + C, right-justified 11 |
| Benefit seq | `BENEFIT_SEQ` → `MPHASE` | Phase 1 is the base coverage |
| Benefit status | PPBEN `STATUS_CODE` | Rulebook-mapped per-row status before PUA override runs |
| Policy contract status | PPOLC `CONTRACT_CODE`/`CONTRACT_REASON` → `ST_T_SR` = 55 | Drives base phase 1 terminal sync (`quikmstr.MSTATUS` → phase-1 `MPHSTAT`) |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source |
|---|---|---:|---:|---|
| quikridr | MPHSTAT | C | 2 | schema_constants / Help phase status |
| quikridr | MPLAN | C | 6 | synthetic `base[:4]+"PA"` for PUA rows |

**Repo references** (population paths only):

| Location | Role |
|---|---|
| `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv` | `STATUS_CODE → MPHSTAT` base mapping (no STATUS_REASON) |
| `QLA_Migration/Mapping/Master_Value_Translation.csv` (~lines 101–124) | `ST_T_SR` → 55, `ST_T_EX` → 56 |
| `app.py` / `QLA_Migration/app.py` `_apply_pua_rider_inheritance` (~3608–3644) | The only PUA override point — missing base=55 branch |
| `app.py` `_cache_quikridr_base_phase` (~3595–3606) | Caches phase-1 fields (incl. terminal MPHSTAT) for PUA lookup |
| `app.py` "BASE PHASE TERMINAL STATUS SYNCHRONIZATION" block (~9598–9652) | Confirms phase-1 MPHSTAT is already terminal (55) **before** it is cached for PUA use |
| `app.py` PUA deferral (~9758–9765, 9827–9838) | PUA rows are queued (`pua_pending_rows`) and processed **after** the full quikridr pass, so `base_phase_cache` is guaranteed populated by the time `_apply_pua_rider_inheritance` runs |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|---|---|---|---|---|
| PPOLC (via base phase 1) | CONTRACT_CODE/REASON → base MPHSTAT=55 | quikridr.MPHSTAT (PUA row) | New branch in `_apply_pua_rider_inheritance`: `elif base_status == 55: MPHSTAT = "55"` | **Yes** |
| PPBEN | STATUS_CODE (PUA row's own value) | quikridr.MPHSTAT (PUA row) | Overridden when base=55 (currently pass-through) | **Yes**, only for base=55 case |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|---|---|---|
| quikridr.MPAR (PUA) | 0 always (#119) | **No** |
| quikridr.MEFFDATE/MAGE/MPAYUP/MLASTANN (PUA) | Base phase 1 inheritance (#60 SD-60-4…6) | **No** |
| Base phase 1 MPHSTAT | Already correct (55) | **No** |
| Non-PUA rider MPHSTAT (ADB, WP, term, etc.) | Untouched — SD-60-11 restricts overrides to PUA only | **No** |
| PUA MPHSTAT when base <50 (→41) or 44/45 (→54) | #60 / #108D | **No** — new branch only adds base=55 case |
| PUA MPHSTAT when base = 50, 53, 57 (other terminal codes) | Currently unchanged (its own PPBEN status) | **No — explicitly out of scope for this pass, see Open Questions** |

---

## 5. Open Client Questions

1. **Scope: 55 only, or all terminal base codes ≥50?** Current Output shows this same gap on base **53** (Terminated/Death, 163 PUA rows stuck at 56) and base **57** (Matured, 4 PUA rows stuck at 56), plus the #133 discovery case on base **50** (1 PUA row currently at 22/Active). Client (Brianna) asked specifically about **surrenders (55)**. Default locked at Discovery/Intake: **fix 55 only** in this pass; flag 53/57/50 as a related, larger follow-on decision for Warren (would also close out #133 if bundled in later).
2. **Does this amend SD-60-12 directly, or layer a narrow carve-out on top (like #108D did for ETI/RPU)?** Recommend the #108D pattern: keep SD-60-12's text for the general terminated-base rule, add a new scope decision (SD-60-13, or a new #160-owned decision) specifically for base=55 → PUA=55.
3. Is there any case where a PUA lapsed **independently** before the base surrendered and should keep its own earlier terminal status rather than following the base to 55? Not observed in the current 71-policy sample (all 71 are cleanly 56→55 candidates with no earlier independent terminal event visible in Output), but worth a explicit confirm from Brianna/Warren before Development.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|---|---|
| Override condition | `base_status == 55` (int-parsed from cached base phase MPHSTAT) |
| Override value | `"55"` (string, matches existing `"41"`/`"54"` string assignment style) |
| Placement | New `elif` branch in `_apply_pua_rider_inheritance`, directly after the existing `elif base_status < 50` branch, before the fallback (no branch) case |
| Scope guard | Only fires inside the existing `_is_paid_up_addition_product` gate — no change to non-PUA riders |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` → QLA via existing converter (#2). Not touched by this fix.
2. No padding/crosswalk change.
3. Validator keys are the 71 current base=55/PUA=56 policies (full list available from the query in Discovery notes).

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|---|---:|---|
| Total quikridr rows | 6,956 | current Output |
| Total PUA rows (any base status) | 494 | `MPLAN` ends `PA` |
| Base phase 1 MPHSTAT=55 policies | 692 | current Output |
| Of those, policies with a PUA phase | 71 | current Output |
| Of those 71, PUA already correctly at 55 | **0** | current Output — 100% currently wrong |
| Expected MPHSTAT deltas (this pass, base=55 only) | **71** | 71 PUA rows 56→55 |
| Rows unchanged | 6,885 | everything else |

### Related (out-of-scope) population, for context on the broader gap

| Base MPHSTAT | Meaning | PUA rows affected | In scope this pass? |
|---|---|---:|---|
| 55 | Surrendered | 71 (all →56) | **Yes** |
| 53 | Terminated/Death | 163 (all →56) | No — flagged for Warren |
| 57 | Matured | 4 (all →56) | No — flagged for Warren |
| 50 | Suspended (Death Claim Pending, #133) | 1 (→22/Active) | No — separate issue #133 |

---

## 10. Sample Trace (5 policies)

| Policy (QLA) | Plan | Base MPHSTAT | PUA MPLAN | Before | After (proposed) | Status |
|---|---|---|---|---|---|---|
| 9010360289C | base+PUA | 55 | 1708PA | 56 | **55** | Fix |
| 9010367705C | base+PUA | 55 | 1708PA | 56 | **55** | Fix |
| 9010376522C | base+PUA | 55 | 1960PA | 56 | **55** | Fix |
| 9010379405C | base+PUA | 55 | 1960PA | 56 | **55** | Fix |
| 9010391228C | base+PUA | 55 | 1970PA | 56 | **55** | Fix |

Regression control (must NOT change): any base<50 PUA (→41, #60) and any base 44/45 PUA (→54, #108D) sample.

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|---|---|---|
| Conflicts with locked SD-60-12 | High | Explicit Warren approval required before Development; document as a carve-out, not a repeal |
| Scope creep to base 53/57/50 without approval | Med | Keep this pass strictly `base_status == 55`; separate issue/decision for the rest |
| A PUA that independently lapsed/expired *before* the base surrendered gets incorrectly overwritten to 55 | Low | Not observed in current 71-row sample; confirm with Brianna; validator should spot-check a few for plausibility |
| Full batch vs surgical remap | Low | Either valid; full batch preferred so `app.py` is the path of record |

---

## 12. Dependency Gate Preview

| Check | Met? |
|---|---|
| Source field present | Yes — rulebook + base phase cache already exist |
| Field definitions confirmed | Yes |
| Client scope clear | Yes — Brianna/Warren opened #160 specifically for surrenders (55) |
| Example policies available | Yes — 71 candidates, sample of 5 above |

---

## 13. Recommended Risk Agent Prompt

```
Risk Agent — Issue #160: PUA Surrendered vs Expired (55/56)
Read Planning report. Quantify PUA MPHSTAT deltas (base=55 -> PUA 56->55, 71 rows).
Confirm base<50 (->41) and base 44/45 (->54) PUA rows unchanged. Confirm SD-60-12
conflict is called out for Development approval. No code.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. In **both** `app.py` and `QLA_Migration/app.py`, in `_apply_pua_rider_inheritance`, add:
   ```python
   elif base_status == 55:
       # Issue #160: base Surrendered — PUA follows base to Surrendered, not its own PPBEN-mapped Expired.
       row_data["MPHSTAT"] = "55"
   ```
   placed after the existing `elif base_status < 50: row_data["MPHSTAT"] = "41"` branch.
2. Do **not** change the 44/45 → 54 branch (#108D), the <50 → 41 branch (#60/SD-60-3), or any other rider/base logic.
3. Do **not** extend to base 53/57/50 without a separate, explicit Warren decision.
4. Bump `APP_VERSION` in **both** files (per AGENTS.md requirement).
5. Re-emit `quikridr` (full policy batch, or scoped remap through the same `_apply_pua_rider_inheritance` path).
6. Validator: `tools/validators/validate_issue160_pua_surrender_status.py` (fail-closed) — all base=55 policies with a PUA phase must show PUA MPHSTAT=55, zero remaining at 56; base<50 and base 44/45 PUA populations unchanged in count.
7. Publish `Output/Test_Validation/quikridr.csv` on PASS.

---

## Appendix

- Related: #60 (SD-60-12 conflict — needs Warren approval), #108D (precedent pattern), #133 (same class, different status code, not bundled)
- Reference: `Issue_Log_Items/Issue_160/Issue_160_Discovery_Notes.md`
