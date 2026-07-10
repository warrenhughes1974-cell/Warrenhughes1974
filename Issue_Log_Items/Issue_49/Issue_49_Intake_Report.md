# Issue #49 — Intake Report

**Issue:** #49 — QuikMstr Active Phase Status  
**Date:** 2026-07-10  
**Framework stage:** Stage 1 — Intake (updated after business-rule clarification)  
**Status:** Active · **Current Decision:** No-Go  
**Client Contact:** Eric · **QLAdmin Owner:** Warren  
**Engine inspected:** `app.py` / `QLA_Migration/app.py` **v57.69**  
**Code changes:** None (intake is read-only)

---

### Issue Summary

When the first phase on a policy is inactive and another phase on the same policy is active, `quikmstr.MSTATUS` must reflect the status of the **first active phase**, not the inactive first phase.

**QLAdmin manual authority (confirmed):**

| Status range | Classification |
|--------------|----------------|
| **0 through 49** | **Active** |
| **50 and above** | **Inactive** |

The original issue description had the threshold direction reversed. The corrected requirement is:

```text
When the first phase on a policy is inactive, with a status number of 50 or greater,
and another phase on the same policy is active, with a status number from 0 through 49,
the status written to QuikMstr must match the status of the first active phase on the policy.
```

**Intended outcome (analysis basis only — not implemented):**

1. Review phases in established phase order.
2. If the first phase status is **0–49 (active)**, retain current QuikMstr status behavior.
3. If the first phase status is **50 or greater (inactive)**, search later phases in order.
4. Select the status from the first later phase that is **active (0–49)**.
5. Write that status to `QuikMstr`.
6. If no active phase exists, preserve existing QuikMstr / Issue #13 PPOLC fallback.

**Confirmed today:** `quikmstr.MSTATUS` is derived from **PPOLC policy-master fields**, not from phase/`quikridr` status. Phase status is a separate path (`PPBEN` → `quikridr.MPHSTAT`), with a one-way sync that can push terminal `MSTATUS` onto phase 1.

---

### Current QuikMstr Status Flow

**Confirmed**

| Step | Location | Behavior |
|------|----------|----------|
| Source table | `PPOLC` (`PPOLC_PolicyMaster_Extract_*.csv`) | One row per policy |
| Rulebook map | `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv` | `CONTRACT_CODE` → `MSTATUS` |
| Composite interceptor | `QLA_Migration/app.py` ~6231–6242 (mirrored in root `app.py`) | Builds composite key before translation |
| Translation | `QLA_Migration/Mapping/Master_Value_Translation.csv` (`ST_*`) | Composite → numeric QLAdmin code |
| Output field | `quikmstr.MSTATUS` | Policy-level status only |

**Interceptor logic (Issue #13, v57.48) — confirmed:**

```text
if CONTRACT_CODE == 'T':
    key = CONTRACT_CODE + '_' + CONTRACT_REASON   # e.g. T_LP
else if PAID_UP_TYPE in {PU, RU, ET, LE, LP, SP}:
    key = PUT_ + PAID_UP_TYPE                     # e.g. PUT_RU
else:
    key = CONTRACT_CODE + '_' + CONTRACT_REASON   # e.g. A_
→ translate via ST_{key}  (prefix applied only when target field is MSTATUS)
```

**Examples of `ST_` results (confirmed from translation file):**

| Key | `MSTATUS` | Label (from status analysis) | Manual range |
|-----|-----------|------------------------------|--------------|
| `ST_A_` | 22 | Active | Active (0–49) |
| `ST_I_` / `ST_I_PND` | 10 | Named “Inactive” in analysis labels | **Active range (0–49)** per QLAdmin manual |
| `ST_I_INP` | 12 | Inactive Pending (name) | **Active range (0–49)** per QLAdmin manual |
| `ST_PUT_RU` | 45 | Reduced Paid Up | Active (0–49) |
| `ST_PUT_LP` | 54 | Lapsed | Inactive (≥ 50) |
| `ST_T_LP` | 54 | Lapsed | Inactive (≥ 50) |
| `ST_T_DC` | 53 | Terminated/Death | Inactive (≥ 50) |

Note: descriptive names in `status_analysis_runner.py` (e.g. code 10 = “Inactive”) are **not** the Issue #49 active/inactive test. The **QLAdmin manual ranges 0–49 / 50+** are authoritative for this issue.

**Confirmed — not used for `quikmstr.MSTATUS` today:**

- `PPBEN.STATUS_CODE` / `STATUS_REASON`
- `quikridr.MPHSTAT` / `MPHASE`
- Any “first active phase” scan

**Downstream coupling (confirmed):** After `quikmstr` is written, `quikridr` phase-1 rows may **inherit** non-active `MSTATUS` into `MPHSTAT` (`app.py` ~6555–6576). Direction is **master → phase 1**, not phase → master. The inherit block list is `{11, 22, ACTIVE}` — **not** the manual 0–49 active range.

---

### Source Data and Phase Ordering

#### Policy master (QuikMstr status authority today)

| Item | Value |
|------|-------|
| LifePRO table | `PPOLC` |
| Resolver | `qla_core/lifepro_source_resolver.py` → `quikmstr` |
| Policy key | `POLICY_NUMBER` → crosswalk → `MPOLICY` |
| Status fields | `CONTRACT_CODE`, `CONTRACT_REASON`, `PAID_UP_TYPE` |
| Grain | 1 row per policy (fleet: 5,084 source / 5,083 converted) |

#### Phase / benefit rows (phase status authority)

| Item | Value |
|------|-------|
| LifePRO table | `PPBEN` |
| Resolver | `lifepro_source_resolver.py` → `quikridr` |
| Policy key | `POLICY_NUMBER` → `MPOLICY` |
| Phase order field | `BENEFIT_SEQ` → `MPHASE` (`Sync_Rulebook_quikridr.csv`) |
| Phase status field | `STATUS_CODE` → `MPHSTAT` |
| Status reason | `STATUS_REASON` present on source; **not** used in a composite interceptor for `MPHSTAT` |
| “First phase” in conversion | `MPHASE == 1` (base coverage; `AGENTS.md`: MPHASE 1 = base) |

**How “first phase” is determined today (confirmed):**

- Rulebook maps `BENEFIT_SEQ` → `MPHASE` with note “Phase sequence”.
- Engine treats phase `"1"` as base for several features (terminal status sync, UL `MCV0`, modal-factor base phase, etc.).
- There is **no** separate sort/search for “first active phase” when writing `MSTATUS`.

**`MPHSTAT` translation (confirmed):**

- Unlike `MSTATUS`, `MPHSTAT` does **not** get the `ST_` prefix in the translation branch (`app.py` ~6423–6425).
- Bare letter keys are used: `A→22`, `T→56`, `P→41`, `S→55`, `D→53`, `L→54`, `W→32` (`Master_Value_Translation.csv`).
- Phase-1 `MPHSTAT` may then be overwritten by the terminal-status sync from `quikmstr.MSTATUS` when that status is not in `{"", "11", "22", "ACTIVE"}`.

**Batch order note (confirmed):** Full batch builds tables from `TABLE_SCHEMAS` with `quikclnt`/`quikclid` first; `quikmstr` is converted before `quikridr` in practice so the phase-1 sync can read emitted `quikmstr.csv`.

---

### Current Active/Inactive Interpretation

#### QLAdmin manual (authoritative for Issue #49)

| Range | Meaning for this issue |
|-------|------------------------|
| 0–49 | Active |
| ≥ 50 | Inactive |

#### Project descriptive labels (informational only)

From `plan_analysis/status_analysis/status_analysis_runner.py` (names only; **not** the Issue #49 range test):

| Code | Description label |
|------|-------------------|
| 10 | Inactive (name) — still in manual **active** range 0–49 |
| 12 | Inactive Pending (name) — still in manual **active** range 0–49 |
| 22 | Active |
| 32 | Waiver |
| 41 / 42 / 44 / 45 | Paid Up / Special Active / ETI / RPU |
| 50+ | Suspended / Death / Lapsed / Surrendered / Expired / Matured / CV |

Governance valid set: `data_governance/constants/valid_codes.py` → `POLICY_STATUS_CODES`.

#### Does a `≥ 50` inactive / first-active-phase rule already exist?

**Confirmed: No.**

- No converter logic selects `MSTATUS` from the first active phase when phase 1 is inactive (≥ 50).
- The only numeric “active vs terminal” gate found for status sync is the hard-coded block list on phase-1 inherit: skip overwrite when `MSTATUS` ∈ `{11, 22, ACTIVE}` (`app.py` ~6574–6576). That is **not** the QLAdmin manual 0–49 / 50+ rule.
- Issue #13 changed termination vs NFO precedence on **PPOLC fields**, not phase scanning.

#### Threshold clarification (resolved)

| Item | Disposition |
|------|-------------|
| Original issue text (“inactive &lt; 50”) | **Superseded** — threshold was reversed |
| Corrected rule | Inactive = **≥ 50**; Active = **0–49** |
| Authority | **QLAdmin manual** |

#### Fleet evidence (read-only, current Output)

| Observation | Result |
|-------------|--------|
| `quikmstr.MSTATUS` vs phase-1 `MPHSTAT` mismatches | **0** (phase 1 mirrors master after sync) |
| `MPHSTAT` / `MSTATUS` values 10 or 12 in current output | **None** |
| LifePRO `PPBEN.STATUS_CODE = I` | **0 rows** |
| `PPBEN` seq1 ≠ `A` with a later seq `A` | **0 policies** |
| Output: phase1 ≥ 50 and a later phase in 0–49 (e.g. 22) | **35** policies — **in-scope candidate population** under corrected rule |
| Output: phase1 in 0–49 (≠ later), later phase = 22 | **142** policies (mostly 45/41/42/44 + active rider/PUA) — **out of override scope** (first phase already active per manual) |

**Confirmed cause of many “phase1 non-22 / later 22” output rows:**  
PPBEN benefits are often both `STATUS_CODE=A`, while PPOLC `PAID_UP_TYPE` drives `MSTATUS` to NFO/terminal codes (e.g. `RU→45`, `LP→54`). Phase 1 then **inherits** that `MSTATUS`; later phases keep bare `A→22`. Example:

| Policy | PPOLC | PPBEN seq1/2 | Emitted MSTATUS / MPHSTAT | Issue #49 override? |
|--------|-------|--------------|---------------------------|---------------------|
| `018187C` | A + RU | A / A | 45 / phase1=45, phase2=22 | **No** (45 is active 0–49) |
| `018252C` | A + LP | A / A | 54 / phase1=54, phase2=22 | **Yes candidate** (54 inactive; later 22 active) |
| `010380550C` | A + PU | A / A | 41 / phase1=41, phase2=22 | **No** (41 is active 0–49) |

So the UI can show an inactive (≥ 50) first phase beside an active (0–49) later phase even when LifePRO benefit letter statuses are both `A`, because phase 1 inherits policy-master `MSTATUS`.

---

### Existing Reusable Patterns

| Pattern | Location | Relevance |
|---------|----------|-----------|
| **Base phase terminal status sync** | `app.py` ~6555–6576 | Closest status/phase coupling — but **reverse** of Issue #49 (copies `MSTATUS` → phase-1 `MPHSTAT`) |
| **MSTATUS composite interceptor** | `app.py` ~6231–6242 | Established surgical hook for `quikmstr.MSTATUS` (Issue #13) |
| **Issue #13 validator** | `tools/validators/validate_issue13_mstatus.py` | Pattern for status regression checks |
| **Status analysis mirror** | `plan_analysis/status_analysis/status_analysis_runner.py` → `derive_mstatus_from_source_fields` | Documents current PPOLC→MSTATUS rules |
| **“Active” cancel-date filter** | `_is_active_rna_cancel_date` | Different domain (RNA), not phase status |
| **Latest-row / first-match selectors** | QuikLoan Issue #44 sort; reinsurance phase resolve | Precedence patterns exist, but **not** “first active phase → QuikMstr” |

**Confirmed:** There is **no** existing process that selects the first active phase and writes it to `quikmstr.MSTATUS`.

---

### Edge Cases

| Scenario | Current behavior (confirmed where noted) | Planning input |
|----------|------------------------------------------|----------------|
| First phase inactive (≥ 50), later phase active (0–49) | No phase-based override; `MSTATUS` stays PPOLC-derived; phase1 often mirrors that via inherit | **In-scope** under corrected rule |
| First phase active (0–49), later also active | `MSTATUS` stays PPOLC-derived | **Preserve** current behavior |
| Multiple later phases active | N/A for `MSTATUS` today | First later phase in order with status 0–49 |
| No phase active (all ≥ 50) | `MSTATUS` remains PPOLC composite + `ST_` translation | Preserve existing fallback |
| Phase ordering missing / duplicate `BENEFIT_SEQ` | `MPHASE` from mapped `BENEFIT_SEQ`; no `MSTATUS` arbiter | Needs deterministic tie-breaker in planning |
| Blank / invalid / nonnumeric phase status | Current output: **0** blank / **0** nonnumeric `MPHSTAT`; source has blank `STATUS_CODE` rows | Skip invalid when searching; do not treat blank first phase as inactive |
| Interaction with phase-1 inherit sync | Inherit copies non-`{11,22,ACTIVE}` `MSTATUS` onto phase 1 | If override sets `MSTATUS` into 0–49 (e.g. 22), inherit will not push terminal onto phase 1 |
| Issue #13 termination precedence | Applies to PPOLC-derived path | Phase override must run **after** Issue #13 provisional `MSTATUS` |

---

### Likely Change Surface

**Primary (if implemented later):**

| Artifact | Role |
|----------|------|
| `app.py` and `QLA_Migration/app.py` | Surgical `MSTATUS` logic (after Issue #13 interceptor and/or post-map enrichment). **Must bump `APP_VERSION` in both** when coding. |
| Possibly PPBEN cache during `quikmstr` or post-`quikridr` enrichment | Needed to read phase statuses; batch order / circularity with phase-1 sync must be designed in planning |
| `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv` | Unlikely unless a new source field is mapped |
| `QLA_Migration/Mapping/Master_Value_Translation.csv` | Only if new status keys are needed (not indicated at intake) |

**Validators / governance / tests likely touched later:**

| Artifact | Role |
|----------|------|
| New `tools/validators/validate_issue49_*.py` | Trace + fleet checks (pattern from Issue #13) |
| `data_governance/rules/chk_quikmstr.py` (`POL-004`) | Still validates recognized `MSTATUS` codes |
| `validation/validation_rules.py` (`MSTR-001`) | Invalid `MSTATUS` |
| `tools/validators/validate_issue13_mstatus.py` | Regression — Issue #13 population must not silently reverse |

**Indirect / regression watch (not primary scope):**

| Artifact | Why |
|----------|-----|
| `app.py` ~6555–6576 phase-1 `MPHSTAT` sync | Coupled to `MSTATUS`; changing master status changes what phase 1 inherits |
| Issue #34 / #44 consumers of `quikmstr.MSTATUS` | Governance / loan context use master status |
| Claims cross-table checks vs `quikmstr` | Policy presence/status context |

**Out of scope per intake constraints:** redesign of rider emit, claims status, rate logic, wholesale rulebook rewrite, changing `MPHSTAT` as a primary target.

---

### Dependencies and Open Questions

#### Dependencies

| Item | Notes |
|------|-------|
| Issue #13 (CLOSED v57.48) | Defines current PPOLC→`MSTATUS` precedence; phase override runs after that provisional value |
| Phase-1 `MPHSTAT` inherit | Reverse coupling; changing `MSTATUS` changes what phase 1 inherits on the subsequent `quikridr` pass |
| QLAdmin manual active/inactive ranges | **Resolved** — 0–49 active; ≥ 50 inactive |
| Current Decision No-Go | Business still No-Go; intake does not change that |

#### Open questions for Stage 2 (threshold blockers removed)

1. **Authority source for phase status:** Raw `PPBEN.STATUS_CODE`, pre-sync translated `MPHSTAT`, or post-sync / simulated display `MPHSTAT`?
2. **Example policies:** Still none supplied by client; fleet candidates (e.g. `018252C`) available for planning traces.
3. **Collateral fields:** `MSTATDATE` / phase-1 `MPHSTAT` remain out of primary scope unless Risk expands.
4. **No PPBEN rows:** Confirm preserve Issue #13 PPOLC `MSTATUS` (expected).

---

### Intake Verdict

**`READY FOR STAGE 2`**

Active/inactive ranges are confirmed from the **QLAdmin manual** (0–49 active; ≥ 50 inactive). The original reversed threshold is corrected. Technical findings on PPOLC→`MSTATUS`, PPBEN→`MPHSTAT`, Issue #13, phase-1 sync, and the absence of a first-active-phase→QuikMstr pattern remain unchanged and are sufficient to begin Planning.

---

### Proposed Stage 2 — Planning Prompt

```text
Perform Stage 2 — Planning only for Issue #49 (QuikMstr Active Phase Status). Do not write implementation code or bump APP_VERSION. Using Issue_Log_Items/Issue_49/Issue_49_Intake_Report.md and the confirmed QLAdmin manual ranges (0–49 active, ≥50 inactive), design the smallest safe change so QuikMstr.MSTATUS uses the first later active phase when phase 1 is inactive. Choose phase-status authority, placement relative to Issue #13 and phase-1 sync, edge-case handling, validation, and regression. Stop after Planning; do not begin Dependency Gate or Development.
```

---

*End of Stage 1 Intake (clarified). No code, mappings, outputs, or version numbers were changed.*
