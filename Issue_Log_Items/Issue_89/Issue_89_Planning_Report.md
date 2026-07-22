# Issue #89 — Planning Report

**Issue:** #89 — Policy fee wipe on `quikridr`-only rebatch (`MANNLFEE` / modal fees)  
**Framework stage:** Planning Agent  
**Status:** Planning Complete  
**Generated:** 2026-07-22  
**Agent/script:** Planning Agent (Cursor Grok 4.5) — Pre-Risk Auto-Chain

---

## 1. Executive Finding

LifePRO still carries `POLICY_FEE` / `BENEFIT_FEE` = **$10.00** on `9010310404` → `010310404C`, but current `QLA_Migration/Output/quikridr.csv` has **fleet-wide blank** `MANNLFEE` (0 of 6,934 populated). Root cause is architectural: `#21C` loads `_policy_fee_map` **only inside the `quikmstr` table path**, while `#58` modal-fee derivation runs after `quikridr` emit. The 2026-07-21 `#88` **quikridr-only** rebatch never built the fee cache → `MANNLFEE` blank → `#58` logged `updated=0, zero_fee=5083`. Recommended fix: load fee cache on the `quikridr` path (mirror `#88` PPOLC billing-mode cache), add a fail-closed population guard, then re-emit `quikridr`. Fee formula and `#88` MPREM logic stay unchanged.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|--------------|--------------|---------------------|----------:|
| PPOLC | `PPOLC_PolicyMaster_Extract_20260630.csv` | Yes | 5,084 (POLICY_FEE>0 = **4,457**) |
| PPBEN | `PPBEN_PolicyBenefit_Extract_20260630.csv` | Yes | used for ridr emit |

### Available source fields

| Field | Column / source | Populated % | Notes |
|-------|-----------------|------------:|-------|
| Policy number | PPOLC / PPBEN `POLICY_NUMBER` | 100% | Crosswalk → QLA `MPOLICY` |
| Annual policy fee | PPOLC `POLICY_FEE` | ~87% >0 | `#21C` authority |
| Benefit fee | PPBEN `BENEFIT_FEE` | base often matches | corroboration only; do not change map |
| Mode / annual prem | PPOLC `MODE_PREMIUM` / `ANNUAL_PREMIUM` | high | unchanged this issue |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source (Help / schema) |
|-------|-------|------|--------|------------------------|
| quikridr | MANNLFEE | NUMERIC | 8.4 | Help §7.203 — Annual policy fee |
| quikridr | MSEMIFEE | NUMERIC | 8.4 | Semi-annual policy fee |
| quikridr | MQTRLFEE | NUMERIC | 8.4 | Quarterly policy fee |
| quikridr | MMTHDFEE | NUMERIC | 8.4 | Monthly direct policy fee |
| quikridr | MMTHBFEE | NUMERIC | 8.4 | Monthly bank-draft policy fee |

**Repo references** (population paths only):

| Location | Role |
|----------|------|
| `app.py` ~6958–6977 | `#21C` fee cache — **only under `if t_id == quikmstr`** (defect) |
| `app.py` ~7512–7519 | `#21C` interceptor — `MANNLFEE` from `_policy_fee_map` on BENEFIT_SEQ 1 |
| `app.py` ~8353–8573 | `#58` `apply_modal_policy_fees_to_quikridr` post-emit |
| `qla_core/modal_premium_factors.py` | Modal fee derivation |
| `Sync_Rulebook_quikridr.csv` | `MANNLFEE` target with blank source (engine fills) |
| `Issue_88/_rebatch_quikridr.py` | Ridr-only rebatch that wiped fees |
| `QLA_Migration/Logs/_issue88_quikridr_rebatch_log.txt` | Evidence: no fee cache; zero_fee=5083 |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PPOLC | POLICY_FEE | quikridr.MANNLFEE | Base phase (seq 1) only; format money | **No formula change** — **Yes path harden** (load cache on ridr) |
| Derived | MANNLFEE × quikmstr factors/100 | MSEMIFEE / MQTRLFEE / MMTHDFEE / MMTHBFEE | Existing `#58` | **No** |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| quikmstr.MMODEPREM | PPOLC.MODE_PREMIUM | **No** |
| quikridr.MPREM | ANN_PREM_PER_UNIT + `#88` annualized fallback | **No** |
| MPOLICY padding | format_qladmin_mpolicy (#25) | **No** |
| quikmstr MSEMI/MQTRL/MMTHD/MMTHB | `#36` / `#21J` | **No** (post-ridr copy may still run) |
| quikplan *FEE | plan defaults 0 | **No** |

---

## 5. Open Client Questions

| ID | Question | Blocks? |
|----|----------|---------|
| — | None for Development of harden + restore | — |

UAT acceptance is internal/Eric verify on `010310404C` Pol Fee = $10.00 and Names-tab modes include modal fee.

---

## 6. Formatting / Fallback Rules

- Preserve `#21C`: write `MANNLFEE` only when `POLICY_FEE` parses > 0; base BENEFIT_SEQ 1 / MPHASE 1 only.
- Preserve `#58`: `M*FEE = MANNLFEE × (factor/100)` · 4 dp; skip when `MANNLFEE` ≤ 0.
- **New guard (Planning recommendation):** after ridr emit + `#58`, if PPOLC fee>0 count ≥ N (e.g. 1000) and Output base `MANNLFEE`>0 count == 0 → **fail run** (log ERROR). Soft WARN is how this escaped.

---

## 7. Policy Key Handling

- Fee cache keyed by `normalize(POLICY_NUMBER)` (LifePRO), same as today.
- Emit `MPOLICY` via existing crosswalk + `#25` padding — **do not change**.
- Sample: `9010310404` → `010310404C`.

---

## 8. Estimated Record Counts

| Population | Count |
|------------|------:|
| PPOLC `POLICY_FEE` > 0 | 4,457 |
| Current Output `MANNLFEE` populated | **0** (broken) |
| Expected after fix (base rows) | ~4,457 |
| `#58` modal fee updates when fees present | ~4,457 (was 0 on bad rebatch) |

---

## 9. Sample Trace (≥3 policies)

| Policy | Plan | Source POLICY_FEE | Current MANNLFEE | Expected MANNLFEE | Expected modal (S/Q/D/B) |
|--------|------|------------------:|------------------:|------------------:|--------------------------|
| `010310404C` | 1960PO | 10.00 | blank | 10.00 | 5.20 / 2.65 / 0.90 / 0.8702 |
| `010367131C` | 17085M (#58 Eric) | 10.44 | blank | 10.44 | per `#58` validator |
| `010391876C` | (#21C example) | 10.44 | blank | 10.44 | derived from factors |

---

## 10. Risks and Unknowns

| Risk | Mitigation |
|------|------------|
| Future ridr-only scripts again skip fee path | Load cache on **quikridr** path; fail-closed guard |
| Guard false-positive on intentional zero-fee extract | Threshold + compare to PPOLC count in same Source package |
| Touching `#88` MPREM while fixing fees | Explicit no-change; regression spot-check `#88` anchors |
| Full vs ridr-only recovery | Either OK once harden lands; prefer ridr rebatch + validators for speed |

---

## 11. Recommended Risk Agent Prompt

```
Proceed to Risk Agent — Issue #89

Read AI_Agents/Risk_Agent.md, Issue_89_Planning_Report.md,
Issue_89_Intake_Summary.md, Issue_89_Dependency_Gate.md.

Simulate before/after: fleet MANNLFEE populated count; sample
010310404C / 010367131C / 010391876C annual + modal fees.
Confirm #88 MPREM and #26 primary map unchanged.
Do not code. Produce Issue_89_Risk_Review_Report.md.
```

---

## 12. Recommended Development Task (do not implement)

1. In `app.py` / `QLA_Migration/app.py`: load `_policy_fee_map` from PPOLC when processing **`quikridr`** (alongside existing `#88` BILLING_MODE cache). Keep or leave `quikmstr` load; ridr must not depend on table order.
2. After `#58` apply: assert fee population vs PPOLC; **fail** (or hard ERROR blocking success) if catastrophic wipe detected.
3. Bump `APP_VERSION` both app.py copies.
4. Re-emit `quikridr` (ridr rebatch OK once harden is in); run `validate_issue58_quikridr_modal_fees.py` + spot `#21C` / `#88`.
5. Publish `Output/Test_Validation/quikridr.csv` on PASS.
6. Update `_rebatch_quikridr.py` (or docs) so future partial rebatches run fee validators.

**Do not** change fee formula, rulebook fee columns, or MPREM logic.
