# Issue #135 — Implementation Notes (Production apply)

**Issue:** #135 — Claims Settlement vs CSO Total_Paid  
**Stage:** Development (production consume — Option 3 + 459 expansion) + Output reconcile  
**Generated:** 2026-08-02  
**Engine:** v58.57 (no code bump for reconcile — file promote only)  
**Production Output mutated:** **Yes** — intended package restored to Output root via Test_Validation promote  
**Issue Closed:** **Yes** — Closed 2026-08-02 (v58.61); residual 9 source HOLDs + 3 death zero-payee holds documented

---

## Output / Test_Validation reconcile (2026-08-02 late)

| State | quikclms | quikclmp |
|---|---:|---:|
| Output root before promote | 5594 | 5366 |
| Test_Validation (intended) | 6044 | 5497 |
| Output root after promote | **6044** | **5497** |

Cause: Output root had been overwritten back to the pre-#135 baseline (byte-match to `Archive/*_pre_issue135_20260802T205039Z.csv`) while Test_Validation retained the applied 6044/5497 package. Prior evidence claiming Output was already 6044/5497 was incorrect for the live Output root.

Promotion: copy only `quikclms.csv` + `quikclmp.csv` from `Output/Test_Validation/` → `Output/` after rollback archives under `QLA_Migration/Archive/*_pre_issue135_reconcile_20260802T210607Z.csv`. Test_Validation kept byte-identical. Non-table `claims_*` artifacts moved to `QLA_Migration/Reports/`. Evidence: `evidence/issue135_reconcile_promote_summary.json`, `evidence/issue135_reconcile_report.md`.

---

## Approved mechanism

Warren approved Option 3 + 459 disposition:

| Bucket | Count | Treatment |
|---|---:|---|
| Option-3 CORRECTED (prior overlay) | 43 | Consume into Output (header MPAID + economic payees) |
| DERIVED_HIGH | 142 | Emit death header + PRELSA payees from PACTG eco legs |
| NO_PACTG_HISTORY | 308 | CSO-controlled **header-only** (no quikclmp) |
| HOLD_INCOMPLETE_SOURCE | 9 | **HOLD** — not emitted |

Phase A `MINTAMT=0` remains mandatory on all headers.

---

## Code / wiring

| Item | Path |
|---|---|
| Expansion module | `qla_core/issue135_cso_claims_expansion.py` |
| Apply runner | `Issue_Log_Items/Issue_135/tools/issue135_apply_production_overlay.py` |
| Focused validator | `Issue_Log_Items/Issue_135/tools/_validate_issue135_production.py` |
| #134 marker preserve | `qla_core/issue134_claim_memo_overlay.py` (keeps `CSO_CONTROLLED_NO_PACTG_HISTORY`) |
| Post-emit hook | `app.py` / `QLA_Migration/app.py`: **#135 expand → #134 PNOTE-B → #135 MINTAMT=0** (v58.57 order lock) |
| APP_VERSION | **v58.57** (both app.py copies) |

### Conventions used (not invented)

- `CLAIMNUM` = `RC-{policy_digits}` (existing death convention)
- `CLAIMSTAT` = `2` (post-#79 death paid-in-full; Item 15’s historic `3` is not present in current Output)
- `MPHASE=1`, `MSEQ=0` (headers), payee `MSEQ` 1..n
- `ORIGSTTUS=3` for settled death headers
- Header-only marker in **MEMOTEXT** (`CSO_CONTROLLED_NO_PACTG_HISTORY`); CAUSE is C(3) and cannot hold it
- CSO dates: `Date_Incurred`→`DTOFDEATH`, `Notice_date`→`RPTDATE`, `Last_Pd_Date`→`PDDATE`
- No fabricated check numbers / payee stubs (`***NEEDS_PAYEE_IDENTITY***` not emitted)

---

## Exact emit / hold counts (this apply)

| Metric | Count |
|---|---:|
| quikclms before → after | 5,594 → **6,044** (+450) |
| quikclmp before → after | 5,366 → **5,497** (+131 net) |
| Option-3 headers updated | **43** |
| DERIVED_HIGH headers emitted | **142** |
| DERIVED_HIGH payee rows emitted | **194** |
| DERIVED payee holds (no safe name) | **0** |
| NO_PACTG_HISTORY header-only | **308** |
| HOLD_INCOMPLETE_SOURCE (not emitted) | **9** |

### HOLD policies (9) — incomplete/ambiguous PACTG chains

```text
9010395879C; 9010741943C; 9010771580C; 9010771662C; 9011153243C; 9011154868C; 9011158069C; 9011175485C; 9011193674C
```

### 308 NO_PACTG_HISTORY

These policies have **CSO Total_Paid** but **no PACTG accounting records** in the current dated extract (`PACTG_Accounting_Extract20260630`). They are represented as header-only claim rows with marker `CSO_CONTROLLED_NO_PACTG_HISTORY` and **zero** `quikclmp` rows (no fabricated payees, checks, or accounting history).

---

## Validation

| Check | Result |
|---|---|
| Focused production validator (post-reconcile Output) | **PASS** (`evidence/issue135_production_validation.json`; clms=6044 clmp=5497) |
| Grok independent second-pass (v58.56 apply) | **PASS** (`evidence/issue135_production_grok_second_pass.json`) |
| Grok second-pass (v58.57 post-reconcile) | **PASS** (`evidence/issue135_v5857_grok_second_pass.json`) |
| Issue #134 claim memos | **PASS** (missing `[PNOTE-B]` on death+B = **0**; death+B=1351) |
| Teachers MPAID | 9011156098C=15000; 9010914301C=25019.98; 9010391359C=1260.06 |
| MINTAMT nonzero | **0** (6044/6044) |
| Duplicate MPOLICY/CLAIMNUM/MSEQ (headers) | **0** |
| Marker 308 preserved after #134 | **PASS** (308; 0 with quikclmp) |
| Test_Validation synchronized | `Output/Test_Validation/quikclms.csv` + `quikclmp.csv` = Output root |
| Accountability #135 | **IN_DATA** (validator job + spot-check 6044/5497/marker 308) |
| Closure | **Not Closed** — 9 HOLDs + 459 category remain |

Audits (not in Output root): `Issue_Log_Items/Issue_135/evidence/issue135_production_*` and copies under `QLA_Migration/Reports/`.

Output hygiene (v58.57): `Migration_Audit_Log.txt` → `QLA_Migration/Logs/`; `cso_mortality_crosswalk_qa.csv` + `variation_code_audit.csv` → `QLA_Migration/Reports/`. App write paths redirected accordingly.

Pre-apply backups: `QLA_Migration/Archive/quikclms_pre_issue135_*.csv`, `quikclmp_pre_issue135_*.csv`, `quikclms_pre_issue135_134overlay_*.csv`.

---

## MATCH_CSO zero-payee cohort backfill (v58.60)

**Engine:** v58.60  
**Production Output mutated:** **Yes** — `quikclmp.csv` append only (quikclms unchanged)

| Metric | Count |
|---|---:|
| Cohort (MATCH_CSO, CLAIMSTAT=2, MPAID>0, recon payee_rows=0) | **140** |
| SAFE_BACKFILL applied | **137** policies / **194** payee rows |
| HOLD_INCOMPLETE (no PE/B1 RNA) | **3** |
| HOLD_MISMATCH | **0** |
| quikclmp before → after | 5,301 → **5,495** |
| Golden 9011156655C payees | **4** (5145.67; header money unchanged) |

Residual holds (economic 2032→1058 proven; payee identity missing in PRELSA):

```text
9010792038C; 9011062307C; 9015000341C
```

Module: `qla_core/issue135_match_cso_zero_payee_backfill.py` (inventory/classify/SAFE allowlist; auto_discover from expansion).  
Evidence: `issue135_match_cso_zero_payee_*` under `Issue_Log_Items/Issue_135/evidence/`.  
Issue **not Closed** — prior 9 HOLDs + these 3 residual zero-payee holds remain.

---

## Rebuild + Q deploy (2026-08-02 late evening)

**Engine:** v58.60 (no code bump — restore/promote + DBF regenerate only)  
**Production Output mutated:** **Yes** — restored verified TV package to Output root  
**Issue Closed:** **Yes** (final close after surrender backfill + MSEQ join fix)

| Step | Result |
|---|---|
| Output before restore | 5594 / 5366 (stale pre-#135) |
| Test_Validation source (deploy) | **6044 / 5495** |
| Final package (Closed) | **6044 / 5935** (+440 surrender payees) |
| Q copy | `Q:\CSO\CSO_Test_6_30_2026` via DBF Append Tool **PASS** |

### MPOLICY C(11) + payee MSEQ=header (2026-08-02 follow-up)

Blank QLAdmin payee UI root causes: (1) claims DBF `MPOLICY C(10)` vs master `C(11)`; (2) payee `MSEQ` 1..n vs header `MSEQ=0` index join. Both fixed; append-tool templates_11 load path documented.

### Surrender zero-payee backfill (v58.61)

440/440 CLAIMSTAT=99 MPAID>0 zero-payee policies: Rule1 PE 90/92/94 sum-match (179) or Rule2 OWNR→INSD→PAYR (261). Golden `9011158068C` HOLLAND QUICK 3531.25.

Residual holds (not blocking Closed):
- 9 HOLD_INCOMPLETE_SOURCE (not emitted)
- 3 death zero-payee HOLD (`9010792038C`; `9011062307C`; `9015000341C`)

---

## Intentionally not done

- Inventing settlements for the 9 HOLDs or the 3 residual death zero-payee holds
- Blind final-only MPAID patch without economic reconstruction
- Blind mass-apply of zero-payee cohort without SAFE/HOLD classification
- Mutation of non-claims tables
