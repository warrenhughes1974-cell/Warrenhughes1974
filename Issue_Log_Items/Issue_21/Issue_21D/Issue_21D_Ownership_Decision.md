# Issue #21D — Ownership Decision

**Issue:** Interest Crediting Rate / Blank Owner Name  
**Date:** 2026-06-27  
**Converter version:** v57.35  
**Prior stages:** Intake ✅ · Planning ✅ · Dependency Gate ✅ (CONDITIONAL PASS)  
**Stage:** Ownership Decision ✅  
**Next stage:** Risk Agent (not started)

---

## 1. Final ownership decision

```text
PARTIAL DEVELOPMENT AUTHORIZED
```

| Work stream | Authorization |
|-------------|---------------|
| **Track A** — Interest crediting rate | **GO** |
| **Track B1** — quikclnt referential integrity | **GO** |
| **Track B2** — RNA re-extract | **HOLD** (client-owned; pending extract delivery) |

Development shall proceed **only** for Track A and Track B1. Track B2 remains pending client action (RNA re-extract). Full Issue #21D close requires B2 completion after client delivers corrected PRELSA extract.

---

## 2. Issue context (summary for record)

Issue #21D comprises two **independent** defects:

| Track | Symptom | Population | Root cause |
|-------|---------|------------|------------|
| **A** | Dividend Accum Int Rate 4.00% vs 4.50% (ISWL) | 2,268 policies | Hardcoded `quikdvdp.MDEPINT = 4.00` |
| **B** | Blank insured/owner names | 25 policies (0.49%) | RNA gaps + quikclnt missing rows |

Tracks do **not** share a root cause. Policy `010713704C` appears in both coincidentally.

---

## 3. Track A — ownership analysis

### 3.1 Authority model (decided)

| Layer | Owner | Artifact / action |
|-------|-------|-------------------|
| **Rate authority (content)** | **Client / Actuarial** | Business rule: ISWL = 4.50%; CSO crosswalk delivery |
| **Rate authority (runtime)** | **QLAdmin** | Read `CSO_Mortiality_Crosswalk.csv`; apply via converter |
| **ISWL scope gate** | **Shared** | Client validates 8-plan list; QLAdmin implements allowlist |
| **Non-ISWL fallback** | **Shared** | Client confirms 4.00% acceptable; QLAdmin preserves fallback |

**Binding authority:** `plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv` — column `nfo_interest_source` (4.50% for all 8 ISWL plans).

**Prohibited:** Fleet-wide rulebook constant 4.50; blanket CSO numeric apply to 1,688 non-ISWL policies on other CSO plan codes.

### 3.2 Ownership by activity

| Activity | Owner |
|----------|-------|
| Crosswalk authority (content updates) | **Client** |
| Crosswalk consumption / MDEPINT logic | **QLAdmin** |
| Rulebook (`Sync_Rulebook_quikdvdp.csv`) | **QLAdmin** — comment/fallback only |
| Converter (`app.py`, `cso_mortality_crosswalk.py`) | **QLAdmin** |
| Validation (`validate_issue21d_mdepint.py`) | **QLAdmin** |
| Client UAT (4.50% display) | **Client** |
| Production approval (Track A) | **Shared** |
| Future maintenance (CSO CSV updates) | **Shared** — Client delivers; QLAdmin validates |

### 3.3 #21E coordination

Cash value (Issue #21E) remains **Client-owned** business decision. QLAdmin and Client share joint UAT on overlapping sample policies. Track A Development does **not** imply #21E closure.

---

## 4. Track B1 — ownership analysis

### 4.1 Scope (decided)

Repair **~7 policies** where IN/PO exist in quikclid but **quikclnt row missing** (14 RNA NAME_IDs fleet-wide; NULL ADDRESS_ID root cause).

### 4.2 Ownership by activity

| Activity | Owner |
|----------|-------|
| Referential integrity standard | **QLAdmin** |
| Converter quikclnt emit fix | **QLAdmin** |
| Rulebook (if needed) | **QLAdmin** |
| Validation / golden harness extension | **QLAdmin** |
| Source RNA (existing file) | **Client** — already delivered |
| Partial UAT (7 policies) | **Client** |
| Communicating partial vs full fix | **Shared** |

### 4.3 Prohibited (QLAdmin)

- Synthesizing NAME_IDs
- Mapping `PRIMARY_PERSON = I` to MPRIMID
- Role inference when RNA lacks IN/PO

---

## 5. Track B2 — ownership analysis (client-owned)

### 5.1 Scope

**~18 policies** require IN and/or PO rows in RNA that are absent from the current extract. **Converter cannot manufacture missing identities.**

### 5.2 Ownership (explicit)

| Activity | Owner |
|----------|-------|
| PRELSA / RNA extraction | **Client** |
| Source correction in LifePRO | **Client** |
| Delivery of updated extract | **Client** |
| Policy list / gap evidence | **QLAdmin** (already provided) |
| Re-batch after extract receipt | **QLAdmin** |
| Revalidation | **QLAdmin** |
| Full name UAT | **Client** |

**Track B2 is a client-owned activity.** QLAdmin holds HOLD until EXT-B1 is satisfied.

---

## 6. Development authorization

| Work stream | Decision | Justification |
|-------------|----------|---------------|
| **Track A** | **GO** | Gate PASS; CSO + allowlist conditions clear; no external blocker |
| **Track B1** | **GO** | Gate PASS; bounded 7-policy fix; no external data required |
| **Track B2** | **HOLD** | External RNA dependency; identity data cannot be invented |

Detail: `Issue_21D_Development_Authorization.md`

---

## 7. Risk ownership (summary)

| Category | Primary owner |
|----------|---------------|
| **Technical risk** (regression, implementation) | **QLAdmin** |
| **Data quality risk** (RNA completeness, CSO accuracy) | **Client** |
| **Business approval risk** (UAT, production) | **Client** |
| **Shared coordination** (#21E, partial release messaging) | **Shared** |

Detail: `Issue_21D_Risk_Ownership.md`

---

## 8. Remaining client actions

| Priority | Action |
|----------|--------|
| P1 | RNA re-extract for 18 policies (**blocks full Track B**) |
| P2 | UAT Track A after v57.36 |
| P3 | UAT Track B (partial then full) |
| P4 | Confirm non-ISWL 4.00% (recommended) |

Detail: `Issue_21D_Remaining_Client_Actions.md`

---

## 9. Deliverables index

| File | Purpose |
|------|---------|
| `Issue_21D_Ownership_Decision.md` | This document |
| `Issue_21D_Ownership_Matrix.md` | Full responsibility matrix |
| `Issue_21D_Development_Authorization.md` | GO/HOLD with scope |
| `Issue_21D_Remaining_Client_Actions.md` | Client action register |
| `Issue_21D_Risk_Ownership.md` | Residual risk by org |

---

## 10. Protected issues (no regression)

| Issue | Constraint |
|-------|------------|
| #25 MPOLICY width | No MPOLICY format change |
| #26 MPREM | No quikridr MPREM change |
| #28 Plan mapping | No crosswalk authority change |
| #21M / #21M-FU | No QUIKMEMO grain change |
| v57.28 | MPRIMID guard preserved |

---

## 11. Stop condition

Ownership Decision complete. **Do not begin Development or Risk Agent execution in this session.**

Proceed to **Risk Agent** using the prompt below.

---

# Cursor Prompt — Risk Agent

Copy everything below into a **new Cursor chat** to begin the Risk Agent stage.

---

```markdown
# Cursor Prompt — Issue #21D Risk Agent

You are continuing the **LifePRO → QLAdmin Conversion Project**.

**Current converter version:** v57.35 (baseline); Development target **v57.36+**  
**Issue:** #21D — Interest Crediting Rate / Blank Owner Name  
**Completed stages:** Intake ✅ · Planning ✅ · Dependency Gate ✅ · Ownership Decision ✅  
**Your stage:** Risk Agent only  
**Do NOT:** repeat prior stages · modify code · begin Development until Risk Agent completes and authorizes

---

## Issue summary

Two **independent** defects:

| Track | Defect | Population | Root cause |
|-------|--------|------------|------------|
| **A** | Dividend Accum Int Rate 4.00% vs 4.50% (ISWL) | 2,268 | Hardcoded `quikdvdp.MDEPINT = 4.00` |
| **B** | Blank insured/owner names | 25 (0.49%) | RNA IN/PO gaps + quikclnt missing rows |

---

## Ownership decision (authoritative)

```text
PARTIAL DEVELOPMENT AUTHORIZED
```

| Stream | Dev auth | Owner highlights |
|--------|----------|------------------|
| **Track A** | **GO** | CSO crosswalk authority (Client content / QLAdmin runtime); ISWL allowlist 8 codes |
| **Track B1** | **GO** | quikclnt NULL-address fix — **QLAdmin** |
| **Track B2** | **HOLD** | RNA re-extract — **Client** (18 policies) |

Development proceeds for **A + B1 only**. B2 pending client PRELSA delivery.

---

## Intake findings (key)

- Track A: `Sync_Rulebook_quikdvdp.csv` MDEPINT=4.00 → all 5,083 policies; QLAdmin field = Dividend Accum Int Rate
- `quikplan.NFOINT = A` already correct for ISWL (separate path)
- Track B: 7 policies quikclnt-fixable; 18 need RNA; 0 MPRIMID='I' leaks
- Example: `010713704C` — both tracks

---

## Planning decisions (key)

- Track A: Option B — CSO plan-aware MDEPINT, **ISWL allowlist only** (not blanket CSO)
- Track B: Option D hybrid — B1 converter + B2 client extract
- Rejected: fleet 4.50 constant; converter role inference

---

## Dependency Gate (key)

- Track A: PASS with A-CON-1..4 (allowlist, quikridr MPLAN lookup, 4.00 fallback)
- Track B1: PASS (~7 policies, 14 missing NAME_IDs)
- Track B2: BLOCKED on EXT-B1 (RNA re-extract)
- Cross-issue: #21E coordinate UAT; #25/#26/#28/#21M no impact

---

## Authorized development scope

### Track A (GO)

- Surgical `app.py` / `QLA_Migration/app.py`: MDEPINT = 4.50 when MPLAN ∈ {1658C1, 1658CS, 1659C2, 1659CR, 1659CS, 1659SR, 1669SR, 1679CS}
- MPLAN from in-batch `quikridr.csv` phase-1 row
- Fallback MDEPINT = 4.00 otherwise
- Optional: extend `qla_core/cso_mortality_crosswalk.py`
- Create `tools/validators/validate_issue21d_mdepint.py`
- Version bump v57.36
- **Prohibited:** global rulebook 4.50; blanket CSO apply to non-ISWL

### Track B1 (GO)

- Surgical quikclnt emit for NULL ADDRESS_ID clients with RNA names
- Extend `validate_insured_owner_golden.py`; create `validate_issue21d_blank_names.py`
- **Prohibited:** synthetic IDs; PRIMARY_PERSON=I → MPRIMID

### Track B2 (HOLD)

- No Development until client delivers updated `RelationshipNameAddress_Extract`
- After delivery: re-batch + validate only (no new inference logic expected)

---

## Outstanding client dependencies

| ID | Action | Blocks |
|----|--------|--------|
| EXT-B1 | RNA re-extract (18 policies) | Full Track B / full #21D close |
| CA-2 | UAT Track A | Track A release |
| CA-3/4 | UAT Track B | Track B release |
| CA-5 | Non-ISWL 4.00% confirm | Recommended prod sign-off |
| #21E | Cash value decision | Separate issue |

---

## Repository constraints (mandatory)

From `AGENTS.md`:
- Surgical edits only; preserve rollback safety
- Do not rewrite app.py wholesale
- Preserve QLA formatting, field order/types/lengths
- Bump app.py version on Development
- Preserve rulebook-driven architecture

**Protected issues:**
- **#25** MPOLICY (v57.30)
- **#26** MPREM (v57.31)
- **#28** Plan mapping (v57.35 CLOSED)
- **#21M** QUIKMEMO grain (v57.34)
- **v57.28** MPRIMID guard

---

## Required reading

### Prior stage artifacts
```
Issue_Log_Items/Issue_21/Issue_21D/
  Issue_21D_Intake_Report.md
  Issue_21D_Planning_Report.md
  Issue_21D_Dependency_Gate_Report.md
  Issue_21D_Ownership_Decision.md          (this chain)
  Issue_21D_Ownership_Matrix.md
  Issue_21D_Development_Authorization.md
  Issue_21D_Remaining_Client_Actions.md
  Issue_21D_Risk_Ownership.md
  Issue_21D_Interest_Rate_Population.csv    (2,268 rows)
  Issue_21D_Blank_Name_Population.csv       (25 rows)
```

### Code touchpoints (review for risk — do not edit yet)
```
QLA_Migration/Configs/Sync_Rulebook_quikdvdp.csv
app.py / QLA_Migration/app.py
  ~4839-4950  quikdvdp caches
  ~5007-5010  quikdvdp source filter
  ~5011-5016  quikclnt dedup / RNA bridge
  ~5442-5455  MPRIMID guard + rel_map
qla_core/cso_mortality_crosswalk.py
plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv
tools/validators/validate_insured_owner_golden.py
```

---

## Risk Agent tasks

1. **Track A risk register** — regression, non-ISWL blast radius, #21E interaction, MPLAN lookup failure modes
2. **Track B1 risk register** — quikclnt duplicates, QLAdmin NULL-address acceptance, partial-fix communication
3. **Track B2 residual risk** — client extract SLA, unfixable policies if IN/PO absent in LifePRO
4. **Cross-issue regression matrix** — #25, #26, #28, #21M, v57.28
5. **Rollback plan** — per-track revert procedure
6. **Go/No-Go for Development** — explicit recommendation after risk review

---

## Expected Risk Agent deliverables

Create under `Issue_Log_Items/Issue_21/Issue_21D/`:

| File | Content |
|------|---------|
| `Issue_21D_Risk_Agent_Report.md` | Executive risk summary + Development go/no-go |
| `Issue_21D_Risk_Register.csv` | Risk ID, track, category, owner, severity, mitigation, status |
| `Issue_21D_Regression_Matrix.md` | Protected issues + shared components |
| `Issue_21D_Rollback_Plan.md` | Track A / B1 revert steps |

If Risk Agent recommends **GO**, append **Development Agent handoff prompt** to `Issue_21D_Risk_Agent_Report.md`.

---

## Explicit stop conditions

**STOP after Risk Agent deliverables.**

Do NOT:
- Modify code or rulebooks (unless Risk Agent is explicitly authorized to — default: read-only)
- Begin Development before Risk Agent publishes go/no-go
- Run Ownership Decision again

**Development may begin only if** Risk Agent report recommends GO for Track A and/or B1 with documented mitigations.

Assume **no prior conversation history**. Start by reading Ownership and Dependency Gate artifacts.
```

---

*End of Issue #21D Ownership Decision*
