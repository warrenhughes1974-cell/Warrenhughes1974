# Issue #51 — Tracking Sheet

| Field | Value |
|-------|-------|
| Issue ID | 51 |
| Title | Missing Interest Table (A60MIR / A96DAR) — Projected Values Crash Loop |
| Status | **Ready for Client UAT** |
| Gates | G0 ✓ · G1 ✓ · G2 ✓ · G3 ✓ · G4 ✓ · G5 ✓ · G6 ✓ · G7 ✓ (docs) |
| Engine | **v57.76** |
| Resolution | Added QuikAint interest-rate stubs for closed riders A60MIR and A96DAR so QLAdmin Projected Values no longer fails looking up a missing interest table. |
| Reporter | Client UAT |
| Owner | Warren (Conversion) |
| Example | 010348734C / 9010348734 / A60MIR status 56 |
| Root cause | A-prefix plans lacked QuikAint rows; QLAdmin Projected Values SEEK fails → endless error loop |
| Fix | Emit QuikAint stubs @ 0.0000 from PPBEN.FV_GUAR_RATE authority |
| Related | #32 (QuikUint — do not use), #21D, #21E, #28 |

## Deliverables

| Artifact | Path |
|----------|------|
| Intake | `Issue_51_Intake_Summary.md` |
| Planning | `Issue_51_Planning_Report.md` |
| Dependency Gate | `Issue_51_Dependency_Gate.md` |
| Risk Review | `Issue_51_Risk_Review_Report.md` |
| Research script | `scripts/research_issue51_quikaint_gap.py` |
| Evidence | `evidence/issue51_*.csv` + screenshot |
| Implementation | `Issue_51_Implementation_Notes.md` |
| Validation | `Issue_51_Validation_Report.md` — **PASS** |
| Regression | `Issue_51_Regression_Report.md` — **PASS** |
| Resolution | `Issue_51_Resolution_Summary.md` |

## Client UAT (next)

1. Load `QuikAint.csv` with rate package into QLAdmin.
2. Retest **Projected Values** on **010348734C** (A60MIR) — expect no endless loop.
3. Retest A96DAR sample (e.g. **010510671C**).
4. If loop persists after QuikAint confirmed loaded → escalate QuikAing/QuikAinf stubs per Risk fallback E.

## Git release

Commit/push **pending** user request. After approval: issue-scoped commit `Close Issue #51: … (v57.76)` + `git push`.
