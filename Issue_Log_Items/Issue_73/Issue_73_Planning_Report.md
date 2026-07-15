# Issue #73 — Planning Report

**Issue:** #73 — Country code (`MISSCNTRY`) must be `0000` for all policies  
**Framework stage:** Planning Agent  
**Status:** Ready for Dependency Gate  
**Generated:** 2026-07-15  
**Model:** Cursor Grok 4.5 (locked)  
**Scope decisions:** `Issue_73_Scope_Decisions.md`  
**Intake:** `Issue_73_Intake_Summary.md`

---

## 1. Executive Finding

Client requires Issue Country = **`0000`** on every policy. Normalized target is `quikmstr.MISSCNTRY` (not a date field; not client mailing country).

Today the Sync Rulebook hard-defaults `MISSCNTRY` to **`USA`** (blank Source_Field + Default_Value). Current Output: **5083 / 5083 = USA**. Rate / plan segmentation already uses **`ISSCNTRY=0000`** (“ALL”), so policy `USA` is inconsistent with rate keys.

**Direction:** One-line rulebook default change `USA` → `0000`. No LifePRO extract column required. Expected blast: **all 5083** `quikmstr` rows, **one field only**. Ready for Dependency Gate / Risk.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/? | Role |
|--------------|--------------|:-----------:|------|
| *(none for MISSCNTRY)* | — | N/A | Field is rulebook **constant default**, not mapped from LifePRO |
| PPOLC | `PPOLC_PolicyMaster_Extract_*.csv` | Yes | Supplies other quikmstr fields; **not** used for MISSCNTRY today |

### Available source fields

| Field | Column / source | Populated % | Notes |
|-------|-----------------|------------:|-------|
| Issue country | *(no LifePRO column mapped)* | N/A | Rulebook Default_Value only |
| ISSUE_STATE | PPOLC → `MISSUEST` | (existing) | **Out of scope** — state, not country |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Semantics |
|-------|-------|------|--------|-----------|
| quikmstr | MISSCNTRY | C | 4 (typical) | Issue Country segmentation key; `0000` = ALL (other) |
| *(compare)* rate keys | ISSCNTRY | C | 4 | Already defaulted to `0000` in `qla_core` loaders |
| *(out of scope)* quikclnt | MCOUNTRY | — | — | Address/mailing country — do not change |

**Repo references (population paths only):**

| Location | Role |
|----------|------|
| `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv` | `,MISSCNTRY,USA,Default Country` — **change site** |
| `QLA_Migration/app.py` / root `app.py` ~6537–6546 | Applies `Default_Value` when Source_Field blank |
| Schema list ~395 | `MISSCNTRY` in quikmstr column order |
| `qla_core/rate_factor_loader.py`, `rate_dbf_schema.py` | Rate `ISSCNTRY` default `0000`; `DEFAULT_CNTRY_TXT = "ALL (OTHER)"` |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| *(constant)* | — | `quikmstr.MISSCNTRY` | Default **`0000`** (was `USA`) | **Yes** |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| MPOLICY padding | `format_qladmin_mpolicy` (#25) | **No** |
| quikridr.MPREM | ANN_PREM_PER_UNIT + fallback (#26) | **No** |
| MISSUEST | ISSUE_STATE | **No** |
| MRESSTATE | RES_STATE | **No** |
| quikclnt.MCOUNTRY | COUNTRY_CODE | **No** |
| Rate ISSCNTRY emit | config default `0000` | **No** (already correct) |
| All other quikmstr fields | existing | **No** |

---

## 5. Open Client Questions

1. **OBQ-73-1:** Confirm “country date = 0000” means Issue Country on Policy Display (`MISSCNTRY`), not client address country (`MCOUNTRY`).  
   - **Planning assumption (SD-73-1/4):** **Yes** — Issue Country only. Escalate only if UAT shows they meant mailing country.

2. **OBQ-73-2:** Any exception policies that must keep a real country code (e.g. non-US issue)?  
   - **Assumption (SD-73-2):** **No** — fleet-wide `0000` per client wording (“all policies”).

No hard client blocker if SD-73-* accepted.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Crosswalk + 10-char MPOLICY padding (#25) — unchanged |
| MISSCNTRY | Exactly four chars: `0000` (not blank, not `USA`, not padded spaces) |
| Dates / money | N/A |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` → `Master_Crosswalk.csv` → QLA  
2. Apply `format_qladmin_mpolicy()` for CHARACTER(10) keys  
3. This issue does not alter key handling

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| quikmstr rows (current Output) | 5,083 | `Output/quikmstr.csv` |
| Rows with MISSCNTRY=USA (before) | 5,083 | 100% |
| Rows with MISSCNTRY≠USA (before) | 0 | |
| Rows expected MISSCNTRY=0000 (after) | 5,083 | Fleet-wide |

---

## 10. Sample Trace (5 policies)

| Policy (QLA) | MISSCNTRY before | After (proposed) | MISSUEST (unchanged) |
|--------------|------------------|------------------|----------------------|
| 010143726C | USA | **0000** | CA |
| 010148272C | USA | **0000** | MO |
| 010148856C | USA | **0000** | MO |
| 010149295C | USA | **0000** | NE |
| 010157076C | USA | **0000** | NE |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Client meant `MCOUNTRY` not `MISSCNTRY` | Low–Med | SD-73-1; UAT Issue Country on Policy Display |
| Any QLAdmin process expects `USA` literal | Low | Rate keys already `0000`; `0000` is QLA “ALL” convention |
| Accidental touch of issue state / residence | Low | Single rulebook cell; validator checks only MISSCNTRY + regression on neighbors |
| Fleet-wide change (5083 rows) | Low (one field) | Risk Agent: confirm delta is MISSCNTRY-only |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | **N/A** (constant default; PPOLC present for batch context) |
| Field definitions confirmed | **Yes** — MISSCNTRY in schema; `0000` = ALL |
| Client scope clear | **Yes** — SD-73-* |
| Example policies / before-state | **Yes** — full fleet measurable |

---

## 13. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue 73.

Read AI_Agents/Risk_Agent.md and Issue_Log_Items/Issue_73/Issue_73_Planning_Report.md
(+ Issue_73_Scope_Decisions.md, Issue_73_Dependency_Gate.md).

Model: Cursor Grok 4.5. Do not code.

Quantify: 5083 quikmstr rows MISSCNTRY USA→0000; confirm zero collateral field changes;
go/no-go for Development (rulebook Default_Value only).
```

---

## 14. Recommended Development Task (Do Not Implement)

1. In `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv`, change `MISSCNTRY` Default_Value from `USA` to `0000`; update Transformation_Note to “Default Issue Country ALL (0000) — Issue #73”.
2. Re-run conversion (or issue-scoped emit) so `Output/quikmstr.csv` reflects the new default.
3. Version bump **only if** `app.py` must be touched (Planning expects **rulebook-only** → no bump unless Dev finds an override). If any engine hardcode of `USA` for MISSCNTRY exists, remove surgically and bump both `app.py` copies.
4. Add validator: `Issue_Log_Items/Issue_73/scripts/validate_issue73_misscntry.py` — assert count(`MISSCNTRY` ≠ `0000`) = 0; assert sample policies = `0000`; assert `MISSUEST` / `MCOUNTRY` unchanged vs baseline where practical.
5. On PASS, publish modified `quikmstr.csv` to `QLA_Migration/Output/Test_Validation/`.

---

## Appendix

- Related: rate `ISSCNTRY=0000` defaults; Issue #71 BAND standardization (similar “force ALL key” pattern)
- Rulebook: `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv`
- Intake: `Issue_73_Intake_Summary.md`
- Scope: `Issue_73_Scope_Decisions.md`
