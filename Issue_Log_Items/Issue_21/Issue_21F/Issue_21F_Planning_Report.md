# Issue 21F — Planning Report

**Issue:** Truncated Premium History — conversion premium adjustment  
**Framework stage:** Planning complete (business locked 2026-07-11)  
**Status:** **READY FOR RISK / DEVELOPMENT AUTHORIZATION**  
**Engine baseline:** v57.63 (pre-21F adjustment)  
**Authority:** Eric confirmed all seven planning recommendations  

---

## 1. Executive finding

Truncation is **source-imposed** (PACTG extract floor ~2017-01-01). The `quikprmh` mapping is correct for rows present. Business does **not** require full transaction replay to issue. Instead, reconcile **lifetime premiums paid** by emitting **one Conversion Adjustment** row so:

```
Σ(quikprmh.PREMIUM) + Adjustment  =  LifePRO_Total_Premiums_Paid
```

for eligible **non-ISWL** policies when LifePRO total exceeds the converted history sum.

**Golden example (client workbook):** 010310404C — LifePRO $17,040.05 vs history $1,846.20 → adjustment **$15,193.85** dated **2017-12-31**.

---

## 2. Confirmed LifePRO source

| Source | File pattern | Fields |
|---|---|---|
| PPBENTYP | `PPBENTYP_BenefitType_Extract_*.csv` | Base `PREMIUMS_PAID`, PUA `PU_PREMIUMS_PAID`, Supplemental `SU_PREMIUMS_PAID`, Substandard `SL_PREMIUMS_PAID` |

```
LifePRO_Total = PREMIUMS_PAID + PU_PREMIUMS_PAID + SU_PREMIUMS_PAID + SL_PREMIUMS_PAID
```

(Per-policy aggregation rules for BA/BF/PU/SU/SL TYPE_CODE rows to be finalized in Development; avoid double-counting if components live both as TYPE_CODE rows and dedicated columns.)

**ISWL (excluded phase 1):** `PPBEN` `FV_GUAR_DEPOSITS` / `FV_BASIS2` — do not adjust.

Workbook reference: `docs/Copy of Premium Paid Fields.xlsx` (Non-ISWL sheet).

---

## 3. Confirmed QLAdmin target

| Table | Field | Use for adjustment |
|---|---|---|
| **quikprmh** | `MPOLICY` | Crosswalked policy |
| | `DATEPAID` | **2017-12-31** |
| | `PREMIUM` (and likely `MLIFE`) | Adjustment amount (money format) |
| | `MSOURCE` / `MBATCH` / `USER_ID` | Conversion Adjustment marker (exact codes at Dev) |
| | Other money splits (`MTERM`, `MSUPP`, `MANN`, `MHEALTH`, `XS`) | Defaults **0.00** unless Dev finds need to split components onto MSUPP/MHEALTH |
| | `RENEWAL`, `MPAIDTO`, `MMODEPD`, etc. | Safe defaults consistent with synthetic row (not a real payment) |

**Schema (unchanged):**  
`MPOLICY, DATEPAID, RENEWAL, PREMIUM, MLIFE, MTERM, MSUPP, MANN, MHEALTH, XS, MPAIDTO, POSTDATE, MPOSTDATE, MSOURCE, MBATCH, USER_ID, MBILLFRM, MMODEPD`

No new columns. No Output-folder audits — validation CSVs go to `QLA_Migration/Reports/`.

---

## 4. Eligibility & formulas

| Case | Action |
|---|---|
| ISWL / UL book | Exclude; report `ISWL_EXCLUDED` |
| `LifePRO_Total − History_Total > 0` | Emit one adjustment row; status `LOADED` |
| Difference `== 0` (within money tolerance) | No row; status `NO_GAP` |
| Difference `< 0` | No row; status `NEGATIVE_EXCEPTION` |

```
History_Total = sum(PREMIUM) over existing quikprmh rows for MPOLICY
Adjustment   = LifePRO_Total − History_Total   # positive only when loading
```

Existing history rows are never modified or deleted.

---

## 5. Reports (UAT)

| Report | Location | Contents |
|---|---|---|
| Validation | `Reports/issue21f_premium_adjustment_validation.csv` | LifePRO total, components, before, adjustment, after, variance, status |
| Exceptions | `Reports/issue21f_premium_adjustment_exceptions.csv` | Negatives + optional ISWL exclusions |

---

## 6. Implementation constraints (`AGENTS.md`)

- Surgical only — prefer helper in `qla_core/` + thin wire in `app.py` / `QLA_Migration/app.py`
- Do not redesign `quikprmh` schema or rewrite PACTG conversion wholesale
- Bump `APP_VERSION` in **both** app.py files
- Preserve QLA money formatting and field order
- Regression: non-candidate policies’ existing `quikprmh` rows unchanged; only additive adjustment rows for candidates

---

## 7. Regression / risk preview (for Risk Agent)

| Risk | Mitigation |
|---|---|
| Double-count if adjustment re-run | Idempotent marker (Conversion Adjustment) — skip if already present for policy |
| Wrong policies (ISWL) get cash-like premium rows | Hard exclude ISWL/UL book |
| Negative loads distort totals | Exception path only |
| Output pollution | Reports under `Reports/` only |
| Inflated `PREMIUM` on screen looks like a payment | Classification + fixed 12/31/2017 date |

---

## 8. Recommended Development outline (post-auth)

1. Build LifePRO four-component totals cache (non-ISWL).
2. After `quikprmh` materialization, compute per-policy history sums.
3. Emit adjustment rows + validation/exception reports.
4. Issue validator: sample 010310404C (and peers); zero change to non-candidate history bytes where possible; schema intact.
5. Publish modified `quikprmh.csv` to `Output/Test_Validation/` on PASS.

---

## 9. Exit criteria for Planning

- [x] Business Q&A confirmed (Eric)  
- [x] Source fields identified  
- [x] Target table/schema identified  
- [x] ISWL deferred  
- [x] Negative handling defined  
- [ ] Risk Review GO  
- [ ] Development Authorization  

**Next:** Risk Agent → Development Authorization → code.
