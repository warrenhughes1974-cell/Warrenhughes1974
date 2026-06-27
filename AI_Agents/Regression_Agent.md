# Regression Agent

**Stage:** 7 of 8  
**Code changes:** **Prohibited**

---

## Purpose

Ensure the issue fix did **not break unrelated conversion behavior**: other tables, fields, row counts, schema integrity, and **prior issue fixes** (#25 MPOLICY, #26 MPREM). Validation proves the fix works; Regression proves nothing else broke.

---

## Inputs

| Input | Source |
|-------|--------|
| Validation report | PASS required |
| Before snapshot | Pre-fix `QLA_Migration/Output/_issue*_before/` or git baseline |
| After output | Post-fix batch output |
| Full batch log | `_full_batch_test_log.txt` if available |
| `validate_output.py` | If project standard checks exist |

---

## Required Research / Execution

1. **Row count comparison** — quikmstr, quikridr, quikprmh, quikplan, quikclid, quikclnt (+ issue-specific tables)
2. **Non-target field diff** — affected table(s): all columns except intentional change
3. **Prior fix spot-checks:**
   - Issue #25: MPOLICY 10-char width on sample policies
   - Issue #26: MPREM = ANN_PPU where populated; MMODPREM stable
4. **Schema manifest** — field order/types unchanged (AGENTS.md)
5. **MRIDRID / crosswalk** — no new blank keys introduced (if applicable)
6. Optional: run `_run_full_batch_test.py` if batch not already run post-fix

---

## Required Deliverables

Use `AI_Agents/Templates/Regression_Report_Template.md`.

Save as: `Issue_Log_Items/Issue_<ID>/Issue_<ID>_Regression_Report.md`

Include:

- Row count table (before/after)
- Fields confirmed unchanged
- Prior issue fix regression check results
- Fleet impact summary (if broad table)
- PASS / FAIL verdict

---

## Stop Conditions

- **FAIL:** Return to Development with regression failure details
- **PASS:** Advance to Closure Agent; status **Ready for Client UAT** (or Closed if client UAT waived)

---

## Gate Criteria (G6 — Regression Pass)

- [ ] Row counts stable (except intentional target changes)
- [ ] Unrelated fields unchanged
- [ ] #25 / #26 preservation verified
- [ ] Regression report published
- [ ] No schema integrity violations

---

## Example Cursor Prompt

```
Regression Agent — Issue [ID]

Read AI_Agents/Regression_Agent.md and Templates/Regression_Report_Template.md.

Compare Output/ to _issue<id>_before/ or documented baseline.

Verify Issue #25 MPOLICY padding and Issue #26 MPREM mapping still pass their validators.

Do not modify code.

Publish Issue_<ID>_Regression_Report.md.
```

---

## Examples

| Issue | Regression focus |
|-------|------------------|
| **#26** | quikprmh identical; MVPU/MUNIT; 7002 quikridr rows; only MPREM changed |
| **#25** | No row count change; non-MPOLICY fields identical |
| **#21M** | N/A |
