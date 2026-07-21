# Issue #58 — Planning Report

**Issue:** #58 — Premium Mode Amounts Incorrect  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning complete — ready for Dependency Gate  
**Generated:** 2026-07-13  
**Agent:** Planning Agent (read-only) · Model: Cursor Grok 4.5  
**Intake / GPT review:** Intake diagnosis accepted; GPT caveat incorporated (do not assume fee×premium-factor is proven for every product)

---

## 1. Executive Finding

Names-tab Modal Premium **amounts** on fee-bearing policies omit the modalized policy fee. Eric’s sample **`010367131C`** has correct plan factors on `quikmstr` (Issue #36) and correct annual/current-mode dollars, but quarterly/monthly display as base premium × factor only (`$13.13` / `$4.46` instead of `$15.90` / `$5.40`).

QLAdmin Help defines separate coverage-level fee fields on **`quikridr`**: `MANNLFEE` / `MSEMIFEE` / `MQTRLFEE` / `MMTHDFEE` / `MMTHBFEE`. Issue **#21C** populated only `MANNLFEE`; the four modal fee slots remain **blank fleet-wide** (0 / 4,457). Plan-level `quikplan` modal fee columns are also **0.0000** and are **out of scope** without authoritative plan fee schedules.

**Recommended direction:** After `quikmstr` factor enrichment (#36 + PAC overrides), derive and write base-coverage modal fees:

`M*FEE = MANNLFEE × (corresponding quikmstr factor / 100)` · NUMERIC 8.4

This matches Eric’s expected amounts exactly. **GPT caveat accepted:** the same derivation is **confirmed for Eric’s product family** (`17085M` / related GL85) and several traditional plans via `MODE_PREMIUM ≈ ANNUAL × factor`, but **not universal** across all fee-bearing plans (notably some ISWL plans). Risk must treat fleet roll-out as **Conditional** until plan-family UAT / OBQ clears, or Development ships with a documented inclusion set.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/? | Role for #58 |
|--------------|--------------|-------------|--------------|
| PPOLC | `PPOLC_PolicyMaster_Extract_*.csv` | Yes | `POLICY_FEE` → already cached for #21C; `ANNUAL_PREMIUM` / `MODE_PREMIUM` for validation only |
| PPBEN | `PPBEN_PolicyBenefit_Extract_*.csv` | Yes | Base benefit fee / units / ANN_PREM_PER_UNIT (context; not remapped) |
| — | Modal policy fee extract columns | **No** | Not in LifePRO extracts — **derive** |

**Authoritative inputs for derivation (conversion-owned):**

| Source | File / object | Fields |
|--------|---------------|--------|
| Annual fee (existing) | `quikridr` phase 1 | `MANNLFEE` (#21C from PPOLC `POLICY_FEE`) |
| Policy modal factors | `quikmstr` (post #36) | `MSEMI`, `MQTRL`, `MMTHD`, `MMTHB` **after** PAC overrides |
| Plan factors (fallback only) | `quikplan` / mapping | Same percent scale if `quikmstr` factors missing |

### Available source fields

| Field | Column / source | Populated % | Notes |
|-------|-----------------|------------:|-------|
| Policy fee (annual) | PPOLC.`POLICY_FEE` → `MANNLFEE` | ~87% of base rows | #21C — do not change |
| Modal fee amounts | LifePRO | **0%** | Absent — derive |
| Modal factors | `quikmstr` MSEMI… | ~100% post #36 | Percent scale (e.g. 52.0000) |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source |
|-------|-------|------|--------|--------|
| QuikRidr | MANNLFEE | NUMERIC | 8.4 | Help §7.203 — Annual policy fee (**preserve #21C**) |
| QuikRidr | MSEMIFEE | NUMERIC | 8.4 | Help — Semi-annual policy fee |
| QuikRidr | MQTRLFEE | NUMERIC | 8.4 | Help — Quarterly policy fee |
| QuikRidr | MMTHDFEE | NUMERIC | 8.4 | Help — Monthly **direct** policy fee |
| QuikRidr | MMTHBFEE | NUMERIC | 8.4 | Help — Monthly **bank draft** policy fee |

**Related (read-only for this issue):**

| Table | Field | Role |
|-------|-------|------|
| QuikMstr | MSEMI / MQTRL / MMTHD / MMTHB | Factor inputs (percent of annual) |
| QuikPlan | ANNLFEE / SEMIFEE / QTRLFEE / MTHDFEE / MTHBFEE | Plan defaults — currently **0.0000**; **do not invent** |
| QuikPlan | RRULE | Rounding for premium calculation (e.g. `22`); fees are separate add-ons |

Help Plan setup (Data Maintenance): mode factors = % of annual premium; **Modal Fees** = “Modal policy fees to be charged” (separate from factors). Coverage Display “Pol Fee” = modal policy fee for the phase.

**Repo references:**

| Location | Role |
|----------|------|
| `Sync_Rulebook_quikridr.csv` | MSEMIFEE…MMTHBFEE unmapped (blank) |
| `app.py` #21C interceptor | `POLICY_FEE` → `MANNLFEE` on BENEFIT_SEQ 1 only |
| `qla_core/modal_premium_factors.py` | Factor copy + PAC; **no fee population today** |
| Post-`quikridr` emit in `app.py` | Calls plan-factor → PAC on `quikmstr` — **hook site for #58 after PAC** |

---

## 4. Required Source-to-Target Field Mapping

| Source | Source field | QLAdmin target | Transformation | Change? |
|--------|--------------|----------------|----------------|---------|
| quikridr (phase 1) | MANNLFEE | — | Read only | **No** |
| quikmstr | MSEMI | quikridr.MSEMIFEE | `MANNLFEE × MSEMI/100` · format 4 dp | **Yes — new** |
| quikmstr | MQTRL | quikridr.MQTRLFEE | `MANNLFEE × MQTRL/100` | **Yes — new** |
| quikmstr | MMTHD | quikridr.MMTHDFEE | `MANNLFEE × MMTHD/100` | **Yes — new** |
| quikmstr | MMTHB | quikridr.MMTHBFEE | `MANNLFEE × MMTHB/100` | **Yes — new** |

### Formula (Eric-proven)

```
# After apply_plan_modal_factors_to_quikmstr + apply_pac_gl85_modal_overrides:
for each quikridr row where MPHASE in (1, 01) and MANNLFEE > 0:
    MSEMIFEE  = round(MANNLFEE * MSEMI  / 100, 4)   # or format "%.4f"
    MQTRLFEE  = round(MANNLFEE * MQTRL  / 100, 4)
    MMTHDFEE  = round(MANNLFEE * MMTHD  / 100, 4)
    MMTHBFEE  = round(MANNLFEE * MMTHB  / 100, 4)
```

Join factors by `MPOLICY` (`format_qladmin_mpolicy`). Use **post-PAC** `MSEMI`/`MQTRL` so GL85 PAC Q/S policies get 25% / 50% fee modalization consistent with Names-tab factors.

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| quikmstr.MMODEPREM | PPOLC.MODE_PREMIUM (#26) | **No** |
| quikridr.MPREM | ANN_PREM_PER_UNIT + fallback (#26) | **No** |
| quikridr.MANNLFEE | POLICY_FEE (#21C) | **No** |
| quikmstr MSEMI…MMTHB | #36 / PAC | **No** (read after PAC) |
| quikplan factors / fees | #21J / defaults | **No** — do not invent plan SEMIFEE… |
| MPOLICY padding | #25 | **No** |
| Rider phases MPHASE > 1 | — | **No** — fees stay on base row only (mirror #21C) |

---

## 5. Open Client Questions

| # | Question | Disposition for Development |
|---|----------|------------------------------|
| **OBQ-1** | Confirm modal policy fees = **annual fee × same plan/policy modal factors** for **all** products (not only GL85 / traditional), including ISWL where LifePRO `MODE_PREMIUM` often ≠ `ANNUAL × factor`? | **Soft blocker for Conditional Go** — default ship derive-all with UAT on ISWL samples; or Risk may require plan-family inclusion list |
| OBQ-2 | For Names tab monthly grid, should Draft use `MMTHBFEE` and Direct use `MMTHDFEE` independently (recommended)? | **Accepted** — mirror #36 MMTHD/MMTHB independence |
| OBQ-3 | Leave `quikplan` modal fee defaults at 0.0000 (recommended)? | **Accepted** — no plan fee authority in repo |

No hard extract-data blocker. OBQ-1 is the GPT-aligned product-authority question.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | `format_qladmin_mpolicy` when joining mstr ↔ ridr |
| Fee format | NUMERIC 8.4 string, e.g. `2.7666` |
| Rounding | Compute fee to 4 decimals; QLAdmin displays mode premiums to cents |
| MANNLFEE blank/0 | Leave all four modal fees blank (do not write 0.0000 unless already present) |
| Missing factors | Skip fee write; log count (should be rare post #36) |
| PAC | Always use factors **after** `apply_pac_gl85_modal_overrides` |
| Grain | Base coverage only (`MPHASE` 1 / 01) |

---

## 7. Memo / Text / Special Handling

**No memo change required** for #58. Optional later Closure note that Names-tab amounts need modal fees as well as factors (#36).

---

## 8. Policy Number Key Handling

1. Join `quikridr.MPOLICY` ↔ `quikmstr.MPOLICY` with padded keys (#25)  
2. Resolve factors from `quikmstr` row (already PAC-adjusted)  
3. Orphans / missing factors: skip + count; do not invent  

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| Base `quikridr` rows | 5,083 | Issue #49 baseline / fleet |
| `MANNLFEE` > 0 | **4,457** | Candidates for modal fee write |
| Modal fees currently non-blank | **0** | All four fields |
| Mode 3/6 proxy: `MODE_PREMIUM ≈ ANNUAL×factor` (±$0.02) | **580 / 816** (71%) | Evidence rollup — **not** Names-tab proof; product variance flag |
| `17085M` mode 3/6 proxy match | **23 / 23 (100%)** | Eric’s plan family |
| PAC GL85 samples | `010560185C` (Q→25%), `010442216C` (S→50%) | Must use overridden factors |

---

## 10. Sample Trace (policies)

| Policy | Plan | Mode | MANNLFEE | Factors S/Q/D/B | Proposed S/Q/D/B fees | Expected Names Qtly / Mthly |
|--------|------|------|----------|-----------------|------------------------|-----------------------------|
| **010367131C** | 17085M | 6 | 10.44 | 52 / 26.5 / 9 / 8.3333 | **5.4288 / 2.7666 / 0.9396 / 0.8700** | **$15.90 / $5.40** (Eric) |
| 010367132C | 170858 | 6 | 10.44 | same | same | same pattern |
| 010560185C | 170858 | 3 PAC | 10.44 | 52 / **25** / 9 / 8.3333 | 5.4288 / **2.6100** / 0.9396 / 0.8700 | Uses PAC Q factor |
| 010442216C | 170858 | 6 PAC | 10.44 | **50** / 26.5 / 9 / 8.3333 | **5.2200** / 2.7666 / … | Uses PAC S factor |
| 010380808C | 1960PO | 6 | 10.00 | 52 / 26.5 / 9 / 8.7019 | 5.2000 / 2.6500 / 0.9000 / 0.8702 | Traditional-style match |
| 010713704C | 1659C2 | 12/PAC | 25.00 | 52.5 / 27 / 9.1999 / 8.8018 | 13.1250 / 6.7500 / 2.299975 / 2.20045 | **ISWL — UAT priority** (mode prem ≠ annual×factor) |

**Before (010367131C):** MSEMIFEE…MMTHBFEE blank → Names Q/Mth = `$13.13` / `$4.46`.  
**After (proposed):** fees as above → Q = `49.56×0.265 + 2.7666 ≈ 15.90`; Mth = `49.56×0.09 + 0.9396 ≈ 5.40`.

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Fee schedule ≠ premium factors on some products (ISWL / UL) | **Medium–High** | Risk Conditional Go; OBQ-1; UAT ISWL samples; optional plan allowlist |
| Writing fees from plan defaults on `quikplan` | Medium | **Out of scope** — leave plan fees 0 |
| Running fee derive **before** PAC overrides | High | Wire **after** `apply_pac_gl85_modal_overrides` |
| Overwriting `MANNLFEE` / `MMODEPREM` / `MPREM` | High | Explicit exclude from write set |
| Phases > 1 accidentally fee’d | Low | Mirror #21C base-only |
| Rounding display vs 4-dp storage | Low | Match Help 8.4; Eric cents reconcile |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | **Yes** — `MANNLFEE` + `quikmstr` factors (no new LifePRO extract) |
| Field definitions confirmed | **Yes** — Help QuikRidr §7.203 |
| Client scope clear | **Mostly** — Eric symptom clear; fleet authority = OBQ-1 / Conditional |
| Example policies available | **Yes** — 010367131C + PAC + ISWL |

---

## 13. Recommended Risk Agent Prompt

```
Risk Agent — Issue #58: Premium Mode Amounts (quikridr modal fees)

Read AI_Agents/Risk_Agent.md, Issue_58_Planning_Report.md, Issue_58_Intake_Summary.md.
Evidence: Issue_58/evidence/issue58_fee_factor_mode_match.csv,
          Issue_58/evidence/issue58_plan_mode36_match_rollup.csv.

Quantify before/after: 4457 base rows with MANNLFEE>0 and blank MSEMIFEE/MQTRLFEE/MMTHDFEE/MMTHBFEE.
Simulate MANNLFEE × quikmstr factors (post-PAC). Do not change code.

Issue Go / Conditional Go / No-Go for Development.
Preserve #21C MANNLFEE, #26 MPREM/MMODEPREM, #36 factors/PAC, #25 MPOLICY.
Call out ISWL plan families where MODE_PREMIUM ≠ ANNUAL×factor as Conditional risk.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. Add `apply_modal_policy_fees_to_quikridr(ridr_df, mstr_df)` in `qla_core/modal_premium_factors.py` (or adjacent module) — base phase only; four fee fields from `MANNLFEE × factor/100`.
2. In `app.py` and `QLA_Migration/app.py`, after PAC overrides (and after `quikridr` emit is available for rewrite): apply fee derive; write updated `quikridr.csv`. Prefer single post-emit block that already loads mstr+ridr.
3. Bump `APP_VERSION` in **both** `app.py` files.
4. Validator: `tools/validators/validate_issue58_quikridr_modal_fees.py` — Eric amounts, PAC samples, MANNLFEE/MPREM/MMODEPREM unchanged, fleet blank→populated counts.
5. Do **not** modify `Sync_Rulebook_quikplan` fee defaults or `MANNLFEE` mapping.
6. If Risk issues Conditional Go with allowlist: gate derive by `MPLAN` set from Risk report.

---

## Appendix

- Intake: `Issue_58_Intake_Summary.md`
- Evidence: `evidence/issue58_fee_factor_mode_match.csv`, `evidence/issue58_plan_mode36_match_rollup.csv`
- Related: #21C, #21J, #36, #26, #25
- GPT review (2026-07-13): endorse formula for Eric; require product/plan validation before blind 4,457-policy claim
- References: QLAdmin Help QuikRidr p.~900 (MANNLFEE…); Plan Modal Fees / Mode Factors (Data Maintenance ~p.540)
