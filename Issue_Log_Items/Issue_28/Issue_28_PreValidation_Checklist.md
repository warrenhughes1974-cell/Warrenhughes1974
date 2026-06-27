# Issue #28 — Pre-Validation Checklist

**Development complete:** 2026-06-24  
**Engine version:** v57.35  
**Stage:** Development → Validation handoff

---

## Development completion checklist

| # | Item | Status |
|---|------|--------|
| D-01 | Phase 0 — DISCHO25 row in governance catalog | ✅ |
| D-02 | Phase 0 — Migration catalog synced (141 data rows) | ✅ |
| D-03 | Phase 1 — `load_product_catalog_crosswalk()` authority promotion | ✅ |
| D-04 | Phase 2 — P3E default enabled | ✅ |
| D-05 | Phase 2 — Post-quikplan resolver refresh (batch) | ✅ |
| D-06 | Version bumped to v57.35 (`app.py` + `QLA_Migration/app.py`) | ✅ |
| D-07 | Protected issue code paths untouched | ✅ |
| D-08 | Python syntax check passed | ✅ |
| D-09 | Runtime spot-check: 10827 MN5K→1CSIMN, DISCHO25→9DIS25 | ✅ |
| D-10 | Development deliverables created | ✅ |
| D-11 | Batch re-run executed | ⬜ **Validation Agent** |
| D-12 | Validator suite executed | ⬜ **Validation Agent** |

---

## Preconditions for Validation Agent

- [ ] Use v57.35 code (verify header in `app.py`)
- [ ] Confirm `plan_governance/product_catalog_crosswalk.csv` row count = 141 data rows
- [ ] Confirm governance and migration catalog files are identical
- [ ] Full batch re-run required — v57.34 output is invalid baseline for PASS
- [ ] B-02 (re-UAT scope) still open — blocks Release only, not Validation

---

## Validation Agent must execute (see Validation Matrix)

| Priority | ID | Procedure |
|----------|-----|-----------|
| P0 | V-01 | `_issue28_intake_analysis.py` → mismatches: 0 |
| P0 | V-02 | `validate_issue28_plan_mapping.py` → 141/141 match |
| P0 | V-03 | Client examples: 1CSIMN, 960CWP, 94PDIS |
| P0 | V-04 | `validate_output.py` schema check |
| P0 | V-05 | `_run_full_batch_test.py` |
| P0 | V-06–V-09 | Protected issue validators (#25, #26, #21M, #21M-FU) |
| P0 | V-11 | DISCHO25 PLAN=9DIS25 in quikplan |
| P1 | V-12–V-13 | P3E MPLAN alignment + referential integrity |
| P1 | V-14–V-16 | Variation audit, CSO, rate sample |

---

## Environment notes for Validation

| Variable | v57.35 default | Override |
|----------|----------------|----------|
| `QLA_CLOSED_MPLAN_AUTHORITY` | **1** (enabled) | Set `0` to disable P3E |
| `QLA_ALLOW_LEGACY_MPLAN_FALLBACK` | 0 | Unchanged |
| `CROSSWALK_OVERLAY` | 0 | Unchanged |

---

## Evidence to archive (Validation Agent)

```
Issue_Log_Items/Issue_28/evidence/
  ├── v57.34_quikplan_plan_snapshot.csv (if not already archived)
  ├── v57.35_quikplan_plan_diff.csv
  ├── validate_issue28_results.txt
  └── protected_issue_validator_results.txt
```

---

## Fail-fast criteria

Stop Validation and escalate if:

- Any protected issue validator FAIL
- Issue #28 validator shows >33 expected PLAN changes (unexpected drift)
- quikplan row count or schema integrity regression
- P3E trace shows UNAUTHORIZED for remediated PLAN_CODEs after batch
