# Issue #167 — Discovery Notes (Search & Discuss)

**Issue:** #167 — Dividend Premium Payment
**Date:** 2026-09-09
**Framework stage:** Stage 0 Discovery (G-D)
**Code:** None
**Reported by:** Eric (via Warren)

---

## Client ask (verbatim + normalized)

> For policy 9010397528C, the dividend does not appear to have been paid on the 9/1/2026 anniversary. The dividend option is for dividend to Reduce Premium. Note dividend is larger than annual premium with remaining dividend paid in cash.

**Normalized:** On **9010397528C**, QLAdmin does not show a **9/1/2026** anniversary dividend. LifePRO election is **Reduce Premium** (`DIVIDEND=2`), and when the dividend exceeds annual premium the excess is paid in cash (`EXCESS_DIVIDEND=1`). Eric is seeing the 9/1/2026 event missing after load.

---

## Client symptom vs current Output

Anchor policy **9010397528C** (8/31/2026 Output):

| Table / field | Current value |
|---|---|
| `quikridr` phase 1 `MLASTANN` | **55** |
| `quikridr` phase 1 `MEFFDATE` | 19710901 |
| `quikmstr.MDIVOPT` | **2** (Reduce Premium) — matches LifePRO |
| `quikmstr.MMODEPREM` / `MMODE` | 60.00 / 12 (annual) |
| `quikmstr.MPAIDTO` / `MBILLTO` | 20260901 |
| `quikbenh` last dividend dates | **20250901** (no 20260901 row) |
| `quikdvpr` last row | 20250901 / 93.29 |

`MLASTANN` is **not** a LifePRO field. It is computed as `valuation_year − issue_year` (`2026 − 1971 = 55`) with **no month/day test**. Anniversary-accurate duration on an 8/31 valuation is **54**, because 9/1 has not occurred.

If QLAdmin treats `MLASTANN=55` as “the 9/1/2026 anniversary already ran,” it will not generate the missing dividend. That matches Eric’s symptom.

---

## Source findings

### PPBENTYP 8/31 (`PPBENTYP_BenefitType_Extract_20260831.csv`)

Base (TYPE_CODE=BA) for 9010397528:

| Field | Value |
|---|---|
| `DIVIDEND` | **2** (Reduce Premium) |
| `EXCESS_DIVIDEND` | **1** (excess to cash) |
| `DIVIDENDS_CREDITED` | 2118.81 |
| `ACCUM_DIVIDENDS` | 0.00 |

Fleet: **7** BA rows have `DIVIDEND=2`. Only **2** also have `EXCESS_DIVIDEND=1`: **9010397528** and **9010412641**. Conversion does **not** currently map `EXCESS_DIVIDEND`.

### PPBEN / PPOLC

- Issue date **19710901** (anniversary month/day = 9/1).
- `PAID_TO_DATE` / `PROCESSED_TO_DATE` already **20260901** on the 8/31 extract — that is the **paid-through** date from the **9/1/2025** premium, not proof that the 9/1/2026 dividend posted.

### PACTG 8/31 (`PACTG_Accounting_Extract20260831.csv`)

**No 9/1/2026 dividend posting** for this policy. We cannot convert a 2026 dividend that LifePRO has not written yet.

The **9/1/2025** anniversary is present and matches Eric’s reduce-premium + excess-cash note:

| Added | Effective | Debit / Credit | Amount | Meaning |
|---|---|---|---:|---|
| 20250902 | 20250901 | 516 / 12 | 93.29 | Dividend applied to reduce premium (full dividend) |
| 20250902 | 20250901 | 12 / 96 | 33.29 | Excess paid in cash |
| 20250902 | 20250901 | 12 / 110 | 60.00 | Annual premium applied (`60 + 33.29 = 93.29`) |

### What conversion emitted for 9/1/2025

`quikbenh` has **both** MBENTYP 1 and 2 on 20250901 at **93.29** each. Type 2 is the real 516 debit. Type 1 $93.29 comes from an earlier 20241114 debit-515 posting (later contra’d), not from the $33.29 excess-cash leg. Secondary data-quality note — not the 2026 miss.

---

## Current conversion path

| Layer | Path | Role |
|---|---|---|
| Duration | `app.py` `_compute_quikridr_mlastann` | Calendar-year only: `val.year − issue.year` |
| Issue date | `Sync_Rulebook_quikridr.csv` `ISSUE_DATE → MEFFDATE` | LifePRO PPBEN issue date |
| Valuation date | `QLA_VALUATION_DATE` | Batch date (8/31/2026) |
| ETI/RPU override | `_apply_issue76_eti_rpu_phase1_payup_mlastann` | Already anniversary-accurate from **paid-to** (#76 / #108B). This policy is Active 22 — override does not run. |
| Dividend option | `quikmstr.MDIVOPT` from PPBENTYP `DIVIDEND` via `DV_*` (#110) | Already **2** |
| Excess cash flag | LifePRO `EXCESS_DIVIDEND` | **Not mapped** |
| Dividend history | `qla_core/quikbenh_dividend_history_converter.py` (#114) | PACTG debit 0514–0518 → MBENTYP 1–5. 516→2, 515→1. Does not invent future anniversaries. |

---

## Current vs desired (working hypothesis)

| | Current (8/31 load) | Desired for QLAdmin to pay 9/1/2026 |
|---|---|---|
| `MLASTANN` | 55 (year-only) | **54** (anniversary not reached) |
| 9/1/2026 `quikbenh` row | Absent | Still absent from conversion — QLAdmin should **generate** it |
| `MDIVOPT` | 2 | 2 (keep) |
| Excess-to-cash | Unmapped | Confirm whether QLAdmin does this automatically when dividend > premium, or needs a flag |

---

## Related issues (Closed-row conflict check)

| Issue | Relationship |
|---|---|
| **#76 / #108B** | Same duration bug, already fixed for ETI/RPU only. Do **not** rewrite those rows from issue date; they stay on paid-to anniversary math. |
| **#110** | `MDIVOPT` recovered. This policy is already 2. Do not change the option map. |
| **#114 / #117** | Dividend history from PACTG. Do not invent a 20260901 history row on an 8/31 extract. Preserve MBENTYP 8/10/11/12. |
| **#60** | PUA inherits base `MEFFDATE`, so PUA `MLASTANN` will follow the shared calculator. |
| **#124** | `MLASTANNV` on QuikIswl is issue **date**, not duration. Unrelated. |

No Closed row says active-policy `MLASTANN` must stay calendar-year. #108B documented that calendar-year subtraction runs a year high when the anniversary has not occurred.

On current 8/31 Output, anniversary-accurate duration would drop `MLASTANN` by 1 on about **2,142** `quikridr` rows / **1,575** policies (**745** Active). ETI/RPU phase-1 (~314) stay on the #76 path.

---

## Proposed work list (Planning will refine — no code)

1. Change `_compute_quikridr_mlastann` to completed years using month/day vs `QLA_VALUATION_DATE` (same formula as #108B, from `MEFFDATE` / issue date).
2. Leave the ETI/RPU #76 override untouched.
3. Confirm with Eric/QLAdmin whether Reduce Premium + excess cash is automatic, or whether `EXCESS_DIVIDEND` needs a target field (only 2 policies).
4. Do **not** fabricate a 9/1/2026 `quikbenh` row from the 8/31 extract.
5. Optional later: 9/1/2025 type-1 $93.29 vs true excess cash $33.29 (history quality, not the 2026 miss).

---

## Open questions / defaults locked at Discovery

1. **Primary target:** `quikridr.MLASTANN` anniversary math — yes, unless Intake finds a different QLAdmin driver.
2. **Do we emit a 20260901 history row?** Default **no** on an 8/31 source cut. Revisit only if a post-9/1 LifePRO extract exists and Eric wants history converted rather than QLAdmin-generated.
3. **`EXCESS_DIVIDEND`:** open. Need QLAdmin field / Help confirmation.
4. **`MPAIDTO=20260901`:** leave as LifePRO paid-to unless anniversary processing also requires paid-to = last completed anniversary.

---

## Stop

Awaiting **“Proceed to Intake”**.
