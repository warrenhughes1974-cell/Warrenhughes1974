# Development Agent

**Stage:** 5 of 8  
**Code changes:** **Allowed — surgical only**

---

## Purpose

Implement the **approved** fix from Planning + Risk. Changes must be minimal, issue-specific, rollback-safe, and aligned with `AGENTS.md`.

---

## Prerequisites (all required)

- [ ] Planning report complete (G1)
- [ ] Dependency Gate **PASS** (G2)
- [ ] Risk report **Go** or **Conditional Go** (G3)
- [ ] User explicitly approved Development (e.g. "approved for development", "implement the fix")

**Do not start Development from Planning alone.**

---

## Inputs

| Input | Source |
|-------|--------|
| Risk report | Recommended dev task section |
| Planning mapping | Source → target fields |
| Rulebooks | `Sync_Rulebook_*.csv` |
| Engine | `app.py`, `QLA_Migration/app.py`, `qla_core/*` |

---

## Required Research (before editing)

1. Read surrounding code — match naming, patterns, indentation
2. Confirm exact rulebook line(s) to change
3. Identify whether fix is rulebook-only, engine hook, or new table path
4. Plan version bump if `app.py` modified (per AGENTS.md)

---

## Required Deliverables

1. **Surgical code/rulebook diff** (minimal blast radius)
2. **Version bump** in `app.py` / `QLA_Migration/app.py` header if engine touched
3. **Validation script** — `QLA_Migration/_validate_issue<id>_*.py`
4. **Implementation summary** in issue folder: `Issue_<ID>_Implementation_Notes.md`
5. Before/after trace table for example policies
6. List of files changed (for Validation Agent)

### Change constraints (AGENTS.md)

- Do NOT rewrite `app.py` wholesale
- Do NOT alter unrelated field order/types/lengths
- Do NOT change crosswalk behavior unless issue requires it
- Do NOT break Issue #25 `format_qladmin_mpolicy()` behavior
- Do NOT revert Issue #26 `ANN_PREM_PER_UNIT` → `MPREM` + fallback
- Prefer rulebook + minimal engine hook over new frameworks

---

## Stop Conditions

Stop and escalate if:

- Risk assumption invalidated during implementation
- Fix requires broad premium recalculation or schema redesign
- New dependency discovered (return to Dependency Gate)
- Validation script cannot be written against measurable criteria

Do not mark Development complete without validation script.

---

## Gate Criteria (G4 — Development Complete)

- [ ] Only approved scope implemented
- [ ] Version updated if `app.py` changed
- [ ] Validation script added
- [ ] Implementation notes published
- [ ] No unrelated files modified
- [ ] Ready for Validation Agent

---

## Example Cursor Prompt

```
Development Agent — Issue [ID]: [Title]

Approved for development per Issue_<ID>_Risk_Review_Report.md.

Read AI_Agents/Development_Agent.md and AGENTS.md.

Implement surgical fix only:
- [specific rulebook/engine changes from risk report]

Add _validate_issue<id>_*.py
Version bump app.py
Do NOT change [list untouched fields from risk report]

Run batch only if needed for evidence — prefer targeted validation script first.

Deliver implementation notes + before/after trace table.
```

---

## Examples

| Issue | Dev scope |
|-------|-----------|
| **#26** | Rulebook `ANN_PREM_PER_UNIT` → `MPREM`; fallback in engine; v57.31 |
| **#25** | `format_qladmin_mpolicy()` applied post-crosswalk; v57.30 |
| **#21M** | **Not approved** — blocked pre-Development |
