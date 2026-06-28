# Issue #21D — Intake Report

**Issue:** Interest Crediting Rate / Blank Owner Name Investigation  
**Intake agent:** Issue #21D Intake (read-only)  
**Date:** 2026-06-27  
**Converter version analyzed:** v57.35  
**Status:** INTAKE COMPLETE — no implementation authorized

---

## 1. Purpose

Issue #21D investigates two client-reported defects from the Issue #21 validation bundle:

- **Track A:** QLAdmin shows **4.00%** Dividend Accum Int Rate; client confirms **4.50%** for ISWL.
- **Track B:** Some policies show **blank insured/owner names** in QLAdmin.

This intake determines origin, population, involved artifacts, and whether the tracks share a root cause.

---

## 2. Executive summary

| Track | Verdict | Population | Root cause (one line) |
|-------|---------|------------|------------------------|
| **A — Interest rate** | **Confirmed defect** | **2,268 ISWL policies (100%)** | `quikdvdp.MDEPINT` **hardcoded to 4.00** in rulebook |
| **B — Blank names** | **Confirmed defect (small)** | **25 policies (0.49%)** | Missing RNA IN/PO rows and/or **quikclnt row gaps** for resolved IDs |
| **Shared cause?** | **No** | — | Independent data paths |

Client business clarification received: **all ISWL plans should use 4.50% crediting rate.** This resolves the prior Issue #21D "AWAITING CLIENT" rate question for Planning.

---

## 3. Track A — Interest crediting rate

### 3.1 Questions answered

| # | Question | Answer |
|---|----------|--------|
| 1 | Where does 4.00% originate? | **`Sync_Rulebook_quikdvdp.csv` → `MDEPINT` default `4.00`**, emitted to `quikdvdp.csv` |
| 2 | Is it hardcoded? | **Yes** — rulebook default with explicit comment *"Hardcoded Product Rate"* |
| 3 | Does another extract contain 4.50%? | **Yes** — `CSO_Mortiality_Crosswalk.csv` (4.50%, code `A`); already applied to **`quikplan.NFOINT`** |
| 4 | Do all ISWL plans get the same value? | **Yes** — all 2,268 ISWL policies have `MDEPINT = 4.00` |
| 5 | Affected population | **2,268 policies** on 8 ISWL plan codes |
| 6 | Files involved | See §3.3 |

### 3.2 Important nuance for Planning

QLAdmin **Dividend Accum Int Rate** maps to **`quikdvdp.MDEPINT`**, not `quikplan.NFOINT`. The converter already sets **`quikplan.NFOINT = A` (4.50%)** via CSO crosswalk, but that does **not** correct the Dividend Accum display. Planning must confirm whether both fields must align and whether Issue #21E (cash value) depends on `MDEPINT` vs `NFOINT`.

QUIKAINT (`1205IS` PFSA lineage) does **not** contain legacy ISWL QL plan codes (`1658C1`, etc.) and is **not** the source of the 4.00% display on sample policies.

### 3.3 Artifact inventory (Track A)

| Artifact | Path |
|----------|------|
| Hardcoded rate rule | `QLA_Migration/Configs/Sync_Rulebook_quikdvdp.csv` |
| Policy dividend deposit output | `QLA_Migration/Output/quikdvdp.csv` |
| Plan assumptions | `QLA_Migration/Output/quikplan.csv` |
| CSO rate authority | `plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv` |
| CSO loader | `qla_core/cso_mortality_crosswalk.py` |
| Plan rulebook defaults | `QLA_Migration/Configs/Sync_Rulebook_quikplan.csv` |
| QUIKAINT build (reference) | `plan_analysis/phase_r6_quikaint_rates/build_quikaint.py` |
| Population CSV | `Issue_21D_Interest_Rate_Population.csv` |

---

## 4. Track B — Blank owner / insured names

### 4.1 Questions answered

| # | Question | Answer |
|---|----------|--------|
| 1 | Total blank-name population | **25 policies** |
| 2 | Owner blank | **20** |
| 3 | Insured blank | **19** |
| 4 | Both blank | **14** |
| 5 | ISWL disproportionate? | **No** — 13/2,268 ISWL (0.57%) vs 12/2,815 non-ISWL (0.43%) |
| 6 | Source data availability | RNA healthy fleet-wide; **specific policies lack IN/PO rows**; PPOLC `PRIMARY_PERSON=I` is type flag only |
| 7 | Responsible converter | **RNA extract (gap)** + **quikclnt completeness**; quikmstr/rel_map behave correctly; v57.28 blocks `I` leak |
| 8 | Root-cause candidates | RC-B1 RNA gap, RC-B2 quikclnt missing row, RC-B3 partial owner |

### 4.2 PRIMARY_PERSON hypothesis

**Partially confirmed, reframed:** `PRIMARY_PERSON = I` is **not** a client ID. v57.28 **prevents** it from becoming `MPRIMID` (0 leaks in batch). The defect is that **no alternate insured ID source** fills MPRIMID when RNA lacks IN rows.

### 4.3 Example 010713704C

- PPOLC: `PRIMARY_PERSON = I`
- RNA: only `SA`, `BK` — no individual insured/owner
- quikmstr: blank MPRIMID / MOWNRID
- LifePRO hierarchy (separate analysis): IN|PA|PO roles exist — **extract gap**

### 4.4 Artifact inventory (Track B)

| Artifact | Path |
|----------|------|
| RNA extract | `QLA_Migration/Source/RelationshipNameAddress_Extract_20260530.csv` |
| PPOLC | `QLA_Migration/Source/PPOLC_PolicyMaster_Extract_20260530.csv` |
| quikclnt rulebook | `QLA_Migration/Configs/Sync_Rulebook_quikclnt.csv` |
| quikclid rulebook | `QLA_Migration/Configs/Sync_Rulebook_quikclid.csv` |
| Value translation | `QLA_Migration/Mapping/Master_Value_Translation.csv` |
| rel_map + MPRIMID guard | `app.py` / `QLA_Migration/app.py` |
| QA validator | `tools/validators/validate_insured_owner_golden.py` |
| Population CSV | `Issue_21D_Blank_Name_Population.csv` |

---

## 5. Deliverables produced

| File | Description |
|------|-------------|
| `Issue_21D_Intake_Report.md` | This report |
| `Issue_21D_Policy_Population_Summary.md` | Population metrics |
| `Issue_21D_Root_Cause_Inventory.md` | Root-cause matrix |
| `Issue_21D_Trace_Samples.md` | End-to-end traces |
| `Issue_21D_Interest_Rate_Population.csv` | 2,268 ISWL rows |
| `Issue_21D_Blank_Name_Population.csv` | 25 affected rows |

**Location:** `Issue_Log_Items/Issue_21/Issue_21D/`

---

## 6. Recommendations for Planning (non-binding)

1. **Track A:** Plan surgical rulebook change for `MDEPINT` (4.00 → 4.50 or CSO-driven lookup); coordinate with Issue #21E.
2. **Track B:** Plan two workstreams — (a) RNA re-extract audit for missing IN/PO on 25 policies; (b) quikclnt completeness pass for IDs in quikmstr but absent from quikclnt.
3. **Do not merge** the two tracks into a single remediation phase.

---

## 7. Constraints honored

- No code changes
- No rulebook changes
- No Planning or Development execution
- Converter left at v57.35

---

# Planning Agent Handoff Prompt

Copy everything below into a **new Cursor chat** to begin Issue #21D Planning.

---

```markdown
# Cursor Prompt — Issue #21D Planning Agent

You are continuing the **LifePRO → QLAdmin Conversion Project**.

**Converter version:** v57.35  
**Prior stage:** Issue #21D Intake — **COMPLETE** (read-only)  
**Your stage:** Planning only — no Development until plan is approved

---

## Issue #21D — Interest Crediting Rate / Blank Owner Name

Two **independent** tracks. Intake confirmed they do **NOT** share a root cause.

---

## Intake conclusions (authoritative)

### Track A — Interest crediting rate

- **Symptom:** QLAdmin "Dividend Accum Int Rate" = **4.00%**; client confirms **4.50%** for all ISWL.
- **Population:** **2,268 policies** (100% of ISWL fleet) on 8 plan codes:
  - 1658C1, 1658CS, 1659C2, 1659CR, 1659CS, 1659SR, 1669SR, 1679CS
- **Root cause:** `QLA_Migration/Configs/Sync_Rulebook_quikdvdp.csv` hardcodes **`MDEPINT = 4.00`**.
- **Evidence:** All ISWL rows in `QLA_Migration/Output/quikdvdp.csv` show `MDEPINT = 4.00`.
- **Correct rate already elsewhere:** `CSO_Mortiality_Crosswalk.csv` specifies 4.50% / code `A`; `quikplan.NFOINT = A` on all ISWL templates — but QLAdmin Dividend Accum field reads **`quikdvdp.MDEPINT`**, not `quikplan.NFOINT`.
- **Example:** Policy `010713704C` (legacy `9010713704`, MPLAN `1659C2`).

### Track B — Blank owner/insured names

- **Symptom:** QLAdmin shows blank names (commas only).
- **Population:** **25 policies (0.49%)** — NOT ISWL-disproportionate (13 ISWL / 12 non-ISWL).
- **Root causes:**
  1. **RNA gap:** Specific policies missing `IN`/`PO` rows in `RelationshipNameAddress_Extract` (example `010713704C` has only `SA`+`BK`).
  2. **quikclnt gap:** Client IDs on `quikmstr` (from rel_map) missing from `quikclnt` despite names in RNA (example `592064`).
  3. **`PRIMARY_PERSON = I`:** Type flag only; v57.28 guard blocks MPRIMID leak (**0** `MPRIMID='I'` in batch).
- **Example:** Policy `010713704C` — PPOLC `PRIMARY_PERSON=I`, blank MPRIMID/MOWNRID, RNA has no IN/PO.

---

## Intake artifacts (read first)

```
Issue_Log_Items/Issue_21/Issue_21D/
  Issue_21D_Intake_Report.md
  Issue_21D_Policy_Population_Summary.md
  Issue_21D_Root_Cause_Inventory.md
  Issue_21D_Trace_Samples.md
  Issue_21D_Interest_Rate_Population.csv      (2,268 rows)
  Issue_21D_Blank_Name_Population.csv           (25 rows)
```

---

## Key code / config paths

| Track | Primary touchpoint |
|-------|-------------------|
| A | `QLA_Migration/Configs/Sync_Rulebook_quikdvdp.csv` (`MDEPINT`) |
| A (reference) | `plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv`, `qla_core/cso_mortality_crosswalk.py` |
| B | `RelationshipNameAddress_Extract_20260530.csv`, `Sync_Rulebook_quikclnt.csv`, quikclnt conversion in `app.py` |
| B | `app.py` v57.28 MPRIMID guard (~5442–5446), `_load_rel_map` (~542–582) |

---

## Planning deliverables required

1. **Issue_21D_Planning_Report.md** — separate plans for Track A and Track B
2. **Issue_21D_Remediation_Design_TrackA.md** — MDEPINT authority decision, QLAdmin field mapping validation, joint #21E note
3. **Issue_21D_Remediation_Design_TrackB.md** — RNA re-extract vs converter fix decision tree, quikclnt completeness approach
4. **Issue_21D_Test_Plan.md** — golden policies, population regression, schema integrity
5. **Issue_21D_Risk_Register.md** — rollback, blast radius, cross-issue dependencies

---

## Business rules (mandatory)

- Surgical edits only; preserve QLA formatting and schema integrity
- Do not refactor unrelated code; do not rewrite app.py wholesale
- Update version number only when Development modifies app.py
- Track A change must be evaluated against Issue #21E (cash value)
- Track B must not reintroduce PRIMARY_PERSON type-flag leak

---

## Validation baseline

- Full batch output: `QLA_Migration/Output/` (5,083 policies)
- Existing validator: `tools/validators/validate_insured_owner_golden.py`
- Issue #21 golden policies include `010713704C` (both tracks)

---

## Success criteria for Planning

- Clear go/no-go remediation design per track
- Explicit decision on MDEPINT source (hardcode 4.50 vs CSO-driven vs extract-driven)
- Explicit decision on Track B: source re-extract scope vs quikclnt converter fix
- Rollback-safe phased implementation outline for Development Agent
- No code changes during Planning

Stop after Planning deliverables and Development Agent handoff prompt.
```

---

*End of Issue #21D Intake Report*
