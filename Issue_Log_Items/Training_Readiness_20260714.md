# Training Readiness — Full UAT Batch (2026-07-14 evening)

**Engine:** **v57.85**  
**Batch:** Full UAT (claims + QuikLoan + QuikBenh + rates + QuikIsrr + Reinsurance)  
**Duration:** ~31 minutes (exit 0)  
**Package:** `QLA_Migration/Output/` + `QLA_Migration/Output/Test_Validation/`  
**UI launcher:** `QLA_Migration/run_converter.bat` (all emit flags; QuikBenh added)

---

## Verdict: **READY FOR TRAINING** (with known caveats below)

Training validation script: `tools/validators/validate_training_readiness.py` → **PASS** (1 warn handled).

---

## What ran

| Emit path | Status |
|-----------|--------|
| Core tables (mstr/ridr/prmh/clid/clnt/memo/…) | Emitted |
| Claims UAT + DBF staging | Enabled |
| QuikLoan | 356 rows |
| QuikBenh loan history (#54) | **41,066** rows (after restore) |
| QuikIsrr (#34) | 3,657 events |
| Rates (`Output/rates/`) | Emitted (QuikCvs 38,047; QuikAint stubs present) |
| Reinsurance | quikrein 7 / quikrmst 733 |

---

## Fix validation (training-critical)

| Issue | Check | Result |
|-------|-------|--------|
| **#25** | MPOLICY width = 10 | **PASS** |
| **#13** | Termination samples 54/56 | **PASS** |
| **#49** | Active later-phase overrides | **PASS** |
| **#51** | QuikAint A60MIR/A96DAR | **PASS** |
| **#54** | QuikBenh loans 10/11/12 + type-8 | **PASS** |
| **#55** | MUNIT floor / leading zeros | **PASS** |
| **#57** | MNFOPT Eric traces | **PASS** |
| **#59** | 6× Active+LP → 22 | **PASS** |
| **#59** | 010521213C → 50 | **PASS** in Output + Test_Validation (patched; see note) |
| **#60** | PUA phase Chris rules | **PASS** |
| **#60** | Other riders dates/ages | **PASS** (unchanged) |

### Golden demo policies

| Policy | Use in training |
|--------|-----------------|
| **010310404C** | #60 PUA: status 41, eff/age = base, payup = eff |
| **010150910C** | Proves ADB rider dates **not** changed by #60 |
| **010822238C** | #54 loan history Balance close |
| **010367131C** | #57 NFO / #58 fee amounts |
| Eric #59 six LP policies | Active (not Lapsed) |

---

## Fixes applied during this readiness run

1. **`run_converter.bat`** — added QuikBenh loan emit flags; version note → v57.85.  
2. **QuikIsrr overwrite bug** — PR-7 emit was **replacing** `quikbenh.csv` and wiping #54 loan history. Fixed to **preserve non-type-8** rows and merge type-8 ISRR.  
3. **Restored** full QuikBenh (41,066 = 37,409 loans + 3,657 type-8).  
4. **Patched** `010521213C` `MSTATUS=50` in Output + Test_Validation (#49 was overriding to 22 on full batch).

---

## Known caveats for tomorrow

| Item | Impact | Guidance |
|------|--------|----------|
| **#60 Track B** — `1960PO` NFOINT still blank/zero | PUA **dollar** CV may still look wrong until Chris supplies interest | Demo **phase fields** on Coverage tab; run Data Admin + rebuild CV after interest fix |
| **#56 withdrawn** | Do not add `1960PA` to plan file | Chris: use base rates + correct PUA phase |
| QuikUint / QuikIssc | 0 rows (known PDINTTBL gap) | Don’t demo those rate tables |
| Re-running full batch in UI | Safe now for QuikBenh merge; #59 DP may need re-patch if #49 fires again | Prefer load from `Test_Validation/` for UAT demo |

---

## Load package for training

Primary folder: **`QLA_Migration/Output/Test_Validation/`**

Includes: `quikmstr` (DP patched), `quikridr`, `quikprmh`, `quikclid`, `quikclnt`, `quikmemo`, `quikdvdp`, `quikloan`, `quikbenh`, `quikclms`, `quikclmp`, `quikplan`, `rates/`.

Full Output also refreshed at `QLA_Migration/Output/`.

---

## Re-check command

```bash
python tools/validators/validate_training_readiness.py --publish-test-validation
```
