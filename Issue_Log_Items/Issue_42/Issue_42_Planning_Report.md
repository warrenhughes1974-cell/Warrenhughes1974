# Issue #42 — Planning Report

**Issue:** #42 — Missing Rate Extract Rows (L01/L10)  
**Framework stage:** Planning Agent  
**Status:** Blocked — Awaiting load-path decision (PDAGE vs Rate_Table refresh)  
**Generated:** 2026-07-13  
**Agent/script:** Intake/Planning on Cursor Grok 4.5 · `_scan_20260713_rate_extracts.py`

---

## 1. Executive Finding

CSO’s 2026-07-13 LifePRO extracts **do contain** the Issue #42 missing age/duration rows: `L01 10Y` NP/RV (2,544 each) and `L10 LP9595` NP/RV (6,192 each) in `PDAGE_AgeDuration_Rates_Extract_20260713.csv`. The production age/duration loader still reads `Rate_Table_Extract_Txt.txt`, which has **zero** of those coverage IDs. This is no longer a “rows do not exist in LifePRO extracts” problem for #42 — it is a **source-path / grain-mapping** problem so QuikNps/QuikTvs can emit. Eric’s residual CV gaps (`L17` CV, `960 LP85-8` CV) remain true source absences; New Era’s “no NP” for `0824 P DTH` and `L10 GPO OL` matches our scan.

**Direction:** Prefer Option A (point/merge age-duration load to PDAGE 20260713 for missing Rate_Table keys) or Option B (CSO regenerates Rate_Table twin including these IDs). Do **not** invent rates. Stop before Development until Dependency Gate records the chosen option.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/? | Row count (file) | #42 keys |
|--------------|--------------|-------------|------------------:|----------|
| Age/Duration (PDAGE) | `PDAGE_AgeDuration_Rates_Extract_20260713.csv` | Yes | 338,644 | L01 10Y NP/RV; L10 LP9595 NP/RV **present** |
| Age/Duration (prior) | `PDAGE_…_20260630.csv` | Yes | 250,769 | #42 keys **absent** |
| Rate_Table (loader) | `Rate_Table_Extract_Txt.txt` | Yes | 1,128,985 | #42 keys **absent** |
| Attained-age (PAAGERAT) | `PAAGERAT_…_20260713.csv` | Yes | 32,109 | #42 NP/RV **absent** (PR-only for related IDs) |
| Attained-age (resolver today) | `PAAGERAT_…_20260630.csv` | Yes | 24,425 | Prefer path still points here |

### Available source fields (PDAGE vs Rate_Table)

| Field | PDAGE | Rate_Table | Notes |
|-------|-------|------------|-------|
| COVERAGE_ID | Yes | Yes | Exact match keys for #42 |
| TYPE_CODE | Yes | Yes | NP, RV |
| AGE / SEX / BAND / DURATION | Yes | Yes | Compatible grain |
| UW class | `UWCLS` | `UNDERWRITING_CLASS` | Rename on merge |
| Value | `VALUE1` (+ VALUE2–10) | `VALUE` | #42 samples use VALUE1; STORAGE_FORMAT=`D` |
| VALUE_FLOAT | `VALUE1_FLOAT` | n/a | Sample floats were 0.0; use VALUE1 text |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field / role | Source |
|-------|--------------|--------|
| `QuikNps` | Net premium factor grid | Rate TYPE_CODE NP → QuikNps (`rate_dbf_schema.TYPE_TO_TABLE`) |
| `QuikTvs` | Terminal/reserve factors | Rate TYPE_CODE RV → QuikTvs |
| Plan keys | `5L0110` for L01 10Y LT; L10 LP95 family via crosswalk | Catalog / PCOVRSGT segment refs |

**Repo references**

| Location | Role |
|----------|------|
| `qla_core/plan_source_paths.rate_table_extract()` | Prefers `Source/Rate_Table_Extract_Txt.txt` |
| `qla_core/plan_source_paths.paagerat_extract()` | Prefers PAAGERAT **20260630** (not 20260713) |
| `plan_analysis/.../rate_loader_config.example.json` | `source_rate_extract` + unused-looking `pdage_extract` |
| `qla_core/rate_dbf_schema.py` | NP→QuikNps, RV→QuikTvs |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PDAGE (or refreshed Rate_Table) | `L01 10Y` NP rows | QuikNps under `5L0110` | Existing age/duration emit | **Yes** — source must be visible to loader |
| PDAGE (or refreshed Rate_Table) | `L10 LP9595` NP/RV | QuikNps / QuikTvs for L10 LP95 catalog plans | Existing emit + segment→plan join | **Yes** — source must be visible |
| PAAGERAT | n/a for #42 NP/RV | — | Not authority for these duration tables | No |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| quikmstr.MMODPREM | PPOLC (#26 guard) | **No** |
| quikridr.MPREM | #26 mapping | **No** |
| MPOLICY padding | #25 | **No** |
| Existing Rate_Table keys already loading | Rate_Table_Txt | **No** — additive only |
| Issue #40/#41 CV inheritance | QuikCvs paths | **No** |

### Options (Development must pick one after Risk)

| Option | Description | Blast radius |
|--------|-------------|--------------|
| **A** | Prefer/merge PDAGE 20260713 for coverage+TYPE missing from Rate_Table | Path + optional merge helper; regression on all rates if mis-wired |
| **B** | CSO delivers Rate_Table twin that includes L01 10Y / L10 LP9595; keep loader as-is | Lowest converter change; depends on CSO |
| **C** | Replace Rate_Table entirely with PDAGE as primary age/duration source | Highest risk; needs full parity proof |

**Recommendation for Risk:** Prefer **A** (surgical miss-fill from PDAGE) or **B** if CSO can turn PDAGE around into Rate_Table quickly. Avoid C unless parity proven.

---

## 5. Open Client Questions

1. Confirm New Era will still deliver **`L17` CV** and **`960 LP85-8` CV** age/duration rows (Eric already flagged).
2. For **`960 LP85-8`**: confirm only **CV** remains outstanding (NP=1,128 and RV=1,128 now in PDAGE 20260713).
3. Accept New Era finding that **`0824 P DTH` NP** and **`L10 GPO OL` NP** do not exist in LifePRO (QLA scan agrees — only PR in PAAGERAT)?
4. Prefer **Rate_Table re-extract** (Option B) vs QLA **PDAGE miss-fill** (Option A) for loading L01/L10 LP9595?

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | N/A (plan-level rates); #25 preserved elsewhere |
| Coverage ID | Exact string match (`L01 10Y`, `L10 LP9595`) |
| Value | Use PDAGE `VALUE1` → Rate_Table `VALUE` / existing emit path |
| Blanks / zeros | Do not invent NP for 0824 / L10 GPO OL |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

Not applicable to rate-table emit. Preserve #25/#26 on any future policy-touching work.

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| `L01 10Y` NP PDAGE rows | 2,544 | Scan 20260713 |
| `L01 10Y` RV PDAGE rows | 2,544 | Scan 20260713 |
| `L10 LP9595` NP PDAGE rows | 6,192 | Scan 20260713 |
| `L10 LP9595` RV PDAGE rows | 6,192 | Scan 20260713 |
| Same keys in Rate_Table_Txt | 0 | Scan |
| QuikNps keys for `5L0110` today | 0 (prior proof) | Client L01 follow-up report |

---

## 10. Sample Trace (plan-level)

| Plan / coverage | Before (Rate_Table) | After (if PDAGE wired) | Status |
|-----------------|---------------------|------------------------|--------|
| `L01 10Y` NP → `5L0110` QuikNps | 0 rows | 2,544 source rows available | Pending path |
| `L10 LP9595` NP | 0 rows | 6,192 available | Pending path |
| `L10 LP9595` RV | 0 rows | 6,192 available | Pending path |
| `L17` CV | 0 | 0 | Still CSO |
| `960 LP85-8` CV | 0 | 0 | Still CSO |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Wiring PDAGE incorrectly overwrites good Rate_Table keys | High | Miss-fill only where Rate_Table count=0 |
| PDAGE VALUE1–10 / STORAGE_FORMAT grain vs Rate_Table VALUE | Medium | Pilot emit for L01/L10 LP9595 only; compare to LifePRO screenshots |
| PAAGERAT path still on 20260630 | Medium | Separate small path bump to 20260713 (may be #48 follow-on) |
| Remaining CV gaps treated as converter defects | Low | Document as CSO/New Era source |

---

## 12. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue #42.

Read AI_Agents/Risk_Agent.md.
Model: Cursor Grok 4.5. Do not code.

Quantify before/after impact of Option A (PDAGE 20260713 miss-fill into age/duration emit for L01 10Y + L10 LP9595 only) vs Option B (await Rate_Table re-extract).
Confirm no touch to #25/#26/#40/#41.
Produce go/no-go for Development once Option A or B is chosen.
```

---

## 13. Recommended Development Task (do not implement)

1. If Option A: surgical path/merge so age-duration emit sees PDAGE rows for coverages absent from Rate_Table; bump APP_VERSION; add validator asserting QuikNps/QuikTvs row counts for `5L0110` / L10 LP9595 keys.  
2. If Option B: no converter change; re-run rate emit after CSO drops Rate_Table with keys; validate counts.  
3. Optionally update `paagerat_extract()` candidate to prefer `…_20260713.csv`.  
4. Do not invent `0824 P DTH` / `L10 GPO OL` NP or `L17`/`960 LP85-8` CV.
