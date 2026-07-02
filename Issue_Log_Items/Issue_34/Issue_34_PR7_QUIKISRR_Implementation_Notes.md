# Issue #34 — PR-7 QUIKISRR Implementation Notes

**Issue:** #34 — ISWL Partial Surrender History Package  
**Date:** 2026-07-02  
**Status:** **COMPLETE — ready for review**

---

## Scope delivered

PR-7 emits the approved four-table partial surrender history package:

| Table | Output path | Mode |
|-------|-------------|------|
| QuikClms | `QLA_Migration/Output/quikclms.csv` | Append phase-0 partial rows |
| QuikClmp | `QLA_Migration/Output/quikclmp.csv` | Append phase-0 payment rows |
| QuikBenh | `QLA_Migration/Output/quikbenh.csv` | **New file** — append/merge at client load |
| QuikIsrr | `QLA_Migration/Output/QuikIsrr.csv` | **New file** — MISWL omitted |

No transaction audit (QuikAudt) records created.

---

## Files created / modified

| File | Action |
|------|--------|
| `qla_core/quikisrr_loader.py` | **New** — candidate load, payee resolution, row builders |
| `Issue_Log_Items/Issue_34/tools/quikisrr_pr7_emit.py` | **New** — PR-7 emit runner |
| `tools/validators/iswl_quikisrr_reconcile.py` | **New** — V-ISRR-01..22 validator |
| `QLA_Migration/Output/quikclms.csv` | **Modified** — 2,114 → 5,730 rows (+3,616) |
| `QLA_Migration/Output/quikclmp.csv` | **Modified** — 1,709 → 5,325 rows (+3,616) |
| `QLA_Migration/Output/quikbenh.csv` | **New** — 3,616 rows |
| `QLA_Migration/Output/QuikIsrr.csv` | **New** — 3,616 rows |
| `Issue_Log_Items/Issue_34/output/PR7_QUIKISRR/*` | **New** — artifacts |
| `Issue_Log_Items/Issue_34/output/baselines/iswl_quikisrr_regression_baseline.json` | **New** |

**Not modified:** `app.py`, Issue #31–#33 rate loaders/outputs, existing claims derivation code.

---

## Row counts

| Metric | Value |
|--------|------:|
| Candidate population (pre-exception) | **3,623** events / **636** policies / **$1,217,593.55** |
| Main emit (all four tables) | **3,616** events / **635** policies / **$1,216,073.15** |
| Payee exceptions | **7** rows — policy `010826551C` (no OWNR/INSD) |
| Manual hold (excluded) | **3** rows — policy `9010780411` |
| Reversal excluded | **61** rows |

---

## Field rules applied

- **MPHASE = 0**, **MSEQ = 1..n** per policy ordered by EFFECTIVE_DATE, DATE_ADDED, RECORD_SEQUENCE
- **CLAIMNUM** = `PS-{policy_digits}-{seq:03d}`
- **ORIGSTTUS = 22** (schema field name in emitted CSV)
- **CLAIMSTAT = 99**, **CAUSE = SRR**
- **Amounts:** gross PACTG TRANS_AMOUNT on MFACE, MPAID, MAMOUNT, MGROSS, MBEN, MSURRAMT
- **Dates:** maintenance = EFFECTIVE_DATE; processed = DATE_ADDED
- **Payee:** quikclid OWNR → quikclnt; fallback INSD; exception if neither
- **QuikBenh:** MBENTYP = 8
- **QuikIsrr:** MISWL column omitted (no PFNDR)

---

## Validation results

Validator: `python tools/validators/iswl_quikisrr_reconcile.py`

| Check | Result |
|-------|--------|
| V-ISRR-01 .. V-ISRR-21 | **PASS** |
| V-ISRR-19 existing claims prefix | **PASS** — SHA-256 hash unchanged for pre-PR-7 rows |
| V-ISRR-22 regression (full run) | **PASS** — QuikUint, QuikIssc, QuikCvs validators (first full run ~468s) |

Summary artifact: `Issue_Log_Items/Issue_34/output/PR7_QUIKISRR/quikisrr_reconcile_summary.json`

---

## Exception artifacts

| File | Rows |
|------|-----:|
| `quikisrr_payee_exceptions.csv` | 7 |
| `quikisrr_policy_9010780411_hold.csv` | 3 |
| `quikisrr_reversal_excluded.csv` | 61 |
| `quikisrr_sequence_audit.csv` | 3,616 |
| `quikisrr_emitted_events.csv` | 3,616 |
| `quikisrr_candidate_population.csv` | 3,623 |

---

## Known issues / notes

1. **QuikBenh duplicate MPOLICY+MDATE:** 5 policy-date pairs share the same DATE_ADDED across multiple events (different EFFECTIVE_DATE/amount). Both rows are emitted with distinct MBEN — valid per schema index (non-unique NTX).
2. **010834096C:** insured-only fallback applied successfully (1 policy).
3. **QuikBenh client load:** file is new in this repo; client Loyal2QL may already have dividend history in quikbenh — **merge/append at load**, do not replace.
4. **PRODUCT_ID fallback:** logged when PLAN_CODE absent; see `quikisrr_product_id_fallbacks.csv` if present.

---

## Deferred items

- Integrate PR-7 emit into `app.py` batch orchestration (not requested; standalone runner used)
- DBF generation for quikbenh / QuikIsrr
- UAT claims DBF re-alignment after quikclms/quikclmp row growth

---

## Run commands

```text
python Issue_Log_Items/Issue_34/tools/quikisrr_pr7_emit.py
python tools/validators/iswl_quikisrr_reconcile.py
python tools/validators/iswl_quikisrr_reconcile.py --skip-regression   # faster re-check
```

---

## Recommendation

**PR-7 is ready for review.** All 22 validation checks pass; prior ISWL rate-table regression passed on full validator run. Existing claims rows preserved; partial surrender package complete for 3,616 events.
