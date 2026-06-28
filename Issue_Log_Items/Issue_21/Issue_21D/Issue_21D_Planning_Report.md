# Issue #21D — Planning Report

**Issue:** Interest Crediting Rate / Blank Owner Name  
**Date:** 2026-06-27  
**Converter version:** v57.35  
**Stage:** Planning complete  
**Prior stage:** Intake complete (2026-06-27)  
**Next stage:** Dependency Gate (not started)

---

## 1. Executive summary

Issue #21D comprises **two independent defects** confirmed by Intake. Planning evaluated remediation options separately and selected:

| Track | Defect | Population | **Recommended remediation** |
|-------|--------|------------|----------------------------|
| **A** | Dividend Accum Int Rate 4.00% vs 4.50% | 2,268 ISWL (100%) | **Option B:** Plan-aware `MDEPINT` from **CSO Mortality Crosswalk** |
| **B** | Blank insured/owner names | 25 policies (0.49%) | **Option D (Hybrid):** quikclnt referential integrity **+** RNA re-extract |

**No code was modified during Planning.**

---

## 2. Intake recap (not repeated — authoritative reference)

| Document | Purpose |
|----------|---------|
| `Issue_21D_Intake_Report.md` | Full intake findings |
| `Issue_21D_Root_Cause_Inventory.md` | Root-cause matrix |
| `Issue_21D_Policy_Population_Summary.md` | Population metrics |
| `Issue_21D_Trace_Samples.md` | End-to-end traces |
| `Issue_21D_Interest_Rate_Population.csv` | 2,268 ISWL rows |
| `Issue_21D_Blank_Name_Population.csv` | 25 affected rows |

**Cross-track verdict:** No shared root cause.

---

## 3. Track A — Planning summary

### Confirmed root cause

`Sync_Rulebook_quikdvdp.csv` hardcodes **`MDEPINT = 4.00`** → QLAdmin Dividend Accum Int Rate.

### Planning discovery (critical)

All **5,083 policies** currently receive `MDEPINT = 4.00`, not ISWL only. A naive constant change to **4.50** would alter **2,815 non-ISWL policies** without business sign-off.

### Options evaluated

| Option | Description | Decision |
|--------|-------------|----------|
| A | Rulebook 4.00 → 4.50 | **Rejected** — non-ISWL blast radius |
| B | CSO crosswalk plan-aware MDEPINT | **Selected** |
| C | LifePRO extract-driven | **Deferred** — no extract mapped today |

### Recommended authority model

- **Source:** `plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv`
- **Field:** `nfo_interest_source` → numeric `MDEPINT` (4.50 for ISWL)
- **Fallback:** Rulebook default 4.00 when no CSO numeric rate
- **Alignment:** Matches existing `quikplan.NFOINT = A` path

### Track A — code areas (Development)

- `app.py` / `QLA_Migration/app.py` — quikdvdp MDEPINT enrichment
- `qla_core/cso_mortality_crosswalk.py` — optional rate-percent helper
- `tools/validators/validate_issue21d_mdepint.py` — new

**Detail:** `Issue_21D_Interest_Rate_Strategy.md`

---

## 4. Track B — Planning summary

### Confirmed root causes

1. **RC-B1:** RNA missing `IN`/`PO` rows for specific policies (~14 with missing IDs)
2. **RC-B2:** 14 RNA `NAME_ID`s absent from quikclnt (8 policies in blank-name set); sample clients have names but NULL `ADDRESS_ID`
3. **RC-B3:** Partial owner gaps (~7 policies)

**Ruled out:** `MPRIMID = 'I'` leak (0 policies).

### Options evaluated

| Option | Description | Decision |
|--------|-------------|----------|
| A | Converter tolerates missing RNA | **Rejected** — identity inference risk |
| B | Generate missing quikclnt rows | **Phase 1 of hybrid** |
| C | Require RNA re-extract | **Phase 2 of hybrid** |
| D | Hybrid B + C | **Selected** |

### Recommended approach

| Phase | Action | Owner | Expected fix count |
|-------|--------|-------|-------------------|
| **B1** | quikclnt emit for NAME_IDs with names but null address | Development | ~8 policies |
| **B2** | RNA re-extract for blank-name policy list | Client / extract team | ~14 policies |
| **B3** | Full batch + validators + UAT | Conversion + client | Close criteria |

### Track B — code areas (Development)

- `app.py` — quikclnt source prep (~5011–5016)
- `tools/validators/validate_insured_owner_golden.py` — extend
- `tools/validators/validate_issue21d_blank_names.py` — new

**Detail:** `Issue_21D_Blank_Name_Strategy.md`

---

## 5. Risk summary

| Track | Overall regression risk | Key mitigation |
|-------|----------------------|----------------|
| A | Low (Option B) | Plan-scoped CSO lookup; reject fleet constant |
| B | Low–medium | Preserve v57.28 guard; no synthetic IDs |

**Full analysis:** `Issue_21D_Risk_Assessment.md`

---

## 6. Decision record

| Track | Selected option | Score (see matrix) |
|-------|-----------------|-------------------|
| A | B — CSO plan-aware MDEPINT | 46/50 |
| B | D — Hybrid quikclnt + RNA | 41/50 |

**Matrix:** `Issue_21D_Decision_Matrix.md`

---

## 7. Implementation roadmap

| Step | Track | Deliverable |
|------|-------|-------------|
| 1 | Both | Dependency Gate PASS |
| 2 | A | Development v57.36 MDEPINT branch |
| 3 | B | Development quikclnt integrity branch |
| 4 | B | Client RNA re-extract |
| 5 | Both | Validators + full batch |
| 6 | Both | Client UAT + Issue #21E joint check (Track A) |

**Detail:** `Issue_21D_Implementation_Strategy.md`

---

## 8. Client actions required

| # | Action | Track | Blocking Development? | Blocking close? |
|---|--------|-------|----------------------|-----------------|
| 1 | Confirm 4.50% ISWL rate | A | No (done) | No |
| 2 | Confirm non-ISWL 4.00% acceptable until separately governed | A | No | Recommended |
| 3 | RNA re-extract for 25-policy list | B | No (B1 can proceed) | **Yes for RC-B1** |
| 4 | UAT on sample policies | Both | No | **Yes** |

---

## 9. Protected issues (do not regress)

| Issue | Status | Constraint |
|-------|--------|------------|
| #25 MPOLICY width | RELEASED v57.30 | No MPOLICY format change |
| #26 MPREM | RELEASED v57.31 | No quikridr MPREM change |
| #28 Plan mapping | CLOSED v57.35 | No crosswalk authority change |
| #21M QUIKMEMO | RELEASED v57.34 | No memo grain change |
| v57.28 MPRIMID guard | ACTIVE | Must preserve |

---

## 10. Planning deliverables index

| File | Status |
|------|--------|
| `Issue_21D_Planning_Report.md` | This document |
| `Issue_21D_Interest_Rate_Strategy.md` | Complete |
| `Issue_21D_Blank_Name_Strategy.md` | Complete |
| `Issue_21D_Risk_Assessment.md` | Complete |
| `Issue_21D_Decision_Matrix.md` | Complete |
| `Issue_21D_Implementation_Strategy.md` | Complete |

---

## 11. Success criteria — Planning

| Criterion | Met? |
|-----------|------|
| Independent solution analysis per track | ✓ |
| Recommended remediation selected per track | ✓ |
| Risks documented | ✓ |
| Code areas identified | ✓ |
| Client actions identified | ✓ |
| No code modified | ✓ |

**Planning status: COMPLETE**

---

## 12. Stop condition

Planning stops here. Do **not** proceed to Development, Risk Agent, or Ownership Decision until **Dependency Gate** completes.

---

# Cursor Prompt — Dependency Gate

Copy everything below into a **new Cursor chat** to begin the Dependency Gate stage.

---

```markdown
# Cursor Prompt — Issue #21D Dependency Gate

You are continuing the **LifePRO → QLAdmin Conversion Project**.

**Current converter version:** v57.35  
**Issue:** #21D — Interest Crediting Rate / Blank Owner Name  
**Prior stages:** Intake ✓ · Planning ✓  
**Your stage:** Dependency Gate only  
**Do NOT:** repeat Intake or Planning · modify code · begin Development · run Risk Agent · run Ownership Decision

---

## Issue summary

Issue #21D contains **two independent defects** with **separate remediations**:

| Track | Defect | Population | Planning recommendation |
|-------|--------|------------|------------------------|
| **A** | QLAdmin Dividend Accum Int Rate shows **4.00%**; client requires **4.50%** for ISWL | **2,268 ISWL policies (100%)** | **Option B:** Plan-aware `quikdvdp.MDEPINT` from **CSO Mortality Crosswalk** by MPLAN |
| **B** | Blank insured/owner names in QLAdmin | **25 policies (0.49%)** | **Option D (Hybrid):** Phase B1 quikclnt referential integrity + Phase B2 RNA re-extract |

**Cross-track:** No shared root cause. Sample policy `010713704C` exhibits both defects coincidentally.

---

## Intake findings (authoritative)

### Track A
- Root cause: `QLA_Migration/Configs/Sync_Rulebook_quikdvdp.csv` hardcodes `MDEPINT = 4.00`
- QLAdmin field: Dividend Accum Int Rate ↔ `quikdvdp.MDEPINT`
- `quikplan.NFOINT = A` already correct (4.50% code via CSO crosswalk) — different path
- **Critical:** All 5,083 policies have MDEPINT=4.00 today — fleet-wide constant change to 4.50 is **rejected**

### Track B
- RC-B1: RNA missing IN/PO rows (~14 policies with missing MPRIMID/MOWNRID)
- RC-B2: 14 RNA NAME_IDs missing from quikclnt (8 policies); names exist in RNA, often NULL ADDRESS_ID
- RC-B3: Partial owner gaps
- MPRIMID='I' leak: **0** (v57.28 guard active)
- Not ISWL-disproportionate

---

## Planning decisions (authoritative)

| Track | Selected | Rejected |
|-------|----------|----------|
| A | **B** — CSO crosswalk plan-aware MDEPINT | A (fleet 4.50 constant), C (extract — deferred) |
| B | **D** — Hybrid B1 quikclnt + B2 RNA re-extract | A (converter fallback without signed rules) |

---

## Repository constraints (mandatory)

From `AGENTS.md`:
- Surgical edits only; preserve rollback safety
- Do not redesign architecture or rewrite app.py wholesale
- Preserve QLA formatting, field order/types/lengths
- Update version number only when Development modifies app.py
- Preserve rulebook-driven mapping architecture

**Protected issues — do NOT regress:**
- **#25** MPOLICY 10-char left-pad (RELEASED v57.30)
- **#26** quikridr.MPREM (RELEASED v57.31)
- **#28** Plan mapping authority (CLOSED v57.35)
- **#21M** QUIKMEMO grain (RELEASED v57.34)
- **v57.28** MPRIMID guard (block PRIMARY_PERSON type flags)

---

## Required reading (Dependency Gate)

### Intake artifacts
```
Issue_Log_Items/Issue_21/Issue_21D/
  Issue_21D_Intake_Report.md
  Issue_21D_Policy_Population_Summary.md
  Issue_21D_Root_Cause_Inventory.md
  Issue_21D_Trace_Samples.md
  Issue_21D_Interest_Rate_Population.csv
  Issue_21D_Blank_Name_Population.csv
```

### Planning artifacts
```
Issue_Log_Items/Issue_21/Issue_21D/
  Issue_21D_Planning_Report.md
  Issue_21D_Interest_Rate_Strategy.md
  Issue_21D_Blank_Name_Strategy.md
  Issue_21D_Risk_Assessment.md
  Issue_21D_Decision_Matrix.md
  Issue_21D_Implementation_Strategy.md
```

### Code / config touchpoints (review only — no edits)
```
QLA_Migration/Configs/Sync_Rulebook_quikdvdp.csv     # MDEPINT hardcoded 4.00
QLA_Migration/Configs/Sync_Rulebook_quikclnt.csv     # RNA → quikclnt
QLA_Migration/Configs/Sync_Rulebook_quikclid.csv     # RNA → quikclid
plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv
qla_core/cso_mortality_crosswalk.py
app.py / QLA_Migration/app.py
  ~5011-5016  quikclnt dedup / RNA bridge
  ~4839-4950  quikdvdp caches
  ~5442-5455  MPRIMID guard + rel_map
QLA_Migration/Source/RelationshipNameAddress_Extract_20260530.csv
QLA_Migration/Output/  (v57.35 baseline batch)
tools/validators/validate_insured_owner_golden.py
```

---

## Dependency Gate tasks

Analyze and document **cross-issue dependencies**, **blocking relationships**, and **release sequencing** for both tracks independently.

### Track A dependencies to verify
- [ ] Issue **#21E** (Cash Value) — does CV computation depend on MDEPINT, NFOINT, or QUIKAINT?
- [ ] CSO crosswalk availability and versioning — is `nfo_interest_source` the approved MDEPINT authority?
- [ ] Non-ISWL policies — confirm 4.00% fallback acceptable for plans without CSO numeric rate
- [ ] QUIKAINT / rate-table pipeline — confirm no conflict with MDEPINT change
- [ ] Batch order — quikdvdp runs after quikridr (MPLAN resolution)

### Track B dependencies to verify
- [ ] Batch order — quikclnt → quikclid → quikmstr (rel_map reload)
- [ ] RNA re-extract — identify owner, lead time, and whether B1 can ship before B2
- [ ] quikclnt schema / QLAdmin minimum fields for name-only clients (NULL address)
- [ ] Claims / relationship analysis artifacts — confirm no conflict with PRELSA changes
- [ ] v57.28 MPRIMID guard — confirm no Dependency Gate recommendation violates it

### Cross-cutting
- [ ] Can Track A and Track B Development proceed in parallel?
- [ ] Can tracks ship in one release (v57.36) or must they split?
- [ ] Validator dependencies — new validators vs existing golden harness

---

## Expected Dependency Gate deliverables

Create under `Issue_Log_Items/Issue_21/Issue_21D/`:

| File | Content |
|------|---------|
| `Issue_21D_Dependency_Gate_Report.md` | PASS / PASS WITH CONDITIONS / BLOCKED per track |
| `Issue_21D_Dependency_Matrix.csv` | Issue × dependency × status × owner |
| `Issue_21D_Release_Sequence.md` | Recommended phasing (A, B1, B2) |
| `Issue_21D_Blockers_and_Conditions.md` | Explicit blockers; conditions for Development start |

If **BLOCKED**, document what must resolve before Development. If **PASS**, append Development Agent handoff prompt to the Gate Report.

---

## Client actions pending (Gate must track)

| Action | Track | Owner |
|--------|-------|-------|
| Confirm non-ISWL MDEPINT 4.00% until separately governed | A | Client |
| RNA re-extract for blank-name policy list | B | Client / LifePRO extract |
| Joint #21D / #21E UAT plan acknowledgment | A | Client |

---

## Explicit stop conditions

**STOP after Dependency Gate deliverables.** Do NOT:
- Modify code or rulebooks
- Begin Development
- Run Risk Agent
- Run Ownership Decision
- Update master tracking sheet status to RELEASED

**Proceed to Development only if:** Dependency Gate report status is PASS or PASS WITH CONDITIONS and all BLOCKED items have documented resolution paths.

---

## Success criteria (Dependency Gate)

- [ ] Track A and Track B dependency analyses **separate** in report
- [ ] #21E cross-dependency explicitly resolved or deferred with condition
- [ ] Protected issues (#25, #26, #28, #21M, v57.28) checked
- [ ] Release sequence documented
- [ ] Development authorized or blocked with clear rationale
- [ ] No code modified

Assume **no prior conversation history**. Start by reading Planning artifacts listed above.
```

---

*End of Issue #21D Planning Report*
