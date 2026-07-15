# Issue #75 — Dependency Gate

**Issue:** #75 — Bank Acct / `MBANKNO` QLA validation  
**Framework stage:** Dependency Gate (G2)  
**Generated:** 2026-07-15  
**Model:** Cursor Grok 4.5 (locked)  
**Gate result:** **PASS — Ready for Risk Review**

---

## Source data

| Check | Met? | Notes |
|-------|:----:|-------|
| Required LifePRO extract(s) present in local `Source/` | **N/A*** | Extracts used on batch path (#21H/#45); not checked out in this workspace |
| Before-state measurable | **Met** | `QLA_Migration/Output/quikmstr.csv` + defect CSV |
| Column / mapping documented | **Met** | PPACH / PPPAC / lookup / RNA via prior issues + `app.py` |
| Re-extract required? | **No** | Format defect is in converted output |

\*Development later needs Source extracts on the batch machine (same as #45). Not a blocker for Risk.

---

## Field definitions

| Check | Met? | Notes |
|-------|:----:|-------|
| QLAdmin target table/field | **Met** | `quikmstr.MBANKNO` = Bank Acct (Help § Policy Display) |
| Field semantics / validation | **Met** | Routing + `/` + account; routing validated; `/S` `/A` optional |
| LifePRO source semantics | **Met** | Documented in #21H / #45 |
| Transformation notes | **Met** | Require 9-digit ABA; single slash; strip acct punctuation |

---

## Client clarification

| Check | Met? | Notes |
|-------|:----:|-------|
| Scope boundary | **Met** | Format/validation of Bank Acct emit; SD-75-* |
| Edge cases (blank vs bad ABA) | **Met*** | Soft assumption OBQ-75-1: blank + exception (same as #45) |
| UAT acceptance | **Met** | 010161748C edits without routing error after reload |

\*Soft assumptions documented; Risk may proceed. Client can confirm OBQ-75-1/2 before Development if preferred.

---

## Evidence

| Check | Met? | Notes |
|-------|:----:|-------|
| Example policy | **Met** | 010161748C |
| Screenshot | **Met** | Invalid routing number (//) |
| Before-state measurable | **Met** | 986 ABA≠9; 15 multi-slash; 165 punct |

---

## Regression guards

| Check | Met? | Notes |
|-------|:----:|-------|
| Issue #25 MPOLICY | **Met** | Untouched |
| Issue #26 MPREM | **Met** | Untouched |
| Unrelated rulebooks | **Met** | Emit-path only planned |
| Issue #45 contract | **Met** | Keep both-halves-required emit |

---

## Blockers

**None** for Risk Review.

---

## Gate decision

| Gate | Result |
|------|--------|
| G0 Intake | **PASS** |
| G1 Planning | **PASS** |
| **G2 Dependency** | **PASS** |
| G3 Risk | Await “Proceed to Risk Agent” |

**Recommended tracking status:** **Ready for Risk Review**

---

## Deliverable paths

- `Issue_Log_Items/Issue_75/Issue_75_Tracking_Sheet_Row.tsv`
- `Issue_Log_Items/Issue_75/Issue_75_Intake_Summary.md`
- `Issue_Log_Items/Issue_75/Issue_75_Scope_Decisions.md`
- `Issue_Log_Items/Issue_75/Issue_75_Planning_Report.md`
- `Issue_Log_Items/Issue_75/Issue_75_Dependency_Gate.md`
- `Issue_Log_Items/Issue_75/evidence/issue75_mbankno_format_defects.csv`
