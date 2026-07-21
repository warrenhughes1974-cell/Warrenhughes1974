# Issue #48 — Validation Report

**Issue:** #48 — Secondary Rate File (PAAGERAT fallback)  
**Framework stage:** Validation Agent (G5)  
**Engine:** **v57.69**  
**Date:** 2026-07-10  
**Result:** **PASS**

---

## Commands run

```text
python QLA_Migration/_validate_issue48_secondary_rate.py
→ ALL CHECKS PASSED (v57.69 path wiring)
```

---

## Acceptance checklist (Risk §11)

| Check | Result |
|-------|--------|
| Path resolve → Source `Rate_Table_Extract_Txt.txt` | **PASS** |
| Source `.txt` MD5 = twin `Rate_Table_Extract_20260427.csv` | **PASS** (0 content delta) |
| `paagerat_extract()` → Source `…_20260630.csv` | **PASS** |
| Config `source_rate_extract` points at Source `.txt` | **PASS** |
| `7619PU` RV / `A96DAR` NP not suppressed | **PASS** (keys still in Rate_Table) |
| DISCHO25 / L01 10Y MA PR still present | **PASS** |
| #42 gaps still absent | **PASS** |
| No Issue #48 artifacts in `Output/` | **PASS** |
| Secondary audit written under `Issue_48/evidence/` | **PASS** (158 cov+TYPE rows) |

---

## Trace / coverage results

| Key | Expected | Result |
|-----|----------|--------|
| Resolved Rate_Table path | Source `.txt` | Pass |
| Content vs prior twin | Identical bytes | Pass |
| PAAGERAT path | Source 20260630 | Pass |
| PAAGERAT key set vs prior 20260428 | Same keys / same row count (0 key delta) | Pass |
| #42 `L01 10Y` NP / `L10 LP9595` | Still missing | Pass |

No client policy examples were in scope (G2 waiver A5).

---

## Did we add rates that were not already in PAAGERAT?

### Short answer

**No — Issue #48 did not add any new rate content.**

The secondary file is the same Rate_Table extract the pipeline already used (byte-identical twin). Wiring it from `Source/` does not introduce rates that were not already available on the Rate_Table path.

### Detail

| Question | Answer |
|----------|--------|
| New Rate_Table rows from #48? | **0** — MD5 match to prior twin |
| New PAAGERAT keys from Source 20260630 vs prior 20260428? | **0** key / row-count delta |
| Shared TYPE keys in Rate_Table but not exact in PAAGERAT? | **158** cov+TYPE (CV/NP/RV/PR/DB/NF) |
| Were those 158 already Rate_Table-sourced before #48? | **Yes** — Rate_Table was already streamed by `rate_pipeline` |
| Did #48 newly load those because PAAGERAT lacked them? | **No** — path rename/prefer only; dual-stream behavior unchanged |

**PR coverages present in Rate_Table but not as exact PAAGERAT cov+TYPE** (pre-existing Rate_Table authority, not new from #48):

`665 STME95`, `DISCHO20 B`, `DISCHO2475`, `DISCHO247B`, `DISCHO247C`, `DISCHO25`, `DISCHO29`, `DISCHO70`, `DISCHO80`, `DISCHO90`, `L01 10Y MA`

PAAGERAT remains the attained-age authority for its own PR/NF/BP/U5/U6 segment rows (109+ shared-type PAA-only keys at exact ID grain). Those were already on the PAAGERAT path.

Evidence: `evidence/issue48_paagerat_miss_rate_table_secondary_audit.csv`

---

## Untouched fields / surfaces

| Surface | Check | Result |
|---------|-------|--------|
| Policy tables / #25 / #26 | Out of scope; not modified | Pass |
| CV/NP/RV/DB suppress | Not implemented | Pass |
| #31 ISWL allowlists | Untouched | Pass |
| #42 missing rows | Still absent | Pass |

---

## Row counts (source)

| Source | Rows |
|--------|-----:|
| Rate_Table (Source `.txt`) | 1,128,984 |
| PAAGERAT (Source 20260630) | 24,424 |
| Emit delta from #48 path wiring | **0** (expected) |

---

## G5 gate: **PASS**

**Next:** Regression Agent (G6).
