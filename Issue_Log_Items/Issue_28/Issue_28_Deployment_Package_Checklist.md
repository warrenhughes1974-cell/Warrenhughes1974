# Issue #28 — Deployment Package Checklist

**Version:** v57.35  
**Issue:** #28 — CLOSED  
**Date:** 2026-06-27

---

## Pre-deploy

- [ ] Confirm Git branch contains commit `Release v57.35 - close Issue #28 plan mapping authority`
- [ ] Verify `app.py` header shows v57.35
- [ ] Verify catalog files identical (governance ↔ migration)
- [ ] Archive v57.34 output baseline (if not already in `Issue_28/evidence/`)

---

## Deploy files

- [ ] `app.py`
- [ ] `QLA_Migration/app.py`
- [ ] `qla_core/product_catalog_authority.py`
- [ ] `plan_governance/product_catalog_crosswalk.csv`
- [ ] `QLA_Migration/Mapping/product_catalog_crosswalk.csv`
- [ ] `tools/validators/validate_issue28_plan_mapping.py`

---

## Environment

- [ ] `QLA_CLOSED_MPLAN_AUTHORITY=1` (default — confirm not overridden to 0)
- [ ] `CROSSWALK_OVERLAY=0`
- [ ] `QLA_RUN_MODE=UAT` (or production equivalent)

---

## Post-deploy batch

- [ ] Run `python tools/batch_tests/run_full_batch_test.py`
- [ ] Confirm exit code 0
- [ ] Confirm quikplan 141 rows, quikridr 7002 rows

---

## Post-deploy validation

- [ ] `python tools/validators/validate_issue28_plan_mapping.py` → PASS
- [ ] `python tools/validators/validate_mpolicy_width.py` → PASS
- [ ] `python tools/validators/validate_issue26_mprem.py` → PASS
- [ ] `python tools/validators/validate_issue21m_quikmemo.py` → PASS
- [ ] `python tools/validators/validate_issue21m_dbf_packaging.py` → PASS
- [ ] Client examples: 1CSIMN, 960CWP, 94PDIS, 9DIS25

---

## Production gates (if applicable)

- [ ] Rate team sign-off (V-16)
- [ ] Operations deployment window
- [ ] CAB approval (if required)
- [ ] Optional #21K DBF reload

---

## Rollback ready

- [ ] v57.34 code tag available
- [ ] `Issue_28_Rollback_Checklist.md` accessible to ops

---

**Package complete when all deploy + validation items checked.**
