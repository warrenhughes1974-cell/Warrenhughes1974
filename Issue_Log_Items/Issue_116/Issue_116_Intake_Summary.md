# Issue #116 — Intake Summary

**Issue:** #116 — QuikDvdp interest-paid-to date loaded from the premium paid-to date (negative accrued interest in QLAdmin)
**Date:** 2026-07-25
**Framework stage:** Intake (Stage 1 of 8)
**Status:** Intake
**Owner:** Warren
**Assigned:** Warren
**Priority:** Go-No Go
**Raised by:** Warren, 2026-07-25 (from a QLAdmin Dividend History screen review with Eric)
**Related:** #38 (quikdvdp MDEPOSIT / MINTYTD / MINTDATE), #21D (ISWL MDEPINT), #114 (dividend history), #117 (dividend ledger completeness)

---

## Symptom

QLAdmin's Dividend History window for policy **9010380808C** shows **Accrued Interest of −$126.93** against a Current Balance of $9,220.33. Interest Paid To reads **12/01/2026** — five months in the future.

QLAdmin accrues from Interest Paid To to the current date. A future date produces a negative period and therefore a negative accrual. Confirmed against a production QLAdmin policy (02792356W): balance $72.90 × Int Rate 4.50% × 266 days ÷ 365 = **$2.39**, matching the $2.38 shown on that screen. The formula is not in doubt.

---

## Root cause (identified during intake)

`quikdvdp.MINTDATE` is being populated from `quikmstr.MPAIDTO` — the **premium** paid-to date — on **every row in the table**, because the PACTG 641 enrichment that is supposed to supply the real interest date never matches a policy.

The cache is keyed through `Master_Crosswalk`:

| Item | Value |
|------|-------|
| Cache key built at `app.py` 7319 | `cw_map.get('9010380808')` → **`010380808C`** |
| Lookup key at `app.py` 8394 (`tp`) | emitted MPOLICY → **`9010380808C`** |

The crosswalk `New_Value` drops the leading `9`, so the two key spaces never intersect. The batch log records the cache building successfully — `Auto-loaded quikdvdp PACTG 641 cache (63 policies)` — and it is then never read.

The adjacent `quikridr_mplan_cache` in the same block is keyed off emitted output and works correctly (2,268 rows correctly receive the ISWL `MDEPINT` of 4.50). That is the pattern to copy.

---

## Measured before-state (v58.36 Output)

| Measure | Value |
|---|---|
| `quikdvdp` rows | 5,083 |
| Rows where `MINTDATE` == `quikmstr.MPAIDTO` | **5,083 (100%)** |
| Rows where `MINTYTD` == `0.00` | **5,083 (100%)** |
| Rows with a future-dated `MINTDATE` | 992 |
| Policies with `MDEPOSIT` > 0 | 59 |
| **Policies displaying negative accrued interest** | **16** |
| PACTG 641 interest rows available but unused | 788 rows / 63 policies / $49,071.94 |

Every one of the 59 policies that actually carries a dividend accumulation balance has PACTG 641 activity, so all 59 can be given a correct interest date.

---

## Reference: what the field should hold

Production QLAdmin policy 02792356W (screenshot supplied by Warren, 2026-07-25):

| Field | Value | Source |
|---|---|---|
| Interest Paid To | 11/01/2025 | date of the **last interest posting** on the policy |
| premium Paid To | 11/01/2013 | unrelated field, twelve years apart |
| Current Balance | 72.90 | `MDEPOSIT` |
| Int Rate | 4.50 | `MDEPINT` |
| Accrued Interest | 2.38 | derived by QLAdmin, not stored |

The two dates are independent. Loading the premium date into the interest date is unambiguously wrong.

---

## Scope

**In scope**

- Correct the `quikdvdp` PACTG 641 cache key so `MINTDATE` and `MINTYTD` resolve
- Re-emit `quikdvdp`; publish to `Output/Test_Validation/` on validator PASS
- Validation report under `QLA_Migration/Reports/`

**Out of scope**

- `MDEPINT` rate values — **Eric confirmed 2026-07-25 that the rates in QLAdmin are correct**; #21D Track A logic stands unchanged
- `MDEPOSIT` sourcing (#38 — working correctly, ties to `PPBENTYP.ACCUM_DIVIDENDS`)
- Adding MBENTYP 6 / 7 dividend history rows (#117)
- The `MPAIDTO` fallback itself — retained for the 5,020 zero-balance rows
- Any change to `quikmstr`, `quikridr` or `Master_Crosswalk`

---

## Affected path (anticipated)

- `app.py` and `QLA_Migration/app.py` — the `quikdvdp` 641 cache build (~line 7319), version bump
- `QLA_Migration/Reports/issue116_*.csv` — validation
- `QLA_Migration/Output/quikdvdp.csv` — re-emitted
- `QLA_Migration/Output/Test_Validation/quikdvdp.csv` — published on PASS

---

## G0 gate

| Criterion | Result |
|-----------|--------|
| Issue scoped | Yes |
| Symptom measurable from current Output | Yes — 5,083/5,083 rows wrong; 16 policies visibly negative |
| Source artifacts identified | Yes — PACTG 641 rows present in `Source/` |
| Root cause identified | Yes — cache key space mismatch, single call site |
| Severity / owner assigned | Yes — Go-No Go, Warren |

**G0 PASS** — proceed to Planning.
