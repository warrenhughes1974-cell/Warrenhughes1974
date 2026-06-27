# Planning Agent

**Stage:** 2 of 8  
**Code changes:** **Prohibited**

---

## Purpose

Determine **how** the issue should be fixed: confirm LifePRO sources, QLAdmin targets, field mappings, formatting rules, and open questions. Planning produces the blueprint Development will follow.

---

## Inputs

| Input | Source |
|-------|--------|
| Intake summary | `Issue_<ID>_Intake_Summary.md` |
| LifePRO source extracts | `QLA_Migration/Source/` |
| Rulebooks | `QLA_Migration/Configs/Sync_Rulebook_*.csv` |
| Crosswalk | `QLA_Migration/Mapping/Master_Crosswalk.csv` |
| QLAdmin Help | `docs/claims_conversion_reference/QLAdmin_Help.pdf` |
| Prior research reports | `Issue_Log_Items/Issue_<ID>/` |

---

## Required Research

1. **LifePRO source:** table/file name, columns, row grain, sample policies
2. **QLAdmin target:** table, field names, types, lengths (Help PDF or schema manifest)
3. **Current mapping:** grep rulebooks + `app.py` for target fields
4. **Population analysis:** counts, blank rates, plan/benefit breakdowns (read-only scripts OK)
5. **Trace policies:** before-state for client examples
6. **Unrelated fields:** explicitly list what must **not** change
7. **Prior fixes:** confirm plan does not break #25 MPOLICY padding or #26 MPREM

---

## Required Deliverables

Use `AI_Agents/Templates/Planning_Report_Template.md`.

Save as: `Issue_Log_Items/Issue_<ID>/Issue_<ID>_Planning_Report.md`

Optional read-only script: `QLA_Migration/_research_issue<id>_<topic>.py`

### Minimum content

1. Executive finding
2. Confirmed LifePRO source(s)
3. Confirmed QLAdmin target structure
4. Proposed source-to-target mapping
5. Open client questions
6. Formatting / fallback rules
7. Policy key handling (crosswalk + MPOLICY padding)
8. Estimated record counts
9. Sample trace (≥3 policies)
10. Risks and unknowns
11. Recommended Risk Agent prompt
12. Recommended Development task (do not implement)

---

## Stop Conditions

Stop after Planning and run **Dependency Gate** before Risk if any of:

- Source file not in repo and not confirmed deliverable
- QLAdmin target field undefined
- Client scope ambiguous (convert X or Y?)
- Mapping requires premium recalculation globally

**Do not proceed to Risk Agent** until Dependency Gate clears blockers (or documents accepted assumptions with client sign-off).

---

## Gate Criteria (G1 — Planning Complete)

- [ ] Planning report published
- [ ] Source and target documented (or gap explicitly listed)
- [ ] Trace table included (or blocked reason)
- [ ] Open questions enumerated
- [ ] Development task outlined but **not executed**
- [ ] No code, rulebook, or output changes

---

## Example Cursor Prompt

```
Planning Agent — Issue [ID]: [Title]

Read AI_Agents/Planning_Agent.md and Templates/Planning_Report_Template.md.

Research only — no code changes, no rulebook changes, no batch run.

Deliver Issue_<ID>_Planning_Report.md and optional _research_issue*.py.

Preserve Issue #25 MPOLICY padding and Issue #26 MPREM behavior in recommendations.

Issue context:
[paste intake summary or client report]
```

---

## Examples

| Issue | Planning outcome |
|-------|------------------|
| **#26** | Map `ANN_PREM_PER_UNIT` → `MPREM`; fallback `MODE_PREMIUM`; MMODPREM unchanged |
| **#25** | 10-char left-pad MPOLICY via `format_qladmin_mpolicy()` |
| **#21M** | QUIKMEMO target confirmed; PNOTE/PENSE missing → stop at Dependency Gate |
