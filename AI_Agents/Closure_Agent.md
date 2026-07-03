# Closure Agent

**Stage:** 8 of 8  
**Code changes:** **Prohibited** (documentation only)

---

## Purpose

Produce the **issue-log-ready resolution summary** that closes the item in client tracking sheets. Closure consolidates Intake → Regression into a single authoritative record for audit and future agents.

---

## Inputs

| Input | Source |
|-------|--------|
| Intake summary | Optional reference |
| Planning report | Mapping decisions |
| Risk report | Go decision + impact |
| Implementation notes | What changed |
| Validation report | PASS |
| Regression report | PASS |
| Client UAT feedback | If available |

---

## Required Research

- Verify all prior stage deliverables exist in `Issue_Log_Items/Issue_<ID>/`
- Confirm validation + regression both PASS (or document client UAT waiver)
- List exact files/version for rollback reference

---

## Required Deliverables

Use `AI_Agents/Templates/Issue_Resolution_Template.md`.

Save as: `Issue_Log_Items/Issue_<ID>/Issue_<ID>_Resolution_Summary.md`

Also update (required at G7):

- `Issue_Log_Items/Issue_Log_Master_Tracking_Sheet.md` → status **Closed**
- Sub-tracking sheet row if applicable
- **`app.py` / `QLA_Migration/app.py` version bump** when batch or rate pipeline changed (sync both files)
- **Git:** stage issue-scoped files only → commit → **`git push -u origin HEAD`** (user-approved branch)
- Resolution summary records **commit hash** and **remote branch** for network rollout

### G7 git release workflow (automatic)

When Validation + Regression both PASS and the user approves closure:

1. Confirm production-ready checklist (validators PASS; `app.py` version if applicable).
2. Stage **issue-scoped files only** — do not commit unrelated workspace changes.
3. Commit with message: `Close Issue #NN: [title] (vXX.XX)`.
4. **`git push -u origin HEAD`** — required so network batch machines receive the fix.
5. Record commit hash + branch in `Issue_<ID>_Resolution_Summary.md`.
6. Note: `QLA_Migration/Output/` is gitignored — document **GENERATE RATE TABLES** / batch re-run on network after pull.

### Resolution summary must include

1. Issue ID, title, final status **Closed**
2. Problem statement (1 paragraph)
3. Root cause category (mapping / source / scope / client definition)
4. Fix summary (what changed, version, files)
5. Evidence pointers (validation + regression report paths)
6. Trace policy confirmation table
7. Explicit **non-changes** (what was preserved)
8. Residual risks / follow-ups (if any)
9. Rollback notes

---

## Stop Conditions

Do not close if:

- Validation or Regression FAIL
- Client UAT required but not completed (status stays **Ready for Client UAT**)
- Open blocker without documented waiver

---

## Gate Criteria (G7 — Closure)

- [ ] Resolution summary published
- [ ] All artifact paths linked
- [ ] Status set to **Closed** in tracking
- [ ] No open blockers without owner
- [ ] **Production ready:** `app.py` version bumped when batch/rate path changed; validators PASS; network batch instructions documented (`Output/` gitignored → re-run emit on pull)
- [ ] **Git release:** issue-scoped **commit** created; **`git push`** to remote completed (or user explicitly waives push with reason)
- [ ] Commit hash + branch recorded in resolution summary
- [ ] Framework cycle complete

---

## Example Cursor Prompt

```
Closure Agent — Issue [ID]

Read AI_Agents/Closure_Agent.md and Templates/Issue_Resolution_Template.md.

Validation and Regression both PASS.

Produce Issue_<ID>_Resolution_Summary.md suitable for issue log and client readout.
Update tracking sheet to Closed.
If Development touched code: bump app.py version, commit issue-scoped files, git push to remote.
Record commit hash in resolution summary.

Do not modify conversion code beyond version header if already committed in G4.
```

---

## Examples

| Issue | Closure headline |
|-------|------------------|
| **#26** | MPREM now maps annual premium per unit; modal premium unchanged on quikmstr; v57.31 |
| **#25** | MPOLICY left-padded to 10 characters across quik* emit; v57.30 |
| **#21M** | Not closed — blocked at Dependency Gate |
