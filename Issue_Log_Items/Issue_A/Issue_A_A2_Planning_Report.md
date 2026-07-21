# Issue A — A2 Planning Report (Calc Dfcy / Deficiency Reserves)

**Sub-item:** A2  
**Framework stage:** Planning (A2 scope)  
**Status:** **Blocked — Awaiting CSO Clarification**  
**Generated:** 2026-07-20  
**Track:** Internal only

---

## 1. Executive finding

Robert’s rule: for plans **without indeterminate premiums**, ask CSO whether deficiency reserves should be calculated; if yes, set **Calc Dfcy = TRUE** in QLAdmin.

In conversion output this is **`quikplan.DEFICIENCY`**. Today **all 141 plans emit `N`** (rulebook default `DEFICIENCY,N,SKIP_TRANSLATION`). No code change should ship until CSO answers **fleet-wide vs plan-by-plan** and confirms which plans are truly **indeterminate premium**.

**Conflict to resolve:** Data governance rule **DG-QUIKPLAN-020** requires `DEFICIENCY=N` for plan codes starting with **A–Z or 9** (58 plans). If CSO wants Calc Dfcy ON for some of those, governance rule and/or scope must be revised with CSO sign-off.

---

## 2. Field mapping

| QLAdmin UI | CSV column | Current emit | Proposed when CSO says yes |
|------------|------------|--------------|----------------------------|
| **Calc Dfcy** | `DEFICIENCY` | `N` (all plans) | `Y` for confirmed non-indeterminate plans |

**Not the same field:** `CALCADV` (also defaults `N`) — separate plan attribute; Robert’s email refers to **Calc Dfcy** = `DEFICIENCY` per QLAdmin Help / phase R1 research.

**Rulebook today:**

```46:46:QLA_Migration/Configs/Sync_Rulebook_quikplan.csv
,DEFICIENCY,N,,,SKIP_TRANSLATION
```

---

## 3. Current fleet state (Output after A1 run, v58.20)

| Metric | Count |
|--------|------:|
| Total plans | 141 |
| `DEFICIENCY=N` | 141 |
| `DEFICIENCY=Y` | 0 |

**Indeterminate-premium heuristic (DESCR contains INTEREST-SENSITIVE / ISWL / etc.):** **8 plans**

| PLAN | DESCR |
|------|-------|
| 1658C1 | INTEREST-SENSITIVE WHOLE LIFE |
| 1658CS | INTEREST-SENSITIVE WHOLE LIFE |
| 1659C2 | INTEREST-SENSITIVE WHOLE LIFE |
| 1659CS | INTEREST-SENSITIVE WHOLE LIFE |
| 1659CR | INTEREST-SENSITIVE WHOLE LIFE |
| 1659SR | INTEREST-SENSITIVE WHOLE LIFE |
| 1669SR | INTEREST-SENSITIVE WHOLE LIFE |
| 1679CS | INTEREST-SENSITIVE WHOLE LIFE |

**A2 candidate set (if CSO says yes for all non-indeterminate):** **133 plans** (heuristic only — not authoritative).

Full inventory: `Issue_Log_Items/Issue_A/Reports/A2_deficiency_inventory.csv`

---

## 4. Indeterminate premium — what we do **not** know yet

Conversion has **no LifePRO “indeterminate premium” flag** wired today. Options for an authoritative list:

| Source | Usability |
|--------|-----------|
| CSO / Eric plan-by-plan list | **Preferred** |
| DESCR keywords (8 ISWL above) | Starter only |
| `plan_classification.csv` `IS_UL` | Only 7 rows populated — insufficient |
| PRODUCT type on quikplan | Needs CSO mapping |

**Do not auto-detect from description alone** (same lesson as A1).

---

## 5. Governance conflict (must resolve before Development)

**DG-QUIKPLAN-020:** For plans whose first character is **A–Z or 9**, `DEFICIENCY` must be **`N`**.

- **58 plans** in current Output match that pattern (mostly `9*` riders + `A*` annuity riders).
- Robert’s A2 could require **`Y`** on some numeric-prefix life plans (e.g. `1L17SP`, `1668SP`) without touching DG-020.
- If CSO wants Calc Dfcy on **`9*` or `A*` plans**, DG-020 must be **waived/revised** explicitly.

---

## 6. Recommended implementation (after CSO answer)

Mirror A1 pattern — **config-driven, surgical:**

1. Add `QLA_Migration/Configs/deficiency_calc_plans.csv` (`PLAN`, `DEFICIENCY`, `NOTES`) **or** `calc_dfcy_yes.csv` plan list only.
2. Post-process in `apply_deficiency_settings()` after quikplan emit (same layer as single-prem).
3. **Exclude** plans on CSO indeterminate-premium list (keep `N`).
4. Do **not** change rulebook default until CSO confirms fleet rule.
5. If DG-020 conflict: limit Y to numeric-prefix plans only, or update governance with CSO approval.

**Estimated row changes (if CSO says yes for all non-indet heuristic):** up to **133** plans `N→Y`. Validate with actuarial UAT on sample reserves.

---

## 7. Open questions — CSO (required before Development)

1. **Fleet rule:** Should Calc Dfcy be **Y for all non-indeterminate-premium plans**, or only a **named list**?
2. **Indeterminate list:** Provide authoritative plan codes (we propose excluding the **8 ISWL** plans above as starters).
3. **Prefix `9*` / `A*` riders:** Should any ever have Calc Dfcy **Y**? (Conflicts with DG-QUIKPLAN-020 today.)
4. **Acceptance:** Which plan(s) will CSO use to UAT deficiency reserve behavior after reload?

---

## 8. Risk preview (for Risk Agent when CSO clears)

| Risk | Severity |
|------|----------|
| Valuation / reserve calculation behavior change | High |
| DG-QUIKPLAN-020 failures on A/9 plans if set Y | High |
| Unrelated fields (#25/#26) | None |

**Recommendation:** **NO-GO for Development** until CSO answers §7.

---

## 9. Checklist / next steps

| Step | Owner |
|------|-------|
| CSO answers §7 | CSO |
| Risk Agent quantifies impact per confirmed plan list | Warren |
| Development (config + post-process) after approval | Composer 2.5 |
| Re-run quikplan + Issue A checklist A2 | Warren |

---

## Appendix

- Script: `Issue_Log_Items/Issue_A/scripts/_research_issueA_a2_deficiency.py`
- Inventory: `Issue_Log_Items/Issue_A/Reports/A2_deficiency_inventory.csv`
