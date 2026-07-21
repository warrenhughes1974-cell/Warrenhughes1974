# Issue #79 — Risk Review Report

**Issue:** #79 — Align `quikclms.CLAIMSTAT` to real Policy-book conventions  
**Framework stage:** Risk Agent (G3)  
**Status:** **Conditional Go → Ready for Development** (pending explicit user approval)  
**Generated:** 2026-07-17  
**Model:** Cursor Grok 4.5 (locked)  
**Status note:** Risk analysis only — no production code changes.  
**Evidence:** `evidence/issue79_risk_claimstat_simulation.csv` · `scripts/risk_review_issue79_claimstat.py`  
**Scope:** `Issue_79_Scope_Decisions.md` (SD-79-1 … SD-79-10)

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Impact is quantified and matches the locked Policy-book rule; Development may proceed under the locks below.

| Factor | Assessment |
|--------|------------|
| Scope | `quikclms.CLAIMSTAT` only |
| Impact | **1,769** headers change; **3,855** already-99 unchanged |
| After distribution | **2** = 1,290 · **99** = 4,334 · **1** = 0 |
| False Pending closed | All **494** Pending remapped (15 death→2, 479 surrender→99) |
| #78 payments | Untouched (`quikclmp` 6,151 rows) |
| Item 15 death=3 | Superseded by SD-79-8 (deaths→2) |
| ORIGSTTUS | Leave alone this issue — **1,769** rows that today mirror CLAIMSTAT will diverge unless a companion fix follows |

Development may proceed after user says **Approved for Development** and switches to **Composer 2.5**.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| Death SETTLED/PAID/FUNDED+evidence | 3 or 1 | **2** Paid in Full | **Yes** |
| Surrender / partial / disbursement | 99 or 1 | **99** | **Yes** when 1 |
| Maturity | (none today) | **98** | N/A until family appears |
| Truly unpaid open | 1 | **1** | Keep (0 rows in sim) |
| `quikclmp` | — | Unchanged | **No** |
| Claim money fields | — | Unchanged | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| MPOLICY padding (#25) | **No** |
| MPREM / MMODPREM (#26) | **No** |
| `quikclmp` (#78) | **No** |
| MPAID / MFACE / NETDB / dates | **No** |
| Rates / quikmstr / quikridr | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `claims_analysis/config/quikclms_derivation_rules.json` | Today: SETTLED→3, FUNDED→1 |
| `Sync_Rulebook_quikclms.csv` | claimstat → CLAIMSTAT |
| `qla_core/claims_emit_enhancements.py` | ISWL disbursement → 99 (already aligned) |
| `docs/Policy/quikclms.dbf` | Authority: death→2, SRR→99, MAT→98 |

---

## 4. Population Analysis (simulated on current Output)

| Metric | Count |
|--------|------:|
| Total `quikclms` rows | 5,624 |
| Rows that would change | **1,769** |
| Rows unchanged | 3,855 |
| Remaining Pending after remap | **0** |
| `quikclmp` rows (must stay) | 6,151 |

### Before → After

| CLAIMSTAT | Before | After |
|-----------|------:|------:|
| 1 Pending | 494 | **0** |
| 2 Paid in Full | 0 | **1,290** |
| 3 Settled | 1,275 | **0** |
| 99 Surrender | 3,855 | **4,334** |
| 98 Matured | 0 | 0 |

### Change breakdown

| Family | Before → After | Rows |
|--------|----------------|-----:|
| DEATH_CLAIM | 3 → 2 | 1,275 |
| DEATH_CLAIM | 1 → 2 | 15 |
| SURRENDER_CLAIM | 1 → 99 | 479 |

---

## 5. Fallback Recommendation

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| **A. Full SD-79 remap (recommended)** | 1,769 | Matches Policy book + user lock |
| B. Close Pending only (1→2/99); leave deaths at 3 | 494 | Reject — still inconsistent with book |
| C. Deaths 3→2 only; leave Pending | 1,275 | Reject — leaves open-work queue |
| D. Also rewrite ORIGSTTUS = new CLAIMSTAT | 1,769+ | Reject for #79 — wrong semantics (book ORIGSTATUS = policy status) |
| E. Do nothing | 0 | Reject |

**Recommended:** Option A.  
**ORIGSTTUS lock:** do **not** copy new CLAIMSTAT into ORIGSTTUS (OBQ-79-1 default). Document residual mirror drift; companion may set true pre-death policy status later.

---

## 6. Trace Policies

| Policy | Family | Before | After | Payment? | Pass? |
|--------|--------|--------|-------|----------|-------|
| `010397318C` | DEATH | 3 | **2** | Yes / MPAID 3626.03 | **Yes** |
| `010391359C` | DEATH FUNDED | 1 | **2** | Yes / MPAID 0 | **Yes** |
| `010469081C` | SURRENDER FUNDED | 1 | **99** | No row; MPAID 9722.80 | **Yes** |
| `010154425C` | DISBURSEMENT | 99 | **99** | Yes | **Yes** (unchanged) |

---

## 7. Material Status Moves (not dollar changes)

Status remap only — largest *population* moves:

| Move | Rows | Meaning |
|------|-----:|---------|
| Death 3 → 2 | 1,275 | Settled label → Paid in Full |
| Surrender 1 → 99 | 479 | Close false Pending surrenders |
| Death 1 → 2 | 15 | Close false Pending deaths |

No MPAID/MFACE deltas by design (sum MPAID unchanged at simulation: **$22,842,262.46**).

---

## 8. Material Calculation Impact

- **Intentional:** Closed historical claims stop looking like open QLAdmin work.
- **Not accidental:** Payment table and claim dollars unchanged.
- **Residual:** ORIGSTTUS will no longer equal CLAIMSTAT on remapped rows (today ~2,114 mirrored; after remap fewer accidental mirrors). Acceptable under SD / OBQ default.

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserve** |
| Issue #26 MPREM | **N/A / untouched** |
| Issue #78 quikclmp recovery | **Preserve** — no payment rewrite |
| Claims Item 15 death=3 | **Superseded** by SD-79-8 |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] Traces: `010397318C`→2, `010391359C`→2, `010469081C`→99, `010154425C` stays 99
- [ ] Fleet: CLAIMSTAT counts ≈ 2:1290 / 99:4334 / 1:0 / 3:0
- [ ] `quikclmp` row count still 6,151; sample amounts unchanged
- [ ] MPAID/MFACE/NETDB unchanged on remapped rows
- [ ] ORIGSTTUS not mass-copied from new CLAIMSTAT
- [ ] No quikmstr/quikridr/rates changes
- [ ] Audit CSV: 1,769 change rows with reason codes

---

## 11. Recommended Development Agent Task

1. Surgical post-emit (or derivation) remap of `quikclms.CLAIMSTAT` per SD-79-2..5 using claim family + payment/MPAID/lifecycle evidence.
2. Write `QLA_Migration/Reports/issue79_claimstat_remap_audit.csv`.
3. Do **NOT** change: `quikclmp`, claim money/date fields (except if a paid-date fill is already separate), ORIGSTTUS, #25/#26.
4. Version bump both `app.py` copies: current **v57.98** → **v57.99**.
5. Validator: `QLA_Migration/_validate_issue79_claimstat.py` covering §10.
6. On PASS: copy `quikclms.csv` only to `Output/Test_Validation/`.

---

## Appendix

- Simulation CSV: `Issue_Log_Items/Issue_79/evidence/issue79_risk_claimstat_simulation.csv`
- Simulation script: `Issue_Log_Items/Issue_79/scripts/risk_review_issue79_claimstat.py`
- Companion (not #79): ORIGSTTUS/ORIGSTATUS = pre-death policy status; CAUSE defaults
