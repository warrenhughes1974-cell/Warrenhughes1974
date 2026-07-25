# Issue #114 — Dependency Gate

**Issue:** #114 — Total dividends credited not converted (dividend history absent from QuikBenh)
**Framework stage:** Dependency Gate (Stage 3 of 8)
**Generated:** 2026-07-25
**Agent:** Cursor Grok 4.5
**Code changes:** none (prohibited at this stage)

---

## Status: **PASS**

All required source data, field definitions and evidence are in hand. Four edge-case business questions remain open, but each carries a **safe non-blocking default that emits no guessed data** — unmapped rows route to an exception report rather than into `quikbenh`. Together they represent **$40,167.36 of $1,889,445.44 (2.1%)** and **14 of 593 policies**. Proceed to Risk.

---

## 1. Checklist

### Source data

| Check | Met? | Evidence |
|-------|------|----------|
| Required LifePRO extract(s) present in `QLA_Migration/Source/` | **Met** | `PPBENTYP_BenefitType_Extract_20260630.csv` (14.29 MB), `PACTG_Accounting_Extract20260630.csv` (803.06 MB) |
| Extract row count > 0 | **Met** | PPBENTYP 7,002 data rows / 5,083 policies; PACTG 404,450 policy rows |
| Column headers documented (not just Excel letters) | **Met** | Client cited "column M"; confirmed as `DIVIDENDS_CREDITED`, 13th column of 133 |
| Extract date/version matches batch under test | **Met** | Both dated 20260630, same drop feeding v58.35 Output |
| Re-extract required? | **N/A** | No — lifetime total and 2018-forward transactions both present. A pre-2018 PACTG re-pull would remove the need for Layer B but is **not** required; #21F set the precedent for plugging the gap instead. |

### Field definitions

| Check | Met? | Evidence |
|-------|------|----------|
| QLAdmin target table confirmed | **Met** | QuikBenh — Help §5.1.2.6 p.85 (Dividend History window sources) + §7.47 p.724 (schema) |
| QLAdmin target field semantics confirmed | **Met** | `MPOLICY` C10, `MBENTYP` C2, `MDATE` D8, `MBEN` N10.2 |
| LifePRO source field semantics confirmed | **Met** | `DIVIDENDS_CREDITED` lifetime total; election codes 514–518 per LifePRO Accounting Transaction Information §05xx |
| Transformation notes identified | **Met** | §6 of Planning Report — dates, money, benefit type, padding, idempotency |
| Benefit type code list confirmed | **Met** | QLAdmin Help §6.5 p.649 — codes 1–5 are the five dividend dispositions |
| Code→type mapping validated against data | **Met** | Option 4 policies post exclusively under 517, option 3 under 514, option 2 under 516, option 1 under 515 — 1:1 with QLAdmin option codes |

### Client clarification

| Check | Met? | Evidence |
|-------|------|----------|
| Scope boundary agreed (in / out) | **Met** | Eric 2026-07-25: lifetime dividends into the dividend history table; two components supplied for cost basis, not a computed basis. Warren confirmed same day. |
| Business rule for edge cases (fallback, blank, zero) | **Met with defaults** | Four open questions below; all default to exception-report, none emit guessed data |
| Retention / filtering rules | **Met** | Exclude reversals, counterparty codes, 641 interest, 562/563 surrenders — documented in Planning §4 |
| UAT acceptance criteria stated | **Met** | Per policy, sum of `quikbenh` MBENTYP 1–5 equals `PPBENTYP.DIVIDENDS_CREDITED`; Dividend History window populated for 593 policies |

### Evidence

| Check | Met? | Evidence |
|-------|------|----------|
| Example policies identified | **Met** | 9010431301, 9010435671, 9010143726, 9010412641, 9010463017 — traced to transaction level |
| Screenshots or docx support client claim | **Met** | Eric's email names the extract and column; verified directly against the file |
| Before-state measurable from current output | **Met** | `quikbenh` MBENTYP 1–5 = **0 rows** at v58.35; `quikdvpr` 31 rows / $4,846.21 |

### Regression guards

| Check | Met? | Evidence |
|-------|------|----------|
| Plan preserves Issue #25 MPOLICY padding | **Met** | `format_qladmin_mpolicy` used for all emitted keys |
| Plan preserves Issue #26 MPREM mapping | **Met** | `quikridr` not touched |
| Plan preserves Issue #21F CONV_ADJ premium rows | **Met** | `quikprmh` not touched; gross-on-both-sides convention documented |
| Plan preserves Issue #38 / #21D dividend accumulations | **Met** | `quikdvdp` not touched |
| Plan preserves Issue #110 MDIVOPT | **Met** | `quikmstr` read-only (option used to type plug rows) |
| Plan preserves Issue #34 MBENTYP 8 and #54 MBENTYP 10/11/12 | **Met** | Strip-and-rebuild limited to MBENTYP 1–5 via `replace_types` guard |
| Plan does not alter unrelated rulebooks | **Met** | New converter module + new rules JSON; no edits to existing `Sync_Rulebook_*.csv` |

---

## 2. Open items carried forward (non-blocking)

| # | Question | Policies | $ | Default if unanswered |
|---|----------|---------:|--:|----------------------|
| OQ-1 | Dividend option **6 = Reduce Loan** (Product Book 12-263). QLAdmin has no dividend-to-loan benefit type; nearest is 12, already owned by #54. | 7 | 21,283.44 | Exception report — no plug row emitted |
| OQ-2 | `TYPE_CODE = OR` rider rows carry dividends; #21F excluded OR from premium totals | 3 | 18,719.96 | Exclude, matching #21F; list in exceptions |
| OQ-3 | 4 policies have dividends credited but a blank dividend option | 4 | 163.96 | Exception report — no benefit type derivable |
| OQ-4 | `quikdvpr` holds 31 historical rows but QuikDvpr is the forward "Dividends to Pay Premium" schedule (Help §7.87) | 6 | 4,846.21 | Leave untouched in #114; raise as a separate issue |
| OQ-5 | Confirm New Era accepts deriving cost basis outside QLAdmin (no life basis field exists) | — | — | #21G decision stands; #114 delivers the component |

**Combined exposure of OQ-1 through OQ-3:** 14 policies, $40,167.36 — **2.1%** of the lifetime dividend total. The remaining **$1,849,278.08 across 579 policies** maps unambiguously.

Note OQ-1, OQ-2 and OQ-3 overlap slightly by policy but not by dollar; totals above are dollar-additive.

---

## 3. Blockers

**None.**

No missing extract, no undefined QLAdmin field, no absent example policies. Under the Dependency Gate stop conditions, none of the four stop-condition rows apply: the extracts are present, the target field definitions are documented in the QLAdmin Help schema, and the business rule for every edge case has a documented conservative default that withholds data rather than inventing it.

---

## 4. Recommended issue status update

**Ready for Risk Review**

---

## G2 gate criteria

- [x] Dependency gate document published
- [x] Status is PASS
- [x] Tracking sheet row published (`Issue_114_Tracking_Sheet_Row.tsv`)
- [x] No code changes made
