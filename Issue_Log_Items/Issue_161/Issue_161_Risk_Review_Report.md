# Issue #161 — Risk Review Report

**Issue:** #161 — POA Information Missing (`quikclid.MRELATION` wrong code: `PW` vs `POFA`)
**Framework stage:** Risk Agent
**Status:** Ready for Development
**Fallback simulated:** N/A — no fallback needed, single deterministic value-translation edit
**Generated:** 2026-09-08
**Agent/script:** Manual review (Cursor, Planning/Risk session 2026-09-08)

**Status note:** Risk analysis only — no production code changes made in this stage.

---

## Go / No-Go Recommendation

**GO** — This is a single-row value-translation correction (`PW → POFA` instead of `PW → PW`) with a fully confirmed root cause, no schema change, no new table, and a blast radius limited to a small, distinct fleet-wide subset (412 of ~32,285 `quikclid` rows, i.e. ~1.3%).

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| `Master_Value_Translation.csv` row (LifePRO `PW`) | `PW,PW` | `PW,POFA` | **Yes** |
| `policy_code_authorities.csv` row (`MRELATION`/`PW`) | `MRELATION,PW,PW relationship` | `MRELATION,POFA,Power of Attorney relationship` | **Yes** |
| `quikclid.MCLIENTID` / `MPOLICY` / `MPHASE` for PW-sourced rows | unchanged | unchanged | No |
| Every other `MRELATION` code (INSD, OWNR, PAYR, ASGN, BENP, BENC, BANK, CUST, GRUP, GUAR, JOIN, MAIL, SERV, TRST, WAIT, O1, P1) | unchanged | unchanged | No |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| quikmstr.MMODPREM | PPOLC.MODE_PREMIUM | **No** |
| quikridr.MPREM | ANN_PREM_PER_UNIT + fallback (#26) | **No** |
| quikbenf (beneficiary table) | B1/B2/P/C filter | **No** — PW/POFA remains excluded by design |
| MPOLICY key padding | format_qladmin_mpolicy (#25) | **No** |
| quikridr.MUWCLASS (#159) | PPBEN UNDERWRITING_CLASS | **No** — unrelated table |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `QLA_Migration/Mapping/Master_Value_Translation.csv` line 49 | Single row to edit: `PW,PW` → `PW,POFA` |
| `data_governance/config/policy_code_authorities.csv` line 58 | Single row to edit: label/target code update |
| `QLA_Migration/Configs/Sync_Rulebook_quikclid.csv` | Unchanged — `RELATE_CODE → MRELATION` direct mapping stays as-is; only the translated value changes downstream |
| `app.py` (root + `QLA_Migration/`) | No code logic change expected — translation is data-file-driven; only version bump needed per `AGENTS.md` |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| Total `quikclid` rows analyzed (live build, 2026-09-02) | 32,285 |
| Rows that would change (`MRELATION`: `PW`→`POFA`) | 412 |
| Rows unchanged | 31,873 |
| Blank / zero source rows affected | 0 — all 412 PW rows are fully populated (client name, address, etc. via `quikclnt`) |

### Breakdown

| Dimension | rows | would_change |
|-----------|-----:|-------------:|
| `MRELATION = PW` (all policies, fleet-wide) | 412 | 412 |
| `MRELATION = PW` on the 3 client-cited example policies | 3 | 3 |
| All other `MRELATION` codes combined | 31,873 | 0 |

---

## 5. Fallback Recommendation (if applicable)

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| Direct value-translation edit (`PW,PW` → `PW,POFA`) | 412 | **recommended** — deterministic, no conditional logic, matches confirmed live QLAdmin dropdown |
| Leave `PW` as-is, add new `quikmemo`/policy-note workaround | 0 (no dbf value change) | reject — does not fix the actual field the client is looking at (Other Information panel), adds an unrequested table dependency |

**Recommended fallback:** None needed — the direct value-translation edit is unconditional and fully deterministic.

---

## 6. Trace Policies

| Policy | Before (`MRELATION`) | Proposed | Pass? |
|--------|-------:|---------:|-------|
| 9010442216C | PW | POFA | Pending Development + Validation |
| 9010451650C | PW | POFA | Pending Development + Validation |
| 9011045619C | PW | POFA | Pending Development + Validation |

---

## 7. Top Largest Changes

N/A — this is a categorical code relabel, not a numeric/dollar change. No "largest changes" ranking applies; all 412 affected rows undergo the identical `PW→POFA` substitution.

---

## 8. Material Calculation Impact

None. `MRELATION` is a relationship-role label, not a calculation input. No reserve, premium, or valuation figure is affected by this fix — this is purely a display/relationship-visibility correction in the QLAdmin UI.

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | Preserved — no key-format logic touched |
| Issue #26 MPREM / MMODPREM | Preserved — unrelated table/field |
| Issue #30 RNA crosswalk keying (`IDENTIFYING_ALPHA`) | Preserved — only the `MRELATION` translation value for `PW` changes; `NAME_ID`/`IDENTIFYING_ALPHA` mapping logic untouched |
| Issue #159 (`quikridr.MUWCLASS`) | Preserved — unrelated table, no overlap |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] Trace policies: 9010442216C, 9010451650C, 9011045619C — confirm `MRELATION=POFA` in re-emitted `quikclid.csv`
- [ ] Untouched fields: all other `MRELATION` codes (INSD, OWNR, PAYR, BENP, BENC, ASGN, BANK, SERV, GUAR, TRST, WAIT, MAIL, GRUP, CUST, JOIN, O1, P1) — row-for-row unchanged
- [ ] Row counts stable: `quikclid.csv` total row count unchanged (412 rows relabeled, 0 added/removed); `quikclnt.csv`, `quikbenf.csv`, `quikmstr.csv` unchanged
- [ ] Edge cases: confirm 0 residual `MRELATION=PW` rows in re-emitted Output; confirm `POFA` count == source `RELATE_CODE=PW` count (412)
- [ ] Live UI confirmation: DBF Append re-run, then visually confirm QLAdmin Names/Other-Information panel shows `POFA - Power of Attorney` for at least one trace policy (screenshot)

---

## 11. Recommended Development Agent Task

1. Edit `QLA_Migration/Mapping/Master_Value_Translation.csv` row 49: `PW,PW` → `PW,POFA`
2. Edit `data_governance/config/policy_code_authorities.csv` row 58: `MRELATION,PW,PW relationship` → `MRELATION,POFA,Power of Attorney relationship`
3. Do NOT change: any other row in either file; `Sync_Rulebook_quikclid.csv`; `quikbenf` source filter; any other table/rulebook
4. Version bump: next available `app.py` version (root + `QLA_Migration/app.py` — both copies per `AGENTS.md`)
5. Add fail-closed validator: `tools/validators/validate_issue161_poa_relation_code.py`

---

## Appendix

- Diagnostic script: live-build `quikclid.dbf` scan via `dbfread` (ad hoc, 2026-09-08 session) — no permanent script yet; will be formalized as the Development-stage validator
- Simulation script: N/A — deterministic single-value substitution, no simulation needed beyond the population analysis above
