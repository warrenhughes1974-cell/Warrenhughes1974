# Run Issue Resolution Framework — Master Prompt

Copy everything below the line into Cursor. Replace the `[ISSUE BLOCK]` with your issue details.

## Locked stage → model map (2026-07-11)

| Stage | Agent | Model |
|-------|--------|-------|
| 1 | Intake | Cursor Grok 4.5 |
| 2 | Planning | Cursor Grok 4.5 |
| 3 | Dependency Gate | Cursor Grok 4.5 |
| 4 | Risk | Cursor Grok 4.5 |
| 5 | Development | Composer 2.5 |
| 6 | Validation | Cursor Grok 4.5 |
| 7 | Regression | Cursor Grok 4.5 |
| 8 | Closure | Composer 2.5 |

Do **not** change this map unless the user manually overrides it. Mirror: `AI_Agents/Framework.md` and `.cursor/rules/issue-framework-stage-agents.mdc`.

---

## Prompt (copy from here)

```
Run the Issue Resolution Framework for the issue below.

Read and follow:
- AI_Agents/Framework.md
- AI_Agents/Intake_Agent.md
- AI_Agents/Planning_Agent.md
- AI_Agents/Dependency_Gate.md
- .cursor/rules/issue-framework-stage-agents.mdc

Use the locked stage→model map in Framework.md.

**Pre-Risk Auto-Chain (default):** In this session, run Intake → Planning → Dependency Gate
automatically on Cursor Grok 4.5. Do not wait for a separate "proceed to Planning" prompt.
Same rule applies when the user says "open issue [ID]" with a symptom.

Do NOT:
- Write or modify conversion code
- Modify Sync_Rulebook_*.csv
- Run full batch conversion
- Skip Dependency Gate if inputs are missing
- Auto-run Risk, Development, or later stages

DO:
- Research the repo, source extracts, rulebooks, QLAdmin Help, and prior Issue_Log_Items artifacts
- Use Templates in AI_Agents/Templates/ for deliverables
- Save deliverables under Issue_Log_Items/Issue_<ID>/
- Create read-only diagnostic scripts under QLA_Migration/_research_issue*.py if needed
- Preserve Issue #25 MPOLICY padding and Issue #26 MPREM mapping in all recommendations
- Follow AGENTS.md surgical-change rules

Stop after Dependency Gate unless I explicitly say:
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

**Not needed for Planning or Dependency Gate** — those are part of the Pre-Risk Auto-Chain when an issue is opened.

Use these **only after** Dependency Gate (or later) and gates pass.

### Risk Agent (Cursor Grok 4.5)

```
Proceed to Risk Agent for Issue [ID].

Read AI_Agents/Risk_Agent.md and AI_Agents/Templates/Risk_Report_Template.md.
Model: Cursor Grok 4.5 (locked). Do not code. Produce before/after impact analysis and go/no-go recommendation.
```

### Development Agent (Composer 2.5 — requires explicit approval)

```
Issue [ID] is approved for Development.

Switch to Composer 2.5. Read AI_Agents/Development_Agent.md.
Make surgical changes only. Version-bump app.py. Add validation script.
Do not regress Issue #25 MPOLICY padding or Issue #26 MPREM mapping.
```

### Validation + Regression (Cursor Grok 4.5) + Closure (Composer 2.5)

```
Issue [ID] development is complete.

Run Validation Agent then Regression Agent on Cursor Grok 4.5; then Closure Agent on Composer 2.5 per AI_Agents/*.md.
Produce validation and regression reports from Templates/.
End with issue-log-ready resolution summary.
```

---

## Quick reference — issue statuses

Intake → Planning → (Blocked | Ready for Risk Review) → Ready for Development → In Development → Ready for Validation → Ready for Client UAT → Closed

See `AI_Agents/Framework.md` for full definitions.
