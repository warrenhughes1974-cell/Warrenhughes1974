---
name: issue
description: Start or continue the verified issue workflow for an issue ID. Use when the user types /issue or asks to open, continue, or process an issue through Discovery through Closure.
disable-model-invocation: true
---

# /issue

Read `AI_Agents/Verified_Development_Delivery_Workflow.md`.

1. Parse the issue ID from the user text (`/issue 143` → `143`).
2. Use the Research agent (Sonnet, `claude-sonnet-5-thinking-high`) for stages 0–4. No production code.
3. Auto-continue Discovery → Intake → Risk unless wrong-target or a missing decision is flagged.
4. On Risk GO with no Closed-row conflict, hand to Coder (`composer-2.5-fast`).
5. After Composer self-test, run:

```text
python tools/validators/run_workflow_gate.py --issue <ID>
python tools/validators/run_workflow_gate.py --smoke <ID>
```

6. If risk_tier is money, engine, status, rates, or claims, invoke Independent Audit (`cursor-grok-4.6-high-fast`) on the frozen candidate. Do not use Auto or inherit.
7. Print the delivery receipt. Empty proof stays NOT_RUN / UNVERIFIED / BLOCKED.
8. Do not say Closed, checked in, or ready for Eric unless the matching gates passed.
