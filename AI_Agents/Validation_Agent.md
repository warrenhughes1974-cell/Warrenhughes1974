# Validation Agent

**Stage:** 6 of 8  
**Code changes:** **Prohibited** (validation scripts may be run, not production logic)

---

## Purpose

Prove the Development change **meets acceptance criteria**: trace policies, field alignment, fallback behavior, and row integrity. Validation is issue-specific proof — not the full fleet regression (that is Regression Agent).

---

## Inputs

| Input | Source |
|-------|--------|
| Implementation notes | `Issue_<ID>_Implementation_Notes.md` |
| Validation script | `QLA_Migration/_validate_issue<id>_*.py` |
| Risk testing checklist | Risk report §10 |
| Output directory | `QLA_Migration/Output/` |
| Before snapshot | `Output/_issue<id>_before/` if captured |

---

## Required Research / Execution

1. Run issue validation script with any required flags (`--before-dir`, etc.)
2. Verify **trace policies** from client report
3. Verify **edge cases** from Risk report
4. Confirm **untouched fields** listed in Risk report (spot-check or script)
5. Confirm **row counts** for directly affected table(s)
6. Document PASS/FAIL with evidence (counts, tables, command output)

---

## Required Deliverables

Use `AI_Agents/Templates/Validation_Report_Template.md`.

Save as: `Issue_Log_Items/Issue_<ID>/Issue_<ID>_Validation_Report.md`

Include:

- Command(s) run
- Trace policy results table
- Field alignment summary
- Row counts
- PASS / FAIL verdict
- Failures → return to Development Agent with specific fixes

---

## Stop Conditions

- **FAIL:** Return to Development; do not run Regression until Validation passes
- **PASS:** Advance to Regression Agent

---

## Gate Criteria (G5 — Validation Pass)

- [ ] All trace policies pass (or documented waivers)
- [ ] Validation script exits 0
- [ ] Untouched fields confirmed for issue scope
- [ ] Validation report published
- [ ] Status: **Ready for Regression** (or return to Development)

---

## Example Cursor Prompt

```
Validation Agent — Issue [ID]

Read AI_Agents/Validation_Agent.md and Templates/Validation_Report_Template.md.

Run QLA_Migration/_validate_issue<id>_*.py against Output/.
Use before snapshot if available.

Do not modify production code unless validation script has a bug.

Publish Issue_<ID>_Validation_Report.md with PASS/FAIL.
```

---

## Examples

| Issue | Key validation checks |
|-------|----------------------|
| **#26** | MPREM 13.20/10.96/9.12; fallback rows; MMODPREM unchanged |
| **#25** | MPOLICY width = 10 everywhere; Issue #25 samples |
| **#21M** | N/A — not developed |
