# Phase P3D — MPLAN Authority Impact Analysis (Comprehensive Report)

Generated: 2026-05-26

**Scope:** Enterprise impact of Phase P3C Closed Product Catalog Authority on downstream quikmstr, quikridr, rider linkage, referential integrity, rulebooks, crosswalks, governance, claims, and DBF assumptions.

**Analysis type:** Governance assessment only — no implementation changes.

---

## SECTION A — Current MPLAN Architecture

### quikmstr — No MPLAN field

- **Schema:** `MPOLICY`, billing, status, relationships — no `MPLAN` or `PLAN` column (`app.py` TABLE_SCHEMAS).
- **Rulebook:** `Sync_Rulebook_quikmstr.csv` maps policy-level fields only (POLICY_NUMBER→MPOLICY, billing, status).
- **Plan identity:** quikmstr does **not** carry product/plan codes. Policy master links to riders only via shared `MPOLICY`.
- **P3C impact:** **None directly.** quikmstr is unaffected by closed catalog authority.

### quikridr — MPLAN populated independently

**Population path:**

```
PPBEN.csv (source, locked in batch)
  → Filter: BENEFIT_SEQ numeric ≥ 1 (defines MPHASE)
  → Sync_Rulebook_quikridr.csv: PLAN_CODE → MPLAN
  → Master_Value_Translation.csv (generic trans_map)
  → Master_Crosswalk.csv flat lookup (app.py ~3960):
        val = cw_map.get(val, val)   ← passthrough if no match
  → Post-row: MRIDRID injection, MPHASE default "1", MPAR from PPBENTYP cache
  → MPHASE=1: MPHSTAT synced from quikmstr.csv
```

**Key architectural facts:**

| Attribute | quikridr MPLAN | quikplan PLAN (P3C) |
|-----------|----------------|---------------------|
| Source file | PPBEN.csv | quikplan_source.csv |
| Source key | PLAN_CODE | COVERAGE_ID |
| Rulebook | Sync_Rulebook_quikridr.csv | Sync_Rulebook_quikplan.csv |
| Crosswalk | Flat Master_Crosswalk (combined) | product_catalog_crosswalk + CrosswalkAuthority + overlay |
| Closed authority | **NO** | **YES** (default with UAT overlay) |
| Consumes quikplan output | **NO** | N/A (catalog table) |
| Passthrough allowed | **YES** (`cw_map.get(val,val)`) | **NO** under P3C |

### quikactg — Same legacy path as quikridr

- `Sync_Rulebook_quikactg.csv`: `PACTG.PLAN_CODE → MPLAN` via Master_Crosswalk.
- Same flat crosswalk passthrough behavior as quikridr.
- **P3C impact:** Not governed; same orphan risk pattern.

### Product setup isolation

When `QLA_PRODUCT_SETUP_ISOLATED=1`, batch skips quikplan conversion while quikridr/quikmstr still run. This creates a **temporal split**: quikplan can be re-emitted with P3C authority while quikridr retains legacy MPLAN values from the prior batch.

---

## SECTION B — Referential Integrity Risk Analysis

### Current state (P3C quikplan + legacy quikridr batch output)

| Metric | Value |
|--------|-------|
| quikplan.PLAN rows | 133 |
| quikplan unique PLAN | 133 |
| quikplan PLAN outside closed catalog | **0** |
| quikplan PLAN with spaces | **0** |
| quikridr rows | 11,698 |
| quikridr unique MPLAN | 139 |
| quikridr blank MPLAN | **2,348** |
| Orphan MPLAN (MPLAN ∉ quikplan.PLAN) | **39** |
| MPLAN containing spaces | **31** |

### Is every MPLAN guaranteed to exist in quikplan under P3C?

**NO.** P3C governs quikplan emission only. quikridr continues emitting MPLAN values independently. **39 orphan MPLAN codes** are present in current output, up from 7 pre-P3C (P3C made quikplan stricter, widening the gap).

### Orphan scenarios

1. **Passthrough compat values (31 codes with spaces):** e.g. `0824 P DIS`, `1579 GPO`, `L10 PRE97` — quikridr emits PPBEN PLAN_CODE via Master_Crosswalk passthrough; quikplan P3C emits authoritative codes (`94PDIS`, `9GPO79`, etc.).

2. **Catalog-external codes (8 codes without spaces):** e.g. `1L15GD` (11 rows), `9DIS90` (12 rows), `L17 BASE` (20 rows) — PPBEN PLAN_CODE values with no quikplan catalog row (product not in quikplan_source).

3. **Legacy collision codes:** e.g. `9DIS25` (34 rider rows) — legacy Master_Crosswalk collision; P3C quikplan splits to `9DIS24`/`9DS24C`/`9DS24B`.

4. **Blank MPLAN (2,348 rows):** PPBEN PLAN_CODE blank or unresolved; not flagged by `validate_output.py` critical fields.

### Rider/base policy mismatch risks

- **MPHASE logic is independent of MPLAN authority:** MPHASE comes from BENEFIT_SEQ; MPLAN from PLAN_CODE on same row. Phase logic does not validate MPLAN against quikplan.
- **Rider rows (MPHASE > 1) with orphan MPLAN:** Many orphan codes appear on rider phases (e.g. `9DIS25` 34 rider rows, `9DIS90` 12 rider rows). Rider linkage to product catalog breaks when MPLAN ∉ quikplan.PLAN.
- **MRIDRID injection unaffected:** Relationship priority RU→IN→INSD operates on rel_map; no PLAN validation.

### Claims linkage risks

- **Direct claims impact: LOW.** Claims pipeline validates `MPOLICY` against quikmstr (Phase 20); no MPLAN/PLAN field in quikclms/quikclmp rulebooks.
- **Indirect impact: MEDIUM.** QLAdmin product screens join quikridr.MPLAN to quikplan.PLAN; orphan MPLAN may cause display/join failures in policy review UAT.

### DBF generation assumptions

- UAT DBF generation reads emitted CSV outputs. quikplan DBF under P3C is clean; quikridr DBF still contains orphan/spaced MPLAN values.
- Documented FK: `quikridr.MPLAN → quikplan.PLAN` (P1B dependency map DEP-quikridr-MPLAN).

---

## SECTION C — Rulebook Impact Analysis

### Sync_Rulebook_quikridr.csv

```csv
PLAN_CODE,MPLAN,,
BENEFIT_SEQ,MPHASE,,Phase sequence
```

- **No Transformation_Note** on MPLAN mapping.
- **No closed authority annotation.**
- Crosswalk application is engine-implicit at `app.py` line ~3960, not rulebook-driven.
- **No rules reference space-containing PLAN values directly** — spaces originate from source PPBEN PLAN_CODE passthrough.

### Sync_Rulebook_quikmstr.csv

- No PLAN/MPLAN rules. **No changes required.**

### Sync_Rulebook_quikplan.csv

```csv
COVERAGE_ID,PLAN,,,,Map to crosswalk via engine
```

- Governed by P3C closed authority in product setup runner.
- Batch path uses CrosswalkAuthority but not P3C closed filter unless overlay enabled.

### Sync_Rulebook_quikactg.csv

```csv
quikactg,MPLAN,PACTG,PLAN_CODE,Use Master_Crosswalk.csv PLAN crosswalk
```

- Same legacy passthrough dependency as quikridr.
- **Requires update in P3F** if closed authority extended to accounting.

### Rules requiring updates

| Rulebook | Update needed? | Reason |
|----------|----------------|--------|
| quikridr | **RECOMMENDED (P3E)** | Add Transformation_Note documenting closed authority resolution path |
| quikmstr | No | No MPLAN |
| quikplan | No | P3C complete |
| quikactg | **RECOMMENDED (P3F)** | After quikridr alignment |
| quikclms/quikclmp | No | No MPLAN |

---

## SECTION D — Crosswalk Impact Analysis

### Master_Crosswalk product mappings

- ~240 product/entity rows mixed with ~4,920 policy-number rows.
- **quikridr/quikactg:** Uses full combined flat map — all product rows active.
- **quikplan (P3C):** Uses separated `CrosswalkAuthority` + `product_catalog_crosswalk.csv`; legacy product rows are fallback/diagnostics only.

### product_catalog_crosswalk.csv

- **Authoritative column:** `crosswalk_ql_plan_code` (133 plans, 0 spaces).
- **Compat column:** `ql_plan_code` — 33 CROSSWALK_DIVERGENT rows retain passthrough values for rollback lineage.
- **quikridr does not read this file.** This is the core P3C/P3D authority split.

### Policy Form Crosswalk overlay

- Applies to quikplan only (UAT overlay / CROSSWALK_OVERLAY).
- Aligns quikplan PLAN with `crosswalk_ql_plan_code` when overlay enabled.
- **Does not affect quikridr MPLAN.**

### Dead legacy paths (obsolete for quikplan emit)

1. `Master_Crosswalk` product passthrough for quikplan — superseded by P3C.
2. `ql_plan_code` compat passthrough values — diagnostics/rollback only.
3. `QLA_ALLOW_LEGACY_PRODUCT_FALLBACK=1` — explicit rollback mode.

### Active legacy paths (still driving quikridr)

1. `cw_map.get(val, val)` passthrough in app.py generic loop.
2. Full Master_Crosswalk product rows without catalog layer.
3. PPBEN PLAN_CODE as source identity (not COVERAGE_ID).

---

## SECTION E — Required Changes

### REQUIRED before MPLAN governance cutover

| ID | Finding | Root cause | Risk | Minimal remediation |
|----|---------|------------|------|---------------------|
| P3D-001 | quikridr MPLAN authority split | P3C not applied to quikridr path | 39 orphans, 31 spaced MPLANs | P3E: closed-authority MPLAN resolution via product catalog |
| P3D-002 | No runtime FK enforcement | Governance WARN only | Silent orphans in DBF | P3D: batch referential gate before emit |
| P3D-003 | 2,348 blank MPLAN rows | Not in critical validation | Broken FK semantics | P3D: BLANK_MPLAN ERROR + PPBEN trace |

### RECOMMENDED hardening

| ID | Finding | Remediation |
|----|---------|-------------|
| P3D-004 | quikactg same legacy path | P3F after quikridr |
| P3D-005 | Batch quikplan lacks P3C closed filter | P3G batch parity |

### SAFE TO LEAVE AS-IS

- quikmstr (no MPLAN)
- Claims pipeline (MPOLICY only)
- MRIDRID relationship injection logic
- MPHASE phase-aware rider sequencing

### OBSOLETE LEGACY LOGIC

- Master_Crosswalk product passthrough for quikplan emit
- ql_plan_code compat passthrough values (33 rows)
- Flat crosswalk for quikplan in product setup (replaced by closed catalog)

---

## SECTION F — Governance Recommendations

### Recommended next phases

1. **P3D — MPLAN Referential Governance** *(this analysis phase — complete)*
   - Deliverables: impact analysis, remediation matrix, orphan inventory
   - Next: implement batch governance gate (WARN→ERROR), blank MPLAN trace

2. **P3E — quikridr Authority Alignment** *(REQUIRED before cutover)*
   - Apply closed catalog MPLAN resolution: PLAN_CODE → authoritative plan
   - Reverse lookup: compat/passthrough PLAN_CODE → crosswalk_ql_plan_code
   - Eliminate spaced MPLAN emission
   - Controlled flag: `QLA_CLOSED_MPLAN_AUTHORITY=1`

3. **P3F — Product Referential Validation Layer**
   - Extend to quikactg
   - Pre-DBF referential check: quikridr.MPLAN ⊆ quikplan.PLAN
   - Add MPLAN to validate_output critical fields

4. **P3G — Batch Product Authority Parity**
   - Align batch quikplan with product setup P3C when overlay enabled
   - Optional: unified product authority module for all tables

### MPLAN cutover decision

| Question | Answer |
|----------|--------|
| Is MPLAN governance cutover safe now? | **NO** |
| Is additional hardening required first? | **YES** — P3E minimum |
| Is MPLAN closed-authority effectively required? | **YES** — P3C created mandatory downstream alignment |
| Overall governance risk rating | **HIGH** |

---

## Artifact Index

All outputs under `plan_analysis/phase_p3d_mplan_authority_impact_analysis/`:

- `executive_mplan_authority_impact_summary.md` (concise summary)
- `comprehensive_mplan_authority_impact_report.md` (this document)
- `mplan_referential_integrity_analysis.csv`
- `product_authority_dependency_trace.csv`
- `legacy_product_dependency_inventory.csv`
- `required_remediation_matrix.csv`
- `obsolete_legacy_product_logic_inventory.csv`

Regenerate: `python plan_analysis/phase_p3d_mplan_authority_impact_analysis/phase_p3d_mplan_authority_impact_runner.py`
