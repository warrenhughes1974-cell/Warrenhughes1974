# Issue #49 — Planning Report

**Issue:** #49 — QuikMstr Active Phase Status  
**Framework stage:** Stage 2 — Planning only  
**Generated:** 2026-07-10  
**Intake reference:** `Issue_Log_Items/Issue_49/Issue_49_Intake_Report.md`  
**Engine baseline:** `app.py` / `QLA_Migration/app.py` **v57.69**  
**Code changes:** None (planning is read-only)

---

### Issue Summary

`quikmstr.MSTATUS` is today derived only from **PPOLC** via the Issue #13 composite interceptor and `ST_*` translation. Phase statuses live on **`quikridr.MPHSTAT`** (from `PPBEN`), and phase 1 may **inherit** non-blocked `MSTATUS` values. That produces QLAdmin displays where phase 1 is inactive (≥ 50) while a later phase is active (0–49), yet the policy master still shows the inactive/PPOLC status.

**Planning goal:** Design the smallest safe change so that, when the first phase is inactive (≥ 50) and a later phase is active (0–49), `QuikMstr.MSTATUS` is set to that first active later phase’s status. Do not change `MPHSTAT`, claims, rates, or other `quikmstr` fields in this issue.

**Expected in-scope fleet size (current Output, approximate):** ~**35** policies with phase-1 status ≥ 50 and a later phase in 0–49 (e.g. 22). Policies whose phase 1 is already 0–49 (including NFO 41/44/45) are **out of override scope**.

---

### Confirmed Business Rule

**Authority for active/inactive ranges:** QLAdmin manual.

| Status number | Classification |
|---------------|----------------|
| 0 through 49 | Active |
| 50 and above | Inactive |

**Per-policy rule (confirmed):**

```text
For each policy:

1. Order the policy phases using the established phase order.
2. Inspect the first phase.
3. If the first phase status is between 0 and 49, preserve the current QuikMstr status behavior.
4. If the first phase status is 50 or greater, inspect the remaining phases in order.
5. Select the first later phase whose status is between 0 and 49.
6. Set QuikMstr.MSTATUS to that active phase's status.
7. If no active phase exists, preserve the existing QuikMstr.MSTATUS behavior.
```

**Confirmed — not part of this rule:** Changing `MSTATDATE`, redesigning `MPHSTAT`, or altering Issue #13 PPOLC precedence when the override does not fire.

---

### Current Technical Flow

**Confirmed (from intake / code):**

```text
PPOLC row
  → Sync_Rulebook_quikmstr: CONTRACT_CODE → MSTATUS
  → Issue #13 interceptor (app.py ~6231–6242): build T_/PUT_/A_ composite
  → ST_* translation (app.py ~6423–6425)
  → write quikmstr.csv (MSTATUS)

PPBEN rows (later in batch)
  → Sync_Rulebook_quikridr: BENEFIT_SEQ → MPHASE, STATUS_CODE → MPHSTAT
  → bare-letter translation (A→22, T→56, …) — no ST_ prefix
  → if MPHASE == "1": optional inherit from quikmstr.MSTATUS
       when MSTATUS not in {"", "11", "22", "ACTIVE"}  (app.py ~6555–6576)
  → write quikridr.csv
```

**Confirmed gaps:**

- No first-active-phase → `MSTATUS` path exists.
- Raw `PPBEN` often has **both** benefits `STATUS_CODE=A` even when emitted phase 1 is ≥ 50 (inherit artifact). Using raw letters alone would **not** fire the corrected rule for the observed candidate population.

---

### Recommended Authority for Phase Status

**Recommendation: Use simulated QLAdmin display phase status (post-synchronization semantics), not raw `PPBEN.STATUS_CODE` alone.**

| Option | What it uses | Fires for ~35 candidates? | Matches QLAdmin display? |
|--------|--------------|---------------------------|----------------------------|
| A. Raw `PPBEN.STATUS_CODE` | Letter A/T/… | **No** (seq1 often still `A`) | No — ignores phase-1 inherit |
| B. Pre-sync translated `MPHSTAT` only | Bare map A→22 etc. | **No** (phase1 still 22 before inherit) | No — not what UI shows after sync |
| C. **Simulated / final display status** | Translate PPBEN like `MPHSTAT`, then apply the **same phase-1 inherit rule** using provisional Issue #13 `MSTATUS`; later phases = translated only | **Yes** | **Yes** — matches what QLAdmin shows after conversion |

**Why C (planning recommendation):**

1. The issue is about the status **QLAdmin presents** on phases vs policy master.
2. Intake proved the candidate pattern is largely **phase-1 inherit from `MSTATUS`**, not LifePRO letter divergence.
3. User guidance: prefer final converted phase status when it reflects QLAdmin display.

**How to obtain C without a broken batch order:**

- **Preferred placement:** During `quikmstr` conversion, **after** Issue #13 produces provisional numeric `MSTATUS`, load/cache PPBEN phases for the policy and compute display statuses:
  - Translate each phase’s `STATUS_CODE` with the same bare-letter map used for `MPHSTAT`.
  - For the first phase only: if provisional `MSTATUS` is non-blank and not in `{11, 22, ACTIVE}`, set display status = provisional `MSTATUS` (mirror `app.py` ~6574–6576); else use translated value.
  - For later phases: use translated value only.
- Then apply the Issue #49 selection rule to those display statuses and optionally override `MSTATUS`.

**Alternative (acceptable but weaker):** After `quikridr` is written, read actual post-sync `MPHSTAT` and patch `quikmstr.MSTATUS`. Simpler to reason about emitted files, but leaves phase-1 `MPHSTAT` reflecting the **pre-override** master within the same batch (out of `MSTATUS`-only scope, yet inconsistent until a design that re-runs inherit). Prefer the in-`quikmstr` simulation so the subsequent `quikridr` pass inherits from the **final** `MSTATUS`.

**Confirmed fact vs recommendation:** It is **confirmed** that post-sync phase-1 `MPHSTAT` currently equals `MSTATUS`. It is a **planning recommendation** to simulate that display status during `quikmstr` rather than reading raw PPBEN letters only.

---

### Recommended Phase Selection Algorithm

**Policy key:** Group by converted `MPOLICY` (crosswalked from `PPBEN.POLICY_NUMBER` / `PPOLC.POLICY_NUMBER`).

**Phase order (authoritative):**

1. Numeric `BENEFIT_SEQ` ascending (source), which maps to `MPHASE` ascending.
2. **Tie-breaker if duplicate sequence:** ascending original source row order within the extract (stable, deterministic).
3. **First phase:** first row after that sort (normally `MPHASE` / `BENEFIT_SEQ` = 1). If phase 1 is missing, use the minimum sequence row as first phase.

**Status parse:**

- Accept integer-like strings (`"54"`, `"54.0"`).
- Blank, nonnumeric, or unmapped letter-after-failed-translate → **invalid** for range tests.

**Algorithm (pseudocode):**

```text
provisional = Issue_13_translated_MSTATUS(PPOLC row)   # existing behavior

phases = PPBEN rows for policy, sorted by BENEFIT_SEQ asc, then row order
if no phases:
    MSTATUS = provisional
    return

display[] = []
for i, phase in enumerate(phases):
    translated = bare_letter_map(STATUS_CODE)   # same as MPHSTAT path
    if i == 0:
        if provisional not in {"", "11", "22", "ACTIVE"} and is_numeric(provisional):
            display_status = provisional      # simulate phase-1 sync
        else:
            display_status = translated
    else:
        display_status = translated
    display.append(display_status)

first = display[0]
if not is_numeric(first) or int(first) < 50:
    MSTATUS = provisional                     # active or invalid first → preserve
    return

for status in display[1:]:
    if is_numeric(status) and 0 <= int(status) <= 49:
        MSTATUS = normalize_status(status)    # first active later phase
        return

MSTATUS = provisional                         # no active later phase
```

**Active test:** `0 <= status <= 49` (QLAdmin manual).  
**Inactive test:** `status >= 50`.

---

### Placement in Conversion Flow

**Recommended order of operations for each `quikmstr` row:**

1. Rulebook map + existing transforms.
2. **Issue #13** `MSTATUS` composite interceptor + `ST_*` translation → provisional numeric status.
3. **Issue #49** first-active-phase override (new) → maybe replace `MSTATUS`.
4. Write `quikmstr` row.
5. Later: `quikridr` conversion runs phase-1 inherit against the **final** `MSTATUS`.

**Why after Issue #13 (confirmed dependency):**  
Issue #13 defines the correct PPOLC-derived status (including `CONTRACT_CODE=T` precedence). The override must start from that value as the fallback and as the simulated phase-1 inherit input. Running #49 before #13 would reintroduce the wrong NFO-vs-termination behavior on the fallback path.

**Why not only inside `quikridr`:**  
`MSTATUS` is owned by `quikmstr`; patching master from rider mid-row is awkward. Enrichment during `quikmstr` (with PPBEN cache) keeps a single write of master status.

**PPBEN cache (planning note):**  
Similar to other `quikmstr` enrichment caches (PPACH, PPBENTYP). Load once per batch when converting `quikmstr`, keyed by LifePRO `POLICY_NUMBER` / crosswalked `MPOLICY`, storing ordered `(BENEFIT_SEQ, STATUS_CODE)` (and optionally pre-translated status).

---

### Interaction With Existing Status Logic

| Existing logic | Interaction | Planning disposition |
|----------------|-------------|----------------------|
| Issue #13 interceptor ~6231–6242 | Must run **before** #49 | **Required** |
| `ST_*` translation | Produces provisional numeric `MSTATUS` | Unchanged |
| Phase-1 inherit ~6555–6576 | Uses final `MSTATUS` after #49 | If #49 sets an active code (e.g. 22), inherit **will not** overwrite phase 1 (22 blocked). Phase 1 then keeps PPBEN-translated active status — aligned with master. If #49 does not fire, inherit behaves as today. |
| Inherit block list `{11,22,ACTIVE}` vs manual 0–49 | Inherit still uses old block list | **Out of scope** to widen inherit to full 0–49; only `MSTATUS` selection uses the manual range |
| NFO codes 41/44/45 on phase 1 | Active per manual → #49 does **not** override | Preserves RPU/ETI/Paid-Up masters even when a later phase is 22 |

**Scope boundary (confirmed):** Do not change the phase-1 inherit block list or `MPHSTAT` mapping in Issue #49 unless Dependency Gate / Risk explicitly expands scope.

---

### Edge-Case Handling

| Scenario | Expected Result |
|----------|-----------------|
| Phase 1 status is 0–49 | Preserve current QuikMstr status behavior (Issue #13 provisional) |
| Phase 1 is 50+, phase 2 is 0–49 | QuikMstr uses phase 2 status |
| Phase 1 is 50+, phase 2 is 50+, phase 3 is 0–49 | QuikMstr uses phase 3 status |
| All phases are 50+ | Preserve current QuikMstr status |
| Only one phase exists and it is active (0–49) | Preserve current behavior |
| Only one phase exists and it is inactive (≥ 50) | Preserve current behavior |
| Blank / invalid phase status before an active phase | Do **not** treat blank first phase as inactive (preserve provisional). When scanning later phases, **skip** invalid statuses and select the first valid active (0–49) |
| Duplicate phase sequence values | Sort by `BENEFIT_SEQ` asc, then source row order; first row = first phase; first later valid active wins |
| No PPBEN phases exist | Preserve current QuikMstr status |
| Phase status changes during existing synchronization | Use **simulated display status** (Recommendation C): phase 1 reflects inherit-from-provisional; later phases use translated PPBEN only — same decision QLAdmin display would show after sync with that provisional master |
| Unmapped `STATUS_CODE` that remains a letter after translate | Treat as invalid; skip in active search; if first phase invalid → preserve provisional |

---

### Proposed Change Surface

**Stage 5 development targets (do not implement now):**

| File | Region / function | Change |
|------|-------------------|--------|
| `QLA_Migration/app.py` | After MSTATUS interceptor ~6231–6242 / after `ST_` translate when `t_id=quikmstr` and `t_f=MSTATUS` | Call new override helper with provisional status + PPBEN phase cache |
| `app.py` (repo root) | Same regions (must stay in sync; `run_converter.bat` launches root `app.py`) | Identical surgical edit |
| Both `app.py` files | `APP_VERSION` | Bump when coding (not now) |
| Optional: `qla_core/` small helper module | e.g. `quikmstr_active_phase_status.py` | Pure functions: parse status, sort phases, select first active — keeps `app.py` surgical |

**Not expected to change:**

| Artifact | Reason |
|----------|--------|
| `Sync_Rulebook_quikmstr.csv` / `quikridr.csv` | Logic is engine-side selection, not a new mapped column |
| `Master_Value_Translation.csv` | Reuse existing bare-letter + `ST_*` maps |
| Phase-1 inherit block (~6555–6576) | Out of `MSTATUS`-only scope |
| Claims / rates / other tables | Out of scope |

**Later documentation (Stage 8 / release — not now):**

- `Issue_Log_Items/Issue_Log_Master_Tracking_Sheet.md`
- Release notes for the version that ships #49
- Optional short note in `QLA_Migration/RUN_GUIDE.md` only if status behavior is documented there

---

### Validation Plan

**Stage 6 — read-only review + validation script(s).**

| Deliverable | Purpose |
|-------------|---------|
| `tools/validators/validate_issue49_mstatus.py` (new) | Automated checks against Output + Source |
| `Issue_Log_Items/Issue_49/Issue_49_Validation_Report.md` | Pass/fail matrix |
| Trace CSV (optional under `Issue_49/`) | Before/after for candidate policies |

**Minimum script checks:**

1. **Range authority:** Override only when simulated/first display phase ≥ 50 and a later phase ∈ 0–49.
2. **Preserve when phase 1 active:** Sample NFO policies (`018187C` MSTATUS 45, `010380550C` 41) unchanged by #49.
3. **Candidate override:** Policies like `018252C` (phase1 display 54, later 22) → `MSTATUS` becomes `22` (or whatever first later 0–49 status is).
4. **All inactive / single inactive phase:** `MSTATUS` equals Issue #13 provisional.
5. **No PPBEN:** `MSTATUS` unchanged vs Issue #13.
6. **Schema:** `MSTATUS` still in `VALID_MSTATUS_CODES` / `POL-004`.
7. **Issue #13 regression subset:** Re-run or call into `validate_issue13_mstatus.py` expectations for the 607 termination population where phase-1 display remains inactive with no later active phase.

**Test matrix (required):**

| Scenario | Expected Result |
|----------|-----------------|
| Phase 1 status is 0–49 | Preserve current QuikMstr status behavior |
| Phase 1 is 50+, phase 2 is 0–49 | QuikMstr uses phase 2 status |
| Phase 1 is 50+, phase 2 is 50+, phase 3 is 0–49 | QuikMstr uses phase 3 status |
| All phases are 50+ | Preserve current QuikMstr status |
| Only one phase exists and it is active | Preserve current behavior |
| Only one phase exists and it is inactive | Preserve current behavior |
| Blank phase status before an active phase | Skip invalid status and select first valid active phase (if first was blank → preserve provisional; blanks in later scan are skipped) |
| Duplicate phase sequence values | Apply BENEFIT_SEQ then row-order tie-breaker |
| No PPBEN phases exist | Preserve current QuikMstr status |
| Phase status changes during existing synchronization | Use simulated display status (Recommendation C) |

---

### Regression Plan

**Stage 7 — batch + comparison.**

| Check | Method |
|-------|--------|
| Full batch row counts | `quikmstr` 5083; `quikridr` unchanged row count |
| `MSTATUS` delta population | Diff pre/post `quikmstr.csv`; expect ~35 overrides (measure exactly at Risk/Dev) |
| Non-candidate stability | All policies with phase-1 display 0–49 keep prior `MSTATUS` |
| Issue #13 hold | Termination-first keys still correct where no later active phase |
| Phase-1 inherit side effect | For overridden policies (new `MSTATUS` in 0–49), phase-1 `MPHSTAT` should follow PPBEN translate (not terminal inherit) after rebatch — **observe**, do not expand issue to force `MPHSTAT` edits |
| Unrelated fields | `MBILLDAY`, modal factors, `MPREM`, banking columns unchanged |
| Governance | `chk_quikmstr` POL-004 clean on `MSTATUS` |

**Baseline:** Freeze current Output (or a dated copy under `QLA_Migration/Archive/` / issue evidence) before the development batch for side-by-side `MSTATUS` comparison only.

---

### Risks and Safeguards

| Risk | Severity | Safeguard |
|------|----------|-----------|
| Using raw PPBEN letters → rule never fires | High (misses defect) | Mandate Recommendation C (simulated display status) |
| Applying override when phase 1 is NFO (41–45) | High (wrong blast radius ~142) | Strict ≥ 50 trigger only |
| Circularity with phase-1 inherit | Medium | Run #49 on provisional status during `quikmstr` so inherit sees final master |
| Issue #13 regressions | Medium | Validator + termination sample traces |
| Inherit block list ≠ manual 0–49 | Low for #49 | Document; do not change inherit in this issue |
| Duplicate/missing phase 1 | Low | Documented sort + min-sequence fallback |
| Scope creep into `MPHSTAT` | Medium | Explicit out-of-scope; observe only in regression |

**Rollback:** Revert the surgical `app.py` / `QLA_Migration/app.py` block and version bump; no rulebook dependency if implemented as engine-only.

---

### Dependencies

| Dependency | Status | Blocks Stage 3? |
|------------|--------|-----------------|
| QLAdmin manual 0–49 / 50+ ranges | **Resolved** | No |
| Issue #13 closed behavior | Available | No — must preserve as fallback |
| PPBEN extract in Source package | Available | No |
| Phase-1 inherit semantics | Available (simulate, don’t rewrite) | No |
| Client example policy | Not supplied; fleet candidates exist | No for Gate if Risk accepts measured candidates |
| Business Decision still No-Go | Process | Does not block technical Stage 3; blocks production release until Go |

**No hard technical dependency missing for Dependency Gate.**

---

### Stage 2 Verdict

**`READY FOR STAGE 3`**

Planning recommends a surgical post–Issue #13 override on `quikmstr.MSTATUS` that uses **simulated QLAdmin display phase statuses** (PPBEN translate + existing phase-1 inherit semantics against provisional `MSTATUS`), selects the first later phase in `BENEFIT_SEQ` order with status **0–49** when the first phase is **≥ 50**, and otherwise preserves current PPOLC/`ST_*` behavior. Scope remains `QuikMstr.MSTATUS` only.

---

### Proposed Stage 3 — Dependency Gate Prompt

```text
Perform Stage 3 — Dependency Gate only for Issue #49. Do not write application code or bump APP_VERSION. Using Issue_49_Intake_Report.md and Issue_49_Planning_Report.md, confirm: (1) no conflicting open issues on MSTATUS; (2) Issue #13 fallback remains intact; (3) PPBEN availability in batch; (4) phase-1 inherit remains out of change scope; (5) measured ~35-policy candidate set is acceptable for Risk. Emit Issue_49_Dependency_Gate.md with GO / NO-GO for Stage 4. Do not begin Risk or Development.
```

---

*End of Stage 2 Planning. No code, mappings, outputs, or version numbers were changed.*
