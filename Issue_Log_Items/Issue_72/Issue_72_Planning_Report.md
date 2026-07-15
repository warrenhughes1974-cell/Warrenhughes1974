# Issue #72 — Planning Report

**Issue:** #72 — NFO option must match ETI/RPU status (`MSTATUS` 44→`MNFOPT` 2; 45→3)  
**Framework stage:** Planning Agent  
**Status:** Ready for Dependency Gate  
**Generated:** 2026-07-15  
**Model:** Cursor Grok 4.5 (locked)  
**Scope decisions:** `Issue_72_Scope_Decisions.md`  
**Intake:** `Issue_72_Intake_Summary.md`

---

## 1. Executive Finding

Robert requires **exercised** ETI/RPU status and NFO to match on Policy Display: status **44 → NFO 2**, status **45 → NFO 3**.  

Today `MNFOPT` is the LifePRO **election** from PPBENTYP (`NON_FORFEITURE` / `BF_NON_FORFEITURE`), translated by Issue **#57**. That is correct for active/other statuses, but wrong when the policy is already **on** ETI/RPU via `PAID_UP_TYPE` (e.g. `010407670C`: PUT=`RU` → status 45, election LP `4` → `MNFOPT=2`).  

**Direction:** Keep #57 for non-44/45. Add a **narrow post-map force** on final `quikmstr.MSTATUS` only. Expected touch: **~277** of **400** ETI/RPU masters (98 @44, 179 @45). No source re-extract required.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/? | Role |
|--------------|--------------|:-----------:|------|
| PPBENTYP | `PPBENTYP_BenefitType_Extract_*.csv` | Yes | Election `NON_FORFEITURE` / `BF_NON_FORFEITURE` (#57 path) |
| PPOLC | `PPOLC_PolicyMaster_Extract_*.csv` | Yes | `PAID_UP_TYPE`, `CONTRACT_CODE`/`REASON` → `MSTATUS` |
| PPBEN | phase cache (#49) | Yes | May change final `MSTATUS` before NFO force |

NFO force itself is **not** source-driven — it is derived from **final QLAdmin `MSTATUS`**.

### Available source fields (trace)

| Field | Source | Notes |
|-------|--------|-------|
| NON_FORFEITURE | PPBENTYP BA row | LP 0–9; #57 maps 3/4/5 → 1/2/3 |
| PAID_UP_TYPE | PPOLC | `ET`→44, `RU`→45 via `PUT_*` + `ST_` |
| CONTRACT_CODE / REASON | PPOLC | #13 / #59 precedence |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Domain | Source |
|-------|-------|------|--------|--------|
| quikmstr | MSTATUS | numeric status | 44=ETI, 45=RPU | Schema + `ST_` / `PUT_` translations |
| quikmstr | MNFOPT | NFO option | 0=None, 1=APL, 2=ETI, 3=RPU | Schema + `NF_` translations |

**Repo references (population paths only):**

| Location | Role |
|----------|------|
| `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv` | `NFO_OPT→MNFOPT` default `0` |
| `app.py` / `QLA_Migration/app.py` ~6621–6633 | Enrich `MNFOPT` from `lifepro_extra['NON_FORFEITURE']` when 0 |
| Same ~6785–6787 | `NF_` / `ST_` / `PUT_` via `Master_Value_Translation.csv` |
| Same ~6570–6599 | MSTATUS interceptor (#13 / #59) |
| Same ~6789–6817 | #49 active-phase MSTATUS override (**after** `ST_`) |
| `Master_Value_Translation.csv` | `NF_3/4/5→1/2/3`; `PUT_ET→44`, `PUT_RU→45` |

**Schema field order (important):** `MSTATUS` appears **before** `MNFOPT` on quikmstr. After the per-field loop, `row_data['MSTATUS']` is final (#49 applied). Safest Dev hook: **post-map on completed `row_data`** immediately before bank-draft gate / `output.append` for quikmstr.

---

## 4. Required Source-to-Target Field Mapping

| Driver | Condition | Target | Transformation | Change? |
|--------|-----------|--------|----------------|---------|
| Final `MSTATUS` | `= 44` | `MNFOPT` | Force **`2`** | **Yes** |
| Final `MSTATUS` | `= 45` | `MNFOPT` | Force **`3`** | **Yes** |
| PPBENTYP NFO + #57 | `MSTATUS` ∉ {44,45} | `MNFOPT` | Unchanged election path | **No** |
| PPOLC PUT / contract | — | `MSTATUS` | Unchanged | **No** |

### Fields that must remain unchanged

| Target | Touch? |
|--------|--------|
| MPOLICY padding (#25) | **No** |
| quikridr.MPREM (#26) | **No** |
| MSTATUS / MPHSTAT | **No** |
| MDIVOPT | **No** |
| `NF_3/4/5` translation table | **No** (keep for non-44/45) |
| Rulebook (do not re-add PUT→MNFOPT fleet-wide) | **No** |
| Rates / MCV / RRULE | **No** |

---

## 5. Open Client Questions

1. **OBQ-72-1:** Confirm Robert’s rule applies even when LifePRO election differs from exercised status (e.g. elected ETI, on RPU).  
   - **Planning assumption (SD-72-1/2/3):** **Yes** — status wins for 44/45. Treat as locked unless client objects.

2. **OBQ-72-2:** Any need to sync `quikridr.MPHSTAT` 44/45 to a rider-level NFO field?  
   - **Assumption:** **No** — Robert cited master NFO opt vs status; QLAdmin Options NFO is `quikmstr.MNFOPT`.

No hard client blocker for Dependency Gate if SD-72-* accepted.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| MNFOPT value | Single digit string `2` or `3` (existing numeric shield) |
| When to force | Final MSTATUS exactly `44` or `45` (after normalize) |
| When not to force | All other statuses — leave #57 election result |
| Logging | Optional count: “Issue #72: forced MNFOPT from ETI/RPU status on N polic(ies)” |

---

## 7. Policy Key Handling

- MPOLICY: unchanged (#25)  
- Crosswalk: unchanged  
- Match key for override: normalized `row_data['MPOLICY']` + final `MSTATUS` only  

---

## 8. Estimated Record Counts (current Output)

| Population | Count | Action |
|------------|------:|--------|
| quikmstr rows | 5,083 | Scan |
| MSTATUS=44 | 206 | Force MNFOPT=2 where ≠2 → **98** changes |
| MSTATUS=45 | 194 | Force MNFOPT=3 where ≠3 → **179** changes |
| **Total MNFOPT deltas** | **277** | Expected |
| Already correct (44+2 / 45+3) | 123 | No-op |
| Non-44/45 masters | 4,683 | **Zero** MNFOPT change from #72 |

---

## 9. Sample Trace

| Policy | MSTATUS | MNFOPT now | After #72 | Notes |
|--------|---------|------------|-----------|-------|
| **010407670C** | 45 | 2 | **3** | PUT=RU; LP NFO election 4 (ETI) — Robert sample |
| 010165095C | 45 | 2 | **3** | Mismatch peer |
| 010379477C | 45 | 1 | **3** | Mismatch peer |
| 010403916C | 45 | 3 | 3 | Already correct |
| 010374099C | 44 | 1 | **2** | Mismatch peer |
| 010149295C | 44 | 2 | 2 | Already correct |
| 010367131C | 22 | 2 | **2 (unchanged)** | #57 Eric ETI election; not 44/45 |

---

## 10. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Override before #49 changes MSTATUS | High | Hook **after** final status on completed row |
| Re-adding fleet PUT→MNFOPT undoes #57 | High | Do **not** restore rulebook row; status-gated only |
| Client wanted election preserved on 44/45 | Med | SD assumes Robert wins; document in Risk |
| Operators expect CV fix from NFO alone | Low | Notes: still need Data Admin + rebuild CV for blank MCV |
| Touching MDIVOPT by mistake | Low | Field allow-list: MNFOPT only |

---

## 11. Recommended Risk Agent Prompt

```
Risk Agent — Issue #72 NFO matches ETI/RPU status

Read Issue_72_Intake_Summary.md, Issue_72_Planning_Report.md, Issue_72_Scope_Decisions.md.
Quantify before/after MNFOPT for MSTATUS 44/45; prove non-44/45 unchanged; prove #57 Eric samples unchanged.
Go / Conditional Go / No-Go for Development.
No code.
```

---

## 12. Recommended Development Task (do not implement)

1. In `app.py` **and** `QLA_Migration/app.py`, after quikmstr `row_data` is fully mapped (after #49 status final; before or with existing post-row gates), apply:  
   - if `MSTATUS == "44"` → `MNFOPT = "2"`  
   - if `MSTATUS == "45"` → `MNFOPT = "3"`  
2. Log forced count.  
3. Bump `APP_VERSION` both copies.  
4. Do **not** change `Master_Value_Translation.csv` NF_* keys or re-add PUT→MNFOPT to rulebook.  
5. Re-batch quikmstr → publish `Output/quikmstr.csv` + `Output/Test_Validation/quikmstr.csv`.  
6. Validator `tools/validators/validate_issue72_mnfopt_status.py`:  
   - all status 44 → MNFOPT 2  
   - all status 45 → MNFOPT 3  
   - sample `010407670C` = 3  
   - control `010367131C` still 2 (status 22)  
   - #25/#26 smoke unchanged  

**Model for Development:** Composer 2.5 (locked).

---

## Gate Criteria (G1 — Planning Complete)

- [x] Planning report published  
- [x] Source and target documented  
- [x] Trace table included  
- [x] Open questions enumerated (assumed SD-72-*)  
- [x] Development task outlined but **not** executed  
- [x] No code, rulebook, or output changes  
