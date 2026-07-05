# Reinsurance Phase 1 — Implementation Notes

**Scope:** QLAdmin Reinsurance Phase 1 (stored LifePRO values only)  
**Engine:** v57.50  
**Status:** Complete — validation PASS (May 2026 extract)

---

## Phase 1 scope

| Included | Excluded |
|----------|----------|
| `QuikRein` (treaty setup) | `QuikRcoa` |
| `QuikRmst` (policy/phase/treaty master) | `QuikRbll`, `QuikRblh`, `QuikRpln`, `QuikRval`, `QuikReft` |
| | PRADJ billing/history |

---

## Stored-value authority rule

LifePRO stored reinsurance values are authoritative. The converter **does not recalculate**:

- Retained amount
- Ceded amount
- Reinsurance premium
- Net amount at risk (NAR)
- Treaty allocation
- Percent-of-initial ceded (`MPCTCEDED` remains blank in Phase 1)

Values are parsed, formatted, and mapped — not derived by formula.

---

## LifePRO source files

| File pattern | Role |
|--------------|------|
| `PROD_PTRTY_TreatySetup_Extract*.csv` | `QuikRein` driver |
| `PREIN_ReinsuranceDetail_Extract*.csv` | Parent detail (`MRETAINED` source) |
| `PREINTRT_ReinsuranceDetailTreaty_Extract*.csv` | `QuikRmst` driver (`MCEDED` source) |

**Dependencies:** Converted `quikmstr.csv` and `quikridr.csv` in `QLA_Migration/Output/` for policy/phase validation.

**Crosswalks:**

- `plan_governance/config/reinsurer_crosswalk.csv` — `MREINCO`, `MREINNAME` (Phase 1 placeholders)
- `plan_governance/config/reinsurance_type_crosswalk.csv` — `REINSURANCE_CODE` → `MTYPE`

---

## Output tables generated

| Table | Output path (gated) | Rows (May 2026) |
|-------|---------------------|-----------------:|
| `QuikRein` | `QLA_Migration/Output/quikrein.csv` | 7 |
| `QuikRmst` | `QLA_Migration/Output/quikrmst.csv` | 733 |

QA reports (always): `plan_analysis/phase_r9_quikrein_rmst/`

---

## PREINTRT canonical selection

LifePRO stores multiple historical treaty allocation rows per policy/benefit/treaty key. `QuikRmst` grain is **policy / phase / treaty**.

| Metric | Count |
|--------|------:|
| Raw `PREINTRT` rows | 3,545 |
| Canonical rows (latest `EFFECTIVE_DATE`, then `RECORD_SEQUENCE`) | 733 |
| Superseded rows (audited, not summed) | 2,812 |
| `QuikRmst` emitted | 733 |

Superseded detail: `plan_analysis/phase_r9_quikrein_rmst/superseded_preintrt_rows.csv`

---

## Reconciliation (May 2026 extract)

| Check | Result |
|-------|--------|
| Ceded (`PREINTRT.AMOUNT_REINSURED` canonical sum vs `QuikRmst.MCEDED`) | **$4,101,000.00** source = emit — PASS |
| Retained sum | INFO only — `MRETAINED` repeats on each treaty row per parent `PREIN` |
| QuikRein treaty count vs `PROD_PTRTY` | 7 = 7 — PASS |
| Exceptions | 0 |

---

## Placeholder reinsurer crosswalk

Phase 1 uses **user-approved placeholders** in `reinsurer_crosswalk.csv`:

- `CONFIDENCE`: `Manual Placeholder`
- `SOURCE`: `User Provided`

These are **not** LifePRO source-proven legal reinsurer names. Every emit trace row flags the placeholder status in `reinsurance_mapping_trace.csv`.

Treaty codes: L14, L14CSI, L14CSO, L15, L15CSI, L15CSO, MUNICH50.

---

## MUNICH50 note

`MUNICH50` emits in **QuikRein** (treaty setup) but has **zero** `PREINTRT` rows in the May 2026 extract. No `QuikRmst` rows for this treaty — expected.

---

## Environment flags

| Flag | Effect |
|------|--------|
| `QLA_ENABLE_REINSURANCE_EMIT=1` | Run converter in batch (root or QLA_Migration `app.py`) |
| `QLA_REINSURANCE_WRITE_OUTPUT=1` | Write `quikrein.csv` + `quikrmst.csv` to Output |

**Off by default** — standard batch behavior unchanged unless flags are set.

---

## Code modules (no redesign)

| Module | Purpose |
|--------|---------|
| `qla_core/reinsurance_source_loader.py` | Read-only PROD_PTRTY/PREIN/PREINTRT loaders + canonical selection |
| `qla_core/reinsurance_lookups.py` | Crosswalks, quikmstr/quikridr indexes, phase resolution |
| `qla_core/reinsurance_converter.py` | QuikRein/QuikRmst emit + QA reports |
| `plan_analysis/phase_r9_quikrein_rmst/reinsurance_runner.py` | Headless QA runner |
| `tools/validators/validate_reinsurance_phase1.py` | Automated validation |

Batch hooks: root `app.py` and `QLA_Migration/app.py` (gated, mirrors QuikLoan pattern).

---

## Known warnings / follow-up

1. **Placeholder reinsurer names** — confirm legal reinsurer identity before production load.
2. **Five policy/treaty groups** had different `AMOUNT_REINSURED` across historical effective dates; latest-date canonical row selected (not summed).
3. **Phase resolution fallback** — when BENEFIT_SEQ does not match quikridr, single-phase policies fall back to the only converted phase (0 exceptions on May 2026 extract).
4. **Retained reconciliation** — informational only; do not expect 1:1 sum match across treaty rows.
5. **Phase 2+** — QuikRcoa, billing/history, PRADJ, and production reinsurer crosswalk remain out of scope.

---

## Validation commands

```powershell
python plan_analysis/phase_r9_quikrein_rmst/reinsurance_runner.py
python tools/validators/validate_reinsurance_phase1.py
```

Artifact: `plan_analysis/phase_r9_quikrein_rmst/reinsurance_validation.json`
