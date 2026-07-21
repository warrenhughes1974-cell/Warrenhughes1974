# Issue #79 — Planning Report

**Issue:** #79 — Align `quikclms.CLAIMSTAT` to real Policy-book conventions  
**Framework stage:** Planning Agent  
**Status:** Planning Complete → Dependency Gate  
**Generated:** 2026-07-17  
**Model:** Cursor Grok 4.5 (locked)  
**Code changes:** None  
**Scope authority:** `Issue_79_Scope_Decisions.md` (SD-79-1 … SD-79-10)

---

## 1. Executive Finding

Real `docs/Policy/quikclms.dbf` uses **2** for finished deaths, **99** for surrenders, **98** for maturities, and virtually never **1** or **3** on historical paid claims. Our emit maps SETTLED→**3** and FUNDED→**1**, leaving **494 Pending** (492 with payments) and **1,275 deaths at 3**. User locked the Policy-book rule. Recommended direction: post-map / derivation remap of `CLAIMSTAT` by claim family + payment/lifecycle evidence. **Go for Dependency Gate / Risk.**

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source / authority | File pattern | In package? | Row count |
|--------------------|--------------|-------------|----------:|
| Policy-book authority | `docs/Policy/quikclms.dbf` | Yes | 7,691 |
| Converted headers | `Output/quikclms.csv` | Yes | 5,624 |
| Converted payments | `Output/quikclmp.csv` | Yes | 6,151 (post-#78) |
| Derivation rules | `claims_analysis/config/quikclms_derivation_rules.json` | Yes | — |

CLAIMSTAT is **not** a Master_Value_Translation lookup. It is derived from reconstructed lifecycle + family defaults.

### Available signals for remap

| Signal | Source | Notes |
|--------|--------|-------|
| Claim family | `MEMOTEXT` / reconstructed claim family | DEATH / SURRENDER / PARTIAL / DISBURSEMENT |
| Lifecycle | memo token SETTLED/FUNDED/PAID | Drives today’s 3 vs 1 |
| Payment evidence | `quikclmp` join or MPAID > 0 | Closes false Pending |
| Policy-book pattern | CAUSE SRR→99, MAT→98, numeric death→2 | Target convention |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source |
|-------|-------|------|--------|--------|
| quikclms | CLAIMSTAT | N | 2 | Help: 1 Pending, 2 Paid in Full, 3 Settled, 4 Denied, 98 Matured, 99 Surrender |
| quikclms | ORIGSTTUS | C | — | CSV name; DBF is ORIGSTATUS — out of scope unless Risk adds safe mirror |

**Repo references:**

| Location | Role |
|----------|------|
| `claims_analysis/config/quikclms_derivation_rules.json` | lifecycle_status_mapping + claim_family_mapping |
| `QLA_Migration/Configs/Sync_Rulebook_quikclms.csv` | claimstat → CLAIMSTAT |
| `qla_core/claims_emit_enhancements.py` | ISWL Disbursement → 99 override |
| `QLA_Migration/app.py` claims emit | Integration point for remap hook |

---

## 4. Required Source-to-Target Field Mapping

| Input | Rule | Target CLAIMSTAT | Change? |
|-------|------|------------------|---------|
| DEATH + paid/settled/funded with evidence | SD-79-2 | **2** | Yes (from 1 or 3) |
| SURRENDER / PARTIAL_SURRENDER / DISBURSEMENT | SD-79-3 | **99** | Yes when currently 1 |
| MATURITY family | SD-79-4 | **98** | Yes if any exist at wrong status |
| Truly unpaid open death | SD-79-5 | **1** | Rare keep |
| Denied (if ever evidenced) | Help | **4** | N/A today |

### Fields that must remain unchanged

| Target | Touch this issue? |
|--------|-------------------|
| `quikclmp` rows (#78) | **No** |
| `quikclms` money fields (MPAID/MFACE/…) | **No** (status only) |
| MPOLICY padding (#25) | **Preserve** |
| MPREM (#26) | **No** |

---

## 5. Open Client Questions

1. **OBQ-79-1:** When remapping CLAIMSTAT, should `ORIGSTTUS` also be updated, left as-is, or fixed separately to pre-death policy status?  
   - *Planning default:* leave ORIGSTTUS alone this issue (companion), unless Risk finds emit currently forces ORIGSTTUS=CLAIMSTAT and a minimal sync is safer.

2. **OBQ-79-2:** Any death claims with payments but still “Pending” intentionally for contestability?  
   - *Planning default:* no — historical conversion; paid → 2.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| CLAIMSTAT | Numeric string `2` / `99` / `98` / `1` / `4` |
| Audit | before_status, after_status, family, mpolicy, reason_code |
| Idempotent | Remap only when current ≠ proposed |

---

## 7. Memo / Text / Special Handling

Do not rewrite MEMOTEXT. Family detection may read existing memo lineage tokens already present.

---

## 8. Policy Number Key Handling

No key changes. Use existing MPOLICY (#25) for joins to `quikclmp` payment evidence.

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| quikclms rows | 5,624 | Output |
| Would change CLAIMSTAT | ~1,769 | Death 1/3→2 + Surrender 1→99 |
| Deaths → 2 | ~1,290 | 15 Pending + 1,275 Settled |
| Surrenders → 99 | ~479 | Pending surrender |
| Stay 99 | ~3,855 | Already aligned |
| Truly remain Pending | ~2 | Pending with no payment (edge) |

---

## 10. Sample Trace

| Policy | Before | After | Reason |
|--------|--------|-------|--------|
| `010397318C` | 3 | **2** | Death paid/settled → Paid in Full |
| `010391359C` | 1 | **2** | Death FUNDED + payment |
| `010469081C` | 1 | **99** | Surrender pending → Surrender |
| `010154425C` | 99 | **99** | Disbursement already correct |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Item 15 used CLAIMSTAT=3 for orphans | Medium | SD-79-8 supersession documented |
| ORIGSTTUS left inconsistent with CLAIMSTAT | Medium | OBQ-79-1; companion preferred |
| False family parse from MEMOTEXT | Low | Prefer reconstructed family fields if still on staged emit path |
| Open claims wrongly closed | Low | Keep 1 only when no payment + not settled/paid |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source / authority present | Yes — Policy DBF + Output |
| Field definitions confirmed | Yes — Help + real book |
| Client scope clear | Yes — SD-79-* locked |
| Example policies available | Yes |

---

## 13. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue #79.

Read AI_Agents/Risk_Agent.md and Templates/Risk_Report_Template.md.
Also read Issue_79_Intake_Summary.md, Issue_79_Scope_Decisions.md,
Issue_79_Planning_Report.md, Issue_79_Dependency_Gate.md.

Model: Cursor Grok 4.5. Do not code.

Quantify before/after CLAIMSTAT impact (~1,769 headers): deaths→2,
pending surrenders→99. Confirm #78 payments untouched. Go/No-Go for Development.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. Surgical remap of `quikclms.CLAIMSTAT` after claims emit (or in derivation) per SD-79-2..5.
2. Write `Reports/issue79_claimstat_remap_audit.csv`.
3. Do not touch `quikclmp` or claim money fields.
4. Version bump both `app.py` (next after current, e.g. v57.99 if still on v57.98).
5. Validator: `_validate_issue79_claimstat.py` — counts, traces, non-candidate money unchanged.
6. On PASS: copy `quikclms.csv` to `Output/Test_Validation/`.

---

## Appendix

- Related: #78, Claims Item 15 (superseded for death=3), Phase 10B lifecycle mapping  
- Authority: `docs/Policy/quikclms.dbf` status×CAUSE analysis 2026-07-17
