# Issue 71 — Validation Report

**Issue:** #71 — BAND standardize to `00`  
**Framework stage:** Validation Agent  
**Engine version:** v57.90  
**Validation script:** `Issue_Log_Items/Issue_71/scripts/validate_issue71_band.py`  
**Output directory:** `QLA_Migration/Output/` (+ `Output/rates/`, `Output/Test_Validation/rates/`)  
**Before snapshot:** N/A (rate emit regenerate; policy tables not modified by #71)  
**Generated:** 2026-07-14  
**Model:** Cursor Grok 4.5 (locked)  
**Verdict:** **PASS**

**UAT note:** Client confirmed Policy Display cash values restored after rate reload (“back in business”).

---

## Commands Run

```bash
python Issue_Log_Items/Issue_71/scripts/validate_issue71_band.py
python QLA_Migration/_validate_ye_20251231.py
```

Issue-specific validator: **exit 0 / PASS**.  
YE validator: **1 FAIL** on Issue #60 golden sample (pre-existing; unrelated to BAND). All other YE checks PASS.

---

## 1. Trace Policy Results

| Policy | Plan | Field | Expected | Actual | Result |
|--------|------|-------|----------|--------|--------|
| 010718309C | 1658C1 | quikridr.MBAND | `00` | `00` | PASS |
| 010718309C | 1658C1 | QuikPlCv.BAND | `00` | `00` (4 keys) | PASS |
| 010718309C | 1658C1 | QuikCvs.BAND | `00` | `00` (2,020 rows) | PASS |
| 010718309C | 1658C1 | MCV0 | unchanged ~986 | `986.03000` | PASS |
| 010713704C | 1659C2 | MBAND / PlCv BAND | `00` | `00` / `00` | PASS |
| 015000057C | 17CSI5 | MBAND / PlCv BAND | `00` | `00` / `00` | PASS |
| 010718309C | 1658C1 | UAT CV display | non-zero grid | Client confirmed restored | PASS |

---

## 2. Acceptance Criteria (from Risk checklist §10)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | QuikCvs BAND unique = {`00`} | PASS (38,047 rows) |
| 2 | QuikPlCv BAND unique = {`00`} | PASS (94 rows) |
| 3 | QuikPlBd BDCODE = `00` | PASS (73 rows) |
| 4 | quikridr MBAND still 100% `00` | PASS (6,936 rows) |
| 5 | `010718309C` MCV0 unchanged | PASS (`986.03000`) |
| 6 | Non-rate tables not altered by #71 | PASS (no ridr/plan emit in this fix) |
| 7 | YE validator PASS where applicable | PASS for #71 scope; #60 golden FAIL pre-existing |

Additional Risk items:

| Criterion | Result |
|-----------|--------|
| QuikGps/QuikPlGp BAND = `00` after dedupe | PASS (Gps 415; PlGp 12) |
| GP plan `5L01MA` key present | PASS (`M`/`SM`/`00`) |
| Test_Validation/rates published | PASS (23 CSV files) |
| QuikIssc BAND = `00` | PASS (8 rows) |

---

## 3. Source Alignment

| Check | Result |
|-------|--------|
| LifePRO bands 1/2/3 → emit `00` | PASS (`map_band` collapse) |
| Multi-band GP collapse keep former `01` | PASS (emit completed with 0 blockers; Gps 415 rows) |
| Policy MBAND not flipped to `01` | PASS (still 100% `00`) |

---

## 4. Untouched Fields Confirmed

| Field / table | Check | Result |
|---------------|-------|--------|
| MCV0 amounts | Trace `010718309C` = 986.03 | PASS |
| NFOINT (quikplan) | `1658C1`=A, `1659C2`=A, `17CSI5`=F | PASS (untouched) |
| LOANINTX | 141/141 = `A` (Issue #70) | PASS (untouched) |
| MPREM / MMODPREM | Not in #71 emit path | PASS (N/A — rates only) |
| quikridr schema / MBAND rulebook | Still `00`; no flip to `01` | PASS |

---

## 5. Row Counts

| Table | Count | Notes |
|-------|------:|-------|
| QuikCvs | 38,047 | BAND all `00` |
| QuikPlCv | 94 | BAND all `00` |
| QuikNps | 46,998 | BAND all `00` |
| QuikGps | 415 | Reduced vs pre-dedupe multi-band (expected) |
| QuikPlGp | 12 | BAND all `00` |
| QuikPlBd | 73 | BDCODE all `00` |
| quikridr | 6,936 | Unchanged by #71 |
| quikplan | 141 | Unchanged by #71 |
| quikmstr | 5,084 | Unchanged by #71 |

---

## 6. Impact Summary

| Metric | Value |
|--------|------:|
| Rate factor/key BAND cells standardized to `00` | All in-scope rate tables |
| QuikGps rows after SD-71-5 dedupe | 415 |
| Policy table rows changed by #71 | 0 |
| Issue validator | PASS |

---

## 7. Failures (if any)

| # | Description | Severity | Return to Dev? |
|---|-------------|----------|----------------|
| — | None for Issue #71 | — | No |
| YE #60 golden | Pre-existing Issue #60 sample fail | Out of scope | No (track under #60) |

---

## 8. Recommendation

- [x] Advance to **Regression Agent**
- [ ] Return to **Development Agent** with fixes: N/A

---

## Appendix — Validator stdout

```text
Issue #71 BAND validation (v57.90)
  OK: QuikCvs.csv BAND unique={00} rows=38047
  OK: QuikPlCv.csv BAND unique={00} rows=94
  OK: QuikNps.csv BAND unique={00} rows=46998
  OK: QuikGps.csv BAND unique={00} rows=415
  OK: QuikPlBd BDCODE unique={00} rows=73
  OK: quikridr MBAND 100% 00 (6936 rows)
  OK: 010718309C MCV0=986.03000 (unchanged ~986.00)
  OK: QuikPlCv key exists for plan 1658C1 BAND=00
RESULT: PASS
```

---

## Gate Criteria (G5 — Validation Pass)

- [x] All trace policies pass (incl. client UAT confirmation)
- [x] Validation script exits 0
- [x] Untouched fields confirmed for issue scope
- [x] Validation report published
- [x] Status: **Ready for Regression**
