# Issue #34 — QUIKISRR Late SME Scope Reconciliation

**Issue:** #34 — ISWL QuikIsrr (Partial Surrender)
**Date:** 2026-07-02
**Mode:** Planning and scope reconciliation only — **no development, no QuikIsrr.csv, no loader/validator changes**
**Trigger:** Late SME field-level guidance on QLAdmin partial surrender processing
**Final recommendation:** **READY AFTER SME CONFIRMATION** (see §K)

> **2026-07-02 (Final SME Sign-Off Package):** Seven approve/correct questions consolidated in [`Issue_34_Final_SME_Signoff_Package.md`](Issue_34_Final_SME_Signoff_Package.md). This document's analysis remains authoritative; the sign-off package is the SME action surface.

---

## A. Late SME impact summary

The SME's new guidance describes what **live QLAdmin partial surrender processing** creates: QuikClms, QuikClmp, QuikBene/QuikBenh ("QuikBenh for converted records"), QuikIsrr, and a transaction audit record. This **contradicts the closed Q11 decision** (QuikIsrr-only) in one critical way: the earlier Option 1 assumed QLAdmin does not need companion claim records for pre-conversion history. The SME's explicit statement "QuikBenh **for converted records**" and the full field mappings for QuikClms/QuikClmp indicate the SME expects the **full record set for converted partial surrenders too**.

Impact on closed decisions:

| Closed decision | Late-SME impact |
|-----------------|-----------------|
| Q11 QuikIsrr-only | **REOPENED** — SME field guidance implies full package (QuikClms + QuikClmp + QuikBenh + QuikIsrr) |
| Q7 MISWL = PFNDR.VALUATION_DATE | **NARROWLY REOPENED** — SME's QuikIsrr field list omits MISWL entirely (see §G) |
| Candidate rule (PACTG 0561, no reversals, no 9010780411) | **UNCHANGED** — 3,623 rows / 636 policies / $1,217,593.55 reconfirmed |
| MSURRDATE = EFFECTIVE_DATE, MSURRAMT = gross TRANS_AMOUNT | **UNCHANGED** — consistent with SME "amount is whatever the user input; no adjustments" |
| Output path `QLA_Migration/Output/QuikIsrr.csv` | **UNCHANGED** |
| Full-surrender status 55 guidance | **NOT APPLICABLE to PR-7** — QuikIsrr is partial-only; no status changes for partials (SME statement 2). Noted for future full-surrender work. |

---

## B. Revised scope assessment

| Option | Description | Assessment |
|--------|-------------|------------|
| **A — QuikIsrr-only** | Original closed plan | **No longer defensible alone** — SME field guidance explicitly covers converted records; QuikIsrr-only would leave QLAdmin claim seek (policy + phase 0) empty for 3,623 historical events |
| **B — Full package** | QuikClms + QuikClmp + QuikBenh + QuikIsrr (audit optional) | **Recommended target scope** — matches SME processing model; QuikClms/QuikClmp infrastructure already exists in this repo; QuikBenh is a simple 4-field table |
| **C — Staged** | PR-7A QuikIsrr, PR-7B companions | Viable fallback **only if** SME confirms QuikIsrr is independently loadable; not recommended because MISWL semantics (§G) and companion scope share the same SME session |

**Recommendation: Option B**, excluding the transaction audit record (see §C — QuikAudt is a before/after-image memo table that cannot be authentically reproduced for historical events; recommend SME sign-off on exclusion).

---

## C. Existing output / schema inventory

| Table | QLAdmin Help | Output CSV | Schema in repo | Writer in repo | Notes |
|-------|--------------|------------|----------------|----------------|-------|
| **QuikClms** | §7.67 Death Claims (CLAIMSTAT 99 = Surrenders) | `Output/quikclms.csv` — 2,114 rows | `app.py QUIKCLMS_SCHEMA` + `validation_config/schema_manifest.json` | **Yes** — claims pipeline (UAT emit, DBF, validation) | All rows `MPHASE=1`, `MSEQ=0`; **zero** partial-surrender rows; **no phase-0 rows** → no collision with SME seek rule |
| **QuikClmp** | §7.66 Death Claim Payee Details | `Output/quikclmp.csv` — 1,709 rows | Same manifest + `Sync_Rulebook_quikclmp.csv` | **Yes** — claims pipeline | Payee fields already populated from converted client data for death claims — **reusable pattern** |
| **QuikBenh** | §7.47 Policy Benefit History — `MPOLICY C10, MBENTYP C2, MDATE D8, MBEN N10.2`, index MPOLICY+DToS(MDATE) | **None** | **None** | **None** | Client Loyal2QL converter notes quikbenh "done" (dividend history written there). New emit must **coordinate**: client-side loader must append, not replace |
| **QuikBene** | §7.45 Policy Benefits — identical 4 fields | **None** | **None** | **None** | Client converter: "opened/cleared only". SME prefers **QuikBenh** for converted records — adopt QuikBenh |
| **QuikIsrr** | §7.143 — `MPOLICY C10, MSURRDATE D8, MSURRAMT N10.2, MISWL D8`, index MPOLICY | **None** (by design — PR-7) | Planning docs only | **None** (by design) | PFNDR readiness validated (99.83%) but see §G |
| **Transaction audit (QuikAudt)** | §7.41 — `MUSER, MDATE, MTIME, MDBF, MPOLICY, MAUDIT(memo)` | **None** | **None** | **None** | Before/after policy images — not reproducible for historical events; **recommend exclude** |

**Reuse verdict:** the claims pipeline (rulebook derivation, UAT emit, money-field formatting, DBF generation, cross-table MPOLICY validation) is directly reusable for the QuikClms/QuikClmp portion. QuikBenh and QuikIsrr are simple appends by comparison (4 fields each) but need new isolated writers.

---

## D. Source availability for payee / owner fields

Tested against the 636 candidate policies (QLAdmin key form `NNNNNNNNN + C`):

| Requirement | Source | Coverage |
|-------------|--------|----------|
| Owner identity | `Output/quikclid.csv` `MRELATION = OWNR` | **634 / 636 policies (99.7%)** |
| Primary insured fallback | `quikclid` `MRELATION = INSD` | 1 additional policy (`010834096C`, client 602820) |
| No owner or insured link | — | **1 policy: `010826551C`** (only SERV + BENP links) — needs disposition (use SERV/BENP payee, source lookup, or exception) |
| Owner name (MPAYNAME = LastFirstName) | `Output/quikclnt.csv` `MLNAME/MFNAME` | **607/607 owner clients — 0 blank** |
| Owner address 1 / city / state / zip | `quikclnt` `MADDR1, MCITY, MSTATE, MZIP, MZIP2` | **0 blank addr1/city** across all 607 owner clients |
| Owner Tax ID (MTIN) | `quikclnt.MTAXID` | **59 of 607 owner clients blank or `000000000`** — matches existing death-claim payee handling; confirm blank-TIN emit is acceptable |
| Raw source fallback | `Source/RelationshipNameAddress_Extract_20260530.csv` (84.8 MB) | Available if converted tables are insufficient |

**Zip note:** SME said "Owner ZipFull" → QuikClmp splits `MPAYZIP` (5) + `MPAYZIP2` (+4); quikclnt already stores `MZIP`/`MZIP2` split — direct mapping.

**Verdict:** owner/payee data is **available and high quality** — 634/636 direct, 1 fallback, 1 exception.

---

## E. Claim sequence design

SME rule: for a partial, seek **policy + phase 0** in QuikClms; find max sequence among existing partials; add 1.

Repo evidence:

- Existing `quikclms.csv`: all 2,114 rows are `MPHASE = 1`, `MSEQ = 0` (death/full-surrender/disbursement claims). **No phase-0 rows exist.**
- Therefore for every candidate policy, max existing partial sequence = 0 → historical partial sequences start at **1**.

Proposed design (needs SME sign-off on phase value):

```text
For each policy in the 3,623-row candidate set:
  order events by EFFECTIVE_DATE, then DATE_ADDED, then RECORD_SEQUENCE
  MSEQ = 1, 2, 3, ... per policy (QuikClms.MSEQ = QuikClmp.MSEQ per event)
  MPHASE = 0 on QuikClms/QuikClmp partial rows (per SME seek rule)
```

- **Existing QuikClms rows:** must be **considered** (scan for policy+phase-0 max seq) but never modified. Today the scan trivially returns 0 everywhere; the design stays correct if client-side data ever adds phase-0 rows.
- **Open (NEEDS SME):** SME field list says `MPHASE = Phase` while the seek rule says phase 0. Confirm converted partial rows carry **MPHASE = 0** (recommended — matches the seek rule and avoids key collision with existing phase-1 death/surrender claims on the same policies; 306 of 636 candidate policies already have phase-1 claim rows).

---

## F. Date and amount mapping

### Date semantics

The SME distinguishes maintenance date vs processed/system date. Source evidence on the 3,627 unreversed fleet 0561 rows: `DATE_ADDED` is **never blank**, spans **2018–2026** (true historical posting dates), equals `EFFECTIVE_DATE` on 2,415 rows, is later on 1,171, earlier on 41 (backdated postings).

| SME term | Recommended source | Rationale |
|----------|-------------------|-----------|
| Date of transaction / maintenance date | **`PACTG.EFFECTIVE_DATE`** | Already the closed MSURRDATE decision (Q12); reversal chains keep EFFECTIVE_DATE stable |
| Date transaction processed / system date | **`PACTG.DATE_ADDED`** — **not** conversion run date | These are historical records; stamping the 2026 conversion date on 2018–2025 events would misdate all history. DATE_ADDED is the authentic LifePRO processing date, present on 100% of rows |

Field-level application:

| Field | Source |
|-------|--------|
| QuikClms `DTOFDEATH`, `RPTDATE` | `EFFECTIVE_DATE` (SME: date of transaction / maintenance date) |
| QuikClms `PDDATE`, `ACCPTDATE` | `DATE_ADDED` (SME: processed / system date) |
| QuikClmp `MPMTDATE` (and `MCHKDATE` if populated) | `DATE_ADDED` |
| QuikBenh `MDATE` | `DATE_ADDED` |
| QuikIsrr `MSURRDATE` | `EFFECTIVE_DATE` (unchanged) |

Note: SME wrote `DTODEATH`; the QLAdmin/converter schema field is `DTOFDEATH` (`ORIGSTTUS` in the emitted CSV header vs Help's `ORIGSTATUS` — follow the emitted header). The 41 backdated rows (DATE_ADDED < EFFECTIVE_DATE) should be flagged in validation, not excluded.

### Amount semantics

SME statement 2: partials have **no adjustments**; all amounts identical to user input. Confirmed final mapping — single source, no netting:

```text
PACTG 0561 TRANS_AMOUNT (gross)
  → QuikClms.MFACE
  → QuikClms.MPAID
  → QuikClmp.MAMOUNT
  → QuikClmp.MGROSS
  → QuikBenh.MBEN
  → QuikIsrr.MSURRAMT
```

Fixed values per SME: QuikClmp `MHDPMT=C`, `MHDCODE` blank, `MBANKNO` blank, `MHOLDINT=0.00`, `MFEDTAX=0.00`, `MSTTAX=0.00`; QuikClms `CLAIMSTAT=99` (Help §7.67 confirms 99 = Surrenders), `CAUSE=SRR` (fits C3); QuikBenh `MBENTYP=8`.

**Open (NEEDS SME):** `ORIGSTATUS` = "policy status before processing surrender" — for historical events the point-in-time status is not in the extracts. Recommend a fixed premium-paying status code (converted quikmstr uses numeric codes; `22` is the dominant active status) or blank; SME to choose.

---

## G. MISWL reassessment

**Does the QuikIsrr schema include MISWL?** **Yes** — verified directly from `docs/claims_conversion_reference/QLAdmin_Help.pdf` §7.143: `MISWL DATE 8.0 — "Monthiversary date the transaction was added to the UL/ISWL table"`. The SME's field list (MPOLICY, MSURRDATE, MSURRAMT) **omits it**.

**Is the PFNDR-derived value semantically correct?** **Questionable.** The PFNDR readiness pass matched 99.83% mechanically, but PFNDR is a **point-in-time snapshot** (one valuation date per policy, clustered in **May 2026**). "First VALUATION_DATE ≥ MSURRDATE" therefore assigns the 2026 snapshot date to events from 2018–2025 — that is the snapshot date, **not** the historical monthiversary on which the transaction entered the UL/ISWL table. The match-rate success masked this semantic gap.

**Repo precedent:** QLAdmin's QuikPrmh schema (§7.191) also contains MISWL ("ISWL date"), and the production `Output/quikprmh.csv` (205,577 rows) **omits the MISWL column entirely** — converted history in this project already treats MISWL as system-managed/omitted.

**SME's own model:** MISWL describes when live processing posts to the UL/ISWL value table. For converted records, QLAdmin rebuilds ISWL values post-load (or the field remains blank as with QuikPrmh).

**Recommendation (NEEDS SME — one question):** emit QuikIsrr **with MISWL blank** (or column omitted, matching the QuikPrmh precedent), consistent with the SME field list. Retire the PFNDR match rule for population purposes; keep the PFNDR readiness artifacts as source-coverage evidence. If the SME instead requires MISWL populated, the PFNDR snapshot value is available but must be explicitly approved as acceptable semantics (2026 snapshot dates on historical events, 6 `ONLY_EARLIER` exceptions).

---

## H. Revised blockers

| # | Item | Class | Detail |
|---|------|-------|--------|
| S1 | Scope confirmation (Q11 reopened) | **NEEDS SME** | Confirm Option B full package (QuikClms + QuikClmp + QuikBenh + QuikIsrr, no audit) for the 3,623 events |
| S2 | MISWL disposition (Q7 narrowed) | **NEEDS SME** | Blank/omitted (recommended, QuikPrmh precedent) vs PFNDR snapshot date |
| S3 | MPHASE on partial claim rows | **NEEDS SME** | 0 (per seek rule — recommended) vs coverage phase |
| S4 | ORIGSTATUS for historical events | **NEEDS SME** | Point-in-time status unavailable; fixed code vs blank |
| S5 | QuikBenh emit coordination | **NEEDS SME / client** | Client Loyal2QL already writes dividend history to quikbenh; confirm this repo's benefit-type-8 rows append without clobbering client-side data |
| S6 | Owner exceptions | **NEEDS SME** | 1 policy no owner/insured (`010826551C`); 1 insured-fallback (`010834096C`); 59 blank/zero TINs |
| S7 | QuikAudt exclusion | **NEEDS SME** (sign-off) | Recommend exclude — memo audit not reproducible for history |
| N1 | Policy 9010780411 hold | Manual review | Unchanged (3 rows, $951.30) |

**No source blockers.** PACTG, PFNDR, converted client/relationship tables, and the raw RelationshipNameAddress extract are all present. **CONFIRMED / STRONG EVIDENCE / READY classification per table:**

| Table | Classification |
|-------|----------------|
| QuikIsrr | **STRONG EVIDENCE** — candidate set fully validated; blocked only by S2 (MISWL) |
| QuikClms | **NEEDS SME** — S3, S4; data otherwise complete |
| QuikClmp | **NEEDS SME** — S6; payee data 99.7% complete |
| QuikBenh | **NEEDS SME** — S5 coordination; field data fully derivable |
| Transaction audit | **RECOMMEND EXCLUDE** — S7 |

---

## I. Recommended implementation approach

**Option B — full partial surrender history package**, one PR (PR-7), sequenced internally:

1. **QuikIsrr** emit (3,623 rows → `QLA_Migration/Output/QuikIsrr.csv`) — candidate set already validated to the penny.
2. **QuikClms + QuikClmp** partial rows (phase 0, MSEQ 1..n per policy) — reuse claims pipeline formatting/validation; append-only against existing 2,114/1,709-row outputs.
3. **QuikBenh** new emit (MBENTYP 8) after client coordination (S5).
4. **No transaction audit** (pending S7 sign-off).
5. Exception outputs: 9010780411 hold; owner-exception policies; backdated-date audit.

Expected volumes: +3,623 rows each to QuikIsrr/QuikClms/QuikClmp/QuikBenh (claims table grows from 2,114 to ~5,737 rows).

Staging (Option C) is a fallback only if the SME wants QuikIsrr loaded ahead of companion coordination — not recommended as the default because S2 (MISWL) gates QuikIsrr itself.

---

## J. Updated documentation list

| Document | Change |
|----------|--------|
| `Issue_34_Final_SME_Signoff_Package.md` | **New** — final approve/correct package for PR-7 (Questions 1–7) |
| `Issue_34_Late_SME_Scope_Reconciliation.md` | **New** — this document |
| `Issue_34_QUIKISRR_Decision_Review.md` | Updated — late-SME note; Q11/Q7 status |
| `Issue_34_QUIKISRR_Companion_Table_Reconciliation.md` | Updated — SME chose full record set; Q11 superseded |
| `Issue_34_QUIKISRR_Final_Decision_Closure.md` | Updated — status downgraded to READY AFTER SME CONFIRMATION; scope revision |
| `Issue_34_QuikIsrr_Planning.md` | Updated — status, scope, MISWL |
| `Issue_34_QuikIsrr_SME_Questions.md` | Updated — Q7/Q11 reopened; new Q15–Q19 |
| `Issue_34_Blockers.md` | Updated — S1–S7 |

---

## K. Final recommendation

## **READY AFTER SME CONFIRMATION**

The late SME guidance reopens scope (Q11) and MISWL (Q7). All required **source data is present and validated** — there are no source blockers and no technical blockers.

**SME action:** complete approve/correct on Questions 1–7 in [`Issue_34_Final_SME_Signoff_Package.md`](Issue_34_Final_SME_Signoff_Package.md).

Do **not** create QuikIsrr.csv, loaders, validators, or begin PR-7 development until SME sign-off is recorded.
