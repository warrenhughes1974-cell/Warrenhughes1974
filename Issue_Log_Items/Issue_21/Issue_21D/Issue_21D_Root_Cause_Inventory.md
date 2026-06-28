# Issue #21D — Root Cause Inventory

**Intake date:** 2026-06-27  
**Converter version:** v57.35  
**Scope:** Track A (interest rate) and Track B (blank names) — independent inventories

---

## Cross-track verdict

| Question | Answer |
|----------|--------|
| Do Track A and Track B share a common root cause? | **No** |
| Shared layer? | Both surface in QLAdmin Policy Display, but data paths are unrelated |
| Shared policy example? | Yes (`010713704C`) — coincidental overlap, not causal |

---

## Track A — Interest crediting rate

### Symptom

QLAdmin **Dividend Accum Int Rate** shows **4.00%**; client confirms **4.50%** for all ISWL plans.

### Confirmed origin of 4.00%

| Layer | Artifact | Finding |
|-------|----------|---------|
| **Primary (confirmed)** | `QLA_Migration/Configs/Sync_Rulebook_quikdvdp.csv` | **`MDEPINT` default hardcoded to `4.00`** with note *"Hardcoded Product Rate"* |
| **Output evidence** | `QLA_Migration/Output/quikdvdp.csv` | All **2,268 ISWL policies** emit `MDEPINT = 4.00` |
| **QLAdmin field mapping** | Issue #21 client screenshots + `quikdvdp` schema | **Dividend Accum Int Rate ↔ `quikdvdp.MDEPINT`** |

**Hardcoded?** **Yes** — rulebook default, not sourced from LifePRO extract.

### Correct rate authority (4.50%) — where it exists

| Source | Location | ISWL value |
|--------|----------|------------|
| Client business rule | Issue #21D intake brief | **4.50% for all ISWL** |
| CSO Mortality Crosswalk | `plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv` | All 8 ISWL rows: `nfo_interest_source = 4.50%`, `nfo_interest_code = A` |
| Converter output (different field) | `QLA_Migration/Output/quikplan.csv` | **`NFOINT = A`** on all ISWL plan templates (applied via `qla_core/cso_mortality_crosswalk.py` in `app.py`) |

### Not the source of QLAdmin 4.00% display

| Candidate | Why ruled out or secondary |
|-----------|----------------------------|
| `quikplan.NFOINT` blank | **Ruled out** — current batch shows `NFOINT = A` (4.50% code) |
| `quikplan.VARGP = 4` | Variation/premium flag default in rulebook; not the Dividend Accum Int field |
| `quikplan.DEPINT = 0.00` | Rulebook default; separate deposit-int field |
| QUIKAINT `MINTRATE` | Legacy ISWL QL plan codes (`1658C1`, etc.) **not present** in `plan_analysis/phase_r6_quikaint_rates/quikaint_emit_trace.csv`; PFSA code `1205IS` tops out at 3.5% promo — different product lineage |

### Files / modules involved (Track A)

| File / module | Role |
|---------------|------|
| `Sync_Rulebook_quikdvdp.csv` | **Root cause** — hardcoded `MDEPINT = 4.00` |
| `app.py` / `QLA_Migration/app.py` | Emits `quikdvdp` from rulebook |
| `Sync_Rulebook_quikplan.csv` | `NFOINT`, `DEPINT`, `VARGP` defaults; CSO overlay for `NFOINT` |
| `plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv` | Authoritative 4.50% / code `A` for ISWL |
| `qla_core/cso_mortality_crosswalk.py` | Applies `NFOINT`/`INTMETHCV` to quikplan |
| `plan_analysis/phase_r6_quikaint_rates/build_quikaint.py` | QUIKAINT builder (PFSA rates; no legacy ISWL plan codes) |

### Track A root-cause statement

> QLAdmin reads **4.00%** from **`quikdvdp.MDEPINT`**, which is **hardcoded in the quikdvdp rulebook**. The business-authoritative **4.50%** exists in the **CSO crosswalk** and is already loaded into **`quikplan.NFOINT = A`**, but that field drives a **different actuarial/QLAdmin interest path** than Dividend Accum Int Rate. **All ISWL policies are uniformly affected.**

---

## Track B — Blank owner / insured names

### Symptom

QLAdmin Policy Display shows blank names (comma-only) for insured and/or owner on some converted policies.

### Ruled out

| Hypothesis | Evidence |
|------------|----------|
| `PRIMARY_PERSON = I` mapped to `MPRIMID` | **0 policies** with `MPRIMID = 'I'` in batch; v57.28 guard strips single-letter alpha values |
| Global RNA extract failure | RNA has **6,387 IN** and **6,125 PO** rows across **5,084 policies** — extract is healthy fleet-wide |

### Confirmed root-cause families

#### RC-B1 — Policy-specific RNA gap (missing IN/PO rows)

| Evidence | Detail |
|----------|--------|
| Example `010713704C` | RNA has only `SA` + `BK`; **no `IN` or `PO`** |
| LifePRO hierarchy (claims analysis) | Policy `9010713704` shows roles `B1\|B2\|BK\|IN\|PA\|PO\|SA` in LifePRO — **IN/PO exist in source system but not in delivered RNA extract row set** |
| `PPOLC.PRIMARY_PERSON` | **`I`** — type indicator only; cannot supply client ID |
| Downstream | `quikclid` lacks IN/PO → `rel_map` cannot set `MPRIMID`/`MOWNRID` |

**Layer:** Source extract completeness (policy-specific) + relationship conversion chain.

#### RC-B2 — Client ID resolved but missing from quikclnt

| Evidence | Detail |
|----------|--------|
| Example `010766896C` | `MPRIMID = MOWNRID = 592064` but **592064 not in quikclnt** |
| RNA for 592064 | **JOHNSON, PENNY** present with `RELATE_CODE = IN` |
| Downstream | QLAdmin join to `quikclnt` returns blank name |

**Layer:** `quikclnt` conversion / client deduplication — relationship IDs promoted to `quikmstr` without matching client row.

#### RC-B3 — Owner role not populated (partial)

Several policies have insured ID + name but **blank `MOWNRID`** (owner-only gap). Often **`HAS_PO_IN_QUikCLID = N`**.

### Responsibility matrix (Track B)

| Component | Responsible? | Notes |
|-----------|--------------|-------|
| `RelationshipNameAddress_Extract` | **Yes (RC-B1)** | Policy-specific missing IN/PO rows |
| `PPOLC.PRIMARY_PERSON` | **Contributing** | `I` flag is not a client ID; must not map to MPRIMID |
| `Sync_Rulebook_quikclnt.csv` | **No direct defect found** | Maps RNA name fields correctly when rows exist |
| `Sync_Rulebook_quikclid.csv` | **No direct defect** | Pass-through `RELATE_CODE → MRELATION` |
| `app.py` rel_map / v57.28 guard | **Correct behavior** | Blocks type-flag leak; cannot invent IDs |
| `quikmstr` rulebook | **No PRIMARY_PERSON → MPRIMID rule** (post-v57.26) | IDs come from rel_map only |
| `quikclnt` converter | **Yes (RC-B2)** | Some NAME_IDs referenced by quikclid/quikmstr absent from quikclnt output |

### Files / modules involved (Track B)

| File / module | Role |
|---------------|------|
| `RelationshipNameAddress_Extract_20260530.csv` | Primary name/relationship source (PRELSA) |
| `PPOLC_PolicyMaster_Extract_20260530.csv` | `PRIMARY_PERSON` type flag |
| `Sync_Rulebook_quikclnt.csv` | RNA → quikclnt field map |
| `Sync_Rulebook_quikclid.csv` | RNA → quikclid relational map |
| `Master_Value_Translation.csv` | `IN→INSD`, `PO→OWNR`, `SA→SERV`, `BK→BANK` |
| `app.py` (`_load_rel_map`, v57.28 MPRIMID guard) | quikmstr ID population from quikclid |
| `tools/validators/validate_insured_owner_golden.py` | Golden-policy QA harness |

### Track B root-cause statement

> Blank names are caused by **(1) missing IN/PO relationship rows in the delivered RNA extract for specific policies**, and **(2) client IDs referenced on quikmstr without a corresponding quikclnt row**. The **`PRIMARY_PERSON = I` hypothesis is resolved** — v57.28 prevents the flag from becoming MPRIMID, but PPOLC offers no usable insured client ID. This is **not ISWL-specific** and affects **25 policies (0.49%)**.

---

## Planning implications (inventory only — no implementation)

| Track | Likely remediation class | Risk |
|-------|-------------------------|------|
| A | Rulebook / rate authority — change `MDEPINT` source to 4.50% or map from CSO/ plan | Medium — verify QLAdmin field pairing with `NFOINT`; joint validation with Issue #21E (cash value) |
| B | Source re-extract (RNA IN/PO) + quikclnt completeness audit | Medium — small population; high client visibility on sample policies |
