# Issue #21D — Rollback Strategy

**Date:** 2026-06-27  
**Converter version (baseline):** v57.35  
**Target version (Development):** v57.36+  
**Scope:** Track A + Track B1 independent rollback paths  
**Principle:** Tracks deploy together but roll back independently

---

## 1. Rollback overview

| Track | Revert surface | Source dependency | Re-batch required |
|-------|----------------|-------------------|-------------------|
| **Track A** | app.py MDEPINT branch + optional CSO helper | None | Yes |
| **Track B1** | app.py quikclnt emit logic | None | Yes |
| **Track B2** | Restore prior RNA extract | Client file | Yes |
| **Full #21D** | Revert A + B1 code; restore RNA if B2 applied | Optional RNA | Yes |

**Baseline preservation:** Archive v57.35 `QLA_Migration/Output/` before Development merge.

---

## 2. Track A rollback — MDEPINT

### 2.1 Trigger conditions

| Condition | Action |
|-----------|--------|
| Non-ISWL policies show MDEPINT 4.50 | **Immediate rollback** |
| ISWL count < 2,268 at 4.50 | Investigate; rollback if logic error |
| NFOINT regression detected | Rollback Track A changes |
| Client UAT fails on rate display | Hold release; rollback if logic defect confirmed |
| Protected-issue validator failure caused by A change | Rollback |

### 2.2 Rollback steps

| Step | Action | Owner |
|------|--------|-------|
| A-RB-1 | Revert `app.py` and `QLA_Migration/app.py` to v57.35 (or remove MDEPINT enrichment block only) | QLAdmin |
| A-RB-2 | Revert `qla_core/cso_mortality_crosswalk.py` if rate-percent helper added | QLAdmin |
| A-RB-3 | Revert rulebook comment on `Sync_Rulebook_quikdvdp.csv` if changed | QLAdmin |
| A-RB-4 | Remove or disable `validate_issue21d_mdepint.py` from release gate | QLAdmin |
| A-RB-5 | Re-run full batch from v57.35 code | QLAdmin |
| A-RB-6 | Verify: all 5,083 MDEPINT = 4.00 | QLAdmin |
| A-RB-7 | Document rollback in issue log | QLAdmin |

### 2.3 Rollback verification

```text
PASS: validate_issue21d_mdepint.py not applicable (reverted)
PASS: MDEPINT distribution matches v57.35 baseline
PASS: NFOINT unchanged
PASS: Protected-issue validators PASS
```

### 2.4 Partial rollback

Not applicable — Track A is atomic (single enrichment branch). Cannot partially roll back ISWL-only in production without code change.

---

## 3. Track B1 rollback — quikclnt integrity

### 3.1 Trigger conditions

| Condition | Action |
|-----------|--------|
| Duplicate MCLIENTID in quikclnt | **Immediate rollback** |
| MPRIMID='I' leak (count > 0) | **Immediate rollback** |
| quikclnt row explosion (> +20 rows) | Investigate; rollback if unbounded emit |
| QLAdmin rejects NULL-address clients fleet-wide | Hold release; assess rollback |
| Wrong names on sample policies | Rollback if logic defect (not RNA data issue) |

### 3.2 Rollback steps

| Step | Action | Owner |
|------|--------|-------|
| B1-RB-1 | Revert quikclnt source prep changes in `app.py` / `QLA_Migration/app.py` (~5011–5016) | QLAdmin |
| B1-RB-2 | Revert optional quikclid-referenced post-pass if added | QLAdmin |
| B1-RB-3 | Revert `validate_insured_owner_golden.py` extensions | QLAdmin |
| B1-RB-4 | Remove or disable `validate_issue21d_blank_names.py` from gate | QLAdmin |
| B1-RB-5 | Re-run full batch from reverted code | QLAdmin |
| B1-RB-6 | Verify: 14 missing NAME_IDs restored; 25 blank-name population | QLAdmin |
| B1-RB-7 | Document rollback | QLAdmin |

### 3.3 Rollback verification

```text
PASS: quikclnt row count matches v57.35 baseline
PASS: 14 RNA IDs missing from quikclnt (restored state)
PASS: MPRIMID='I' = 0
PASS: validate_insured_owner_golden.py PASS (baseline expectations)
```

### 3.4 Partial rollback

Track B1 is atomic. If combined A+B1 release fails B1-only, revert B1 code while retaining Track A (independent code paths).

---

## 4. Track B2 rollback — RNA extract

**Not Development scope.** Documented for operational completeness.

| Step | Action |
|------|--------|
| B2-RB-1 | Restore prior `RelationshipNameAddress_Extract_*.csv` from archive |
| B2-RB-2 | Re-run batch on v57.36+ code (or v57.35 if full revert) |
| B2-RB-3 | Verify blank-name population returns to pre-B2 state |

---

## 5. Combined release rollback decision tree

```
                    Release issue detected
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
         MDEPINT wrong    quikclnt dup     Both / unclear
              │               │               │
         Rollback A      Rollback B1     Rollback both
              │               │               │
              └───────────────┴───────────────┘
                              │
                    Re-batch v57.35 or partial revert
                              │
                    Protected-issue validators PASS
                              │
                    Client notified + issue log updated
```

---

## 6. Git / version rollback

| Item | Procedure |
|------|-----------|
| Code | `git revert` commit(s) for v57.36 Issue #21D changes, or checkout v57.35 tag/commit |
| Version header | Restore `v57.35` in app.py header |
| Output artifacts | Do not overwrite v57.35 archive; write rollback output to separate folder |
| Validators | Keep validator scripts in repo but mark inactive in release gate |

---

## 7. Communication template (rollback)

| Audience | Message |
|----------|---------|
| Client | Issue #21D v57.36 release rolled back to v57.35 for [Track A / B1 / both]. [Reason]. B2 RNA action unchanged. |
| Internal | Rollback steps A-RB/B1-RB completed; baseline verified; re-Development scheduled after root-cause fix. |

---

## 8. Rollback readiness checklist (pre-Development)

| Item | Status |
|------|--------|
| v57.35 output archived | Required before Dev |
| Git tag or commit hash for v57.35 recorded | Required |
| Rollback owner assigned (QLAdmin) | Default: conversion team |
| Client partial-fix messaging prepared | Required for B1 |

---

*Rollback strategy approved by Risk Agent. Independent per-track revert preserves rollback safety per AGENTS.md.*
