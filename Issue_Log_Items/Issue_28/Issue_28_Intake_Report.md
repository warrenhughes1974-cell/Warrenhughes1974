# Issue #28 — Intake Report

**Status:** Intake Complete  
**Priority:** No-Go until investigation completes  
**Engine version reviewed:** v57.34  
**Intake date:** 2026-06-24  
**Mode:** Read-only — no code, config, or crosswalk modifications

---

## 1. Executive Summary

Issue #28 reports that QLAdmin plan numbers emitted by the v57.34 converter do not match the client-approved **Policy Form Crosswalk (5.22.2026)**. Intake investigation **confirms the client examples and identifies the full divergent population (33 of 141 plans)**.

**Key finding:** The converter is operating as currently configured — not as the client expects. The authoritative crosswalk **is present in the repository** (`crosswalk_ql_plan_code` column in `product_catalog_crosswalk.csv` and the xlsx source file), but the **default batch runtime reads the compatibility column `ql_plan_code`** instead. That column was intentionally seeded from stable pre-crosswalk emit values (Phase P2E/P3C rollback-safe design) and flags divergences as `CROSSWALK_DIVERGENT`.

The Policy Form Crosswalk xlsx overlay path exists but is **disabled by default** (`CROSSWALK_OVERLAY=0`). All 33 mismatches between runtime behavior and the authoritative crosswalk are explained by this dual-column catalog architecture — **not by missing crosswalk data or unknown converter logic**.

| Metric | Value |
|--------|------:|
| Crosswalk rows | 141 |
| Runtime exact matches | 108 (76.6%) |
| Runtime mismatches | 33 (23.4%) |
| Client examples confirmed | 3 / 3 |

**Ownership:** Configuration / authority-column selection in `load_product_catalog_crosswalk()` and unreconciled P3C catalog state — **not** Master_Crosswalk corruption or rulebook errors.

---

## 2. Scope

### In scope
- Repository inventory of all plan-mapping artifacts
- Runtime mapping authority and precedence
- Policy Form Crosswalk 5.22.2026 consumption path
- End-to-end trace of three client examples
- Population-wide crosswalk comparison

### Out of scope (deferred to Planning)
- Code changes, catalog updates, crosswalk reconciliation
- Batch re-run with overlay flags
- Client sign-off on remediation approach

### Protected issues (untouched)
Issues #21M, #21M-FU, #21K, #25, #26 — no investigation artifacts modified those workstreams.

---

## 3. Repository Artifacts Reviewed

See **`Issue_28_Mapping_Inventory.md`** for the complete artifact catalog.

| Category | Key paths |
|----------|-----------|
| Authoritative crosswalk | `plan_analysis/source_data/crosswalk/Policy Form Crosswalk 5.22.26.xlsx` |
| Runtime catalog | `plan_governance/product_catalog_crosswalk.csv` |
| Legacy crosswalk | `QLA_Migration/Mapping/Master_Crosswalk.csv` |
| Rulebooks | `Sync_Rulebook_quikplan.csv`, `Sync_Rulebook_quikridr.csv` |
| Converter | `app.py`, `qla_core/quikplan_converter.py`, `qla_core/product_catalog_authority.py`, `qla_core/crosswalk_enrichment.py` |
| Output evidence | `QLA_Migration/Output/quikplan.csv`, `quikridr.csv` |

---

## 4. Runtime Mapping Architecture

See **`Issue_28_Runtime_Mapping_Flow.md`** for diagrams.

**quikplan PLAN path (default batch):**

```
COVERAGE_ID → rulebook → load_crosswalk_authority().product_plan_map
  ← product_catalog_crosswalk.csv [ql_plan_code]
  ← Master_Crosswalk legacy product rows (fallback)
  → passthrough if unmapped
  → (optional) xlsx overlay if CROSSWALK_OVERLAY=1
```

**quikridr MPLAN path (default batch):**

```
PPBEN PLAN_CODE → rulebook → Master_Crosswalk cw_map passthrough
  (P3E closed authority OFF by default)
```

---

## 5. Mapping Authority Analysis

| Question | Answer | Evidence |
|----------|--------|----------|
| Which artifact controls quikplan PLAN at runtime? | `product_catalog_crosswalk.csv` via `ql_plan_code` | `load_product_catalog_crosswalk()` line 427–428 in `product_catalog_authority.py` |
| Is crosswalk xlsx used directly? | Only if `CROSSWALK_OVERLAY=1` (default OFF) | `crosswalk_enrichment.py` |
| Does Master_Crosswalk override divergent rows? | No — client examples absent from product rows | Grep + trace |
| Is authoritative column stored? | Yes — `crosswalk_ql_plan_code` | Catalog CSV + 33 `CROSSWALK_DIVERGENT` flags |
| Is authoritative column used for emit? | **No** in default batch | Runtime simulation |

---

## 6. Crosswalk Consumption Analysis

| Ingestion path | Status |
|----------------|--------|
| xlsx → direct runtime overlay | Available, **disabled** |
| xlsx → `crosswalk_ql_plan_code` in product catalog | **Complete** for 140/141 IDs |
| xlsx → `ql_plan_code` runtime emit | **Retains legacy passthrough** for 33 divergent rows |
| xlsx → Master_Crosswalk product rows | Partial — divergent IDs typically **not added** |
| Generated artifact last updated | Phase P2E/P3C scaffolding (catalog seeded from stable emit) |
| Generated artifact matches xlsx? | **`crosswalk_ql_plan_code` matches**; **`ql_plan_code` intentionally differs** for 33 rows |

---

## 7. Reported Example Validation

See **`Issue_28_Trace_Samples.md`**.

| Client example | Authoritative PLAN | v57.34 emitted PLAN | Match? |
|----------------|-------------------|---------------------|--------|
| 10827 CSI Life MN$5000 | 1CSIMN | 10827 MN5K | **NO** |
| 0823 9 Waiver of Premium - Child | 960CWP | 0823 960CH | **NO** |
| 0824P Payor Disability Rider | 94PDIS | 0824 P DIS | **NO** |

All three: `mapping_status=CROSSWALK_DIVERGENT`, runtime reads `ql_plan_code`, crosswalk value present in `crosswalk_ql_plan_code`.

---

## 8. Crosswalk Comparison Results

| Metric | Count |
|--------|------:|
| Total crosswalk rows | 141 |
| Total runtime mappings evaluated | 141 |
| Exact matches | 108 |
| Changed / divergent mappings | 33 |
| Missing from converter catalog | 1 (`DISCHO25` in crosswalk — verify governance row `DISCHO247C`) |
| Extra in converter | 0 |
| Duplicate mappings | 0 |
| Many-to-one (authoritative) | 0 |

**Discrepancy origin:** Single source — **`product_catalog_crosswalk.csv` dual-column design** where runtime consumes compat column. Not multiple conflicting sources.

Detail: **`Issue_28_Mapping_Differences.csv`**

---

## 9. Population Statistics

See **`Issue_28_Population_Summary.md`**.

- 33/33 `CROSSWALK_DIVERGENT` rows mismatch authoritative crosswalk at runtime
- 108/108 `STABLE_EMIT` rows match authoritative crosswalk at runtime
- Client-reported "numerous additional plans" aligns with the full 33-row divergent population

---

## 10. Root Cause Candidates

| # | Candidate | Confidence | Evidence |
|---|-----------|------------|----------|
| RC-1 | **`load_product_catalog_crosswalk()` reads `ql_plan_code` not `crosswalk_ql_plan_code`** | **HIGH — proven** | Code + runtime simulation; all 33 mismatches |
| RC-2 | P3C catalog seeded for rollback safety; crosswalk authority never promoted to emit column | **HIGH** | `governance_notes`, P2E runner, `CROSSWALK_DIVERGENT` flags |
| RC-3 | `CROSSWALK_OVERLAY=0` prevents xlsx from correcting emit post-conversion | **HIGH** | Env default + crosswalk_enrichment.py |
| RC-4 | Master_Crosswalk lacks product rows for passthrough IDs | **MEDIUM** | Contributes passthrough but catalog is primary authority |
| RC-5 | P3E MPLAN authority cannot resolve to authoritative PLAN while quikplan emits compat codes | **MEDIUM** | Circular dependency in resolver universe |
| RC-6 | QLA_Migration/Mapping catalog copy stale (133 vs 140 rows) | **LOW runtime impact** | Batch uses plan_governance path |

**Not supported:** Random converter bug, rulebook misconfiguration, or missing crosswalk file.

---

## 11. Ownership Assessment

| Layer | Owns current behavior? | Should own client-expected behavior? |
|-------|------------------------|--------------------------------------|
| Policy Form Crosswalk xlsx | Authoritative business source | Yes |
| product_catalog_crosswalk.csv | Stores both compat + authoritative columns | Yes — **emit column selection is the gap** |
| load_product_catalog_crosswalk() | Selects compat column for runtime | **Primary ownership for #28** |
| crosswalk_enrichment overlay | Optional xlsx apply | Secondary / feature-flag path |
| Master_Crosswalk.csv | Legacy fallback | Supplemental only for divergent rows |
| app.py batch flags | Controls overlay + P3E | Configuration ownership |

**Conclusion:** Discrepancy is **owned by catalog authority configuration and emit-column selection**, not by undiscovered mapping logic. The converter faithfully emits what the catalog's `ql_plan_code` column specifies.

---

## 12. Risks

| Risk | Severity | Description |
|------|----------|-------------|
| No-Go release | **Critical** | 33 plans (23.4%) emit non-approved QL Plan Codes |
| quikridr MPLAN referential integrity | **High** | Passthrough MPLAN values may not exist in quikplan PLAN universe |
| Rate / CSO crosswalk mismatches | **Medium** | downstream lookups keyed on authoritative PLAN may fail |
| Catalog copy drift | **Low** | QLA_Migration/Mapping catalog 7 rows behind governance |
| P3E enablement without quikplan fix | **High** | Would produce UNAUTHORIZED MPLAN for divergent rows |

---

## 13. Open Questions

1. **Business decision:** Promote `crosswalk_ql_plan_code` to runtime emit column, or enable `CROSSWALK_OVERLAY=1` in production batch?
2. Should all 33 `CROSSWALK_DIVERGENT` rows be remediated atomically, or phased by product line?
3. Confirm `DISCHO25` vs `DISCHO247C` crosswalk ID naming — 1 catalog gap row.
4. Does client UAT environment run with different overlay/P3E flags than dev batch?
5. Are FORM column changes (crosswalk form numbers vs truncated LifePRO form) in scope for #28 or a separate issue?
6. Required regression scope: rate tables, CSO assumptions, variation classification for 33 plan code changes?

---

## 14. Recommendation for Planning Agent

1. **Treat as authority promotion issue**, not converter defect investigation.
2. **Preferred remediation path (surgical):** Update `load_product_catalog_crosswalk()` to emit from `crosswalk_ql_plan_code` when present and non-blank, falling back to `ql_plan_code` — OR flip `ql_plan_code` values for the 33 divergent rows after business approval.
3. **Alternative:** Enable `CROSSWALK_OVERLAY=1` in batch — applies xlsx post-conversion but does not fix quikridr MPLAN without P3E coordination.
4. **Coordinate quikplan + quikridr:** Remediation must update quikplan PLAN first, then enable/verify P3E MPLAN authority alignment.
5. **Use existing artifacts:** `plan_governance/manifests/plan_change_manifest.csv` already lists intended PLAN transitions for divergent rows.
6. **Validate with:** Re-run batch, compare output to `Issue_28_Mapping_Differences.csv`, confirm 33 → 0 mismatches.
7. **Preserve rollback:** Keep compat column documented; do not modify Issues #21M, #21M-FU, #21K, #25, #26.
8. **Sync** `QLA_Migration/Mapping/product_catalog_crosswalk.csv` with governance copy after remediation.

---

## Deliverables Index

| File | Purpose |
|------|---------|
| `Issue_28_Intake_Report.md` | This report |
| `Issue_28_Mapping_Inventory.md` | Artifact catalog |
| `Issue_28_Runtime_Mapping_Flow.md` | Architecture + flow diagrams |
| `Issue_28_Crosswalk_Inventory.csv` | Authoritative crosswalk rows |
| `Issue_28_Mapping_Differences.csv` | Row-level comparison |
| `Issue_28_Missing_From_Converter.csv` | Catalog gaps |
| `Issue_28_Extra_In_Converter.csv` | Extra mappings (empty) |
| `Issue_28_Trace_Samples.md` | Client example traces |
| `Issue_28_Population_Summary.md` | Population statistics |
| `_issue28_intake_analysis.py` | Read-only analysis script |
| `_population_stats.json` | Machine-readable counts |

---

## Cursor-Ready Prompt for Planning Agent

```
# Cursor Prompt — Issue #28 Planning Agent

You are continuing work on the **LifePRO → QLAdmin Conversion Project**.

Current converter version: **v57.34**

Perform **ONLY the Planning Agent stage** for **Issue #28**. Do NOT implement code changes yet.

## Intake Findings (Authoritative)

Intake completed 2026-06-24. Read all artifacts in:
`Issue_Log_Items/Issue_28/`

### Proven root cause
- Policy Form Crosswalk 5.22.2026 is stored in `product_catalog_crosswalk.csv` → `crosswalk_ql_plan_code`
- Default batch runtime reads **`ql_plan_code`** (compat/passthrough) via `load_product_catalog_crosswalk()` in `qla_core/product_catalog_authority.py`
- 33 rows flagged `CROSSWALK_DIVERGENT` — ALL mismatch authoritative crosswalk at runtime
- 108 rows `STABLE_EMIT` — match authoritative crosswalk
- `CROSSWALK_OVERLAY=0` (default) — xlsx not applied in batch
- Client examples confirmed: 10827 MN5K→1CSIMN, 0823 960CH→960CWP, 0824 P DIS→94PDIS

### Protected issues (do not regress)
#21M, #21M-FU, #21K, #25, #26

## Planning Objectives

1. Evaluate remediation options:
   - A) Change runtime to prefer `crosswalk_ql_plan_code` in `load_product_catalog_crosswalk()`
   - B) Update `ql_plan_code` values for 33 divergent rows (catalog-only)
   - C) Enable `CROSSWALK_OVERLAY=1` in production batch
   - D) Hybrid: catalog promotion + P3E MPLAN authority enablement

2. For each option document:
   - Blast radius
   - quikplan vs quikridr coordination
   - Rate/CSO/variation downstream impact
   - Rollback strategy
   - Version bump requirement (app.py)

3. Produce:
   - `Issue_28_Remediation_Plan.md`
   - `Issue_28_Test_Plan.md`
   - `Issue_28_Risk_Register.md`
   - Recommended option with business justification

4. Reference existing manifests:
   - `plan_governance/manifests/plan_change_manifest.csv`
   - `Issue_28_Mapping_Differences.csv`

## Constraints
- Surgical changes only per AGENTS.md
- No unrelated converter refactors
- Preserve QLA formatting and schema integrity
- Planning only — stop before Development

Stop after Planning deliverables are complete.
```

---

*Intake stage complete. Do not proceed to Development without Planning review.*
