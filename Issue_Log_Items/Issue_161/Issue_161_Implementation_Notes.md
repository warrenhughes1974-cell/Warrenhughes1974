# Issue #161 — Implementation Notes

**Issue:** #161 — POA Information Missing
**Engine:** **v59.11** (amended same day; v59.10 alone was insufficient — see Amendment below)
**Developed:** 2026-09-08
**Code + Output remap applied** (`quikclid` MRELATION remap + new `quikcloth` table build)

---

## Amendment (v59.11) — corrected root cause

v59.10 fixed `quikclid.MRELATION` from `PW` to `POFA`, which was necessary but **not sufficient**. Live UAT check (Warren, `Q:\CSO\CSO_Test_6_30_2026`) still showed an empty "Other Information" grid after the v59.10 DBF Append. Investigation found a table named **`quikcloth.dbf`** in the live QLAdmin data folder with **0 rows**, fields `MPOLICY`/`MRELATION`/`MCLOTHID`. Cross-checked against `docs/claims_conversion_reference/QLAdmin_Help.pdf`, section **7.69**:

```text
QuikCloth - Client Other Record
INDEX KEY: QuikCloth.ntx = MPOLICY + MRELATION + MCLOTHID
MPOLICY    CHARACTER  10.0  Policy number
MRELATION  CHARACTER   4.0  Relation (ASGN-assignee, LAPS-2nd lapse notice)
MCLOTHID   CHARACTER  12.0  Client ID
```

This is the table that actually backs the Names tab **Other Information** grid — not `quikclid`. It has never been emitted by this conversion. v59.11 adds it, scoped to the POFA population only (client-reported symptom).

---

## What changed

1. **`Master_Value_Translation.csv`** — LifePRO `PW` now translates to QLAdmin `POFA` (was pass-through `PW`).
2. **`policy_code_authorities.csv`** — approved `MRELATION` code is now `POFA` (Power of Attorney relationship). The old `PW` authority row is gone.
3. **`QLA_Migration/Output/quikcloth.csv`** — **new** table, built from the `quikclid` POFA population: `MPOLICY`, `MRELATION=POFA`, `MCLOTHID` (= the POA client's ID, same value/format as `quikclid.MCLIENTID`).
4. **Both `app.py` copies** — version banner **v59.11** only. No generic conversion-loop logic change; both fixes are scoped, standalone remap/build scripts (same pattern as Issue #160).
5. **Current Output** — `quikclid.MRELATION` `PW` → `POFA` on **341** rows (unchanged from v59.10); **341** new `quikcloth.csv` rows (1:1 with quikclid POFA population).
6. **Validator** — `tools/validators/validate_issue161_poa_relation_code.py` (fail-closed) extended to also gate on `quikcloth` presence, row count, and key match against `quikclid` POFA rows.

Rate tables, `quikbenf`, `quikclnt`, `quikmstr`, MPOLICY padding, and non-PW/POFA relation codes were not edited. `quikcloth` rows for other "Other Information" codes (ASGN, JINS, JOWN, LAPS) are **out of scope** — not client-reported, not built.

---

## Files touched

| File | Change |
|---|---|
| `QLA_Migration/Mapping/Master_Value_Translation.csv` | `PW,PW` → `PW,POFA` |
| `data_governance/config/policy_code_authorities.csv` | `MRELATION,PW,...` → `MRELATION,POFA,Power of Attorney relationship` |
| `app.py` | APP_VERSION v59.11 + header notes (v59.10 + v59.11) |
| `QLA_Migration/app.py` | same |
| `QLA_Migration/Output/quikclid.csv` | 341 `MRELATION` remaps (v59.10) |
| `QLA_Migration/Output/quikcloth.csv` | **new** — 341 rows built from quikclid POFA population (v59.11) |
| `QLA_Migration/Output/Test_Validation/quikclid.csv` | published copy |
| `QLA_Migration/Output/Test_Validation/quikcloth.csv` | published copy |
| `tools/validators/validate_issue161_poa_relation_code.py` | extended with quikcloth checks |
| `Issue_Log_Items/Issue_161/tools/apply_issue161_pofa_relation_remap.py` | scoped `quikclid` remap |
| `Issue_Log_Items/Issue_161/tools/build_issue161_quikcloth_poa.py` | new — builds `quikcloth.csv` |
| `QLA_Migration/Archive/issue161_pre_remap/quikclid_pre_issue161.csv` | before snapshot |

---

## Before / after (UAT)

| Policy | Client | quikclid MRELATION | quikcloth row |
|---|---|---|---|
| 9010442216C | 712072 MARLYS VANDER WAL | PW → POFA | new: MPOLICY=9010442216C, MRELATION=POFA, MCLOTHID=712072 |
| 9010451650C | 712326 TIMOTHY MOUNTAIN | PW → POFA | new: MPOLICY=9010451650C, MRELATION=POFA, MCLOTHID=712326 |
| 9011045619C | 591432 ANDREW MAZZURCO | PW → POFA | new: MPOLICY=9011045619C, MRELATION=POFA, MCLOTHID=591432 |

Fleet: **341** `quikclid` rows remapped; **341** `quikcloth` rows built (1:1 match).

---

## Not invented

`quikcloth`'s schema (`MPOLICY`+`MRELATION`+`MCLOTHID`) is a documented QLAdmin table (Help 7.69), not a new field or table we designed. We are only populating it for the exact population already proven correct in `quikclid` (POFA), not inventing scope for other relation codes.

---

## Rollback

1. Delete `QLA_Migration/Output/quikcloth.csv` (and its `Test_Validation` copy).
2. Restore `QLA_Migration/Archive/issue161_pre_remap/quikclid_pre_issue161.csv` over `QLA_Migration/Output/quikclid.csv`.
3. Revert the two mapping/authority rows.
4. Set both `APP_VERSION` values back to v59.09.

---

## Addendum (2026-09-08) — MCLOTHID left-justified in the DBF, not the CSV

`QLA_Migration/Output/quikcloth.csv` was always correctly right-justified (12-char, leading
spaces, byte-for-byte matching `quikclid.MCLIENTID`). But after a fresh **DBF Append** to
`Q:\CSO\CSO_Test_6_30_2026\quikcloth.dbf`, the live DBF's `MCLOTHID` came back
**left-justified** (e.g. `'704086      '` instead of `'      704086'`), while `quikclid.MCLIENTID`
in the same append was correctly right-justified.

**Root cause:** `C:\Users\warren\Desktop\DBF_Append_Tool\src\append_engine.py` has a
`CLIENT_ID_FIELDS` whitelist (`MCLIENTID`, `MPRIMID`, `MOWNRID`, `MPAYRID`, `MASGNID`,
`MBENPID`, `MBENCID`, `MBENFID`, `MCID`, `MOWNCID`, `MRIDRID`) that gets `rjust()`-padded on
APPEND; every other character field is left-justified per normal DBF convention. `MCLOTHID`
(new in v59.11) was not in that whitelist. Not a repo/conversion defect — no `app.py` or
Output CSV change needed.

**Fix (external tool, not this repo):** added `MCLOTHID` to `CLIENT_ID_FIELDS` in
`append_engine.py` (used by both the headless `run_append_batch.py` path and the GUI EXECUTE
path — confirmed both import the same engine). Re-ran the headless APPEND
(`python src/run_append_batch.py --csv input --templates templates --output output`), verified
`output/quikcloth.dbf` now carries `'      704086'` etc. (12 chars, right-justified, matching
`MCLIENTID`), then republished the corrected `quikcloth.dbf` to
`Q:\CSO\CSO_Test_6_30_2026\quikcloth.dbf` (341 rows, same as before — single-file overwrite,
`quikclid.dbf` on Q: untouched). Note: QLAdmin had auto-built a `QUIKCLOTH.ntx` index against
the old (bad) data at `Q:\CSO\CSO_Test_6_30_2026\`; if the Other Information grid still looks
stale after restart, that index may need to be rebuilt/deleted by QLAdmin.

**Regression guard:** `tools/validators/validate_issue161_poa_relation_code.py` now also reads
the live `append_engine.py` and FAILs if `MCLOTHID` is missing from `CLIENT_ID_FIELDS`, so this
can't silently regress on a future tool update. WARNs (does not FAIL) if run on a machine
without the Desktop tool.
