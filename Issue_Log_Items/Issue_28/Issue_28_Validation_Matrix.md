# Issue #28 — Validation Matrix

**Risk analysis date:** 2026-06-24  
**Applies after:** Development v57.35 (Phase 0 + Phase 1 minimum)

---

## Validation matrix

| ID | Domain | Validator / procedure | Owner | Phase | Pass criteria | Priority |
|----|--------|----------------------|-------|-------|---------------|----------|
| V-01 | Crosswalk | `_issue28_intake_analysis.py` | Validation | Post-batch | `mismatches: 0` | **P0** |
| V-02 | PLAN mapping | `_validate_issue28_plan_mapping.py` (new) | Development → Validation | Post-batch | 141/141 authoritative match | **P0** |
| V-03 | Client examples | Manual / scripted spot check | Validation + Client | UAT | 1CSIMN, 960CWP, 94PDIS | **P0** |
| V-04 | quikplan schema | `validate_output.py` | Validation | Post-batch | No schema drift | **P0** |
| V-05 | Full batch | `_run_full_batch_test.py` | Validation | Post-batch | Completes without error | **P0** |
| V-06 | MPOLICY width | `validate_mpolicy_width.py` | Regression | Post-batch | #25 PASS | **P0** |
| V-07 | MPREM | `validate_issue26_mprem.py` | Regression | Post-batch | #26 PASS | **P0** |
| V-08 | QUIKMEMO | `validate_issue21m_quikmemo.py` | Regression | Post-batch | #21M PASS | **P0** |
| V-09 | MEMOKEY merge | `validate_issue21m_dbf_packaging.py` | Regression | Post-batch | #21M-FU PASS | **P0** |
| V-10 | MUNIT | `validate_issue21k_munit.py` | Regression | Post-batch | #21K PASS (env) | P1 |
| V-11 | DISCHO25 | Catalog + quikplan row check | Validation | Post-batch | PLAN=9DIS25 emitted | **P0** |
| V-12 | MPLAN (Phase 2) | P3E trace sample | Validation | Post-P3E | Auth MPLAN on sample riders | P1 |
| V-13 | MPLAN referential | quikridr MPLAN ∈ quikplan.PLAN | Validation | Post-P3E | 0 orphan auth MPLAN | P1 |
| V-14 | Variation audit | `variation_code_audit.csv` diff | Validation | Post-batch | Review 33 plan keys | P1 |
| V-15 | CSO crosswalk | `cso_mortality_crosswalk_qa.csv` | Validation | Post-batch | Review missing plans | P1 |
| V-16 | Rate reconciliation | Sample per changed PLAN | Risk/Rate team | Pre-production | Document PLAN_NOT_IN_TARGET | P1 |
| V-17 | Golden policies | `validate_insured_owner_golden.py` (if in scope) | Validation | Post-batch | No unrelated drift | P2 |
| V-18 | Product catalog CSV | Row count 141; no blank auth column | Validation | Post-dev | Governance = migration copy | P1 |
| V-19 | P3C diagnostics | Unauthorized emit manifest | Validation | Post-batch | 33 cleared | P1 |
| V-20 | Before/after diff | `Issue_28_Mapping_Differences.csv` regen | Validation | Post-batch | Archive in evidence/ | P1 |

---

## Execution order

```
1. Development completes Phase 0 + 1 → v57.35
2. Full batch re-run
3. V-01, V-02, V-04, V-05 (core #28)
4. V-06 through V-09 (protected issues — mandatory)
5. V-11, V-18, V-19
6. V-14, V-15, V-16 (downstream — before production)
7. Phase 2 optional → V-12, V-13
8. Client UAT V-03 (B-02)
```

---

## Sample policy validation (minimum set)

| Policy / product | Validation focus |
|------------------|------------------|
| Any policy with 10827 MN5K | quikplan PLAN=1CSIMN |
| Any policy with 0823 960CH | quikplan PLAN=960CWP; quikridr MPLAN (Phase 2) |
| Any policy with 0824 P DIS | quikplan PLAN=94PDIS |
| Policy with 8046 JPO (10 rows) | High-touch rider product |
| Policy with DISCHO247C | MPLAN 9DS24C vs compat 9DIS25 |
| PUA policy (621/961/970 PUA) | PUA inheritance if Phase 2 enabled |

Source: `Issue_28_Policy_Impact_Summary.csv`

---

## Golden / regression baseline

| Baseline artifact | Location | Use |
|-------------------|----------|-----|
| v57.34 quikplan.csv | `QLA_Migration/Output/` | Before-state PLAN diff |
| v57.34 Mapping Differences | `Issue_28_Mapping_Differences.csv` | 33-row expected changes |
| v57.34 release validators | Release notes | Expected PASS counts |

New baseline required post-fix for Issue #28 closure — not a pre-development blocker.

---

## Fail actions

| Fail type | Action |
|-----------|--------|
| V-02 mismatch | Do not release; debug authority loader |
| V-06–V-09 fail | **Stop** — rollback; protected issue regression |
| V-16 rate gaps | Escalate to rate team; may HOLD production |
| Client UAT fail (V-03) | Rollback or targeted fix |
