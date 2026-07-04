# Issue #38 — Planning Report

**Issue:** #38 — Dividend Accumulations  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning complete — proceed to Dependency Gate  
**Generated:** 2026-07-03  
**Engine analyzed:** `app.py` / `QLA_Migration/app.py` (current batch output)  
**Agent:** Planning Agent (read-only research)

---

## 1. Executive finding

**Confirmed defect:** Every policy in `quikdvdp.csv` has **`MDEPOSIT = 0.00`**, including **59 policies** where LifePRO **`PPBENTYP.ACCUM_DIVIDENDS` > 0**. The rulebook already maps that field to `MDEPOSIT`, but a post-processing enrichment step **overwrites the balance to zero** when the PACTG transaction cache does not contain the policy.

**Confirmed secondary defect:** The transaction cache never loads because the code hardcodes **`PACTG_Accounting_Extract20260427.csv`**, which is **not in Source** (available file: **`PACTG_Accounting_Extract20260530.csv`**).

**Recommended direction (Planning):** **Option B — Preserve PPBENTYP authority.** Stop zeroing `MDEPOSIT` on cache miss; treat **`ACCUM_DIVIDENDS`** as the balance source per existing rulebook. Fix PACTG file resolution for optional interest-side fields only. **Do not** sum PACTG account 514 transactions as the accumulation balance — that is transaction activity, not the point-in-time balance LifePRO stores on PPBENTYP.

**Go/no-go for next stage:** **Proceed to Dependency Gate** with **conditional scope** — balance fix (Track A) can advance; interest YTD/date fields (Track B) blocked until PEVNTNONFC or client-approved PACTG fallback.

---

## 2. Confirmed LifePRO source table/file(s)

| Source table | File in Source/ | In package? | Row count (benefit seq 1) |
|--------------|-----------------|-------------|--------------------------:|
| **PPBENTYP** — Benefit Type | `PPBENTYP_BenefitType_Extract_20260530.csv` | Yes | 5,083 |
| **PACTG** — Accounting (optional enrichment) | `PACTG_Accounting_Extract20260530.csv` | Yes | ~205k+ tx rows |
| **PEVNTNONFC** — Non-forfeiture events | *(none)* | **No** | — |
| **PPBEN** — Plan code join | `PPBEN_PolicyBenefit_Extract_20260530.csv` | Yes | used for plan breakdown |

### Available source fields (Track A — balance)

| Field | Column | Populated (seq 1) | Notes |
|-------|--------|------------------:|-------|
| Policy number | `POLICY_NUMBER` | 100% | Join via `Master_Crosswalk.csv` |
| Benefit filter | `BENEFIT_SEQ` | seq `1` only emitted | Engine filters to seq 1 |
| **Accumulation balance** | **`ACCUM_DIVIDENDS`** | **59 policies > 0** | Authoritative balance per rulebook |
| Dividend option | `DIVIDEND` | populated | Value `3` = accumulation on affected policies |
| Non-forfeiture | `NON_FORFEITURE` | populated | |
| Dividends credited (lifetime) | `DIVIDENDS_CREDITED` | populated | Not mapped to quikdvdp today |

### Available source fields (Track B — interest YTD/date)

| Field | Column | Status |
|-------|--------|--------|
| Accrued interest YTD | `DV_ACCRU_INT` | Rulebook → `MINTYTD`; source table **PEVNTNONFC missing** |
| Interest paid-to date | `DV_INT_PD_TO_DATE` | Rulebook → `MINTDATE`; **PEVNTNONFC missing** |
| PACTG interest credits | `DEBIT_CODE = 641` | Present in PACTG; engine partially uses for cache YTD |

---

## 3. Confirmed QLAdmin target structure

From `validation_config/schema_manifest.json` and Issue #21D UAT precedent:

| Table | Field | QLAdmin meaning (business) | Type / format |
|-------|-------|---------------------------|---------------|
| **quikdvdp** | `MPOLICY` | Policy key | CHARACTER(10), crosswalk + #25 padding |
| **quikdvdp** | **`MDEPOSIT`** | **Dividend Accumulations balance** | Money `9999999.99` |
| **quikdvdp** | `MINTYTD` | Dividend accumulation interest YTD | Money |
| **quikdvdp** | `MDEPINT` | Dividend Accum Int Rate (percent) | Numeric; #21D ISWL override |
| **quikdvdp** | `MINTDATE` | Interest paid-to / last credit date | Date `YYYYMMDD` |

**Repo references:**

| Location | Role |
|----------|------|
| `QLA_Migration/Configs/Sync_Rulebook_quikdvdp.csv` | Maps `ACCUM_DIVIDENDS` → `MDEPOSIT` |
| `QLA_Migration/app.py` ~5477–5535 | PACTG cache build (hardcoded filename) |
| `QLA_Migration/app.py` ~6131–6150 | Enrichment overwrites `MDEPOSIT` |
| `qla_core/lifepro_source_resolver.py` | Pattern for dynamic PACTG resolution (used elsewhere) |
| `Issue_Log_Items/Issue_21/Issue_21D/` | Confirms QLAdmin reads dividend deposit fields from **quikdvdp** |

---

## 4. Required source-to-target field mapping

### Track A — Balance (recommended for Issue #38 close)

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PPBENTYP | `POLICY_NUMBER` | `MPOLICY` | Crosswalk + `format_qladmin_mpolicy()` (#25) | No |
| PPBENTYP | **`ACCUM_DIVIDENDS`** | **`MDEPOSIT`** | Strip spaces; `float` → `{:.2f}`; **preserve on emit** | **Yes — stop overwrite** |
| Rulebook default | — | `MDEPINT` | 4.00 fallback; ISWL allowlist 4.50 (#21D) | No |
| PPBENTYP filter | `BENEFIT_SEQ = 1` | one row per policy | Existing filter | No |

### Track B — Interest YTD / date (deferred unless client requires in same release)

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PEVNTNONFC | `DV_ACCRU_INT` | `MINTYTD` | Money format | Blocked — no extract |
| PEVNTNONFC / PPOLC | `DV_INT_PD_TO_DATE` / paid-to | `MINTDATE` | `YYYYMMDD`; MPAIDTO fallback in rulebook | Blocked — partial |
| PACTG (fallback) | 641 tx in current year | `MINTYTD` | Sum if client approves | Planning option only |

### Fields that must remain unchanged

| Target | Current behavior | Touch this issue? |
|--------|------------------|-------------------|
| `quikmstr.MMODPREM` | PPOLC modal premium (#26 untouched) | **No** |
| `quikridr.MPREM` | ANN_PREM_PER_UNIT + fallback (#26) | **No** |
| `MPOLICY` padding | `format_qladmin_mpolicy()` (#25) | **No** |
| `quikdvdp.MDEPINT` | 4.00 default; ISWL → 4.50 (#21D) | **No** (regression guard) |
| Row count `quikdvdp` | 5,083 (one per seq-1 PPBENTYP) | **No change expected** |

---

## 5. Options evaluated

| Option | Description | Decision |
|--------|-------------|----------|
| **A** | Fix PACTG filename only; keep summing 514 as `MDEPOSIT` | **Rejected** — 514 sum ≠ LifePRO accumulation balance |
| **B** | Preserve rulebook `ACCUM_DIVIDENDS`; remove zero-on-miss enrichment | **Selected** for Track A |
| **C** | Use PACTG running ledger for balance | **Rejected** — no running balance in extract; high risk |
| **D** | Fleet-wide rulebook change only | **Rejected** — rulebook already correct; bug is in `app.py` enrichment |

---

## 6. Open client questions

1. **Scope:** Fix all **59 policies** with accumulation balances, or only **960 PO (8 policies)**?
2. **Balance authority:** Confirm **`PPBENTYP.ACCUM_DIVIDENDS`** matches the LifePRO screen labeled “Dividend Accumulations” on the sample screenshots.
3. **Screenshot amounts:** Please confirm ~**$9,888** and ~**$9,220** for the two reported policies (matches source extract).
4. **Track B:** Is **`MINTYTD` / `MINTDATE`** required for UAT sign-off, or is **`MDEPOSIT` balance** sufficient for Issue #38?
5. **PEVNTNONFC:** Can LifePRO deliver **`PEVNTNONFC`** (Non-Forfeiture Events) extract for interest YTD/date?
6. **960 PO `MDEPINT`:** Is **4.00%** correct for 960 PO dividend accum int rate (separate from ISWL 4.50%)?

---

## 7. Recommended formatting rules

| Rule | Recommendation |
|------|----------------|
| Policy key | `Master_Crosswalk.csv` → `format_qladmin_mpolicy()` (#25) |
| Money (`MDEPOSIT`, `MINTYTD`) | `{:.2f}`; strip commas/spaces on read |
| Zero balance | Emit **`0.00`** when source `ACCUM_DIVIDENDS` is zero — do not suppress row |
| Blanks | `MINTDATE` blank when unknown; do not invent dates |
| Dates | `YYYYMMDD` digits only (existing quikdvdp sanitizer) |

---

## 8. Policy number key handling

1. LifePRO `POLICY_NUMBER` (e.g. `9010378830`) → `Master_Crosswalk.csv` → `010378830C`
2. Apply **`format_qladmin_mpolicy()`** at emit (#25)
3. PACTG cache must normalize through same crosswalk (already implemented in cache loop)
4. Orphan policies: existing engine behavior — log and skip if no crosswalk match

---

## 9. Estimated record counts

| Metric | Count | Basis |
|--------|------:|-------|
| PPBENTYP seq-1 source rows | 5,083 | Source extract |
| `quikdvdp` output rows (unchanged) | 5,083 | Current output |
| Policies with **`ACCUM_DIVIDENDS > 0`** | **59** | Population analysis 2026-07-03 |
| **960 PO** with balance > 0 | **8** | Client-reported product family |
| Rows changing **`MDEPOSIT`** (Track A) | **59** | From 0.00 → source balance |
| Rows changing **`MDEPINT`** | **0** | Out of scope |

### Population by plan (59 policies)

| Plan code | Count |
|-----------|------:|
| 960 OL | 31 |
| 621 END85 | 8 |
| **960 PO** | **8** |
| 960 LP65 | 3 |
| 670 GL85-M | 3 |
| Other | 6 |

Full list: `Issue_38_Population.csv`

---

## 10. Sample trace (5 policies)

| Policy (QLA) | LifePRO | Plan | Source balance | Current `MDEPOSIT` | Proposed `MDEPOSIT` | `MDEPINT` | Status |
|--------------|---------|------|---------------:|-------------------:|--------------------:|----------:|--------|
| 010378830C | 9010378830 | 960 PO | 9,888.08 | 0.00 | **9,888.08** | 4.00 | Client example |
| 010380808C | 9010380808 | 960 PO | 9,220.33 | 0.00 | **9,220.33** | 4.00 | Client example |
| 010435671C | 9010435671 | 960 PO | 17,237.02 | 0.00 | **17,237.02** | 4.00 | Max 960 PO balance |
| 010405802C | 9010405802 | 670 GL85-M | 11,672.07 | 0.00 | **11,672.07** | 4.00 | Non-960 PO regression sample |
| 010713704C | 9010713704 | 659 CEN II | 0.00 | 0.00 | **0.00** | 4.50 | ISWL #21D control — must stay 0.00 |

Detail: `Issue_38_Trace_Samples.csv`

---

## 11. Risks and unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Enrichment change touches all 5,083 rows | Low | Only 59 non-zero values change; validator asserts count |
| Regress Issue #21D ISWL `MDEPINT` | Medium | Regression trace on `010713704C`; run `validate_issue21d_mdepint.py` |
| Regress Issue #25 MPOLICY width | Low | Run `validate_mpolicy_width.py` |
| Wrong balance authority (PPBENTYP vs PACTG) | Medium | Client confirms screenshots; trace 5 policies |
| `MINTYTD`/`MINTDATE` still zero/blank after Track A | Low | Document as known gap; Track B separate |
| PACTG 514 sum logic removed/disabled | Low | Document as intentional — not balance source |

---

## 12. Dependency Gate preview

See `Issue_38_Dependency_Gate.md` for full checklist.

| Check | Track A (balance) | Track B (interest YTD/date) |
|-------|-------------------|----------------------------|
| PPBENTYP in Source | **Met** | Met |
| PACTG in Source | **Met** (fix path in dev) | Met |
| PEVNTNONFC in Source | N/A | **Missing** |
| QLAdmin target field confirmed | **Met** (`MDEPOSIT`) | Partial |
| Example policies | **Met** | Met |
| Client scope | **Needs confirmation** (59 vs 8) | Needs confirmation |

---

## 13. Recommended Risk Agent prompt

```
Risk Agent — Issue #38: Dividend Accumulations

Read AI_Agents/Risk_Agent.md (if present), Issue_38_Planning_Report.md, and Issue_38_Dependency_Gate.md.

Quantify blast radius for Track A: preserve PPBENTYP ACCUM_DIVIDENDS as quikdvdp.MDEPOSIT; stop zero-on-miss enrichment in app.py; fix PACTG resolver path (do not use 514 sum as balance).

Regression guards: Issue #25 MPOLICY padding, Issue #26 MPREM, Issue #21D ISWL MDEPINT.

Deliver go/conditional-go with fallback rules. No code.
```

---

## 14. Recommended Development task (do not implement)

1. **`QLA_Migration/app.py` + root `app.py` (mirror):** In QUIKDVDP ENRICHMENT (~6131–6150), **remove the else-branch** that sets `MDEPOSIT`/`MINTYTD`/`MINTDATE` to zero on cache miss — **preserve rulebook-mapped values** from PPBENTYP.
2. **Optional same change:** When policy **is** in `quikdvdp_tx_cache`, do **not** overwrite `MDEPOSIT` from 514 sum; limit cache to `MINTYTD`/`MINTDATE` only if Track B approved.
3. **PACTG path (~5477):** Replace hardcoded `PACTG_Accounting_Extract20260427.csv` with `resolve_lifepro_source("quikprmh")` or equivalent from `qla_core/lifepro_source_resolver.py`.
4. **Version bump:** `app.py` patch version (e.g. v57.41) when batch path touched.
5. **Validator:** `tools/validators/validate_issue38_mdeposit.py` — assert 59 policies match PPBENTYP; trace `010378830C`, `010380808C`; assert `010713704C` stays 0.00; row count 5,083 unchanged.
6. **Regression:** Run `validate_issue21d_mdepint.py`, `validate_mpolicy_width.py`, `validate_issue26_mprem.py`.

**No rulebook CSV change required** for Track A — mapping already correct.

---

## Appendix

| Artifact | Path |
|----------|------|
| Population (59 rows) | `Issue_Log_Items/Issue_38/Issue_38_Population.csv` |
| Trace samples | `Issue_Log_Items/Issue_38/Issue_38_Trace_Samples.csv` |
| Research script | `QLA_Migration/_research_issue38_quikdvdp.py` |
| Intake summary | `Issue_Log_Items/Issue_38/Issue_38_Intake_Summary.md` |
| Client screenshots | `docs/960 PO - LifePRO Policy Screenshots.docx` |
| Related | Issue #21D (MDEPINT), #25 (MPOLICY), #26 (MPREM) |

---

## G1 gate

- [x] Planning report published
- [x] Source and target documented; gaps listed (PEVNTNONFC)
- [x] Trace table included (5 policies)
- [x] Open questions enumerated
- [x] Development task outlined — **not executed**
- [x] No code, rulebook, or output changes

**Next stage:** Dependency Gate → Risk Agent
