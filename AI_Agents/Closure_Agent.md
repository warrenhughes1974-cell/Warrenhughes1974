# Closure Agent

**Stage:** 8 of 8  
**Code changes:** **Prohibited** (documentation only)  
**Assigned model (locked 2026-07-22):** **Cursor Grok 4.5** — change only if user manually overrides Framework / stage-agents rule

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

### Brief resolution (required — issue log paste-ready)

**Every closure must produce this line first**, before the long-form report:

```text
Resolution: [One brief sentence — what the fix was. Plain language. Do **not** include engine version in this line.]
```

**Rules:**
- **One sentence** (two only if truly needed for clarity).
- State **what changed**, not the full root-cause essay.
- **Do not put `app.py` / engine version in the Resolution line** — version stays in the resolution summary header / tracking Release column only.
- Use in: resolution summary header, tracking sheet **Resolution** field, and client readout when the user asks for "the resolution."

**Examples:**

| Issue | Brief resolution |
|-------|------------------|
| #21A | Resolution: PPBENTYP cache reads BF_NON_FORFEITURE for ISWL/BF policies and maps LifePRO NFO codes 1 and 2 to APL (MNFOPT=1) per SME guidance. |
| #26 | Resolution: quikridr.MPREM now maps from ANN_PREM_PER_UNIT with MODE_PREMIUM fallback; modal premium on quikmstr unchanged. |
| #25 | Resolution: MPOLICY left-padded to 10 characters across all quik* emit tables. |
| #50 | Resolution: QUIKMEMO fixed-width PNOTE parse + DBF MEMOKEY left-pad for Memo tab SEEK; sample new-note policies 01159D276C, 01222DCC, 01330D153C, … |

Also update (required at G7):

- `Issue_Log_Items/Issue_Log_Master_Tracking_Sheet.md` → status **Closed** + **Resolution** column/field
- Sub-tracking sheet row if applicable — include **Resolution:** line in the row (Description or dedicated column)
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

1. **`Resolution:`** one-line fix summary (paste-ready — **required at top**)
2. Issue ID, title, final status **Closed**
3. Problem statement (1 paragraph) — long-form detail below the brief line
4. Root cause category (mapping / source / scope / client definition)
5. Fix summary (what changed, version, files)
6. Evidence pointers (validation + regression report paths)
7. Trace policy confirmation table
8. Explicit **non-changes** (what was preserved)
9. Residual risks / follow-ups (if any)
10. Rollback notes

---

## Stop Conditions

Do not close if:

- Validation or Regression FAIL
- Client UAT required but not completed (status stays **Ready for Client UAT**)
- Open blocker without documented waiver
- **Output accountability gate fails** (below) — unless the user explicitly waives with reason + date in the resolution summary

### Output accountability gate (required before Closed)

An issue must **not** be marked **Closed** until the fix is proven in **full** `QLA_Migration/Output/` (code-only or `Test_Validation/`-only is insufficient):

1. **Issue validator PASS** on current full Output for the tables this issue owns.
2. **Accountability IN_DATA** for this issue ID via  
   `python tools/validators/validate_issue_log_accountability.py`  
   (or an equivalent spot-check recorded in the resolution summary). **GAP blocks Closure.** Environmental WARN is allowed.
3. **Publish** modified tables to `Output/Test_Validation/` on PASS (partial UAT reload).

Record validator command + accountability status (**IN_DATA**) in `Issue_<ID>_Resolution_Summary.md`.

---

## Gate Criteria (G7 — Closure)

- [ ] **`Resolution:`** one-line fix summary published (paste-ready)
- [ ] Resolution summary published (long-form)
- [ ] Tracking sheets updated with **Resolution** + status **Closed**
- [ ] All artifact paths linked
- [ ] Status set to **Closed** in tracking
- [ ] No open blockers without owner
- [ ] **Output gate:** issue validator PASS on full `QLA_Migration/Output/`
- [ ] **Output gate:** accountability **IN_DATA** for this issue (no GAP); evidence cited in resolution summary
- [ ] **Output gate:** affected tables published to `Output/Test_Validation/`
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

Before marking Closed, confirm Output accountability gate:
- issue validator PASS on full QLA_Migration/Output/
- validate_issue_log_accountability.py shows this issue IN_DATA (GAP blocks Closure)
- affected tables published to Output/Test_Validation/

Produce Issue_<ID>_Resolution_Summary.md suitable for issue log and client readout.
Lead with the required **`Resolution:`** one-line fix summary.
Cite Output gate evidence (validator + IN_DATA).
Update tracking sheet to Closed and include the same Resolution line.
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
