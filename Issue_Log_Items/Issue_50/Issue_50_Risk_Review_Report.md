# Issue #50 — Risk Review Report

**Issue:** #50 — Policy Notes Missing  
**Framework stage:** Risk Agent (G3)  
**Status:** **CONDITIONAL GO** — Ready for Development (await explicit Development approval)  
**Fallback simulated:** Yes — header-derived fixed-width PNOTE parse vs current pandas skip  
**Generated:** 2026-07-11  
**Agent:** Risk Agent — read-only review (no production code in this stage)  
**Model:** Cursor Grok 4.5 (locked)  
**Script:** `Issue_Log_Items/Issue_50/scripts/risk_review_issue50_pnote_parse.py`

**Status note:** Risk analysis only — no production code changes unless later approved.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Development may proceed **only** with these constraints:

1. Replace PNOTE ingest with a **header-derived fixed-width reader** (field widths from padded PNOTE header names; all 7,976 data lines are exactly **1,166** chars).  
2. **Do not** use heuristic “join extra CSV commas” as the primary fix — fixed-width is proven exact.  
3. **PENSE reader unchanged** in this issue (no proven same defect; leave `#21M` ENS path alone).  
4. Preserve **#21M-FU** one-row-per-`MEMOKEY`, **#25** padding, **#21J** `[CONVERSION]` prepend order.  
5. Ship validator asserting `018495BC` contains Bauerly + Last Known Address, and control `010335038C` MEMOTEXT body unchanged vs pre-fix baseline.

Simulation recovers **1,939** dropped PNOTE rows, changes **1,043** memo bodies, adds **147** policies that newly gain PNOTE/ENS content in the merge set, removes **0** keys, and keeps the #21M control policy **byte-stable**. Blast radius is `quikmemo` MEMOTEXT only.

---

## 1. Current vs Proposed Mapping

| Concern | Current | Proposed | Change? |
|---------|---------|----------|---------|
| PNOTE file read | `pd.read_csv(..., on_bad_lines="skip")` | Fixed-width slice using header field widths | **Yes** |
| PNOTE → `[PNOTE]` format | `_format_pnote_memotext` | Unchanged | **No** |
| PENSE read / `[ENS]` | Existing pandas path | Unchanged | **No** |
| Merge grain | One row per MEMOKEY (`\n---\n`) | Unchanged | **No** |
| `#21J` `[CONVERSION]` | Prepend first | Unchanged | **No** |
| MEMOKEY | `format_qladmin_mpolicy` (#25) | Unchanged | **No** |
| QUIKMEMO schema | MEMOKEY + MEMOTEXT | Unchanged | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| `quikmstr` / `quikridr` / `quikplan` / `quikprmh` | **No** |
| #25 MPOLICY / MEMOKEY padding | **No** (continue to call existing helper) |
| #26 `quikridr.MPREM` / `quikmstr.MMODPREM` | **No** |
| Rulebooks / Master_Crosswalk values | **No** |
| PENSE ENS filter (`ENS_KEY_TYPE=P`) | **No** |
| Claims tables | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `qla_core/quikmemo_converter.py` — `_read_csv` / PNOTE branch | **Primary Dev touch** |
| `qla_core/quikmemo_converter.py` — format / merge helpers | Reuse only |
| `qla_core/quikmemo_dbf_generator.py` | Regenerate DBF+DBT after re-emit (no logic change expected) |
| `qla_core/modal_premium_factors.py` / `append_issue21j_conversion_memos` | Untouched; still prepends after convert |
| `QLA_Migration/app.py` quikmemo batch | Version bump + call path unchanged |
| `tools/validators/validate_issue21m_quikmemo.py` | Update expected counts / add #50 asserts as needed |

---

## 4. Population Analysis

### Source / parse

| Metric | Count |
|--------|------:|
| PNOTE data lines (raw) | 7,976 |
| Lines with exact fixed width 1,166 | **7,976** (100%) |
| Pandas rows kept today | 6,037 |
| Rows recovered by fixed-width | **1,939** |
| Blank PNOTE rows still skipped | 30 (same before/after) |

### QUIKMEMO body impact (PNOTE+PENSE merge, before #21J prepend)

| Metric | Before (pandas) | After (fixed-width) | Delta |
|--------|----------------:|--------------------:|------:|
| PNOTE segments emitted | 6,007 | 7,946 | **+1,939** |
| PENSE segments | 23,346 | 23,346 | 0 |
| Distinct MEMOKEY (notes merge) | 4,379 | 4,526 | **+147** |
| MEMOKEY text unchanged | — | 3,483 | — |
| MEMOKEY text changed | — | **1,043** | — |
| MEMOKEY removed | — | **0** | — |
| Total MEMOTEXT chars | 4,293,383 | 4,709,192 | **+415,809** (~0.4 MB) |

### SAL concentration

| Metric | Count |
|--------|------:|
| SAL policies in `quikridr` | 163 |
| SAL MEMOKEYs with changed body | **130** |
| Matches Planning malformed intersect | Yes |

### Fleet row count after #21J

Current `quikmemo.csv` = **5,083** (full `quikmstr` fleet with `[CONVERSION]`).  
Proposed fix does **not** change grain: still one row per converted policy. Expect **5,083** rows after re-batch; **MEMOTEXT** richer for 1,043+ keys that already exist, and ~147 CONVERSION-only policies gain first `[PNOTE]` content.

Evidence: `evidence/issue50_risk_simulation_summary.csv`, `issue50_risk_memotext_changes.csv`

---

## 5. Fallback Recommendation

| Option | Rows recovered | Assessment |
|--------|---------------:|------------|
| **A. Header fixed-width PNOTE parse** | **1,939** | **Recommended** — 100% line-length match; Bauerly LINE_1 exact |
| B. Heuristic CSV re-join extra commas | ~1,939 | Reject as primary — ambiguous LINE boundary assignment |
| C. Client re-extract with quoted CSV | N/A | Reject for this issue — extract is already complete fixed-width |
| D. SAL-only special case | 130 | Reject — hides fleet defect; 913 non-SAL policies also lose notes |
| E. Do nothing / UAT load-only | 0 | Reject — Bauerly text absent from CSV/DBF today |

**Recommended fallback:** None required beyond Option A. If fixed-width fails a row (should not — 0 short/long lines today), log and skip that row only (preserve current blank-skip behavior).

---

## 6. Trace Policies

| Policy | Role | Before | After | Pass? |
|--------|------|--------|-------|------:|
| **018495BC** | Client example | Last Known only; **no** Bauerly | Bauerly **+** Last Known | **Yes** |
| **010335038C** | #21M control | Has `[PNOTE]` | Identical body | **Yes** (stable) |
| **01159D276C** (SAL) | ONLY_MALFORMED sample | No `[PNOTE]` in merge | Gains `[PNOTE]` | **Yes** (direction) |

`018495BC` fixed-width `LINE_1` Seq 1:

> Vincent J. Bauerly, if living otherwise to: Ethel R. Bauerly.

Evidence: `evidence/issue50_risk_traces.csv`

---

## 7. Largest MEMOTEXT Growth (top changes)

Largest deltas are policies that regain many comma-containing note rows (claim/correspondence narratives). Exact top-N list: `evidence/issue50_risk_memotext_changes.csv` (sorted by `DELTA_LEN`).

Material point: growth is **additive recovered source text**, not recalculation drift. No numeric premium/rate fields move.

---

## 8. Material Calculation Impact

| Area | Impact |
|------|--------|
| Premium / modal / MPREM | **None** |
| Plan / status / crosswalk | **None** |
| Memo display content | **Intentional correction** — restore LifePRO notes previously dropped |
| DBT size | ~+0.4 MB MEMOTEXT before CONVERSION; acceptable |
| Orphan / crosswalk | Simulation orphan path unchanged; **0** removals |

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **PASS** — continue `format_qladmin_mpolicy`; example already `'  018495BC'` |
| Issue #26 MPREM / MMODPREM | **PASS** — out of scope |
| Issue #21M / #21M-FU grain | **PASS** — one MEMOKEY row; merge separator unchanged |
| Issue #21J `[CONVERSION]` | **PASS** — prepend left in place (A3 from Dependency Gate) |
| Issue #28 SAL catalog | **PASS** — no PLAN mapping changes |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] `018495BC` MEMOTEXT contains `Bauerly` and `Last Known Address`
- [ ] `010335038C` note body unchanged vs pre-fix baseline (strip `[CONVERSION]` if comparing)
- [ ] ≥1 SAL ONLY_MALFORMED policy gains `[PNOTE]` (e.g. from `issue50_sal_malformed_impact.csv`)
- [ ] `quikmemo.csv` row count remains **5,083** (with #21J) or documented equivalent
- [ ] All MEMOKEY lengths = 10 (#25)
- [ ] PENSE segment counts unchanged vs baseline
- [ ] `validate_issue21m_quikmemo.py` / packaging validator updated then PASS
- [ ] DBF+DBT co-located in `quikmemo_uat_dbf/`; Bauerly readable from DBF MEMOTEXT
- [ ] Untouched: `quikridr.MPREM`, `quikmstr` non-memo fields, rulebooks
- [ ] Spot-check: no MEMOKEY removed relative to prior note-bearing set

---

## 11. Recommended Development Agent Task

**Switch to Composer 2.5** after user says Issue #50 is approved for Development.

1. In `qla_core/quikmemo_converter.py`, add a PNOTE fixed-width reader driven by padded header field widths; use it for the PNOTE path only (keep `_read_csv` for PENSE or split helpers cleanly).  
2. Do **not** change formatters, merge grain, orphan rules, or `#21J` append.  
3. Bump `APP_VERSION` in **both** root `app.py` and `QLA_Migration/app.py` (currently **v57.73** → next patch, e.g. **v57.74**).  
4. Add `tools/validators/validate_issue50_pnote_parse.py` with asserts from §10.  
5. Re-run quikmemo (or full batch); confirm DBF+DBT packaging.  
6. On validator PASS, copy modified `quikmemo.csv` (+ uat_dbf if used for UAT) to `QLA_Migration/Output/Test_Validation/`.  
7. Do **not** modify Sync_Rulebook_*.csv, Master_Crosswalk, or unrelated converters.

---

## G3 checklist

- [x] Risk report published with Go/No-Go  
- [x] Impact quantified (not guessed)  
- [x] Unrelated fields explicitly marked untouched  
- [x] #25 / #26 preservation confirmed  
- [ ] User acknowledged recommendation → **awaiting your Development approval**

---

## Appendix

| Artifact | Path |
|----------|------|
| Risk simulation script | `Issue_Log_Items/Issue_50/scripts/risk_review_issue50_pnote_parse.py` |
| Simulation summary | `evidence/issue50_risk_simulation_summary.csv` |
| Changed MEMOKEY list | `evidence/issue50_risk_memotext_changes.csv` |
| SAL changed keys | `evidence/issue50_risk_sal_changed_keys.csv` |
| Traces | `evidence/issue50_risk_traces.csv` |
| Planning / Dep Gate | `Issue_50_Planning_Report.md`, `Issue_50_Dependency_Gate.md` |

---

## Next step

If you accept this Conditional Go, reply:

```
Issue #50 is approved for Development.

Switch to Composer 2.5. Read AI_Agents/Development_Agent.md.
Make surgical changes only. Version-bump app.py. Add validation script.
Do not regress Issue #25 MPOLICY padding or Issue #26 MPREM mapping.
```
