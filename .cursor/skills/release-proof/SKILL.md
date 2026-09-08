---
name: release-proof
description: Run release-candidate proof for an issue or release ID, including package and destination checks. Use when the user types /release-proof or asks if a package is ready for Eric or released.
disable-model-invocation: true
---

# /release-proof

Read `AI_Agents/Verified_Development_Delivery_Workflow.md`.

Luna orchestrates release proof and does not code. Composer implements approved fixes. Grok is Warren-only on the release track.

1. Parse `<ID>` or release ID.
2. Confirm git HEAD, engine version, valuation date, and that proof is against full Output when Output is in play.
3. Run:

```text
python tools/validators/run_workflow_gate.py --release-proof <ID>
```

4. If `validate_release_closed_issues.py` exists, run it on the delivery candidate Output.
5. Classify golden mismatches A / B / C before changing production code. Source/Output agreement alone is not Class A.
6. Clean-checkout + full Output rebuild is required for this command.
7. Local package creation is not delivery. Verify the destination copy hash.
8. If recipient access cannot be verified: `PUBLISHED — RECIPIENT ACCESS NOT VERIFIED`.
9. Print the delivery receipt. Do not say released or ready for Eric with UNVERIFIED destination or missing UAT on a client-visible defect.
