---
name: check-in
description: Verify or perform scoped check-in of a validated issue candidate to origin/main. Use when the user types /check-in or asks to push, sync, or check in an issue.
disable-model-invocation: true
---

# /check-in

Read `AI_Agents/Verified_Development_Delivery_Workflow.md`.

Standing authorization is a normal push to `origin/main` only. Not force-push, merge, or deploy.

1. Parse the issue ID.
2. Confirm the local candidate SHA and that required files exist in that commit tree.
3. If not yet pushed and destination is `origin/main`, perform a normal push of the scoped commit.
4. Query the live remote, not cached tracking:

```text
git ls-remote --exit-code origin refs/heads/main
```

5. Run:

```text
python tools/validators/run_workflow_gate.py --check-in <ID>
```

6. If the remote SHA does not contain the candidate (or a verified successor that still has the fix), report `NOT VERIFIED AS CHECKED IN`.
7. `PUSHED TO FEATURE BRANCH` is not `INCLUDED IN DELIVERY BRANCH`.
8. Never say checked in, synced, all set, or ready for Eric from a local commit or a failed push.
