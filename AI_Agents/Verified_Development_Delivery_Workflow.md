# Verified Development and Delivery Workflow

**Version:** 1.0.0  
**Locked:** 2026-09-08  
**Applies to:** every development project in this repository going forward  

Warren must never be told a fix is done, checked in, released, or available for testing unless the corresponding evidence exists.

A passing local test is not a commit.  
A local commit is not a push.  
A push is not inclusion in the delivery branch.  
A delivery-branch commit is not a rebuilt package.  
A rebuilt package is not proof the recipient can access it.

Report those facts separately. Use `NOT_RUN`, `BLOCKED`, or `UNVERIFIED` — never fill missing proof with `PASS`.

---

## 1. Operating goals

1. Take Warren out of routine flow.
2. Keep cost down (right model, no extra loops).
3. Do not ship mistakes.

Scripts run repetitive checks. Models interpret relevant failures. Do not send full customer datasets or verbose passing logs to models.

After two repair attempts at the same failure with no new evidence: stop and classify. Do not loop.

Keep handoffs compact: issue ID, spec version, paths, diff summary, gate results.

---

## 2. Model roles

| Role | Job | Locked model ID | Notes |
|------|-----|-----------------|-------|
| Research | Stages 0–4 | `claude-sonnet-5-thinking-high` | No production code. No invented actuarial/business decisions. |
| Implementation | Stage 5 + Composer testing + packaging | `composer-2.5-fast` | Surgical only. Cannot grant independent validation to its own work. |
| Independent audit | Stage 6 when Grok is required | `cursor-grok-4.6-high-fast` | Frozen candidate only. Must not edit. Returns VALIDATED / VALIDATION FAILED / INSUFFICIENT EVIDENCE. |
| Release orchestrator | Release proof, classify A/B/C, report | Luna (`gpt-5.6-luna-medium`) | Does not code. Must not hand release work to Grok. |
| Specialist | One unresolved hard problem | `claude-opus-5-thinking-high` | Warren approval only. |

**Do not use Auto or `inherit` for these roles.**

Preferred non-Fast Composer/Grok IDs are not in the current available list. Fast IDs above are the installed routing. If a requested model is missing, report it and use manual handoff. Do not silently substitute.

Verify requested vs actual model from runtime evidence when available. Do not trust a model’s self-description.

### Grok tier (cost control)

Grok is required only when the approved spec risk tier is one of:

`money` · `engine` · `status` · `rates` · `claims`

Routine mapping, configuration, documentation, and workflow/tooling use Composer plus the executable gates only.

### Effort

Medium research for narrow work. Higher effort for financial calculations, shared-engine changes, or hard reasoning. Do not enable maximum effort or premium speed by default.

---

## 3. Nine stages (names unchanged)

Do not rename Stage 6 or 7. Composer’s test loop is **Development self-test** inside Stage 5.

| Stage | Name | Owner |
|------:|------|--------|
| 0 | Discovery | Research (Sonnet) |
| 1 | Intake | Research |
| 2 | Planning | Research |
| 3 | Dependency Gate | Research |
| 4 | Risk | Research |
| 5 | Development | Composer (includes self-test) |
| 6 | Validation | Grok when tier requires it; otherwise gates |
| 7 | Regression | Composer + gates |
| 8 | Closure | Docs + gates |

### Auto-advance (standing authorization 2026-09-08)

| After | Do this | Unless |
|-------|---------|--------|
| Discovery complete | Continue Intake → Planning → Dependency Gate → Risk | Wrong-target risk or missing business/actuarial decision |
| Risk **GO**, no Closed-row conflict | Start Development | Risk NO-GO or CONDITIONAL GO timing not met |
| Local tests + regression PASS | Scoped local candidate commit | Required files missing from the commit |
| Candidate VALIDATED | Normal push to `origin/main` | Destination is not `origin/main`, or force-push / merge / deploy |

Skipping Discovery does not waive dependencies, risk, or evidence.

CONDITIONAL GO: record conditions and enforce their timing. A material spec change needs a new spec version. Standing Development approval applies to that issue + spec version only.

### Warren exception list (only stops)

- Risk **NO-GO**
- Class C (cannot establish the correct result)
- Proposed change would reverse a Closed guide row
- Force push, protected-branch merge, or deployment
- Client UAT confirmation on client-visible defects
- Opus / other specialist

Do not ask again for the same standing check-in to `origin/main`.

---

## 4. Stage requirements

### 0 Discovery

Confirm the business symptom, source, target table/UI, owning component, current behavior, and relevant Closed fixes.

Trace beyond CSVs when needed: source → conversion → DBF/DBT → load → QLAdmin → display / report / print.

Flag and stop only for wrong-target risk or a missing decision.

### 1–4 Intake → Risk

No production code. No executable test changes except read-only diagnostics.

Define scope, current vs expected behavior, authoritative sources and cut, allowed/prohibited files, acceptance criteria, smoke and regression requirements, representative and boundary cases, populations and tables, rollback, and downstream verification.

Freeze the specification and test expectations with a version/hash.

Missing required dependency: **BLOCKED**. Do not Risk.  
Risk **NO-GO**: stop. Do not start Development.

### 5 Development

Smallest approved fix plus its permanent tests. Prefer rulebook + small engine hook.

If `app.py` changes: bump `APP_VERSION` in both root `app.py` and `QLA_Migration/app.py`. Verify consistency; do not overwrite legitimate file differences.

Composer runs reproduction, correction, boundary, negative, and validator tests here (self-test). Do not invoke Grok on a candidate already known to fail.

### 6 Validation

Independent check of the frozen candidate after required deterministic checks.

Grok (when required) receives: approved spec, primary evidence, actual diff, candidate manifest, validator logic, smoke coverage, negative-test results, and run evidence.

Grok independently derives selected expected results and inspects population coverage. Targeted source inspection is allowed. Grok must not edit the candidate or approve only Composer’s narrative.

Any earlier review is **PROVISIONAL**.

### 7 Regression

Intended changes occur. Unrelated behavior is preserved. Compare by approved keys and fields. Do not normalize away padding, precision, duplicates, or field-width differences.

### 8 Closure

Blocked until applicable G7 items, mandatory smoke, verified check-in, delivery proof, and required client UAT (if client-visible) are satisfied.

Do not rename “ready for review” or “ready for check-in” to **Closed**.

---

## 5. Mandatory smoke

Every implemented fix or behavior change adds or extends a permanent smoke mapped to that issue and acceptance criterion. This includes conversion code, rulebooks, schema/precision, validators/golden corrections, packaging/append, UI/print, and workflow tooling.

Documentation-only fixes need a deterministic check of the corrected contract. They are not exempt.

Reusing a smoke file is fine. Claiming an unrelated existing smoke covers the fix is not.

Each smoke must:

1. Assert the corrected behavior, not file existence.
2. Be registered in `SMOKE_JOBS` when that registry exists, **and** in `tools/workflow/coverage_map.json`.
3. Run through `--smoke-only` when that entrypoint exists, or through `run_workflow_gate.py --smoke`.
4. Have a stable ID and issue mapping.
5. Produce machine-readable results and a meaningful failure.
6. Exit nonzero on failure.
7. Stay in future applicable regression/release runs.

Bug fixes: the issue test rejects the pre-fix case; the fixed candidate passes; reintroducing the defect in an isolated fixture is detected.  
New behavior: removing or corrupting it fails the test.

Never mutate authoritative source, published Output, or live DBFs for those demonstrations.

Fail closed on missing files/columns, missing evidence, wrong source cut, zero matches when a population is expected, missing/duplicate required records, swallowed exceptions, and a smoke that was registered but never executed.

`PASS`, `FAIL`, `NOT_RUN`, `BLOCKED`, and approved `NOT_APPLICABLE` stay distinct.

A later dataset may lack an old issue’s population. Keep that issue’s fixture smoke running and report dataset applicability. For the **current** data issue, absence of affected records is **GAP** and blocks `IN_DATA` closure. Do not use `NOT_APPLICABLE` to evade that.

Expected values come from approved rules and source evidence. Do not calculate expected results with the same business function under test.

Do not remove tests, weaken assertions, widen tolerances, change goldens, or add exclusions just to get PASS. That needs a documented reason, spec change if material, and independent review.

Historical Closed issues without smoke: inventory as backlog. Do not silently Close them and do not block new work on those gaps.

Protected baseline (must remain mapped): **#25** MPOLICY padding, **#26** MPREM, **#143** BF RPU MUNIT. Inspect #143’s recorded requirements; do not guess assertions. If the #143 script is missing on a branch, report **GAP** — do not invent checks.

---

## 6. Candidate commit (every issue)

“Approved for Development” / auto-start after Risk GO authorizes a **scoped local** commit after focused tests pass. It does not authorize force-push, merge, or deploy.

Before commit:

- Inspect the actual diff.
- Enumerate required implementation, fixtures, validators, smokes, registration, and guide files.
- Stage explicit issue-owned paths only. No `git add .` / `git add -A`.
- Exclude secrets, unauthorized customer data, unrelated work, transients.

Record candidate SHA and engine version. Verify those files exist **in that commit’s tree**.

Issue-level proof:

- Issue tests
- Mapped smokes
- No undeclared working-tree inputs
- Required files present in the commit

Full clean-checkout + full Output rebuild is **release-candidate only** (see §10).

---

## 7. Frozen evidence

Create a candidate manifest (`Issue_Log_Items/Issue_<ID>/evidence/candidate_manifest.json`) with:

- issue and spec identity
- candidate commit and engine version
- source-cut identity and hashes
- rulebook/config identities
- retained quikplan/rate provenance when applicable
- Output hashes and row counts when Output was rebuilt
- validator and smoke identities
- expected vs executed smoke IDs
- commands, exit codes, timestamps
- gate results

A PASS belongs to that candidate and data fingerprint. Changing code, tests, expectations, relevant config, inputs, or Output invalidates affected proof.

Store run results separately from immutable build inputs. Do not amend a commit just to insert its own SHA.

If a later docs-only closure commit is needed, keep the tested build SHA explicit.

---

## 8. Verified check-in

Standing authorization: normal push of a validated candidate to **`origin/main`**.

Before push: verify destination and commit scope.

After push:

1. Record the command result.
2. Query the live remote: `git ls-remote --exit-code origin refs/heads/main`
3. Record observed remote SHA and verification time.
4. Confirm the candidate (or its verified successor) is present.
5. Confirm the fix and smoke were not omitted or reverted.

A zero exit code is not enough — the SHA must match.

If `main` has advanced: establish ancestry **and** inspect the actual delivery candidate. Ancestry alone does not prove the fix was not reverted.

`PUSHED TO FEATURE BRANCH` is not `INCLUDED IN DELIVERY BRANCH`.

If merge/squash/cherry-pick/rebase changes the delivery candidate, record the new SHA and re-run required proof.

On failed push, missing credentials, offline remote, or unverifiable state:

`NOT VERIFIED AS CHECKED IN — <reason>`

Never say “checked in,” “synced,” “all set,” or “ready for Eric” from a local commit or an attempted push.

---

## 9. Output, packaging, release

**QLA Output/** holds table CSVs and optional `rates/`.  
`Output/Test_Validation/` is the explicit affected-table-copy exception.  
Reports, logs, manifests, and narratives stay outside Output/.

Use isolated candidate output first. Do not overwrite a validated published batch to test a new candidate.

Older policy cuts keep the newest approved quikplan and rates. Record that provenance.

Official Desktop DBF Append only. Append onto approved master templates. Never recreate or wipe DBFs. Test against safe copies, not live masters.

After every full batch, Append Tool input and output must match that batch (including retained plan/rate exceptions).

### Release orchestrator

Luna orchestrates, classifies, runs gates, reports. Luna does not code. Composer implements approved changes. Grok is Warren-only on the **release** track. The automatic Grok review above is the **issue** lane only.

### Failure classes (before changing production code)

| Class | Meaning | Action |
|-------|---------|--------|
| A | Approved rules + correct source-cut prove the validator/golden is stale | Fix the validator; keep audit history; smoke detects recurrence |
| B | Evidence proves an engine defect | Return to Development |
| C | Conflict or cannot establish the correct result | Stop. Tell Warren. |

Source/Output agreement alone is not enough for Class A.

### Release-candidate extra proof

Required before “released” / “ready for Eric”:

- Isolated clean checkout at the delivery SHA
- Recreate dependencies from recorded config
- Authorized hash-identified external data only
- Issue tests, fixture smokes, full Output rebuild, issue validator on `QLA_Migration/Output/`, Closed-row validators, complete `--smoke-only`
- Package identity/hash; destination copy verified

### Ready for client testing

The artifact or environment must be reachable on the intended authorized path.

If not: `PUBLISHED — RECIPIENT ACCESS NOT VERIFIED`

Display, print, load, or reindex defects need evidence at that layer. CSV checks alone cannot close a printed-notice defect.

Client UAT is required to **Close** client-visible defects. Internal workflow/tooling issues do not wait on Eric UAT.

---

## 10. Closure

Existing G-D and G0–G7 remain in force where those artifacts exist.

Additionally:

- Permanent issue-linked smoke exists, is registered, and executed
- Required tests PASS on the frozen candidate
- Full-Output issue proof and `IN_DATA` when the issue owns Output
- Affected tables copied to `Output/Test_Validation/` when Output was rebuilt
- `Completed_Issues_Release_Validation_Guide.md` updated when that guide exists
- Closed-fix coverage preserved
- Independent validation completed when the Grok tier applies
- Commit / push / integration proof
- Package / delivery proof when claiming released
- Client UAT when client-visible
- No unresolved blockers or stale evidence

Only then:

```text
MM/DD/YYYY Resolution: <what we fixed and verified>. Examples: <policy 1>; <policy 2>; <policy 3>.
```

Use real verified examples and the actual verification date.

---

## 11. Commands and gate runner

Slash skills (human-triggered): `/issue`, `/smoke`, `/check-in`, `/release-proof`

Executable (source of truth):

```text
python tools/validators/run_workflow_gate.py --issue <ID>
python tools/validators/run_workflow_gate.py --smoke <ID|all>
python tools/validators/run_workflow_gate.py --check-in <ID>
python tools/validators/run_workflow_gate.py --release-proof <ID|release-ID>
```

Nonzero exit when a required gate is failed, missing, stale, or unverifiable.

Coverage map: `tools/workflow/coverage_map.json` (versioned).  
When `tools/validators/validate_release_closed_issues.py` exists, its `SMOKE_JOBS` is merged and must include every mapped required smoke.

Protected baseline membership is checked even if a registry row is deleted.

---

## 12. Delivery receipt

Issue deliverables: `Issue_Log_Items/Issue_<ID>/`

At every stop, show current stage, blocker, and exact next action.

At every completion / check-in / release report:

```text
ISSUE:
CURRENT STAGE:
OVERALL STATUS:

IMPLEMENTATION:
SPECIFICATION VERSION:
SMOKE IDS:
SMOKE RESULTS:
NEGATIVE-TEST PROOF:
REGRESSION:
FULL OUTPUT VALIDATION:
ACCOUNTABILITY:
INDEPENDENT VALIDATION:

LOCAL COMMIT:
ENGINE VERSION:
REQUIRED FILES PRESENT IN COMMIT:
CLEAN-CHECKOUT PROOF:

REMOTE:
BRANCH:
REMOTE SHA:
REMOTE VERIFICATION TIME:
INTEGRATION/MERGE STATUS:

OUTPUT/BATCH ID:
PACKAGE ID/HASH:
DELIVERY LOCATION:
DESTINATION VERIFIED:
CLIENT UAT:

REMAINING BLOCKERS:
NEXT ACTION:
```

Plus one plain-English sentence, for example:

“The fix and smoke are committed locally, but the push has not succeeded. It is not available to Eric yet.”

---

## Final operating rule

No permanent smoke coverage: not complete.  
No verified commit: not committed.  
No live remote proof: not verified as checked in.  
No matching rebuilt artifact: not released.  
No verified testing destination: not ready for the recipient.  
No required UAT: not Closed (client-visible only).
