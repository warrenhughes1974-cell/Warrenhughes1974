# Issue #116 — Dependency Gate

**Issue:** #116 — QuikDvdp interest-paid-to date loaded from the premium paid-to date
**Framework stage:** Dependency Gate (Stage 3 of 8)
**Generated:** 2026-07-25
**Agent:** Cursor Grok 4.5
**Code changes:** none (prohibited at this stage)

---

## Status: **PASS**

Root cause is located to a single call site, the source data is present, the target field
semantics are confirmed against both the QLAdmin manual and a live production policy, and
the one business variable in the area (the crediting rate) has been confirmed by the client
as correct and is out of scope. No open questions block Development.

---

## 1. Checklist

### Source data

| Check | Met? | Evidence |
|-------|------|----------|
| Required LifePRO extract present | **Met** | `PACTG_Accounting_Extract20260630.csv` — 788 non-reversed 641 rows across 63 policies, $49,071.94 |
| Extract covers every affected policy | **Met** | All 59 policies with `MDEPOSIT` > 0 have 641 activity |
| Extract date matches batch under test | **Met** | 20260630, same drop feeding v58.36 |
| Re-extract required? | **N/A** | Data is present and already being read — it is discarded on a key mismatch |

### Field definitions

| Check | Met? | Evidence |
|-------|------|----------|
| QLAdmin target table confirmed | **Met** | `QuikDvdp` — schema `MPOLICY, MDEPOSIT, MINTYTD, MDEPINT, MINTDATE` |
| `MINTDATE` semantics confirmed | **Met** | Production policy 02792356W: Interest Paid To 11/01/2025 = date of the last interest posting, while premium Paid To is 11/01/2013 — the two are independent fields |
| Accrual formula confirmed | **Met** | 72.90 × 4.50% × 266/365 = 2.39 vs 2.38 displayed — QLAdmin accrues from `MINTDATE` to the current date |
| LifePRO source field semantics confirmed | **Met** | PACTG account 0641 "Interest on Dividend Accums" (LifePRO Accounting Transaction Information); credited to account 0310, the accumulation balance |
| Transformation notes identified | **Met** | Planning §3 — key space only; filter, date selection and YTD logic already correct |

### Client clarification

| Check | Met? | Evidence |
|-------|------|----------|
| Scope boundary agreed | **Met** | Warren 2026-07-25: fix the date; leave rates alone |
| Crediting rate (`MDEPINT`) | **Resolved — out of scope** | Eric confirmed 2026-07-25 that the rates in QLAdmin are correct. #21D Track A stands. |
| Business rule for policies with no 641 activity | **Met** | Retain the existing `MPAIDTO` fallback; all such rows carry `MDEPOSIT` 0.00 so nothing is displayed |
| UAT acceptance criteria stated | **Met** | No policy with a balance shows negative accrued interest; `MINTDATE` equals the last 641 posting for all 59 |

### Evidence

| Check | Met? | Evidence |
|-------|------|----------|
| Example policies identified | **Met** | 9010380808C traced end to end; 59-policy projection published |
| Screenshot supports the claim | **Met** | Two QLAdmin screens supplied by Warren 2026-07-25 — the defect (9010380808C, −126.93) and the reference (02792356W, +2.38) |
| Before-state measurable from current Output | **Met** | 5,083/5,083 rows have `MINTDATE` == `MPAIDTO`; 5,083/5,083 have `MINTYTD` 0.00 |
| Root cause proven, not inferred | **Met** | `Master_Crosswalk.csv` line 60 maps `9010380808` → `010380808C`; emitted `MPOLICY` is `9010380808C` |

### Regression guards

| Check | Met? | Evidence |
|-------|------|----------|
| Plan preserves #38 `MDEPOSIT` | **Met** | Enrichment writes only `MINTYTD` / `MINTDATE` |
| Plan preserves #21D `MDEPINT` | **Met** | ISWL branch untouched; 4.00 / 4.50 split asserted in validation |
| Plan preserves #25 MPOLICY padding | **Met** | Fix routes through the existing `_format_qladmin_mpolicy` helper |
| Plan preserves #110 `MDIVOPT` | **Met** | `quikmstr` not written |
| Plan preserves #114 `quikbenh` | **Met** | Different table; not touched |
| Plan does not alter rulebooks | **Met** | `Sync_Rulebook_quikdvdp.csv` unchanged |
| Blast radius bounded | **Met** | 59 of 5,083 rows change; the other 5,024 must be byte-identical |

---

## 2. Open items carried forward

**None blocking.**

| # | Item | Default |
|---|------|---------|
| OQ-1 | ~990 zero-balance rows keep a future-dated `MINTDATE` from the `MPAIDTO` fallback | Leave as-is — `MDEPOSIT` is 0.00 so no accrual is displayed (Planning §5) |

---

## 3. Blockers

**None.** The extract is present, the target field definition is documented and corroborated
by production data, the example policies are traced, and the only business variable in the
area has been confirmed by the client.

---

## 4. Recommended issue status update

**Ready for Risk Review**

---

## G2 gate criteria

- [x] Dependency gate document published
- [x] Status is PASS
- [x] Tracking sheet row published (`Issue_116_Tracking_Sheet_Row.tsv`)
- [x] No code changes made
