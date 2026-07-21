# Stage 4A Source Authority and Plan Universe Report

**Project:** Citizens Product and Rate Conversion  
**Date:** 2026-07-12  
**Issues:** CIT-DATA-001, CIT-PLAN-002  
**Mode:** Business analysis / data governance / planning only

---

## 1. Executive Summary

Stage 4A reconciled the Citizens plan universe without forcing a preferred count. The **union of relevant sources yields 340 distinct raw plan codes**. The familiar **308 (tracker) vs 301 (DBF)** gap **bridges exactly** as 308 − 23 tracker-only + 16 DBF-only = 301. The crosswalk (~156 codes) and reserve wave (138) are **subsets with different purposes**, not competing “true” totals.

Source authority is documented as **PROPOSED / PENDING** across domains. **Nothing was marked AUTHORITATIVE.** Draft Quik output remains **NOT_AUTHORITATIVE**. Working plan_manifest.csv was populated (340 rows) with conservative statuses.

**Stage 4B (CIT-ARCH-001 / CIT-ENGINE-001) may proceed** under neutrality: configuration and Engine pin must not encode unapproved business assumptions.

---

## 2. Stage Verdict

### **PASS WITH REVIEW ITEMS**

Universe reconciled and bridged; authority proposals and 20 decision records seeded; client/actuarial approvals still required.

---

## 3. Input-Validation Result

**PASS** — `reports/governance/Stage4A_Input_Validation_Report.md`

All required Stage 3 outputs, tracker, DBF extract, crosswalk, requirements catalog, reserve staging, draft outputs, product docs, and Access extracts were present and readable.

---

## 4. Source-Register Summary

**File:** `manifests/source_authority_register.csv` — **16** registered sources (SA-001…SA-016)

| Status used | Examples |
|-------------|----------|
| PENDING_REVIEW | Plans DBF, Reserve DBF |
| DERIVED_WORKING | Tracker, catalog, crosswalk, staging, assumptions |
| SUPPORTING | CV ZIPs, Access MDB, product catalog |
| VALIDATION_ONLY | Access CSV checkpoints |
| NOT_AUTHORITATIVE | Draft Quik, OCR |
| HISTORICAL | SourceData dump |

---

## 5. Source Authority by Domain

**File:** `reports/governance/source_authority_by_domain.csv`

High-confidence **proposals** (still not approved): Reserve DBF for CV / terminal reserve / net / PU; Access for gross premium validation/source; Plans DBF for plan identity and loan-IR/fee candidates.

**Domains lacking identified primary authority (MISSING_AUTHORITY=Y):** participating status, interest-sensitive status, issue-date range, ETI, dividends, most credited/guaranteed interest, COI/expenses/loads/surrender/modal/guideline/MEC/target/settlement, client UAT — **12+ domains** flagged unknown or missing.

Full narrative: `SOURCE_AUTHORITY.md`.

---

## 6. Plan-Universe Reconciliation

**File:** `reports/governance/plan_universe_master_reconciliation.csv` — **340** rows

| Reconciliation status | Count |
|----------------------|------:|
| FULLY_MATCHED (also mapped) | 154 |
| MISSING_MAPPING (in tracker∩DBF but no QLAdmin map) | 131 |
| TRACKER_ONLY | 23 |
| DBF_ONLY | 16 |
| RESERVE_STAGING_ONLY | 15 |
| CROSSWALK_ONLY | 1 |

Identity match tracker∩DBF = 154 + 131 = **285**.

---

## 7. Explanation of 308 Versus 301

**File:** `reports/governance/plan_count_bridge_308_to_301.csv`

```
308 tracker
− 23 tracker-only
+ 16 DBF-only
= 301 DBF
```

**Residual: 0.** Differences are fully listed (not buried in “other”).

### Tracker-only (23)

`802N,802P,802Q,802R,9R1F,9R1M,9R5F,9R5M,B1MN,B1MS,B2FS,B2MS,B3FS,B3MS,CFA4,CFA7,DR1F,DR1M,DR5F,DR5M,R29,R69,RW9`

Likely: requirements additions, aliases, or missing master rows — **CIT-DEC-002**.

### DBF-only (16)

`$GS2,100V,802E,9PFM,BAYN,CFA0,CTRP,DR6G,DX1F,DX51,DX5F,DX5M,FBAF,GS28,HIV,MEB`

Likely: administrative/special/out-of-scope candidates — **CIT-DEC-003**. Do not auto-exclude.

No material case/whitespace-only duplicates found between sets (normalized distinct count = raw distinct = 340).

---

## 8. Crosswalk Coverage Explanation

**File:** `reports/governance/crosswalk_coverage_analysis.csv`

- **111** spreadsheet rows → **156** expanded CFIC codes  
- Purpose: **working QLAdmin mapping subset**, often grouping sex/smoker variants to one QLPlan  
- **Not** “only 156 plans exist”  
- Incomplete vs 308/301 by design today — **CIT-DEC-004**

---

## 9. Reserve-Staging Coverage Explanation

**File:** `reports/governance/reserve_staging_coverage_analysis.csv`

- **138** plans staged; **138** listed in draft `emit_summary.json`  
- Interpretation: **reserve extract/emit wave subset** from `cifi0007`  
- Absence of a plan from staging ≠ “reserves not applicable”  
- 15 codes appear reserve/draft without tracker/DBF membership — flagged `RESERVE_STAGING_ONLY` / pending source

---

## 10. Alias and Relationship Candidates

**File:** `reports/governance/plan_alias_and_relationship_candidates.csv` — **75** candidates

Types include: sex/smoker variation families, QLAdmin consolidations from crosswalk grouped cells, format variations if any.

**No merges performed.**

---

## 11. Rate-Requirement Authority Findings

**File:** `reports/governance/plan_rate_requirement_authority_matrix.csv`

Controlled cell values applied from catalog/tracker plus reserve/draft evidence enrichment (e.g. `REQUIRED_CONVERTED_DRAFT` for staged+draft CV/reserve/net).

Applicability is **not** inferred solely from file presence; catalog “Not expected” → `NOT_APPLICABLE`; unknowns remain distinct.

---

## 12. Populated Working Plan-Manifest Summary

**File:** `manifests/plan_manifest.csv` — **340** rows

- Statuses conservative (`READY_FOR_REVIEW`, `IN_PROGRESS`, `NOT_STARTED`)  
- Draft Quik ≠ completion (`CONVERSION_STATUS=IN_PROGRESS` only when draft present)  
- Extra governance columns added per Stage 4A spec  
- **Not** client-approved

---

## 13. Proposed Decision-Log Entries

**File:** `DECISION_LOG.md` — **CIT-DEC-001 … CIT-DEC-020** all **PROPOSED**

---

## 14. Source-Authority Documentation Updates

**File:** `SOURCE_AUTHORITY.md` — populated with proposed primary/secondary/validation sources, conflict rules, gaps, and decision links. No `AUTHORITATIVE` seals.

---

## 15. Blocking Decisions

**File:** `reports/governance/Stage4A_Blocking_Decisions_Register.csv`

| Level | Examples |
|-------|----------|
| BLOCKS_BEFORE_CONVERSION | Authority for CV/reserve/GP; mapping completeness for emit |
| BLOCKS_BEFORE_UAT / RELEASE | Client active/historical; approval process |
| NONBLOCKING | Draft status (already clear); SourceData historical; reporting standard |
| Does **not** block Stage 4B config/engine | CIT-DEC-004 incompleteness; most rate authorities if Engine kept neutral |

---

## 16. Nonblocking Review Items

- Quarantine `cifianu1` / `AgentName` disposition  
- Neutralize remaining “CSO-style” wording in legacy docs  
- Refine Access-family linkage flags  
- Confirm whether DBF-only codes like `$GS2` / `HIV` are administrative

---

## 17. Controlled Plan-Count Recommendation

**File:** `reports/governance/controlled_plan_count_recommendation.md`

Executive citation should always state **multiple** populations (340 union / 285 matched / 308 tracker / 301 DBF / 156 crosswalk / 138 reserve wave).

---

## 18. Counts by Scope Category (Proposed)

| Scope | Count |
|-------|------:|
| IN_SCOPE_BASE_PLAN | 288 |
| IN_SCOPE_RIDER | 36 |
| IN_SCOPE_PENDING_SOURCE | 15 |
| REQUIRES_REVIEW | 1 |
| OUT_OF_SCOPE | 0 (none auto-assigned) |

---

## 19. Plans Missing QLAdmin Mappings

**~184** in-scope codes without crosswalk/tracker QL plan — mapping backlog (does not block Engine pin).

---

## 20. Plans Missing Rate Requirements

Tracker/catalog cover **308**; DBF-only and some staging-only codes lack requirement rows — review via CIT-DEC-003 and staging-only list.

---

## 21. Plans Missing Identified Rate Sources

**~199** in-scope without reserve staging and without matching CV ZIP family — many may still be “required but source pending” or N/A pending actuarial.

---

## 22. Rate Types / Domains Lacking Source Authority

From domain matrix: **≥12** domains with `MISSING_AUTHORITY=Y` or UNKNOWN primary (ETI, dividends, most interest beyond loan IR candidate, COI/expenses/modal/guideline family, participating/IS flags, issue dates, UAT).

Reserve CV/TV/NP/PU have **proposed** DBF primary (pending actuarial). Gross premium has **proposed** Access primary.

---

## 23. Required Client Decisions

CIT-DEC-001, 002, 003, 007, 008, 016 (participating), 020; classification of DBF-only admin codes; confirm Access “ACTIVE” note at plan-code level.

---

## 24. Required Actuarial Decisions

CIT-DEC-009–017; OBQ-1/OBQ-2; mean reserve; ETI; sex/smoker member design (CIT-DEC-005).

---

## 25. Required Internal Decisions

CIT-DEC-004 mapping workplan; CIT-DEC-018/019 already proposed; Stage 4B sequencing; whether v1 defers dividends/ETI/COI.

---

## 26. Recommended Stage 4B Entry Criteria

| Criterion | Met? |
|-----------|------|
| Plan universe sufficiently understood | **YES** — bridge closed; subsets explained |
| Source authority gaps documented | **YES** |
| Immediate blockers identified | **YES** — conversion blocked; config/engine not |
| Config will not encode unapproved business rules | **YES if** paths/engine only |
| Engine integration business-rule neutral | **YES if** Option A pin without Citizens rate rules |

**Stage 4B may proceed:** **YES** (CIT-ARCH-001 + CIT-ENGINE-001 only).

---

## 27. Recommended Stage 4B Execution Order

1. CIT-ARCH-001 — project root + path configuration (replace `legacy_cfic_paths` / `sys.path` hacks)  
2. CIT-ENGINE-001 — pin Enterprise Engine package (Option A)  
3. Parallel: client/actuarial review of CIT-DEC-001…003, 009…013  
4. Later: CIT-ENGINE-002 retarget active scripts; CIT-PLAN-001 finalize manifests after approvals

---

## 28. Exact Next Cursor Prompt

```text
You are executing Stage 4B — CIT-ARCH-001 and CIT-ENGINE-001 only.

Work in:
C:\Users\warren\Documents\GitHub\Warrenhughes1974\Citizens_Product_Rate_Conversion

Authority: Stage4A_Source_Authority_and_Plan_Universe_Report.md allows Stage 4B
because plan-universe differences are explained and Engine/config work can remain
business-rule neutral.

Scope:
1. Implement config-driven project paths (source_locations, output_locations, citizens.yaml stubs).
2. Document and implement Enterprise Engine Option A version pin in engine_version.yaml
   (install instructions only if authorized; do not vendor-copy qla_core).
3. Do NOT encode plan counts, rate applicability, or mappings as approved facts.
4. Do NOT run conversion, do NOT publish Quik files, do NOT populate mappings/approved,
   do NOT approve DECISION_LOG entries, do NOT modify CFIC_Rates, do NOT initialize Git
   unless explicitly authorized in this prompt.

Use Composer 2.5 if framework Development model is required for code changes.
```

---

## 29–33. Confirmations

| Item | Status |
|------|--------|
| No conversion logic changed | **YES** |
| No conversion executed | **YES** |
| qla_core not modified/installed | **YES** |
| Git not initialized | **YES** |
| CFIC_Rates not modified | **YES** |

---

## Artifact Index

| Artifact | Path |
|----------|------|
| Input validation | `reports/governance/Stage4A_Input_Validation_Report.md` |
| Source register | `manifests/source_authority_register.csv` |
| Authority by domain | `reports/governance/source_authority_by_domain.csv` |
| Master reconciliation | `reports/governance/plan_universe_master_reconciliation.csv` |
| 308↔301 bridge | `reports/governance/plan_count_bridge_308_to_301.csv` |
| Crosswalk coverage | `reports/governance/crosswalk_coverage_analysis.csv` |
| Reserve coverage | `reports/governance/reserve_staging_coverage_analysis.csv` |
| Alias candidates | `reports/governance/plan_alias_and_relationship_candidates.csv` |
| Rate requirement matrix | `reports/governance/plan_rate_requirement_authority_matrix.csv` |
| Plan manifest | `manifests/plan_manifest.csv` |
| Blocking register | `reports/governance/Stage4A_Blocking_Decisions_Register.csv` |
| Count recommendation | `reports/governance/controlled_plan_count_recommendation.md` |
| Validation | `reports/governance/Stage4A_Validation_Report.md` |
| Decision log | `DECISION_LOG.md` |
| Source authority | `SOURCE_AUTHORITY.md` |

---

*Stage 4A complete — 2026-07-12*
