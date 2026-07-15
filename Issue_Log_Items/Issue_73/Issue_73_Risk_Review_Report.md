# Issue #73 — Risk Review Report

**Issue:** #73 — Country code (`MISSCNTRY`) must be `0000` for all policies  
**Framework stage:** Risk Agent  
**Status:** **Go → Ready for Development** (pending explicit user approval)  
**Generated:** 2026-07-15  
**Model:** Cursor Grok 4.5 (locked)  
**Status note:** Risk analysis only — no production code changes.  
**Evidence:** `evidence/issue73_risk_impact_summary.csv` · `evidence/issue73_risk_misscntry_simulation.csv` · `scripts/risk_review_issue73_misscntry.py`

---

## Go / No-Go Recommendation

**GO** — Single rulebook default change; impact fully quantified; aligns with client rule, rate-key `ISSCNTRY=0000`, and existing data-governance **POL-025** (expects `MISSCNTRY=0000`).

| Factor | Assessment |
|--------|------------|
| Scope | `quikmstr.MISSCNTRY` only |
| Impact | **5,083 / 5,083** rows `USA` → `0000` (100%) |
| Collateral fields | **0** expected (`MISSUEST`, `MRESSTATE`, `MCOUNTRY` untouched) |
| Engine touch | **None required** — blank-source default from Sync Rulebook |
| #25 / #26 | Untouched |
| Governance | POL-025 already flags non-`0000` as advisory — fix clears fleet finding |

Development may proceed after user says **Approved for Development** and switches to **Composer 2.5**.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| `quikmstr.MISSCNTRY` | Rulebook default `USA` | Rulebook default **`0000`** | **Yes** (all rows) |
| `quikclnt.MCOUNTRY` | Address/country path | Unchanged | **No** |
| Rate `ISSCNTRY` | Already `0000` | Unchanged | **No** |
| `MISSUEST` / `MRESSTATE` | Existing LP maps | Unchanged | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| MPOLICY padding (#25) | **No** |
| quikridr.MPREM / MMODPREM (#26) | **No** |
| MSTATUS / MNFOPT / MDIVOPT | **No** |
| MISSUEST / MRESSTATE | **No** |
| quikclnt.MCOUNTRY | **No** |
| Rates / QuikPlSt / ISSCNTRY emit | **No** |
| Other Sync Rulebooks | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv` L18 | `,MISSCNTRY,USA,Default Country` — **only change site** |
| `app.py` / `QLA_Migration/app.py` ~6537–6546 | Applies `Default_Value` when Source_Field blank — no hardcode of `USA` |
| Schema list ~395 | Field present in quikmstr order |
| `data_governance/rules/chk_quikmstr.py` POL-025 | Already expects `MISSCNTRY=0000` |
| `qla_core/rate_*` ISSCNTRY defaults | Already `0000` — policy will match rates |

**Grep confirmation:** No production Python hardcodes `MISSCNTRY=USA`; only the rulebook default.

---

## 4. Population Analysis (simulated on current Output)

| Metric | Count |
|--------|------:|
| quikmstr rows | 5,083 |
| MISSCNTRY = USA (before) | 5,083 |
| MISSCNTRY = 0000 (before) | 0 |
| **Would change to 0000** | **5,083** |
| Rows unchanged | 0 |

### Breakdown

| Dimension | rows | would_change |
|-----------|-----:|-------------:|
| All policies (constant default) | 5,083 | 5,083 |

Uniform transition: every row `USA` → `0000`. No plan/status carve-outs.

---

## 5. Fallback Recommendation

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| **A. Rulebook default `0000` (recommended)** | 5,083 | Matches client + POL-025 + rate keys |
| B. Post-map force in `app.py` | 5,083 | Reject — unnecessary if rulebook drives the field |
| C. Keep `USA` | 0 | Reject — fails client + POL-025 |
| D. Map from LifePRO country | unknown | Reject — no LP column in use; client wants constant `0000` |

**Recommended:** Option A. No fallback needed.

---

## 6. Trace Policies

| Policy | MISSCNTRY before | After | MISSUEST (must stay) | Pass? |
|--------|------------------|-------|----------------------|-------|
| 010143726C | USA | **0000** | CA | Yes |
| 010148272C | USA | **0000** | MO | Yes |
| 010148856C | USA | **0000** | MO | Yes |
| 010149295C | USA | **0000** | NE | Yes |
| 010157076C | USA | **0000** | NE | Yes |

---

## 7. Top Changes

Not numeric. Entire fleet is the same one-field transition (`USA` → `0000`). Sample of 20 policies in `evidence/issue73_risk_misscntry_simulation.csv`.

---

## 8. Material Calculation Impact

| Area | Impact |
|------|--------|
| Premium / CV / NFO | None |
| Rate lookup alignment | **Positive** — policy Issue Country matches rate `ISSCNTRY=0000` |
| Address / tax country | None (`MCOUNTRY` out of scope) |
| Intentional vs drift | Intentional client correction of wrong default |

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserved** — out of scope |
| Issue #26 MPREM / MMODPREM | **Preserved** — out of scope |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] Fleet: count(`MISSCNTRY` ≠ `0000`) = **0**
- [ ] Trace policies above all show `0000`
- [ ] Untouched: `MISSUEST`, `MRESSTATE` unchanged vs pre-fix baseline for sample set
- [ ] Untouched: `quikclnt.MCOUNTRY` distribution unchanged
- [ ] Row counts: `quikmstr` row count unchanged (5,083)
- [ ] Schema / field order unchanged
- [ ] No accidental `app.py` edits unless Dev found a hardcode (none expected)
- [ ] Publish `Test_Validation/quikmstr.csv` on PASS

---

## 11. Recommended Development Agent Task

1. Edit **only** `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv`:  
   `MISSCNTRY` Default_Value `USA` → `0000`; note → `Default Issue Country ALL (0000) — Issue #73`.
2. Do **not** change `app.py` unless a hidden override is found (Risk found none).
3. Do **not** touch `quikclnt` rulebook / `MCOUNTRY`, `MISSUEST`, rates, #25/#26 paths.
4. Re-run conversion (or regenerating quikmstr path) so Output reflects the default.
5. Version bump: **not required** for rulebook-only change. If `app.py` must be touched, bump both root and `QLA_Migration/app.py`.
6. Add `Issue_Log_Items/Issue_73/scripts/validate_issue73_misscntry.py` — FAIL if any `MISSCNTRY` ≠ `0000`.
7. On validator PASS → copy modified `quikmstr.csv` to `QLA_Migration/Output/Test_Validation/`.

---

## Appendix

- Planning: `Issue_73_Planning_Report.md`
- Scope: `Issue_73_Scope_Decisions.md`
- Dependency Gate: `Issue_73_Dependency_Gate.md` (PASS)
- Simulation script: `scripts/risk_review_issue73_misscntry.py`
- Governance: `data_governance/rules/chk_quikmstr.py` POL-025
