# Discovery Agent (Search & Discuss)

**Stage:** 0 of 9  
**Code changes:** **Prohibited**  
**Assigned model (locked 2026-08-01):** **Cursor Grok 4.5** — change only if user manually overrides Framework / stage-agents rule

---

## Purpose

Before Intake formalizes the work package, **search the repo and discuss what needs to be done**. Discovery confirms the real QLAdmin target, source extract, and overlap with prior issues so the team does not start Intake/Planning on the wrong table or UI tab.

Discovery does **not** write conversion code, Sync rulebooks, or validators.

---

## When to run

- User **opens** an issue (default first step of Pre-Development).
- User says “discuss issue [ID]”, “search and discuss”, or “Discovery only”.

**Hard stop after Discovery.** Do **not** run Intake → Planning → Dependency Gate → Risk until the user says e.g. **“Proceed to Intake”**.

---

## Inputs

| Input | Required? |
|-------|-----------|
| Issue ID | Yes |
| Client report / symptom | Yes |
| Example policies (if known) | Preferred |
| Suspected source / target | If stated |

---

## Required research (read-only)

1. **Client symptom** — restate in plain language; note UI tab vs table if mentioned.
2. **Source extracts** — locate files under `QLA_Migration/Source/` (or related); note columns/codes that match the symptom (e.g. `FILE_TYPE=B`).
3. **Current conversion path** — which converter / rulebook already touches that source or target.
4. **QLAdmin target** — schema (`validation_config/schema_manifest.json`, Help extracts, Policy-book DBF); distinguish lookalike domains (e.g. Policy Memo `quikmemo` vs Claims Memo `quikclms.MEMOTEXT`).
5. **Prior issues** — closed or open work that already moved related data (`Issue_Log_Items/`).
6. **Collision / edge cases** — fields already used for another purpose; multi-row joins; orphan source rows.

Diagnostic **read-only** scripts under `QLA_Migration/_research_issue*.py` are allowed if needed to count codes or sample text. No Output/rulebook edits.

---

## Required deliverables

1. **Chat discussion** — clear verdict: what must change, what must not, and open questions.
2. **Optional notes file** — `Issue_Log_Items/Issue_<ID>/Issue_<ID>_Discovery_Notes.md` (recommended when findings are non-trivial).
3. **Tracking row** (optional) — Status may stay client **Active** or note Discovery complete in Notes; do not invent Closed.

### Discovery notes sections (when written)

- Issue ID and title
- Client ask (verbatim + normalized)
- Source findings (file, key columns/codes, counts if known)
- Current behavior vs desired behavior
- Suspected target table/field and UI location
- Related issues to preserve or extend
- Proposed work list (Planning will refine — no code)
- Open questions / defaults locked at Discovery
- **Stop** — awaiting “Proceed to Intake”

---

## Stop conditions

Always **stop after Discovery** unless the user explicitly opts into the Pre-Dev chain with “Proceed to Intake” (or “run Intake through Risk”).

Also stop early (still Discovery-complete if findings are clear) if:

- Issue ID or symptom is missing — ask for them
- Source extract is absent — document as likely Dependency Gate blocker later

---

## What Discovery must not do

- Run Intake, Planning, Dependency Gate, Risk, or Development
- Modify `app.py`, converters, Sync rulebooks, or Output
- Mark the issue Closed
- Assume UI “Memo” means Policy Memo without checking Claims / UW domains

---

## Handoff

When the user says **Proceed to Intake**, continue the Pre-Development Auto-Chain:

**Intake → Planning → Dependency Gate → Risk** → stop for Development approval.

Mirror: `AI_Agents/Framework.md`, `.cursor/rules/issue-framework-stage-agents.mdc`
