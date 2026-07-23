# LifePRO → QLAdmin Issue Resolution Framework

**Version:** 1.3  
**Project:** Warrenhughes1974 / QLA Migration  
**Scope:** Gated issue log remediation — no code until Development approved  
**Agent map locked:** 2026-07-22 — **Cursor Grok 4.5 for all stages** (was mixed Composer/Grok)  
**Auto-chains locked:** 2026-07-22 — Pre-Dev through Risk; Post-Dev through Validation; Post-Val through Closure  

---

## Purpose

Every issue log item must pass through the same **gated process** before production conversion logic changes. This framework prevents:

- Coding before source data or field definitions are confirmed
- Broad refactors that break stable conversions
- Missing validation/regression evidence
- Unresolved client questions shipped as assumptions

**Hard rule:** Follow `AGENTS.md` enterprise conversion rules at all times. Surgical edits only.

---

## Auto-Chains (default — locked 2026-07-22)

### Pre-Development Auto-Chain (on issue open)

When the user **opens** an issue, complete stages **1 → 4** in the same session:

| Order | Stage | Deliverable |
|------:|-------|-------------|
| 1 | Intake | `Issue_<ID>_Intake_Summary.md` (+ tracking row if needed) |
| 2 | Planning | `Issue_<ID>_Planning_Report.md` |
| 3 | Dependency Gate | `Issue_<ID>_Dependency_Gate.md` |
| 4 | Risk | `Issue_<ID>_Risk_Review_Report.md` |

**Stop after Risk.** Report Go/No-Go findings and **ask for Development approval**.  
Do **not** start Development until the user says e.g. “Approved for Development”.

### Post-Development Auto-Chain (after Dev approval)

**Development → Validation** → then **stop**. Report Validation PASS/FAIL.

### Post-Validation Auto-Chain (after Validation PASS)

**Regression → Closure** (G7 Output accountability + commit/push rules still apply).

**Hard stops:**
- Intake incomplete (no ID / no symptom) → stop
- Dependency Gate **BLOCKED** → stop; do not Risk
- Risk **No-Go** → stop; do not ask for Development
- Validation **FAIL** → stop; return to Development (do not Closure)

**Opt-out:** “Intake only” / “stop after Intake” → stop after Intake.

Mirror: `.cursor/rules/issue-framework-stage-agents.mdc`

---

## Overall Workflow

```mermaid
flowchart TD
    A[Intake Agent] --> B[Planning Agent]
    B --> C{Dependency Gate}
    C -->|Missing inputs| D[Blocked]
    D --> C
    C -->|All dependencies met| E[Risk Agent]
    E --> F{Go / No-Go}
    F -->|No-Go| B
    F -->|Go| G[Development Agent]
    G --> H[Validation Agent]
    H --> I{Pass?}
    I -->|Fail| G
    I -->|Pass| J[Regression Agent]
    J --> K{Pass?}
    K -->|Fail| G
    K -->|Pass| L[Closure Agent]
    L --> N[Git commit + push]
    N --> M[Closed + Issue Log Summary]
```

### Linear stage order

| Stage | Agent | Code allowed? | Assigned model |
|-------|--------|---------------|----------------|
| 1 | Intake | **No** | **Cursor Grok 4.5** |
| 2 | Planning | **No** | **Cursor Grok 4.5** |
| 3 | Dependency Gate | **No** | **Cursor Grok 4.5** |
| 4 | Risk | **No** | **Cursor Grok 4.5** |
| 5 | Development | **Yes** (surgical only) | **Cursor Grok 4.5** |
| 6 | Validation | Read-only + scripts | **Cursor Grok 4.5** |
| 7 | Regression | Read-only + batch/compare | **Cursor Grok 4.5** |
| 8 | Closure | Docs only | **Cursor Grok 4.5** |

**Agent assignment rule:** Use **Cursor Grok 4.5** for every stage unless the user manually changes this table (or `.cursor/rules/issue-framework-stage-agents.mdc`).

---

## Required Decision Gates

| Gate | Location | Pass criteria |
|------|----------|---------------|
| **G0 — Intake complete** | After Intake | Issue scoped, artifacts listed, severity/owner assigned |
| **G1 — Planning complete** | After Planning | Source/target mapping documented, open questions listed |
| **G2 — Dependencies satisfied** | Dependency Gate | No blockers on source files, client answers, field defs, screenshots |
| **G3 — Risk approved** | Risk Agent | Go/conditional-go with quantified impact; fallback rules defined |
| **G4 — Development complete** | Development | Surgical diff, version bump if `app.py`, validation script added |
| **G5 — Validation pass** | Validation | Trace policies, field alignment, row counts per test plan |
| **G6 — Regression pass** | Regression | Unrelated tables/fields unchanged; no schema drift |
| **G7 — Closure** | Closure | **`Resolution:`** one-line fix summary published; resolution summary + tracking sheets updated; **`app.py` version bumped** if engine/rate path touched; **git commit + push to remote** (issue-scoped); **Output accountability gate:** issue validator PASS on full `QLA_Migration/Output/` + accountability **IN_DATA** for this issue (no GAP) + affected tables in `Test_Validation/`; **production-ready** batch verified (validators + network pull instructions) |

**Development cannot begin until G1 + G2 + G3 are satisfied.**

---

## Issue Statuses

Use these statuses in issue tracking sheets and report headers:

| Status | Meaning | Next action |
|--------|---------|-------------|
| **Intake** | Issue received; not yet analyzed | Run Intake Agent |
| **Planning** | Research and mapping in progress | Run Planning Agent |
| **Blocked — Awaiting Client Data** | Missing LifePRO extract, re-pull, or file delivery | Dependency Gate; client action |
| **Blocked — Awaiting Client Clarification** | Business rule, target field, or scope undefined | Dependency Gate; client Q&A |
| **Ready for Risk Review** | Planning done; dependencies clear | Run Risk Agent |
| **Ready for Development** | Risk go/conditional-go approved | Run Development Agent |
| **In Development** | Code/rulebook changes in progress | Complete dev + self-check |
| **Ready for Validation** | Dev complete; awaiting proof | Run Validation Agent |
| **Ready for Client UAT** | Validation + regression pass | Client QLAdmin review |
| **Closed** | Resolution summary published; fix **proven in full Output** (validator PASS + accountability IN_DATA); **committed and pushed** | Archive artifacts; network batch at new `app.py` version |

---

## Framework Rules (Non-Negotiable)

1. **No code changes** during Intake, Planning, Dependency Gate, or Risk stages.
2. **Development cannot begin** until Planning and Risk are complete (G1 + G3).
3. If **source data, client clarification, field definitions, or screenshots** are missing, **stop at Dependency Gate**.
4. All code changes must be **surgical and issue-specific** — no wholesale rewrites.
5. Every development change must include **validation and regression evidence**.
6. Every issue must end with an **issue-log-ready resolution summary** (Closure Agent).
7. **G7 brief resolution (required):** Closure must publish a single paste-ready line — **`Resolution:`** followed by one brief sentence stating what the fix was (**do not include engine version** in this line; version belongs in the summary header / Release column). This line goes in the resolution summary header, tracking sheets, and client readout — not only the long-form report.
8. **G7 release gate:** When Development touched conversion or rate code, Closure must **commit issue-scoped changes and `git push` to remote** so network batch machines can pull the fix. Bump **`app.py` version** when the batch path changes.
9. **G7 Output accountability gate:** Do **not** mark **Closed** until (a) the issue validator PASSes on **full** `QLA_Migration/Output/`, (b) `validate_issue_log_accountability.py` (or equivalent) shows this issue **IN_DATA** (GAP blocks Closure), and (c) affected tables are published to `Output/Test_Validation/`. Code-only or TV-only proof is insufficient. User waiver only, with reason + date.
10. **Preserve prior fixes:** Issue #25 MPOLICY padding (`format_qladmin_mpolicy`) and Issue #26 MPREM mapping (`ANN_PREM_PER_UNIT` + fallback) must not regress.

---

## Artifact Locations

| Artifact type | Typical path |
|---------------|--------------|
| Issue deliverables | `Issue_Log_Items/Issue_<NN>/` or `Issue_<NN><Letter>/` |
| Research scripts | `tools/validators/`, `Issue_Log_Items/Issue_*/scripts/`, legacy stubs at `QLA_Migration/_*.py` |
| Rulebooks | `QLA_Migration/Configs/Sync_Rulebook_*.csv` |
| Crosswalk | `QLA_Migration/Mapping/Master_Crosswalk.csv` |
| Source extracts | `QLA_Migration/Source/` |
| Conversion output | `QLA_Migration/Output/` |
| Agent prompts | `AI_Agents/*.md` |
| Templates | `AI_Agents/Templates/` |

---

## Examples by Issue

### Issue #25 — MPOLICY fixed-width padding

| Stage | Outcome |
|-------|---------|
| Intake | Client: QLAdmin "Policy Not Found" for short policy keys |
| Planning | Target: 10-char left-pad on MPOLICY across quik* tables |
| Dependency Gate | Crosswalk + output CSV verified; no client blocker |
| Risk | Low blast radius; DBF `.strip()` on load noted as separate concern |
| Development | `format_qladmin_mpolicy()` in `qla_core/normalize_utils.py`; v57.30 |
| Validation | `_validate_mpolicy_width.py` — 279k fields, 0 short |
| Regression | Row counts unchanged; only MPOLICY width |
| Closure | Issue #25 resolved; padding preserved for all future issues |

**Lesson:** Display/locate failures may be CSV vs DBF load — plan DBF path separately if needed.

---

### Issue #26 — MPREM annual premium per unit

| Stage | Outcome |
|-------|---------|
| Intake | Prem/Unit on Coverage tab wrong; client values match modal premium |
| Planning | QLAdmin Help: `MPREM` = annual premium per unit → `ANN_PREM_PER_UNIT` |
| Dependency Gate | PPBEN extract available; QLAdmin field def confirmed |
| Risk | 3,718 rows change; fallback for blank ANN (`MODE_PREMIUM`); MMODPREM untouched |
| Development | Rulebook + engine fallback; v57.31; `_validate_issue26_mprem.py` |
| Validation | Trace policies 13.20 / 10.96 / 9.12; MMODPREM unchanged |
| Regression | quikprmh, MVPU, MUNIT, row counts unchanged |
| Closure | MPREM fix documented; modal premium remains on quikmstr |

**Lesson:** Always run Planning + Risk before mapping changes that touch premium semantics.

---

### Issue #21M — QUIKMEMO / Policy Notes / ENS

| Stage | Outcome |
|-------|---------|
| Intake | Notes/ENS not converted; no quikmemo rulebook |
| Planning | Target QUIKMEMO (`MEMOKEY` + `MEMOTEXT`); sources PNOTE + PENSE cited |
| Dependency Gate | **BLOCKED** — PNOTE/PENSE not in Source/ package |
| Risk | Not started (awaiting extracts) |
| Development | **No-Go** |
| Validation | — |
| Regression | — |
| Closure | Pending |

**Lesson:** New-table builds stop at Dependency Gate until LifePRO delivers extracts.

---

## How to Run

1. Open an issue in chat (or paste the master prompt from `AI_Agents/Run_Issue_Framework_Prompt.md`)
2. Agent auto-runs **Intake → Planning → Dependency Gate → Risk** on Cursor Grok 4.5, then stops and asks for Development approval
3. Say **“Approved for Development”** → agent runs **Development → Validation**, then stops with Validation readout
4. On Validation **PASS**, agent continues **Regression → Closure** (G7 gates still apply)

---

## Related Documents

- `AGENTS.md` — Enterprise conversion guardrails
- `AI_Agents/Dependency_Gate.md` — Blocker checklist
- `AI_Agents/Templates/` — Report templates
- `Issue_Log_Items/Issue_Log_Master_Tracking_Sheet.md` — Master issue index
