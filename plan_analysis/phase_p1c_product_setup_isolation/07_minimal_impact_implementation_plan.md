# Minimal-Impact Implementation Plan (Phase P1C → P2)

## Objective

Isolate product setup with **zero semantic change** and **minimal app.py diff**, preserving Sync_Rulebook_quikplan behavior exactly.

---

## Phase Breakdown

### P1C (Current) — Architecture & Design ✅

- Document isolation architecture
- Dependency analysis
- Governance recommendations
- Code isolation map
- **No code changes**

### P2A — Shared Module Extraction (Low Risk)

**Goal:** Single transformation engine callable from app.py and subprocess.

| Step | Action | Risk |
|---|---|---|
| 2A.1 | Create `qla_core/schema_constants.py` — copy `TABLE_SCHEMAS["quikplan"]` list | Low |
| 2A.2 | Create `qla_core/normalize_utils.py` — extract `normalize()`, `extract_day()` | Low |
| 2A.3 | Create `qla_core/quikplan_converter.py` — extract quikplan rulebook loop from app.py | Medium |
| 2A.4 | app.py: replace inline quikplan loop with `convert_quikplan()` call | Medium |
| 2A.5 | Parallel-run test: diff output before/after extraction | Validation gate |

**Rollback:** Revert app.py to inline loop; delete qla_core.

**app.py version bump:** v55.7 → v55.8 (surgical extraction only).

### P2B — Product Setup Subprocess Runner

| Step | Action | Risk |
|---|---|---|
| 2B.1 | Create `plan_governance/phase_p2_product_setup_runner/product_setup_runner.py` | Low |
| 2B.2 | Runner calls `qla_core.quikplan_converter.convert_quikplan()` | Low |
| 2B.3 | Add crosswalk enrichment adapter (overlay only) | Medium |
| 2B.4 | Add governance diagnostics engine (additive CSV) | Low |
| 2B.5 | Parallel-run: runner output vs app.py single-table output | Validation gate |

### P2C — app.py UI Launcher (~155 lines)

| Step | Action | Risk |
|---|---|---|
| 2C.1 | Product Setup tab (paths + run button) | Low |
| 2C.2 | Subprocess hook + stdout parser | Low |
| 2C.3 | Status banner extension | Low |
| 2C.4 | Optional: batch skip quikplan checkbox | Low |

### P2D — Batch Isolation Cutover

| Step | Action | Risk |
|---|---|---|
| 2D.1 | Enable `QLA_PRODUCT_SETUP_ISOLATED=1` in test environment | Medium |
| 2D.2 | Full batch run without quikplan in loop | Validation |
| 2D.3 | Verify quikridr MPLAN references resolve | Validation |
| 2D.4 | Business signoff | Gate |

### P3 — Crosswalk Authority Migration (Business-Gated)

| Step | Action | Risk |
|---|---|---|
| 3.1 | Segregate plan rows from Master_Crosswalk.csv | High — requires policy impact analysis |
| 3.2 | Policy Form Crosswalk becomes sole plan map | Medium |
| 3.3 | FORM overlay precedence (crosswalk over LifePRO form) | Medium — 94 rows affected |
| 3.4 | Parallel diff + business signoff | Gate |

### P4 — quikplan.dbf Generation (Optional UAT)

| Step | Action | Risk |
|---|---|---|
| 4.1 | Create `quikplan_dbf_generator.py` (mirror Phase 21B) | Low |
| 4.2 | quikplan DBF layout from QLAdmin spec / existing reference | Medium |
| 4.3 | CSV/DBF row alignment manifest | Low |

### P5+ — Actuarial Attachment (Future, Not Now)

- HRIGPKEY population governance
- QuikPlbd rate loads
- Vary-by dimension validation

---

## Implementation Order (Recommended)

```
P2A (extract) → P2B (runner) → validate identical output → P2C (UI) → P2D (batch skip) → P3 (crosswalk authority)
```

**Do not skip validation gates.**

---

## Files Created (P2)

| File | Purpose |
|---|---|
| `qla_core/quikplan_converter.py` | Shared rulebook engine |
| `qla_core/crosswalk_enrichment.py` | Policy Form Crosswalk join |
| `plan_governance/phase_p2_product_setup_runner/product_setup_runner.py` | Subprocess CLI |
| `plan_governance/phase_p2_product_setup_runner/product_setup_governance_engine.py` | Diagnostics |
| `plan_governance/config/product_setup_runner_config.json` | Default paths |

## Files Modified (P2)

| File | Change |
|---|---|
| `app.py` | Import qla_core for quikplan; add UI launcher; optional batch skip |
| `AGENTS.md` | Document product isolation flags |

## Files NOT Modified

| File | Reason |
|---|---|
| `Sync_Rulebook_quikplan.csv` | Stable — preserve mappings/defaults |
| `plan_analysis/quikplan_source.csv` | Frozen source |
| Claims orchestration modules | Out of scope |
| `Master_Crosswalk.csv` | Until P3 business approval |

---

## Acceptance Criteria (P2 Complete)

- [ ] Isolated runner produces byte-identical `quikplan.csv` to current app.py (pre-P3)
- [ ] Rulebook line count unchanged (80 rules)
- [ ] Schema field order matches TABLE_SCHEMAS (79 fields)
- [ ] 133 rows in / 133 rows out
- [ ] Diagnostics CSV generated without blocking emit (default)
- [ ] Policy batch succeeds with quikplan skipped
- [ ] Rollback restores prior quikplan.csv in one command
- [ ] No claims regression (Phase 22 metrics unchanged)

---

## Effort Estimate

| Phase | Effort |
|---|---|
| P2A extraction | 1–2 sessions |
| P2B runner | 1 session |
| P2C UI | 1 session |
| P2D cutover + validation | 1 session |
| P3 crosswalk authority | Business-dependent |

---

## Regression Risks

| Risk | Mitigation |
|---|---|
| Extraction changes formatting | Parallel diff gate |
| Batch skip breaks MPLAN refs | Pre-flight catalog check + orphan diagnostic |
| Master_Crosswalk segregation breaks policy batch | Defer to P3; keep plan rows until validated |
| Duplicate PLAN silently emitted | Additive ERROR diagnostic |
