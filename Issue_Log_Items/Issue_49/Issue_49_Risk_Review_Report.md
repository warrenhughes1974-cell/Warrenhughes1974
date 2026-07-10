# Issue #49 — Risk Review Report

**Issue:** #49 — QuikMstr Active Phase Status  
**Framework stage:** Stage 4 — Risk  
**Status:** **GO** — Ready for Development (await explicit Stage 5 approval)  
**Generated:** 2026-07-10  
**Baseline engine:** v57.69  
**Evidence:** `evidence/issue49_override_candidates.csv`  
**Code changes in this stage:** None (read-only simulation)

---

## Go / No-Go Recommendation

```text
GO
```

Proceed with a **surgical** post–Issue #13 override on `quikmstr.MSTATUS` only, using simulated QLAdmin display phase status (Planning Recommendation C). Fleet impact is **bounded (35 policies)**, **homogeneous (54 → 22)**, and **non-overlapping** with the Issue #13 termination population.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Rows changing |
|-------|---------|----------|--------------:|
| **`quikmstr.MSTATUS`** | PPOLC → Issue #13 composite → `ST_*` only | Same, then if display phase 1 ≥ 50 and a later phase ∈ 0–49, set `MSTATUS` to that later phase status | **35** |
| **`quikmstr.MSTATDATE`** | `CONTRACT_DATE` | Unchanged | **0** |
| **`quikridr.MPHSTAT`** | PPBEN + phase-1 inherit from `MSTATUS` | **No direct edit**; after rebatch, phase 1 will stop inheriting terminal status when master becomes 22 | Indirect on same 35 |
| All other fields | — | Unchanged | **0** |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| `quikmstr.MMODPREM` / modal factors (#36) | **No** |
| `quikmstr.MBILLDAY` (#47) | **No** |
| `quikridr.MPREM` (#26) | **No** |
| `MPOLICY` padding (#25) | **No** |
| `MNFOPT` / `MDIVOPT` (#21A) | **No** |
| `Master_Value_Translation.csv` | **No** |
| Claims / rates | **No** |
| Phase-1 inherit block list code | **No** (behavior follows new `MSTATUS` only) |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `app.py` / `QLA_Migration/app.py` ~6231–6242 | Issue #13 MSTATUS interceptor — **run before** #49 |
| Same files ~6423–6425 | `ST_` / bare translation |
| Same files ~6555–6576 | Phase-1 `MPHSTAT` inherit (unchanged code; consumes final `MSTATUS`) |
| `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv` | No change |
| `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv` | No change |
| Optional `qla_core/` helper | Pure selection functions (recommended) |
| `tools/validators/validate_issue13_mstatus.py` | Regression guard |
| New `tools/validators/validate_issue49_mstatus.py` | Stage 6 |

---

## 4. Population Analysis (simulated from current Output)

Simulation uses emitted `quikridr.MPHSTAT` ordered by `MPHASE` as the **display** phase status (equivalent to post-sync / Recommendation C for today’s batch).

| Metric | Count |
|--------|------:|
| `quikmstr` policies | 5,083 |
| Multi-phase policies with phase 1 ≥ 50 and a later phase ∈ 0–49 | **35** |
| Of those, `MSTATUS` would change | **35** |
| Transition | **54 → 22** on all 35 |
| Multi-phase with phase 1 ∈ 0–49 and a different later active (preserve) | **142** |
| Overlap with Issue #13 T+PUT source population | **0** |

### Candidate samples

| MPOLICY | Phase1 | Later first active | Current MSTATUS | Proposed |
|---------|-------:|-------------------:|----------------:|---------:|
| `018252C` | 54 | 22 | 54 | **22** |
| `018253C` | 54 | 22 | 54 | **22** |
| `018499CC` | 54 | 22 | 54 | **22** |
| `01FG8033CC` | 54 | 22 | 54 | **22** |

Full list: `evidence/issue49_override_candidates.csv`.

### Why not the 142 NFO+later-active rows?

Phase 1 statuses 41/42/44/45 are **active** under the QLAdmin manual (0–49). Rule step 3 preserves current QuikMstr behavior — **intentional non-change**.

---

## 5. Fallback Recommendation

| Scenario | Recommendation |
|----------|----------------|
| No PPBEN phases | Keep Issue #13 `MSTATUS` |
| Phase 1 blank/invalid | Keep Issue #13 `MSTATUS` (do not treat as inactive) |
| Phase 1 ≥ 50, no later 0–49 | Keep Issue #13 `MSTATUS` |
| Duplicate `BENEFIT_SEQ` | Sort seq asc, then source row order |
| Translation miss on later phase | Skip; continue scan |

---

## 6. Trace Policies ( fore Development / Validation)

| Policy | Role | Expect after #49 |
|--------|------|------------------|
| `018252C` | Override candidate | `MSTATUS=22` |
| `018253C` | Multi later actives | `MSTATUS=22` (first later active) |
| `018187C` | Phase1=45 (active), later=22 | `MSTATUS` **unchanged** (45) |
| `010380550C` | Phase1=41, later=22 | `MSTATUS` **unchanged** (41) |
| `010516211C` | Issue #13 trace (T/LP → 54) | Unchanged unless it appears in candidate CSV (it does not) |

---

## 7. Interaction Risks

| Risk | Assessment | Mitigation |
|------|------------|------------|
| Issue #13 regression | **Low** — 0 overlap with candidates; fallback is #13 | Re-run `validate_issue13_mstatus.py` |
| Phase-1 inherit after override | **Low / beneficial** — master 22 blocks inherit; phase 1 keeps PPBEN `A→22` | Observe in regression; do not edit inherit list |
| Using raw PPBEN only | **High if chosen** — would miss all 35 | **Do not**; stick to Recommendation C |
| Governance / QuikLoan using `MSTATUS` | **Low** — 35 policies move 54→22 (more “in force”) | Note for UAT; out of #49 code scope |
| Blast radius creep to NFO | **High if threshold wrong** | Hard-code ≥ 50 trigger only; assert 142 unchanged |

---

## 8. Development Blueprint (Stage 5 — do not implement in Risk)

1. Bump `APP_VERSION` in **both** `app.py` and `QLA_Migration/app.py`.
2. During `quikmstr` batch, cache PPBEN `(POLICY_NUMBER → ordered BENEFIT_SEQ, STATUS_CODE)`.
3. After Issue #13 + `ST_` translation yields provisional `MSTATUS`, compute display phase statuses (Recommendation C) and apply override.
4. Leave phase-1 inherit code unchanged.
5. Add `tools/validators/validate_issue49_mstatus.py` asserting 35 transitions and preserve samples.
6. No rulebook / translation file edits.

---

## 9. Risk Verdict

| Item | Result |
|------|--------|
| Blast radius | **35** policies, all `54→22` |
| Issue #13 conflict | **None** (0 overlap) |
| Rulebook change | **None** |
| Premium / schema risk | **None** |
| **Stage 4 decision** | **GO** |

**Ready for Stage 5 — Development** after explicit user approval to code.

---

## 10. Proposed Stage 5 — Development Prompt

```text
Perform Stage 5 — Development for Issue #49 per Issue_49_Planning_Report.md and Issue_49_Risk_Review_Report.md. Surgical only: after Issue #13 MSTATUS translation in app.py and QLA_Migration/app.py, override MSTATUS when simulated display phase 1 is ≥50 and a later phase is 0–49. Use PPBEN cache + bare-letter map + phase-1 inherit simulation. Bump APP_VERSION in both app.py files. Do not change rulebooks, MPHSTAT inherit block list, or unrelated fields. Add tools/validators/validate_issue49_mstatus.py. Stop after Development; do not claim Validation complete until Stage 6.
```

---

*End of Stage 4 Risk. No application code or version changes were made.*
