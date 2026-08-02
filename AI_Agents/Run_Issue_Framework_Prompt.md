# Run Issue Resolution Framework — Master Prompt

Copy everything below the line into Cursor. Replace the `[ISSUE BLOCK]` with your issue details.

## Locked stage → model map (Stage 0 locked 2026-08-01)

| Stage | Agent | Model |
|-------|--------|-------|
| 0 | Discovery | Cursor Grok 4.5 |
| 1 | Intake | Cursor Grok 4.5 |
| 2 | Planning | Cursor Grok 4.5 |
| 3 | Dependency Gate | Cursor Grok 4.5 |
| 4 | Risk | Cursor Grok 4.5 |
| 5 | Development | Cursor Grok 4.5 |
| 6 | Validation | Cursor Grok 4.5 |
| 7 | Regression | Cursor Grok 4.5 |
| 8 | Closure | Cursor Grok 4.5 |

Do **not** change this map unless the user manually overrides it. Mirror: `AI_Agents/Framework.md` and `.cursor/rules/issue-framework-stage-agents.mdc`.

**Auto-chains:** Open → **Discovery (stop)** → on “Proceed to Intake” Intake→Planning→DG→Risk (stop for Dev approval) → after approval Dev→Validation (stop) → on Val PASS Regression→Closure.

---

## Prompt (copy from here)

```
Run the Issue Resolution Framework for the issue below.

Read and follow:
- AI_Agents/Framework.md
- AI_Agents/Discovery_Agent.md
- AI_Agents/Intake_Agent.md
- AI_Agents/Planning_Agent.md
- AI_Agents/Dependency_Gate.md
- .cursor/rules/issue-framework-stage-agents.mdc

Use the locked stage→model map in Framework.md.

**Discovery first (default):** Run Discovery (Search & Discuss) on Cursor Grok 4.5.
Search the repo/sources/UI target, discuss what needs to be done, optionally write
Issue_<ID>_Discovery_Notes.md. STOP after Discovery and ask whether to Proceed to Intake.
Do NOT run Intake → Risk until the user says "Proceed to Intake".

**Pre-Development Auto-Chain (after Proceed to Intake):** Run Intake → Planning →
Dependency Gate → Risk automatically on Cursor Grok 4.5. Stop after Risk and ask for
Development approval.

Do NOT (before Development approval):
- Write or modify conversion code
- Modify Sync_Rulebook_*.csv
- Run full batch conversion
- Skip Dependency Gate if inputs are missing
- Start Development without explicit approval
- Skip Discovery unless the user says "Skip Discovery" or opens with "Proceed to Intake"

DO:
- Research the repo, source extracts, rulebooks, QLAdmin Help, and prior Issue_Log_Items artifacts
- Distinguish lookalike UI domains (e.g. Policy Memo vs Claims Memo)
- Use Templates in AI_Agents/Templates/ for Intake+ deliverables
- Save deliverables under Issue_Log_Items/Issue_<ID>/
- Create read-only diagnostic scripts under QLA_Migration/_research_issue*.py if needed
- Preserve Issue #25 MPOLICY padding and Issue #26 MPREM mapping in all recommendations
- Follow AGENTS.md surgical-change rules

After Discovery, wait for: "Proceed to Intake."
After Risk GO, wait for: "Approved for Development."
Then run Development → Validation and stop with Validation readout.
On Validation PASS, continue Regression → Closure.

At the end of Discovery, report:
1. Verdict — what must change / must not
2. Suspected source and QLAdmin target (table/field + UI)
3. Related issues
4. Open questions
5. Ask: Proceed to Intake?

At the end of the Pre-Dev chain, report:
1. Current issue status (from Framework.md status list)
2. Gate passed / blocked
3. Deliverable file paths
4. Open client questions
5. Ask for Development approval (if Risk GO)

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

### After Discovery (required unless Discovery skipped)

```
Proceed to Intake for Issue [ID].

Continue the Pre-Development Auto-Chain: Intake → Planning → Dependency Gate → Risk.
Stop after Risk and ask for Development approval. No conversion code.
```

**Not needed for Planning or Dependency Gate** — those are part of the Pre-Dev Auto-Chain after Proceed to Intake.

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

Discovery → Intake → Planning → (Blocked | Ready for Risk Review) → Ready for Development → In Development → Ready for Validation → Ready for Client UAT → Closed

See `AI_Agents/Framework.md` for full definitions.
