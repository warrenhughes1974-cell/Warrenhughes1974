# Issue #48 — Planning Report

**Issue:** #48 — Secondary Rate File (PAAGERAT fallback)  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning complete — Ready for Dependency Gate  
**Generated:** 2026-07-10  
**Agent:** Planning Agent (read-only analysis)  
**Diagnostic:** `Issue_Log_Items/Issue_48/_research_issue48_fallback_inventory.py`  
**Evidence:** `evidence/issue48_source_identity.txt`, `evidence/issue48_fallback_inventory.csv`

---

## 1. Executive Finding

Client rule: when rates are **absent from PAAGERAT**, examine secondary Source file `Rate_Table_Extract_Txt.txt` before treating the rate as missing.

Intake proved that file is **byte-identical** to the Rate_Table extract the pipeline already uses (`Rate_Table_Extract_20260427.csv`). It adds **no new rows** and does **not** close Issue #42 gaps.

Today’s rate pipeline already streams **both** sources into the same factor grids:

1. `rate_factor_loader.transform_source(source_rate_extract)` — Rate_Table age × duration  
2. PAAGERAT loaders (PR / NF / BP / U5 / U6) — attained-age SEQ  

So Issue #48 is **not** “add a missing extract.” It is:

1. **Wire** Source-folder `Rate_Table_Extract_Txt.txt` as a first-class rate path (client delivery location).  
2. **Codify precedence** for shared TYPE_CODEs: PAAGERAT wins when present for a resolved PLAN; Rate_Table fills only when PAAGERAT has no usable rows for that PLAN/TYPE.  
3. **Do not** invent grain conversion (age×duration ↔ attained SEQ) or use Rate_Table for PAAGERAT-only TYPE_CODEs (BP, U5, U6, NC, PU, RD, YP).

**Recommended next stage:** Dependency Gate (confirm scope assumptions below), then Risk.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|--------------|--------------|---------------------|----------:|
| Rate_Table (secondary / client-named) | `Rate_Table_Extract_Txt.txt` | **Yes** | 1,128,984 |
| Rate_Table (existing twin) | `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv` | Twin (not Source/) | 1,128,984 (identical MD5) |
| PAAGERAT (primary attained-age) | `PAAGERAT_AttainedAge_Rates_Extract_20260630.csv` | **Yes** | 24,424 |
| Segment link | `PCOVRSGT_CoverageSegment_Extract_20260630.csv` | **Yes** | required for PAAGERAT resolve |
| Coverage | `PCOVR_Coverage_Extract_20260630.csv` | **Yes** | PAAGERAT enrich |
| Crosswalk | `Policy Form Crosswalk 5.22.26.xlsx` | plan_analysis | COVERAGE_ID → PLAN |

### Available source fields

| Field | Rate_Table | PAAGERAT | Notes |
|-------|------------|----------|-------|
| Coverage / segment ID | `COVERAGE_ID` (parent-style) | `COVERAGE_ID` (= `PCOVRSGT.SEGT_ID`) | Different ID grain |
| Rate type | `TYPE_CODE` | `TYPE_CODE` | Shared: CV, DB, NF, NP, PR, RV |
| Axes | `AGE`, `DURATION` | `SEQ` (attained), `RECORD_SEQ` | **Incompatible grids** |
| Sex / band / UW | `SEX`, `BAND`, `UNDERWRITING_CLASS` | `SEX`, `BAND`, `UWCLS` | Mappable via existing crosswalks |
| Value | `VALUE` | `VALUE_INFO` (authoritative) | |

### TYPE_CODE vocabulary (measured)

| Bucket | TYPE_CODEs |
|--------|------------|
| Rate_Table only | DV, NN, PN, SL, TP, TX, UF |
| PAAGERAT only | BP, NC, PU, RD, U5, U6, YP |
| Shared | CV, DB, NF, NP, PR, RV |

Exact `(COVERAGE_ID, TYPE_CODE)` overlap between files is near-zero for shared types because PAAGERAT keys are **segments**, Rate_Table keys are **parent coverages**. Segment-aware check: most Rate_Table parents have **no** linked PAAGERAT segment for the same TYPE (expected — Rate_Table already supplies those plans today).

---

## 3. Confirmed QLAdmin Target Structure

| Table | TYPE_CODE | Source path today | Grid mode |
|-------|-----------|-------------------|-----------|
| `QuikCvs` | CV | Rate_Table (+ #40 inheritance) | Issue-age × duration |
| `QuikNps` | NP | Rate_Table (+ shared/inheritance) | Issue-age × duration |
| `QuikTvs` | RV | Rate_Table | Issue-age × duration |
| `QuikDbs` | DB | Rate_Table | Issue-age × duration |
| `QuikDvs` | DV | Rate_Table only | Issue-age × duration |
| `QuikGps` | PR | Rate_Table **and** PAAGERAT PR | Age×dur **or** VARGP=3 attained |
| `QuikNff` | NF | Rate_Table **and** PAAGERAT NF | Age×dur **or** attained |
| `QuikGps` | BP | PAAGERAT only (ISWL Phase 2) | VARGP=3 attained |
| `QuikCoi` / `QuikGcoi` | U6 / U5 | PAAGERAT only | VARGP=3 attained |

**Repo references:**

| Location | Role |
|----------|------|
| `qla_core/rate_pipeline.py` | Orchestrates Rate_Table stream then PAAGERAT streams |
| `qla_core/rate_factor_loader.py` | Rate_Table transform + pivot |
| `qla_core/paagerat_pr_loader.py` | PAAGERAT PR / NF attained-age |
| `qla_core/paagerat_bp_loader.py` / `paagerat_ul_coi_loader.py` | BP / U5 / U6 |
| `qla_core/plan_source_paths.py` | Resolves Rate_Table + PAAGERAT paths (Source `.txt` **not** listed) |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | `source_rate_extract` → twin CSV; `paagerat_pr_extract` → older PAAGERAT dated file |
| `qla_core/rate_dbf_schema.py` | `TYPE_TO_TABLE`, excluded codes |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field / key | QLAdmin target | Transformation | Change? |
|----------------|---------------------|----------------|----------------|---------|
| PAAGERAT (when present for PLAN+TYPE) | TYPE + SEQ + VALUE_INFO | QuikGps / QuikNff / COI tables | Existing attained-age loaders | **No** (keep authority) |
| Rate_Table secondary (when PAAGERAT absent for PLAN+TYPE) | TYPE + AGE + DURATION + VALUE | Same `TYPE_TO_TABLE` factor table | Existing age×duration loader | **Precedence / audit only** |
| Source path | `Rate_Table_Extract_Txt.txt` | `source_rate_extract` / `rate_table_extract()` | Prefer Source `.txt`, else twin CSV | **Yes** (path resolve) |
| PAAGERAT-only types BP/U5/U6/… | — | QuikGps BP / QuikCoi / QuikGcoi | No Rate_Table fallback | **No** |

### Proposed precedence rule (Development blueprint)

```
For each (PLAN, TYPE_CODE) in shared set {PR, NP, CV, RV, NF, DB}:
  if PAAGERAT yields IN_SCOPE rows for that PLAN+TYPE (after segment resolve):
      emit PAAGERAT (existing) — Rate_Table must not override / collide
  else if Rate_Table yields IN_SCOPE rows for that PLAN+TYPE:
      emit Rate_Table — tag source = RATE_TABLE_SECONDARY / PAAGERAT_MISS
  else:
      rate remains missing (Issue #42-style gap)
```

**Important:** Rate_Table is already streamed unconditionally today. Planning recommends making the rule **explicit and collision-safe** (suppress or skip Rate_Table cells when PAAGERAT already owns the PLAN+TYPE), plus Source-path wiring — not a second full Rate_Table load.

### Fields / behaviors that must remain unchanged

| Target / rule | Current source | Touch this issue? |
|---------------|----------------|-------------------|
| #25 MPOLICY padding | `format_qladmin_mpolicy` | **No** |
| #26 `quikridr.MPREM` | ANN_PREM_PER_UNIT fallback | **No** |
| #31 ISWL BP/U5/U6/PR suppress | PAAGERAT allowlists | **No** — do not let Rate_Table PR override BP plans |
| #37 / #41 CV duration placement | Rate_Table CV | **No** logic change |
| #40 CV inheritance | `cv_inheritance_loader` | **No** |
| #42 missing L01/L10 rows | CSO extract | **No** — this file does not fill them |
| Policy tables (quikmstr/ridr/…) | — | **No** |

### Proposed implementation shape (Development — do not implement yet)

1. Extend `plan_source_paths.rate_table_extract()` candidate list:  
   `QLA_Migration/Source/Rate_Table_Extract_Txt.txt` → dated twin CSV.  
2. Align `rate_loader_config.json` / batch config `source_rate_extract` to Source file (or resolver).  
3. Optionally align `paagerat_pr_extract` to Source `PAAGERAT_…_20260630.csv` (separate hygiene; call out in Risk).  
4. Add PLAN+TYPE ownership set from PAAGERAT stream; when building Rate_Table grids for shared types, skip/suppress rows whose PLAN+TYPE is already PAAGERAT-owned (prevents V03 collisions if both ever resolve to same PLAN).  
5. Emit audit CSV: `paagerat_miss_rate_table_secondary_used.csv` (PLAN, TYPE, coverage_id, row counts).  
6. Version bump both `app.py` copies if engine path touched.

---

## 5. Open Client Questions

1. **Precedence confirmation:** When PAAGERAT has rates for a PLAN+TYPE, must Rate_Table always yield (never merge/override)? Planning assumes **yes**.  
2. **Fallback TYPE scope:** Confirm fallback applies only to shared types `{PR, NP, CV, RV, NF, DB}` that already map via `TYPE_TO_TABLE` — **not** BP/U5/U6/NC/etc.  
3. **Grain:** Confirm we must **not** reshape Rate_Table age×duration into PAAGERAT attained-age SEQ (VARGP=3) when falling back — use existing Rate_Table Quik grid rules.  
4. **Source of truth path:** Prefer `Source/Rate_Table_Extract_Txt.txt` over `plan_analysis/.../Rate_Table_Extract_20260427.csv` when both exist (identical today)?  
5. **Example products:** Any specific plans the BA expects to light up from this secondary file (none provided at intake)?

Questions 1–3 can be accepted as **Planning assumptions** at Dependency Gate if client is silent; Risk should still quantify collision/blast radius.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | N/A for rate tables (PLAN keys, not MPOLICY) |
| PLAN | Crosswalk + existing segment resolve; preserve #28 catalog authority |
| Factor CHAR(7) / NFF/COI widths | Existing `rate_dbf_schema` formatters — no change |
| AGE cap >99 → 99 | Existing audited rule — no change |
| Blanks / missing | If neither PAAGERAT nor Rate_Table has PLAN+TYPE → leave missing; do not invent zeros |
| Source audit tag | Record `PAAGERAT` vs `RATE_TABLE_SECONDARY` on emit/trace |

---

## 7. Memo / Text / Special Handling

N/A — rate factor tables only.

---

## 8. Policy Number Key Handling

1. Rate emit is **PLAN-keyed**, not policy-keyed.  
2. Policy conversion (#25 MPOLICY padding) must not change.  
3. Orphan / unmapped COVERAGE_ID: existing reject / PLAN_INVALID paths — no new orphan policy behavior.

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| Secondary Rate_Table rows | 1,128,984 | Source `.txt` |
| Distinct Rate_Table coverages | 65 | Inventory |
| Distinct Rate_Table (cov, type) keys | 212 | Inventory |
| PAAGERAT rows | 24,424 | Source 20260630 |
| Shared TYPE_CODEs | 6 | CV, DB, NF, NP, PR, RV |
| Rate_Table PR coverages with no PAAGERAT link | 10 | DISCHO* + L01 10Y MA (665 STME95 has link) |
| New unique rate rows vs twin CSV | **0** | MD5 identity |
| Policies affected | N/A (plan-rate tables) | No policy examples provided |

**Net emit impact expectation:** Path wiring alone → **zero** row-count change (identical bytes). Precedence/collision hardening → may **reduce** duplicate risk; may change which source “owns” a PLAN+TYPE only if both currently resolve (rare on exact IDs; segment resolve needs Risk quantification).

---

## 10. Sample Trace (coverage-level — no policies provided)

| Coverage (Rate_Table) | TYPE | PAAGERAT present? | Before (today) | After (proposed) | Status |
|-----------------------|------|-------------------|----------------|------------------|--------|
| `DISCHO25` | PR | No (no segment PR link) | Rate_Table PR already streamed if crosswalked | Same emit; tag `RATE_TABLE_SECONDARY` | Candidate |
| `L01 10Y MA` | PR / NP / RV | PAAGERAT has `L01 10Y LT` PR only (different ID) | Rate_Table MA rows load; LT NP still missing (#42) | Unchanged for #42 NP gap | Partial |
| `L10 LP95` | NP / CV / RV | PAAGERAT PR on segment; not NP/CV/RV | Rate_Table NP/CV/RV already primary | Keep Rate_Table; PAAGERAT PR stays for premium | No conflict expected |
| `658 CEN I` | CV / NP / … | 0 PAAGERAT rows historically for some ISWL | Rate_Table supplies CV/NP where present | Explicit secondary after PAAGERAT miss | Candidate |
| `L10 LP9595` | NP / RV | Absent both extracts | Missing | Still missing (#42) | Out of scope |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Client expects new rates; file is identical twin | Medium | Document in Dependency Gate; set expectation |
| Dual stream collision (Rate_Table + PAAGERAT → same Quik cell) | High | PLAN+TYPE ownership suppress; keep V03 blocker |
| Accidental Rate_Table override of ISWL BP/COI authority (#31) | High | Exclude BP/U5/U6 from fallback; preserve suppress lists |
| Misreading “PAAGERAT first” as dropping Rate_Table primary for CV/NP | High | Only suppress Rate_Table when PAAGERAT **owns** that PLAN+TYPE |
| Config still points at older PAAGERAT dated path | Medium | Hygiene item in Dev task; Risk notes |
| Grain conversion pressure from BA | High | Explicit No-Go without actuarial sign-off |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present (`Rate_Table_Extract_Txt.txt`) | **Yes** |
| PAAGERAT + PCOVRSGT + PCOVR present | **Yes** |
| Field / schema definitions confirmed | **Yes** (Rate_Table + PAAGERAT known) |
| Client scope clear (fallback TYPE set + no grain convert) | **Partial** — assumptions proposed; Gate may accept or ask client |
| Example policies available | **No** — soft; coverage traces substitute |
| QLAdmin target undefined | **No** — targets known |
| Duplicate of #42 | **No** — related but distinct |

**Gate expectation:** PASS WITH ASSUMPTIONS (or CONDITIONAL if client must confirm Q1–Q3).

---

## 13. Recommended Risk Agent Prompt

```
Risk Agent — Issue #48: Secondary Rate File (PAAGERAT fallback)

Read AI_Agents/Risk_Agent.md and Issue_Log_Items/Issue_48/Issue_48_Planning_Report.md.
Also read Intake summary and evidence/issue48_*.

No code. No rulebook edits. No batch emit.

Quantify:
1. Blast radius of wiring Source/Rate_Table_Extract_Txt.txt (expect 0 row delta vs twin).
2. PLAN+TYPE pairs where both Rate_Table and PAAGERAT can resolve after segment chain
   (collision candidates for QuikGps PR / QuikNff NF).
3. Impact of suppressing Rate_Table when PAAGERAT owns PLAN+TYPE.
4. Regression risk to #31 ISWL, #37/#40/#41 CV, #42 gaps (must remain open).
5. Go / Conditional-Go / No-Go with fallback rules.

Deliver Issue_48_Risk_Review_Report.md (+ optional simulation CSV).
```

---

## 14. Recommended Development Task (Do Not Implement)

1. Update `qla_core/plan_source_paths.rate_table_extract()` to prefer  
   `QLA_Migration/Source/Rate_Table_Extract_Txt.txt`, then existing twin CSV.  
2. Point rate loader config `source_rate_extract` at Source path (or rely on resolver).  
3. Implement PAAGERAT PLAN+TYPE ownership set; suppress Rate_Table shared-type emit when owned (surgical, in pipeline stream or grid build).  
4. Write audit: `Reports/` or `Issue_48/evidence/` — secondary-used + suppressed-collision rows (**not** in `Output/`).  
5. Version bump: both root `app.py` and `QLA_Migration/app.py` if engine path touched.  
6. Validation script: `QLA_Migration/_validate_issue48_secondary_rate.py`  
   - MD5/path resolve picks Source file  
   - Sample DISCHO25 / L01 10Y MA still emit from Rate_Table when PAAGERAT miss  
   - No new QuikCvs/QuikNps regression vs baseline for PAAGERAT-owned plans  
   - #42 keys still absent  

---

## Appendix

- Diagnostic script: `Issue_Log_Items/Issue_48/_research_issue48_fallback_inventory.py`  
- Related issues: #31, #37, #40, #41, #42, rate inheritance validation  
- References: `qla_core/rate_pipeline.py`, `rate_segment_resolution.py`, `rate_dbf_schema.py`  
- G1 checklist: Planning report published; sources/targets documented; coverage traces included; open questions enumerated; Development outlined but **not** executed; **no** code/rulebook/output changes beyond this report + research artifacts
