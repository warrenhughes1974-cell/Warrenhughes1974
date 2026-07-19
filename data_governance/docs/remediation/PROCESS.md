# Data Governance Remediation Process

**Control tower:** one Cursor session owns examine → decision → handoff → close.  
**Execution:** a separate agent implements only the approved item.  
**Hard rule:** no database writes until status is `DECIDED` and an execution handoff (or explicit same-session override) is given.

## Stages (every item)

| Stage | Owner | Writes? | Exit criteria |
|-------|--------|---------|---------------|
| 1. Examine | Control tower | No | Scope, counts, options, validation/regression guards |
| 2. Business Decision | User + control tower | No | `02_decision.md` approved |
| 3. Handoff Prompt | Control tower | No | `03_execution_prompt.md` ready; **auto-launch Execution Agent** when data region + backup path are known (user does not need to paste the prompt) |
| 4. Implement | Execution Agent (Task/subagent) | Yes (item-only) | `04_change_log.md` with row counts |
| 5. Validate | Execution / Validation | Read-only + scripts | Target rule IDs clear or listed exceptions |
| 6. Regression | Execution / Validation | Read-only | Prior CLOSED items still clean; non-candidates unchanged |
| 7. Close | Control tower | Docs only | Tracker `CLOSED`; next item opened |

## Status vocabulary

`QUEUED` → `EXAMINING` → `AWAITING_DECISION` → `DECIDED` → `IN_IMPLEMENTATION` → `VALIDATING` → `REGRESSING` → `CLOSED`  
Also: `BLOCKED`, `DEFERRED`

## Session commands

| User says | Control tower does |
|-----------|-------------------|
| `Start process` | Create/refresh docs; open next QUEUED item Examine |
| `Examine DG-R-00N` | Stage 1 only; present options |
| `Decision: ...` | Write `02_decision.md`; draft execution prompt |
| `Launch execution` / data path provided | Auto-start Execution Agent with `03_execution_prompt.md` (no manual paste) |
| `Give me the execution prompt` | Print copy-paste prompt (optional fallback) |
| `Close DG-R-00N` | Verify artifacts; mark CLOSED; open next |
| `Status` | Summarize TRACKER.md |
| `Defer DG-R-00N because ...` | Mark DEFERRED; open next |

## Artifact layout

```text
data_governance/docs/remediation/
  PROCESS.md
  TRACKER.md
  PROMPT_TEMPLATE.md
  BASELINE_FINDINGS.md
  CONVERSION_SYSTEM_DEFAULTS.md   # rulebook/emit defaults (prevent reintroduction)
  items/
    DG-R-00N_<slug>/
      01_examine.md
      02_decision.md
      03_execution_prompt.md
      04_change_log.md
      05_validation.md
      06_regression.md
```

## Ordering rule

Do not start item N+1 until item N is `CLOSED` or `DEFERRED`.

## Authority references

- Rule catalog: `data_governance/docs/RULE_CATALOG.md`
- Business defaults: `QLA_Migration/Data_Goverence.txt`
- Conversion system defaults: `CONVERSION_SYSTEM_DEFAULTS.md` (rulebook/emit — prefer preventing reintroduction over DBF-only patches)
- Framework overview: `data_governance/README.md`
- Enterprise edit rules: `AGENTS.md` (surgical changes only; governance rules themselves are not rewritten to silence findings)
