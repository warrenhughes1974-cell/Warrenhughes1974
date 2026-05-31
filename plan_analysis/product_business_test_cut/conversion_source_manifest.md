# v57.3 Product Business Test Cut — Conversion Source & Output Manifest

Use **`QLA_Migration/`** paths in the GUI (app defaults). Root copies of `Master_Crosswalk.csv` and `Master_Value_Translation.csv` are kept in sync with `QLA_Migration/Mapping/`.

---

## A. Configuration files (required)

| File | Path | Role |
|------|------|------|
| Rulebooks (14 tables) | `QLA_Migration/Configs/Sync_Rulebook_<table>.csv` | Field mapping per QLA table |
| Master crosswalk | `QLA_Migration/Mapping/Master_Crosswalk.csv` | Policy + legacy product ID crosswalk |
| Value translation | `QLA_Migration/Mapping/Master_Value_Translation.csv` | Code/value translations |
| Product catalog (P3C) | `plan_governance/product_catalog_crosswalk.csv` | Authoritative 140-plan closed catalog |
| Policy form crosswalk (optional overlay) | `docs/plan_conversion_reference/Policy Form Crosswalk 5.22.26.xlsx` | UAT product overlay when enabled |

### Rulebook inventory

| Table | Rulebook file |
|-------|----------------|
| quikplan | `Sync_Rulebook_quikplan.csv` |
| quikmstr | `Sync_Rulebook_quikmstr.csv` |
| quikclnt | `Sync_Rulebook_quikclnt.csv` |
| quikclid | `Sync_Rulebook_quikclid.csv` |
| quikridr | `Sync_Rulebook_quikridr.csv` |
| quikbenf | `Sync_Rulebook_quikbenf.csv` |
| quikagts | `Sync_Rulebook_quikagts.csv` |
| quikdvdp | `Sync_Rulebook_quikdvdp.csv` |
| quikdvpr | `Sync_Rulebook_quikdvpr.csv` |
| quikprmh | `Sync_Rulebook_quikprmh.csv` |
| quikactg | `Sync_Rulebook_quikactg.csv` |
| quikclms | `Sync_Rulebook_quikclms.csv` |
| quikclmp | `Sync_Rulebook_quikclmp.csv` |

---

## B. LifePRO source files — full batch conversion

Point **Source Data File** at any file in `QLA_Migration/Source/`; batch mode locks that folder for all tables.

### Primary source CSV (one per converted table)

| Output table | LifePRO source file | Notes |
|--------------|---------------------|-------|
| **quikclnt** | `quikclnt.csv` | Run first (priority) |
| **quikclid** | `quikclid.csv` | Run second; also used as Relational File |
| **quikmstr** | `quikmstr.csv` | Uses PPBENTYP extract for MNFOPT/MDIVOPT |
| **quikbenf** | `quikbenf.csv` | Uses `quikclid.csv` relational join |
| **quikridr** | `PPBEN.csv` | P3E MPLAN authority applied when enabled |
| **quikagts** | `PAGNT.csv` | Looks up agent name/address from emitted quikclnt |
| **quikdvdp** | `PPBENTYP.csv` | Dividend deposit |
| **quikprmh** | `PACTG_Accounting_Extract20260427.csv` | Premium history |
| **quikdvpr** | `PACTG_Accounting_Extract20260427.csv` | Dividend premium (filtered) |
| **quikactg** | `PACTG_Accounting_Extract20260427.csv` | Accounting crosswalk |

### Supporting source files (same folder)

| File | Used by |
|------|---------|
| `RelationshipNameAddress_Extract.csv` | quikclnt / quikclid name & address enrichment |
| `PPBENTYP.csv` | quikmstr MNFOPT/MDIVOPT auto-load |
| `PPACH.csv` | quikmstr banking (MBANKNO) |
| `PPBEN.csv` | quikridr (primary source) |
| `PAGNT.csv` | quikagts (primary source) |
| `PACTG_Accounting_Extract20260427.csv` | quikprmh, quikdvpr, quikactg |

**Canonical copies outside this folder** (removed from Source as duplicates):

| File | Path |
|------|------|
| `quikplan_source.csv` | `plan_analysis/quikplan_source.csv` |
| `PCOMP.csv` | `plan_analysis/PCOMP.csv` |
| `PCOVR.csv` / `PCOVRSGT.csv` | `plan_analysis/source_data/coverage/` |

---

## C. Product setup path (quikplan — separate from batch)

**Do not rely on batch for quikplan** when Product Setup Isolation is enabled (default in business cut).

| File | Path |
|------|------|
| Quikplan source | `plan_analysis/quikplan_source.csv` |
| Rulebook | `QLA_Migration/Configs/Sync_Rulebook_quikplan.csv` |
| Master crosswalk | `Master_Crosswalk.csv` or `QLA_Migration/Mapping/Master_Crosswalk.csv` |
| Value translation | `Master_Value_Translation.csv` or `QLA_Migration/Mapping/Master_Value_Translation.csv` |
| Product catalog | `plan_governance/product_catalog_crosswalk.csv` |
| PCOMP lookup | `plan_analysis/PCOMP.csv` |

**Post-steps after product setup emit:**

1. P3E quikridr MPLAN alignment (if quikridr already exists)
2. R7B rate variation flags (automatic in v57.3 conversion path)

### Rate segmentation inputs (for PLANVALOPT / *VARY* flags)

| File | Path |
|------|------|
| Rate table extract | `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv` |
| PAAGERAT extract | (via `qla_core/plan_source_paths.py` resolution) |
| PCOVRSGT / PCOVR | `plan_analysis/source_data/coverage/` |
| Emitted rate keys (optional) | `plan_analysis/phase_r5_rate_loader/emitted_dbf/` |

---

## D. Claims UAT path (optional — UAT mode only)

Requires `QLA_RUN_MODE=UAT` and `QLA_BATCH_INCLUDE_CLAIMS_UAT=1`.

| Output | UAT source (not LifePRO Source folder) |
|--------|----------------------------------------|
| quikclms | `plan_analysis/phase17_uat_governance_reporting/uat_candidate_quikclms.csv` |
| quikclmp | `plan_analysis/phase17_uat_governance_reporting/uat_candidate_quikclmp.csv` |

Rulebooks: `Sync_Rulebook_quikclms.csv`, `Sync_Rulebook_quikclmp.csv`

---

## E. Tables populated on full conversion

### Standard LifePRO batch (11 tables → CSV)

Written to **`QLA_Migration/Output/`**:

1. `quikclnt.csv`
2. `quikclid.csv`
3. `quikmstr.csv`
4. `quikbenf.csv`
5. `quikridr.csv`
6. `quikagts.csv`
7. `quikdvdp.csv`
8. `quikprmh.csv` *(skipped if PACTG extract missing)*
9. `quikdvpr.csv` *(same source as quikprmh)*
10. `quikactg.csv` *(same source as quikprmh)*

**quikplan** — via **Product Setup Conversion** panel (not standard batch when isolated):

11. `quikplan.csv` — includes P3C authority + R7B rate variation flags

### Claims UAT add-on (when enabled)

12. `quikclms.csv`
13. `quikclmp.csv`

### Audit / sidecar outputs (not QLA load tables)

| File | When |
|------|------|
| `Migration_Audit_Log.txt` | Every batch table |
| `variation_code_audit.csv` | quikplan conversion (VARGP/VARDB classification) |
| `product_governance_diagnostics.csv` | Product setup subprocess |
| P3E / P3C governance CSVs | Under `plan_analysis/phase_p3*` when runners execute |

---

## F. GUI path mapping (recommended)

| UI field | Set to |
|----------|--------|
| Field Mapping (Rulebook) | `QLA_Migration/Configs/Sync_Rulebook_quikplan.csv` |
| Source Data File | `QLA_Migration/Source/quikmstr.csv` *(any file in Source folder for batch)* |
| Value Translation | `QLA_Migration/Mapping/Master_Value_Translation.csv` |
| ID Crosswalk | `QLA_Migration/Mapping/Master_Crosswalk.csv` |
| Relational File | `QLA_Migration/Output/quikclid.csv` *(after quikclid run)* |
| Output Directory | `QLA_Migration/Output` |

---

## G. Regeneration commands

```bash
# 1. Product setup (quikplan + R7B flags)
python plan_governance/phase_p2_product_setup_runner/product_setup_runner.py ^
  --uat-overlay --closed-product-authority --strict-authority ^
  --emit --output-dir QLA_Migration/Output

# 2. Full LifePRO batch (GUI: RUN FULL BATCH CONVERSION)
python QLA_Migration/_run_full_batch_test.py

# 3. quikridr MPLAN alignment
python plan_analysis/phase_p3e_quikridr_authority_alignment/phase_p3e_quikridr_authority_runner.py --closed-mplan-authority --emit

# 4. Product cut validation package
python plan_analysis/product_business_test_cut/run_product_business_test_cut.py
```

---

## H. Deferred actuarial assumptions

These are **not populated** in this cut (see `deferred_actuarial_assumptions_note.md`):

MORT, ETIMORT, RSVINT, RSVMETH, INTMETHCV, INTMETHTV, NFOINT, STOREMEANS, CALCMIDS

Rulebook may carry defaults for schema fields (e.g. NFOINT blank, INTMETHCV=A); rate loader actuarial placeholders remain configurable separately.
