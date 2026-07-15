# Issue #76 — Intake Summary

**Issue:** #76 — ETI/RPU phase-1 pay-up date + duration for Policy Display cash values  
**Framework stage:** Intake Agent (G0)  
**Status after intake:** Planning (Pre-Risk Auto-Chain)  
**Generated:** 2026-07-15  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Conversion (primary)  
**Priority:** Go-No Go — Policy Display CV anniversary dates wrong (2080s) on exercised ETI/RPU  
**Reporter chain:** Warren YE UAT · screenshots `010407670C` · related Robert CV validation context  
**Note:** Prior chat briefly labeled this work “Issue #73”; **#73 is CLOSED** (MISSCNTRY). This is the correct ID.

---

## Client symptom (verbatim / observed)

On Policy Display **`010407670C`** (Status **RPU**):

- Cash Values showed **02/01/2080 / 2080 / 2081** while contractual pay-up was **02/01/2027** and `MLASTANN=53`.
- Manual edit: set phase-1 **Payup = Paid To (10/01/2012)** → CV dates moved to **10/01/2026 / 2026 / 2027**.
- Duration column **`t`** showed **14** after that edit.

User direction (locked 2026-07-15):

1. Set **Payup** to the policy **paid-to** date (`MPAIDTO`).  
2. Calculate **duration** (`MLASTANN`) as **current system year − pay-up year**.  
3. Run Intake on **Cursor Grok 4.5**.

---

## Normalized symptom

| Field | Today (phase 1) | Required for ETI/RPU (44/45) |
|-------|-----------------|------------------------------|
| `quikridr.MPAYUP` | LifePRO `PAY_UP_DATE` (e.g. age-88 **20270201**) | **`quikmstr.MPAIDTO`** (e.g. **20121001**) |
| `quikridr.MLASTANN` | `valuation_year − MEFFDATE year` (e.g. **53**) | **`system_year − MPAYUP year`** (e.g. **14**) |

QLAdmin Cash Values panel uses pay-up + duration for anniversary dating when computing/displaying CV lines. Wrong pay-up + issue-based duration → far-future dates.

---

## Example policies

| QLA | MSTATUS | MPAIDTO | Phase-1 MPAYUP now | MLASTANN now | Proposed MPAYUP | Proposed MLASTANN |
|-----|---------|---------|--------------------|--------------|-----------------|-------------------|
| **`010407670C`** | 45 | 20121001 | **20270201** | **53** | **20121001** | **14** (2026−2012) |
| Peer ETI/RPU | 44/45 | varies | often ≠ paid-to | issue-based | = MPAIDTO | sys year − payup year |

---

## Fleet snapshot (Output 2026-07-15)

| Population | Count |
|------------|------:|
| MSTATUS 44 | 206 |
| MSTATUS 45 | 194 |
| Phase-1 rows on 44/45 | **400** |
| Phase-1 MPAYUP ≠ MPAIDTO | **223** |
| Phase-1 MLASTANN ≠ proposed duration | **400** |

---

## Suspected domain

**`quikridr` phase 1** for policies whose **`quikmstr.MSTATUS` ∈ {44, 45}**.  
Not `quikmstr.MNFOPT` (#72 — already fixed). Not PUA inheritance (#60). Not `MISSCNTRY` (#73 CLOSED).

Affected QLAdmin table: **`quikridr`** (Help §7.203 — `MPAYUP`, `MLASTANN`, `MCV0/1/2`).

---

## In scope / out of scope (first pass)

| In scope | Out of scope |
|----------|----------------|
| Phase-1 `MPAYUP` ← `quikmstr.MPAIDTO` when master status 44/45 | Changing phase-1 for active / non-ETI/RPU statuses |
| Phase-1 `MLASTANN` ← system year − year(`MPAYUP`) for those rows | Changing #60 PUA rule (`MPAYUP=MEFFDATE` on `*PA`) |
| Preserve MEFFDATE / MAGE / MEXPRY / MUNIT / MPREM | Inventing stored MCV amounts (rebuild CV remains UAT) |
| Validator + rebatch `quikridr` + Test_Validation | MRRULE / rates / NFOINT (#60 Track B) |
| Document UAT: Data Admin + Rebuild CV after reload | Altering `quikmstr.MPAIDTO` itself |

---

## Related issues

| Issue | Relationship |
|-------|----------------|
| **#60** | PUA-only `MPAYUP=MEFFDATE` — **must not regress**; #76 is phase-1 ETI/RPU |
| **#72** | NFO 44→2 / 45→3 — complementary; already Done for display NFO |
| **#73** | CLOSED MISSCNTRY — **not** this issue (ID collision avoided) |
| **#21E** | Traditional MCV blank by design — rebuild CV after dates fixed |
| **#71** | BAND→00 — rate lookup; separate |

**Not a regression of #25 / #26.**

---

## Artifact inventory

| Have | Missing |
|------|---------|
| Screenshots: 2080 CVs; payup=paid-to → 2026 CVs; `t=14` | Formal Chris write-up (user lock accepted) |
| Sample `010407670C` source PAY_UP_DATE=20270201 | Confirmation whether YE batch should use `QLA_VALUATION_DATE` year instead of system year for MLASTANN (Planning OBQ) |
| Locked SD answers (payup=MPAIDTO; duration=sys year−payup) | — |

---

## Immediate blockers visible at intake

None for Intake. Planning must lock:

1. Scope = **phase 1 + master status 44/45 only** (assumed from UAT).  
2. **“Current” year** for duration = conversion run date year vs `QLA_VALUATION_DATE` year (YE=2025 → duration **13** vs screenshot **14**).  
3. Interaction with existing `_apply_quikridr_mlastann` (today always uses **MEFFDATE**).

---

## Gate Criteria (G0 — Intake Complete)

- [x] Issue folder created under `Issue_Log_Items/Issue_76/`
- [x] Intake summary written
- [x] Example policies listed
- [x] Owner and priority assigned
- [x] No code or rulebook changes made

---

## Recommended next step

**Planning Agent** (same session — Pre-Risk Auto-Chain) → Dependency Gate → stop.
