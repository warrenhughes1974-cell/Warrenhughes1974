# Issue #145B — UAT result capture

Fill this after Control and Test are loaded into equivalent QLAdmin environments and anniversary / ISWL processing has been run on **both**.

**Testers:** _______________  
**Date run:** _______________  
**QLAdmin environment:** _______________  
**Valuation / process date:** _______________

**2026-08-20 agent note:** Package reconfirmed (Control SHA matches Output; Test = 10 gold rows removed; #146 leftovers still in both). QLAdmin load and anniversary were **not** run from this workspace — no QLAdmin UAT environment is available to the agent. Actuals below stay blank until Warren/Eric run both legs. Overall status: **INCOMPLETE — blocked on QLAdmin A/B execution.** Do not treat this as PASS, FAIL, or authorization to implement.

Converter was not changed for this test. Control QuikIsrr SHA `667d73c79889bf6dd81bcf201ce25928b89004b99d38ff8340e9dd92cad0c6d0`. Test SHA `ac6e1c4b01d7be2d8b3dbc01482827a6876a21a91a9965819fb7055bf6893919`.

---

## Pre-anniversary (should match on both legs)

| Policy | Expected MUNIT | Control actual | Test actual | Match? |
|---|---:|---:|---:|---|
| 9010815236C | 25 | | | |
| 9011050114C | 25 | | | |
| 9011069610C | 50 | | | |

If pre-anniversary units already differ, stop. The packages were not loaded equivalently.

---

## Post-anniversary units

| Policy | Expected Control | Control actual | Expected Test | Test actual |
|---|---:|---:|---:|---:|
| 9010815236C | 23.59744 | | 25 | |
| 9011050114C | 24.864 | | 25 | |
| 9011069610C | 49.594 | | 50 | |

Also record Amount Ins / MDB if shown:

| Policy | Expected Control face | Control actual | Expected Test face | Test actual |
|---|---:|---:|---:|---:|
| 9010815236C | 23,597.44 | | 25,000 | |
| 9011050114C | 24,864.00 | | 25,000 | |
| 9011069610C | 49,594.00 | | 50,000 | |

---

## Side-effect watch (same on both legs unless noted)

| Check | Control | Test | Material difference? |
|---|---|---|---|
| Billed / modal premium | | | |
| Cash / fund value | | | |
| Vanish flag | T / T / T expected | T / T / T expected | |
| #146 9010761639C units | | | Must not change vs each other |
| #146 9010760840C units | | | Must not change vs each other |
| Non-gold ISWL sample (pick one) | | | |

---

## Decision

- [ ] **PASS** — Control dropped as expected; Test held LifePRO units. Supports later #145B emit exclusion.  
- [ ] **FAIL** — Test still lost units. Do not implement exclusion.  
- [ ] **INCOMPLETE** — load / anniversary not equivalent; rerun.

**Notes:**

---

## Sign-off

| Role | Name | Date |
|---|---|---|
| Tester | | |
| Warren | | |
