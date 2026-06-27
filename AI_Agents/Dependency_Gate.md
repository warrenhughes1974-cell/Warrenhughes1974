# Dependency Gate

**Stage:** 2.5 (between Planning and Risk)  
**Code changes:** **Prohibited**

---

## Purpose

Hard stop checkpoint. Verify all **external and client-owned dependencies** are satisfied before spending effort on risk quantification or development. The gate prevents building on missing extracts, undefined fields, or unanswered business questions.

---

## Inputs

| Input | Source |
|-------|--------|
| Planning report | `Issue_<ID>_Planning_Report.md` |
| Open questions list | Planning §5 |
| Source folder inventory | `QLA_Migration/Source/` |
| Client artifacts | docx, screenshots, Issue_Log_Items |

---

## Dependency Checklist

Mark each item **Met**, **Missing**, or **N/A**:

### Source data

| Check | Met? |
|-------|------|
| Required LifePRO extract(s) present in `QLA_Migration/Source/` | |
| Extract row count > 0 | |
| Column headers documented (not just Excel letters) | |
| Extract date/version matches batch under test | |
| Re-extract required? (document if yes) | |

### Field definitions

| Check | Met? |
|-------|------|
| QLAdmin target table confirmed (Help PDF / schema) | |
| QLAdmin target field semantics confirmed | |
| LifePRO source field semantics confirmed | |
| Transformation notes identified (dates, money, padding) | |

### Client clarification

| Check | Met? |
|-------|------|
| Scope boundary agreed (in / out) | |
| Business rule for edge cases (fallback, blank, zero) | |
| Retention / filtering rules (if applicable) | |
| UAT acceptance criteria stated | |

### Evidence

| Check | Met? |
|-------|------|
| Example policies identified | |
| Screenshots or docx support client claim | |
| Before-state measurable from current output | |

### Regression guards

| Check | Met? |
|-------|------|
| Plan preserves Issue #25 MPOLICY padding | |
| Plan preserves Issue #26 MPREM mapping | |
| Plan does not alter unrelated rulebooks | |

---

## Required Deliverables

Add section to planning report or create:

`Issue_Log_Items/Issue_<ID>/Issue_<ID>_Dependency_Gate.md`

Contents:

1. Checklist with Met/Missing/N/A
2. **Status:** PASS | FAIL
3. If FAIL: exact blocker list + owner + requested client action
4. Recommended issue status update

---

## Stop Conditions

**FAIL — stop pipeline** when any required item is Missing without documented client waiver:

| Blocker type | Issue status |
|--------------|--------------|
| Missing extract / file | **Blocked — Awaiting Client Data** |
| Undefined business rule / scope | **Blocked — Awaiting Client Clarification** |
| Missing QLAdmin field definition | **Blocked — Awaiting Client Clarification** |
| No example policies or evidence | **Blocked — Awaiting Client Clarification** (or proceed with fleet-only analysis if Risk agrees) |

**PASS — proceed to Risk Agent** when all required dependencies Met or explicitly waived in writing by client.

---

## Gate Criteria (G2 — Dependencies Satisfied)

- [ ] Dependency gate document published
- [ ] Status is PASS, or FAIL with no advancement to Risk
- [ ] Tracking sheet status updated
- [ ] No code changes

---

## Example Cursor Prompt

```
Dependency Gate — Issue [ID]

Read AI_Agents/Dependency_Gate.md and the Issue_<ID>_Planning_Report.md.

Evaluate the checklist. Do not code.

Publish Issue_<ID>_Dependency_Gate.md with PASS or FAIL.
If FAIL, set status to Blocked — Awaiting Client Data or Clarification.
```

---

## Examples

| Issue | Gate result |
|-------|-------------|
| **#26** | PASS — PPBEN in Source; QLAdmin Help confirms MPREM |
| **#25** | PASS — crosswalk + output available |
| **#21M** | FAIL — PNOTE/PENSE not in Source/ |
