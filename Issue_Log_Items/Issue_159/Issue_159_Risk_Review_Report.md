# Issue #159 — Risk Review Report

**Issue:** #159 — L10/L14 traditional-life reserves at $0 (UW key mismatch)  
**Framework stage:** Risk Agent (G3)  
**Status:** **GO — Ready for Development** (after user approval)  
**Fallback simulated:** N/A — restore locked #118 map; no new business rule  
**Generated:** 2026-09-02  
**Agent/script:** read-only counts on current `QLA_Migration/Output/quikridr.csv`

**Status note:** Risk analysis only — no production code changes unless later approved.

---

## Go / No-Go Recommendation

**GO** — pass `plan=` into `map_rider_uwclass` in both `app.py` copies and re-emit `quikridr` from LifePRO `UNDERWRITING_CLASS`. Blast radius is ~616 rider UW codes; rate tables, PVO, premiums, and policy numbers stay put.

**Conditions (surgical, not blockers):**

1. Feed the **LifePRO letter**. Remapping current `ST`/`00` is a no-op (`QLA_UWCLASS_DOMAIN` pass-through).
2. Do not change `map_uwclass` itself or any rate loader.
3. Non-L10 `S→ST` stays (1,524 rows, including `5L0110`).
4. Do not invent L14 PQ/ST/PR TV/NP pages.
5. Bump **both** `APP_VERSION` to **v59.08**.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|---|---|---|---|
| quikridr.MUWCLASS | `map_rider_uwclass(val)` | `map_rider_uwclass(val, plan=MPLAN)` | **Yes** |
| L10 LifePRO S | ST | SM | **Yes** |
| L14 LifePRO N/Q/T/R | 00 | NT / PQ / ST / PR | **Yes** |
| L10 B / P | BL / PR | BL / PR | **No** |
| Non-L10 S | ST | ST | **No** |
| QuikTvs / QuikNps / QuikPlTv | plan-aware already | unchanged | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|---|---|---|
| quikmstr.MMODPREM | MODE_PREMIUM | **No** |
| quikridr.MPREM | #26 / #88 / #137 | **No** |
| MPOLICY | #2 / #25 | **No** |
| MBAND | #71 = 00 | **No** |
| PLANVALOPT / GDVARYTV | #96 / #136 | **No** |
| rates/* factor values | PDAGE / PAAGERAT | **No** |

---

## 3. Repo References

| Location | Role |
|---|---|
| `app.py` + `QLA_Migration/app.py` ~9303 | Broken call |
| `qla_core/rate_dbf_schema.py` | Correct map (leave as-is) |
| Rate loaders | Already plan-aware |
| `validate_issue118_uwclass.py` | UAT would FAIL today; not a release smoke |
| `rate_emit.ensure_members_for_rider_uw` | Adds ST/00 to QuikPlUw without a TV grid |

---

## 4. Population Analysis

| Metric | Count |
|---|---:|
| Total quikridr rows | 6,956 |
| Rows that would change | **~616** (384 L10 ST→SM + 232 L14 00→NT/PQ/PR/ST) |
| Rows unchanged | ~6,340 |
| Blank / zero source | stay 00 |

### Breakdown

| Dimension | rows | would_change |
|---|---:|---:|
| 1L1095 phase 1 ST | 216 | 216 → SM |
| 1L10OD phase 1 ST | 45 | 45 → SM |
| Other L10_PLANS ST (riders) | 123 | 123 → SM |
| 1L14SC 00 | 232 | 232 → NT 101 / PQ 111 / PR 13 / ST 7 |
| Non-L10 ST | 1,524 | **0** |
| 1L1095 BL+PR (already calculate) | 162 | **0** |

Valuation dollars unlocked after CSO reload (N-class / SM only): **~$2.35M** of the $2.53M on these three plans (1L1095 $1.11M + 1L10OD $0.24M + L14 NT share of $1.18M). L14 PQ/ST/PR share of the $1.18M may stay $0 (no source RV).

---

## 5. Fallback Recommendation (if applicable)

| Option | Rows changed | Assessment |
|---|---:|---|
| **A. Pass plan= + letter-sourced re-emit** | ~616 | **recommended** |
| B. Surgical Output remap only, no app.py | 616 | Reject — next batch regresses again |
| C. Clone SM/NT TV pages onto ST/00 | thousands of rate rows | Reject — duplicates the wrong key; #118 sheet violated |
| D. Turn UWVARYTV=N | plan flags | Reject — Closed #136 real-variation rule |

**Recommended fallback:** none. Kill switch is revert the one-line `app.py` change (`QLA` not required).

---

## 6. Trace Policies

| Policy | Before | Proposed | Pass? |
|---|---|---|---|
| 9011189929C | BL | BL | Yes |
| 9011190516C | ST | SM | Yes |
| 9011193156C | PR | PR | Yes |
| 9011059291C (5L0110) | ST | ST | Yes — must not flip |
| 9011206462C | 00 | NT | Yes |
| 9011208194C | 00 | ST | Yes (no TV — residual) |
| 9011207210C | 00 | PQ | Yes (no TV — residual) |

---

## 7. Top Largest Changes

Not a dollar field on emit. Largest **count** concentrations: 1L1095 216 ST→SM; 1L14SC 232 00→split; 9JPO10 92 ST→SM (L10 JPO rider; no TV on that plan today — membership only).

---

## 8. Material Calculation Impact

Intentional: L10 smoker and L14 N-class policies become able to look up existing TV/NP pages. Accidental drift would be non-L10 ST→SM or BL/PR flips — Validation must prove those counts stay at 0.

QuikValf $0 will not move in-repo. Do not FAIL Validation on a stale `QuikValf.dbf`.

---

## 9. Prior Fix Preservation

| Check | Result |
|---|---|
| Issue #25 / #2 MPOLICY padding | Untouched |
| Issue #26 MPREM / MMODPREM | Untouched |
| Issue #118 map rules | Restored on emit, not rewritten |
| Issue #96 / #136 PVO | Untouched |
| Issue #71 BAND 00 | Untouched |
| Issue #107 LP9595 | Untouched (notify only if Dev later remaps RV source) |
| Closed #157 / #158 PR ownership | Untouched |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] UAT: 9011190516C = SM; 9011206462C = NT; 9011208194C = ST; 9011207210C = PQ
- [ ] Unchanged: 9011189929C = BL; 9011193156C = PR; 9011059291C = ST
- [ ] 1L1095 / 1L10OD phase 1 ST count = 0
- [ ] 1L14SC 00 count = 0
- [ ] Non-L10 ST count still 1,524 (±0)
- [ ] quikridr row count still 6,956; MPREM / MPOLICY / MBAND unchanged on a sample join
- [ ] QuikTvs row counts unchanged
- [ ] `validate_issue118_uwclass.py` PASS
- [ ] New #159 validator PASS
- [ ] Publish Test_Validation/quikridr.csv

---

## 11. Recommended Development Agent Task

1. Both `app.py` files:  
   `val = map_rider_uwclass(val, plan=self.normalize(row_data.get("MPLAN", "")))`
2. Do NOT change: `map_uwclass` body, rate loaders, rulebooks, PVO, MPREM, MPOLICY, QuikTvs values.
3. Version bump: **v59.07 → v59.08** in both `app.py` files.
4. Re-emit `quikridr` from PPBEN letters (full batch or #118-style apply that calls `map_rider_uwclass(letter, plan=plan)`).
5. Add `tools/validators/validate_issue159_muwclass_plan_aware.py` (fail-closed). Register in `SMOKE_JOBS` only at Closure.
6. Publish `Output/Test_Validation/quikridr.csv`.

---

## Appendix

- Before-state: current Output `quikridr`
- After-state gold: `Issue_118/evidence/issue118_plan_uw_inventory.csv`
- Valuation symptom: `docs/Valuation/analysis/Valx_QuikValf_Comparison_20260630.md`
