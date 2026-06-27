# Issue #28 — Implementation Strategy

**Recommended approach:** Option A (Phase 1) + Option E Phase 2 (P3E)  
**Target engine version:** v57.35 (suggested)  
**Planning date:** 2026-06-24  
**Status:** Planning only — not implemented

---

## Phase 0 — Catalog completeness (prerequisite)

### Objective

Add missing `DISCHO25` catalog row before or with Phase 1.

### Files

| File | Action |
|------|--------|
| `plan_governance/product_catalog_crosswalk.csv` | Add row: `DISCHO25 → 9DIS25` (all crosswalk columns from xlsx) |
| `QLA_Migration/Mapping/product_catalog_crosswalk.csv` | Sync full catalog to 141 rows |

### Validation

- `DISCHO25` appears in quikplan output as PLAN `9DIS25`
- P3C unauthorized manifest no longer lists DISCHO25

---

## Phase 1 — Runtime authority promotion (Option A)

### Objective

Make `load_product_catalog_crosswalk()` prefer `crosswalk_ql_plan_code` when non-blank.

### Files to modify

| File | Scope | Est. lines |
|------|-------|------------|
| `qla_core/product_catalog_authority.py` | `load_product_catalog_crosswalk()` — column precedence logic | ~15–25 |
| `app.py` | Version `v57.34` → `v57.35`; release note reference | ~2 |
| `QLA_Migration/app.py` | Mirror version bump | ~2 |

### Proposed logic (pseudocode — not implemented)

```
for each catalog row:
  plan = crosswalk_ql_plan_code if non-blank else ql_plan_code
  map[lifepro_coverage_id] = plan
```

Preserve existing normalize/strip behavior. Do not remove `ql_plan_code` column.

### Files to create

| File | Purpose |
|------|---------|
| `tools/validators/_validate_issue28_plan_mapping.py` | Compare quikplan PLAN to crosswalk inventory (141 rows) |
| `Issue_Log_Items/Issue_28/evidence/` | Before/after diffs post-development |

### Files explicitly NOT modified

| File | Reason |
|------|--------|
| `Sync_Rulebook_quikplan.csv` | Rulebook correct — engine crosswalk handles PLAN |
| `Sync_Rulebook_quikridr.csv` | Phase 2 scope |
| `Master_Crosswalk.csv` | Policy/product separation preserved |
| Issue #21M / #21K / #25 / #26 code paths | Orthogonal |

### Version bump

Per AGENTS.md: increment `app.py` version when modifying conversion behavior.

---

## Phase 2 — quikridr MPLAN alignment (Option E)

### Objective

After Phase 1 validated, enable authoritative MPLAN resolution for quikridr.

### Files to modify

| File | Scope |
|------|-------|
| `app.py` | Document/default `QLA_CLOSED_MPLAN_AUTHORITY=1` for batch (or batch launcher script) |
| Batch run configuration | Env var in RUN_GUIDE or orchestration |

### Preconditions

- quikplan output contains authoritative PLAN codes for all 33 previously divergent rows
- P3E resolver `authoritative_union()` intersects quikplan PLAN set with catalog

### Validation

- Sample policies with riders 0823 960CH, 0824 P DIS, 10827 MN5K show MPLAN = 960CWP, 94PDIS, 1CSIMN
- P3E trace: no UNAUTHORIZED for remediated PLAN_CODEs
- Re-run referential integrity analysis (phase_p3d pattern)

---

## Phase 3 — Governance cleanup (optional, same release)

| Task | File |
|------|------|
| Update `mapping_status` for 33 rows to `AUTHORITY_ALIGNED` | product catalog CSV |
| Refresh `plan_change_manifest.csv` uat_status | manifests |
| Update P2E generator to seed compat from authoritative on future regen | `phase_p2e_authority_separation_runner.py` |

Defer generator change if not regenerating catalog in this release.

---

## Validation approach

### Automated

| Step | Command / artifact |
|------|-------------------|
| 1 | Full batch: `_run_full_batch_test.py` |
| 2 | Issue #28 validator: `_validate_issue28_plan_mapping.py` → expect 0 mismatches |
| 3 | Issue #25 MPOLICY width validator |
| 4 | Issue #26 MPREM validator |
| 5 | Issue #21M / 21M-FU memo validator |
| 6 | Re-run `Issue_Log_Items/Issue_28/_issue28_intake_analysis.py` on new output |

### Manual / analytical

| Step | Check |
|------|-------|
| 7 | Client 3 examples in quikplan.csv |
| 8 | CSO QA CSV — review missing_plan_codes |
| 9 | variation_code_audit.csv — 33 plan keys |
| 10 | Rate sample for 1CSIMN, 960CWP, 94PDIS (phase_r3 pattern) |

### Success criteria

- Runtime crosswalk comparison: **141/141 match** (or 140/140 if DISCHO25 excluded from quikplan source scope — must document)
- Protected issue validators: **ALL PASS**
- No new blank MRIDRID / schema integrity violations

---

## Rollback strategy

| Phase | Rollback |
|-------|----------|
| Phase 1 | Revert commit on `product_catalog_authority.py` + version; compat column unchanged — output restores instantly |
| Phase 0 catalog | Revert CSV add for DISCHO25 |
| Phase 2 P3E | Set `QLA_CLOSED_MPLAN_AUTHORITY=0` — no code revert required |

Keep v57.34 tagged output as before-state evidence.

---

## Client UAT impact

| UAT area | Impact |
|----------|--------|
| Product catalog review | **Full re-review** of 33 changed PLAN codes |
| Client examples (3) | Must PASS — primary acceptance test |
| Rider policies | Phase 2 — verify MPLAN on live policies |
| Memo tab (#21M) | No re-test required unless batch scope changes |
| Claims UAT | No direct impact |

### Suggested UAT script additions

1. Open quikplan for 10827 MN5K → confirm PLAN `1CSIMN`
2. Open quikplan for 0823 960CH → confirm PLAN `960CWP`
3. Open quikplan for 0824 P DIS → confirm PLAN `94PDIS`
4. Spot-check 5 additional rows from `Issue_28_Mapping_Differences.csv` (previously N)

---

## Estimated scope summary

| Phase | Dev effort | Validation effort |
|-------|-------------|-------------------|
| Phase 0 | 0.25 day | 0.1 day |
| Phase 1 | 0.5–1 day | 0.5 day |
| Phase 2 | 0.5 day | 0.5 day |
| **Total** | **1.25–1.75 days** | **1.1 days** |

---

## Dependency on other agents

| Agent | Input needed |
|-------|--------------|
| Dependency Gate | Client confirmation crosswalk is binding; UAT scope acceptance |
| Risk Agent | Rate table impact sign-off for 33 PLAN changes |
| Development Agent | This strategy + PASS gate |
| Validation Agent | Validator suite results |
