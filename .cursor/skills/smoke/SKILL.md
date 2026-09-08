---
name: smoke
description: Run issue-linked smoke coverage and the workflow smoke gate. Use when the user types /smoke or asks to run smokes for an issue or all issues.
disable-model-invocation: true
---

# /smoke

Read `AI_Agents/Verified_Development_Delivery_Workflow.md`.

1. Parse `<ID>` or `all` from the user text.
2. Run the executable gate (source of truth):

```text
python tools/validators/run_workflow_gate.py --smoke <ID|all>
```

3. If `tools/validators/validate_release_closed_issues.py` exists and the user asked for all, also run:

```text
python tools/validators/validate_release_closed_issues.py --smoke-only
```

4. Report expected, executed, missing, skipped, and failed smoke IDs separately.
5. A registered smoke that did not execute is FAIL. A skipped smoke is NOT_RUN, not PASS.
6. Do not claim coverage from an unrelated existing smoke.
