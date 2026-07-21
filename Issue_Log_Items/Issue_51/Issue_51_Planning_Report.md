# Issue #51 — Planning Report

**Issue:** #51 — Missing Interest Table (A60MIR / A96DAR) — Projected Values Crash Loop  
**Framework stage:** Planning Agent  
**Status:** Ready for Dependency Gate  
**Generated:** 2026-07-11  
**Agent/script:** Planning Agent (Cursor Grok 4.5) · `scripts/research_issue51_quikaint_gap.py`

---

## 1. Executive Finding

QLAdmin Projected Values looks up **QuikAint** (Annuity Interest Rates, Help §7.31) by rider MPLAN for A-prefixed `quikplan` codes. Conversion emits `A60MIR` and `A96DAR` in the plan catalog and as `quikridr` coverages, but **does not emit QuikAint** for those plans (and the PFSA QuikAint builder never included them). Result: `"Interest table not found for A60MIR, cannot calculate balance"` and an endless error loop.

All **6** in-force MIR/DAR rider rows are already **MPHSTAT=56**, and LifePRO `PPBEN.FV_GUAR_RATE` is **.00** with zero FV balances — so a **QuikAint stub at 0.0000** is consistent with current LifePRO authority and is the surgical crash-stop. Suppressing terminated riders from projection is a **QLAdmin configuration** question, not the conversion table fix.

**Direction:** Emit QuikAint rows for A60MIR/A96DAR into `Output/rates/`; wire into rate package. Do **not** use QuikUint. Preserve #25/#26.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|--------------|--------------|---------------------|----------:|
| PPBEN (benefit + FV fields) | `PPBEN_PolicyBenefit_Extract_20260630.csv` | Yes | 6 OR rows on 863 / 896 DAR |
| Product catalog / crosswalk | `Mapping/product_catalog_crosswalk.csv` | Yes | 863→A60MIR; 896 DAR→A96DAR |
| Rate factors (premium/CV — not interest) | Rate_Table / PAAGERAT extracts | Yes (plan_analysis) | Loaded to QuikGps/Dbs/Nps/Tvs/Cvs — **not** QuikAint |
| PDINT / PDINTTBL for 863/896 | — | **No** | N/A — ISWL path only |

### Available source fields (interest authority)

| Field | Column / source | Populated % | Notes |
|-------|-----------------|------------:|-------|
| Policy number | PPBEN.POLICY_NUMBER | 100% | Crosswalk to QLA |
| Plan | PPBEN.PLAN_CODE | 100% | `863` / `896 DAR` |
| Status | STATUS_CODE / STATUS_REASON | 100% | All `T` (terminated) |
| Guaranteed rate | **FV_GUAR_RATE** | 100% at `.00` | Authority for stub |
| Fund balances | FV_BALANCE1/2 | 100% at `.00` | No live deposit balance |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source (Help / schema) |
|-------|-------|------|--------|------------------------|
| **QuikAint** | MPLAN | C | 6 | Help **§7.31** p.695 |
| QuikAint | MEFFDATE | D | 8 | Index: `MPLAN + MEFFDATE` |
| QuikAint | MINTRATE | N | 7.4 | Interest rate (crediting) |
| QuikAint | MINTRATE1 | N | 7.4 | Guaranteed initial interest rate |

**Repo references:**

| Location | Role |
|----------|------|
| `QLA_Migration/Data_Goverence.txt` L155 | A-plans need QUIKAINT / AING / AEXP / AINF |
| `data_governance/rules/chk_quikplan.py` PLAN-023 | Advisory when A-plan missing annuity tables |
| `plan_analysis/phase_r6_quikaint_rates/build_quikaint.py` | PFSA QuikAint builder (no MIR/DAR) |
| `qla_core/quikuint_loader.py` | **Reject for this issue** — ISWL QuikUint only |
| `QLA_Migration/Output/rates/` | Current load package — **no QuikAint** |

Companion tables (PLAN-023 advisory; emit only if UAT still fails after QuikAint):

| Table | Help | Fields |
|-------|------|--------|
| QuikAing | §7.30 | MPLAN, MISSUEST, MEFFDATE, MGTDRATE |
| QuikAinf | §7.29 area | Nonforfeiture rates |
| QuikAexp | §7.11 | Annuity expense load |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PPBEN (forms 863 / 896 DAR) | FV_GUAR_RATE (fleet = .00) | QuikAint.MINTRATE | Format N(7.4) → `0.0000` | **Yes — add rows** |
| Same | FV_GUAR_RATE | QuikAint.MINTRATE1 | Same as MINTRATE for stub | **Yes** |
| Catalog | Crosswalk QLA MPLAN | QuikAint.MPLAN | `A60MIR` / `A96DAR` | **Yes** |
| Convention (PFSA builder) | First tier back-date | QuikAint.MEFFDATE | `19000101` | **Yes** |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| quikmstr.MMODPREM | PPOLC.MODE_PREMIUM | **No** |
| quikridr.MPREM | ANN_PREM_PER_UNIT + fallback (#26) | **No** |
| MPOLICY padding | format_qladmin_mpolicy (#25) | **No** |
| quikdvdp.MDEPINT | #21D ISWL/non-ISWL rules | **No** |
| QuikUint ISWL rows | #32 PDINT path | **No** (do not add MIR/DAR here) |
| quikridr status-56 rows | Sync_Rulebook_quikridr | **No** — keep terminated history |

---

## 5. Open Client Questions

1. **Rate authority:** Confirm **0.0000** QuikAint stub is acceptable for closed MIR/DAR (matches all PPBEN `FV_GUAR_RATE`). If a historical product guaranteed rate (e.g. 3%/4%) is preferred for documentation, provide the schedule.
2. **Terminated riders in Projected Values:** Confirm whether QLAdmin should skip MPHSTAT=56 riders in projection (vendor/config) vs always requiring interest tables when rider rows exist (conversion responsibility = tables).
3. **Companion tables:** If QuikAint alone does not clear the loop, authorize QuikAing/QuikAinf stubs at the same 0% rate.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | N/A (plan-level QuikAint — no MPOLICY) |
| Dates | `MEFFDATE` as YYYYMMDD `19000101` (Help DATE 8) |
| Rates | N(7.4) four-decimal strings (`0.0000`) matching PFSA append CSV style |
| Blanks / zeros | Explicit `0.0000` — do not omit row (row absence is the defect) |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` → `Master_Crosswalk.csv` → QLA (for UAT traces only)
2. QuikAint is **plan-keyed**, not policy-keyed
3. #25 padding unchanged on all policy tables

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| Target QuikAint rows to add | **2** | 1 row × A60MIR + A96DAR |
| quikridr policies affected | **6** | 2 A60MIR + 4 A96DAR |
| Active MIR/DAR riders | **0** | All status 56 |
| Existing Output QuikAint rows | **0** | File absent |
| Unrelated rate tables changed | **0** | Surgical add only |

---

## 10. Sample Trace (6 policies)

| Policy (QLA) | LifePRO LP | Rider | MPHSTAT | Before (QuikAint) | After (proposed) | Status |
|--------------|------------|-------|---------|-------------------|------------------|--------|
| 010348734C | 9010348734 | A60MIR | 56 | Missing → error loop | Row MINTRATE=0.0000 | Client example |
| 010335095C | 9010335095 | A60MIR | 56 | Missing | Same stub | Peer |
| 010510671C | 9010510671 | A96DAR | 56 | Missing | Same stub | Peer |
| 010511203C | 9010511203 | A96DAR | 56 | Missing | Same stub | Peer |
| 010538650C | 9010538650 | A96DAR | 56 | Missing | Same stub | Peer |
| 010549966C | 9010549966 | A96DAR | 56 | Missing | Same stub | Peer |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| QuikAint alone insufficient (needs Aing/Ainf) | Medium | Conditional Go: primary QuikAint; secondary stubs if UAT fails |
| 0% incorrect vs historical product rate | Low (fleet terminated, FV=0) | Document authority; client can supply schedule later |
| Infinite loop is QLAdmin bug even with table present | Low | UAT after emit; escalate to vendor if persists |
| Wiring QuikAint into rate pipeline expands blast radius | Medium | Prefer surgical append CSV + manifest update over broad R5 rewrite |
| Accidental QuikUint expansion | High if done | Explicitly forbid — wrong table |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | **Met** — PPBEN + catalog |
| Field definitions confirmed | **Met** — Help §7.31 |
| Client scope clear | **Mostly** — crash-stop clear; rate schedule soft |
| Example policies available | **Met** |

---

## 13. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue #51.

Read AI_Agents/Risk_Agent.md and Templates/Risk_Report_Template.md.
Model: Cursor Grok 4.5. Do not code.

Quantify impact of adding 2 QuikAint stub rows (A60MIR, A96DAR @ 0.0000)
from PPBEN.FV_GUAR_RATE authority. Confirm QuikUint / #21D / #25 / #26 untouched.
Issue Conditional Go vs Go vs No-Go for Development.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. Add QuikAint schema support if missing from `rate_dbf_schema.py` / writer helpers (Help §7.31 — 4 fields only).
2. Emit **exactly two** rows to `QLA_Migration/Output/rates/QuikAint.csv` (and DBF if rate package emits DBF):
   - `A60MIR,19000101,0.0000,0.0000`
   - `A96DAR,19000101,0.0000,0.0000`
3. Update rate CSV manifest / load package checklist so QuikAint is included in UAT rate load.
4. Do **not** add MIR/DAR to QuikUint allowlist; do **not** filter status-56 from quikridr; do **not** touch #21D MDEPINT.
5. Version bump `app.py` + `QLA_Migration/app.py` if engine/rate path touched.
6. Validation script: `tools/validators/validate_issue51_quikaint.py` — asserts both MPLANs present; schema; no QuikUint pollution; ridr population unchanged.

---

## Appendix

- Diagnostic script: `Issue_Log_Items/Issue_51/scripts/research_issue51_quikaint_gap.py`
- Evidence: `Issue_Log_Items/Issue_51/evidence/issue51_*.csv`
- Screenshot: `evidence/issue51_client_screenshot_010348734C.png`
- Related: #32, #21D, #21E, #28
- References: QLAdmin Help §7.31 QuikAint; Data_Goverence.txt L155; PLAN-023
