# Recommended Rollback Strategy (Phase P1C)

## Principle

Product setup isolation must be **rollback-safe** at every stage — staged, emitted, and DBF — without affecting policy conversion or claims governance.

---

## Rollback Layers

### Layer 1: Pre-Run Snapshot (Automatic)

Before every product setup run that may emit:

```
plan_governance/replay/snapshots/quikplan_{YYYYMMDD_HHMMSS}.csv
```

Copy current `output/quikplan.csv` if it exists.

Recorded in `product_setup_run_manifest.csv`:

```
rollback_snapshot_path, emit_timestamp, source_sha256, staged_rows, emitted_rows
```

### Layer 2: Staged-Only Mode (Default)

```
QLA_PRODUCT_SETUP_EMIT=0   (default)
```

Runner writes `plan_governance/staged/quikplan_staged.csv` only.

`output/quikplan.csv` **unchanged** — zero rollback needed.

### Layer 3: Emit Rollback (Manual or Flag)

```
QLA_PRODUCT_SETUP_ROLLBACK=1
```

Runner action:

1. Read most recent snapshot from manifest
2. Copy snapshot → `output/quikplan.csv`
3. Log rollback event to manifest
4. Skip transformation

app.py **Rollback Last Emit** button sets this flag and re-invokes runner.

### Layer 4: DBF Rollback

DBF files are **derived artifacts** — rollback = regenerate from known-good CSV or delete:

```
plan_governance/dbf/quikplan.dbf  → delete or regenerate from snapshot CSV
```

Never treat DBF as authoritative over CSV.

### Layer 5: Batch Isolation Rollback

```
QLA_PRODUCT_SETUP_ISOLATED=0
```

Restores quikplan processing in policy batch loop (current v55.7 behavior).

No file changes required.

---

## Rollback Decision Matrix

| Scenario | Action |
|---|---|
| Bad staged output | Do not emit; discard staged file |
| Bad emit to output/ | Restore snapshot CSV |
| Bad DBF | Delete DBF; regenerate from good CSV |
| Wrong crosswalk version | Rollback CSV + re-run with correct crosswalk |
| Extraction regression (P2A) | Revert app.py import; use inline loop |
| Batch fails after isolation | Disable isolation flag; verify catalog exists |

---

## Manifest Audit Trail

Each run appends to `product_setup_run_manifest.csv`:

| Column | Purpose |
|---|---|
| run_id | UUID |
| run_timestamp | ISO datetime |
| run_mode | STAGE / EMIT / ROLLBACK |
| source_path | quikplan_source.csv |
| source_sha256 | Determinism check |
| crosswalk_path | Policy Form Crosswalk version |
| rulebook_path | Sync_Rulebook_quikplan.csv |
| staged_path | Staged CSV location |
| emitted_path | Output CSV (if emit) |
| rollback_snapshot_path | Pre-emit backup |
| staged_rows | Row count |
| diagnostic_errors | Count |
| diagnostic_warnings | Count |
| production_dbf_flag | Always N until authorized |
| operator | Optional user ID |

---

## Parallel Safety with Claims

| Concern | Isolation |
|---|---|
| Claims hold manifest | Untouched |
| quikclms/quikclmp emit | Untouched |
| output/quikmstr.csv | Untouched by product rollback |
| output/quikridr.csv | Read-only reference for orphan diagnostic |
| Master_Crosswalk.csv | Not modified during product rollback |

Product rollback restores **only** `output/quikplan.csv` (and optional DBF).

---

## Validation After Rollback

1. Row count matches snapshot manifest
2. PLAN uniqueness restored
3. quikridr MPLAN orphan count unchanged (catalog restored)
4. Policy batch pre-flight passes (catalog exists)

---

## Git Discipline (Recommended)

Tag known-good catalog states:

```
product-catalog/v1.0-133rows-20260523
```

Commit emitted `quikplan.csv` to tag (or store in replay snapshot store) for enterprise audit.

Do NOT auto-commit from runner — manual analyst action.

---

## Environment Flag Summary

| Flag | Default | Effect |
|---|---|---|
| `QLA_PRODUCT_SETUP_EMIT` | 0 | Allow write to output/quikplan.csv |
| `QLA_PRODUCT_SETUP_ROLLBACK` | 0 | Restore last snapshot |
| `QLA_PRODUCT_SETUP_ISOLATED` | 0 | Skip quikplan in policy batch |
| `QLA_PRODUCT_GOVERNANCE_BLOCK` | 0 | Block emit on ERROR diagnostics |
| `QLA_PRODUCT_SETUP_GENERATE_DBF` | 0 | Generate quikplan.dbf |
| `QLA_PRODUCTION_DBF_AUTHORIZED` | N | Production DBF gate (existing) |

---

## Recovery Time Objective

| Layer | RTO |
|---|---|
| Staged-only discard | Immediate |
| CSV snapshot restore | < 1 minute |
| Batch isolation disable | Immediate (env flag) |
| Full P2 extraction revert | Git revert app.py + qla_core |
