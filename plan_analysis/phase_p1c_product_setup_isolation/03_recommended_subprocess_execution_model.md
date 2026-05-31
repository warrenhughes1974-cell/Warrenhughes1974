# Recommended Subprocess Execution Model (Phase P1C)

## Pattern Reference

Mirror the proven **Phase 21B claims UAT DBF** subprocess pattern in app.py:

- app.py launches external Python script via `subprocess.run`
- Captures stdout/stderr to UI log
- Parses structured status lines from stdout
- Writes manifest + summary from subprocess results
- Never inlines complex logic in app.py

Product setup follows the same orchestration contract.

---

## Subprocess Entry Point

```
plan_governance/phase_p2_product_setup_runner/product_setup_runner.py
```

### CLI Interface (Proposed)

```bash
python product_setup_runner.py \
  --source plan_analysis/quikplan_source.csv \
  --crosswalk "docs/plan_conversion_reference/Policy Form Crosswalk 5.22.26.xlsx" \
  --rulebook QLA_Migration/Configs/Sync_Rulebook_quikplan.csv \
  --pcomp plan_analysis/PCOMP.csv \
  --translation QLA_Migration/Mapping/Master_Value_Translation.csv \
  --plan-crosswalk QLA_Migration/Mapping/Master_Crosswalk.csv \
  --output-dir QLA_Migration/Output \
  --stage-dir plan_governance/staged \
  --manifest-dir plan_governance/manifests \
  --ridr-reference QLA_Migration/Output/quikridr.csv \
  --emit 0 \
  --generate-dbf 0 \
  --production-dbf-flag N
```

### Environment Flags

| Flag | Default | Purpose |
|---|---|---|
| `QLA_PRODUCT_SETUP_EMIT` | `0` | `1` = copy staged to output/quikplan.csv |
| `QLA_PRODUCT_SETUP_GENERATE_DBF` | `0` | `1` = generate quikplan.dbf from emitted CSV |
| `QLA_PRODUCT_GOVERNANCE_BLOCK` | `0` | `1` = block emit on ERROR diagnostics |
| `QLA_PRODUCT_SETUP_ROLLBACK` | `0` | `1` = restore prior snapshot, skip transform |

---

## Execution Flow

```
┌─────────────┐
│   START     │
└──────┬──────┘
       ▼
┌─────────────────────┐     yes    ┌──────────────────┐
│ Rollback flag set?  │───────────►│ Restore snapshot │
└─────────┬───────────┘            │ Exit SUCCESS     │
          │ no                     └──────────────────┘
          ▼
┌─────────────────────┐
│ Snapshot current    │  (if output/quikplan.csv exists)
│ quikplan.csv        │
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ Load source +       │
│ crosswalk +         │
│ rulebook + lookups  │
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ convert_quikplan()  │  ← shared qla_core module (same as app.py)
│ rulebook engine     │
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ Crosswalk overlay   │  PLAN/FORM/DESCR/PLANNAME enrichment
│ (business authority)│
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ Write staged CSV    │  plan_governance/staged/quikplan_staged.csv
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ Run diagnostics     │  Additive — append to diagnostics CSV
│ (governance engine) │
└─────────┬───────────┘
          ▼
┌─────────────────────┐     no     ┌──────────────────┐
│ Emit enabled AND    │───────────►│ STAGED_ONLY exit │
│ no blocking errors? │            │ (success)        │
└─────────┬───────────┘            └──────────────────┘
          │ yes
          ▼
┌─────────────────────┐
│ Copy to output/     │  quikplan.csv
│ quikplan.csv        │
└─────────┬───────────┘
          ▼
┌─────────────────────┐     no     ┌──────────────────┐
│ Generate DBF?       │───────────►│ DONE             │
└─────────┬───────────┘            └──────────────────┘
          │ yes
          ▼
┌─────────────────────┐
│ quikplan_dbf_gen    │  From emitted CSV only
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ Write manifests +   │
│ stdout status lines │
└─────────────────────┘
```

---

## Structured Stdout (for app.py parsing)

```
PRODUCT_SETUP_STATUS: SUCCESS
SOURCE_ROWS: 133
STAGED_ROWS: 133
EMITTED_ROWS: 133
UNIQUE_PLAN: 132
DIAGNOSTIC_WARNINGS: 94
DIAGNOSTIC_ERRORS: 1
ORPHAN_MPLAN_COUNT: 7
MANIFEST_PATH: plan_governance/manifests/product_setup_run_manifest.csv
STAGED_PATH: plan_governance/staged/quikplan_staged.csv
EMITTED_PATH: QLA_Migration/Output/quikplan.csv
ROLLBACK_SNAPSHOT: plan_governance/replay/snapshots/quikplan_20260523_143022.csv
RULEBOOK_LINEAGE: Sync_Rulebook_quikplan.csv
```

DBF stage (optional):

```
QUIKPLAN_CSV_ROWS: 133
QUIKPLAN_DBF_ROWS: 133
QUIKPLAN_ROW_MATCH: Y
```

---

## app.py Subprocess Hook (Future — Minimal)

Pseudocode only (P2 implementation):

```python
def _invoke_product_setup_runner(self):
    runner = os.path.join(ROOT, "plan_governance", "phase_p2_product_setup_runner",
                          "product_setup_runner.py")
    result = subprocess.run(
        [sys.executable, runner, *self._product_setup_runner_args()],
        capture_output=True, text=True, timeout=120,
    )
    self._log_subprocess_stream("product-setup-stdout", result.stdout)
    self._parse_product_setup_stdout(result.stdout)
    return result.returncode == 0
```

app.py adds ~40 lines (launcher + parser + status panel) — no transformation logic.

---

## Timeout and Error Handling

- Default timeout: 120 seconds (133-row catalog — ample margin)
- Non-zero exit code: app.py shows ERROR status; does not overwrite output
- Partial staged file: valid for business review even if emit blocked
- Subprocess crash: rollback snapshot remains available

---

## Determinism Requirements

Each run manifest must record:

- SHA256 of source file
- Crosswalk filename + modification date
- Rulebook path
- Git commit hash (optional)
- Python version
- `production_dbf_flag=N`

Identical inputs → identical staged output (required for replay audit).
