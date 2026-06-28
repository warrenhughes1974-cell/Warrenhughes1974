# Issue #21D — Implementation Strategy

**Date:** 2026-06-27  
**Converter version (baseline):** v57.35  
**Target version (Development):** v57.36+ (increment on app.py change)  
**Status:** Planning only — not authorized for Development until Dependency Gate passes

---

## Overview

Two **independent, sequentially deployable** work packages. Either can roll back without affecting the other.

```
Track A (MDEPINT)          Track B Phase 1 (quikclnt)     Track B Phase 2 (RNA)
     │                              │                              │
     ▼                              ▼                              ▼
 CSO lookup at              Emit missing NAME_IDs          Client re-delivers
 quikdvdp emit              from RNA → quikclnt           RelationshipNameAddress
     │                              │                              │
     └────────── full batch re-run ─┴──────────────────────────────┘
                              validators + UAT
```

---

## Track A — Implementation outline (MDEPINT)

### A.0 Preconditions

- [ ] Dependency Gate PASS
- [ ] Planning sign-off on Option B (CSO plan-aware)
- [ ] Baseline batch output archived (`QLA_Migration/Output/` v57.35)

### A.1 Development tasks

| # | Task | File(s) | Blast radius |
|---|------|---------|--------------|
| A1 | Add CSO rate-percent resolver (or extend existing module) | `qla_core/cso_mortality_crosswalk.py` | Read-only CSV; new helper only |
| A2 | During `quikdvdp` row emit: resolve policy MPLAN; if CSO `nfo_interest_source` is numeric percent, set `MDEPINT` | `app.py`, `QLA_Migration/app.py` | quikdvdp only |
| A3 | Retain rulebook `4.00` as fallback when no CSO numeric rate | `Sync_Rulebook_quikdvdp.csv` (comment only) | None |
| A4 | Bump version to v57.36 | `app.py` header | — |
| A5 | Create validator `validate_issue21d_mdepint.py` | `tools/validators/` | QA only |

### A.2 Validation

| Step | Command / action | Pass criteria |
|------|------------------|---------------|
| 1 | Full batch | Completes without error |
| 2 | `validate_issue21d_mdepint.py` | 2,268 ISWL → MDEPINT=4.50; non-ISWL unchanged |
| 3 | Diff quikdvdp vs baseline | Only MDEPINT column changes on ISWL rows |
| 4 | NFOINT spot check | All 8 ISWL plan templates still NFOINT=A |
| 5 | Client UAT | `010713704C` shows 4.50% Dividend Accum Int Rate |

### A.3 Rollback

Revert app.py to v57.35; re-run batch. No source extract dependency.

---

## Track B — Implementation outline (blank names)

### B.0 Preconditions

- [ ] Dependency Gate PASS
- [ ] RNA re-extract request submitted (Phase 2 — can proceed in parallel)

### B1 — quikclnt referential integrity (converter-only)

| # | Task | File(s) | Blast radius |
|---|------|---------|--------------|
| B1 | Diagnose 14 missing NAME_IDs (NULL ADDRESS_ID hypothesis) | Analysis only | — |
| B2 | Adjust quikclnt source prep: ensure NAME_ID with individual name emits even when ADDRESS_ID null | `app.py` (~5011–5016) | quikclnt (+14 rows max) |
| B3 | Optional post-pass: add quikclid-referenced IDs missing from quikclnt | `app.py` | quikclnt only |
| B4 | Extend golden validator: MPRIMID/MOWNRID must exist in quikclnt when non-blank | `validate_insured_owner_golden.py` | QA |
| B5 | Create `validate_issue21d_blank_names.py` | `tools/validators/` | QA |
| B6 | Bump version (same release as A or separate) | `app.py` | — |

**Expected outcome:** 8 policies with `id_not_in_quikclnt` pattern resolve.

### B2 — RNA re-extract (client-side)

| # | Task | Owner |
|---|------|-------|
| B7 | Deliver `Issue_21D_Blank_Name_Population.csv` to extract team | Conversion team |
| B8 | Re-pull PRELSA for policies with `HAS_IN_IN_QUikCLID=N` | Client / LifePRO |
| B9 | Drop replacement `RelationshipNameAddress_Extract_*.csv` into Source | Client |
| B10 | Re-run full batch | Conversion team |

**Expected outcome:** Policies like `010713704C` gain IN/PO rows → quikclid → rel_map → MPRIMID/MOWNRID populated.

### B3 — Validation

| Step | Pass criteria |
|------|---------------|
| RNA NAME_ID ⊆ quikclnt | 100% for quikclid-referenced IDs |
| Blank-name population | 0 rows (or documented exceptions) |
| MPRIMID='I' | 0 |
| Golden policies | `validate_insured_owner_golden.py` PASS |
| Client UAT | Names on `010713704C`, `010766896C`, `011080481C` |

### B4 — Rollback

| Phase | Rollback |
|-------|----------|
| B1 | Revert app.py quikclnt logic |
| B2 | Restore prior RNA extract file |

---

## Batch execution order (unchanged)

```
quikclnt → quikclid → quikmstr → … → quikdvdp
```

Track B1 must complete **before** quikclid/quikmstr if testing referential integrity in same run. Track A can run in same batch once quikridr/MPLAN available to quikdvdp step.

---

## Release packaging

| Package | Contents | Can ship independently? |
|---------|----------|-------------------------|
| **21D-A** | MDEPINT CSO enrichment + validator | Yes |
| **21D-B1** | quikclnt integrity + validator | Yes |
| **21D-B2** | New RNA extract + batch re-run | Requires client file |

**Recommended client communication:** Ship 21D-A + 21D-B1 together (v57.36); 21D-B2 when extract arrives.

---

## Code areas summary

| Area | Track A | Track B |
|------|---------|---------|
| `app.py` / `QLA_Migration/app.py` | quikdvdp MDEPINT branch | quikclnt emit branch |
| Rulebooks | Comment update only | No change expected |
| `qla_core/cso_mortality_crosswalk.py` | Optional helper | — |
| Validators | New MDEPINT | Extend golden + new blank-name |
| Source extracts | — | RNA replacement (client) |

---

## Client actions checklist

| # | Action | Track | Blocking? |
|---|--------|-------|-----------|
| 1 | Confirm non-ISWL may remain 4.00% until governed | A | Recommended |
| 2 | UAT Dividend Accum Int Rate on ISWL sample | A | Yes for close |
| 3 | RNA re-extract for blank-name policy list | B | Yes for RC-B1 |
| 4 | UAT name display on Issue #21 samples | B | Yes for close |

---

*Implementation strategy complete. Awaiting Dependency Gate before Development.*
