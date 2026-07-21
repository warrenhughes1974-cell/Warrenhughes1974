# Issue #48 — Risk Review Report

**Issue:** #48 — Secondary Rate File (PAAGERAT fallback)  
**Framework stage:** Risk Agent (G3)  
**Status:** **CONDITIONAL GO** — Ready for Development (await explicit Development approval)  
**Fallback simulated:** Yes — read-only PLAN+TYPE ownership / collision simulation  
**Generated:** 2026-07-10  
**Agent:** Risk Agent — read-only review (no production code in this stage)  
**Script:** `Issue_Log_Items/Issue_48/_risk_review_issue48_ownership.py`

**Status note:** Risk analysis only — no production code changes unless later approved.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Implement **path wiring + audit only** in this release slice:

1. Prefer `QLA_Migration/Source/Rate_Table_Extract_Txt.txt` in `rate_table_extract()` / config (`A4`).  
2. Emit an audit of Rate_Table PLAN+TYPE keys that have no PAAGERAT owner for shared types.  
3. **Do not** suppress Rate_Table `CV` / `NP` / `RV` / `DB` merely because PAAGERAT also has rows — those TYPE_CODEs are **not** emitted by PAAGERAT loaders today.  
4. Ownership suppress (`A1`) applies only to **PR / NF** (types PAAGERAT actually streams). Simulation finds **0** PR/NF PLAN+TYPE overlaps → **0 suppress row impact** now.

Path wiring alone has **0 row delta** (Source `.txt` MD5 = twin CSV). Collision suppress on NP/RV would be **unsafe** (would drop large Rate_Table grids with no PAAGERAT QuikNps/QuikTvs replacement).

---

## 1. Current vs Proposed Mapping

| Concern | Current | Proposed | Change? |
|---------|---------|----------|---------|
| Rate_Table path | `plan_analysis/.../Rate_Table_Extract_20260427.csv` | Prefer `Source/Rate_Table_Extract_Txt.txt`, else twin | **Yes** (path only) |
| Dual stream | Rate_Table all `TYPE_TO_TABLE` + PAAGERAT PR/NF/BP/U5/U6 | Unchanged emit order | **No** (this slice) |
| PR/NF when both resolve | Both can stream (collision risk) | If overlap: keep PAAGERAT, suppress Rate_Table PR/NF | **Yes** (guard; **0 pairs today**) |
| CV/NP/RV/DB | Rate_Table primary | Remain Rate_Table primary even if PAAGERAT has same coverage | **No suppress** |
| BP/U5/U6 | PAAGERAT only | No Rate_Table fallback | **No** |
| #42 gaps | Missing | Still missing | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| `quikmstr` / `quikridr` / policy tables | **No** |
| #25 MPOLICY padding | **No** |
| #26 `quikridr.MPREM` | **No** |
| #31 ISWL BP/COI/PR suppress allowlists | **No** |
| #37 / #40 / #41 CV placement / inheritance | **No** |
| QuikCoi / QuikGcoi / QuikUint / QuikIssc | **No** (except QuikIssc still reads Rate_Table path — must resolve to same bytes) |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `qla_core/plan_source_paths.py` | Path resolve — primary Dev touch |
| `qla_core/rate_pipeline.py` | Dual stream orchestration |
| `qla_core/paagerat_pr_loader.py` | PAAGERAT PR / NF only |
| `qla_core/rate_factor_loader.py` | Rate_Table transform |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | `source_rate_extract` config |
| `qla_core/quikissc_loader.py` | Uses `source_rate_extract` — must keep working |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| Path wiring MD5 match (Source `.txt` vs twin) | **Yes** |
| Path wiring row delta | **0** |
| Rate_Table shared PLAN+TYPE keys (crosswalked) | 160 |
| PAAGERAT shared PLAN+TYPE keys (segment-resolved) | 111 |
| Overlap PLAN+TYPE (any shared type) | **2** |
| Overlap that are PR or NF (suppress-eligible) | **0** |
| Overlap NP/RV (do **not** suppress) | **2** |
| ISWL BP plan overlaps | **0** |
| Rate_Table-only PLAN+TYPE (secondary candidates) | 158 |
| Rate_Table-only source rows (shared types) | 816,013 |
| PAAGERAT-only PLAN+TYPE | 109 |

### The only PLAN+TYPE overlaps (informational — do not suppress)

| PLAN | TYPE | Target | RT rows | PAA rows | Coverage |
|------|------|--------|--------:|---------:|----------|
| `7619PU` | RV | QuikTvs | 3724 | 94 | `619 SPS PU` |
| `A96DAR` | NP | QuikNps | 78 | 3 | `896 DAR` |

PAAGERAT does **not** stream NP/RV into QuikNps/QuikTvs. Suppressing Rate_Table here would delete grids with no replacement → **rejected**.

### Secondary PR examples (PAAGERAT miss → Rate_Table already supplies)

| PLAN | Coverage | RT PR rows |
|------|----------|-----------:|
| `9DIS25` | DISCHO25 | 117 |
| `5L01MA` | L01 10Y MA | 9720 |
| `2665ST` | 665 STME95 | 117 |
| (+ 8 other DISCHO* plans) | | |

Evidence:  
`evidence/issue48_risk_impact_summary.csv`  
`evidence/issue48_risk_collision_candidates.csv`  
`evidence/issue48_risk_secondary_candidates.csv`

---

## 5. Fallback Recommendation

| Option | Emit delta | Assessment |
|--------|------------|------------|
| **A. Path wiring + audit only** | **0** | **Recommended** — satisfies client Source delivery + A4 |
| B. A + suppress Rate_Table on all shared overlaps (incl. NP/RV) | Drops 3,802 RT rows on 2 plans; no Quik replacement | **Reject** — unsafe grain / loader gap |
| C. A + suppress Rate_Table PR/NF when PAAGERAT owns PLAN+TYPE | **0** pairs today | **Optional guard** — safe to code; no current blast |
| D. Reshape Rate_Table → attained SEQ | Unknown / actuarial | **Reject** — violates A3 |
| E. Claim #42 closed | 0 new rows | **Reject** |

**Recommended:** Option **A**, with optional inert Option **C** guard for PR/NF only.

---

## 6. Trace (coverage / PLAN — no policies provided)

| Key | Before | Proposed (Option A) | Pass? |
|-----|--------|---------------------|-------|
| Path resolve | Twin CSV | Source `.txt` (same bytes) | Yes |
| `9DIS25` PR | Rate_Table emit (if crosswalked) | Unchanged + audit tag secondary | Yes |
| `5L01MA` PR | Rate_Table | Unchanged | Yes |
| `L01 10Y` / `L10 LP9595` NP (#42) | Missing | Still missing | Yes (out of scope) |
| `7619PU` RV | Rate_Table 3724 rows | **Unchanged** (do not suppress) | Yes |
| `A96DAR` NP | Rate_Table 78 rows | **Unchanged** (do not suppress) | Yes |
| ISWL BP plans | PAAGERAT BP authority | Untouched | Yes |

---

## 7. Largest potential change (if unsafe Option B were chosen)

| PLAN+TYPE | RT rows at risk | Why rejected |
|-----------|----------------:|--------------|
| `7619PU` RV | 3724 | PAAGERAT RV not emitted to QuikTvs |
| `A96DAR` NP | 78 | PAAGERAT NP not emitted to QuikNps |

---

## 8. Edge Cases

| Edge | Handling |
|------|----------|
| Identical Source `.txt` and twin | Path prefer Source; content unchanged |
| PAAGERAT NP/RV present alongside Rate_Table | Keep Rate_Table; do not treat as A1 owner |
| Future PR/NF dual resolve | Optional suppress guard (0 today) |
| Unmapped Rate_Table coverages | Existing PLAN_INVALID / skip — no invent |
| Config still points at older PAAGERAT dated file | Hygiene: prefer Source `…_20260630.csv` in same Dev slice if touching config |

---

## 9. Regression Surfaces

| Surface | Risk | Mitigation |
|---------|------|------------|
| QuikIssc / rate pipeline path break | Medium | Resolver must find Source `.txt`; validate file opens |
| Accidental NP/RV suppress | **High** | Explicit Dev scope: suppress PR/NF only |
| #31 ISWL | Low | 0 BP overlaps; no allowlist edits |
| #37/#40/#41 CV | Low | No CV logic change |
| #42 | None | Remains open |
| Dual-stream V03 collisions on PR/NF | Low now | 0 overlaps; guard optional |
| Output folder pollution | Process | Audits → `Issue_48/evidence/` or `Reports/`, not `Output/` |

---

## 10. Recommended Development Task (surgical)

1. `plan_source_paths.rate_table_extract()`: add  
   `QLA_Migration/Source/Rate_Table_Extract_Txt.txt` as first candidate.  
2. Update `rate_loader_config.json` `source_rate_extract` to Source path (or empty + resolver).  
3. Optional: same for `paagerat_pr_extract` → Source `PAAGERAT_…_20260630.csv`.  
4. Optional inert guard: build PAAGERAT PR/NF PLAN set; skip Rate_Table PR/NF rows for those PLANs (expect 0 skips).  
5. Write audit CSV under `Issue_48/evidence/` or `QLA_Migration/Reports/` — not Output.  
6. Bump `APP_VERSION` in **both** `app.py` and `QLA_Migration/app.py` if engine path touched.  
7. Validation: `_validate_issue48_secondary_rate.py`  
   - Resolved path ends with `Rate_Table_Extract_Txt.txt` when present  
   - MD5 equals twin  
   - `7619PU` RV / `A96DAR` NP row counts unchanged vs baseline  
   - Sample secondary PR plans still present  
   - #42 keys still absent  

**Do not:** suppress CV/NP/RV/DB; grain-convert; close #42; touch policy rulebooks.

---

## 11. Validation / Regression Checklist (for later agents)

- [ ] Path resolve → Source `.txt`  
- [ ] Factor row counts for QuikCvs/Nps/Tvs/Gps unchanged vs pre-change baseline (Option A)  
- [ ] `7619PU` RV and `A96DAR` NP not reduced  
- [ ] DISCHO* / `5L01MA` PR still emit  
- [ ] ISWL BP/COI plans unchanged  
- [ ] #42 still 0 rows for L01 10Y NP / L10 LP9595  
- [ ] No new files left in `QLA_Migration/Output/` root except table CSVs  

---

## 12. Gate G3 checklist

- [x] Risk report published with Go/No-Go (**CONDITIONAL GO**)  
- [x] Impact quantified (0 path delta; 0 PR/NF suppress; 2 unsafe NP/RV overlaps documented)  
- [x] Unrelated fields marked untouched  
- [x] #25 / #26 preservation confirmed  
- [ ] User / project lead acknowledged recommendation (awaiting)

---

## Appendix

- Dependency Gate: `Issue_48_Dependency_Gate.md` (PASS; A1–A5)  
- **A1 refinement for Development:** “PAAGERAT owns PLAN+TYPE” means **PAAGERAT loader emits that TYPE** (PR/NF), not merely that PAAGERAT file contains the TYPE_CODE.  
- Related: #31, #37, #40, #41, #42
