# Issue #28 — Code Changes

**Development date:** 2026-06-24  
**Engine version:** v57.34 → **v57.35**

---

## Phase 0 — DISCHO25 catalog row

### `plan_governance/product_catalog_crosswalk.csv`

**Change:** Insert row after `DISCHO247C`:

```csv
DISCHO25,9DIS25,DISCHO25,Home Office Discount - 25%-10Yr,Home Office Discount - 25%-10Yr,POLICY_FORM_CROSSWALK,STABLE_EMIT,9DIS25,DISCHO25,Home Office Discount - 25%-10Yr,Home Office Discount - 25%-10Yr,Catalog row from Policy Form Crosswalk 5.22.26 — Issue 28 Phase 0
```

**Rationale:** DISCHO25 is a distinct active product (not DISCHO247C). Missing row blocked quikplan emission and caused incorrect P3E resolution.

### `QLA_Migration/Mapping/product_catalog_crosswalk.csv`

**Change:** Full sync from governance copy (141 data rows + header = 142 lines). Resolves B-05 stale migration copy (was 133 rows).

---

## Phase 1 — Runtime authority promotion

### `qla_core/product_catalog_authority.py` — `load_product_catalog_crosswalk()`

**Before:** Read `ql_plan_code` (compat/passthrough) only.

**After:**

```python
plan = normalize(row.get(auth_col, "")) if auth_col else ""
if not plan:
    plan = normalize(row.get(compat_col, ""))
```

**Rationale:** Promotes `crosswalk_ql_plan_code` to runtime authority per Planning Option A. Preserves `ql_plan_code` as fallback for rows without authoritative column. No schema or column removal.

**Verified mappings (spot check):**

| Coverage_ID | Before (compat) | After (authoritative) |
|-------------|-----------------|------------------------|
| 10827 MN5K | 10827 MN5K | 1CSIMN |
| 0823 960CH | 0823 960CH | 960CWP |
| 0824 P DIS | 0824 P DIS | 94PDIS |
| DISCHO247C | 9DIS25 | 9DS24C |
| DISCHO25 | (missing) | 9DIS25 |

---

## Phase 2 — P3E MPLAN alignment

### `qla_core/product_catalog_authority.py` — `closed_mplan_authority_enabled()`

**Before:** Default `QLA_CLOSED_MPLAN_AUTHORITY=0` (opt-in).

**After:** Default enabled; opt-out with `QLA_CLOSED_MPLAN_AUTHORITY=0|false|no`.

**Rationale:** Planning strongly recommended P3E in same release so QUIKRIDR.MPLAN aligns with corrected quikplan PLAN authority.

### `app.py` and `QLA_Migration/app.py` — batch quikplan post-emit refresh

**Added after quikplan.csv write (batch only):**

```python
if is_batch and t_id.lower() == "quikplan" and self._closed_mplan_authority_enabled():
    mplan_resolver, quikplan_plan_set, _ = self._init_mplan_authority(out_dir, cw_path)
    self.log(
        f"P3E MPLAN AUTHORITY: refreshed resolver after quikplan emit "
        f"(quikplan PLAN universe={len(quikplan_plan_set)})"
    )
```

**Rationale:** Batch previously initialized P3E resolver at startup using **stale** quikplan.csv from prior run. Refresh ensures quikridr uses authoritative PLAN universe from current batch emit.

---

## Version bump — v57.35

### `app.py`

- Header version block (line ~4–6)
- Window title (line ~227)
- Header label (line ~273)
- Batch init log (line ~4238)

### `QLA_Migration/app.py`

- Mirror of all four version touchpoints above

---

## New file — validator (for Validation Agent)

### `tools/validators/validate_issue28_plan_mapping.py`

Compares quikplan emitted PLAN per coverage ID against `load_crosswalk_authority()` product map. Includes client example checks and catalog sync warning.

**Not executed during Development** (per stop condition).

---

## Files explicitly NOT modified

| File | Reason |
|------|--------|
| `Sync_Rulebook_quikplan.csv` | Rulebook correct — engine crosswalk handles PLAN |
| `Sync_Rulebook_quikridr.csv` | No rulebook change required |
| `Master_Crosswalk.csv` | Policy/product separation preserved |
| Issue #21M / #21M-FU / #21K / #25 / #26 code paths | Protected issues — orthogonal |
| `Policy Form Crosswalk 5.22.26.xlsx` | Source of truth — read-only |

---

## Deferred work (Phase 3 — optional)

| Task | Status |
|------|--------|
| Update `mapping_status` to `AUTHORITY_ALIGNED` for 33 rows | Deferred — governance cleanup |
| Refresh `plan_change_manifest.csv` uat_status | Deferred |
| P2E generator compat seed update | Deferred |
| RUN_GUIDE env var documentation | Recommended during Release Integration |
