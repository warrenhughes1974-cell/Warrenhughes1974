# Issue #135 — Planning Report

**Issue:** #135 — Claims Settlement vs CSO Total_Paid  
**Framework stage:** Planning Agent  
**Status:** Planning complete → Dependency Gate  
**Generated:** 2026-08-02  
**Agent/script:** Cursor Grok 4.5 (locked); Discovery evidence + Output spot counts  
**Code changes:** None  

---

## 1. Executive Finding

Death-claim **paid amounts** must equal CSO **`Total_Paid`** (hard control). Client accounting examples teach which PACTG lines to include/exclude. Current Output fails proven cases (reinstatement 3×, duplicate payout 2×, missing loan death) and leaves ~459 CSO deaths unmatched.

**Plan (phased):**

1. **Always emit `MINTAMT = 0.00`** (user lock — interest not needed).
2. **Reverse-engineer** PACTG include/exclude rules so reconstructed settlement = `Total_Paid`.
3. Apply rules surgically in claims reconstruction / balancing / derivation; emit corrected `quikclms.MPAID` + `quikclmp` payments.
4. Clear **`DTOFDEATH`** on non-death claim families; improve surrender completeness as linked workstream (not CSO hard-gated).

**Development update 2026-08-02:** Warren approved **Option 3** (correct economic events, then derive both tables). Controlled overlay produced for **43/45** evidence candidates; production Output amounts **not** mutated pending consume-path approval. Eric **459** remain supply gaps (readiness template only).

Safe to Dependency Gate / Risk with **phased Development** and hold unresolved residuals.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source | File pattern | In Source/? | Notes |
|---|---|---|---|
| CSO expected paid | `docs/Claims/CSO Life claims summary - 2017 - 2025.xlsx` | Docs (control) | ~1,656 death claims; `Total_Paid` hard control |
| Accounting teacher set | `docs/Claims/Claim Accounting examples.xlsx` | Docs | Red text + column J correct totals |
| PACTG accounting | `PACTG_Accounting_Extract*.csv` | Yes — `20260630` | Primary GL ledger for claim math |
| PRELSA relationships | `RelationshipNameAddress_Extract*.csv` | Yes — `20260630` | Payee / beneficiary linkage |
| Existing claims lineage | `claims_analysis/` phases 4–10, 17, 22–24 | Repo | Reuse; do not rebuild architecture |

### Key PACTG patterns (from teacher workbook)

| Pattern | Example codes / accounts | Role |
|---|---|---|
| Death funding | `6001*R` → `2032` Death Clearing | Include in settlement build |
| Death payout | `2032` → `1058` Death Claim Payment | Economic payout |
| Div-on-deposit interest | `603703R` / `2023` | **Exclude** (Item 16 / red) |
| Claim interest in check | `603803R` Interest on Death Benefit | In `MPAID` once; **not** in `MINTAMT` |
| Loan at death | `1017` Loan/Loan Interest; `7046` interest income | Net check; loan domain vs claim — case-driven |
| Reinstatement / endow loops | `1015`, `604413R`, `2031`, `2019`, `2039` | **Exclude** duplicate representations |
| Intra-co / unapplied re-payout | `1058000256`, `2019` ↔ `1058` | Deduplicate |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Role this issue |
|---|---|---|---|
| `QUIKCLMS` | `MPAID` | N | **Primary paid total** — must = CSO `Total_Paid` for death |
| `QUIKCLMS` | `MFACE` / `NETDB` / `LOAN` / `PREMIUM` / … | N | Adjust only if required to keep header coherent with corrected paid; minimize blast |
| `QUIKCLMS` | `MINTAMT` | N | **Always 0.00** |
| `QUIKCLMS` | `MINTST` / `MINTRATE` / `MINTDAYS` | mixed | Leave blank/0 unless already required elsewhere; do not invent interest |
| `QUIKCLMS` | `DTOFDEATH` | D | Populate **death only**; blank for surrender/disbursement/PS |
| `QUIKCLMP` | `MAMOUNT` (+ payee keys) | N | Economic payments; sum should support `MPAID` |

Schema ref: `docs/claims_conversion_reference/quikclms_quikclmp`.

---

## 4. Required Source-to-Target Field Mapping

| Source | Target | Transformation | Change? |
|---|---|---|---|
| CSO `Total_Paid` (control) | `quikclms.MPAID` (death) | Hard-match via PACTG-validated reconstruction | **Yes** |
| Valid PACTG payout rows | `quikclmp.MAMOUNT` | Deduped economic payments | **Yes** (defect classes) |
| — | `quikclms.MINTAMT` | Force `0.00` on all emitted claim headers | **Yes** |
| Death event date | `quikclms.DTOFDEATH` | Death family only | **Yes** (clear non-death) |
| Item 16/18 rules | Balancing layers | Preserve; extend with new exclude patterns | **Extend** |

### Fields that must remain unchanged

| Target | Touch? |
|---|---|
| `quikmstr.MMODPREM` / `quikridr.MPREM` (#26) | **No** |
| MPOLICY padding (#25) | **No** (join only) |
| `quikclms.MEMOTEXT` (#134) | **No** |
| Non-claims tables | **No** |
| Production DBF flags | **No** |

---

## 5. Open Client Questions

| # | Question | Default for Development |
|---|---|---|
| 1 | Interest in QLAdmin | **Closed** — `MINTAMT` always 0 |
| 2 | Unresolved residual after reverse-engineering | **Hold** claim from production emit; log in Reports |
| 3 | Missing CSO deaths with no PACTG path | Classify: extract gap vs hold vs header-only; no invented money |
| 4 | Surrender hard control file | **None** — use accounting examples + existing Item 14 evidence until client provides |

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|---|---|
| Money | 2 decimal; cent tolerance 0.01 vs `Total_Paid` |
| Policy key | `format_qladmin_mpolicy` (#25); CSO policy + `C` |
| Interest | `MINTAMT=0` always; do not add interest on top of `MPAID` |
| Duplicates | One economic payment per real check/payee event |
| Clearing | Never count clearing + downstream payout as two benefits |

---

## 7. Policy Key Handling

CSO `Policy` (e.g. `9010150740`) → Output `MPOLICY` (`9010150740C`) via existing formatter. Crosswalk unchanged.

---

## 8. Estimated Record Counts

| Population | Count (approx) |
|---|---:|
| CSO death claims (hard control) | 1,656 |
| Current amount OK | 1,111 |
| Current amount mismatch | 86 |
| Missing from Output | 459 |
| `quikclms` rows total | 5,594 |
| `MINTAMT` currently nonzero | 487 → all become 0 |
| `CLAIMSTAT=99` with `DTOFDEATH` set | 3,670 (death-date cleanup candidates) |

---

## 9. Sample Trace (≥3)

| Policy | Expected `Total_Paid` | Current `MPAID` | Intended after |
|---|---:|---:|---|
| `9011156098C` | 15,000.00 | 45,000.00 | 15,000.00; 1 economic payee set |
| `9010914301C` | 25,019.98 | 50,039.96 | 25,019.98; deduped payees |
| `9010391359C` | 1,260.06 | 0.00 | 1,260.06 + payee |
| `9010402010C` | 8,920.15 | 8,920.15 | MPAID unchanged; `MINTAMT=0` |

---

## 10. Risks and Unknowns

- Full 1,656 hard control may require multiple rule iterations; unresolved residuals must **hold**, not force-fit.
- Changing `MPAID` without aligning `quikclmp` breaks cross-table validation.
- Surrender / PS emit (#34) may need coordinated `DTOFDEATH` clear — blast radius if over-broad.
- Missing 459 may be outside current extract window — do not invent payments.

---

## 11. Recommended Risk Agent Prompt

Quantify before/after for: (a) force `MINTAMT=0` on all `quikclms`; (b) teacher defect policies; (c) CSO match/mismatch/missing buckets; (d) non-death `DTOFDEATH` clears. Issue Go / Conditional Go / No-Go for **phased** Development.

---

## 12. Recommended Development Task (do not implement yet)

**Phase A (safe, first):** Post-emit or derivation force `quikclms.MINTAMT=0` for all claim headers; validator asserts zero.

**Phase B (financial hard control):** Build CSO↔PACTG reconciliation workbook; implement include/exclude rules for proven defect classes; gate death emit on `MPAID` (+ payee sum) == `Total_Paid`; hold residuals.

**Phase C (linked):** Clear `DTOFDEATH` on non-death; surrender completeness per accounting examples (not CSO-gated).

Surgical only — no claims architecture rewrite; bump `APP_VERSION` both `app.py` copies when code changes.
