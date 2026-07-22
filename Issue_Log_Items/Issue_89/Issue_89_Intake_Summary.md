# Issue #89 — Intake Summary

**Issue:** #89 — Policy fee wipe on `quikridr`-only rebatch (`MANNLFEE` / modal fees blank fleet-wide)  
**Framework stage:** Intake Agent (G0)  
**Status recommendation:** Intake Complete → Planning  
**Generated:** 2026-07-22  
**Owner:** Conversion  
**Priority:** High (client UAT regression; Eric re-reporting fee defect already fixed by #21C / #58)

---

## Client symptom (verbatim + normalized)

**Verbatim (internal):** Eric is saying there is a policy fee issue on policy `010310404C`.

**Normalized:** QLAdmin shows **$0 policy fee** (and blank modal fee slots) on a fee-bearing traditional policy. LifePRO still has annual policy fee **$10.00**. Symptom matches prior #21C (annual Pol Fee missing) and #58 (Names-tab mode amounts short when modal fees blank).

## Example policies

| QLA policy | LifePRO | Plan | Source fee | Current Output `MANNLFEE` | Prior good baseline |
|------------|---------|------|------------|---------------------------|---------------------|
| `010310404C` | `9010310404` | `1960PO` | PPOLC `POLICY_FEE`=**10.00**; PPBEN seq1 `BENEFIT_FEE`=**10.00** | **blank** | `10.0000` + modal 5.20/2.65/0.90/0.8702 (`quikridr_pre_v5785`) |
| Fleet | — | base rows | PPOLC fee>0 = **4,457** | Output populated = **0 / 6,934** | #21C/#58 era ~4,457 |

## Suspected domain

Conversion engine — `quikridr` policy fee emit (`MANNLFEE` + `#58` modal `M*FEE`), not LifePRO source defect.

## In scope (first pass)

- Restore `#21C` / `#58` fee population in current Output for Eric’s package.
- **Harden** so `quikridr`-only rebatches cannot wipe fees again (fee cache must load on ridr path, not only under `quikmstr`).
- Fail-closed guard when source has thousands of fees and Output has ~0.
- Preserve `#25` MPOLICY, `#26`/`#88` MPREM, `#36`/`#21J` modal factors.

## Out of scope (first pass)

- ISWL plan UF monthly expense setup (#43 / #23).
- Changing fee formula (`MANNLFEE × factor/100`).
- Plan-level `quikplan` *FEE columns (still 0 by design in #58).
- Unrelated PUA / CV issues on the same sample policy (#56 withdrawn / #60).

## Related issues

| ID | Relationship |
|----|----------------|
| **#21C** | Parent fix — `POLICY_FEE` → `MANNLFEE` (IMPLEMENTED / RELEASED). This issue is a **regression of that emit path**. |
| **#58** | Modal fees from `MANNLFEE` × factors (IMPLEMENTED v57.80). Cascades when `MANNLFEE` blank. |
| **#88** | Closed v58.23 — `quikridr`-only rebatch restored MPREM but **did not load fee cache** → proximate cause of wipe. |
| **#36 / #21J** | Modal factors on `quikmstr` — preserve; post-ridr copy still runs. |

## Immediate blockers at intake

None for framing. Root cause already evidenced in `QLA_Migration/Logs/_issue88_quikridr_rebatch_log.txt` (`Issue 58: … updated=0, zero_fee=5083`; no Policy Fee Cache line).

## Artifact inventory

| Artifact | Status |
|----------|--------|
| Eric report on `010310404C` | Provided (chat 2026-07-22) |
| PPOLC / PPBEN Source 20260630 | Present |
| Current `Output/quikridr.csv` (blank fees) | Present (mtime 2026-07-21 20:09) |
| Issue #88 ridr-only rebatch log | Present — smoking gun |
| Pre-v5785 ridr baseline with fees | Present under Issue #60 evidence |
| #58 validator / accountability WARN | Prior WARN on blank fees |

## Severity / owner

- **Severity:** High — client sees previously fixed fee defect again; trust / UAT churn.
- **Owner:** Conversion (engine cache placement + emit guard; rebatch `quikridr`).
- **Not** a LifePRO extract gap for this policy.
