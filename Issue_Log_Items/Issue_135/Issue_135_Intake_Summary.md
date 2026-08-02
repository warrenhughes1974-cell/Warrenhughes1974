# Issue #135 — Intake Summary

**Issue:** #135 — Claims Settlement vs CSO Total_Paid  
**Date:** 2026-08-02  
**Framework stage:** Intake complete (G0) — after Stage 0 Discovery  
**Status recommendation:** Proceed Planning → Dependency Gate → Risk  
**Owner:** Conversion (Warren)  
**Raised by:** Warren (client spreadsheets `docs/Claims/`)  
**Priority:** Go  
**Related:** Client Items 14–19 / Phase 23–24; #78, #79, #84, #85, #134; ISWL/PS emit (#34)  
**Code changes:** None  

---

## Client / business symptom (normalized)

Death-claim **paid amounts** in conversion do not reliably match the client CSO claims summary **`Total_Paid`**. Client accounting examples (red text) show specific failure modes: reinstatement multi-count, intra-company duplicate payouts, missing loan-death checks, interest double-count paths, and surrender death-date / incomplete surrender amounts.

---

## Locked decisions (Intake)

| Decision | Source | Lock |
|---|---|---|
| CSO `Total_Paid` is a **hard control** for death claims | User 2026-08-02 | Locked |
| Reverse-engineer PACTG include/exclude rules from `Total_Paid` + accounting examples | Discovery + user | Locked |
| Claim interest field **`MINTAMT` always 0.00** on emit (do not populate interest) | User 2026-08-02 | Locked |
| Paid amount lives in `MPAID` / payee `MAMOUNT` (and related header money fields as already used) | Schema / current path | Locked |

---

## Example policies (teacher / defect set)

| Policy | Defect class | CSO / sheet expected | Current Output (approx) |
|---|---|---:|---:|
| `9011156098C` | Reinstatement triple-count | 15,000.00 | 45,000.00 |
| `9010914301C` | Intra-co / unapplied duplicate | 25,019.98 | 50,039.96 |
| `9010391359C` | Loan death missing payout | 1,260.06 | 0.00 (no payee) |
| `9010150740C` | Div-deposit exclude (good amount) | 3,213.59 | 3,213.59 (missing payee) |
| `9010402010C` | Interest in check; `MINTAMT` set | 8,920.15 | MPAID OK; MINTAMT 1,780.58 → zero |
| `9010429064C` / `9010430296C` | Same interest pattern | sheet J | MPAID OK; zero MINTAMT |
| `9010360289C` / `9010753675C` / `9010429711C` | Surrender incomplete | sheet J | matches incomplete L |
| `9010746846C` | Full surrender vs PS-only | ~21,940 | 7× $271 PS |

Population control: **~1,656** CSO death claims → ~1,111 amount OK / ~86 mismatch / ~459 missing (Discovery snapshot).

---

## Suspected domain

**Claims financial conversion** — `quikclms` settlement amounts + `quikclmp` payments; PACTG reconstruction / balancing / derivation under `claims_analysis/`.

---

## In scope / out of scope (first pass)

| In scope | Out of scope |
|---|---|
| Death `MPAID` / payee sums = CSO `Total_Paid` | Recalculating premiums / rates / QuikPlan |
| PACTG include/exclude rule reverse-engineering | Changing #134 Claims Memo routing |
| Always emit `MINTAMT=0` (and related unused interest fields if Planning confirms) | Inventing interest accrual for QLAdmin |
| Fix known defect classes (reinstatement, duplicates, loan death) | Non-claims tables (`quikmstr`, `quikridr`, …) |
| Clear `DTOFDEATH` on non-death claim families | Full GL redesign outside claims path |
| Surrender completeness / death-date (linked workstream) | Production DBF flag changes without auth |

---

## Related issues

| Issue | Note |
|---|---|
| Items 14–19 / Phase 23–24 | Div-deposit exclusion, orphan standalones, loan combine — extend |
| #78 / #84 / #85 | Payee recovery, header backfill, claim identity |
| #79 | CLAIMSTAT remap — preserve |
| #134 | MEMOTEXT — do not regress |
| #34 / ISWL PS | Partial surrender rows interact with death-date / amounts |

---

## Immediate blockers visible at intake

None blocking Intake. Full-population CSO hard control depends on reverse-engineering work in Development (phased). Missing ~459 CSO deaths may be extract/hold/eligibility — must classify before Closure.

---

## Artifact inventory

| Artifact | Status |
|---|---|
| `docs/Claims/CSO Life claims summary - 2017 - 2025.xlsx` | Present |
| `docs/Claims/Claim Accounting examples.xlsx` | Present (red text) |
| PACTG extract in Source | Present (`PACTG_Accounting_Extract20260630.csv`) |
| PRELSA extract in Source | Present |
| Discovery notes | Present |
| Reverse-engineering method | Present in Discovery notes |

---

## Owner / severity

| Item | Value |
|---|---|
| Owner | Conversion |
| Priority | **Go** |
| Severity | High — claims financial hard control |
