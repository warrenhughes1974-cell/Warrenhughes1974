# Issue #28 — Release Checklist

**Version:** v57.35  
**Date:** 2026-06-27  
**Release type:** Issue #28 — PLAN mapping correction

---

## Code & data readiness

| # | Item | Status | Evidence |
|---|------|--------|----------|
| R-01 | Version v57.35 in `app.py` | ✅ | Header + UI + batch log |
| R-02 | Version v57.35 in `QLA_Migration/app.py` | ✅ | Mirrored |
| R-03 | Phase 1 authority promotion | ✅ | `product_catalog_authority.py` |
| R-04 | Phase 0 DISCHO25 catalog row | ✅ | 141 data rows |
| R-05 | Catalog governance = migration sync | ✅ | Byte-identical files |
| R-06 | Phase 2 P3E default ON | ✅ | Env default + batch refresh |
| R-07 | Issue #28 validator present | ✅ | `tools/validators/validate_issue28_plan_mapping.py` |

---

## Validation readiness

| # | Item | Status | Evidence |
|---|------|--------|----------|
| R-08 | Full batch v57.35 | ✅ | Exit 0 (~814s) |
| R-09 | 141/141 PLAN match | ✅ | Intake + validator |
| R-10 | 33 corrections exact | ✅ | `evidence/v57.35_quikplan_plan_diff.csv` |
| R-11 | Client examples | ✅ | 1CSIMN, 960CWP, 94PDIS |
| R-12 | DISCHO25 emit | ✅ | PLAN=9DIS25 |
| R-13 | P3E MPLAN alignment | ✅ | 7002 AUTHORIZED, 0 orphans |
| R-14 | Output delta clean | ✅ | FORM/DESCR unchanged |

---

## Protected issue regression

| # | Issue | Status | Re-run (2026-06-27) |
|---|-------|--------|---------------------|
| R-15 | #25 MPOLICY width | ✅ PASS | `validate_mpolicy_width.py` |
| R-16 | #26 MPREM | ✅ PASS | `validate_issue26_mprem.py` |
| R-17 | #21M QUIKMEMO | ✅ PASS | `validate_issue21m_quikmemo.py` |
| R-18 | #21M-FU DBF | ✅ PASS | `validate_issue21m_dbf_packaging.py` |
| R-19 | #21K MUNIT CSV | ✅ PASS | CSV precision |
| R-20 | #21K DBF reload | ⚠️ SKIP | Manual script not in batch |

---

## Documentation & artifacts

| # | Artifact | Status |
|---|----------|--------|
| R-21 | Development deliverables | ✅ |
| R-22 | Validation deliverables | ✅ |
| R-23 | Regression & deployment deliverables | ✅ (this release) |
| R-24 | Rollback checklist | ✅ `Issue_28_Rollback_Checklist.md` |
| R-25 | Client UAT package | ✅ `Issue_28_Client_UAT_Package.md` |
| R-26 | Evidence archive | ✅ `Issue_Log_Items/Issue_28/evidence/` |

---

## Blockers & gates

| ID | Item | Staging | Production |
|----|------|---------|------------|
| B-01 | Crosswalk binding | ✅ Resolved (per Validation) | ✅ |
| B-02 | Client re-UAT scope | ⬜ Pending | **BLOCKS** |
| B-03 | DISCHO25 catalog | ✅ Resolved | ✅ |
| B-05 | Catalog sync | ✅ Resolved | ✅ |
| V-16 | Rate review | ⚠️ Observation | **BLOCKS** |

---

## Release sign-off matrix

| Environment | Recommendation | Rationale |
|-------------|----------------|-----------|
| **Staging / UAT** | **READY FOR CLIENT UAT** | All technical gates pass |
| **Limited release** | **READY FOR LIMITED RELEASE** | Same as UAT with controlled policy set |
| **Production** | **NOT READY** | B-02 + V-16 + Client UAT pending |

---

## Final checklist for release manager

- [ ] v57.35 tagged in version control
- [ ] Staging batch output archived
- [ ] Client UAT package delivered
- [ ] Operations briefed on env vars and rollback
- [ ] Rate team notified of 33 PLAN code changes
- [ ] Client UAT scheduled (B-02 acceptance)
- [ ] Production GO held until Client UAT PASS
