# Issue #71 — Intake Summary

**Issue:** #71 — Rate / plan / policy BAND standardize to `00` (NOT APPLICABLE)  
**Framework stage:** Intake Agent (G0)  
**Status after intake:** Planning  
**Generated:** 2026-07-14  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Conversion (primary) — rate emit + band member tables; policy `MBAND` already `00`  
**Priority:** Go-No Go — blocks Policy Display cash-value (and other rate) lookups  
**Reporter chain:** Warren / YE UAT — Policy Display CV zeros on `010718309C` despite loaded factors  

---

## Client symptom (verbatim / observed)

YE Policy Display for **`010718309C`** (`1658C1`) shows Cash Values **0.00** on future anniversary lines. Plan interest (`NFOINT=A`) and QuikCvs factors exist, but policy **`MBAND=00`** while rate keys are **`BAND=01`** — lookup miss.

User direction: **everything band zero** — plan code band setup, policy level, and all rate keys.

Chris already directed (2026-07-14) on quikridr rulebook: **`MBAND` default `00` (NOT APPLICABLE); do not default to `01`.**

---

## Normalized symptom

| Layer | Current YE Output | Target |
|-------|-------------------|--------|
| `quikridr.MBAND` | **`00`** on all 6,936 rows | Keep **`00`** |
| Factor tables (`QuikCvs`, `QuikNps`, `QuikTvs`, …) | Almost all **`BAND=01`** | **`BAND=00`** |
| Key tables (`QuikPlCv`, `QuikPlTv`, …) | Almost all **`BAND=01`** | **`BAND=00`** |
| `QuikPlBd` band definitions | `BDCODE=01` (BAND 1) | `BDCODE=00` (NOT APPLICABLE) |
| `QuikGps` / `QuikPlGp` | Mix **`01`/`02`/`03`** | **`00`** with collision rule (see Planning) |

---

## Example policies

| QLA | Plan | Policy MBAND | Rate BAND today | Symptom |
|-----|------|--------------|-----------------|---------|
| **`010718309C`** | `1658C1` | `00` | `01` | Policy Display CV = 0.00; stored `MCV0≈986` present |
| `010713704C` | `1659C2` | `00` | `01` | Same class mismatch (peer) |
| `015000057C` | `17CSI5` | `00` | `01` | Same class mismatch (peer) |

---

## Suspected domain

**Rates + plan band member setup** (not LifePRO re-extract). Policy band already correct per Chris.

---

## In scope / out of scope (first pass)

| In scope | Out of scope |
|----------|----------------|
| Emit/remap rate factor + key `BAND` → `00` | Changing `MUWCLASS` / gender keys |
| `QuikPlBd` `BDCODE` → `00` | Inventing NFOINT (#60 Track B) |
| Confirm `quikridr.MBAND` stays `00` | Loan / LOANINTX (#70) |
| Document multi-band GP collision handling | Adding new plans |

---

## Related issues

- **#70** — LOANINTX (separate)  
- **#60** — PUA / NFOINT (separate; CV $ still needs interest on CRVM plans)  
- Rulebook note on `Sync_Rulebook_quikridr.csv` MBAND=`00` (Chris 2026-07-14)

---

## Immediate blockers visible at intake

None for Intake. Planning must resolve **QuikGps multi-band → 00 key collisions** before Development.

---

## Gate Criteria (G0 — Intake Complete)

- [x] Issue folder created under `Issue_Log_Items/Issue_71/`
- [x] Intake summary written
- [x] Example policies listed
- [x] Owner and priority assigned
- [x] No code or rulebook changes made
