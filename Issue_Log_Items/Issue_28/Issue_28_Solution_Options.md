# Issue #28 — Solution Options Analysis

**Engine version:** v57.34  
**Planning date:** 2026-06-24  
**Intake basis:** `Issue_Log_Items/Issue_28/` (complete)

---

## Problem statement (proven)

33 of 141 plan mappings emit compatibility/`ql_plan_code` passthrough values instead of Policy Form Crosswalk 5.22.2026 authoritative QL Plan Codes stored in `crosswalk_ql_plan_code`. Root cause: **`load_product_catalog_crosswalk()` reads `ql_plan_code` only** (`qla_core/product_catalog_authority.py:417–438`).

Additional gap: **`DISCHO25`** missing from catalog (see `Issue_28_DISCHO25_Investigation.md`) — not part of the 33, but blocks quikplan completeness.

---

## Option A — Promote `crosswalk_ql_plan_code` to runtime authority

### Description

Modify `load_product_catalog_crosswalk()` to emit from `crosswalk_ql_plan_code` when present and non-blank, falling back to `ql_plan_code` for rows without crosswalk column population.

### Required changes

| Component | Change |
|-----------|--------|
| `qla_core/product_catalog_authority.py` | Update `load_product_catalog_crosswalk()` column precedence |
| `app.py` / `QLA_Migration/app.py` | Version bump only (no batch logic change if function is shared) |
| Catalog CSV | Add `DISCHO25` row (completeness); sync migration copy |
| Validator | New `_validate_issue28_plan_mapping.py` |

**Estimated code:** ~15–25 lines in one function + tests/validator.

### Advantages

- **Surgical** — single authority selection point; aligns runtime with existing P3C closed catalog design (`resolve_authoritative_plan_column()` already prefers `crosswalk_ql_plan_code`).
- Fixes all **33 divergent rows atomically** without editing 33 CSV cells manually.
- Preserves `ql_plan_code` compat column for rollback comparison.
- No new env flags for operators to manage.
- Unblocks P3E MPLAN alignment once quikplan emits authoritative PLAN universe.

### Disadvantages

- Code change required (minimal but touches shared authority module).
- Downstream rate/CSO/variation keyed on old passthrough PLAN codes will shift — requires regression batch.
- Must verify no consumer depended on compat passthrough intentionally.

### Regression impact

| Area | Impact |
|------|--------|
| 33 quikplan PLAN values | **Change** (intended) |
| 108 STABLE_EMIT rows | **No change** (compat = authoritative today) |
| Issues #25, #26, #21M, #21M-FU | **None** — orthogonal fields |
| Issue #21K | **None** — MUNIT schema unrelated |
| P3C diagnostics | **Improved alignment** |
| P3E MPLAN | Enables correct resolution after quikplan fix |

---

## Option B — Enable overlay by default (`CROSSWALK_OVERLAY=1`)

### Description

Leave `load_product_catalog_crosswalk()` unchanged. Set `CROSSWALK_OVERLAY=1` (or GUI default) so `apply_crosswalk_overlay()` rewrites PLAN/FORM/DESCR/PLANNAME from xlsx post-conversion.

### Required changes

| Component | Change |
|-----------|--------|
| `app.py` | Default env, GUI checkbox, or batch launcher |
| Documentation | Operational runbook for overlay flag |
| Optional | Remove dual-column confusion (documentation only) |

### Overlay completeness assessment

| Capability | Status |
|------------|--------|
| xlsx loader (`load_policy_form_crosswalk`) | Complete — 141 rows |
| quikplan PLAN/FORM/DESCR/PLANNAME | Applied when enabled |
| quikridr MPLAN | **Not covered** — overlay is quikplan-only |
| Master_Crosswalk / PPBEN path | **Not covered** |
| Production readiness | Module labeled **"scaffold — disabled by default"** in source header |

### Advantages

- No change to catalog CSV structure.
- xlsx remains single business source for overlay path.
- Rollback = flip flag off.

### Disadvantages

- **Dual authority paths** — catalog compat + xlsx overlay; harder to reason about and test.
- **Does not fix quikridr MPLAN** without separate P3E work.
- Operators must ensure flag on every batch (CLI, GUI, CI) — drift risk.
- Overlay applies **after** crosswalk engine — redundant with catalog if both active.
- FORM changes from crosswalk applied broadly — may expand scope beyond PLAN (#28).
- Not aligned with P3C architecture (catalog as closed authority).

### Regression impact

| Area | Impact |
|------|--------|
| quikplan (33 rows) | Fixed when overlay ON |
| quikridr MPLAN | **Unchanged** unless P3E added |
| Batch reproducibility | **Risk** — flag-dependent outputs |
| Protected issues #25/#26 | Low direct impact |

### Operational impact

- Every environment (dev, UAT, prod batch) must document overlay requirement.
- Client UAT baselines taken without overlay remain invalid — full re-UAT required regardless.

---

## Option C — Modify catalog generation (compat column promotion)

### Description

Update `product_catalog_crosswalk.csv`: set `ql_plan_code = crosswalk_ql_plan_code` for all 33 `CROSSWALK_DIVERGENT` rows. Add `DISCHO25` catalog row. Leave runtime code untouched.

### Required changes

| Component | Change |
|-----------|--------|
| `plan_governance/product_catalog_crosswalk.csv` | 33 row updates + 1 add |
| `QLA_Migration/Mapping/product_catalog_crosswalk.csv` | Sync |
| `phase_p2e_authority_separation_runner.py` | Update generator to emit authoritative into `ql_plan_code` **or** mark generator deprecated |
| `mapping_status` column | Flip divergent rows to `STABLE_EMIT` or new `AUTHORITY_PROMOTED` |

### Advantages

- **Zero runtime code change** — preserves existing architecture literally.
- Explicit, diff-reviewable CSV changes per plan.
- Rollback = revert CSV from git.

### Disadvantages

- **Regeneration risk** — P2E catalog builder seeds `ql_plan_code` from stable emit (`build_product_catalog()` line 144); re-running generator **overwrites** manual fixes unless generator is updated first.
- Two catalog copies must stay synchronized (currently 133 vs 140 rows — drift already exists).
- Does not express authority rule in code — future catalog imports may repeat divergence.
- P3E/quikridr still need verification; data-only fix to quikplan path only.
- Maintenance burden on every crosswalk revision (manual or scripted CSV merge).

### Deployment implications

- Catalog CSV deploy is sufficient for quikplan if all environments load same path.
- No app version requirement unless paired with validation tooling.
- Client must accept output delta without engine version narrative unless version bumped for traceability.

---

## Option D — Feature flag `PLAN_MAPPING_MODE`

### Description

Introduce runtime option:

```
PLAN_MAPPING_MODE = compatibility | authoritative | auto
```

- `compatibility` — current behavior (`ql_plan_code`)
- `authoritative` — `crosswalk_ql_plan_code` preference
- `auto` — use authoritative when `mapping_status=CROSSWALK_DIVERGENT`, else compat

### Required changes

| Component | Change |
|-----------|--------|
| `product_catalog_authority.py` | Mode resolver + env parsing |
| `app.py` | Env wiring, logging, GUI optional |
| Documentation | Mode matrix for ops |
| Tests | Matrix across 3 modes |

### Advantages

- Gradual cutover — UAT can run `authoritative` while dev stays `compatibility`.
- Long-term ops flexibility if multiple conversion projects need different modes.

### Disadvantages

- **Unnecessary complexity** for a one-time authority promotion — existing flags (`CROSSWALK_OVERLAY`, `QLA_CLOSED_MPLAN_AUTHORITY`) already fragment behavior.
- Three code paths to test and maintain indefinitely.
- `auto` mode encodes business rules in env config rather than catalog state.
- Violates AGENTS.md preference for surgical fixes over new frameworks.
- Client expectation is authoritative crosswalk — not a toggle.

### Assessment

**Not recommended** unless client explicitly requires prolonged dual-mode operation. Option A achieves authoritative emit with simpler surface area.

---

## Option E — Hybrid (Planning extension)

**A + P3E:** Promote catalog authority (Option A) **and** enable `QLA_CLOSED_MPLAN_AUTHORITY=1` after quikplan emits authoritative PLAN set, aligning quikridr MPLAN.

Not a separate root fix — **Phase 2** of recommended implementation after quikplan validated.

---

## Options not selected for primary recommendation

| Option | Reason |
|--------|--------|
| Master_Crosswalk-only update | Divergent IDs intentionally absent; duplicates policy numbers vs products |
| Overlay-only (B) | Incomplete (quikridr), dual-path, scaffold status |
| Feature flag (D) | Over-engineering |
| Catalog-only (C) | Viable fallback if code change blocked; regeneration risk |
