# Issue #30 — Missing Name Report

**Issue:** Policy Discovery — Blank / Unresolved Owner & Insured Names  
**Date:** 2026-06-27  
**Converter version analyzed:** v57.36  
**Batch output:** `QLA_Migration/Output/`  
**Analysis type:** Read-only — no code changes

---

## 1. Executive summary

Analysis of the latest v57.36 conversion output identifies **18 policies (0.35% of 5,083)** where the owner and/or insured name is blank or would display as blank/comma-only in QLAdmin.

**All 18 remaining issues originate from missing source relationship data** — specifically absent `IN` and/or `PO` rows in the delivered PRELSA RNA extract. **No policies** in the remaining set are attributable to converter logic defects at v57.36 (quikclnt emit gaps were resolved in Issue #21D Track B1).

| Finding | Result |
|---------|--------|
| Total converted policies | **5,083** |
| Policies with blank/unresolved owner and/or insured | **18** |
| Caused by missing/ambiguous source data | **18 (100%)** |
| Caused by converter logic (v57.36) | **0** |
| `MPRIMID='I'` type-flag leak | **0** |
| Literal punctuation-only names in quikclnt | **0** |

### Recommendation

**Confirm:** Remaining policies are caused by **missing source relationship data**, not a converter defect.

**Recommend:** Track all 18 policies under **Issue #30**. **No additional converter changes are required** unless the client provides updated PRELSA RNA source data or signed business rules for role inference.

---

## 2. Analysis scope

| Source / output | File | Role |
|-----------------|------|------|
| Policy master | `quikmstr.csv` | MPRIMID / MOWNRID |
| Client names | `quikclnt.csv` | Name resolution |
| Relationships | `quikclid.csv` | IN / PO role presence |
| Plan codes | `quikridr.csv` | QL Plan (phase-1 MPLAN) |
| RNA extract | `RelationshipNameAddress_Extract_20260530.csv` | Source IN/PO/PA rows |
| Policy master source | `PPOLC_PolicyMaster_Extract_20260530.csv` | PRIMARY_PERSON context |

---

## 3. Root cause analysis

### 3.1 Root cause distribution

| Root Cause | Policies | Origin layer |
|------------|----------|--------------|
| **Missing Insured relationship** | 12 | Missing source data |
| **Missing Owner relationship** | 6 | Missing source data |
| Missing RNA record | 0 | — |
| Client ID not emitted into quikclnt | **0** | *(resolved v57.36 B1)* |
| PRIMARY_PERSON → non-existent client | **0** | *(v57.28 guard active)* |
| Multiple candidate owners | 0 | — |
| Conversion logic defect | **0** | — |

### 3.2 Origin layer (all affected policies)

| Origin | Count | Description |
|--------|-------|-------------|
| **Missing source data** | **18** | RNA extract lacks IN and/or PO for policy |
| Ambiguous source data | 0 | — |
| Conversion logic | 0 | — |
| Data translation | 0 | — |

### 3.3 Mechanism

1. PRELSA RNA extract does not include `IN` and/or `PO` relationship rows for the policy (confirmed: `HAS_IN_RNA=N` and/or `HAS_PO_RNA=N`).
2. `quikclid` cannot emit insured/owner roles → `rel_map` cannot populate `MPRIMID` / `MOWNRID` on `quikmstr`.
3. QLAdmin Policy Display shows **blank or comma-only** name fields.

**Partial-blank pattern (9 policies):** Insured resolves (IN row in quikclid + quikclnt) but owner blank (PO missing from RNA), or vice versa.

**Both-blank pattern (9 policies):** Neither IN nor PO in RNA or quikclid; both IDs blank on quikmstr.

### 3.4 Relationship to Issue #21D

| Metric | Issue #21D intake (v57.35) | Issue #30 (v57.36) |
|--------|---------------------------|---------------------|
| Affected population | 25 | **18** |
| quikclnt-fixable (B1) | 7 | **0 remaining** |
| RNA-deficient (B2) | 18 | **18** |

Issue #21D Track B1 (v57.36) recovered **7 policies** previously classified as quikclnt gaps. The **18 policies in this report** are the residual RNA-deficient cohort — aligned with Issue #21D Track B2.

---

## 4. Policy list

| Policy | QL Plan | Owner | Insured | Root Cause |
|--------|---------|-------|---------|------------|
| 010422977C | 1960PO | (blank) | (blank) | Missing Insured relationship |
| 010713704C | 1659C2 | (blank) | (blank) | Missing Insured relationship |
| 010713705C | 1659C2 | (blank) | (blank) | Missing Insured relationship |
| 010826551C | 1659CR | (blank) | (blank) | Missing Insured relationship |
| 010948278C | 5667AT | (blank) | (blank) | Missing Insured relationship |
| 014112C | 1SALML | (blank) | (blank) | Missing Insured relationship |
| 018900C | 1SALML | (blank) | (blank) | Missing Insured relationship |
| 010150910C | 221END | (blank) | (blank) | Missing Insured relationship |
| 01ML8151C | 1SALML | (blank) | (blank) | Missing Insured relationship |
| 011188773C | 1L10SO | (blank) | KANEFF, CLEO | Missing Owner relationship |
| 010397945C | 170858 | (blank) | SOUCHEK, MARIAN | Missing Owner relationship |
| 010790779C | 5667AT | (blank) | AASGAARD, JANICE | Missing Owner relationship |
| 010834096C | 1659CR | (blank) | REIGH, DEVONA | Missing Owner relationship |
| 011062307C | 5L0110 | (blank) | GREER, JANIE | Missing Owner relationship |
| 011064567C | 1659CR | (blank) | ANDERSON, MARY | Missing Owner relationship |
| 010774773C | 1659C2 | SECURITY NATIONAL BA, TRUSTEE | (blank) | Missing Insured relationship |
| 010816156C | 1659CR | TUCKER FUNERAL HOME INC | (blank) | Missing Insured relationship |
| 010877890C | 1659SR | THOMPSON, CHRISTOPHER | (blank) | Missing Insured relationship |

Full detail (IDs, RNA flags): `Issue_30_Missing_Name_Policies.csv`

---

## 5. Statistics

| Metric | Value |
|--------|-------|
| Total converted policies | 5,083 |
| Policies with blank owner | **15** |
| Policies with blank insured | **12** |
| Policies with both blank | **9** |
| Policies with partial blank (one role) | **9** |
| Comma-only literal names in quikclnt | **0** |
| QLAdmin comma-only display (blank ID symptom) | **18** |
| Unique root causes | **2** (Missing Insured / Missing Owner relationship) |
| Policies requiring client business review | **18** |
| Policies requiring converter change | **0** |

### By root cause

| Root Cause | Owner blank | Insured blank | Both blank |
|------------|-------------|---------------|------------|
| Missing Insured relationship | 3* | 12 | 9 |
| Missing Owner relationship | 6 | 0 | 0 |

\*Three both-blank policies also list Missing Owner in `All_Causes`; primary label is Missing Insured when both roles absent.

---

## 6. Success criteria assessment

| Criterion | Met? |
|-----------|------|
| Remaining issues caused by missing/ambiguous source data | ✅ **Yes — 100% missing source data** |
| Not caused by converter defect (v57.36) | ✅ **Yes — 0 converter defects** |
| Recommend tracking under Issue #30 | ✅ **Yes** |
| No converter changes without client data/decisions | ✅ **Yes** |

---

## 7. Recommendation

1. **Register all 18 policies under Issue #30** for client tracking and PRELSA re-extract follow-up.
2. **Request client delivery** of updated `RelationshipNameAddress_Extract` with `IN` and `PO` rows for listed policies (reference: `Issue_30_Missing_Name_Policies.csv`).
3. **Do not authorize additional converter changes** — v57.36 B1 resolved all quikclnt emit gaps; remaining gaps are source-data completeness.
4. **Re-batch and re-analyze** after client RNA delivery; expect Issue #30 population to drop to 0 (or documented exceptions if LifePRO lacks IN/PO).
5. **Coordinate with Issue #21D Track B2** — same 18-policy cohort; Issue #30 serves as the master tracking register post-v57.36.

### Client action required

| Action | Owner |
|--------|-------|
| PRELSA RNA re-extract for 18 policies | Client / LifePRO extract team |
| Confirm IN/PO exist in LifePRO for golden policy 010713704C | Client |
| Business review if any policy lacks IN/PO in source system | Client |

---

## 8. Deliverables

| File | Description |
|------|-------------|
| `Issue_30_Missing_Name_Policies.csv` | Full policy-level analysis (18 rows) |
| `Issue_30_Missing_Name_Report.md` | This report |

---

*Issue #30 policy discovery complete. Analysis only — no code modified.*
