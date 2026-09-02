# Issue #159 — Planning Report

**Issue:** #159 — L10/L14 traditional-life reserves at $0 (UW key mismatch)  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning complete  
**Generated:** 2026-09-02  
**Agent/script:** read-only counts against current `QLA_Migration/Output/`

**Status note:** Planning analysis only — no production code changes.

---

## 1. Executive Finding

`app.py` maps `UNDERWRITING_CLASS` → `MUWCLASS` with `map_rider_uwclass(val)` and drops `plan=`. The #118 form-aware rules for L10 (S→SM) and L14 (N→NT, Q→PQ, T→ST, R→PR) never fire on policy emit. Rate loaders still pass plan/coverage, so QuikTvs stays on BL/PR/SM and NT. QLAdmin `UWVARYTV=Y` on L10 (and exact-key lookup on L14) then finds no TV page and writes reserve $0.

The #118 surgical remap restored the keys (1L1095 had 216 SM; 1L14SC was NT 101 / PQ 111 / PR 13 / ST 7). The next full batch overwrote riders through the plan-blind path. Current Output: those same 216 are ST; all 232 L14 are 00.

Direction: one-line wiring in both `app.py` copies, using `row_data["MPLAN"]` already in the loop. Re-emit `quikridr` from the **LifePRO letter**, not from the already-mapped code (`ST` and `00` are in the approved domain and would pass through unchanged). Ready for Dependency Gate.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|---|---|---|---:|
| PPBEN | `UNDERWRITING_CLASS` via `Sync_Rulebook_quikridr.csv` | Used at batch time (gitignored extract; rulebook + #118 letters on file) | 6,956 quikridr rows |

### Available source fields

| Field | Column / source | Notes |
|---|---|---|
| Policy number | PPBEN `POLICY_NUMBER` | #2 / #25: source + C, right-justified 11 |
| Benefit seq | `BENEFIT_SEQ` → `MPHASE` | Phase 1 is the valuation base |
| UW letter | `UNDERWRITING_CLASS` | B/P/S on L10; N/Q/T/R on L14; 0/blank → 00 |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source |
|---|---|---|---:|---|
| quikridr | MUWCLASS | C | 2 | schema_constants / Help rider UW |
| rates/QuikTvs | UWCLASS | C | 2 | rate_dbf_schema |
| rates/QuikPlTv | UWCLASS | C | 2 | Plan Values key |
| rates/QuikPlUw | UWCODE | C | 2 | Dropdown membership (#118) |

**Repo references** (population paths only):

| Location | Role |
|---|---|
| `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv` | `UNDERWRITING_CLASS,MUWCLASS,00` |
| `app.py` / `QLA_Migration/app.py` ~9303 | `map_rider_uwclass(val)` — missing plan |
| `qla_core/rate_dbf_schema.py` | `map_uwclass` / `map_rider_uwclass` / `L10_PLANS` / `L14_PLANS` |
| Rate loaders | Already pass `plan=` / `coverage_id=` |
| `qla_core/rate_emit.py` `ensure_members_for_rider_uw` | Adds policy UW onto QuikPlUw (hides missing TV) |
| `tools/validators/validate_issue118_uwclass.py` | Domain + UAT anchors; not in SMOKE_JOBS |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|---|---|---|---|---|
| PPBEN | UNDERWRITING_CLASS | quikridr.MUWCLASS | `map_rider_uwclass(letter, plan=MPLAN)` | **Yes** — add plan |
| Rate extracts | UNDERWRITING_CLASS | QuikTvs/QuikNps UWCLASS | existing plan-aware map | **No** |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|---|---|---|
| quikmstr.MMODPREM | PPOLC.MODE_PREMIUM | **No** |
| quikridr.MPREM | ANN_PREM_PER_UNIT + fallback (#26) | **No** |
| MPOLICY padding | format_qladmin_mpolicy (#2/#25) | **No** |
| quikridr.MBAND | default 00 (#71) | **No** |
| PLANVALOPT / *VARY* | #96 / #136 | **No** |
| QuikTvs / QuikNps values | PDAGE / Rate_Table | **No** |
| Non-L10 S→ST | #118 form sheet | **No** |

---

## 5. Open Client Questions

1. **L14 Q/T residual $0** — after remap, PQ/ST policies still have no N-class-only TV grid. Default locked at Discovery: emit the sheet class; do not invent factors. Not a Development blocker.
2. **#118 Eric approval** — still pending on the original remap workbook. #159 does not wait on it; it restores the already-approved map on emit.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|---|---|
| Policy key | #2 source + C, 11-char right-justify |
| UW code | Two-character approved domain only |
| Blanks / `0` | 00 (Standard) |
| Remap input | Always the LifePRO letter. Never `map_rider_uwclass(existing MUWCLASS)` — `ST`/`00` are in-domain and would no-op |
| L10 S | SM |
| Non-L10 S | ST |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` → QLA via existing converter (`#2`).
2. Do not change padding or crosswalk.
3. Validator keys are the 11-char `901…C` UAT anchors from #118.

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|---|---:|---|
| Total quikridr rows | 6,956 | current Output |
| L10 family ST (would become SM) | **384** (262 phase 1) | current ST on `L10_PLANS` |
| of which 1L1095 / 1L10OD / 1L10PR | 216 / 45 / 1 | phase 1 |
| L14 00 (would restore NT/PQ/PR/ST) | **232** | all phase 1; #118 inventory NT 101 / PQ 111 / PR 13 / ST 7 |
| Non-L10 ST (must stay) | 1,524 | e.g. 5L0110 S→ST is correct |
| Expected MUWCLASS deltas | **~616** | 384 + 232 |
| Rows unchanged | ~6,340 | including all BL/PR L10 |

---

## 10. Sample Trace (6 policies)

| Policy (QLA) | Plan | Before | After (proposed) | Status |
|---|---|---|---|---|
| 9011189929C | 1L1095 | BL | BL | Unchanged |
| 9011190516C | 1L1095 | ST | SM | Fix |
| 9011193156C | 1L1095 | PR | PR | Unchanged |
| 9011206462C | 1L14SC | 00 | NT | Fix |
| 9011208194C | 1L14SC | 00 | ST | Fix (no TV grid — residual $0) |
| 9011207210C | 1L14SC | 00 | PQ | Fix (no TV grid — residual $0) |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|---|---|---|
| Remapping already-emitted ST/00 is a no-op | High | Dev must feed LifePRO letter |
| Non-L10 S flipped to SM | High | Only `L10_PLANS` / L10 coverage context; validator asserts 5L0110 stays ST |
| QuikPlUw still lists ST on 1L1095 after fix | Med | Membership rebuild from live riders; leftover ST dropdown without TV is OK if no rider uses it |
| L14 Q/T still $0 after CSO reload | Med | Document as #118 known gap; not a #159 FAIL |
| Full batch vs surgical remap | Low | Either is valid if letter-sourced; full batch preferred so `app.py` is the path of record |

---

## 12. Dependency Gate Preview

| Check | Met? |
|---|---|
| Source field present | Yes — rulebook + #118 letters |
| Field definitions confirmed | Yes |
| Client scope clear | Yes — Warren opened #159 |
| Example policies available | Yes — six UAT anchors |

---

## 13. Recommended Risk Agent Prompt

```
Risk Agent — Issue #159: L10/L14 Zero Reserve UW
Read Planning report. Quantify MUWCLASS deltas (L10 ST→SM, L14 00→NT/PQ/PR/ST).
Confirm non-L10 ST unchanged. No code.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. In **both** `app.py` and `QLA_Migration/app.py`, change the MUWCLASS branch to  
   `val = map_rider_uwclass(val, plan=self.normalize(row_data.get("MPLAN", "")))`.  
   `MPLAN` is already written earlier in the same rider row (#105 pattern).
2. Do **not** change `map_uwclass` rules, rate loaders, PVO, bands, or MPREM.
3. Bump `APP_VERSION` in **both** files: **v59.07 → v59.08**.
4. Re-emit `quikridr` (full policy batch, or PPBEN-letter remap like `apply_issue118_output_remap.py`).
5. Validator: `tools/validators/validate_issue159_muwclass_plan_aware.py` — #118 UAT anchors; zero `ST` on `L10_PLANS` phase-1 where rate keys include SM; L14 N-class UAT is NT not 00; 5L0110 `9011059291C` stays ST.
6. Publish `Output/Test_Validation/quikridr.csv` on PASS.

---

## Appendix

- Related: #118, #107 (out of scope), Closed #96/#136/#71/#59
- References: `rate_dbf_schema.py` map; `docs/Valuation/analysis/Valx_QuikValf_Comparison_20260630.md`
- #118 after-state: `Issue_118/evidence/issue118_plan_uw_inventory.csv`
