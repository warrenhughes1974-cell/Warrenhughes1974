# Issue #89 — Risk Review Report

**Issue:** #89 — Policy fee wipe after `quikridr`-only rebatch (`MANNLFEE` / modal fees)  
**Framework stage:** Risk Agent  
**Status:** **Go — Ready for Development** (after user approval)  
**Fallback simulated:** N/A (restore existing `#21C`/`#58` path; harden load site)  
**Generated:** 2026-07-22  
**Agent/script:** Cursor Grok 4.5 · `QLA_Migration/_risk_review_issue89_policy_fee_cache.py`

**Status note:** Risk analysis only — no production code changes.

---

## Go / No-Go Recommendation

**GO** — Restore `#21C`/`#58` fees by loading `_policy_fee_map` on the **`quikridr` path** (same PPOLC pass as `#88` BILLING_MODE) and add a fail-closed population guard so ridr-only rebatches cannot wipe fees again.

Rationale: Impact is a pure restore of previously released behavior (4,457 base rows). Simulation shows 100% factor coverage for fee candidates; `#88` MPREM traces stay intact. No fee-formula change. Blast radius limited to blank→populated fee columns on base phase.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| `_policy_fee_map` load site | Only inside `if t_id == quikmstr` | Also (required) inside `if t_id == quikridr` when reading PPOLC | **Yes — path harden** |
| `quikridr.MANNLFEE` | Blank fleet-wide (broken emit) | PPOLC `POLICY_FEE` on BENEFIT_SEQ 1 (`#21C` interceptor unchanged) | **Restore only** |
| `quikridr` MSEMIFEE…MMTHBFEE | Blank (`#58` skipped zero_fee=5083) | `MANNLFEE × factor/100` (existing helper) | **Restore only** |
| Fail-closed guard | None | ERROR/fail if PPOLC fee>0 ≫ 0 and Output base MANNLFEE>0 == 0 | **Yes — new** |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| `quikmstr.MMODEPREM` | PPOLC.MODE_PREMIUM | **No** |
| `quikridr.MPREM` | `#26` / `#88` | **No** |
| `quikridr.MUNIT` / `MVPU` | existing | **No** |
| MPOLICY padding (#25) | existing | **No** |
| `quikmstr` MSEMI/MQTRL/MMTHD/MMTHB | `#36` / `#21J` | **No** (post-ridr copy may still rewrite factors; values unchanged intent) |
| `quikplan` *FEE | plan defaults | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `app.py` ~6958–6977 | `#21C` fee cache — **quikmstr-only** (root defect) |
| `app.py` ~7156–7193 | `#88` PPOLC BILLING_MODE cache on **quikridr** — **hook site for fee cache** |
| `app.py` ~7512–7519 | `#21C` MANNLFEE interceptor (keep) |
| `app.py` ~8353–8573 | `#58` modal fee apply + rewrite ridr |
| `qla_core/modal_premium_factors.py` | `apply_modal_policy_fees_to_quikridr` |
| `Issue_88/_rebatch_quikridr.py` | Proximate wipe; must remain safe after harden |
| `tools/validators/validate_issue58_quikridr_modal_fees.py` | Validation gate |
| Log: `QLA_Migration/Logs/_issue88_quikridr_rebatch_log.txt` | `Issue 58: updated=0, zero_fee=5083` |

---

## 4. Population Analysis

Script: `_risk_review_issue89_policy_fee_cache.py`  
Sources: PPOLC 20260630 ⋈ crosswalk ⋈ current `Output/quikridr.csv` + `quikmstr.csv`

| Metric | Count |
|--------|------:|
| `quikridr` rows | 6,934 |
| Base phase (MPHASE 1) rows | 5,083 |
| PPOLC `POLICY_FEE` > 0 | 4,457 |
| Fee mapped to QLA MPOLICY | 4,457 |
| **Current** base `MANNLFEE` > 0 | **0** |
| **Would set** `MANNLFEE` after restore | **4,457** |
| **Would set** modal fees (`#58`) | **4,457** |
| Missing quikmstr factors among fee candidates | **0** |
| Fee in PPOLC but no base ridr row | 0 |

### Top plans by restore count (MANNLFEE)

| Plan | Rows |
|------|-----:|
| 1659C2 | 1,147 |
| 1659CR | 641 |
| 1658C1 | 435 |
| 1L1095 | 378 |
| 1L10SO | 361 |
| 1L14SC | 232 |
| 5L0110 | 216 |
| 170858 | 209 |
| 5667AT | 195 |
| 17085M | 153 |
| 1960PO (Eric sample family) | 40 |

### Largest annual fees (sample)

Many policies at **$50.00** (ISWL / high-fee book). Eric traditional sample stays **$10.00**.

---

## 5. Fallback Recommendation

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| **A — Load fee cache on quikridr + fail-closed guard** | 4,457 MANNLFEE + 4,457 modal | **Recommended** |
| B — Process discipline only (“always run quikmstr first”) | 0 code | **Reject** — already failed via `#88` rebatch |
| C — Full batch only, no harden | restore once | **Reject** — same trap next ridr-only script |
| D — Manual Output patch | ad hoc | **Reject** — not repeatable |

**Recommended:** Option A.

**Guard threshold (Development):** If PPOLC fee>0 count ≥ 1,000 and base `MANNLFEE`>0 count == 0 after `#58`, log ERROR and treat run as failed (do not claim Success for client package). Soft WARN only is insufficient (accountability previously WARN’d `#58`).

---

## 6. Trace Policies

| Policy | Role | Before MANNLFEE | Proposed MANNLFEE | Current MPREM (must hold) | Pass? |
|--------|------|----------------:|------------------:|--------------------------:|-------|
| `010310404C` | Eric fee complaint | blank | **10.00** | 13.20000 | Yes (fee restore) |
| `010367131C` | `#58` golden | blank | **10.44** | 9.12000 | Yes |
| `010391876C` | `#21C` example | blank | **10.44** | 8.52000 | Yes |
| `010713704C` | `#21C` $25 example | blank | **25.00** | 20.07680 | Yes |
| `010779727C` | `#88` anchor | blank | **25.00** | **5.8615** (annualized ÷ units) | Yes — MPREM must stay |

Proposed modal for `010310404C` (factors 52 / 26.5 / 9 / 8.7019):  
**5.2000 / 2.6500 / 0.9000 / 0.8702** (matches pre-v5785 baseline).

`#58` validator expects `010367131C`: MANNLFEE 10.44; MSEMIFEE 5.4288; MQTRLFEE 2.7666; MMTHDFEE 0.9396; MMTHBFEE 0.8700.

---

## 7. Top Changes (by annual fee magnitude)

Restore is blank→fee (delta = full fee). Largest annual fees in population are **$50.00** (many policies). Eric’s delta on `010310404C` is **+$10.00** annual Pol Fee (and +modal components on Names tab).

No accidental numeric drift on non-fee columns is intended.

---

## 8. Material Calculation Impact

| Impact | Intentional? |
|--------|--------------|
| Coverage Pol Fee $0 → LifePRO fee | **Yes** — restore `#21C` |
| Names-tab Q/M amounts increase by modal fee | **Yes** — restore `#58` |
| Mode Prem header / MPREM / units | **No change** |
| Valuation Prem/Unit × units (`#88`) | **No change** |

Client-visible: Eric’s fee complaint on `010310404C` should clear after ridr reload. Fleet UAT may notice fees returning on ISWL ($25/$50) that were blank since the `#88` rebatch — that is correct restore, not a new charge invent.

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserve** — no key formatting change |
| Issue #26 primary ANN→MPREM | **Preserve** |
| Issue #88 blank-ANN annualized ÷ units | **Preserve** — verified current MPREM on `010779727C` = 5.8615; Development must not alter MPREM interceptor |
| Issue #36 / #21J factors | **Preserve** |
| Issue #21C / #58 fee formulas | **Preserve** — only load-site + guard |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] `010310404C` phase-1: MANNLFEE=10.00; modal fees 5.20/2.65/0.90/0.8702
- [ ] `010367131C`: `#58` validator golden amounts PASS
- [ ] `010391876C` MANNLFEE=10.44; `010713704C` MANNLFEE=25.00
- [ ] Fleet: base MANNLFEE>0 ≈ 4,457 (not 0)
- [ ] `#58` log line: `updated` ≈ 4457, `zero_fee` ≪ 5083
- [ ] `010779727C` MPREM still 5.8615 (or `#88` validator PASS)
- [ ] Phase-1 MPREM traces `#26`: 010310404C=13.20, 010331768C=10.96, 010367131C=9.12
- [ ] Rider phases (MPHASE>1) still blank fees
- [ ] Ridr-only rebatch after harden still populates fees (prove “never again”)
- [ ] Publish `Output/Test_Validation/quikridr.csv` on PASS

---

## 11. Recommended Development Agent Task

**Model:** Composer 2.5 (locked)  
**Requires:** User says `Approved for Development`

1. In **both** `app.py` and `QLA_Migration/app.py`: inside the existing `quikridr` PPOLC load block (~Issue #88 BILLING_MODE), also build `_policy_fee_map` from `POLICY_NUMBER` + `POLICY_FEE` (same normalize/skip-zero rules as `#21C` quikmstr block). Log cache size.
2. Keep existing `#21C` interceptor and `#58` post-emit; do **not** change formulas.
3. After `apply_modal_policy_fees_to_quikridr`, add fail-closed check: if fee candidates from cache ≥ 1000 and updated/populated MANNLFEE on base == 0 → log ERROR and raise/mark run failed.
4. Bump `APP_VERSION` in both app.py copies.
5. Re-emit `quikridr` (ridr-only OK once harden lands); run `validate_issue58_quikridr_modal_fees.py` + `#88`/`#26` spot checks.
6. Copy PASS `quikridr.csv` to `Output/Test_Validation/`.
7. Optionally note in `Issue_88/_rebatch_quikridr.py` header that fee cache now loads on ridr (no process dependency on quikmstr-first).

**Do NOT change:** Sync_Rulebook fee columns, MPREM/`#88` logic, modal factor formulas, quikplan *FEE, unrelated tables.

**Version bump:** next patch after v58.23 (e.g. v58.24) — Development sets exact.

---

## Appendix

- Simulation CSV: `Issue_Log_Items/Issue_89/evidence/issue89_risk_simulation.csv`
- Summary JSON: `Issue_Log_Items/Issue_89/evidence/issue89_risk_summary.json`
- Script: `QLA_Migration/_risk_review_issue89_policy_fee_cache.py`
- Intake / Planning / Gate: `Issue_89_*` in same folder

---

## Next step

User review → say **`Approved for Development`** and switch session model to **Composer 2.5**.
