# ISWL QUIKUINT Development Order

**Project:** LifePRO → QLAdmin — QUIKUINT (UL Interest Rates)  
**Issue:** #32 — Phase 5  
**Version baseline:** v57.39  
**Date:** 2026-06-30 (SME gate closure)  
**Mode:** Planning only  
**Readiness:** **READY FOR DEVELOPMENT**

---

## Context

Issue #31 (PR-1 through PR-4) is **CLOSED**. All QUIKUINT SME gates are **CLOSED**.

**Phase 5 target:** QUIKUINT → `QuikUint` (4 fields, plan-level effective-date rows with full history)

---

## Recommended build sequence

```text
Phase 0 — SME confirmation  ✅ COMPLETE

  ✅ QuikUint schema (Help §7.223)
  ✅ Loan interest not on QuikUint
  ✅ MGTDRATE mirrors MCURRATE from A1
  ✅ CENII IDENT for all 8 ISWL MPLANs
  ✅ Emit all historical PDINTTBL tiers (fallback: current tier)

Phase 5 — QUIKUINT  ★ Development Agent target — READY

  ├── Add QuikUint to rate_dbf_schema (Help §7.223)
  ├── New pdint_uint_loader.py — CENII/A1 full history + MGTDRATE mirror
  ├── Wire iswl_phase5 in rate_loader_config.json
  ├── PSEGT A1 gate (8/8)
  ├── Emit union merge: DINT_RULE 0 + 3 tiers → 4 START_DATEs/MPLAN
  ├── Dry-run: 32 rows (8 × 4 unique tiers); fallback 8 rows
  └── Validator iswl_quikuint_reconcile.py (V-UINT-01–08)

Phase 5b — CSV emit (after validation PASS)

  ├── rate_loader_emit.py --csv-only includes QuikUint.csv
  ├── Issue #31 regression unchanged
  └── Artifacts under Issue_Log_Items/Issue_32/output/Phase5_QUIKUINT/

Phase 6 — Loan interest (separate PR)

  └── quikplan.LOANINT + QuikPlSt.MLOANINT / MLOANINTX
```

---

## Complexity summary

| Table | Complexity | Phase | Source rows | Output rows | MPLAN coverage |
|-------|------------|-------|-------------|-------------|----------------|
| QUIKUINT | **Medium–High** | 5 | 10 PDINT + 37 PDINTTBL | **32** (union merge) | 8/8 |

---

## Files to modify (Phase 5)

| File | Change type |
|------|-------------|
| `qla_core/pdint_uint_loader.py` | **New** |
| `qla_core/rate_dbf_schema.py` | Add `QuikUint` layout |
| `qla_core/rate_pipeline.py` | Wire uint stream |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | `iswl_phase5` block |
| `plan_analysis/phase_r5_rate_loader/rate_loader_emit.py` | Include QuikUint CSV |
| `tools/validators/iswl_quikuint_reconcile.py` | **New** |
| `tools/validators/iswl_common.py` | Phase 5 output paths |

---

## Development Agent readiness

| Phase | Target | Status |
|-------|--------|--------|
| 0 | SME confirmation | **COMPLETE** |
| 5 | QUIKUINT (PR-5) | **READY FOR DEVELOPMENT** |
| 5b | CSV emit | After Phase 5 validation PASS |
| 6 | Loan interest | Separate track |

**Launch prompt:** [`ISWL_QUIKUINT_Next_Stage_Prompt.md`](ISWL_QUIKUINT_Next_Stage_Prompt.md)

---

## Methodology alignment (Issue #31)

```text
Research → Architecture → Blueprint → Development → Validation → Regression → CSV Emit → Closeout
```

Planning complete through **Blueprint**. **Development Agent may start PR-5.**
