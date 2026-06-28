# Issue #21D — Validation Dependencies

**Date:** 2026-06-27  
**Converter version (baseline):** v57.35  
**Purpose:** Define validation required after Development — not executed during Dependency Gate

---

## Track A — Interest rate validation

### A-V1 — ISWL population validation

| Item | Detail |
|------|--------|
| **Input** | `QLA_Migration/Output/quikdvdp.csv`, `quikridr.csv` |
| **Rule** | Every policy with base MPLAN ∈ {1658C1, 1658CS, 1659C2, 1659CR, 1659CS, 1659SR, 1669SR, 1679CS} → `MDEPINT = 4.50` |
| **Expected count** | 2,268 |
| **Tool** | `validate_issue21d_mdepint.py` (to create) |
| **Fixture** | `Issue_21D_Interest_Rate_Population.csv` |

### A-V2 — Non-ISWL preservation validation

| Item | Detail |
|------|--------|
| **Rule** | All non-ISWL policies → `MDEPINT` unchanged vs v57.35 baseline (4.00) |
| **Expected count** | 2,815 unchanged |
| **Method** | Diff quikdvdp MDEPINT column against baseline; zero non-ISWL deltas |

### A-V3 — CSO crosswalk alignment validation

| Item | Detail |
|------|--------|
| **Rule** | Each ISWL MPLAN: CSO `nfo_interest_source` = 4.50% → MDEPINT = 4.50 |
| **Rule** | `quikplan.NFOINT` remains `A` for all 8 ISWL templates (no regression) |
| **Source** | `CSO_Mortiality_Crosswalk.csv`, `quikplan.csv` |

### A-V4 — Sample policy validation

| Policy | MPLAN | Expected MDEPINT | QLAdmin check |
|--------|-------|------------------|---------------|
| 010713704C | 1659C2 | 4.50 | Dividend Accum Int Rate 4.50% |
| 010718309C | 1658C1 | 4.50 | ISWL sample |
| 010818663C | (verify MPLAN) | 4.50 if ISWL | Issue #21 packet |

### A-V5 — Schema integrity

| Item | Detail |
|------|--------|
| **Tables** | quikdvdp only |
| **Check** | Field order, types, lengths unchanged per `TABLE_SCHEMAS` |
| **Tool** | Existing output validation / schema manifest |

### A-V6 — Cross-issue (#21E) validation

| Item | Detail |
|------|--------|
| **Rule** | Document whether CV changed on ISWL samples after MDEPINT fix |
| **Policies** | 010713704C, 010818663C |
| **Note** | PASS on #21D does not imply PASS on #21E |

---

## Track B — Blank name validation

### B-V1 — Blank-name population validation

| Item | Detail |
|------|--------|
| **Input** | `quikmstr.csv`, `quikclnt.csv`, `Issue_21D_Blank_Name_Population.csv` |
| **Rule** | Insured/owner names non-blank for all 25 previously affected policies (post B1+B2) |
| **Tool** | `validate_issue21d_blank_names.py` (to create) |

### B-V2 — quikclnt completeness validation

| Item | Detail |
|------|--------|
| **Rule** | Every MCLIENTID in quikclid ∪ {MPRIMID, MOWNRID, MPAYRID from quikmstr} ⊆ quikclnt.MCLIENTID |
| **Rule** | Every RNA NAME_ID (except `-----------`) ⊆ quikclnt after B1 |
| **Expected** | 14 missing IDs → 0 (or 13 excluding separator) |

### B-V3 — RNA completeness validation

| Item | Detail |
|------|--------|
| **Rule** | For 25-policy list: quikclid has IN and/or PO rows matching LifePRO roles |
| **Input** | New RNA extract vs `Issue_21D_Blank_Name_Population.csv` |
| **Gate** | Required for B2 acceptance |

### B-V4 — MPRIMID guard validation

| Item | Detail |
|------|--------|
| **Rule** | Zero quikmstr rows with `MPRIMID` ∈ single-letter alpha (especially `I`) |
| **Tool** | `validate_insured_owner_golden.py` |

### B-V5 — Sample policy validation

| Policy | Phase | Expected after fix |
|--------|-------|-------------------|
| 010713704C | B2 | Insured + owner names display |
| 010766896C | B1 | JOHNSON, PENNY (592064 in quikclnt) |
| 011080481C | B1 | Insured YOUNTS, JOSHUA; owner already OK |
| 010872417C | B1 | Insured name from 604080 |

### B-V6 — Golden Issue #21 policy set

| Item | Detail |
|------|--------|
| **Policies** | 010391876C, 010391895C, 010448806C, 010713704C, 010718309C, 010765930C, 010818663C |
| **Tool** | `validate_insured_owner_golden.py` — must PASS (no regression on fixed policies) |

---

## Shared validation dependencies

| Dependency | Required before validation |
|------------|---------------------------|
| Full batch v57.36+ | `run_converter.bat` or `_run_full_batch_test.py` |
| Baseline archive | v57.35 `QLA_Migration/Output/` snapshot |
| Source package | Current extracts; B2 needs new RNA when testing full fix |
| Schema validators | No field order changes |

---

## Validation sequencing

```
1. Development completes Track A (+ optional B1)
2. Full batch run
3. Run validate_issue21d_mdepint.py          (Track A)
4. Run validate_issue21d_blank_names.py      (Track B)
5. Run validate_insured_owner_golden.py      (Track B regression)
6. Diff non-target columns vs baseline       (Both)
7. Client UAT on sample policies             (Both)
8. [After RNA drop-in] Repeat 2–7 for B2     (Track B complete)
```

---

## Acceptance thresholds

| Track | Development merge | Client UAT | Issue close |
|-------|--------------------|-----------|-------------|
| A | A-V1 + A-V2 + A-V3 + A-V5 PASS | A-V4 sample | UAT sign-off |
| B1 | B-V2 + B-V4 (partial) PASS | Partial samples | Not sufficient alone |
| B2 | B-V1 + B-V3 + B-V6 PASS | B-V5 all samples | Full #21D close |
