# Issue #28 — Rollback Checklist

**Risk analysis date:** 2026-06-24  
**Rollback target:** v57.34 behavior

---

## Rollback triggers

- [ ] Protected issue validator failure (#25, #26, #21M, #21M-FU)
- [ ] Issue #28 validator shows unexpected PLAN mappings
- [ ] Client UAT rejection on product catalog
- [ ] Critical rate/CSO failure on production candidate batch
- [ ] Unplanned schema or row-count regression

---

## Rollback procedure

### Step 1 — Code rollback (Phase 1)

| Action | Detail |
|--------|--------|
| Revert commit | `qla_core/product_catalog_authority.py` — restore `ql_plan_code`-only load |
| Revert version | `app.py` / `QLA_Migration/app.py` → v57.34 |
| Verify | `load_product_catalog_crosswalk()` reads compat column only |

**Time:** Minutes (git revert)

### Step 2 — Catalog rollback (Phase 0)

| Action | Detail |
|--------|--------|
| Revert CSV | `plan_governance/product_catalog_crosswalk.csv` — remove DISCHO25 row if added |
| Sync | Revert `QLA_Migration/Mapping/product_catalog_crosswalk.csv` |
| Preserve | **`ql_plan_code` compat column unchanged** — no data loss on revert |

**Note:** Option A primary fix is **code-only** for 33 mappings — catalog `crosswalk_ql_plan_code` column **need not be reverted** (already held authoritative values).

### Step 3 — Crosswalk / xlsx

| Action | Detail |
|--------|--------|
| Revert xlsx? | **No** — xlsx is client authority; unchanged by fix |
| Revert overlay flags? | Reset `CROSSWALK_OVERLAY=0` if toggled |

### Step 4 — Output regeneration

| Action | Detail |
|--------|--------|
| Re-run batch | Full batch at v57.34 |
| Validate | MPOLICY / MPREM / 21M validators PASS |
| Compare | quikplan PLAN returns to 33 passthrough values |

---

## Artifacts to preserve (before rollback)

- [ ] v57.35 quikplan.csv (failed candidate)
- [ ] Validation logs
- [ ] `Issue_28_Mapping_Differences.csv` post-fix attempt
- [ ] Git commit SHA for fix

---

## Rollback verification checklist

After rollback, confirm:

- [ ] `10827 MN5K` PLAN = `10827 MN5K` (not 1CSIMN)
- [ ] `0823 960CH` PLAN = `0823 960CH`
- [ ] `0824 P DIS` PLAN = `0824 P DIS`
- [ ] Protected validators PASS
- [ ] quikplan row count = 141
- [ ] No new schema errors

---

## Partial rollback options

| Scenario | Partial rollback |
|----------|------------------|
| Phase 2 P3E causes MPLAN issues | Disable `QLA_CLOSED_MPLAN_AUTHORITY`; keep Phase 1 quikplan fix |
| DISCHO25 row causes issue | Remove DISCHO25 catalog row only |
| Rate gaps on specific PLAN | **Not recommended** — partial PLAN revert breaks crosswalk alignment |

---

## Rollback ownership

| Component | Rollback owner |
|-----------|----------------|
| Code revert | Development / Release |
| Batch re-run | Operations |
| Client communication | PM / Client liaison |
| Validator sign-off | Validation Agent |

---

## Recovery path after rollback

1. Root-cause failed validation item
2. Re-enter Development with targeted fix
3. Re-run Risk review if scope expands (e.g. FORM alignment added)
