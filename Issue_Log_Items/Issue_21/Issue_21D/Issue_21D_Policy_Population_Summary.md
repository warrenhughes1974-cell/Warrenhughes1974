# Issue #21D — Policy Population Summary

**Intake date:** 2026-06-27  
**Converter version analyzed:** v57.35  
**Output batch:** `QLA_Migration/Output/` (full fleet, 5,083 policies)

---

## Executive linkage verdict

| Track | Issue | Population scope | Shares root cause with other track? |
|-------|-------|------------------|-------------------------------------|
| **A** | Interest crediting rate (4.00% vs 4.50%) | **All 2,268 ISWL policies** | **No** |
| **B** | Blank owner/insured names | **25 policies** (0.49% of fleet) | **No** |

Track A is a **plan/dividend-deposit rate rulebook defect** affecting the entire ISWL product family uniformly.  
Track B is a **relationship/client identity population defect** affecting a small, heterogeneous subset of policies.

---

## Track A — Interest crediting rate (ISWL)

### Known ISWL plan mapping (LifePRO → QLAdmin PLAN)

| LifePRO plan | QL PLAN code | Policies in batch (base MPLAN) |
|--------------|--------------|--------------------------------|
| 658 CEN I | 1658C1 | (subset of 2,268) |
| 658 CEN SD | 1658CS | |
| 659 CEN II | 1659C2 | |
| 659 CEN SR | 1659CR | |
| 659 CEN SD | 1659CS | |
| 659 SR GD | 1659SR | |
| 669 SR GD | 1669SR | |
| 679 CEN SD | 1679CS | |
| **Total ISWL** | **8 plan templates** | **2,268 policies** |

### Rate population findings

| Metric | Value |
|--------|-------|
| ISWL policies with `quikdvdp.MDEPINT = 4.00` | **2,268 / 2,268 (100%)** |
| ISWL `quikplan.NFOINT` after CSO crosswalk | **`A` on all 8 ISWL plan rows** (maps to **4.50%** in CSO Mortality Crosswalk) |
| ISWL `quikplan.VARGP` / `VARDB` | **`4` / `4`** (rulebook defaults — variation codes, not the displayed Dividend Accum rate) |
| QUIKAINT entries for legacy codes (`1658C1`, etc.) | **None** — QUIKAINT only carries PFSA product codes (e.g. `1205IS`) |
| Client-confirmed authoritative ISWL crediting rate | **4.50%** |

### Example policy 010713704C

| Field | Value |
|-------|-------|
| Legacy ID | 9010713704 |
| MPLAN | 1659C2 (659 CEN II) |
| QLAdmin observed | Dividend Accum Int Rate **4.00%** |
| `quikdvdp.MDEPINT` | **4.00** (hardcoded) |
| `quikplan.NFOINT` | **A** (CSO: 4.50%) |

---

## Track B — Blank owner / insured names

### Fleet-wide population

| Metric | Count | % of fleet |
|--------|-------|------------|
| Total policies (`quikmstr`) | 5,083 | 100% |
| Policies with blank insured and/or owner display | **25** | **0.49%** |
| Insured blank (`MPRIMID` missing or name empty) | **19** | 0.37% |
| Owner blank (`MOWNRID` missing or name empty) | **20** | 0.39% |
| Both insured and owner blank | **14** | 0.28% |
| `MPRIMID = 'I'` (PRIMARY_PERSON type-flag leak) | **0** | 0% (v57.28 guard active) |
| Global blank `MPRIMID` (any cause) | 12 | 0.24% |
| Global blank `MOWNRID` | 15 | 0.30% |

### ISWL disproportion analysis

| Metric | ISWL | Non-ISWL |
|--------|------|----------|
| Total policies | 2,268 | 2,815 |
| In blank-name population | **13** | **12** |
| Rate | **0.57%** | **0.43%** |

**Conclusion:** ISWL is **not materially disproportionate**. The blank-name defect is fleet-wide but **extremely small**; ISWL appears slightly more often only because several Issue #21 sample policies are ISWL with RNA gaps.

### Blank-name root-cause mix (25 policies)

| Cause pattern | Approx. count | Description |
|---------------|---------------|-------------|
| Missing ID (no IN/PO in RNA → blank `MPRIMID`/`MOWNRID`) | 14 | Relationship row absent from `RelationshipNameAddress_Extract` for that policy |
| ID not in `quikclnt` (ID in `quikmstr` but client row missing) | 8 | RNA has names; `quikclnt` conversion did not emit the client |
| Missing owner ID only (insured resolves) | 7 | Partial relationship population |
| `PRIMARY_PERSON = I` leak | **0** | Blocked by v57.28 |

### Example policy 010713704C

| Check | Result |
|-------|--------|
| `PPOLC.PRIMARY_PERSON` | **`I`** (type flag, not client ID) |
| `quikmstr.MPRIMID` / `MOWNRID` | **blank** (v57.28 correctly blocks `I`) |
| RNA rows for policy | **2** — `SA` (servicing org), `BK` (bank) only |
| RNA `IN` / `PO` rows | **0** (LifePRO hierarchy analysis shows `IN\|PA\|PO` exist elsewhere) |
| `quikclid` rows | **2** — `SERV`, `BANK` only |

---

## Artifacts

| File | Rows | Description |
|------|------|-------------|
| `Issue_21D_Interest_Rate_Population.csv` | 2,268 | One row per ISWL policy with plan + rate fields |
| `Issue_21D_Blank_Name_Population.csv` | 25 | Affected policies with insured/owner blank flags |

---

## Intake status

**COMPLETE — read-only.** No code, rulebook, or source changes made. Ready for Planning Agent handoff (see `Issue_21D_Intake_Report.md`).
