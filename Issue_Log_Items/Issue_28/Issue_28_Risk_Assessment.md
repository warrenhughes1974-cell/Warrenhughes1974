# Issue #28 — Risk Assessment

**Engine version:** v57.34  
**Planning date:** 2026-06-24  
**Recommended option:** A (with Phase 2 P3E alignment)

---

## Risk register

| ID | Risk | Likelihood | Impact | Severity | Mitigation |
|----|------|------------|--------|----------|------------|
| R-01 | 33 PLAN code changes break rate table lookups | Medium | High | **High** | Re-run rate reconciliation; sample PPBEN policies per changed PLAN |
| R-02 | CSO mortality crosswalk misses new PLAN codes | Medium | Medium | **Medium** | Run CSO QA output review post-batch |
| R-03 | Variation classification (VARGP/VARDB) keyed on old PLAN | Low | Medium | **Medium** | Re-run variation audit; compare 33 plans |
| R-04 | quikridr MPLAN orphan / referential integrity after quikplan fix | Medium | High | **High** | Phase 2: enable P3E after quikplan validated |
| R-05 | Client UAT baseline invalid | Certain | High | **High** | Communicate expected PLAN delta; re-UAT 33 plans + samples |
| R-06 | Catalog regeneration (P2E) reverts manual CSV fixes | Medium | High | **High** | Update generator OR deprecate manual regen; Option A reduces regen dependency |
| R-07 | QLA_Migration/Mapping catalog drift (133 vs 140 rows) | Medium | Low | **Low** | Sync copies in same PR as fix |
| R-08 | DISCHO25 quikplan row missing after fix | Medium | Medium | **Medium** | Explicit catalog add + quikplan completeness check |
| R-09 | DISCHO discount family many-to-one (9DIS25) causes MPLAN collision | Low | Medium | **Medium** | Validate P3E traces for DISCHO25/247C/2475 separately |
| R-10 | FORM column changes scope creep | Low | Medium | **Low** | Keep #28 scoped to PLAN; defer FORM to separate issue if needed |
| R-11 | Regression on protected issues | Low | Critical | **Medium** | Mandatory #25/#26/#21M validators in test plan |
| R-12 | Other conversion projects using compat column | Low | Medium | **Low** | Document authority promotion; compat column retained |

---

## Protected issue impact matrix

| Issue | Touch surface | Option A risk | Option B risk | Option C risk | Notes |
|-------|---------------|---------------|---------------|---------------|-------|
| **#21M** | QUIKMEMO / PNOTE/PENSE | **None** | None | None | No PLAN mapping dependency |
| **#21M-FU** | MEMOKEY merge | **None** | None | None | Orthogonal |
| **#21K** | MUNIT schema widen | **None** | None | None | Companion tooling; not engine |
| **#25** | MPOLICY 10-char pad | **None** | None | None | Re-run width validator |
| **#26** | MPREM ← ANN_PREM_PER_UNIT | **None** | None | None | Re-run MPREM validator |

**Conclusion:** No protected issue code paths require modification for #28 remediation. Regression risk is **validation-only** for those issues.

---

## Product authority (P3C) impact

| Aspect | Current | Post Option A |
|--------|---------|---------------|
| Closed catalog authority column | `crosswalk_ql_plan_code` | Unchanged |
| Runtime emit column | `ql_plan_code` (misaligned) | **Aligned with P3C** |
| `CROSSWALK_DIVERGENT` flags | 33 rows | Can remain as audit trail or flip post-fix |
| Unauthorized emit manifest | Includes DISCHO25 | Should clear after catalog add |

**Risk if not fixing:** P3C analysis and runtime continue to disagree — governance debt accumulates.

---

## MPLAN alignment (P3E) impact

| Aspect | Current | Post Option A only | Post A + P3E |
|--------|---------|-------------------|--------------|
| quikplan PLAN universe | Contains passthrough IDs | Authoritative codes | Authoritative codes |
| P3E resolver intersection | Blocks authoritative MPLAN | **Improved** | **Fully aligned** |
| quikridr default (P3E off) | Passthrough MPLAN | Still passthrough until P3E | Authoritative MPLAN |

**Risk:** Enabling P3E **before** Option A produces UNAUTHORIZED MPLAN (proven in Intake). **Sequence:** quikplan fix first, then P3E.

---

## Client UAT baseline impact

| Baseline artifact | Impact |
|-------------------|--------|
| quikplan.csv from v57.34 batch | **33 PLAN values change** — baseline invalid for plan review |
| quikridr.csv | MPLAN may change in Phase 2 |
| Product setup UAT overlay runs | May already show authoritative PLAN — reconcile with batch path |
| Issue #28 client examples | Must show 1CSIMN, 960CWP, 94PDIS post-fix |

**Risk level:** **High** — client must re-accept product catalog output; expected and desirable.

---

## Other conversion projects

Projects sharing `product_catalog_crosswalk.csv` or `qla_core/product_catalog_authority.py`:

| Impact | Description |
|--------|-------------|
| Shared module change (Option A) | All consumers get authoritative emit — **consistent** |
| Catalog-only (Option C) | Same CSV benefit without module sync |
| Overlay-dependent projects | Option B creates env divergence between projects |

---

## Residual risks after recommended fix

| Residual | Acceptability |
|----------|---------------|
| Rate PLAN_NOT_IN_TARGET for some authoritative codes | Requires rate team review (pre-existing in phase_r3) |
| FORM truncation vs crosswalk form numbers | Out of #28 PLAN scope unless client expands |
| L10 PRE97 crosswalk ID vs L10 OLD naming | Documented in divergent row — authoritative code 1L10OD |

---

## Risk acceptance criteria (for Dependency Gate / Risk Agent)

Proceed to Development when:

1. Client confirms Policy Form Crosswalk 5.22.2026 is binding for **all 33 + DISCHO25** plan codes.
2. Re-UAT scope for 33 plan changes acknowledged.
3. Protected issue validators included in test plan.
4. Rollback path documented (revert function + compat column intact).
