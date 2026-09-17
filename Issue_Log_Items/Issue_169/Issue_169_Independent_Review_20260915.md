# Issue #169 — Independent review of the Discovery / Planning / Risk documents

**Reviewer:** Opus (independent re-verification)
**Date:** 2026-09-15
**Scope:** read-only. No production code, no Output changes.
**Verdict:** **Do not proceed to Development as scoped.** The facts gathered are largely accurate; the diagnosis built on them is not. The proposed fix is a no-op, and the proposed client data request should not be sent.

Script written for this review: `Issue_Log_Items/Issue_169/tools/verify_issue169_reserve_mechanism.py` (read-only).

---

## Headline

1. **The #169 documents diagnose every plan from the terminal-reserve grid (`QuikTvs`) alone. For these plans the reserve is not driven by that grid at all** — it is driven by the net valuation premium (`QuikNps` → `MTABNET`). This was already established for two of the exact plans in scope (`901ADB`, `996ADB`) by the #168 independent review on 9/14, §2.4.
2. **The Bucket B "GO for Development" fix would change nothing.** Replicating `901ADB`/`996ADB`'s `UWCLASS=00` `QuikTvs` rows onto `PR`/`ST` adds rows QLAdmin never reads. Those plans already value non-zero, and their `QuikNps` rows are *already* keyed `PR`/`ST`.
3. **The Bucket A client data request is wrong on all four plans.** For `667 ART` the data is already in the 8/31 package and the defect is on our side. For `9595WP` / `967ADB` / `9SLADB` LifePRO holds **zero** reserve — there is nothing to source.
4. **The real defect on the money item (`5667AT`, $132K) is that `QuikNps` has zero rows for the plan** while every sibling in its product family has them and the source carries the data. Fixable in code, no client ask.

---

## Part 1 — The mechanism the documents missed

`Issue_169_Discovery_Notes.md` §4 and the Planning/Risk reports reason exclusively from `QuikTvs`. Running QLAdmin's own valuation output against LifePRO's (`docs/Valuation/QuikValf.dbf`, 9/2 run, 6/30/2026 valuation; `VALXLIFE.TXT`):

| Plan | What | Rows | QLA res nz | `MTABNET` nz | LP res nz | QLA total | LP total | `res == net/2` |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `196085` | 960 LP85-M (base) | 1 | 0 | 0 | 1 | 0.00 | 1,858.42 | 0/0 |
| `7619PU` | 619 SPS PU (base) | 1 | 0 | 0 | 1 | 0.00 | 90.47 | 0/0 |
| `5667AT` | 667 ART (base) | 96 | **0** | **0** | 95 | **0.00** | **132,229.48** | 0/0 |
| `9595WP` | 1595 WP rider | 3 | 3 | 3 | **0** | 55.25 | **0.00** | 2/3 |
| `901ADB` | 1596 L01 ADB rider | 4 | **4** | 4 | 4 | **98.00** | 261.45 | **4/4** |
| `996ADB` | 1596 bare ADB rider | 1 | **1** | 1 | 1 | **25.00** | 54.00 | **1/1** |
| `967ADB` | 1596 667 ADB rider | 2 | 2 | 2 | **0** | 43.00 | **0.00** | 0/2 |
| `9SLADB` | SAL ADB rider | 5 | 5 | 5 | **0** | 3.60 | **0.00** | 5/5 |

`res == net/2` counts rows where `MRESERVE` equals `MTABNET / 2` within two cents — the signature of a net-premium-driven reserve, i.e. the TV grid is never read.

---

## Part 2 — Claim-by-claim

### 2.1 Bucket B (`901ADB`, `996ADB`) — "GO for Development, replicate `00` grid onto `PR`/`ST`" → **wrong, and it is a no-op**

The documents assert these plans are at "a guaranteed $0" because `QuikTvs` holds only `UWCLASS=00` rows while policies carry `PR`/`ST`.

They are not at $0. They value **non-zero** (98.00 and 25.00), and `MRESERVE = MTABNET / 2` holds on **4 of 4** and **1 of 1** rows. The reserve comes from the net premium. Confirming that in the current (9/13–9/14) rate package:

| Plan | `QuikNps` rows | nonzero | UW classes | `QuikTvs` UW classes |
|---|---:|---:|---|---|
| `901ADB` | 384 | 192 | **`PR`, `ST`** | `00` only |
| `996ADB` | 384 | 192 | **`PR`, `ST`** | `00` only |

The table that actually drives the reserve is **already keyed to the classes the policies carry**. The `00`-only TV grid is a red herring. #168's review reached this same conclusion by a different route (§2.4: all 31 policies across `9L01WP`, `901ADB`, `976659`, `996ADB` entirely net-premium driven, zero unexplained residual, "the `00` reserve grid is never actually read").

Their genuine gap is **magnitude, not keying**: 98.00 vs 261.45 (−63%) and 25.00 vs 54.00 (−54%). That is a net-premium / mean-reserve basis question and would survive the proposed fix untouched.

The supporting P-vs-S class-invariance analysis (3,624/3,624 identical) is methodologically sound and I reproduce no fault in it — it is simply answering a question that does not bear on the outcome.

### 2.2 Bucket A (`5667AT`) — "no source reserve data, blocked, ask CSO/New Era" → **wrong; our emit gap, data already present**

The document's evidence is that all 3,728 `RV` rows for the 667 ART family are zero across every value column. That observation is correct. The inference is not.

**An all-zero `RV` grid is how LifePRO stores this product family.** Confirmed in the current package — every attained-age term plan behaves identically:

| Plan | `QuikTvs` rows | nonzero | `QuikNps` rows | nonzero | classes |
|---|---:|---:|---:|---:|---|
| `5L0110` (L01) | 1,590 | **0** | 2,968 | 1,388 | PR/ST |
| `5L0510` (L05) | 2,279 | **0** | 2,332 | 935 | PR/ST |
| `5L075Y` (L07) | 2,385 | **0** | 2,226 | 882 | PR/ST |
| `5L01MA` | 2 | **0** | 14 | 14 | ST |
| **`5667AT` (667 ART)** | 2,020 | **0** | **0** | **0** | **none** |
| `1L14SC` (L14, permanent) | 1,328 | 1,328 | 1,312 | 1,312 | NT/PQ/PR/ST |

`667 ART` is Annual Renewable Term — same attained-age term family, and its zero TV grid is expected. What makes it the outlier is that it is the **only** member of the family with **no `QuikNps` rows at all**.

The source has the data. From `PAAGERAT_AttainedAge_Rates_Extract_20260831.csv`:

| Coverage | Type | UWCLS | Rows | Nonzero |
|---|---|---|---:|---:|
| 667 ART | NP | P | 156 | **156** |
| 667 ART | NP | S | 132 | **132** |
| 667 ART 95 | NP | P | 152 | **152** |
| 667 ART 95 | NP | S | 152 | **152** |
| 667 ART CR | NP | P | 192 | **192** |
| 667 ART CR | NP | S | 192 | **192** |

976 nonzero net-premium rows, tagged `P`/`S` (the tags that emit to `PR`/`ST`), sitting in the current extract — and none of them reach `QuikNps`. `MTABNET` is therefore zero on all 96 valued rows and the reserve is zero.

This is the same defect class as L01 (`5L0110`: 0 of 124 policies resolving, $169,718) documented in the #168 review §1.6. Together these look like one shared defect worth roughly **$300K**, with all required data already in the package. Note also that the #168 review already **retracted** the L05 data request the #169 documents propose bundling with.

### 2.3 Bucket A (`9595WP`, `967ADB`, `9SLADB`) — "blocked, needs new reserve data" → **wrong direction entirely**

For all three, **LifePRO holds zero reserve** (`LP res nz` = 0, LP total = 0.00) while QLAdmin emits a small positive amount (55.25, 43.00, 3.60). These are not missing reserves; if anything QLAdmin is over-stating. The June comparison classified every one of these rows as `VALX_ZERO (QLA has reserve, Valx none)` — the #169 Discovery Notes record that fact for 1595 and then classify the plan as data-blocked anyway.

Asking CSO/New Era for reserve factors on benefits LifePRO reserves at zero would be a bad client ask. Recommend it not be sent.

### 2.4 Bucket C (`196085`, `7619PU`) — "looks wired correctly, may already be resolved" → **facts right, conclusion wrong**

The table-level observation is accurate and I confirm it: both plans have nonzero `QuikTvs` **and** nonzero `QuikNps` at `UWCLASS=00`, matching every loaded policy's class.

But as of the most recent valuation available, both are at **`MRESERVE` = 0 with `MTABNET` = 0**, against LifePRO's 1,858.42 and 90.47. They are not working. Data present, resolution failing — the same signature as `5667AT`/L01/L05, and consistent with the age/duration alignment boundary flagged in #168 §1.4. These belong in the same investigation, not parked pending a fresh extract.

**The `7619PU` blank-`RSVMETH` line of inquiry in the #169 documents is correct, and policy-level detail now promotes it to the leading candidate.** Its one valued policy (`9011216835C`, age 34, duration 29) has a `QuikNps` value of 59.30 and a `QuikTvs` value of 12.12 at its *exact* age / duration / gender / class cell — the grid resolves — and the valuation still returns `MTABNET` = 0. So the block sits downstream of the grid, and `7619PU`'s `QuikPlTv` rows carry **blank `MORT`, `RSVINT`, `RSVMETH`, `INTMETHTV`, `STOREMEANS`, `CALCMIDS`** while its sibling `7619DT` carries `A1` / `C` / `1`. Credit where due: the #169 documents identified this and I initially rated it secondary. See Part 5.

### 2.5 `967ADB` crosswalk finding — **real, correctly sourced, but not a reserve defect**

The `CROSSWALK_DIVERGENT` status in `plan_governance/product_catalog_crosswalk.csv` and the open `FORM_CONFLICT_REVIEW` / `PASSTHROUGH_LIFEPRO_ID` rows in `plan_governance/manifests/unresolved_product_mapping_manifest.csv` for LifePRO coverage `1596 667` are genuine and worth raising on their own merits. But since LifePRO holds zero reserve for `967ADB`, resolving that mapping will not produce a reserve, and it is not a blocker for this issue.

### 2.6 What holds up

- The form-number → plan-code mapping is correct, including reading "1596 LO1" as `1596 L01` (`901ADB`, whose own description reads "Accidental DB Rider - L01 10Y LT").
- Reading the **8/31** `QLA_Migration/Source/` extracts rather than the superseded April `Rate_Table_Extract_20260427.csv` — the trap that produced #168's original false "no L05 data" reading. Correctly avoided.
- `CSO_Valuation_Setup.csv` genuinely covers no rider plans. True, though not the driver.
- Every raw count and table-presence fact I re-ran reproduced. The gap is interpretive, not clerical.

---

## Part 3 — Corrected position

| Plan | #169 position | Corrected position |
|---|---|---|
| `5667AT` (667 ART) | No source data; blocked; ask CSO/New Era | **`QuikNps` emits zero rows** though 976 nonzero NP rows exist in the 8/31 source. Our defect, data present — PSUBSSEG emit entry **E4 dropped** from the delivered scope (Part 4.1). Related to L01's $169,718 in that both end at `MTABNET`=0, but a different mechanism: L01 *has* NP rows that fail to resolve, `5667AT` has none |
| `901ADB`, `996ADB` | GO for Development: replicate TV `00` → `PR`/`ST` | **No-op** — TV grid never read; `QuikNps` already keyed `PR`/`ST`. Real gap is reserve magnitude (−63% / −54%) |
| `9595WP`, `967ADB`, `9SLADB` | Blocked; needs new reserve data | **LifePRO holds $0.** Nothing missing; QLAdmin slightly over-states. No client ask |
| `196085`, `7619PU` | Looks wired; may already be resolved | **Zero in the latest valuation** with all data present. Same resolution-failure family as `5667AT`/L01/L05 |
| `967ADB` crosswalk gap | Blocker for the fix | Real governance item, but not a reserve defect and not a blocker here |
| Overall shape | 3 buckets: no-data / key-mismatch / already-fine | **One dominant defect**: net-premium resolution on the attained-age term family, plus a magnitude question on the ADB riders. No client data request |

## Part 4 — Root cause, traced

### 4.1 `5667AT` — a planned emit that was scoped, source-verified, and then dropped

`667 ART`'s net premiums live in the **attained-age** extract, not the age/duration one. `PDAGE_20260831` holds only `667 ART 95` `RV` rows (3,728, every value zero, classes `0`/`P`/`S`) and **no `NP` rows for the family at all**. The `NP` data is entirely in `PAAGERAT_20260831`.

Nothing reads it. `qla_core/paagerat_pr_loader.py` exposes a generic `stream_paagerat_rows(type_code=...)` with exactly two thin wrappers — `PR` and `NF`. There is no `NP` wrapper, and no `paagerat_np_loader` module. Across the whole package only **8** coverages carry `NP` in PAAGERAT (1,307 rows) against 77 coverages / 152,165 rows in PDAGE, so the attained-age net-premium leg is a genuine edge case that was never wired.

This was already known. From `Issue_Log_Items/PSUBSSEG_Rate_Substitution/`:

- **Discovery, 2026-08-29:** "`5667AT` (667 ART) | RV/NP source rates exist (PAAGE/PDAGE) but plan emits **no** QuikTvs/QuikNps rows — 195 policies (95 active). … **reserves are not zero, they were never emitted.**"
- **Planning, emit plan Tranche 1:** `| E4 | 5667AT | QuikNps | 19000101 | 667 ART (PAAGERAT) | ~288 src rows |`
- **Dependency Gate:** "`667 ART` NP (288 PAAGERAT)" — **Met**.
- **Delivered scope manifest** (`psubsseg_substitution_scope.csv`, 50 rows): the only `5667AT` row is `667 ART,5667AT,RV,19950101,667 ART 95,EXTRACT,…,PDAGE` — the all-zero RV grid. **E4 is absent.** All 25 delivered `NP` entries source from `PDAGE`; not one sources from `PAAGERAT`.

So **E4 was dropped from the shipped manifest** — consistent with the PAAGERAT `NP` loader leg it depended on never being built. Open item **OI-2** correctly waived `5667AT`'s *RV* grid ("LifePRO 95-era RV genuinely zero"); that waiver appears to have carried the *NP* leg out with it, and the NP leg is the one that actually produces the reserve. Jill's $132,229 is the consequence.

### 4.2 `7619PU` and the ADB riders — open item OI-1, unresolved

`CSO_Valuation_Setup.csv` (`plan_analysis/source_data/rates/`, 52 rows) is the authority for `QuikPlTv` `MORT` / `RSVINT` / `RSVMETH`. Present-vs-absent maps exactly onto populated-vs-blank in Output:

| Plan | In CSO setup | `QuikPlTv` assumptions |
|---|---|---|
| `196085` | yes — `960 LP85-M` | `O1` / `2` / `3` |
| `5667AT` | yes — `667 ART` | `A1` / `G` / `3` |
| `7619DT` | yes — `619 DT` | `A1` / `C` / `1` |
| `7619PU`, `901ADB`, `996ADB`, `967ADB`, `9595WP`, `9SLADB` | **absent** | **all blank** |

PSUBSSEG open item **OI-1** anticipated this ("19950101 `QuikPlTv` basis fields … if the crosswalk lacks the 95 basis, copy the existing band's fields and flag") but its fallback cannot fire for `7619PU`, which has no row in the setup file to copy from. It shipped blank and was never resolved.

This also explains the ADB magnitude gaps without invoking class keys: with no `RSVMETH`, `901ADB`/`996ADB` can only produce the net-premium half-reserve (`MTABNET / 2`), which is exactly what they emit and exactly why they land low against LifePRO.

### 4.3 `196085` — tabular durations run out

Its one valued policy is at **duration 57**; `PDAGE` carries the entire `960` family at **durations 1–12 only** (`960 LP65`, `960 LP85-8`, `960 OL`, `960 PO`). The emitted grid's last nonzero duration is 7 (`QuikNps`) / 9 (`QuikTvs`). `196085` is `RSVMETH=3`, a formula plan, so LifePRO computes beyond the tabular range. One policy, $1,858.42 — a QLAdmin-side question, not a conversion gap.

## Part 5 — Caveat

`docs/Valuation/QuikValf.dbf` is the **9/2** run; `Output/rates/` was regenerated **9/13–9/14**. The mechanism conclusions rest on the current rate tables and hold, but the dollar figures describe the 9/2 state. A fresh QuikValf against the current package should be obtained before any figure here is quoted to the client — the same caveat recorded at #168 §1.7.
