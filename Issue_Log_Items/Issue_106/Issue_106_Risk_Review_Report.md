# Issue #106 — Risk Review Report

**Issue:** #106 — RV Rates Off by One Duration (QuikTvs)  
**Framework stage:** Risk Agent (G3)  
**Status:** **GO** for Development (await explicit user approval)  
**Generated:** 2026-07-24  
**Agent:** Risk Agent (Cursor Grok 4.5, read-only)

**Status note:** Risk analysis only — no production code changes until “Approved for Development.”

---

## Go / No-Go Recommendation

**GO** — Defect is proven in Rate_Table vs current `QuikTvs.csv`. Root cause is the intentional non-CV `source − 1` left after CV-only fixes (#37/#41/#98). Surgical RV identity duration is low-ambiguity, matches Eric’s Dur1/Dur0 diagnosis, and must not reuse the CV first-duration matrix.

---

## 1. Is this actually an issue?

**Yes.** Values match; placement is wrong by one duration.

| Proof | LifePRO / source | Current QL | After identity |
|-------|------------------|------------|----------------|
| 170858 M/17 | Dur1=0, Dur2=8.76, Dur83=1000 | Dur1=8.76, Dur82=1000 | Dur1=0, Dur2=8.76, Dur83=1000 |
| 1659C2 M/17 SM | Dur1=1, Dur83=978 | Dur0=1, Dur82=978 | Dur1=1, Dur83=978 |

Applying CV remap to RV would **over-shift** (8.76 → Dur 3) and truncate terminal 1000 — **reject**.

---

## 2. Current vs proposed mapping

| Field / path | Current | Proposed | Change? |
|--------------|---------|----------|---------|
| RV duration | `source_duration_to_ql` → N−1 | `ql = source` | **Yes** |
| RV factor value | CHAR(7) format | unchanged | No |
| CV duration | `cv_remap_ql_duration` | unchanged | **No** |
| NP/DV/DB/PR duration | source−1 | unchanged | **No** |
| QuikPlTv keys | as today | unchanged | No |

---

## 3. Premium / related fields untouched

| Target | Touched? |
|--------|----------|
| quikridr.MPREM / MMODPREM (#26) | **No** |
| MPOLICY (#2/#25) | **No** |
| QuikCvs / CV first-duration (#37/#41/#98) | **No** |
| QuikNps / QuikDvs / QuikDbs / QuikGps | **No** |
| quikloan / claims | **No** |

---

## 4. Repo references

| Location | Role |
|----------|------|
| `qla_core/rate_dbf_schema.py` | `source_duration_to_ql`; TYPE_TO_TABLE RV→QuikTvs |
| `qla_core/rate_factor_loader.py` | Primary emit branch |
| `qla_core/rate_inheritance_loader.py` | Inherited RV |
| `qla_core/pdage_missfill.py` | Miss-fill RV |
| `qla_core/shared_rate_candidate_loader.py` | Shared RV |
| `QLA_Migration/Output/rates/QuikTvs.csv` | Before-state |
| `docs/670 GL85 Rates.docx` | Client screenshots |
| `docs/RV Factor Samples.docx` | Multi-form samples |
| `docs/QuikTvs_RsvReview_20260724.xlsx` | Client review book |
| Inheritance parity JSON | `1L1095` ← `L10 LP95` |

---

## 5. Population analysis

| Metric | Count |
|--------|------:|
| QuikTvs plans with rows (proof set) | 7+ named |
| 170858 / 17085M / 170588 pages | 986 each |
| 1659C2 pages | 2,128 |
| 221END pages | 476 |
| 1960OL pages | 1,015 |
| 1L1095 pages | 3,096 |
| Rows that would change (conceptually) | **All QuikTvs factor cells** shift +1 duration vs current Output |
| CV rows changed | **0** (must verify) |

### Breakdown (proof plans)

| Plan | Defect | After fix |
|------|--------|-----------|
| 170858, 17085M, 170588 | Dur −1 | Align to LifePRO |
| 1659C2, 221END, 1960OL | Dur −1 | Align to LifePRO |
| 1L1095 | Dur −1 **and** source = LP95 not LP9595 | Dur aligns to LP95; values still LP95 |

---

## 6. Fallback recommendation

| Option | Assessment |
|--------|------------|
| **A — RV identity (`ql = source`)** | **Recommended** — matches Eric + source |
| B — Apply CV FNZ/first-duration to RV | **Reject** — over-shifts GL85 proof |
| C — Change global `source_duration_to_ql` for all non-CV | **Reject this issue** — expands blast to NP/DV/DB/PR without proofs |
| D — Plan-specific hardcodes for named forms only | **Reject** — fleet-wide QuikTvs uses same helper |

**Recommended:** Option A only.

---

## 7. Trace policies / plans

| Plan | Before (M/17 key cell) | Proposed | Pass criteria |
|------|------------------------|----------|---------------|
| 170858 | TV Dur1=8.76 | Dur2=8.76; Dur83=1000 | Match Rate_Table + screenshots |
| 1659C2 SM | Dur0=1; Dur82=978 | Dur1=1; Dur83=978 | Match Rate_Table + samples docx |
| 221END / 1960OL | −1 pattern | identity | Match samples docx |
| 1L1095 | Dur1=4.45 (= LP95 Dur2) | Dur2=4.45; document LP95 source | Eric can research LP95 |

---

## 8. `1L1095` / L10 LP9595 (client question)

| Question | Finding |
|----------|---------|
| Where do QLAdmin `1L1095` RV rates pull from? | LifePRO segment **`L10 LP95`** (Rate_Table), emitted as plan `1L1095` |
| Why don’t L10 LP9595 samples match? | **0** Rate_Table rows for LP9595 in delivered extract |
| Will Dur fix make LP9595 match? | **No** — wrong source ID; need extract or different mapping decision |

Reply to Eric should state LP95 lineage explicitly (draft in session readout).

---

## 9. Residual risks

| Risk | Mitigation |
|------|------------|
| Entire QuikTvs UAT load looks “shifted” vs prior QLAdmin load | Expected; reload Test_Validation QuikTvs; communicate Dur0→Dur1 convention |
| Inheritance paths miss helper | Touch all four emit loaders |
| CNTL paging edge at high durations | Identity keeps Dur83 on page 08 / TV3; re-proof terminals |
| Accidental CV change | Diff QuikCvs row counts/hashes in Validation |

---

## 10. Gates

| Gate | Result |
|------|--------|
| G0 Intake | **PASS** |
| G1 Planning | **PASS** |
| G2 Dependency | **PASS** |
| G3 Risk | **GO** — wait for Development approval |

---

## Ask

Reply **“Approved for Development”** to proceed with RV identity duration implementation + Validation.
