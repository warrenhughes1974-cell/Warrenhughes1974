# Issue #97 — Intake Summary

**Issue:** #97 — Annual policy fees / Names-tab modal premiums incorrect; Memos blank  
**Client log ID:** 97 (Active)  
**Framework stage:** Intake Agent (G0)  
**Status recommendation:** Planning → Dependency Gate → Risk (verify-first; likely UAT/load vs new conversion defect)  
**Generated:** 2026-07-22  
**Owner:** Conversion (Warren) · **Reporter / UAT:** Eric · **Business status:** No-Go  
**Priority:** High (same symptom family as #21C / #58 / #89 / #50)  
**Model:** Cursor Grok 4.5 (locked Intake stage)

---

## 1. Client symptom (verbatim)

> Annual policy fees are incorrect, Modal Premiums on Names tab are incorrect and do not match factors on policy form level, Memos section is blank (Issue 50?). Example policy 010398471C should have a policy fee of $10.44 and it is $0 in QLAdmin. Premium Amounts should be Semiannual - $62.40, Quarterly $31.80, and Monthly $10.80. Memos appear to be blank for all policies. 7/22/2026 No-Go Eric Warren

## 2. Client symptom (normalized)

Three complaints bundled on one log row:

| # | Symptom | Eric expected (010398471C) | What Eric sees in QLAdmin |
|---|---------|----------------------------|---------------------------|
| A | Annual policy fee | $10.44 | $0 |
| B | Names-tab Modal Premiums | S $62.40 / Q $31.80 / M $10.80 | Incorrect (not matching plan factors) |
| C | Memo tab | Notes present | Blank for all policies (suspects #50) |

## 3. Example policy

| Policy | Plan (phase 1) | Notes |
|--------|----------------|-------|
| **010398471C** | `17085M` | Same GL85-M family as #58 goldens (`010367131C`) |

Evidence: `evidence/issue97_010398471C_output_trace.csv`

## 4. Intake finding (critical)

**Current `QLA_Migration/Output/` already matches Eric’s dollar expectations for 010398471C.**

| Field / amount | Current Output | Eric expected | Match |
|----------------|----------------|---------------|-------|
| `quikridr.MANNLFEE` (phase 1) | **10.4400** | 10.44 | Yes |
| Names S (computed) | **62.40** | 62.40 | Yes |
| Names Q (computed) | **31.80** | 31.80 | Yes |
| Names M draft (computed) | **10.80** | 10.80 | Yes |
| `quikmemo` row | Present with `[CONVERSION]` + `[PNOTE]` + `[ENS]` | Not blank in CSV | Yes in CSV |

QLAdmin Names-tab math (Issue #58):

```text
(MPREM × MUNIT × factor/100) + modal_fee
S: (12 × 9.13 × 0.52) + 5.4288 = 62.40
Q: (12 × 9.13 × 0.265) + 2.7666 = 31.80
M: (12 × 9.13 × 0.09) + 0.9396 = 10.80
```

Fleet snapshot (Output as of 2026-07-22 morning ridr/mstr):

| Check | Result |
|-------|--------|
| Base `MANNLFEE` > 0 | **4,457** / 5,083 |
| Modal fee columns > 0 | **4,457** / 5,083 |
| `quikmstr` MSEMI/MQTRL/MMTHD/MMTHB blank | **0** / 5,083 |
| `quikmemo` rows / empty MEMOTEXT | **5,083** / **0** empty |

So Intake classifies this primarily as **re-report / UAT environment** of the fee+factor stack (#21C→#36→#58→#89) plus possible **Memo DBF SEEK** (#50), not a new missing mapping in the current CSV package.

## 5. Suspected domain

| Domain | Assessment |
|--------|------------|
| Conversion CSV emit (current Output) | **Appears correct** for the cited policy |
| UAT load / stale DBF package | **Primary suspect** — Eric sees $0 fee while CSV has 10.44 |
| Plan-level fee fields (`quikplan.ANNLFEE`… = 0) | **Secondary UI trap** — intentional; fees live on `quikridr` |
| Memo CSV vs Memo DBF SEEK (#50) | **Likely for “blank for all”** if QUIKMEMO.DBF rebuilt without left-pad rewrite |
| New formula defect | **Unlikely** until post-reload still fails |

## 6. In scope / out of scope (first pass)

**In scope**

- Prove whether Eric’s QLAdmin environment matches current Output for 010398471C.
- Document the fee/factor stack so this stop re-opening every UAT cycle.
- Confirm Memo path: CSV content vs DBF `MEMOKEY` pad.
- Close the loop on #58 (still “IMPLEMENTED”, not Closed) if goldens still pass after reload.

**Out of scope (unless reload still fails)**

- Changing `MANNLFEE` / modal-fee formulas (#21C/#58).
- Changing plan modal factors (#21J) or policy factor copy (#36).
- Reworking PNOTE parse (#50) unless DBF pad regressed.
- Altering `MMODEPREM` / `MPREM` (#26).

## 7. Related issues (why this keeps coming up)

| ID | What it fixed | Why it still surfaces |
|----|---------------|------------------------|
| **#21C** | `POLICY_FEE` → `quikridr.MANNLFEE` | Fee only on base rider; plan form fees stay 0 |
| **#21J** | Plan factors on `quikplan` | Names tab does **not** read plan alone |
| **#36** | Copy factors → `quikmstr` | Blank policy factors → crude ÷ mode |
| **#58** | Modal fees on `quikridr` | Without M*FEE, Q/M short by fee×factor |
| **#89** | Ridr-only rebatch wiped fees | Partial rebatch made #58 look “broken” again |
| **#50** | PNOTE parse + MEMOKEY left-pad | CSV can be full while Memo tab SEEK shows blank |
| **#88** | MPREM unit fallback | Triggered the ridr-only path that caused #89 |

## 8. Immediate blockers at intake

None for framing. **Planning must treat “reload + screenshot confirmation” as the first gate**, not a new fee formula.

## 9. Artifact inventory

| Artifact | Status |
|----------|--------|
| Client log row (97) | Provided in chat |
| Output trace 010398471C | `evidence/issue97_010398471C_output_trace.csv` |
| Screenshots of Eric’s current QLAdmin | **Missing** |
| Confirmation of last QLAdmin load date/package | **Missing** |
| Prior #58/#89/#50 docs | Present under their Issue folders |

## 10. Owner / severity

- **Owner:** Conversion (verify + package) first; Client UAT confirmation required.
- **Severity:** High for UAT trust; **not** currently evidence of a new Output defect on the cited policy.
