# Run Issue Resolution Framework — Master Prompt

Copy everything below the line into Cursor. Replace the `[ISSUE BLOCK]` with your issue details.

---

## Prompt (copy from here)

```
Run the Issue Resolution Framework for the issue below.

Read and follow:
- AI_Agents/Framework.md
- AI_Agents/Intake_Agent.md
- AI_Agents/Planning_Agent.md
- AI_Agents/Dependency_Gate.md

Start with Intake Agent and Planning Agent ONLY.

Do NOT:
- Write or modify conversion code
- Modify Sync_Rulebook_*.csv
- Run full batch conversion
- Skip Dependency Gate if inputs are missing

DO:
- Research the repo, source extracts, rulebooks, QLAdmin Help, and prior Issue_Log_Items artifacts
- Use Templates in AI_Agents/Templates/ for deliverables
- Save deliverables under Issue_Log_Items/Issue_<ID>/
- Create read-only diagnostic scripts under QLA_Migration/_research_issue*.py if needed
- Preserve Issue #25 MPOLICY padding and Issue #26 MPREM mapping in all recommendations
- Follow AGENTS.md surgical-change rules

Stop after Planning (+ Dependency Gate assessment) unless I explicitly say:
"Proceed to Risk Agent" or "Approved for Development."

At the end, report:
1. Current issue status (from Framework.md status list)
2. Gate passed / blocked
3. Deliverable file paths
4. Open client questions
5. Recommended next agent and prompt

---

[ISSUE BLOCK]

Issue ID:
Title:
Client report (paste):
Affected policies/examples:
Known LifePRO fields or tables:
Suspected QLAdmin target:
Priority:
Any screenshots or docx references:

```

---

## Stage advancement prompts

Use these **only after** the prior stage deliverable exists and gates pass.

### Risk Agent

```
Proceed to Risk Agent for Issue [ID].

Read AI_Agents/Risk_Agent.md and AI_Agents/Templates/Risk_Report_Template.md.

Do not code. Produce before/after impact analysis and go/no-go recommendation.
```

### Development Agent (requires explicit approval)

```
Issue [ID] is approved for Development.

Read AI_Agents/Development_Agent.md.

Make surgical changes only. Version-bump app.py. Add validation script.
Do not regress Issue #25 MPOLICY padding or Issue #26 MPREM mapping.
```

### Validation + Regression + Closure

```
Issue [ID] development is complete.

Run Validation Agent, then Regression Agent, then Closure Agent per AI_Agents/*.md.

Produce validation and regression reports from Templates/.
End with issue-log-ready resolution summary.
```

---

## Quick reference — issue statuses

Intake → Planning → (Blocked | Ready for Risk Review) → Ready for Development → In Development → Ready for Validation → Ready for Client UAT → Closed

See `AI_Agents/Framework.md` for full definitions.
