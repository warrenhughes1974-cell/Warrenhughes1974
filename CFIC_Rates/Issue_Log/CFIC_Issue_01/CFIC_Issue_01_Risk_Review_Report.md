# CFIC Issue #01 — Risk Review Report

**Issue:** CFIC #01 — Green-Sheet Non-Forfeiture / Reserve Rate Extraction  
**Framework stage:** Risk Agent (G3)  
**Status:** **CONDITIONAL GO** — Wave 1 extract pilot approved pending explicit Development approval; Wave 3 QLAdmin emit **NO-GO**  
**Fallback simulated:** Yes — wave-scope / Warren-isolation / OCR blast-radius simulation  
**Generated:** 2026-07-11  
**Agent:** Risk Agent — read-only review (no production code in this stage)  
**Script:** `CFIC_Rates/Issue_Log/CFIC_Issue_01/scripts/risk_review_cfic_issue01.py`

**Status note:** Risk analysis only — no production code changes unless later approved.

---

## Go / No-Go Recommendation

**CONDITIONAL GO (Wave 1 only)** — Approve Development for **P7MN extract pilot** (3 PDFs: ages 18, 30, 50) producing staging CSV under `CFIC_Rates/extracted_green_sheets/`. **Zero Warren blast radius** by design.

**NO-GO (Wave 3 QLAdmin emit)** until **OBQ-1** (factor basis) and **OBQ-2** (rate-key assumptions) are resolved. Do not load `QuikCvs` / `QuikTvs` / `QuikNps` into any Citizens or Warren QLAdmin environment before those gates clear.

**NO-GO (full 1,104-PDF OCR)** until Wave 1 validation passes (≥99.5% spot-check accuracy, CV checkpoint parity).

**Architecture (locked SD-1):** One-time standalone extract — **no `app.py` changes**, no batch integration. Scripts run manually; output is a Citizens QLAdmin load package under `CFIC_Rates/output/rates/`.

---

## 1. Current vs Proposed Mapping

| Concern | Current (before) | Proposed (Wave 1) | Proposed (Wave 3, blocked) | Change? |
|---------|------------------|-------------------|----------------------------|---------|
| CFIC green-sheet rates in QLAdmin | **None loaded** | Staging CSV only (`extracted_green_sheets/`) | `QuikCvs`, `QuikTvs`, `QuikNps` + key tables under `CFIC_Rates/output/rates/` | **Yes** (future) |
| Warren `QLA_Migration/Output/quik*.csv` | Production conversion tables | **Unchanged** | **Unchanged** | **No** |
| Warren `app.py` / rulebooks | v57.76 conversion engine | **Unchanged** | **Unchanged** | **No** |
| Access Proposal Maker CSVs | Premium + sparse illustration checkpoints | Parity reference only | Parity reference only | **No** |
| Source authority | PDF green sheets (not yet extracted) | OCR → staging | Staging → QLAdmin emit | **Yes** (CFIC track only) |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| Warren `quikmstr` / `quikridr` / all policy tables | **No** |
| Warren `QLA_Migration/Output/` | **No** |
| Warren `app.py` / Sync rulebooks | **No** |
| Issue #25 MPOLICY padding | **No** (N/A — no policy keys) |
| Issue #26 `quikridr.MPREM` / `MMODPREM` | **No** (N/A — no premium mapping) |
| Warren rate pipeline (`rate_pipeline.py`, Issue #37/#40/#41 CV) | **No** |
| Access `extracted/*.csv` premium tables | **No** (deferred to future CFIC #02) |

---

## 3. Repo References

| Location | Role | Wave 1 touch? |
|----------|------|---------------|
| `CFIC_Rates/CFIC_Cash_Values/` | Source PDF archive (read-only) | Read only |
| `CFIC_Rates/extracted_green_sheets/` | Staging output (new) | **Yes — write** |
| `CFIC_Rates/Issue_Log/CFIC_Issue_01/scripts/` | Pilot OCR / validation scripts | **Yes — new scripts** |
| `CFIC_Rates/output/rates/` | QLAdmin draft emit | **No** (blocked) |
| `qla_core/rate_dbf_schema.py` | Schema reference for future emit | Read only |
| `QLA_Migration/` (entire tree) | Warren conversion | **No** |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| Total extractable PDFs (program) | 1,104 |
| Product folders | 37 |
| Crosswalk exact match | 35 |
| Crosswalk missing (`R69G`, `Table of Days`) | 2 |
| **Wave 1 pilot PDFs** | **3** |
| **Wave 1 est. staging rows** | **~165** |
| **Wave 1 est. Quik rows per family** | **~16** (if emit were allowed — it is not) |
| **Wave 2 P7* PDFs** | **252** |
| **Wave 2 est. staging rows** | **~13,860** |
| **Full program est. staging rows** | **~55,000–72,000** |
| **Warren QLA output row delta (all waves)** | **0** |

### Wave impact summary

| Wave | PDFs | Est. staging rows | QLAdmin emit | Warren delta |
|------|-----:|------------------:|--------------|-------------:|
| Wave 1 — P7MN pilot | 3 | 165 | **No** | 0 |
| Wave 2 — P7* family | 252 | ~13,860 | **No** (until validation + OBQ) | 0 |
| Wave 3 — full program | ~1,102 | ~55k–72k | **Blocked** (OBQ-1, OBQ-2) | 0 |

Evidence: `evidence/cfic_issue01_risk_impact_summary.csv`

### Rollout complexity tiers

| Tier | Products | Risk note |
|------|----------|-----------|
| `standard_p7_p9` | 4 (P7* in dedicated zips) | **Lowest risk** — pilot target |
| `standard` | 10 | Medium — age_pdf naming |
| `high_expiry_age` | 1 (`802M`) | High — age key ambiguity (OBQ-5) |
| `high_all_ages` | 3 (`1015`, `101G`, `101M`) | High — multi-age single PDF |
| `high_consolidated` | 18 | **Highest** — mega-sheets (OBQ-6) |

Evidence: `evidence/cfic_issue01_risk_rollout_tiers.csv`

---

## 5. Fallback Recommendation

| Option | Scope | Warren delta | Assessment |
|--------|-------|-------------:|------------|
| **A. Wave 1 staging only (recommended)** | P7MN × 3 ages | 0 | **Recommended** — proves OCR without QLAdmin risk |
| B. Skip OCR; hand-key P7MN | 3 PDFs | 0 | **Reject** — not scalable; use only for spot-check |
| C. Full 1,104 PDF OCR now | All products | 0 | **Reject** — unvalidated blast radius |
| D. Emit QuikCvs without OBQ-2 assumptions | CFIC plans | 0 Warren / **high Citizens** | **Reject** — QLAdmin load will fail or mis-price |
| E. Merge CFIC output into Warren `QLA_Migration/Output/` | Combined load | **Non-zero** | **Reject** — violates CFIC scope; cross-contamination |
| F. LLM vision on full corpus without template | All PDFs | 0 | **Reject** — uncontrolled numeric drift |

**Recommended fallback:** Option **A**. If Wave 1 OCR fails accuracy gate, retry with alternate OCR engine (Azure DI / Tesseract template) before expanding scope — do not proceed to Wave 2.

---

## 6. Trace Policies (plan/age checkpoints)

No client policies provided. Plan/age traces for Wave 1 validation:

| Trace key | Access PL7 checkpoint | Green-sheet (Wave 1 OCR) | Pass criteria |
|-----------|----------------------|--------------------------|---------------|
| P7MN / age 18 / M / NS / DUR 10 CV | `CashValueIn10` = 21 | OCR `cash_value` @ DUR=10 | Exact match |
| P7MN / age 18 / M / NS / DUR 20 CV | `CashValueIn20` = 84 | OCR `cash_value` @ DUR=20 | Exact match |
| P7MN / age 18 / M / NS / paid-up DUR 10 | `PaidUpIn10` = 197 | OCR `paid_up` @ DUR=10 | Exact match |
| P7MN / age 30 / M / NS / DUR 10 CV | Access row TBD | OCR | Exact match |
| P7MN / age 50 / M / NS / DUR 10 CV | Access row TBD | OCR | Exact match |

**Authority rule (pending OBQ-8):** Treat green sheets as authoritative for full grids; Access is parity checkpoint only.

---

## 7. OCR Error Blast Radius

| Scenario | Cells in scope | Est. errors @ 0.5% | Impact if emitted |
|----------|---------------:|-------------------:|-------------------|
| Wave 1 pilot | ~1,485 (165 rows × 9 cols) | ~7 | **Contained** — staging only; caught by spot-check |
| Wave 2 P7* | ~124,740 | ~624 | **High** if emit without audit |
| Full program | ~500k–650k | ~2,500–3,250 | **Critical** if emit without tiered rollout |

**Mitigation:** Mandatory `evidence/cfic_issue01_ocr_audit.csv` with 20-cell spot-check per column before Wave 2 approval. Rows below confidence threshold quarantined, not emitted.

---

## 8. Material Calculation Impact

| Phase | Citizens QLAdmin impact | Warren impact |
|-------|-------------------------|---------------|
| Wave 1 (staging) | **None** — no QLAdmin load | **None** |
| Wave 3 (emit, when approved) | **New rate tables** for ~35 CFIC plans — CV/reserve/paid-up calculations change for Citizens WL policies on those plans | **None** if scoped to `CFIC_Rates/output/rates/` |
| Accidental Warren merge | N/A | **Severe** — would contaminate LifePRO conversion load package |

Wave 3 is intentional new rate content for Citizens — not a correction of existing Warren rates. The risk is **loading wrong OCR values**, not **changing unrelated plans**.

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserved** — out of scope |
| Issue #26 MPREM / MMODPREM | **Preserved** — out of scope |
| Warren rate pipeline (#37/#40/#41) | **Preserved** — no shared emit path in Wave 1 |
| CFIC/Warren output isolation | **Required** — hard scope rule |

---

## 10. Regression Testing Checklist (for Validation Agent)

### Wave 1 (required before Wave 2)

- [ ] P7MN ages 18, 30, 50: header plan/age matches filename (100%)
- [ ] Duration sequence complete — no gaps in DUR 1…n
- [ ] OCR spot-check: ≥99.5% accuracy across 20 cells × 9 columns per age
- [ ] CV parity: DUR 10 and DUR 20 vs Access `PermaLife7AdultBefore.csv` (Male, No, matching age)
- [ ] Paid-up parity at DUR 10 vs Access checkpoint
- [ ] Low-confidence rows flagged in `ocr_audit.csv` — none silently dropped
- [ ] Warren `QLA_Migration/Output/` — `git diff` shows **zero** changes
- [ ] No files written outside `CFIC_Rates/`

### Wave 3 (future, when OBQ cleared)

- [ ] `QuikCvs` / `QuikTvs` / `QuikNps` schema vs `rate_dbf_schema.py`
- [ ] CHAR(7) factor width — no overflow rows
- [ ] `QuikPlCv` / `QuikPlTv` key rows present per plan
- [ ] Citizens sandbox import smoke test
- [ ] Warren regression batch unchanged

---

## 11. Recommended Development Agent Task

**Approve Wave 1 only** (Composer 2.5):

1. Create `CFIC_Rates/extracted_green_sheets/staging/P7MN/` output folder
2. Build layout-aware OCR script for `P7MN/18.pdf`, `30.pdf`, `50.pdf` — extract **all 9 body columns** + header fields
3. Write wide staging CSV per Planning schema
4. Produce `evidence/cfic_issue01_ocr_audit.csv` with manual spot-check template
5. Compare CV/paid-up at DUR 10 and 20 vs Access `PermaLife7AdultBefore.csv`

**Do NOT:**
- Modify `QLA_Migration/app.py`, root `app.py`, or any Warren rulebook
- Integrate into batch converter or `rate_pipeline.py` (one-time extract only — see `CFIC_Issue_01_Scope_Decisions.md` SD-1)
- Write to `QLA_Migration/Output/`
- Emit `QuikCvs.csv` or any QLAdmin table
- Process PDFs beyond the 3-file pilot
- Bump Warren `app.py` version

**Validation script (future):** `scripts/validate_cfic_issue01_p7mn_pilot.py`

---

## 12. Gate G3 — Risk Approved

| Slice | Recommendation |
|-------|----------------|
| Wave 1 — P7MN extract pilot | **Conditional Go** |
| Wave 2 — P7* family | **No-Go** until Wave 1 validation pass |
| Wave 3 — QLAdmin emit | **No-Go** until OBQ-1 + OBQ-2 + Wave 2 validation |
| Warren conversion | **No-Go for any changes** |

- [x] Risk report published with Go/No-Go
- [x] Impact quantified (wave simulation)
- [x] Unrelated Warren fields marked untouched
- [x] #25 / #26 preservation confirmed (N/A)
- [ ] User explicit Development approval — **pending**

---

## 13. Recommended next prompt

```
CFIC Issue #01 Wave 1 is approved for Development.

Switch to Composer 2.5. Scope: CFIC_Rates/ only.
Build P7MN OCR extract pilot (ages 18, 30, 50) → staging CSV.
Do NOT touch QLA_Migration/app.py or Warren Output.
Add validation script and OCR audit evidence.
```

**Parallel client action:** Answer OBQ-1 and OBQ-2; schedule Access walkthrough §4–§5.

---

## Appendix

| Artifact | Path |
|----------|------|
| Risk simulation script | `scripts/risk_review_cfic_issue01.py` |
| Wave impact summary | `evidence/cfic_issue01_risk_impact_summary.csv` |
| Rollout complexity tiers | `evidence/cfic_issue01_risk_rollout_tiers.csv` |
| Open business questions | `CFIC_Issue_01_Open_Business_Questions.md` |
| Dependency gate | `CFIC_Issue_01_Dependency_Gate.md` |
