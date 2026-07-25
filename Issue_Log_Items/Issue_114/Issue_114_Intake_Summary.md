# Issue #114 — Intake Summary

**Issue:** #114 — Total dividends credited not converted (dividend history absent from QuikBenh)
**Date:** 2026-07-25
**Framework stage:** Intake (Stage 1 of 8)
**Status:** Intake
**Owner:** Warren
**Assigned:** Warren
**Priority:** Go-No Go
**Raised by:** Eric (New Era), 2026-07-25
**Related:** #21F (premium history conversion adjustment), #21G (cost basis staged only), #38 (dividend accumulations), #54 (QuikBenh loan history), #110 (MDIVOPT), #84 (quikclms DIVIDENDS)

---

## Client statement

> "The total dividends paid are included in the PPBENTYP_BenefitType_Extract. It is column M titled Dividends Credited."

> "We need to do what we did with the premium history because the total dividends credited is needed for cost basis."

Eric is asking for the **Issue #21F pattern applied to dividends**: LifePRO holds a lifetime dividend total in a single field, and he wants that total represented in QLAdmin so the adjusted cost basis (premiums paid − dividends received) can be derived at surrender.

---

## Symptom

QLAdmin carries effectively no dividend history. Against LifePRO's lifetime figure of **$1,889,445.44 across 593 policies**, the current Output holds:

| Target | Present today | Note |
|--------|--------------|------|
| `quikbenh` MBENTYP 1–5 (dividend benefit types) | **0 rows** | Dividend history window is empty |
| `quikdvpr` (MPOLICY/MDATE/MDIV) | 31 rows / 6 policies / $4,846.21 | Wrong table — QuikDvpr is "Dividends to Pay Premium", a forward apply schedule |
| `quikdvdp.MDEPOSIT` | 59 policies / $240,248.25 | Accumulation **balance** only (#38) — not lifetime credited |
| `quikmstr.MDIVOPT` | 811 non-zero (#110) | Election code only, no dollars |

Net effect: the QLAdmin Dividend History window is blank for the entire book, and one of the two components required for cost basis is missing.

---

## Confirmed during intake

1. **Source is present.** `PPBENTYP_BenefitType_Extract_20260630.csv` column M `DIVIDENDS_CREDITED` — 593 policies non-zero, $1,889,445.44, carried entirely on `TYPE_CODE = BA` rows. `SU_DIV_CREDITED`, `PU_DIV_CREDITED` and `SL_DIV_CREDITED` are all zero, so unlike #21F this is a single-component figure, not a four-part sum.
2. **Real dividend transaction history also exists** in `PACTG_Accounting_Extract20260630.csv` under the LifePRO dividend election codes (514/515/516/517), roughly 2,500 rows across 413 policies totalling **$402,010.24** — but only from **2018-01-01**, the same extract floor that forced #21F.
3. **QLAdmin target is confirmed.** The Dividend History window reads `QuikBenh` (Policy Benefit History) using Policy Benefit Type Codes 1–5. `QuikDvpr` is a different table and is not the dividend history.
4. **QLAdmin does not compute life cost basis.** Manual review found cost-basis fields for annuities only (`QuikAbal.MBASIS`, `QuikPcwa.MCOSTBASIS`). Consistent with the #21G finding. Client wants the two components loaded so basis can be derived, not calculated by QLAdmin.

---

## Scope

**In scope**

- Emit dividend history rows to `quikbenh` (`MPOLICY`, `MBENTYP`, `MDATE`, `MBEN`) for benefit types 1–5
- Load real 2018-forward dividend transactions from PACTG dividend election codes
- Add one dated conversion-adjustment row per policy for the pre-2018 remainder so each policy ties to `DIVIDENDS_CREDITED`
- Validation + exception reporting under `QLA_Migration/Reports/`

**Out of scope**

- Any change to `quikprmh` or the #21F premium adjustment
- Any change to `quikdvdp.MDEPOSIT` (#38) or `quikmstr.MDIVOPT` (#110)
- Loading a computed cost basis figure (#21G decision stands — no QLAdmin life basis field)
- Re-pointing or removing the existing 31-row `quikdvpr` load (raised as an open question, deferred)
- `quikclms.DIVIDENDS` decomposition (#84 Track B, blocked on #85)

---

## Affected path (anticipated)

- `qla_core/quikbenh_dividend_history_converter.py` (new — mirrors #54 loan-history converter)
- `plan_governance/config/quikbenh_dividend_history_rules.json` (new)
- `app.py` + `QLA_Migration/app.py` — wiring at the existing `quikbenh` emit block, version bump
- `QLA_Migration/Reports/issue114_*.csv` — validation + exceptions

---

## G0 gate

| Criterion | Result |
|-----------|--------|
| Issue scoped | Yes |
| Symptom measurable from current Output | Yes — 0 dividend rows vs $1.89M expected |
| Source artifacts identified | Yes — PPBENTYP + PACTG, both in `Source/` |
| Severity / owner assigned | Yes — Go-No Go, Warren |

**G0 PASS** — proceed to Planning.
