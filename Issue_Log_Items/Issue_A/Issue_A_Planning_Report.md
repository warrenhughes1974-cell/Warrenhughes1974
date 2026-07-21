# Issue A — Planning Report

**Issue:** A — QuikPlan / PVO / rate-key structural defects (internal)  
**Framework stage:** Planning Agent  
**Status:** Planning → Dependency Gate  
**Generated:** 2026-07-20  
**Agent:** Intake/Planning auto-chain (Cursor Grok 4.5)  
**Track:** Internal only — not client-facing

---

## 1. Executive Finding

Robert’s CSO review surfaces a **fleet-wide QuikPlan structural quality gap**: single-premium modal rules, default PVO keys (even when rates are absent), category checkbox ↔ key alignment, VarGP/VarDB consistency, annuity defaults, and `9*` supplemental fields. Several items already appear in `Go_Live_Open_Items_Running.txt` (07, 08, 09, 10, 26, 32, 40). Issue A consolidates them into one **internal** work package plus a **mandatory conversion checklist**.

Recommended direction: treat as a multi-sub-item remediation (A1–A9). Do not code until Eric single-prem list + CSO Calc Dfcy answers arrive for those sub-items; diagnostic/read-only scans can start immediately against current `quikplan` + `Output/rates/`.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/? | Notes |
|--------------|--------------|-------------|-------|
| Product / plan catalog | PPRDF / plan crosswalk | Yes | Plan codes, descriptions, LOB |
| Rate extracts | Rate_Table / PAAGERAT / segments | Yes | Presence/absence of GP/DB/CV/TV/DV |
| Valuation setup | CSO Valuation_Setup (where used) | Partial | Basis for PlCv/PlTv (#80) |

Issue A is primarily **QLAdmin plan-setup correctness**, not policy-row mapping. LifePRO sources inform which plans are single-prem / annuity / supp, but targets are QuikPlan + QuikPl*.

---

## 3. Confirmed QLAdmin Target Structure

| Table / UI | Fields / area | Role |
|------------|---------------|------|
| `quikplan` | PAYYRS, modal factors (SEMI/QTRL/MTH*), PAR, VARDB, VARGP, PLANVALOPT, Calc Dfcy / deficiency flag, supp type, LOB/PRODUCT | Plan header rules |
| QuikPlGd / PlBd / PlUw / PlSt | Category members + GP/DB/CV/TV/DV checkboxes | PVO category settings |
| QuikPlGp / PlDb / PlCv / PlTv / PlDv (+ factor tables) | Keys + basis columns | Rate keys / defaults |
| Annuity int / schg tables | QuikAint / Issc (or equivalent) | Annuity interest + surrender |

**Gold pattern (Robert):** plan **TESTRD** — no rates, but default category records and default keys; CV/TV basis left empty.

---

## 4. Required Source-to-Target Field Mapping (by sub-item)

| Sub-item | Rule | Target | Change? |
|----------|------|--------|---------|
| **A1** Single prem | PAYYRS=1; S/Q/M mode factors = 0.00 | quikplan | Yes (after Eric list) |
| **A2** Calc Dfcy | If no indeterminate prems and CSO says yes → TRUE | quikplan | Yes (after CSO) |
| **A3** Default keys | Every plan: default Gd/Bd/Uw/St + keys (`0`/`00`/…) even if no rates | QuikPl* | Yes |
| **A4** Empty QuikPl* PLAN | No blank-PLAN orphan rows in emit (or intentional global default only if product requires) | QuikPl* | Yes |
| **A5** Basis info | Real CV/TV keys have required basis; defaults may leave basis empty (TESTRD) | QuikPlCv/Tv | Yes |
| **A6** Category ↔ keys | Checkbox GP/DB/CV/TV/DV must match keys present | PlGd/Bd/Uw/St | Yes |
| **A7** VarGP vs rates | VARGP must match PVO/GP rate grain (≠4 if rates exist) | quikplan.VARGP | Yes |
| **A8** Annuity | PAR=0; VARDB=0; PVO defaults incl. gender 0; int + schg configured | quikplan + annuity tables | Yes |
| **A9** Supp `9*` | Supp type populated; PAR=0 | quikplan | Yes |

### Fields that must remain unchanged

| Target | Touch this issue? |
|--------|-------------------|
| MPOLICY padding (#25) | **No** |
| quikridr.MPREM (#26) | **No** |
| Unrelated policy tables (quikmstr/ridr/clms/…) unless plan-key join breaks | **No** |

---

## 5. Open Client / SME Questions

1. **Eric:** Provide authoritative list of single-premium plans (not description-only).
2. **CSO:** For plans without indeterminate premiums, calculate deficiency reserves? (Calc Dfcy TRUE/Y?)
3. **Eric:** Confirm QuikPlan field name for “supp type” on `9*` plans.
4. **Eric/Warren:** Confirm TESTRD is the canonical minimum default-key template for this region.
5. **Eric:** Annuity interest + surrender (schg) — which tables/schedules must be loaded for go-live?

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Default gender | `0` when Not Applicable (annuity / TESTRD pattern) |
| Default UW / Band | `00` |
| Default country/state | `0000` / `00` (or ALL OTHER per TESTRD/region) |
| Default EFFDATE on stub keys | `01/01/1900` if matching existing QuikPl* convention |
| CV/TV basis on default-only keys | Leave empty (Robert) |
| Single prem mode factors | Annual may remain 100; S/Q/M = 0.00 |

---

## 7. Estimated impact

| Area | Estimate |
|------|----------|
| Plans in current package | ~141 (prior go-live scan) |
| Missing default PVO entirely | ~15 (Go-Live Item 07) |
| VARGP=4 systemic | All plans historically (Item 09) — re-scan required |
| Prefix-9 supp plans | ~56 (Item 26) |

Exact counts: re-run read-only scan after next batch (checklist).

---

## 8. Sample traces (for Risk / Validation later)

| Plan | Use |
|------|-----|
| `10L171` | A1 single-prem modal fail |
| `TESTRD` | A3 gold default keys |
| `130JEB` | A6 category mismatch |
| `1659C2` | A7 VarGP mismatch |
| Annuity rider (e.g. A60MIR / A96DAR) | A8 |
| Any `9*` (e.g. 9OLDWP) | A9 |

---

## 9. Risks and unknowns

- Fixing VARGP/VARDB/PVO may overlap Issue #77 closed logic — Risk must define surgical delta only.
- Blank QuikPl* PLAN row may be QLAdmin UI artifact vs real emit — verify CSV before deleting.
- Annuity schg/int may be product-setup (Eric) not conversion inventable.
- Single-prem list dependency blocks A1 automation.

---

## 10. Recommended Risk Agent prompt

```
Proceed to Risk Agent for Issue A (internal).

Read Issue_A_Intake_Summary.md, Issue_A_Planning_Report.md,
Issue_A_Dependency_Gate.md, and Issue_A_Conversion_Checklist.md.

Quantify blast radius per sub-item A1–A9 on quikplan + QuikPl* + rates.
Preserve #25/#26. Do not code. Go / conditional-go / no-go per sub-item.
```

---

## 11. Conversion checklist mandate

Every time Warren asks to **run a conversion / full batch / re-emit**, the agent must execute  
`Issue_Log_Items/Issue_A/Issue_A_Conversion_Checklist.md` and report pass/fail per check.  
Cursor rule: `.cursor/rules/issue-a-conversion-checklist.mdc`.
