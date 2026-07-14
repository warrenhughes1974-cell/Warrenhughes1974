# Issue #54 — Intake Summary

**Issue:** #54 — Full Loan History Load (LifePRO → QLAdmin Loan History)  
**Date:** 2026-07-11  
**Framework stage:** Intake complete (G0)  
**Status:** Approved → Planning  
**Owner:** Conversion (Warren) · **Reporter:** Eric  
**Business status:** No-Go for Development until G1 + G2 + G3  

**Model:** Cursor Grok 4.5 (locked Intake stage)

---

## 1. Client / business symptom (verbatim + normalized)

**Client / business ask (verbatim, paraphrased from Eric via conversion lead):**

> Eric said there should be a loan history sheet from LifePRO. Can we bring that into QL?

**Normalized:**

LifePRO maintains a **multi-row loan history** per policy (accrual / adjustment / payment / capitalization activity). QLAdmin exposes a **Loan History** screen (Help §5.1.2.7) showing transaction type, date, amount, and running balance. Today the conversion only loads a **current outstanding loan snapshot** into `QuikLoan` (Issue #32 / #44). Full history is **not** converted. Client wants the LifePRO loan history sheet available in QLAdmin.

**Example policies:** none new from Eric at open. Use proven Issue #32 trace policy until Planning expands:

| LifePRO | QLAdmin | Notes |
|---------|---------|-------|
| `9010331768` | `010331768C` | 88 PLOAN rows; latest balance $3,707.11; PACTG 0412 annual capitalization chain held from QUIKCLMS |

---

## 2. Suspected domain

| Layer | Path / table | Role |
|-------|--------------|------|
| Source (snapshot history) | `PLOAN_LoanInformation_Extract_*.csv` | ~93,857 rows / 913 policies — accrual snapshots (TYPE R/A, STATUS H/A/R) |
| Source (accounting txns) | `PACTG_Accounting_Extract_*.csv` 04xx Borrowed Money | ~3,851 loan accounting rows previously held from QUIKCLMS (0411/0412/0413…) |
| Current converter | `qla_core/quikloan_converter.py` | Latest non-zero PLOAN row → `QuikLoan` (9 fields) |
| Current target | `quikloan.csv` / QuikLoan | **One row per MPOLICY** — current loan only |
| Desired UI | QLAdmin Loan History (§5.1.2.7) | Type / Date / Amount / Balance (+ accrued / current / paid-to) |
| Related hold | Phase 22C semantic governance | Loan 04xx must **not** go to QUIKCLMS |

**Domain:** Policy loans / loan history — **not** claims, premium history, or rates.

---

## 3. What we already do vs what Eric is asking for

| Capability | Status |
|------------|--------|
| Current outstanding loan balance / rate / dates in QL | Implemented under **#32 / #44** (gated emit; ~384 active loans) |
| Paid-off / zero-balance QuikLoan rows | Explicitly **not** emitted (`emit_zero_balance_loans: false`) |
| Full PLOAN multi-row history in QL | **Not in scope** of #32 — documented as future (DQ4) |
| PACTG 04xx → Loan History | **Not built** — held from claims; marked future QuikLoan/Loan History workstream |
| QLAdmin Loan History screen populated with LifePRO history | **Missing — this issue** |

---

## 4. What we were waiting on (why this was not done)

These are the real blockers that kept Loan History out of #32 — now the starting gate list for #54:

| ID | Wait item | Status at #54 open |
|----|-----------|--------------------|
| W1 | **Scope authorization** — Issue #32 DQ4 (“Is snapshot-only QuikLoan enough, or is loan history required later?”) left **Open**; #32 deliberately scoped to current balance only | **Cleared by this issue open** — Eric/client ask is now explicit |
| W2 | **QLAdmin target table / load pattern** — Help §5.1.2.7 lists Loan History UI fields; “tables affected” cites **QuikLoan**, but QuikLoan schema is **one current row per policy**. Loan *processing* also writes **QuikAudt**. No proven multi-row history CSV/DBF load path in this conversion | **Open — Planning must resolve** (New Era / QLAdmin Help / UAT proof) |
| W3 | **Authoritative LifePRO source** — PLOAN history (accrual snapshots) vs PACTG 04xx (accounting events) vs both | **Open — Planning + SME** |
| W4 | **Transaction-type crosswalk** — Map LifePRO TYPE/STATUS or PACTG 0411/0412/0413… to QLAdmin Loan History types (loan granted, payment, interest charged, APL) | **Open** |
| W5 | **Relationship to QuikLoan snapshot** — History load must not corrupt #32/#44 current balance; may require QuikLoan emit enabled as companion | **Open — Dependency Gate** |
| W6 | **Zero-balance / closed loans** — Whether paid-off policies need history rows even when QuikLoan is blank | **Open — SME** |
| W7 | **QuikAudt** — Before/after audit memo table; Issue #34 recommended exclude for historical events (not reproducible). May or may not feed Loan History UI | **Open — Planning** |

**Intake verdict:** We were not waiting on missing source extracts. PLOAN and PACTG are present. We were waiting on **business scope + QLAdmin history-load design**, which #32 explicitly deferred.

---

## 5. Intake evidence (known from #32 / Phase 22C — Planning formalizes)

| Check | Result |
|-------|--------|
| PLOAN extract present | Yes — `PLOAN_LoanInformation_Extract_20260530.csv` |
| PLOAN grain | History table: 913 policies, median ~45 rows, max 871 |
| QuikLoan key constraint | `MPOLICY` → one current loan row |
| #32 emit | 384 active; 528 zero-balance held; 1 date-blocked |
| PACTG loan pseudo-claims held | ~3,851 rows / ~663 policies (Phase 22C) — correct hold from QUIKCLMS |
| QLAdmin Help Loan History fields | Transaction Type, Date, Amount, Balance; plus Accrued Interest, Current Balance, Interest Paid To |
| Existing loan history converter | **None** |
| `QLAdmin_Converted_Tables.txt` | `quikloan` listed as cleared / not default-populated historically; **no** separate loan-history table listed |

---

## 6. In scope / out of scope (first pass)

### In scope

- Define and implement load of **LifePRO loan history** into whatever QLAdmin structure feeds the **Loan History** screen
- Preserve Issue **#32 / #44** QuikLoan current-balance semantics (no regression of latest-row selection / HHMMSS sort)
- Keep Phase 22C rule: loan 04xx accounting must **not** re-enter QUIKCLMS as surrender/death claims
- Prove example `010331768C` shows multi-row history consistent with LifePRO (within approved mapping)
- Document source authority (PLOAN vs PACTG vs hybrid) and transaction-type map

### Out of scope (unless Planning expands)

- Redesigning QuikLoan current-balance field mapping (already approved v1.2)
- Loading loan interest into QUIKCLMS / claim interest fields
- Synthesizing QuikAudt before/after policy images unless Planning proves Loan History requires it
- Changing premium history (`quikprmh`) or benefit history (`quikbenh`)
- Enabling QuikLoan default batch emit without explicit gate (may be companion dependency)

---

## 7. Related issues

| Issue | Relationship |
|-------|----------------|
| **#32** | QuikLoan snapshot (PLOAN latest non-zero) — prerequisite / companion; DQ4 deferred this work |
| **#44** | QuikLoan latest-row `LAST_CHG_TIME` HHMMSS fix — must not regress |
| **Phase 22C / claims semantic hold** | 04xx Borrowed Money held from QUIKCLMS → belongs in loan domain |
| **#34** | QuikAudt exclusion precedent for historical events — relevant if history path proposes QuikAudt |
| **#25** | MPOLICY padding — any new loan-history key must use same format |
| **#21F** | Premium History is a **different** history table (`quikprmh`) — pattern reference only |

---

## 8. Artifact inventory

| Artifact | Status |
|----------|--------|
| Eric / client ask for Loan History | Provided (this open) |
| Example policy | Soft — use `9010331768` / `010331768C` until client adds more |
| PLOAN extract | Present |
| PACTG extract | Present |
| Issue #32 field mapping / audits | Present under `Issue_Log_Items/Issue_32/` |
| Phase 22C loan candidate population | Present under `claims_analysis/phase22_semantic_governance/` |
| QLAdmin Help Loan History section | Present (`docs/claims_conversion_reference/QLAdmin_Help.pdf` §5.1.2.7) |
| LifePRO Loan History UI screenshot | **Missing** (soft — useful for Planning grain match) |
| Proven QLAdmin multi-row loan-history load schema | **Missing — hard Planning blocker** |
| New Era confirmation of history table / import layout | **Missing — soft/hard depending on Planning findings** |

---

## 9. Immediate blockers visible at intake

| Blocker | Blocks Development? | Notes |
|---------|---------------------|-------|
| Target table / load pattern unknown | **Yes** until Planning resolves | QuikLoan alone cannot store multi-row history as currently schema’d |
| Source authority (PLOAN vs PACTG) | **Yes** for mapping freeze | Both available; grains differ |
| Transaction type crosswalk | **Yes** for mapping freeze | SME / New Era likely needed |
| LifePRO screenshot of history sheet | Soft | Prefer for UAT; not required to start Planning research |
| QuikLoan emit still gated off by default | Soft / companion | History UI may still show “current” section from QuikLoan |

---

## 10. Severity / owner / priority

| Field | Value |
|-------|--------|
| Severity | High (CSR loan inquiry incomplete without history; accounting trail incomplete) |
| Owner | Conversion (Warren) + Client/SME for type map & source authority |
| Priority | Go for **Planning**; **No-Go** for Development until G1–G3 |
| Duplicate of open item? | No — #32 explicitly deferred this; opens new workstream |

---

## 11. G0 checklist

- [x] Issue folder created under `Issue_Log_Items/Issue_54/`
- [x] Intake summary written
- [x] Example policies listed (or marked none — using #32 trace)
- [x] Owner and priority assigned
- [x] No code or rulebook changes made

---

## 12. Recommended next step

**Planning Agent (Cursor Grok 4.5)** — research:

1. Exact QLAdmin storage for Loan History rows (QuikLoan multi-row? QuikAudt? other DBF?)
2. PLOAN vs PACTG grain fit to UI fields (Type / Date / Amount / Balance)
3. Dependency on #32 QuikLoan emit
4. Draft mapping + open SME questions

Do **not** start Development until Dependency Gate + Risk pass and target table is proven.
