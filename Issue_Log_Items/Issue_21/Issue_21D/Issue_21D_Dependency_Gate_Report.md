# Issue #21D — Dependency Gate Report

**Issue:** Interest Crediting Rate / Blank Owner Name  
**Date:** 2026-06-27  
**Converter version:** v57.35  
**Prior stages:** Intake ✅ · Planning ✅  
**Gate stage:** Dependency Gate ✅  
**Next stage:** Ownership Decision (not started)

---

## 1. Executive summary

| Track | Gate result | Development | Release / Production |
|-------|-------------|-------------|----------------------|
| **A — Interest rate** | **PASS** (with conditions) | **Authorized** | Conditional on UAT + #21E coordination |
| **B — Blank names (B1)** | **PASS** | **Authorized** | Partial fix only (~7 policies) |
| **B — Blank names (B2)** | **BLOCKED** (external) | Blocked for full population | Blocked until RNA re-extract |
| **Issue #21D overall** | **CONDITIONAL PASS** | Track A + B1 may proceed independently | Full close blocked on EXT-B1 |

**Track A is not blocked by Track B external dependencies.**

---

## 2. Gate decision rationale

### CONDITIONAL PASS — overall

All **internal** dependencies for planned Development are satisfied or have documented implementation conditions. One **external** dependency (RNA re-extract) blocks **full** Track B release but does **not** block Track A or Track B Phase B1.

### Track A — PASS

| Criterion | Result |
|-----------|--------|
| CSO crosswalk available | ✅ 8/8 ISWL plans at 4.50% |
| ISWL fleet coverage | ✅ 2,268 policies; MPLAN set matches CSO |
| Helper module | ✅ `cso_mortality_crosswalk.py` in production use |
| quikdvdp path | ✅ Rulebook + app.py emit |
| Non-ISWL preservation plan | ⚠️ Requires ISWL allowlist gate (see A-CON-1) |
| MPLAN resolution | ⚠️ Requires quikridr output lookup (see A-CON-2) |
| Conflicting authorities | ✅ None for ISWL (CSO aligns with NFOINT code A) |

**Evidence:** Gate verification run 2026-06-27 against v57.35 batch output and repo artifacts.

### Track B — CONDITIONAL (B1 PASS / B2 BLOCKED)

| Criterion | Result |
|-----------|--------|
| Source extracts present | ✅ RNA, PPOLC, quikmstr chain |
| quikclnt gap bounded | ✅ 14 NAME_IDs; 12 with NULL ADDRESS_ID + names |
| B1 programmatic repair | ✅ ~7 policies |
| B2 RNA repair | ❌ 18 policies need IN/PO rows — **external** |
| Converter fixes all 25 alone | ❌ Not feasible |

---

## 3. Track A — dependency analysis

### 3.1 Authoritative inputs verified

| Input | Location | ISWL 4.50% | Suitable? |
|-------|----------|------------|-----------|
| CSO Mortality Crosswalk | `plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv` | 8 rows @ 4.50% | **Yes — primary authority** |
| Product catalog | `QLA_Migration/Mapping/product_catalog_crosswalk.csv` | 8 ISWL entries | Yes — plan identification |
| Client business rule | Intake confirmation | 4.50% all ISWL | Yes |
| quikplan.NFOINT | Output (CSO applied) | Code `A` | Aligns; different QLAdmin field |
| Rulebook default | `Sync_Rulebook_quikdvdp.csv` | 4.00 | Fallback only — not ISWL authority |

### 3.2 ISWL plan coverage

| QL PLAN | LifePRO plan | Batch policies | CSO rate |
|---------|--------------|---------------:|----------|
| 1659C2 | 659 CEN II | 1,147 | 4.50% |
| 1659CR | 659 CEN SR | 641 | 4.50% |
| 1658C1 | 658 CEN I | 435 | 4.50% |
| 1659CS | 659 CEN SD | 15 | 4.50% |
| 1659SR | 659 SR GD | 13 | 4.50% |
| 1658CS | 658 CEN SD | 13 | 4.50% |
| 1669SR | 669 SR GD | 2 | 4.50% |
| 1679CS | 679 CEN SD | 2 | 4.50% |
| **Total** | | **2,268** | |

No ISWL MPLAN in batch without CSO row. No CSO ISWL row without batch policies.

### 3.3 Non-ISWL authority

| Fact | Implication |
|------|-------------|
| 5,083 policies currently MDEPINT = 4.00 | Baseline for non-ISWL |
| CSO has numeric rates for 25 other plan codes (1,688 policies) | **Must NOT** apply blanket CSO numeric override |
| Planning preservation rule | Development gates override on **ISWL allowlist (8 codes)** only |

### 3.4 MPLAN / quikdvdp generation

| Item | Finding |
|------|---------|
| quikdvdp source | PPBENTYP (`PPBENTYP_BenefitType_Extract_20260530.csv`) — no PLAN column |
| Batch order | quikclnt → quikclid → quikplan → quikmstr → **quikridr** → quikbenf → **quikdvdp** |
| MPLAN dependency | Development loads phase-1 MPLAN from in-batch `quikridr.csv` (precedent: quikmstr MPAIDTO cache in quikdvdp block) |

### 3.5 Conflicting authorities

| Field | ISWL value | Conflict? |
|-------|------------|-----------|
| quikdvdp.MDEPINT | 4.00 today → 4.50 target | Fix target |
| quikplan.NFOINT | A (4.50% code) | **Aligned — not conflicting** |
| QUIKAINT | No legacy ISWL plan codes | Not used for this display |

---

## 4. Track B — dependency analysis

### 4.1 Source availability

| Source | Available | Role |
|--------|-----------|------|
| `RelationshipNameAddress_Extract_20260530.csv` | ✅ | quikclnt, quikclid |
| `PPOLC_PolicyMaster_Extract_20260530.csv` | ✅ | PRIMARY_PERSON type flag |
| quikmstr / quikclid / quikclnt outputs | ✅ v57.35 batch | Population analysis |

### 4.2 Repair categorization (25 policies)

| Category | Count | Programmatic? | External? |
|----------|------:|:-------------:|:-----------:|
| quikclnt missing row (IN/PO in quikclid) | 7 | **Yes (B1)** | No |
| RNA missing both IN and PO | 9 | No | **Yes (B2)** |
| RNA missing IN only | 3 | No | **Yes (B2)** |
| RNA missing PO only | 6 | No | **Yes (B2)** |

**Converter alone resolves all 25:** **No** (maximum ~7–8 via B1).

### 4.3 quikclnt gap detail

- RNA unique NAME_ID: 13,516  
- quikclnt MCLIENTID: 13,502  
- Gap: 14 IDs (13 valid clients + separator `-----------`)  
- 12/13 missing clients: all RNA rows have NULL ADDRESS_ID; individual names present  

Root cause hypothesis validated for Gate: **quikclnt emit/dedup drops NULL-address clients** — Development may repair without external data.

### 4.4 RNA gap example

Policy **010713704C** (legacy 9010713704):

- PPOLC `PRIMARY_PERSON = I` (type flag)
- RNA: SA + BK only
- LifePRO hierarchy (claims analysis): IN|PA|PO|B1|B2|BK|SA exist in source system
- **Requires RNA re-extract (EXT-B1)**

---

## 5. Cross-issue dependency review

| Issue | Shared with #21D | Impact | Gate assessment |
|-------|------------------|--------|-----------------|
| **#21E** Cash Value | NFOINT, rate assumptions, sample policies | MDEPINT change may affect CV; **joint UAT** | ⚠️ Coordinate — does not block Dev |
| **#21M** | None | None | ✅ No impact |
| **#21M-FU** | None | None | ✅ No impact |
| **#21K** MUNIT | quikridr (read-only MPLAN) | No schema change planned | ✅ No impact |
| **#25** MPOLICY | quikmstr | No MPOLICY change | ✅ No impact |
| **#26** MPREM | quikridr | No MPREM change | ✅ No impact |
| **#28** Plan mapping | MPLAN read for lookup | Read-only; no authority change | ✅ No impact |

---

## 6. Validation dependencies (summary)

Full specification: `Issue_21D_Validation_Dependencies.md`

| Track | Key validators (to create/extend) |
|-------|-----------------------------------|
| A | `validate_issue21d_mdepint.py` — 2,268 ISWL @ 4.50; 2,815 non-ISWL unchanged |
| B | `validate_issue21d_blank_names.py`; extend `validate_insured_owner_golden.py` |

---

## 7. Supporting artifacts

| File | Purpose |
|------|---------|
| `Issue_21D_Dependency_Checklist.md` | Pass/fail checklist |
| `Issue_21D_Blockers_And_Assumptions.md` | Blockers, conditions, assumptions |
| `Issue_21D_Validation_Dependencies.md` | Post-Development validation spec |
| `Issue_21D_External_Dependencies.md` | Client / extract team dependencies |

---

## 8. Recommendations to Ownership Decision

| # | Recommendation |
|---|----------------|
| 1 | **Authorize Development** for Track A (ISWL-scoped MDEPINT) and Track B1 (quikclnt integrity) |
| 2 | **Assign actuarial ownership** of CSO crosswalk as MDEPINT authority for ISWL |
| 3 | **Assign client/extract ownership** of RNA re-extract (EXT-B1) for 18-policy list |
| 4 | **Do not authorize** fleet-wide rulebook 4.50 constant |
| 5 | **Schedule joint #21D / #21E UAT** on 010713704C, 010818663C |

---

## 9. Stop condition

Dependency Gate complete. **Do not proceed to Development, Risk Agent, or Ownership Decision execution in this session.**

Ownership Decision Agent prompt appended below.

---

# Cursor Prompt — Ownership Decision Agent

Copy everything below into a **new Cursor chat** to begin the Ownership Decision stage.

---

```markdown
# Cursor Prompt — Issue #21D Ownership Decision Agent

You are continuing the **LifePRO → QLAdmin Conversion Project**.

**Current converter version:** v57.35  
**Issue:** #21D — Interest Crediting Rate / Blank Owner Name  
**Completed stages:** Intake ✅ · Planning ✅ · Dependency Gate ✅  
**Your stage:** Ownership Decision only  
**Do NOT:** repeat Intake, Planning, or Dependency Gate · modify code · begin Development · run Risk Agent

---

## Issue summary

Issue #21D contains **two independent defects**:

| Track | Defect | Population | Planning recommendation | Gate result |
|-------|--------|------------|----------------------|-------------|
| **A** | QLAdmin Dividend Accum Int Rate **4.00%** vs **4.50%** for ISWL | 2,268 policies | CSO crosswalk plan-aware MDEPINT | **PASS** (with conditions) |
| **B** | Blank insured/owner names | 25 policies (0.49%) | Hybrid: B1 quikclnt + B2 RNA re-extract | **B1 PASS / B2 BLOCKED** |

**Overall gate:** **CONDITIONAL PASS**  
**Track A Development:** Authorized (not blocked by Track B)  
**Full #21D release:** Blocked until RNA re-extract (EXT-B1)

---

## Intake findings (authoritative)

- Track A root cause: `Sync_Rulebook_quikdvdp.csv` hardcodes `MDEPINT = 4.00` → all 5,083 policies
- QLAdmin reads `quikdvdp.MDEPINT` (not `quikplan.NFOINT`); NFOINT already `A` for ISWL
- Track B: RC-B1 RNA missing IN/PO (18 policies); RC-B2 quikclnt missing 14 NAME_IDs (7 policies in blank set)
- MPRIMID='I' leak: 0 (v57.28 guard active)
- Example: `010713704C` — both tracks

---

## Planning decisions (authoritative)

| Track | Selected | Rejected |
|-------|----------|----------|
| A | Option B — CSO plan-aware MDEPINT (ISWL only) | Fleet constant 4.50; extract-driven |
| B | Option D — Hybrid B1 + B2 | Broad RNA fallback without signed rules |

---

## Dependency Gate findings (authoritative)

### Track A — PASS with conditions

| Condition | Detail |
|-----------|--------|
| **A-CON-1** | MDEPINT override **gated to ISWL allowlist (8 MPLAN codes)** — CSO has numeric rates for 25 non-ISWL plans (1,688 policies) |
| **A-CON-2** | MPLAN from in-batch `quikridr.csv` (runs before quikdvdp; PPBENTYP has no PLAN) |
| **A-CON-3** | Fallback MDEPINT = 4.00 for non-ISWL |
| **A-CON-4** | Do not change global rulebook to 4.50 |

**CSO verified:** All 8 ISWL plans → `nfo_interest_source = 4.50%`  
**Batch verified:** 2,268 ISWL policies; MPLAN distribution matches CSO set

### Track B — B1 PASS / B2 BLOCKED

| Phase | Status | Population |
|-------|--------|------------|
| B1 quikclnt integrity | Development authorized | ~7 policies (NULL ADDRESS_ID / missing quikclnt rows) |
| B2 RNA re-extract | **BLOCKED — external** | 18 policies (missing IN and/or PO in RNA) |

**Converter alone cannot fix all 25 policies.**

### Cross-issue

| Issue | Impact |
|-------|--------|
| **#21E** | Coordinate UAT — MDEPINT may affect CV; does not block Dev |
| **#21M, #21M-FU, #21K, #25, #26, #28** | No impact |

---

## Outstanding blockers

| ID | Blocker | Owner | Blocks Dev? | Blocks release? |
|----|---------|-------|-------------|-----------------|
| EXT-B1 | RNA re-extract for 18-policy list | Client / LifePRO extract | No | **Yes (full Track B)** |
| EXT-A2 | Non-ISWL 4.00% confirmation (recommended) | Client / Actuarial | No | Recommended |
| EXT-A3 / EXT-B3 | Client UAT | Client | No | Yes |

---

## Recommended ownership (for your decision)

| Domain | Recommended owner | Track |
|--------|-------------------|-------|
| CSO crosswalk as MDEPINT authority for ISWL | Actuarial / client product | A |
| MDEPINT implementation (app.py, validators) | Conversion engineering | A |
| quikclnt NULL-address emit fix | Conversion engineering | B1 |
| RNA re-extract specification + delivery | Client / LifePRO extract team | B2 |
| UAT sign-off (rate + names) | Client operations | Both |
| #21E joint validation | Client + conversion | A ↔ E |

---

## Repository constraints (mandatory)

From `AGENTS.md`:
- Surgical edits only; preserve rollback safety
- Do not rewrite app.py wholesale
- Preserve QLA formatting, field order/types/lengths
- Bump app.py version on Development (e.g. v57.36)
- Preserve rulebook-driven architecture

**Protected issues — do NOT regress:**
- **#25** MPOLICY width (v57.30)
- **#26** MPREM (v57.31)
- **#28** Plan mapping authority (v57.35 CLOSED)
- **#21M** QUIKMEMO grain (v57.34)
- **v57.28** MPRIMID guard

---

## Required reading

### Intake
```
Issue_Log_Items/Issue_21/Issue_21D/
  Issue_21D_Intake_Report.md
  Issue_21D_Root_Cause_Inventory.md
  Issue_21D_Policy_Population_Summary.md
  Issue_21D_Trace_Samples.md
  Issue_21D_Interest_Rate_Population.csv
  Issue_21D_Blank_Name_Population.csv
```

### Planning
```
  Issue_21D_Planning_Report.md
  Issue_21D_Interest_Rate_Strategy.md
  Issue_21D_Blank_Name_Strategy.md
  Issue_21D_Risk_Assessment.md
  Issue_21D_Decision_Matrix.md
  Issue_21D_Implementation_Strategy.md
```

### Dependency Gate
```
  Issue_21D_Dependency_Gate_Report.md          (this document)
  Issue_21D_Dependency_Checklist.md
  Issue_21D_Blockers_And_Assumptions.md
  Issue_21D_Validation_Dependencies.md
  Issue_21D_External_Dependencies.md
```

---

## Expected Ownership Decision deliverables

Create under `Issue_Log_Items/Issue_21/Issue_21D/`:

| File | Content |
|------|---------|
| `Issue_21D_Ownership_Decision_Report.md` | Formal ownership assignments per track |
| `Issue_21D_Authority_Model.md` | MDEPINT authority sign-off (CSO vs actuarial vs client) |
| `Issue_21D_Client_Action_Register.md` | EXT-B1 RNA request, UAT owners, deadlines |
| `Issue_21D_Development_Authorization.md` | Explicit go/no-go for Track A, B1, B2 |
| `Issue_21D_Ownership_Matrix.csv` | Role × artifact × owner |

---

## Ownership Decision tasks

1. **Track A:** Confirm CSO crosswalk as binding MDEPINT authority for ISWL (or assign alternative)
2. **Track A:** Confirm ISWL allowlist gating (8 codes) vs broader CSO application
3. **Track B1:** Assign conversion team ownership of quikclnt NULL-address fix
4. **Track B2:** Assign client/extract team ownership of RNA re-extract; approve policy list
5. **Cross-issue:** Assign #21E coordination owner for joint UAT
6. **Release:** Decide whether Track A + B1 may release before B2 (recommended: yes, with documented partial fix)
7. **Development authorization:** Issue explicit go/no-go per track based on ownership sign-off

---

## Explicit stop conditions

**STOP after Ownership Decision deliverables.**

Do NOT:
- Modify code or rulebooks
- Begin Development
- Run Risk Agent
- Update master tracking to RELEASED

**Development may begin only after:**
- `Issue_21D_Development_Authorization.md` records **GO** for Track A and/or B1
- Ownership Decision complete

Assume **no prior conversation history**. Start by reading Dependency Gate artifacts listed above.
```

---

*End of Issue #21D Dependency Gate Report*
