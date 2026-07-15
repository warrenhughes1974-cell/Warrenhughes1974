# Issue #71 — Risk Review Report

**Issue:** #71 — BAND standardize to `00`  
**Framework stage:** Risk Agent  
**Status:** **Conditional Go → Ready for Development**  
**Generated:** 2026-07-14  
**Model:** Cursor Grok 4.5 (locked)  
**Status note:** Risk analysis only — no production code changes.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Safe to implement band→`00` on single-band CV/NPS/TVS/key tables (fixes Policy Display lookup). Condition: QuikGps/QuikPlGp multi-band collapse uses keep-former-`01` dedupe (SD-71-5) and UAT checks GP plan `5L01MA` peers.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| quikridr.MBAND | `00` (6,936/6,936) | `00` | **No** |
| QuikCvs.BAND | `01` (38,047) | `00` | **Yes** |
| QuikNps/Tvs/Nff/… BAND | `01` | `00` | **Yes** |
| QuikPlCv/PlTv/… BAND | `01` | `00` | **Yes** |
| QuikGps.BAND | `01`/`02`/`03` | `00` + dedupe | **Yes** |
| QuikPlBd.BDCODE | `01` (+rare 02/03) | `00` | **Yes** |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| MPREM / MMODPREM | **No** |
| MPOLICY padding | **No** |
| MCV0 amounts | **No** |
| NFOINT / LOANINTX | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `qla_core/rate_dbf_schema.py` `map_band` / `BAND_MAP` | Primary emit transform |
| `rate_factor_loader.py` / `rate_key_setup.py` | Consumers |
| `rate_member_setup.py` | QuikPlBd |
| `Sync_Rulebook_quikridr.csv` MBAND | Already correct — do not flip to 01 |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| quikridr already MBAND=00 | 6,936 |
| QuikCvs rows to remap 01→00 | 38,047 |
| Other single-band factor rows (approx) | ~115k+ |
| QuikGps rows with collision if naïve remap | 1,080 |
| QuikPlGp collision keys | 3 |

### Breakdown

| Table class | Action | Collision risk |
|-------------|--------|----------------|
| CV/NPS/TVS/NFF/COI/DBS/DVS + Pl* keys | Remap 01→00 | **None** |
| QuikGps / QuikPlGp | Remap + drop dup keys (keep ex-01) | **Managed** |
| QuikPlBd | BDCODE→00 | Low |

---

## 5. Fallback Recommendation

| Option | Assessment |
|--------|------------|
| A. Remap rates to `00` (recommended) | Aligns with Chris policy band |
| B. Flip policies to `01` | **Reject** — contradicts Chris / rulebook |
| C. Dual-emit 00 and 01 keys | Reject — doubles tables; user asked for zero only |

**Recommended:** Option A + SD-71-5 GP dedupe.

---

## 6. Trace Policies

| Policy | Before (rate BAND) | Proposed | MBAND | Pass criteria |
|--------|-------------------|----------|-------|---------------|
| 010718309C | 01 | **00** | 00 | Keys align; MCV0 still ~986; after Data Admin, Cash Values ≠ all 0.00 |
| 010713704C | 01 | **00** | 00 | same class |
| 015000057C | 01 | **00** | 00 | same class |

---

## 7. Top Changes

| Change | Magnitude |
|--------|-----------|
| QuikCvs BAND value | 38,047 cells `01`→`00` |
| QuikGps row count | Reduce after dedupe (drop ~ex-02/03 duplicates) |

---

## 8. Regression Surfaces

| Surface | Risk | Check |
|---------|------|-------|
| #25/#26/#54/#60 Track A | Low | No ridr field edits except verify MBAND stays 00 |
| Traditional CV calc | Improves | Lookup match |
| CRVM blank NFOINT plans | Unchanged | Still need #60 Track B for $ |
| GP multi-band products | Medium | UAT `5L01MA` |
| Test_Validation partial publish | Med | Must publish **rates/** package |

---

## 9. Recommended Development Agent Task (exact)

**Switch to Composer 2.5.** Then:

1. Surgical normalize: all rate factor/key `BAND` → `00` at emit (prefer centralized post-map in rate pipeline / `map_band` policy for this book — **do not** change quikridr to 01).  
2. QuikPlBd → `BDCODE=00`, label NOT APPLICABLE.  
3. QuikGps/QuikPlGp: after `00`, drop duplicate keys keeping former `01` row content.  
4. Bump `APP_VERSION` both app.py if engine touched.  
5. Regen rates; publish `Test_Validation/rates` (+ quikplan/ridr only if changed).  
6. Add/extend validator: QuikCvs/QuikPlCv BAND all `00`; `010718309C` MBAND=`00` and matching rate key exists.  

**Do not** invent NFOINT or touch LOANINTX.

---

## 10. Validation / Regression Checklist

- [ ] QuikCvs BAND unique values = {`00`}  
- [ ] QuikPlCv BAND unique values = {`00`}  
- [ ] QuikPlBd BDCODE = `00`  
- [ ] quikridr MBAND still 100% `00`  
- [ ] `010718309C` MCV0 unchanged  
- [ ] Non-rate tables row counts unchanged  
- [ ] YE validator still PASS where applicable  

---

## Gate Criteria (G3)

- [x] Go/Conditional Go issued  
- [x] Impact quantified  
- [x] Fallback chosen  
- [x] Dev task surgical and explicit  
- [x] **No code in this stage**  
