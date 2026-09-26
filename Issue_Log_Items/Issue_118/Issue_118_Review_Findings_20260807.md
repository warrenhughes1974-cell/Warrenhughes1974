# Issue #118 — Independent Review Findings (2026-08-07)

**Reviewer:** Opus (second-pass review of Intake / Planning / Dependency Gate)
**Stage:** Dependency Gate re-evaluation — **no code changes**
**Probe:** `Issue_Log_Items/Issue_118/_probe_uw_collision.py` (read-only; prints only)

Purpose: verify the existing #118 documents against actual source and Output data before
Development approval, and surface anything the first pass missed.

---

## Summary

| # | Finding | Severity | New? |
|---|---------|----------|------|
| F1 | 19 forms the sheet calls **ST** have rate grids that are **100% letter `0`** (~641,600 rate rows) | **Blocker** | **New** |
| F2 | 6 forms (not just L14) ask for **more classes than rates exist** | **Blocker** | Partly new (only L14 was flagged) |
| F3 | Closed **Issue #59** validator hard-asserts `Q → NS`; Eric says `Q → PQ` | **Blocker — Closed-row conflict** | **New** |
| F4 | Two confirmed labels **overflow** `UWDESCR` C(20) | High | **New** |
| F5 | `Q` and `N` also appear on **non-L14** plans; Eric's answer was L14-scoped | High | **New** |
| F6 | 5,010 of 11,699 PPBEN benefit rows have **blank** UNDERWRITING_CLASS | High | **New** |
| F7 | 3 L10-family coverages are **not on the sheet**; a global ST default would mislabel smokers | High | **New** |
| F8 | Closed **Issue #136** PVO/UW variation flags will move when class counts change | High | **New** |
| F9 | Planning called `T`/`R` "reinsurance"; they are actually **L14 policies** | Correction | **New** |
| F10 | Spreadsheet-implied `S`→`ST` on non-L10 forms is **supported by data** | Supports plan | — |
| F11 | **T / Q / R premium rates DO exist for L14** in PAAGE/PAAGERAT (`UWCLS` column) and are being **silently dropped** today | **Blocker** | **New — corrects F2** |
| F12 | **Full-scope verification (2026-08-08):** `T`/`R` are L14-only; `Q` is L14 + 2 inherited `DISCHO29` rider rows; `T`/`Q`/`R` rates are **premium-only, L14-only**; no CV/RV/NP/NF exists for them in any family | Confirms F2/F5/F11 | **New** |

---

## F1 — 19 "Standard" forms whose rates are entirely UWCLASS `00`

The sheet lists these forms as `ST — Standard`, but every rate row for their coverage —
across **all** rate families (`Rate_Table` + `PDAGE` + `PAAGE` + `PAAGERAT`) — carries
LifePRO letter `0` (→ QLAdmin `00`, Not Applicable):

| Form | Plan | Rate rows (letter `0`, all families) |
|------|------|-------------------------------------:|
| 960 PO | 1960PO | 77,902 |
| 670 GL85-8 | 170858 | 75,793 |
| 960 OL | 1960OL | 65,225 |
| 666 WL | 1666WL | 64,544 |
| 621 END85 | 221END | 41,815 |
| 980 END65 | 280END | 41,512 |
| 960 LP65 | 196065 | 41,530 |
| 10827 CSI5 | 17CSI5 | 40,217 |
| 991 PWL | 1991PL | 33,295 |
| 665 STME95 | 2665ST | 33,167 |
| 10827 CSI3 | 17CSI3 | 26,609 |
| 619 DT | 7619DT | 24,654 |
| 622 END85 | 222END | 19,328 |
| 10827 CSI7 | 17CSI7 | 13,001 |
| SAL OL | 1SALOL | 12,111 |
| 670 GL858 | 170588 | 10,754 |
| 619 SPS PU | (none) | 10,454 |
| 647 FLP | 7647FP | 9,674 |
| SAL ML | 1SALML | 1 |

**Total ≈ 641,600 rate rows** (earlier draft said 18 forms / ~440,000 — that count used
`Rate_Table` only and missed the `UWCLS` families).

**Why it blocks.** Two mutually exclusive readings, and nobody has picked one:

- **Reading A (re-key):** these plans really become `ST`. Then every one of those ~440,000
  rate rows must change `UWCLASS` `00 → ST`, plus `QuikPlUw`, plus `quikridr.MUWCLASS`
  `00 → ST` for those policies. Large blast radius, but policy and rate stay joined.
- **Reading B (dropdown only):** the sheet is describing what the class *is called*
  when it is shown, and the conversion keeps `00` for non-varying plans. Nothing re-keys.

If we do half of A (policy `ST`, rates still `00`) the rate lookup breaks fleet-wide.
This is the single largest decision in #118 and it is not in Eric's reply.

**Ask Eric:** for products with only one underwriting class in LifePRO, should the rate
keys and policy records convert to `ST`, or stay `00 — Not Applicable` with `ST` only as
the display label?

---

## F2 — "More classes than rates" is 6 forms, not just L14

The first pass flagged only L14. Confirmed the same gap on five more:

| Form | Plan | Premium letters | Value letters (CV/RV/NP/NF) | Sheet target |
|------|------|-----------------|------------------------------|--------------|
| L14 | 1L14SC | `N Q R T` | `N` | NT, ST, PQ, PR |
| L01 10Y MA | 5L01MA | `S` | `S` | ST, PR |
| 659 CEN SR | 1659CR | `S` | `S` | ST, PR |
| 658 CEN SD | 1658CS | `S` | `S` | ST, PR |
| 659 CEN SD | 1659CS | `S` | `S` | ST, PR |
| 659 SR GD | 1659SR | `S` | `S` | ST, PR |

L14 is the special case: it has four **premium** classes but one **value** class. The other
five have a single class on both sides, so `PR` would be membership with nothing behind it.

Note: emitted `QuikGps` for `1659CS` / `1659CR` / `1658CS` / `1659SR` already shows `PR` and
`NS` rows even though their own coverage has only `S` in source — those come from existing
sibling-product rate inheritance, not from the form's own grid. Sharing rates across these
products is therefore an established pattern in the pipeline, not a new mechanism.

**Correction (see F11):** an earlier pass of this review stated that PAAGE / PAAGERAT / PDAGE
have no underwriting column. That was wrong — they carry it as **`UWCLS`**, not
`UNDERWRITING_CLASS`. PDAGE genuinely has only `0/S/P/B/N`, but PAAGE and PAAGERAT do contain
`T`, `Q`, `R` (and one `M`). F2 is therefore about **cash values / reserves / net premium**,
not about premiums.

---

## F3 — Closed-row conflict: Issue #59 validator (rule requires notifying Warren)

`tools/validators/validate_issue59_muwclass.py` asserts:

```
SAMPLE_EXPECT = {
    "011208260C": "SM",  # LifePRO S
    "011208334C": "SM",  # LifePRO S
    "011207563C": "NS",  # LifePRO Q -> NS
}
```

Eric's approved L14 map makes `Q → PQ`. Policy `011207563C` will therefore become `PQ`
and the Closed #59 validator will **FAIL** the moment #118 ships.

The `S → SM` anchors are also at risk depending on which forms those two policies sit on.

Per `.cursor/rules/completed-issues-release-guide.mdc`, this is a conflict with a Closed
row and must be approved by Warren in writing before implementation, then the guide row
and the validator updated in the same change set.

---

## F4 — Two confirmed labels do not fit the field

`QuikPlUw.UWDESCR` and `QuikUwpo.UWDESCR` are `C(20)`.

| Code | Confirmed label | Length | Result |
|------|-----------------|-------:|--------|
| BL | Blended | 7 | ok |
| NT | Standard, Non-Tobacco | **21** | **overflow** |
| PQ | Preferred, Non-Tobacco | **22** | **overflow** |
| PR | Preferred | 9 | ok |
| SM | Standard Smoker | 15 | ok |
| ST | Standard | 8 | ok |

Needs an approved 20-character form (e.g. `STANDARD NON-TOBACCO` / `PREFERRED NON-TOBAC`),
or a decision to truncate. Do not silently cut.

---

## F5 — `Q` and `N` are not L14-only

Eric's answer was scoped to L14. Actual PPBEN distribution:

| Letter | Rows | Plans carrying it |
|--------|-----:|-------------------|
| `Q` | 113 | **L14 (111)**, `DISCHO29` (2) |
| `T` | 7 | L14 only |
| `R` | 13 | L14 only |
| `N` | 108 | L14 (101), `686S 30MRG`, `687J 30MRG`, `8034 30MRG`, `8034 J30MT` |

A global `Q → PQ` / `N → NT` would push `PQ`/`NT` onto DISCHO29 and the 30MRG plans, which
are not on the sheet and have no matching rate keys. The map must be **plan-scoped**, and
we need a rule for the non-L14 `N` plans (today they are `NS`).

---

## F6 — 43% of benefit rows have no underwriting letter

PPBEN `UNDERWRITING_CLASS` distribution (11,699 rows):

```
(blank) 5010 | P 2257 | S 1924 | 0 1416 | B 850 | Q 113 | N 108 | R 13 | T 7 | junk 1
```

Blank appears on `SAL ML`, `SAL OL`, `SAL ADB`, `SAL MULTPL`, `668 SPWL`, `659 CEN II`,
and unnamed plan rows. The sheet calls several of those forms `ST`. Whether blank becomes
`ST` or stays `00` interacts directly with F1 and changes thousands of `quikridr` rows.

(There is also one junk row with `------------------` in both extracts; already excluded
today, worth an explicit guard in any new mapper.)

---

## F7 — Unlisted L10-family coverages would be mislabeled by an ST default

33 coverages have rates but no row on the sheet. Three of them are **L10 family**:

| Coverage | Letters |
|----------|---------|
| L10 CDT | B, P, S |
| L10 PREUNI | B, P, S |
| L10 SDT | B, P, S |

Under the working rule "`S → ST` unless it is an L10 form", these are L10 forms that are
*not on the sheet* — a naive "unlisted ⇒ ST" default would convert genuine L10 **smokers**
to Standard. Other unlisted coverages with real classes: `1578 FTR` (S,P), `8042 STR` (P,S),
`8043 CTR` (P,S), `686S 30MRG` (S,N), `687J 30MRG` (N), `669 SR GD` (S), the `DISCHO*` set.

Eric answered ISWL only. These still need a rule.

---

## F8 — Closed Issue #136 (PVO flags) will move

#136 is Closed on the rule "UW/Gender/Band/State checkboxes on only when that plan family
actually has varying rates," gold example `1658C1`. #118 changes the number of distinct UW
codes per plan (ISWL 3 → 2, L14 1 → 4, and under F1 Reading A many plans 1 → 1 but with a
different code). `VARIES_BY_UWCLASS` and the PVO checkboxes must be re-proven, not assumed.

Same applies to Issue A **A10** (`QuikUwpo` expected set is currently `00/NS/PR/SM/ST`) and
to `qla_core/rate_validation.py` `UWCLASS_DOMAIN`, which will hard-BLOCKER on `BL`/`NT`/`PQ`.

---

## F9 — Correction to the Planning report

Planning §10 lists "Reinsurance T/R — 20 quikridr rows outside new catalog." That is wrong.
`T` (7) and `R` (13) occur **only on plan L14** in PPBEN, and they are exactly the rows
Eric's answer covers (`T → ST`, `R → PR`). They are currently leaking into
`quikridr.MUWCLASS` as raw `T` / `R` (confirmed in current Output: `T` 7, `R` 13), which is
a live defect Eric's mapping fixes. Good news, but the risk register should say so.

---

## F10 — The `S` hypothesis is supported by data

Current Output `quikridr.MUWCLASS`: `PR` 2256, `SM` 1900, `00` 1697, `ST` 840, `NS` 221,
`R` 13, `T` 7.

Letter `S` is the only class on `L15`, `L16`, `L01 10Y MA`, `668 SPWL`, `679 CEN SD`,
`658 CEN SD`, `659 CEN SD`, `659 CEN SR`, `659 SR GD` — all of which the sheet calls
Standard. `S` co-occurs with `B` and `P` only on the L10 family, where the sheet does say
Smoker. So "`S` = Smoker on L10, Standard elsewhere" is consistent with the extract.

This does not remove the need for written confirmation, but it means a Warren waiver
("treat the spreadsheet as authority") is defensible rather than a guess.

---

## F11 — L14 premium rates exist for all four classes and are being dropped today

The rate families use two different column names for the same concept:

| File family | Column | Letters present |
|-------------|--------|-----------------|
| `Rate_Table_Extract` | `UNDERWRITING_CLASS` | `0 S P B N` |
| `PDAGE` (age/duration) | **`UWCLS`** | `0 S P B N` |
| `PAAGE` / `PAAGERAT` (attained age) | **`UWCLS`** | `0 S P B N` **+ `T` `Q` `R` `M`** |

For coverage **L14**, `PAAGERAT` `TYPE_CODE=PR` (premium rates) contains:

| Letter | PAAGERAT rows | PAAGE rows |
|--------|--------------:|-----------:|
| `N` | 82 | 2 |
| `T` | 82 | 2 |
| `Q` | 52 | 2 |
| `R` | 52 | 2 |

So L14 genuinely has **four premium classes** — exactly the four on the client sheet. What it
does **not** have is more than one set of cash values, reserves, net premium, or
non-forfeiture: `PDAGE` and `Rate_Table` carry only `N` for `CV` / `RV` / `NP` / `NF`.

**These rows are being discarded right now.** `S.map_uwclass()` returns `None` for any letter
outside `{0,N,S,P,B}`, and every loader treats `None` as `BAD_VALUE` and skips the row
(`rate_factor_loader.py:233`, `pdage_missfill.py:190`, `shared_rate_candidate_loader.py:143`,
`paagerat_pr_loader.py:119`, `paagerat_ul_coi_loader.py:152`, `rate_inheritance_loader.py:158`).
That is why emitted `QuikGps` for plan `1L14SC` shows only `NS` 82 — the 186 `T`/`Q`/`R`
premium rows never reach Output.

Also dropped by the same rule: coverage `8034 J15MT`, letter `M`, `PR`, 36 PAAGERAT rows.

**Consequence for the client question.** The L14 ask is *not* "invent three classes with no
rates." It is: four real premium classes exist; confirm that ST / PQ / PR share the single
`N` set of cash values, reserves and net premium. Much narrower, and it means Eric's letter
map is directly supported by the rate data.

**Separate surface:** `PREIN_ReinsuranceDetail` also carries `Q` 539, `N` 484, `R` 65, `S` 63,
`T` 34. Reinsurance UW handling must be decided alongside, not after.

---

## Revised blocker list

| ID | Blocker | Owner |
|----|---------|-------|
| B1b | Form-aware `S` / `B` map — confirm or waive to spreadsheet authority | **CLOSED 2026-08-07 — spreadsheet is source of truth (Clarification §5)** |
| B2 | Missing **cash value / reserve** grids for target classes on 6 forms — premiums do exist (F2, F11) | **CLOSED 2026-08-08 for L14** — map policies + emit premiums; do not invent CV; note missing cash values on final report (Clarification §7). Non-L14 sheet gaps remain under B4b. |
| **B10** | **`map_uwclass` silently drops `T`/`Q`/`R`/`M` rate rows (186 on L14, 36 on 8034 J15MT)** | **Conversion — fix with #118** |
| B4b | Unlisted plans/riders incl. 3 L10-family coverages (F5, F7) | Client / Warren |
| **B5** | **00-only forms: re-key to ST or keep 00? (F1)** | **CLOSED 2026-08-07 — keep `00`, descr Standard (Clarification §4)** |
| **B6** | **Blank UNDERWRITING_CLASS rule (F6)** | **Client / Warren** |
| **B7** | **20-char labels for NT / PQ (F4)** | **Client / Warren** |
| **B8** | **Closed #59 validator conflict — written approval (F3)** | **Warren** |
| **B9** | **Re-prove Closed #136 PVO flags + Issue A A10 after remap** | **Conversion (plan into Regression)** |

B5 is CLOSED — keep `00` with description Standard; do not re-key to ST.

---

## F12 — Full-scope verification of letters `T` / `Q` / `R` / `M` (2026-08-08)

**Probes:** `_probe_tqr_scope.py`, `_probe_tqr_followup.py` (read-only; prints only). All four
rate families and both policy extracts were scanned end to end, not sampled.

### Rate side — where the letters exist at all

| Family | Letters present | `T`/`Q`/`R` found? |
|--------|-----------------|--------------------|
| `Rate_Table_Extract_20260427` | `0 S P N B` | **No** |
| `PDAGE_..._20260731` | `0 S P N B` | **No** |
| `PAAGE_..._20260731` | `0 S P N B` + `Q R T M` | Yes — L14 only (+`M` on `8034 J15MT`) |
| `PAAGERAT_..._20260731` | `0 S P N B` + `Q R T M` | Yes — L14 only (+`M` on `8034 J15MT`) |

Every `T`/`Q`/`R` rate row is **coverage `L14`** and **`TYPE_CODE = PR` (premium) only**:

| Coverage | Letter | PAAGERAT | PAAGE | Types |
|----------|--------|---------:|------:|-------|
| L14 | `T` | 82 | 2 | `PR` |
| L14 | `Q` | 52 | 2 | `PR` |
| L14 | `R` | 52 | 2 | `PR` |
| `8034 J15MT` | `M` | 36 | 1 | `PR` |

L14 value/reserve grids remain **`N` only**: `Rate_Table` `CV` 2,836 / `NF` 2,870 / `NP` 2,886 /
`RV` 2,874; `PDAGE` `CV` 360 / `NF` 484 / `NP` 520 / `RV` 520. **No `T`/`Q`/`R` cash value,
reserve, net premium, or non-forfeiture rows exist anywhere.** Confirms OQ-B is a
share-the-`N`-grid decision, not a missing-extract problem.

### Policy side — `T` and `R` are L14-only; `Q` is not

| Letter | PPBEN rows | Plans |
|--------|-----------:|-------|
| `T` | 7 | `L14` only |
| `R` | 13 | `L14` only |
| `Q` | 113 | `L14` **111** + **`DISCHO29` 2** |
| `M` | **0** | — (rate-side only) |

**The `DISCHO29` exception (confirms F5).** Both rows are supplemental riders on policies whose
**base** is L14 and already carries `Q`:

```text
9011212151 seq1 BA plan L14      uw=Q status=A
9011212151 seq2 SU plan DISCHO29 uw=Q status=T
9011238989 seq1 BA plan L14      uw=Q status=A
9011238989 seq2 SU plan DISCHO29 uw=Q status=T
```

The rider inherits the base policy's letter; it is not a `DISCHO29` underwriting class.
`DISCHO29`'s own grid has **`N` premium only** (`Rate_Table` 10 rows, `PDAGE` 12 rows) — **no
`Q` rates**. Today both convert to plan `9DIS29` with `MUWCLASS='NS'`.

**Consequence:** `Q → PQ` must be **plan-scoped to L14**. A global `Q → PQ` would put `PQ` on
`9DIS29`, which has no `PQ` rate key — a new orphan created by the fix.

### Current Output orphans (matches the rate scope exactly)

`quikridr.MUWCLASS` = `00` 1,697 · `PR` 2,256 · `SM` 1,900 · `ST` 840 · `NS` 221 ·
**`T` 7** · **`R` 13**. Emitted rate `UWCLASS` domain is `00 / NS / SM / PR / ST` — so the
7 + 13 orphan policies have **no rate key to join** today. Examples: `9011215903C` (`R`),
`9011208194C` (`T`), both plan `1L14SC`.

### `M` on `8034 J15MT`

36 PAAGERAT + 1 PAAGE premium rows are dropped by `map_uwclass`, but **zero policies carry
`M`**, so no policy is orphaned by it. Rate-completeness item only — decide with B10.

### Bottom line

1. `T` and `R`: **L14 only**, both policy and rate side. Safe to scope to L14.
2. `Q`: **L14 plus 2 inherited `DISCHO29` rider rows** — the map must be plan-scoped.
3. Rates for `T`/`Q`/`R`: **premium only, L14 only**. No CV/RV/NP/NF exists for them anywhere,
 so OQ-B (share the `N` value grid) is the remaining decision.
