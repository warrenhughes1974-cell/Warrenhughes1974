# Issue #42 — Intake Summary

**Issue:** #42 — Missing Rate Extract Rows (L01/L10)  
**Date (original):** 2026-07-08  
**Date (re-intake):** 2026-07-13  
**Framework stage:** Intake complete → Planning / Dependency Gate  
**Status:** Source received (PDAGE 20260713) — load-path still blocked  
**Owner:** Warren · **Assigned:** QLA (path/load) + CSO (remaining CV gaps)  
**Priority:** Conditional Go for Issue #42 NP/RV once Rate_Table or PDAGE path wires; No-Go for remaining CV gaps Eric listed  

---

## Client / business symptom (original)

Client-provided LifePRO screenshots show rate tables that were not present in the April delivered extracts.

| Gap | LifePRO ID | Rate type | Expected QLAdmin impact |
|-----|------------|-----------|-------------------------|
| L01 | `L01 10Y` / segment `L01 10Y LT` | `NP` | Plan `5L0110` — NP cannot load |
| L10 | `L10 LP9595` under `L10 LP95` | `NP` / `RV` | L10 family — NP/RV cannot load |

---

## Client update 2026-07-13 (Eric Scow)

1. **Updated Rate Tables** placed in LifePRO Extract zip on Teams (New Era folder). Files now in `QLA_Migration/Source/` dated **20260713**:
   - `PDAGE_AgeDuration_Rates_Extract_20260713.csv`
   - `PAAGERAT_AttainedAge_Rates_Extract_20260713.csv`
   - `PAAGE_AttainedAge_Rates_Extract_20260713.csv`
2. Eric notified New Era that **Age/Duration** rates still missing for:
   - `L17` **CV**
   - `960 LP85-8` **CV**
   - `960 LP85-8` (age/duration generally — see scan nuance below)
3. New Era stated they could **not** find NPs for `0824 P DTH` or `L10 GPO OL`. Eric asks if anything else is missing.

---

## Re-intake scan (2026-07-13 extracts)

Evidence: `Issue_Log_Items/Issue_42/evidence_20260713_rate_gap_scan.csv`  
Script: `Issue_Log_Items/Issue_42/_scan_20260713_rate_extracts.py`

### Issue #42 core — RESOLVED in PDAGE (not yet in Rate_Table)

| Coverage | Type | PDAGE 20260630 | PDAGE 20260713 | Rate_Table_Txt | PAAGERAT 20260713 |
|----------|------|---------------:|---------------:|---------------:|------------------:|
| `L01 10Y` | NP | 0 | **2,544** | 0 | 0 |
| `L01 10Y` | RV | 0 | **2,544** | 0 | 0 |
| `L10 LP9595` | NP | 0 | **6,192** | 0 | 0 |
| `L10 LP9595` | RV | 0 | **6,192** | 0 | 0 |

### Eric remaining / New Era “cannot find” — confirmed

| ID / type | PDAGE 20260713 | PAAGERAT 20260713 | Verdict |
|-----------|----------------|-------------------|---------|
| `L17` CV | 0 (NP=840, RV=840 present) | PR only | **CV still missing** (Eric correct) |
| `960 LP85-8` CV | 0 | PR only | **CV still missing** (Eric correct) |
| `960 LP85-8` NP/RV | **NP=1,128 / RV=1,128** | PR=284 | Age/duration NP+RV **arrived**; CV still the gap |
| `0824 P DTH` NP | absent | PR=22 only | Agree with New Era — **no NP** |
| `L10 GPO OL` NP | absent | PR=82 (new vs 630) | Agree with New Era — **no NP** (PR now present) |

---

## Suspected domain

**Rates / source extract** — not converter mapping for the original screenshot gaps. After this delivery, remaining work is **which file the rate loader reads** (`Rate_Table_Extract_Txt.txt` vs `PDAGE_…_20260713.csv`) and remaining CSO CV gaps.

---

## In scope / out of scope (first pass)

**In scope**
- Confirm L01/L10 LP9595 rows now exist in delivered extracts
- Plan load path so QuikNps / QuikTvs can emit for `5L0110` / L10 LP9595
- Answer Eric on remaining gaps

**Out of scope**
- Inventing NP for `0824 P DTH` / `L10 GPO OL` if LifePRO has none
- Issue #40/#41 CV inheritance logic
- Filling `L17` / `960 LP85-8` CV without CSO/New Era source rows

---

## Related issues

- #40 / #41 — CV inheritance / endpoint (closed implementation; separate)
- #48 — Secondary Rate_Table / PAAGERAT path wiring (`plan_source_paths.py` still prefers Rate_Table_Txt + PAAGERAT **20260630**)
- Master rate completeness / Segment References workbook (Issue_42 evidence CSVs)

---

## Immediate blockers

1. **Load path:** Converter production age/duration source is still `Rate_Table_Extract_Txt.txt` (no L01 10Y / L10 LP9595). New rows live in **PDAGE 20260713** only.
2. **PAAGERAT resolver** still prefers `…_20260630.csv`, not `…_20260713.csv`.
3. **CSO residual:** `L17` CV and `960 LP85-8` CV still absent from age/duration extract.

---

## Artifact inventory

| Artifact | Status |
|----------|--------|
| Eric emails 2026-07-13 | Received (Teams zip + remaining-gap note) |
| Source PDAGE/PAAGERAT/PAAGE 20260713 | Present under `QLA_Migration/Source/` |
| Rate_Table with L01/L10 LP9595 | **Missing** |
| Scan evidence CSV | Written |
| Example policies | None required for extract-presence issue (plan-level) |

---

## Owner / severity

- **Owner:** Both — CSO delivered PDAGE rows; QLA must wire/load; CSO still owns L17/LP85-8 CV
- **Severity:** No-Go for client UAT of L01 NP / L10 LP9595 until load path uses 20260713 age/duration data
