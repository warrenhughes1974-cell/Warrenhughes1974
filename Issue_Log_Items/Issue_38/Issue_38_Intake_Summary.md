# Issue #38 — Intake Summary

**Issue:** Dividend Accumulations  
**Date:** 2026-07-03  
**Framework stage:** Intake complete (G0)  
**Status:** Approved → Planning  
**Owner:** Conversion (Warren) · **Reporter:** Eric · **Business status:** No-Go

---

## Client symptom

Dividend Accumulations do not appear in QLAdmin. Example policies: **010378830C**, **010380808C** (960 PO). LifePRO screenshots provided in `docs/960 PO - LifePRO Policy Screenshots.docx`.

---

## Normalized finding

QLAdmin reads dividend deposit balances from **`quikdvdp.MDEPOSIT`**. Both sample policies exist in `quikdvdp.csv` but carry **`MDEPOSIT = 0.00`** while LifePRO **`PPBENTYP.ACCUM_DIVIDENDS`** shows **$9,888.08** and **$9,220.33** respectively.

This is **not** Issue #21D (wrong **interest rate** on `MDEPINT`). Issue #38 is a **balance wipe** affecting **59 policies** fleet-wide (8 are 960 PO).

---

## Root cause (confirmed at intake)

Post-rulebook **QUIKDVDP ENRICHMENT** in `QLA_Migration/app.py` forces `MDEPOSIT = "0.00"` when the PACTG transaction cache misses. The cache builder uses hardcoded **`PACTG_Accounting_Extract20260427.csv`**, which is **absent** from Source (only **`20260530`** exists). Cache never builds → all 5,083 rows zeroed.

---

## Example policies

| QLAdmin | LifePRO | Plan | Source `ACCUM_DIVIDENDS` | Output `MDEPOSIT` |
|---------|---------|------|-------------------------:|------------------:|
| 010378830C | 9010378830 | 960 PO | 9,888.08 | 0.00 |
| 010380808C | 9010380808 | 960 PO | 9,220.33 | 0.00 |

---

## Domain and scope (first pass)

| In scope | Out of scope (initial) |
|----------|------------------------|
| `quikdvdp.MDEPOSIT` balance restoration | `quikbenh` dividend history (client-side per Issue #34) |
| PACTG cache path / enrichment logic | Issue #21D ISWL `MDEPINT` regression |
| Population: 59 policies with source balance > 0 | Fleet-wide premium / MPREM (#26) |

---

## Related issues

| Issue | Relationship |
|-------|--------------|
| #21D | Same table (`quikdvdp`); fixed `MDEPINT` only; noted MDEPOSIT unchanged |
| #25 | MPOLICY padding — must not regress |
| #26 | MPREM mapping — must not regress |

---

## Blockers visible at intake

- `PEVNTNONFC` extract missing (rulebook references for `MINTYTD` / `MINTDATE`)
- Screenshot doc is image-only (dollar amounts confirmed from source extract)

---

## G0 gate

- [x] Issue folder created
- [x] Intake summary written
- [x] Example policies listed
- [x] Owner assigned
- [x] No code or rulebook changes

**Next stage:** Planning Agent
