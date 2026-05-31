# Recommended Product Runner Architecture

## Design Goal

app.py v55.7 remains an **orchestration wrapper / launcher / governance controller**. Complex product logic must NOT be inlined into app.py.

## Proposed Tab: "Product Setup Conversion"

### UI Responsibilities (app.py — minimal)

- Path pickers: `quikplan_source.csv`, Policy Form Crosswalk, PCOMP, output targets
- Launch button → subprocess runner
- Display governance summary counts (held / staged / emitted)
- Rollback toggle: `QLA_PRODUCT_GOVERNANCE_HOLD`
- No field-level transformation logic in app.py

### Subprocess Runner (isolated)

```
plan_governance/phase_p2_product_runner/product_setup_runner.py
```

Pipeline stages:
1. **Load** — read `plan_analysis/quikplan_source.csv` (never `output/quikplan.csv`)
2. **Crosswalk Join** — Policy Form Crosswalk on confirmed join key (TBD in P1C)
3. **Rulebook Transform** — `Sync_Rulebook_quikplan.csv` field routing
4. **PCOMP Lookup** — MINUNIT/MAXUNIT joins
5. **Semantic Governance** — classification holds (no auto-fix)
6. **Dependency Check** — quikridr MPLAN orphan detection
7. **Stage** — write `plan_governance/staged/quikplan_staged.csv`
8. **Validate** — key_definitions PLAN uniqueness, schema order
9. **Manifest** — append holds to `product_review_hold_manifest.csv`
10. **Emit** ( gated ) — copy cleared rows to `output/quikplan.csv`

### Isolation Boundaries

| Concern | Product Runner | Policy/Claims Batch |
|---|---|---|
| Source | plan_analysis/quikplan_source.csv | QLA_Migration/Source/* |
| Crosswalk | Policy Form Crosswalk 5.22.26 | Master_Crosswalk (policy only) |
| Holds manifest | product_review_hold_manifest.csv | claims_review_hold_manifest.csv |
| Logs | plan_governance/logs/ | claims_analysis logs |
| Replay | plan_governance/replay/ | claims phase15 replay |

### Dependency Validation Subprocess

Before emit, runner validates:
- Every distinct `quikridr.MPLAN` exists in staged `quikplan.PLAN`
- No duplicate PLAN keys
- FORM present when crosswalk specifies form
- PLANTYPE / HRIGPKEY holds enforced (future phase)

### Execution Command Pattern

```bash
python plan_governance/phase_p2_product_runner/product_setup_runner.py   --source plan_analysis/quikplan_source.csv   --crosswalk "docs/plan_conversion_reference/Policy Form Crosswalk 5.22.26.xlsx"   --rulebook QLA_Migration/Configs/Sync_Rulebook_quikplan.csv   --pcomp plan_analysis/PCOMP.csv   --ridr QLA_Migration/Output/quikridr.csv   --stage-dir plan_governance/staged   --manifest plan_governance/manifests/product_review_hold_manifest.csv   --hold-mode 1
```

app.py invokes this via `subprocess.run` with captured stdout → UI log panel.

## Why Subprocess Isolation

1. **Rollback safety** — product experimentation cannot destabilize claims v55.7 batch path
2. **Audit clarity** — separate logs/manifests per domain
3. **Business review** — product team can rerun without full policy conversion
4. **Determinism** — frozen source + versioned crosswalk + manifest = reproducible lineage

## Integration Point in app.py (future — NOT this phase)

```python
# Pseudocode only — do not implement in P1B
if product_tab_run_requested:
    subprocess.run([sys.executable, PRODUCT_RUNNER, *args], check=False)
    self._load_product_governance_summary()
```

## Regression Risks if NOT Isolated

- Master_Crosswalk plan/policy collision affects claims MPOLICY and plan MPLAN simultaneously
- Silent PLAN remap breaks quikridr orphan detection
- HRIGPKEY premature population blocks actuarial review cycles
