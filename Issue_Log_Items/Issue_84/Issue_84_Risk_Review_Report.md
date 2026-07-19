# Issue #84 — Risk Review Report

**Issue:** #84 — `quikclms` money-field decomposition (Policy-book parity)  
**Framework stage:** Risk Agent (G3)  
**Status:** **Conditional Go → Ready for Development** (pending explicit user approval)  
**Generated:** 2026-07-17  
**Refreshed:** 2026-07-19 (post-#85 Output + user-locked planning defaults)  
**Model:** Cursor Grok 4.5 (locked)  
**Status note:** Risk analysis only — no production code changes.  
**Evidence:**  
- `evidence/issue84_risk_money_recon_simulation.csv` (refreshed 2026-07-19)  
- `evidence/issue84_risk_money_mismatches.csv` (refreshed 2026-07-19)  
- `scripts/risk_review_issue84_money_fields.py`  
- `scripts/risk_review_issue84_join_check.py`  
**Scope:** `Issue_84_Scope_Decisions.md` (SD-84-1 … SD-84-12)

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — proceed in **two Development tracks**. Planning defaults **OBQ-84-1…4 are locked** by user direction (2026-07-19). Post-#85 header structure no longer blocks Track B joins.

| Factor | Assessment |
|--------|------------|
| Symptom confirmed | DIVIDENDS / PREMIUM / SUSPENSE / MINTRATE = **0%** nonzero; LOAN/NETDB/MINTAMT thin vs Policy book |
| Screenshot defects | `010360289C` MPAID≠payee; `010391359C` MPAID=0 after #78 payee recovery |
| Track A (header backfill) | **194** headers with payees but MPAID≈0 (post-#85); **170** of those still in #78 audit (~$767K payout); claim-key `header_zero` = **131** |
| Track B (decomposition + recon) | PACTG components per locked OBQ defaults; policy-level unbalanced still **898** (~$2.46M) |
| Blind MPAID=sum(payee) by MPOLICY | **Reject** as mass rewrite — policy-only join still inflates (4,561) |
| Duplicate pol+phase headers | **Cleared by #85** — current Output: **0** dups / **5,447** headers (was 3,054 dups / 5,624) |
| #79 CLAIMSTAT | Untouched (SD-84-5) |
| #78 payee invent | Untouched (SD-84-6) |

Development may proceed after user says **Approved for Development** and switches to **Composer 2.5**, preferably starting with **Track A**, then Track B.

---

## 2026-07-19 — Planning defaults locked (user)

| OBQ | Locked default | Risk confirmation |
|-----|----------------|-------------------|
| **OBQ-84-1** PACTG → field map | Derive from balancing JSON + Policy-book × PACTG evidence; blank/zero when no source | **Accept** — no invent |
| **OBQ-84-2** #78 header backfill | Yes — when live payees exist and header MPAID≈0 / PDDATE blank | **Accept** — Track A; claim-key join; full audit |
| **OBQ-84-3** Family formulas | Best-effort by claim family; document residuals; do not invent | **Accept** |
| **OBQ-84-4** MINTRATE | Leave **0** without proven LifePRO rate; do **not** default 4.5 | **Accept** — inventing rates rejected |

---

## 1. Current vs Proposed Mapping

| Field | Current emit | Proposed | Change? |
|-------|--------------|----------|---------|
| MPAID | Partial; 194 headers ~0 with live payees (post-#85) | Track A: backfill from existing `quikclmp` when MPAID≈0 | **Yes (Track A)** |
| PDDATE | Often blank when payees exist (679 headers) | Track A: set from payee payment/check date when backfilling | **Yes (Track A)** |
| MFACE | Partial (~87% nonzero) | Track B: PACTG face/gross codes by family | **Yes (Track B)** |
| DIVIDENDS | Constant **0** | Track B: PACTG dividend components | **Yes (Track B)** |
| LOAN | Sparse (44) | Track B: loan offsets; Policy-book often **negative** | **Yes (Track B)** |
| NETDB | Under-filled (~35%) | Track B: family formula / net benefits | **Yes (Track B)** |
| PREMIUM | Constant **0** | Track B: premium due/refund | **Yes (Track B)** |
| SUSPENSE | Constant **0** | Track B: suspense components | **Yes (Track B)** |
| MINTRATE | Constant **0** | Track B: only if LifePRO rate proven; else leave 0 | **Conditional** |
| MINTAMT | Sparse (~9%) | Track B: interest codes | **Yes (Track B)** |
| ADJUST | Always 0 | Track B: residual only when evidenced | Rare |
| CLAIMSTAT | Post-#79 | Unchanged | **No** |
| New `quikclmp` rows | Post-#78 | Unchanged | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| MPOLICY padding (#25) | **No** |
| MPREM / MMODPREM (#26) | **No** |
| `CLAIMSTAT` (#79) | **No** |
| New `quikclmp` invent (#78) | **No** |
| Existing payee amounts (default) | **No** rewrite unless later explicit expansion |
| `quikmstr` / `quikridr` / rates | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `docs/Policy/quikclms.dbf` | Population / formula authority |
| `docs/claims_conversion_reference/PACTG_Accounting_Extract20260427.csv` | Component source |
| `claims_analysis/config/claim_family_balancing_rules.json` | Death/surrender/disbursement code families |
| `claims_analysis/config/quikclms_derivation_rules.json` | Current MPAID/NETDB/MINTAMT sources |
| `claims_analysis/config/prototype_dbf_generation_rules.json` | DIVIDENDS/PREMIUM/SUSPENSE/MINTRATE constant 0 |
| Claims Item 18 path | Prior partial death NETDB/MPAID/MFACE — superseded for full decomp |
| `QLA_Migration/Reports/issue78_quikclmp_recovery_audit.csv` | Header MPAID delta after recovery |
| Issue #85 (v58.03) | Header merge/rephase — cleared dup pol+phase |

---

## 4. Population Analysis (current Output — refreshed 2026-07-19)

| Metric | Count |
|--------|------:|
| `quikclms` rows | **5,447** (was 5,624 pre-#85) |
| `quikclmp` rows | 6,151 |
| Duplicate MPOLICY+MPHASE headers | **0** (was 3,054) |
| Headers with ≥1 payee | 5,432 |
| Multi-header policies | 624 |
| HEADER_ZERO_HAS_PAYEE (policy-join Track A screen) | **194** |
| HEADER_ZERO claim-key join | **131** |
| Of those in #78 recovery audit with header MPAID≈0 | **170** (~$767,220.90) |
| Headers with payee + blank PDDATE | **679** |
| Claim-key MPAID≠payee-sum | **856** (match 4,467) |
| Policy-level unbalanced (sum headers vs sum payees) | **898** (~$2.46M) |
| Naïve MPAID≠payee-sum by MPOLICY only | 4,561 (not a safe rewrite list) |

### Nonzero field rates (ours vs Policy book)

| Field | Ours nonzero (post-#85) | Book nonzero |
|-------|------------------------:|-------------:|
| MPAID | 5,240 (96.2%) | 95.1% |
| MFACE | 4,758 (87.4%) | 87.2% |
| NETDB | 1,910 (35.1%) | 75.6% |
| MINTAMT | 487 (8.9%) | 44.4% |
| LOAN | 44 (0.8%) | 9.2% |
| DIVIDENDS | **0** | 40.5% |
| PREMIUM | **0** | 16.6% |
| SUSPENSE | **0** | 1.9% |
| MINTRATE | **0** | 43.7% |
| ADJUST | **0** | ~0% (1 row) |

### Why policy-only “mismatches” are not Track A

1. Multi-header policies still exist (624) — payee join must use **claim key** (MPOLICY+MPHASE / claimnum), not MPOLICY alone.  
2. Surrender/death semantics often keep **Amount Ins / Net Benefits ≠ check total** (Policy-book pattern; see `010150740C`).  
3. Mass-setting `MPAID = policy payee sum` would destroy correct face/net decompositions.

**Safe Track A rule:** only when `MPAID ≈ 0` **and** payee rows exist for that claim header (claim-key join), set MPAID to that claim’s payee sum and fill PDDATE from payment dates.

### Policy-book authority (unchanged)

Real Policy book reconciles header↔payee at **99.8%** balanced. Our policy-level unbalanced population (**898 / ~$2.46M**) remains a Track B recon goal — not a Track A mass rewrite.

---

## 5. Fallback Recommendation

| Option | Assessment |
|--------|------------|
| **A. Phased Track A then Track B (recommended)** | Fix clear #78 header gaps first; then PACTG decomposition + claim-key / policy-level recon |
| B. Full decomposition + mass MPAID=payee in one Dev | **Reject** — high blast radius; formula risk |
| C. Track A only; defer components | Acceptable interim if UAT prioritizes Net Payment display |
| D. Populate MINTRATE=4.5 fleet default | **Reject** (OBQ-84-4 locked) |
| E. Do nothing | Reject — screenshot defects remain |

**Recommended:** Option A.

---

## 6. Trace Policies

| Policy | Symptom | Risk expectation after fix |
|--------|---------|----------------------------|
| `010391359C` | MPAID 0 / PDDATE blank; payee 1,260.06 | Track A → MPAID **1260.06**, PDDATE filled; CLAIMSTAT stays **2** |
| `010360289C` | MPAID 3,129.06 vs payee 6,139.10; components 0 | Track B / claim-key recon — **do not** blindly overwrite without PACTG story; CLAIMSTAT stays **99** |
| `010150740C` | MFACE 1,500; MPAID=payee 3,213.59 | **Preserve** — correct composite; regression guard |

Policy-book formula examples (authority only): `02505824W`, `02601839W`, `02695880W`, `02393056W`.

---

## 7. Material Money Moves

| Move | Rows | $ impact (approx) |
|------|-----:|------------------:|
| Header MPAID 0 → sum(claim payees) | **194** policy-join / **131** claim-key candidates; 170 proven in #78 audit | ~$767K on #78-zero subset |
| PDDATE blank → payment date | subset of above / up to 679 | Date-only |
| Track B component fills + recon | TBD after map; 898 policy-level unbalanced | Large population move; $ should reconcile to existing payouts, not invent new total paid |

Largest claim-key deltas for Development trace set: `011134051C`, `010762319C`, `010816898C`, `010760306C`, `010858099C`.

---

## 8. Material Calculation Impact

- **Intentional:** QLAdmin Claims money panel shows Net Payment / Paid date when checks already exist; components approach Policy-book decomposition; unbalanced policies move toward book recon.  
- **Not accidental:** CLAIMSTAT and payee invent stay frozen.  
- **Residual risk:** Wrong PACTG code → wrong DIVIDENDS/PREMIUM; Item 18 double-apply; claim-key join errors on multi-header policies.  
- **Acceptance:** Unbalanced residuals stay in audit rather than forced invent (OBQ-84-3 locked).

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserve** |
| Issue #26 MPREM | **Untouched** |
| Issue #78 `quikclmp` recovery | **Preserve** payee rows; Track A only backfills header |
| Issue #79 CLAIMSTAT | **Preserve** |
| Issue #85 header structure | **Preserve** — 0 dup pol+phase; Track B joins on claim key |
| Claims Item 18 | **Supersede / gate** when Track B lands — avoid double money writes |

---

## 10. Regression Testing Checklist (for Validation Agent)

### Track A
- [ ] `010391359C`: MPAID=1260.06; PDDATE non-blank; CLAIMSTAT still 2
- [ ] Count of HEADER_ZERO_HAS_PAYEE (claim-key) after fix ≈ 0 (or exception-audited)
- [ ] `quikclmp` still 6,151 rows; sample amounts unchanged
- [ ] CLAIMSTAT fleet still post-#79 pattern (2 / 99; no Pending invent)
- [ ] #85 uniqueness preserved: 0 duplicate MPOLICY+MPHASE

### Track B
- [ ] `010150740C` unchanged composite (MFACE 1500, MPAID 3213.59)
- [ ] `010360289C` explained/reconciled with audit reason (not silent wrong overwrite)
- [ ] DIVIDENDS/PREMIUM/SUSPENSE/MINTRATE/MINTAMT/LOAN/NETDB population moves toward book rates **only where source evidenced**
- [ ] No invent when PACTG silent; MINTRATE stays 0 without proven rate
- [ ] Policy-level unbalanced count moves down with audited residuals
- [ ] Audit CSVs in `Reports/` only
- [ ] Non-candidate tables unchanged; `Test_Validation/quikclms.csv` only on PASS

---

## 11. Recommended Development Agent Task

1. **Track A (first):** Surgical post-emit header reconcile — when claim has `quikclmp` rows and `MPAID≈0`, set `MPAID` = claim-keyed payee sum; set `PDDATE` from payee dates if blank. Join by claim identity (MPOLICY+MPHASE / claimnum — **not** MPOLICY-only).  
2. **Track B (second):** Derive DIVIDENDS / LOAN / PREMIUM / SUSPENSE / MINTAMT / MINTRATE / NETDB / MFACE refinements from PACTG using family balancing codes (OBQ-84-1); LOAN sign per Policy book; MINTRATE leave 0 without source (OBQ-84-4); include claim-key / policy-level MPAID↔payee recon for the 898 unbalanced set without inventing.  
3. Do **not** change CLAIMSTAT; do **not** invent payees; do **not** mass-set MPAID=policy payee sum.  
4. Gate/replace Item 18 path to avoid double-apply.  
5. Write `QLA_Migration/Reports/issue84_money_field_audit.csv` (+ recon exceptions).  
6. Version bump both `app.py` copies (next after current production banner).  
7. Validator covering §10; on PASS copy `quikclms.csv` to `Output/Test_Validation/`.

---

## Appendix

| Item | Path |
|------|------|
| Scope | `Issue_84_Scope_Decisions.md` |
| Planning | `Issue_84_Planning_Report.md` |
| Dependency | `Issue_84_Dependency_Gate.md` (G2 PASS) |
| Evidence | `evidence/issue84_risk_money_recon_simulation.csv` |
| Mismatches | `evidence/issue84_risk_money_mismatches.csv` |
| Related | #78, #79, #85, Claims Item 18 |

**G3 Risk:** **PASS — Conditional Go**  
**#85 structural blocker:** **Cleared** (0 dup pol+phase in current Output)  
**OBQ defaults:** **Locked 2026-07-19**  
**Next:** User says **Approved for Development** (Composer 2.5). Prefer stating Track A only or Track A+B.

---

## Addendum — Peer review of the mismatch finding (2026-07-17)

A verification pass (`scripts/risk_review_issue84_join_check.py`) tested the original finding against the **real Policy book payee table** (`docs/Policy/quikclmp.dbf`).

### A1. The real book reconciles header↔payee almost perfectly

| Measure | Real Policy book | Our Output |
|---------|-----------------:|-----------:|
| Policies with headers + payees | 7,659 | 2,250 |
| Balanced (sum MPAID = sum MAMOUNT per policy) | **7,645 (99.8%)** | 1,352 (60.1%) |
| Unbalanced | 14 (~$35K total) | **898 (~$2.46M total)** |

So MPAID = payee-sum **is** the Policy-book convention at policy rollup. **898 policies (~$2.46M)** remain genuinely unreconciled — Track B recon goal.

### A2. Structural divergence — resolved by #85

| Measure | Real book | Ours (2026-07-17) | Ours (2026-07-19 post-#85) |
|---------|----------:|------------------:|--------------------------:|
| Duplicate MPOLICY+MPHASE header rows | **0** | **3,054** | **0** |

Track B may now use clean claim-key joins. Conditional Go unchanged; Track B scope includes components + claim-key / policy-level recon.
