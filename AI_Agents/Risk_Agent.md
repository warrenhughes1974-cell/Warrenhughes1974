# Risk Agent

**Stage:** 4 of 8  
**Code changes:** **Prohibited**

---

## Purpose

Quantify **before/after impact** of the proposed fix, evaluate fallback options, identify regression surfaces, and issue a **Go / Conditional Go / No-Go** recommendation for Development. Risk proves the change is safe enough to implement — or documents why it is not.

---

## Inputs

| Input | Source |
|-------|--------|
| Planning report | Passed Dependency Gate |
| Dependency gate | PASS |
| Current conversion output | `QLA_Migration/Output/` |
| Source extracts | `QLA_Migration/Source/` |
| Crosswalk | `Master_Crosswalk.csv` |
| Prior risk reports | e.g. Issue #26 MPREM risk review pattern |

---

## Required Research

1. Every repo location that **populates, transforms, validates, or references** the target field/table
2. **Population analysis:** row counts, blank rates, diffs by plan/seq/status
3. **Before/after simulation** (read-only script — no production logic change)
4. **Fallback options** with row-impact counts (if applicable)
5. **Unrelated fields** that must remain unchanged — verify with joins to source
6. **Trace policies** — simulated after values
7. **Top N largest changes** (if numeric field)
8. Edge cases from Planning open questions

---

## Required Deliverables

Use `AI_Agents/Templates/Risk_Report_Template.md`.

Save as: `Issue_Log_Items/Issue_<ID>/Issue_<ID>_Risk_Review_Report.md`

Optional script: `QLA_Migration/_risk_review_issue<id>_*.py`

Must include:

- Go / No-Go recommendation
- Before/after impact counts
- Fallback recommendation (if any)
- Regression surfaces
- Recommended Development Agent task (exact, surgical)
- Regression testing checklist for Validation Agent

---

## Stop Conditions

- **No-Go:** Do not advance to Development; return to Planning or Dependency Gate
- **Conditional Go:** Development may proceed only with documented fallback/scope limits
- **Go:** Development explicitly approved by user after Risk report review

Never implement code during Risk stage.

---

## Gate Criteria (G3 — Risk Approved)

- [ ] Risk report published with Go/No-Go
- [ ] Impact quantified (not guessed)
- [ ] Unrelated fields explicitly marked untouched
- [ ] #25 / #26 preservation confirmed
- [ ] User (or project lead) acknowledged recommendation

---

## Example Cursor Prompt

```
Risk Agent — Issue [ID]: [Title]

Read AI_Agents/Risk_Agent.md and Templates/Risk_Report_Template.md.

Read-only before/after simulation. Do NOT change production mapping or app.py.

Use QLA_Migration/_risk_review_issue*.py pattern if helpful.

Deliver Issue_<ID>_Risk_Review_Report.md with go/no-go.

Planning report: [path]
```

---

## Examples

| Issue | Risk outcome |
|-------|--------------|
| **#26** | Conditional Go — `mode_prem` fallback; 3,718 rows change; MMODPREM untouched |
| **#25** | Go — padding only; low blast radius |
| **#21M** | Not run — blocked at Dependency Gate |
