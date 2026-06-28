# Issue #21D — Validation Matrix

**Date:** 2026-06-27  
**Converter version (baseline):** v57.35  
**Target version (post-Development):** v57.36+  
**Scope:** Track A + Track B1 post-Development validation  
**Track B2:** Revalidation only after client RNA delivery (separate section)

---

## 1. Pre-Development baseline (archive)

| Step | Action | Artifact |
|------|--------|----------|
| V0.1 | Archive v57.35 batch output | `QLA_Migration/Output/` snapshot |
| V0.2 | Record baseline MDEPINT distribution | All 5,083 @ 4.00 |
| V0.3 | Record blank-name population | `Issue_21D_Blank_Name_Population.csv` (25 rows) |
| V0.4 | Record missing quikclnt IDs | 14 NAME_IDs |

---

## 2. Track A — post-Development validation

### 2.1 Automated

| ID | Validator / check | Pass criteria | Priority |
|----|-------------------|---------------|----------|
| A-V1 | Full batch completes | No conversion errors | **P0** |
| A-V2 | `validate_issue21d_mdepint.py` (new) | 2,268 ISWL policies MDEPINT = 4.50 | **P0** |
| A-V3 | Non-ISWL regression | 2,815 non-ISWL MDEPINT = 4.00 (unchanged vs baseline) | **P0** |
| A-V4 | ISWL allowlist coverage | All 8 MPLAN codes represented; 0 ISWL outside allowlist at 4.50 | **P0** |
| A-V5 | quikdvdp diff vs baseline | Only MDEPINT column changes; only ISWL MPOLICY rows | **P0** |
| A-V6 | NFOINT unchanged | All ISWL quikplan templates NFOINT = A | **P1** |
| A-V7 | CSO crosswalk integrity | 8/8 ISWL rows `nfo_interest_source = 4.50%` | **P1** |
| A-V8 | Schema integrity | quikdvdp field order/types/lengths unchanged | **P0** |

### 2.2 Sample policy validation

| MPOLICY | MPLAN | Check | Expected |
|---------|-------|-------|----------|
| 010713704C | 1659C2 | MDEPINT | 4.50 |
| 010818663C | (ISWL) | MDEPINT | 4.50 |
| (non-ISWL sample) | e.g. 5667AT | MDEPINT | 4.00 |

### 2.3 Client UAT (Track A)

| ID | Action | Owner | Pass criteria |
|----|--------|-------|---------------|
| A-U1 | QLAdmin Dividend Accum Int Rate on 010713704C | Client | Displays 4.50% |
| A-U2 | Spot-check 3 additional ISWL policies | Client | 4.50% |
| A-U3 | Spot-check 2 non-ISWL policies | Client | 4.00% unchanged |
| A-U4 | Joint #21E sample review (optional) | Shared | Document CV vs display field separation |

---

## 3. Track B1 — post-Development validation

### 3.1 Automated

| ID | Validator / check | Pass criteria | Priority |
|----|-------------------|---------------|----------|
| B1-V1 | Full batch completes | No conversion errors | **P0** |
| B1-V2 | `validate_issue21d_blank_names.py` (new) | 7 B1-target policies show names resolved | **P0** |
| B1-V3 | quikclnt completeness | 14 missing NAME_IDs → 0 (excl. documented separator) | **P0** |
| B1-V4 | MCLIENTID uniqueness | No duplicate MCLIENTID in quikclnt | **P0** |
| B1-V5 | Referential integrity | quikclid-referenced MCLIENTID ⊆ quikclnt | **P0** |
| B1-V6 | MPRIMID guard | MPRIMID = 'I' count = 0 | **P0** |
| B1-V7 | `validate_insured_owner_golden.py` (extended) | Golden harness PASS for B1-fixable policies | **P0** |
| B1-V8 | quikclnt row count delta | +≤14 rows vs baseline | **P1** |
| B1-V9 | Schema integrity | quikclnt field order/types/lengths unchanged | **P0** |

### 3.2 Population reduction analysis

| Metric | Baseline (v57.35) | Target (v57.36 B1) | Full close (B2) |
|--------|-------------------|--------------------|-----------------|
| Blank-name policies | 25 | **18** (7 recovered) | **0** |
| RNA IDs missing from quikclnt | 14 | **0** | 0 |
| Policies needing RNA (B2) | 18 | 18 (unchanged) | 0 after extract |

**B1-target policies (expect improvement):**

010766896C, 011080481C, 010464869C, 010464870C, 010872417C, 011047402C, 011047403C

### 3.3 Sample policy verification

| MPOLICY | Missing ID | Expected after B1 |
|---------|------------|-------------------|
| 010766896C | 592064 | JOHNSON, PENNY visible |
| 011080481C | 607190 | YOUNTS, JOSHUA (insured) visible |
| 010464869C | 589330 | Names visible |

### 3.4 Client UAT (Track B1 — partial)

| ID | Action | Owner | Pass criteria |
|----|--------|-------|---------------|
| B1-U1 | Name display on 010766896C | Client | Insured name visible |
| B1-U2 | Name display on 011080481C | Client | Insured name visible |
| B1-U3 | Acknowledge 18 policies still open | Client | B2 list accepted |
| B1-U4 | NULL-address client 592064 | Client | QLAdmin accepts row |

**Still blank after B1 (B2 scope — do not fail B1 UAT):** 010713704C, 010713705C, and 16 others per population CSV.

---

## 4. Cross-issue regression validation

Run after Track A + B1 Development; **required beyond standard validation** for protected issues:

| Issue | Validator | Required? | Expected |
|-------|-----------|-----------|----------|
| #25 MPOLICY | `validate_issue21.py` or width check | **Yes** | PASS — no MPOLICY change |
| #26 MPREM | `_validate_issue26_mprem.py` | **Yes** | PASS — no MPREM change |
| #28 Plan mapping | Issue #28 evidence validators | **Yes** | PASS — no crosswalk change |
| #21M QUIKMEMO | `validate_issue21m_quikmemo.py` | **Yes** | PASS — no memo grain change |
| #21M-FU DBF | `validate_issue21m_dbf_packaging.py` | **Yes** | PASS |
| #21K fleet/MUNIT | `validate_issue21k_fleet.py`, `validate_issue21k_munit.py` | **Recommended** | PASS — no quikplan MUNIT touch |
| v57.28 MPRIMID | Blank-name + golden validators | **Yes** | MPRIMID='I' = 0 |

**#21E:** No automated validator required for #21D close. Coordinate manual UAT if CV samples overlap.

---

## 5. Combined release validation sequence

```
1. Full batch (v57.36+)
2. validate_issue21d_mdepint.py      → P0 PASS
3. validate_issue21d_blank_names.py  → P0 PASS (partial metrics)
4. validate_insured_owner_golden.py  → P0 PASS
5. Protected-issue validators (#25, #26, #28, #21M, #21K) → PASS
6. Diff quikdvdp / quikclnt vs v57.35 baseline
7. Client UAT (A-U1..A-U3, B1-U1..B1-U4)
8. Release notes (partial B fix documented)
```

---

## 6. Track B2 — revalidation (after client RNA delivery)

**Trigger:** Client delivers updated `RelationshipNameAddress_Extract` (EXT-B1)

| ID | Check | Pass criteria |
|----|-------|---------------|
| B2-V1 | Full batch with new RNA | Completes without error |
| B2-V2 | Blank-name population | 0 rows (or documented exceptions) |
| B2-V3 | Golden policies | 010713704C names if IN/PO in new extract |
| B2-V4 | B1 referential checks | Still PASS (no regression) |
| B2-V5 | Client UAT | Full Track B sign-off |

**Not part of current Development validation scope.**

---

*Validation matrix for Risk Agent. Development Agent must implement validators A-V2 and B1-V2.*
