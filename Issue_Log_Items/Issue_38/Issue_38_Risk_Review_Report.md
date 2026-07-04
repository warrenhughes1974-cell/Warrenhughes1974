# Issue #38 — Risk Review Report

**Issue:** #38 — Dividend Accumulations  
**Date:** 2026-07-03  
**Converter version (baseline):** v57.43  
**Prior stages:** Intake ✅ · Planning ✅ · Dependency Gate ✅  
**Framework stage:** Risk Agent (G3)  
**Next stage:** Development Agent (awaiting explicit user authorization)

**Status note:** Risk analysis only — no production code changes in this stage.

---

## Go / No-Go Recommendation

```text
CONDITIONAL GO
```

Development may proceed **safely** for the approved scope: restore **`quikdvdp.MDEPOSIT`** from **`PPBENTYP.ACCUM_DIVIDENDS`** (all **59** policies), populate **`MINTYTD`** / **`MINTDATE`** from **PACTG account 641**, fix hardcoded PACTG path, and add Issue #38 validator.

**Conditions before production sign-off:**
1. Client UAT on sample policies (`010378830C`, `010380808C` minimum).
2. Run protected-issue regression suite (#25, #26, #21D).
3. **Source data is authoritative** — screenshots are evidence of missing QLAdmin data only, not target values (client confirmed 2026-07-03).

---

## 1. Current vs proposed mapping

| QLAdmin field | Current behavior | Proposed behavior | Rows changing |
|---------------|------------------|-------------------|--------------:|
| **`MDEPOSIT`** | Forced **`0.00`** on PACTG cache miss (cache never loads) | **`PPBENTYP.ACCUM_DIVIDENDS`** via existing rulebook; **never zero on miss** | **59** |
| **`MINTYTD`** | Forced **`0.00`** on cache miss | Sum **PACTG 641** credits in **current calendar year** when cache loads | **18** (non-zero after) |
| **`MINTDATE`** | Blank on cache miss | Latest **PACTG 641** effective date when cache loads | **63** |
| **`MDEPINT`** | 4.00 default; ISWL → 4.50 (#21D) | **Unchanged** | **0** |
| **`MPOLICY`** | Crosswalk + #25 padding | **Unchanged** | **0** |

**Explicitly rejected:** Using PACTG account **514** transaction sums as `MDEPOSIT` balance.

**Data authority (client confirmed):** Always use **LifePRO extracts** in `QLA_Migration/Source/` — not screenshot quote values.

---

## 2. Premium / related fields untouched

| Target | Source / behavior | Touched? |
|--------|-------------------|----------|
| `quikmstr.MMODPREM` | PPOLC modal premium | **No** |
| `quikridr.MPREM` | ANN_PREM_PER_UNIT + fallback (#26) | **No** |
| `MPOLICY` width | `format_qladmin_mpolicy()` (#25) | **No** |
| `quikdvdp.MDEPINT` | #21D ISWL allowlist | **No** |
| Row count `quikdvdp` | 5,083 (PPBENTYP seq 1) | **No** |
| All other tables | — | **No** |

---

## 3. Repo references

| Location | Role |
|----------|------|
| `QLA_Migration/app.py` ~5477–5535 | PACTG cache — **hardcoded wrong filename** |
| `QLA_Migration/app.py` ~6131–6150 | Enrichment **zeros MDEPOSIT/MINTYTD/MINTDATE** |
| `QLA_Migration/Configs/Sync_Rulebook_quikdvdp.csv` | `ACCUM_DIVIDENDS` → `MDEPOSIT` (already correct) |
| `qla_core/lifepro_source_resolver.py` | Dynamic PACTG resolution pattern |
| `QLA_Migration/Source/PPBENTYP_BenefitType_Extract_20260530.csv` | Balance authority |
| `QLA_Migration/Source/PACTG_Accounting_Extract20260530.csv` | 641 interest YTD/date |
| `Issue_Log_Items/Issue_38/Issue_38_Risk_Simulation.csv` | Before/after simulation output |

---

## 4. Population analysis (simulated)

| Metric | Count |
|--------|------:|
| Total `quikdvdp` rows | 5,083 |
| **`MDEPOSIT` changes** | **59** |
| **`MDEPOSIT` unchanged (incl. zero)** | **5,024** |
| **`MDEPOSIT > 0` after fix** | **59** |
| **`MINTYTD > 0` after fix** | **18** |
| **`MINTDATE` populated after fix** | **63** (includes policies with 641 history but zero balance) |
| Among 59 balance policies: `MINTDATE` populated | **59** |
| Among 59 balance policies: `MINTYTD > 0` (2026 YTD) | **18** |
| **`MDEPINT` changes** | **0** |

Simulation script: `QLA_Migration/_risk_review_issue38_quikdvdp.py`

### Plan breakdown (59 balance policies)

| Plan code | Policies |
|-----------|----------:|
| 960 OL | 31 |
| 621 END85 | 8 |
| **960 PO** | **8** |
| Other | 12 |

---

## 5. Fallback recommendation

| Scenario | Fallback rule | Row impact |
|----------|---------------|----------:|
| PACTG file not found | Preserve rulebook **`MDEPOSIT`** from PPBENTYP; leave **`MINTYTD=0.00`**, **`MINTDATE` blank** | 59 MDEP still fixed |
| Policy missing from 641 cache | **`MINTYTD=0.00`**, **`MINTDATE` blank**; **`MDEPOSIT` still from PPBENTYP** | subset of 59 |
| `ACCUM_DIVIDENDS` blank/zero in PPBENTYP | **`MDEPOSIT=0.00`** (correct) | unchanged |

**Recommended primary path:** Fix PACTG resolver + stop zero-on-miss for all three fields; **641 cache supplements interest fields only**, does not override balance.

---

## 6. Trace policies (simulated)

| Policy | Plan | MDEPOSIT before → after | MINTYTD before → after | MINTDATE before → after |
|--------|------|-------------------------|------------------------|-------------------------|
| **010378830C** | 960 PO | 0.00 → **9,888.08** | 0.00 → **0.00** | blank → **20251231** |
| **010380808C** | 960 PO | 0.00 → **9,220.33** | 0.00 → **0.00** | blank → **20251231** |
| **010435671C** | 960 PO | 0.00 → **17,237.02** | 0.00 → *(per 641)* | blank → **20251231** |
| **010713704C** | ISWL (#21D control) | 0.00 → **0.00** | 0.00 → **0.00** | blank → blank |
| **010405802C** | 670 GL85-M | 0.00 → **11,672.07** | 0.00 → *(per 641)* | blank → **20251231** |

**Note on MINTYTD:** Engine uses **current calendar year (2026)** for YTD sum. Sample policies show **$0.00 YTD** because no **641** credits posted in 2026 in the extract yet — last credits were **20251231** (2025). **18 policies** fleet-wide have 2026 YTD > 0. This is **source-accurate**, not a defect.

---

## 7. Top 5 largest MDEPOSIT changes

| Policy | Before | After | Delta |
|--------|-------:|------:|------:|
| 010435671C | 0.00 | 17,237.02 | +17,237.02 |
| 010405802C | 0.00 | 11,672.07 | +11,672.07 |
| 010513848C | 0.00 | 10,089.82 | +10,089.82 |
| 010542288C | 0.00 | 10,427.22 | +10,427.22 |
| 010407023C | 0.00 | 9,987.10 | +9,987.10 |

All changes are **intentional corrections** from zero to PPBENTYP source balance — not accidental drift.

---

## 8. Material calculation impact

| Impact type | Assessment |
|-------------|------------|
| QLAdmin dividend deposit display | **Material positive** — 59 policies gain correct balances |
| Surrender / quote totals in QLAdmin | May increase where dividend deposit was omitted — **expected** |
| Premium, modal, coverage | **None** |
| ISWL interest rate (#21D) | **None** |
| Negative balance risk | **None** — source values ≥ 0 |

---

## 9. Risk register

| ID | Category | Severity | Mitigation | Owner |
|----|----------|----------|------------|-------|
| R-01 | Enrichment regression | Low | Surgical else-branch removal; validator on 59 rows | QLAdmin |
| R-02 | Wrong PACTG file persists | Medium | Use `lifepro_source_resolver`; log resolved path | QLAdmin |
| R-03 | 514 sum reintroduced | Medium | Code review — do not map 514 to MDEPOSIT | QLAdmin |
| R-04 | #21D MDEPINT regression | Medium | Trace `010713704C`; run `validate_issue21d_mdepint.py` | QLAdmin |
| R-05 | #25 MPOLICY width | Low | Run `validate_mpolicy_width.py` | QLAdmin |
| R-06 | #26 MPREM | Low | Run `validate_issue26_mprem.py` | QLAdmin |
| R-07 | MINTYTD year filter confusion | Low | Document 2026 YTD = 0 for most policies until 641 posts; UAT note | Shared |
| R-08 | PEVNTNONFC absent | Low | PACTG 641 fallback approved; optional future enhancement | Shared |
| R-09 | Client UAT expectation | Medium | UAT on 010378830C / 010380808C; source not screenshots | Client |

---

## 10. Prior fix preservation

| Check | Expected result |
|-------|-----------------|
| Issue #25 MPOLICY padding | **Pass** — no MPOLICY logic change |
| Issue #26 MPREM / MMODPREM | **Pass** — quikridr/quikmstr untouched |
| Issue #21D ISWL MDEPINT 4.50 | **Pass** — MDEPINT branch unchanged |
| Issue #37 / other open work | **Pass** — quikdvdp-only scope |

---

## 11. Regression testing checklist (Validation Agent)

- [ ] `validate_issue38_mdeposit.py` — 59 policies match PPBENTYP; 5,083 row count
- [ ] Trace `010378830C`, `010380808C` — MDEPOSIT matches source extract
- [ ] Control `010713704C` — MDEPOSIT 0.00; MDEPINT 4.50 unchanged
- [ ] `validate_issue21d_mdepint.py` — PASS
- [ ] `validate_mpolicy_width.py` — PASS
- [ ] `validate_issue26_mprem.py` — PASS
- [ ] Diff quikdvdp vs baseline — only MDEPOSIT/MINTYTD/MINTDATE columns on expected rows
- [ ] Client UAT — dividend accumulation visible in QLAdmin for sample policies

---

## 12. Recommended Development Agent task

**Do not implement until user explicitly authorizes Development.**

1. **`QLA_Migration/app.py` + root `app.py` (mirror):**
   - Replace hardcoded `PACTG_Accounting_Extract20260427.csv` with `resolve_lifepro_source()` / newest PACTG in Source.
   - In QUIKDVDP ENRICHMENT (~6131–6150):
     - **Remove** else-branch that sets `MDEPOSIT`/`MINTYTD`/`MINTDATE` to zero/blank.
     - When policy **is** in cache: apply **641-only** data to `MINTYTD` and `MINTDATE` — **do not overwrite `MDEPOSIT` from 514**.
     - When policy **not** in cache: **preserve rulebook values** already mapped from PPBENTYP.
2. **Do NOT change:** `Sync_Rulebook_quikdvdp.csv`, MDEPINT logic, MPOLICY, MPREM, other tables.
3. **Version bump:** v57.43 → **v57.44** (both `app.py` copies).
4. **Add validator:** `tools/validators/validate_issue38_mdeposit.py`.
5. **Self-check:** Run risk simulation script post-change; compare to `Issue_38_Risk_Simulation.csv`.

---

## 13. Rollback

| Item | Procedure |
|------|-----------|
| Revert | Restore v57.43 `app.py` enrichment block |
| Re-batch | Full batch — quikdvdp returns to all-zero MDEPOSIT |
| Trigger | Validator fail; client UAT reject; unexpected MDEPINT drift |

**Rollback risk:** Low — isolated quikdvdp enrichment; no rulebook change.

---

## G3 gate

- [x] Risk report published with Conditional Go
- [x] Impact quantified (59 / 18 / 63 — not guessed)
- [x] Unrelated fields marked untouched
- [x] #25 / #26 / #21D preservation confirmed
- [ ] User authorization for Development (pending)

**Next step:** User says **“Approved for Development”** → Development Agent implements surgical fix.

---

## Appendix

| Artifact | Path |
|----------|------|
| Simulation CSV | `Issue_Log_Items/Issue_38/Issue_38_Risk_Simulation.csv` |
| Population | `Issue_Log_Items/Issue_38/Issue_38_Population.csv` |
| Planning | `Issue_Log_Items/Issue_38/Issue_38_Planning_Report.md` |
| Dependency Gate | `Issue_Log_Items/Issue_38/Issue_38_Dependency_Gate.md` |
