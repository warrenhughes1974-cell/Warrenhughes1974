# Intake Agent

**Stage:** 1 of 8  
**Code changes:** **Prohibited**

---

## Purpose

Accept a new issue log item, normalize it into a structured work package, and confirm it is understood before any research or mapping begins. Intake does not solve the issue — it frames it.

---

## Inputs

| Input | Required? |
|-------|-----------|
| Issue ID (e.g. `#26`, `21M`) | Yes |
| Client report / symptom description | Yes |
| Example policy numbers or screenshots | Strongly preferred |
| Prior issue cross-references | If known |
| Issue tracking sheet row | If exists |

---

## Required Research

- Locate issue in `Issue_Log_Items/Issue_Log_Master_Tracking_Sheet.md` or sub-tracking sheets
- Check for existing analysis drafts in `Issue_Log_Items/Issue_<ID>/`
- Identify affected QLAdmin table(s) from `QLA_Migration/QLAdmin_Converted_Tables.txt`
- Scan `AGENTS.md` for constraints that apply immediately
- Note whether issue overlaps a **closed** fix (#25 MPOLICY, #26 MPREM) — flag as regression if so

---

## Required Deliverables

1. **Intake summary** (1–2 pages) saved as `Issue_Log_Items/Issue_<ID>/Issue_<ID>_Intake_Summary.md`
2. Updated status recommendation for tracking sheet
3. Artifact inventory: what client provided vs what is missing
4. Initial severity / owner (Conversion / Client / Source / Both)

### Intake summary sections

- Issue ID and title
- Client symptom (verbatim + normalized)
- Example policies
- Suspected domain (policy / rider / premium / client / claims / memo / rates)
- In scope / out of scope (first pass)
- Related issues
- Immediate blockers visible at intake

---

## Stop Conditions

Stop and **do not advance to Planning** if:

- Issue ID or client symptom is missing entirely
- Issue is a duplicate of an open item with no new information (merge instead)

Otherwise proceed to Planning Agent.

---

## Gate Criteria (G0 — Intake Complete)

- [ ] Issue folder created under `Issue_Log_Items/`
- [ ] Intake summary written
- [ ] Example policies listed (or marked "none provided")
- [ ] Owner and priority assigned
- [ ] No code or rulebook changes made

---

## Example Cursor Prompt

```
Intake Agent — Issue [ID]: [Title]

Read AI_Agents/Intake_Agent.md and AI_Agents/Framework.md.

Accept this client report and produce Issue_<ID>_Intake_Summary.md only.
Do not code. Do not modify rulebooks. Do not run conversion.

Client report:
[paste]

Example policies: [list]
```

---

## Example — Issue #21M Intake

**Symptom:** Policy notes and ENS messages visible in LifePRO, absent in QLAdmin.  
**Domain:** New table (`quikmemo`).  
**Owner:** Conversion + Client (scope).  
**Blocker hint:** No QUIKMEMO rulebook; extracts may be missing.  
**Status after intake:** Planning
