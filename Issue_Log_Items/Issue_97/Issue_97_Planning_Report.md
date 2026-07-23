# Issue #97 — Planning Report

**Issue:** #97 — Annual policy fees / Names-tab modal premiums / blank Memos  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning Complete → Dependency Gate  
**Generated:** 2026-07-22  
**Model:** Cursor Grok 4.5  
**Depends on:** `Issue_97_Intake_Summary.md`

---

## 1. Executive finding

Eric’s #97 example (`010398471C`) is **already correct in current full Output** for fee + Names-tab amounts, and `quikmemo` CSV is populated fleet-wide. This issue should be planned as a **verify-first / package-reload** track that explains the recurring fee-factor stack, not as a new modal-fee formula change.

If QLAdmin still shows $0 after a clean reload of `quikridr` + `quikmstr` + `quikmemo` (DBF with #50 MEMOKEY pad), only then open a conversion Development task.

---

## 2. Confirmed LifePRO sources

| Source | Field | Use |
|--------|-------|-----|
| PPOLC Policy Master | `POLICY_FEE` | Annual fee → `quikridr.MANNLFEE` (#21C/#89 cache) |
| PPOLC | `MODE_PREMIUM` | Billed mode $ → `quikmstr.MMODEPREM` (#26) |
| PPBEN base | `ANN_PREM_PER_UNIT`, `NUMBER_OF_UNITS` | `MPREM` / `MUNIT` (#26/#88) |
| PNOTE / PENSE | note / ENS text | `quikmemo.MEMOTEXT` (#21M/#50) |
| Client workbook | `docs/Policy Form Modal Premium Factors.xlsx` | Plan factors → mapping CSV (#21J) |

---

## 3. Confirmed QLAdmin targets

| UI | Table.Field | Role |
|----|-------------|------|
| Coverage Pol Fee (annual) | `quikridr.MANNLFEE` | Annual policy fee on **base** phase |
| Names Modal Premium factors | `quikmstr.MSEMI/MQTRL/MMTHD/MMTHB` | % factors (#36) |
| Names Modal Premium amounts | Computed: `(MPREM×MUNIT×factor/100)+M*FEE` | Needs #58 modal fees |
| Modal fee slots | `quikridr.MSEMIFEE/MQTRLFEE/MMTHDFEE/MMTHBFEE` | `MANNLFEE × factor/100` |
| Plan form factors | `quikplan.ANNL/SEMI/QTRL/MTHD/MTHB` | Authority for factors (#21J) |
| Plan form *FEE | `quikplan.ANNLFEE…` | **Stay 0 by design** — do not use for Pol Fee |
| Memo tab | `quikmemo.MEMOKEY/MEMOTEXT` (+ DBF pad) | #21M/#50 |

---

## 4. Intended mapping stack (do not redesign)

```text
#21J  Mapping CSV ──► quikplan factors
#36   phase-1 MPLAN ──► quikmstr MSEMI/MQTRL/MMTHD/MMTHB (+ PAC overrides)
#21C  PPOLC.POLICY_FEE ──► quikridr.MANNLFEE (base only; cache on mstr + ridr paths #89)
#58   MANNLFEE × post-PAC factor/100 ──► quikridr M*FEE
UI    (MPREM×MUNIT×factor/100) + M*FEE ──► Names-tab dollars
#50   PNOTE fixed-width + MEMOKEY left-pad ──► Memo SEEK
```

**010398471C current Output (plan 17085M):**

| Item | Value |
|------|-------|
| MPREM / MUNIT / MANNLFEE | 12.00 / 9.13 / 10.44 |
| Factors S/Q/MD/MB | 52 / 26.5 / 9 / 8.3333 |
| Modal fees | 5.4288 / 2.7666 / 0.9396 / 0.8700 |
| Computed S/Q/M | **62.40 / 31.80 / 10.80** |

---

## 5. Open client / UAT questions

1. **When was QLAdmin last reloaded** for `quikridr` / `quikmstr` / `quikmemo` relative to the 2026-07-22 ~07:50 Output (and #89 v58.24)?
2. On 010398471C, is Eric reading **Coverage Pol Fee** (`MANNLFEE`) or **Plan setup fee** (`ANNLFEE` = 0)?
3. For Memos: is the load using **CSV only** or **QUIKMEMO.DBF** built with the #50 left-pad post-write?
4. After a forced reload of current Output, do fee / Names amounts / Memo clear on 010398471C?

---

## 6. Formatting / fallback rules

- Preserve QLA money formatting on fee fields (e.g. `10.4400`).
- Preserve #25 MPOLICY / MEMOKEY left-pad.
- Preserve #26 `MPREM` / `MMODEPREM` (do not overwrite billed mode prem).
- Zero LifePRO `POLICY_FEE` → leave `MANNLFEE` blank/0 (~626 policies) — not a defect.

---

## 7. Policy key handling

- Crosswalk / #25 padding unchanged.
- Memo SEEK requires MEMOKEY padding parity with MPOLICY (#50).

---

## 8. Estimated record counts

| Population | Count |
|------------|------:|
| Policies (`quikmstr`) | 5,083 |
| Fee-bearing base riders | 4,457 |
| Zero-fee base riders | 626 |
| `quikmemo` rows | 5,083 (0 empty MEMOTEXT in CSV) |

---

## 9. Sample traces

| Policy | Role | Current Output verdict |
|--------|------|------------------------|
| **010398471C** | #97 Eric example | Fee 10.44; S/Q/M 62.40/31.80/10.80; memo present |
| **010367131C** | #58 golden | Same formula family (17085M) |
| **010310404C** | #89 fee-wipe anchor | Restored under v58.24 |

---

## 10. Risks and unknowns

| Risk | Note |
|------|------|
| Stale UAT DBF | Explains $0 fee + blank memos despite good CSV |
| Looking at plan *FEE | False $0 Pol Fee |
| Partial table reload | Reload ridr without mstr → factors/fees mismatch in UI |
| #58 not formally Closed | Easy to re-open as “new” client row |
| Real post-reload defect | Only then reopen conversion path |

---

## 11. Recommended Risk Agent focus

Quantify: (a) conversion delta if we change nothing; (b) operational verify checklist; (c) Go/No-Go for **code** vs **reload-only**.

---

## 12. Recommended Development task (do not implement yet)

**Preferred path (if Risk Conditional Go — verify track):**

1. No formula changes.
2. Publish/reload package: `quikridr.csv`, `quikmstr.csv`, `quikmemo.csv` (+ DBF via #50 generator).
3. Copy `quikmstr` + `quikmemo` into `Output/Test_Validation/` alongside existing ridr.
4. Run `validate_issue58_quikridr_modal_fees.py` + `validate_issue36_quikmstr_modal_factors.py` + `validate_issue50_pnote_parse.py` / `validate_issue21m_quikmemo.py` against full Output.
5. Ask Eric to re-check 010398471C; if PASS, close #97 as UAT/package and formally close #58.

**Fallback path (only if reload still shows $0):**

- Capture screenshot + field name Eric is on.
- Then surgical investigation (screen mapping / DBF writer), not a stack redesign.
