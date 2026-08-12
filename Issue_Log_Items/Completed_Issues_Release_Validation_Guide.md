# Completed Issues - Release Validation Guide

**Purpose:** Living checklist of every **closed / completed** conversion modification. Use this on every release to confirm each prior fix is still present in `QLA_Migration/Output/` and still agrees with LifePRO source extracts.

**Canonical path:** `Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md`

**Last rebuilt:** 2026-08-06 (CLNT-RJ client-ID width-12 + high-water always-on smoke).  
**Framework authority:** `AI_Agents/Framework.md` v1.5+ rule 12 / G7 — required for every agent and model (**Cursor Grok 4.5, Luna / gpt-5.6-luna-*, Composer**, overrides).  
**Always-on rule:** `.cursor/rules/completed-issues-release-guide.mdc`

---

## How to use this guide (every release)

1. Complete the **Pre-release identity check** below (git + engine + valuation date).
2. Run a **full** policy batch **and** rate emit on that same machine/commit (`QLA_VALUATION_DATE` matching the source extract). Partial rebatch is not a release.
3. Run the **release gate** (identity + package + high-risk smokes + full accountability):

```text
python tools/validators/validate_release_closed_issues.py
```

Faster smoke-only (still blocks on #106/#98/#71/#2/#59/#135/#136/#21F + CLNT-HW + CLNT-RJ width-12):

```text
python tools/validators/validate_release_closed_issues.py --smoke-only
```

Reports land in `QLA_Migration/Reports/release_closed_issues_gate_latest.md` (and `.json`).  
**Exit code 1 = RELEASE_BLOCKED — do not hand off.**

4. If the gate PASSes, confirm the handoff package is **full Output** (table CSVs + `rates/`), not `Test_Validation/` alone.
5. When closing a new issue or committing a conversion change: **add or update a row in this file in the same commit**.

---

## Luna / Composer release checklist (locked)

**Default orchestrator for every release / delivery / fix request:** **Luna** (`gpt-5.6-luna-*`).  
**All coding:** **Composer only** — Luna does **not** write or edit production code, validators, or app.py.  
**Cursor Grok (expensive):** **off-limits to Luna.** Luna must **not** call, hand off to, or ask Grok to code. Warren alone may bring Grok in.  
**Escalate to Warren (chat):** new failure class, engine vs validator unclear, Closed-row conflict (rule 13), or Composer stuck after one clear retry.

Do **not** burn an expensive model on routine cut drift when Output already matches the active source.

### Paste-ready prompt (every release)

Copy this block into the Luna chat. Replace the valuation date. Keep reinsurance on hold unless Warren says otherwise.

```text
Release proof for cut QLA_VALUATION_DATE=<YYYYMMDD>. Reinsurance is ON HOLD — ignore quikrein/quikrmst.

MODEL RULES (locked):
- You are Luna: orchestrate, classify, run gates, report. You do NOT write code.
- All code/validator/app.py edits: Composer only. Give Composer a tight task brief.
- Do NOT use Cursor Grok or any expensive coding model. Do not hand work to Grok.

1. Read Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md (this file: Precedence + high-risk smokes + this checklist).
2. Confirm git HEAD, APP_VERSION, valuation date, full Output (not Test_Validation alone).
3. Run: python tools/validators/validate_release_closed_issues.py
4. If FAIL: do NOT weaken Closed rules and do NOT force engine changes first.
   Classify each FAIL:
   A) Frozen midyear/hardcoded expected vs active-cut source/Output
      → Composer: fix validator to be source/Output-aware; keep midyear as fallback only
   B) Real Output/engine regression
      → Composer: surgical fix + bump APP_VERSION in BOTH app.py and QLA_Migration/app.py
   C) Conflict with a Closed guide row
      → STOP and notify Warren
5. Known class-A pattern (2026-08-04 cut): #59 death-claim status, #21F golden LifePRO total,
   #54 QuikLoan balance, #114 PPBENTYP path — Output was correct; validators were stuck on midyear.
6. After Composer finishes: you re-run the gate. Report PASS/FAIL only. Escalate to Warren only if class is new or B/C / Composer stuck.

Do not mark release clean on WARN-only cut items Warren waived. Do not rebuild reinsurance unless asked.
```

### First question on every new cut

If a Closed validator fails on a **named golden number**, ask first:

> Does active LifePRO source / current Output already match, and is the validator stuck on the previous cut?

If yes → **class A** (validator). If no → **class B** (engine/Output) or **C** (conflict).

### Class A fix rules (do not skip)

| Rule | Detail |
|------|--------|
| Prefer active cut | Resolve expectations from `QLA_VALUATION_DATE` + matching extract under `Source/` or `Source/LifePRO_Extracts_{date}/` |
| Prefer Output companions | e.g. #54 close to `quikloan.MLOANBAL`; #21F golden to the active 21F report `LIFEPRO_TOTAL` |
| Keep midyear fallback | Hardcoded prior-cut goldens stay as fallback only when active source/report is missing |
| Do not force wrong status/money | Never force S/DP→50 over a real T/DC→53; never force midyear balances onto a later cut |
| Twin app sync | After any `app.py` logic change: root and `QLA_Migration/app.py` must match; bump both versions |
| Guide row | If a Closed check becomes source-aware, update that issue’s “Validate from source” cell in this file |

### Model routing (locked — all requests)

| Job | Model |
|-----|--------|
| Orchestrate, batch/gate, classify A/B/C, report | **Luna** (no coding) |
| All code, validators, app.py, rate emit edits | **Composer only** |
| Cursor Grok / expensive coder | **Forbidden for Luna** — Warren only |
| New failure class, precedence fight, Composer stuck | **Warren** (may bring Grok) |

---

## Why releases miss fixes (read this)

`QLA_Migration/Output/` is **not** in git. Pulling new code does **not** put Closed fixes into the client package until you **re-emit** the owned tables on the batch machine.

| What people think shipped | What actually shipped | Typical miss |
|---------------------------|----------------------|--------------|
| Commit / `APP_VERSION` on network | Old `Output/rates/*.csv` still on disk | Rate fixes (#106 duration, #98 CV endpoint, #71 BAND, #136 PVO) absent |
| `Test_Validation/` copy for UAT | Full `Output/` never rebuilt | Client load uses stale full package |
| Policy-only rebatch | Rates not regenerated | QuikTvs/QuikCvs still old |
| Validator PASS last week | New batch overwrote Output without re-running validators | Silent regression |

**Rule:** A release is the triple of (1) git commit / engine version, (2) full Output rebuilt from that commit, (3) Closed-row validators PASS on **that** Output. Missing any one = do not hand off.

**Cut profile:** `plan_governance/config/cut_profile_uat_bat_full.json` uses `required_valuation_date=AUTO` — the cut must set `QLA_VALUATION_DATE` to a YYYYMMDD that has a matching PPOLC extract (for example `20260630` or `20260731`). It is no longer pinned to midyear only. Issue #95 validator / QuikUint loader resolve PDINTTBL from that same date (not a hardcoded 6/30 path).

---

## Pre-release identity check (required)

Run on the **same machine** that builds the client package, after `git pull`:

```text
git rev-parse --short HEAD
git status -sb
python -c "import app; print(getattr(app,'APP_VERSION', '?'))"
echo QLA_VALUATION_DATE=%QLA_VALUATION_DATE%
```

Record:

| Check | Value | Pass? |
|-------|-------|-------|
| Commit hash intended for release | | |
| Working tree clean (or only known Output artifacts) | | |
| `APP_VERSION` matches release notes | | |
| Source package folder / extract date | | |
| `QLA_VALUATION_DATE` matches that extract | | |
| Full policy batch completed after pull | | |
| Rate tables regenerated after pull (if any Closed rate issue since last package) | | |

If commit or version does not match what you told the client, **stop** — rebuild from the correct commit.

---

## High-risk smoke anchors (run every release)

These are the fixes most often “closed in code” but missing from the package. Fail any row = release blocked.

| ID | Smoke (on full Output) | Expected |
|----|------------------------|----------|
| **106** | QuikTvs RV duration identity (e.g. `170858` M/17 Dur2≈8.76; Dur83≈1000; `1659C2` M/17 SM Dur1=1 Dur83=978) | Dur N = LifePRO Dur N — **not** shifted one year early |
| **96 / L17** | `1L17SP` F/age 00 Terminal Rsvs (+ children fingerprint) | Full **annual** grid (not sparse ~38 rows). Dur0 blank/`.00` (not 56.09); Dur1≈**56.09**; Dur2≈**57.81**; Dur3≈**59.64**. Children match `1L17SP`. If active-cut PDAGE has no L17 RV, emit may use dated 7/31 PDAGE L17 with provenance — never invent factors |
| **TV0** | QuikTvs TV0 / Dur 0 | Non–single-premium: blank TV0 filled as `.00`. Single premium (e.g. L17 SP) may keep a real Dur0 value when LifePRO has one |
| **CEN NP** | `1658C1` M/37 PR QuikNps | Level net after year 1 (NP0–NP9 all **4.00** from LifePRO NP Dur1). Do not flatten control plans (`170858` / `1960OL`) |
| **98** | `17085M` M/14 QuikCvs | Year-3 `.06`; age-100 terminal `1000` |
| **71** | Rate BAND / QuikPlBd BDCODE | All `00` (match MBAND) |
| **2** | Sample MPOLICY | Source number + `C`, width 11 |
| **59** | Seven named policies MSTATUS | Six Active 22; death-claim `010521213C`/`9010521213C` = source ST map (S/DP→50; T/DC→53) |
| **135** | Sample death/surrender claims | CSO Total_Paid; MINTAMT=0 |
| **136** | `1658C1` PVO | Band/State/DV off when only defaults |
| **21F** | `quikprmh` CONV_ADJ @ 20171231 | Traditional gold `9010310404C` + ISWL gold `9010718309C` (FV deposits − history; e.g. 4243.06). Fail if ISWL missing CONV_ADJ |
| **CLNT-HW** | Last physical `quikclnt.csv` row | TEMP high-water: `MLNAME=ZZZ CONVERSION HIGHWATER`, `MCLIENTID` = max(prior)+1 left-padded to **12** (e.g. `     713664`). QLAdmin New Client must not land in low LifePRO NAME_ID ranges (12480s). Disable only with `QLA_QUIKCLNT_HIGHWATER=0` |
| **CLNT-RJ** | Client keys on Output + Append DBF | `MCLIENTID` / `MPRIMID` / `MBENFID` / related: numeric→zero decimals, trim, **left-pad spaces to width 12** (v58.81+). Not MPOLICY width-11. Left-justified / short IDs → wrong SEEK / wrong name on Use. Smoke: `python tools/validators/validate_client_id_width12.py` |

The release gate script runs these smokes plus full accountability. Any Closed ID showing **GAP** blocks the release unless Warren waives in writing.

---

## Pre-commit validation chart (overnight rates — 2026-08-04/05)

Run this **before** committing conversion/rate code. Do **not** commit until every row is PASS (or Warren waives in writing).

| # | What | Command / check | PASS looks like |
|---|------|-----------------|-----------------|
| 1 | Engine identity | `python -c "import app; print(app.APP_VERSION)"` + twin `QLA_Migration/app.py` match | Both **v58.81+** (high-water + client-ID width-12); twin hashes aligned |
| 2 | Unit tests (rates) | `python -m pytest tests/test_quiktvs_l17_rv.py tests/test_quiktvs_tv0_fill.py -q` (and `qla_core/tests` if present for #95) | PASS |
| 3 | L17 QuikTvs shape | Spot `Output/rates/QuikTvs.csv` → `1L17SP` F/00 | Dur0 ≠ 56.09; Dur1≈56.09; Dur2≈57.81; annual row count ≫ 38 (e.g. ~398/plan) |
| 4 | #96 validator | `python Issue_Log_Items/Issue_96/validate_issue96_cso_pvo.py` | PASS (annual-grid aware — **not** frozen 38) |
| 5 | #106 validator | `python Issue_Log_Items/Issue_106/validate_issue106_quiktvs_duration.py` | PASS |
| 6 | TV0 + CEN NP | Spot QuikTvs TV0 fill; `1658C1` M/37 PR QuikNps all 4.00 | PASS |
| 7 | **quikclnt high-water** | `python tools/validators/validate_quikclnt_highwater.py` | Last row = `ZZZ CONVERSION HIGHWATER` with `MCLIENTID` = max+1 (width-12). Fail if missing before commit of v58.78+ |
| 8 | **CLNT-RJ client-ID width-12** | `python tools/validators/validate_client_id_width12.py` (+ Append pack from empty template) | All non-blank client keys match `format_qladmin_mclientid` (width 12). No left-justified short IDs in CSV/DBF |
| 9 | Release smoke | `python tools/validators/validate_release_closed_issues.py --smoke-only` | RELEASE_OK / no FAIL on high-risk (includes CLNT-HW + CLNT-RJ) |
| 10 | Guide rows | This file: L17/TV0/CEN NP + **CLNT-HW / CLNT-RJ** rows present | Updated in **same commit** as code |
| 11 | Do **not** commit | `QLA_Migration/Output/**`, Desktop Append Tool, Q: DBFs, secrets | Package artifacts stay local |

**Known open (do not “fix” in commit):** `1658C1` / `658 CEN I` QuikTvs ends at **384** per LifePRO RV (6/30 and 7/31) — waiting on CSO for reserve source. Reinsurance ON HOLD. High-water client is **temporary** until Robert confirms next-ID / remumber — keep gated (`QLA_QUIKCLNT_HIGHWATER`).

---

## Release package contents (do not skip)

| Include in handoff | Do not treat as the release |
|--------------------|-----------------------------|
| Full `QLA_Migration/Output/quik*.csv` | `Output/Test_Validation/` alone |
| Full `QLA_Migration/Output/rates/` (after GENERATE RATE TABLES / rate pipeline) | Old rates left on disk from a prior week |
| Engine version + commit hash in release note | “Code was pushed” without re-batch |
| Accountability + smoke results for this Output | Last issue’s Validation report from a different Output |
| DBFs from Append Tool built from **empty template** with **client-ID width-12** (v58.81+: numeric→zero decimals, trim, left-pad to 12) **and** `quikclnt` EOF high-water (v58.78+) | Old Append that left-justifies short client IDs (wrong SEEK / wrong name on Use); seed-row stacking; or quikclnt without EOF high-water (New Client collides with 12480s) |

**Partial UAT reload** (`Test_Validation/`) is for client screen checks only. **Production / full load package** must be the full Output rebuilt on the release commit.

---

## Partial rebatch danger

| Situation | Required before release |
|-----------|-------------------------|
| Only `quikridr` / `quikmstr` re-emitted | Re-run validators for every Closed issue that owns those tables; rates unchanged only if no rate Closed issue since last rate emit |
| Rate code changed (#106, #98, #71, #77, #83, #113, #136, …) | **Must** regenerate `Output/rates/` on this commit, then smoke anchors |
| New Closed issue since last client package | Full batch + that issue’s tables present in Output + guide row PASS |
| Valuation date / source package changed | Full rebuild; do not mix old rates with new policies |

---


## Maintenance rule (locked)

| When | Action |
|------|--------|
| Issue status -> **Closed** | Add/update row: Resolution, Output tables, Source validation, Validator, Examples |
| Commit ships a conversion modification | Confirm the owning issue row exists and matches the change |
| Release / full batch | Walk this list; do not call the release clean if a Closed row fails without waiver |
| Issue reopened | Change Status to Reopened and note the gap; do not delete history |

Also required by Closure Agent G7 and `.cursor/rules/completed-issues-release-guide.mdc`.

---

## Conflict notification (required — Warren)

If any planned or in-progress change would **contradict, undo, weaken, or bypass** a Closed row in this guide (different mapping, different Output behavior, different source rule, or intentional regression of a prior fix):

1. **Stop** before implementing (or stop coding if already started).
2. **Notify Warren immediately** in chat — name the Closed issue ID(s), what the conflict is, and why the new work appears to require it.
3. Do **not** ship the conflicting change, mark the old row Closed-as-replaced, or “quietly” override the prior fix until Warren approves in writing.
4. After approval: update this guide (and the issue tracking row) to record the new rule and that Warren approved the override, with date.

This applies to every agent and model (Grok, Luna, Composer, overrides), including “small” surgical edits and rulebook-only changes.

---

## Precedence — Closed issues that share fields (do not fight)

Reviewed 2026-08-04. Most Closed rows **layer** (different scopes) or **supersede** (later replaces earlier). Use this order when two rules touch the same field.

### Documented supersessions (later wins)

| Field | Wins | Replaces / limits | Note |
|-------|------|-------------------|------|
| `MPOLICY` | **#2** (source + C, width 11) | #25 width-10 strip-9 | #25 is historical only |
| `quikplan` Band/State/DV invent flags | **#136** | #77 / #96 invent-from-presence | Keep #77 keys/defaults; keep #96 PLANVALOPT + 1SALMI wiring; keep #71 BAND=`00` |
| `quikridr.MPAR` on PUA | **#119** (always 0) | #105 copying base PAR onto PUA | #105 still sets product PAR on non-PUA |
| `quikmstr.MBANKNO` quality | **#75** (PPCOM QLA-safe) | #45 PPPAC fallback alone | Same blank-if-incomplete gate |
| QuikCvs GL85 M ages 1-17 start | **#98** (year 3 / `.06`) | #37/#41 first-duration for that band | Age-100 terminal from #41 kept |
| QuikTvs RV duration | **#106** (Dur N = Dur N) | old RV `duration-1` | CV path (#37/#98) unchanged |
| `quikridr.MPREM` blank ANN | **#88** (annualized modal / units) | #26 loading full modal on blank | Populated ANN_PPU still #26 |
| PNOTE File_Type B | **#134** -> claims memo | #21M/#50 putting B on policy memo | Policy memo still #21M/#50 for other types |
| Claims paid amount | **#135** (CSO Total_Paid, MINTAMT=0) | Item 18 DB+loan+interest as final money | See live tension below |

### Layered status / NFO (compatible if order respected)

| Field | Order (first -> last) |
|-------|------------------------|
| `quikmstr.MSTATUS` | **#13** (terminated: use CONTRACT_REASON) -> **#49** (later active phase when phase-1 display >=50) -> **#59** (7-policy allowlist; #49 excluded for death-claim policy; when source later is T/DC, #13 wins with 53 — do not force 50) -> **#121** (ART plans must not become ETI 44 from PUT LE/ET) |
| `quikmstr.MNFOPT` | **#21A** (ISWL/BF 1/2 -> APL) + **#57** (3/4/5 -> 1/2/3; no PUT overwrite). **#72 force-from-status is report-only** — do not re-enable forcing 44/45 onto MNFOPT |

### Compatible overlays (same area, different columns or scopes)

| Area | Issues | Why OK |
|------|--------|--------|
| Bill day | #21B + #47 | #47 only fills when bill day is 0 |
| Fees | #21C / #58 / #89 | Same fee fields; #89 prevents ridr-only wipe |
| Dividend | #38 + #114 + #116 + #117 (+ #21D rate) | Balance vs history vs paid-to date vs interest rate — different fields |
| Rates keys/PVO | #71 + #77 + #80 + #83 + #96 + #106 + #136 + TV0 + CEN NP | BAND=00, keys, assumptions, companions, SAL/L17 annual RV, RV Dur identity, TV0 fill, level CEN NP, real-rate-only flags |
| Memo | #21M + #50 + #134 | Emit + parse; B carve-out to claims |
| Client ID | CLNT-RJ (v58.81 width-12) + CLNT-HW (v58.78 / A12) | Width-12 left-pad keys for SEEK; TEMP EOF high-water so New Client skips low NAME_IDs |

### Live tension to watch (not two Closed guide rows, but still dangerous)

| Tension | Risk | Rule |
|---------|------|------|
| **Claims Item 18** (still in post-emit) vs **#135 Closed** | Item 18 may rewrite death amounts before #135; if #135 misses a policy, Item 18 can ship | For release proof, **#135 is money authority**. Do not treat Master Sheet “Item 18 IMPLEMENTED” as the final claims rule. |
| **#72 tracking text** vs **#57** | Old TSV/master may still say “force MNFOPT from 44/45” | Engine is report-only since v58.33. Do not reintroduce force without Warren approval. |
| **#59 vs current Output** | Release gate FAILs if six Active+LP are not 22, or death-claim status mismatches active PPOLC (S/DP→50, T/DC→53) | Re-batch or fix mapping; do not force 50 over a real T/DC termination. |

If a new issue needs a different precedence than this table: **stop and notify Warren** (Conflict notification above).

---

## Closed issues checklist

| ID | Short name | Resolution (plain language) | Output tables | Validate from source | Validator / check | Examples |
|----|------------|-----------------------------|-----------------|----------------------|-------------------|----------|
| 2 | 11 Character Policy Number | Resolution: QLAdmin policy numbers now keep the LifePRO source policy number with a trailing C and are right-justified to 11 characters (replacing the old strip-9 crosswalk and 10-character pad). Engine v58.29. UAT: Test_Validation. | all quik* MPOLICY fields | **Source:** PPOLC / PPBEN POLICY_NUMBER. **How:** Take LifePRO POLICY_NUMBER, append C, right-justify to 11 chars; compare every Output MPOLICY. No strip-9 crosswalk. | python QLA_Migration/_validate_issue2_mpolicy.py | any policy - e.g. source 9010374099 -> 9010374099C |
| 13 | Incorrect QL Status (quikmstr.MSTATUS) | When CONTRACT_CODE=T, MSTATUS follows CONTRACT_REASON not PAID_UP_TYPE; 607 policies (v57.48). | quikmstr.MSTATUS | **Source:** PPOLC CONTRACT_CODE / CONTRACT_REASON / PAID_UP_TYPE. **How:** When CONTRACT_CODE=T, MSTATUS must follow CONTRACT_REASON (not PAID_UP_TYPE). | python tools/validators/validate_issue13_mstatus.py | 010516211C->54; 011101663C->56 |
| 21A | NFO / Dividend Options | PPBENTYP cache reads BF_NON_FORFEITURE for ISWL/BF; NFO codes 1/2 -> APL (MNFOPT=1) per SME (v57.47). | quikmstr.MNFOPT / quikridr NFO | **Source:** PPBENTYP BF_NON_FORFEITURE (ISWL/BF). **How:** LifePRO NFO 1/2 map to APL (MNFOPT=1) for ISWL/BF from BF_NON_FORFEITURE cache. | python tools/validators/validate_issue21a_mnfopt.py | 010765930C; 010718309C; 010818663C |
| 21F | Premium History | **v58.79:** Conversion Adjustment `quikprmh` @ 12/31/2017 for **all** plans when LifePRO lifetime paid > history. Traditional: PPBENTYP Base+PUA+SU+SL. ISWL/UL: PPBEN `FV_GUAR_DEPOSITS`. (Was non-ISWL-only v57.73.) | quikprmh | **Source:** PACTG history + PPBENTYP (traditional) / PPBEN FV_GUAR_DEPOSITS (ISWL). **How:** Emit CONV_ADJ @ 20171231 for positive gap. Golden traditional `9010310404C`; ISWL gold `9010718309C` adj = FV deposits − history (e.g. 5492.56−1249.50=4243.06). | python tools/validators/validate_issue21f_premium_adjustment.py | CONV_ADJ rows fleet-wide; 9010310404C; 9010718309C |
| 21G | Total Premium / Cost Basis | Not required in QL - New Era; no master-field load | (none - not loaded) | **Source:** LifePRO Premiums Paid / Tax Basis. **How:** Confirm QLAdmin has no master cost-basis field load; staged report only if needed. No quikmstr field expected. | manual / New Era decision | 010448806C (LifePRO proof only) |
| 21J | Modal Premium Factors | UAT - Coverage Detail modal grid on sample policies | quikplan modal factors; Coverage Detail grid | **Source:** Client modal-factor mapping + PAC GL85 overrides. **How:** Per-plan ANNL/SEMI/QTRL/MTHD/MTHB factors; PAC GL85 quarterly/semiannual overrides. | python tools/validators/validate_issue21j_modal_factors.py | 010713704C Coverage Detail modal grid |
| 21L | Last Change Date | QLAdmin sets date on load | quikmstr last-change date | **Source:** N/A (QLAdmin sets on load). **How:** Confirm conversion does not invent Last Change Date; QLAdmin owns it on load. | manual | N/A |
| 28 | Product catalog PLAN mapping (crosswalk authority) | Resolution: PLAN codes follow Master_Crosswalk / product catalog authority (33 corrections + DISCHO25). | quikplan / quikridr MPLAN | **Source:** Master_Crosswalk + product catalog. **How:** PLAN codes follow crosswalk authority (33 corrections + DISCHO25). | python tools/validators/validate_issue28_plan_mapping.py | client UAT catalog samples |
| 36 | Modal factors on quikmstr (Names-tab Modal Premiums) | Resolution: quikmstr now receives plan-level modal factors (MSEMI/MQTRL/MMTHD/MMTHB) from quikplan, with PAC GL85 quarterly=25 and semiannual=50 overrides, so Names-tab Modal Premiums work (v57.62). | quikmstr MSEMI/MQTRL/MMTHD/MMTHB | **Source:** quikplan modal factors (+ PAC GL85). **How:** Names-tab modal factors on quikmstr match plan factors; PAC GL85 Q=25 S=50. | python tools/validators/validate_issue36_quikmstr_modal_factors.py | 010367131C |
| 37 | Age/Duration rate placement - fleet-wide | Resolution: QuikCvs age/duration placement matches LifePRO CV grids fleet-wide. | rates/QuikCvs | **Source:** Rate_Table / PAAGE CV grids. **How:** CV duration placement matches LifePRO age/duration (fleet QuikCvs). | spot-check QuikCvs + Issue_37 evidence | CV grid samples in Issue_37/ |
| 38 | Dividend Accumulations (quikdvdp.MDEPOSIT) | Resolution: Dividend deposit balances load from PPBENTYP with PACTG 641 interest YTD/date. | quikdvdp.MDEPOSIT / MINTYTD / MINTDATE | **Source:** PPBENTYP balance + PACTG 641. **How:** Dividend deposit balance from PPBENTYP; interest YTD/date from PACTG 641. | python tools/validators/validate_issue38_mdeposit.py | 010378830C; 010380808C |
| 42 | Missing rate extract rows - L01 10Y NP and L10 LP9595 | PDAGE miss-fill; 20260714 refresh. Eric 2026-07-20: 0824/GPO OL NP N/A (PPBEN Status T / Reason EX) | rates/QuikNps, QuikTvs | **Source:** PDAGE + segment resolve. **How:** PDAGE miss-fill supplies missing L01/L10 NP/RV rows; Eric N/A for terminated 0824/GPO. | Issue_42 reconcile scripts / rate counts | L01 10Y NP; L10 LP9595 (where present) |
| 44 | QuikLoan stale PLOAN latest-row (LAST_CHG_TIME sort) | Resolution: QuikLoan sorts PLOAN LAST_CHG_TIME as HHMMSS so same-day zero clears win; Phase B withdrawn | quikloan | **Source:** PLOAN LAST_CHG_DATE / LAST_CHG_TIME. **How:** Latest PLOAN row uses HHMMSS time so same-day zero clears win over stale balances. | loan row count + zero-balance samples | same-day zero-clear loan policies |
| 45 | Bank Draft Account / PPPAC fallback (quikmstr.MBANKNO) | Resolution: Bank-draft policies missing PPACH account numbers now fall back to PPPAC E_ACCOUNT_NUMBER, with ABA from routing lookup or RelationshipNameAddress, and emit MBANKNO only when both account and routing resolve. | quikmstr.MBANKNO / ABA | **Source:** PPACH account; PPPAC E_ACCOUNT_NUMBER fallback; routing lookup. **How:** Bank-draft policies: account from PPACH else PPPAC; emit MBANKNO only when account+routing both resolve. | MBANKNO populated count + samples | 010157076C; 010161748C; 010348734C |
| 47 | Bill Day zero -> Paid-To day | Resolution: When Bill Day is zero, quikmstr.MBILLDAY now uses the day from Paid-To date while non-zero Issue #21B bill days stay unchanged (v57.65). | quikmstr.MBILLDAY | **Source:** Bill day + Paid-To date (PPOLC). **How:** If Bill Day=0, MBILLDAY = day of Paid-To; non-zero #21B days unchanged. | MBILLDAY non-zero fleet check | zero bill-day policies with Paid-To day filled |
| 49 | QuikMstr Active Phase Status | QuikMstr uses first active later phase when phase 1 display >=50; phase-1 MPHSTAT unchanged (v57.71 fix); 35 policies MSTATUS 54->22 | quikmstr.MSTATUS (phase 1 MPHSTAT preserved) | **Source:** PPBEN phases STATUS_CODE. **How:** If phase-1 display >=50, MSTATUS uses first active later phase; phase-1 MPHSTAT unchanged. | python tools/validators/validate_issue49_mstatus.py | 35 policies previously 54->22 |
| 50 | Policy Notes Missing (quikmemo / PNOTE) | Resolution: QUIKMEMO fixed-width PNOTE parse + DBF MEMOKEY left-pad for Memo tab SEEK. New notes e.g. 01159D276C, 01222DCC, 01330D153C, 014075AC, 018187C, 018253C, 018910C, 01ML8522C. | quikmemo | **Source:** PNOTE_PolicyNotes_Extract (fixed-width). **How:** Fixed-width PNOTE parse; DBF MEMOKEY left-pad for Memo tab SEEK. | python tools/validators/validate_issue50_pnote_parse.py | 01159D276C; 01222DCC; 01ML8522C; 018495BC |
| 51 | Missing Interest Table (QuikAint for A60MIR / A96DAR) - Projected Values crash loop | Resolution: Added QuikAint interest-rate stubs for closed riders A60MIR and A96DAR so QLAdmin Projected Values no longer fails looking up a missing interest table. | rates/QuikAint | **Source:** Closed riders A60MIR / A96DAR (stubs). **How:** QuikAint stubs exist for A60MIR and A96DAR so Projected Values does not crash. | python tools/validators/validate_issue51_quikaint.py | 010348734C Projected Values |
| 54 | Full Loan History Load (PACTG -> QuikBenh + PLOAN seed + side-aware 0412) | Resolution: Loan History now loads from QuikBenh with a PLOAN opening-balance seed for mid-stream loans, and CREDIT-side PACTG 0412 interest offsets map to type 12 so QLAdmin Balance closes to the QuikLoan current balance. | quikbenh (+ quikloan balance close) | **Source:** PACTG loan txns + PLOAN opening seed. **How:** Loan history in QuikBenh; PLOAN seed for mid-stream; CREDIT 0412->type 12 so Balance closes to **active-cut** quikloan.MLOANBAL (not a frozen midyear 9731.08). | python tools/validators/validate_issue54_quikbenh_loan_history.py | 9010822238C Benh net = QuikLoan MLOANBAL |
| 55 | Unit Issues (tiny MUNIT floor + leading-zero emit) | Resolution: quikridr MUNIT below 0.001 floored to zero; rider decimals emit with leading digit (0.53000 not .53000); #25/#26 preserved. QLAdmin false 3000 Units = out of scope. | quikridr.MUNIT | **Source:** PPBEN NUMBER_OF_UNITS. **How:** MUNIT < 0.001 floored to 0; decimals emit with leading digit (0.53000). Trace keys are Issue #2 11-char padded 901…C (9018495BC / 9018499CC / 9018510C / 9010434419C), not legacy strip-9. | python tools/validators/validate_issue55_munit_floor.py | 9018495BC; 9018499CC; 9018510C |
| 57 | NFO Option incorrect (LP 3/4/5 + PUT overwrite) | Resolution: NFO codes 3/4/5 -> MNFOPT 1/2/3; removed PAID_UP_TYPE->MNFOPT. Eric: 010367131C, 010148272C, 010143726C (ETI); 010392763C (RPU); 011221309C (APL). | quikmstr.MNFOPT | **Source:** PPBENTYP / NFO codes (not PAID_UP_TYPE). **How:** NFO 3/4/5 -> MNFOPT 1/2/3; PAID_UP_TYPE must not overwrite MNFOPT. | python tools/validators/validate_issue57_mnfopt.py | 010367131C ETI; 010392763C RPU; 011221309C APL |
| 59 | Incorrect QL Status (quikmstr.MSTATUS) | 08/02/2026 Resolution: For six named Active/LP policies, QLAdmin now shows Active (22) instead of Lapsed (54); for the named death-claim policy, status follows current LifePRO (S/DP→50 Death Claim Pending; later T/DC→53). Examples: 01122D991C Active (22); 014FG8217C Active (22); 016FG8217C... | quikmstr.MSTATUS | **Source:** PPOLC CONTRACT_CODE / CONTRACT_REASON / PAID_UP_TYPE (named allowlist). **How:** Listed Active+LP -> 22; death-claim policy -> ST map for current cut (S/DP→50; T/DC→53 via #13 — do not force 50). | python tools/validators/validate_issue59_mstatus.py | 01122D991C; 01ML8522C Active 22; 9010521213C =50 (S/DP) or =53 (T/DC) |
| 70 | QuikPlan LOANINTX Advance/Arrears | v58.50 resolution: CSO-authoritative PCOVR.LOAN_ADV_ARREARS map (0/N->A, 1->R); full Output 137 A / 4 R; UAT passed; Validation+Regression PASS; Test_Validation/quikplan.csv published; accountability #70 IN_DATA; Output hygiene cleared. Related: Issue #32. | quikplan.LOANINTX | **Source:** PCOVR.LOAN_ADV_ARREARS. **How:** 0/N->A (Advance), 1->R (Arrears); only A or R allowed. | python QLA_Migration/_validate_issue70_loanintx.py | fleet 137 A / 4 R (verify current Output counts) |
| 71 | Rate/plan/policy BAND -> 00 | Resolution: All rate factor and rate-key BAND values (and QuikPlBd BDCODE) now emit as 00 (NOT APPLICABLE) to match quikridr MBAND=00, restoring Policy Display cash-value lookup. v57.90. Client UAT PASS. | rate BAND / QuikPlBd BDCODE; quikridr MBAND | **Source:** Rate grids BAND; policy MBAND already 00. **How:** All rate/key BAND and BDCODE = 00 to match MBAND=00 (CV lookup). | BAND domain check on rates/ + quikridr MBAND | 010718309C Policy Display CV |
| 73 | Country code must be 0000 | CLOSED. Resolution: MISSCNTRY default 0000. See Issue_73_Resolution_Summary.md. Do not reuse #73 for new work. | quikmstr.MISSCNTRY | **Source:** rulebook default (not LP country invent). **How:** MISSCNTRY = 0000 fleet-wide to match rate ISSCNTRY=0000. | MISSCNTRY all 0000 | fleet 5083 policies |
| 74 | Var DB Code (quikplan.VARDB) 4 -> 0 only | Resolution: quikplan.VARDB default 4->0 for 121 standard plans; 20 structure plans 1/2/3 unchanged. Rulebook-only. Val+Reg PASS. Test_Validation/quikplan.csv. | quikplan.VARDB | **Source:** Sync_Rulebook VARDB mapping. **How:** VARDB literal 4->0; structure codes 1/2/3 unchanged. | VARDB distribution (no 4 unless intentional) | Test_Validation/quikplan.csv |
| 75 | Bank Acct / MBANKNO QLA validation | CLOSED v58.35. Resolution: Bank-draft quikmstr.MBANKNO is rebuilt from June PPCOM routing joined by account digits, emitting only a checksum-valid 9-digit ABA and a digits-only account (source leading zeros kept). Stats: bank-draft policies 2132; populated QLA-safe 2081; still... | quikmstr.MBANKNO / ABA | **Source:** June PPCOM (checksum-valid ABA / digits-only account). **How:** Bank-draft MBANKNO rebuilt from PPCOM with valid 9-digit ABA. | python Issue_Log_Items/Issue_75/scripts/validate_issue75_mbankno.py | draft-filled bank policies |
| 76 | ETI/RPU phase-1 payup + duration for CV dates | CLOSED. G0-G6 PASS. Test_Validation/quikridr.csv. See Issue_76_Resolution_Summary.md. Client UAT: Data Admin + Rebuild CV. | quikridr phase-1 pay-up for ETI/RPU | **Source:** PPBEN status / units for ETI/RPU. **How:** ETI/RPU phase-1 MPAYUP=MPAIDTO and MLASTANN vs QLA_VALUATION_DATE; candidate count is active-cut (midyear 400 not a hard GAP; WARN if no same-cut count baseline). | python tools/validators/validate_issue76_eti_rpu_payup.py | 010407670C Rebuild CV |
| 77 | Fleet rate setup validation (PVO + default keys vs loaded rates / EX guide) | Resolution: Rate setup now ensures every plan with loaded rates has GP/DB/CV/TV/DV keys and correct Plan Values Options checkboxes, using NOT APPLICABLE defaults only when no real codes exist, without inventing factor values. | quikplan PVO + QuikPl* keys | **Source:** Loaded rate families per plan. **How:** Plans with rates have GP/DB/CV/TV/DV keys + PVO boxes; defaults only when no real codes; no invented factors. | Issue_77 validators / PVO vs key presence | plans with loaded rates in Output/rates |
| 80 | CSO Valuation Setup -> exact QuikPlCv / QuikPlTv assumptions | G5+G6 PASS; UAT: Test_Validation quikplan + QuikPlCv/Tv. Follow-ups: #81, #82. | QuikPlCv / QuikPlTv / quikplan NFOINT/INTMETHCV | **Source:** CSO Valuation_Setup workbook. **How:** Exact assumption codes from Valuation_Setup on 51 non-PUA plans; blank cells stay blank. | spot-check QuikPlCv/Tv vs Valuation_Setup | Test_Validation quikplan + QuikPlCv/Tv |
| 83 | Fleet gender companion rate keys (F/M; Values=N) | Resolution: Rate setup now emits missing Female/Male companion keys fleet-wide when a plan declares both gender members but a GP/DB/CV/TV/DV family only had one sex key, without inventing factor values (QLAdmin Values=N on companions with no factors). Val+Reg PASS; UAT pending... | QuikPlGp/Db/Cv/Tv/Dv keys | **Source:** plan gender members vs factor presence. **How:** Missing F/M companion keys emitted when plan has both genders; Values=N if no factors (no invented rates). | companion key presence for dual-gender plans | 221END |
| 88 | Blank ANN_PPU fallback loads full MODE_PREMIUM into Prem/Unit (valuation x units) | Resolution: When ANN_PREM_PER_UNIT is blank, quikridr.MPREM now uses annualized MODE_PREMIUM ÷ NUMBER_OF_UNITS instead of full modal premium; quikmstr Mode Prem unchanged. Val+Reg PASS; anchor 010779727C; reload Test_Validation/quikridr.csv. | quikridr.MPREM | **Source:** PPBEN ANN_PREM_PER_UNIT / MODE_PREMIUM / NUMBER_OF_UNITS. **How:** If ANN_PPU blank: MPREM = annualized MODE_PREMIUM ÷ units (not full modal). | python tools/validators/validate_issue26_mprem.py + #88 samples | 010779727C |
| 89 | Policy fee wipe after quikridr-only rebatch (MANNLFEE / modal fees) | Resolution: Policy fees now load from LifePRO on every quikridr emit (including ridr-only rebatches), with a fail-closed guard so a blank fleet fee wipe cannot ship again; annual and modal fees are restored on fee-bearing policies. | quikridr MANNLFEE / modal fees | **Source:** LifePRO policy fee fields. **How:** Fees reload on every quikridr emit (including ridr-only); fail-closed if blank wipe. | fee-bearing policies non-blank MANNLFEE | fee-bearing policies after ridr-only rebatch |
| 139 | Policy fees withheld for ISWL/UNKNOWN only | Resolution: Withhold policy fees for ISWL and UNKNOWN (blank phase-1 MPLAN) only; confirmed non-ISWL keep #21C/#58 fees and fee-inclusive `MMODEPREM`. Class from phase-1 `quikridr.MPLAN` via `is_iswl_mplan()` only — not `quikmstr`, not rider phases. Warren approved fleet suppress 2026-08-09; refined to mixed population 2026-08-11 (v58.91). Controlled 07/31 full-batch validation PASS: 5,083 phase-1 policies; ISWL 2,268; non-ISWL 2,815; UNKNOWN 0; 2,191 non-ISWL fee-bearing rows restored; ISWL/UNKNOWN nonzero-fee exceptions 0. **G7 accountability and Closure remain required.** | quikridr MANNLFEE, MSEMIFEE, MQTRLFEE, MMTHDFEE, MMTHBFEE; quikmstr MMODEPREM | **Source:** LifePRO `POLICY_FEE` / fee-inclusive `MODE_PREMIUM`; class from phase-1 MPLAN allowlist. **How:** ISWL/UNKNOWN five fee fields = 0 and audit accounts for their `MMODEPREM` reductions; non-ISWL fees retained where #21C/#58 apply; UNKNOWN count/list exposed (clean accept UNKNOWN=0). **Reversible:** `QLA_SUPPRESS_POLICY_FEES=0` disables Issue 139 for all. | `python tools/validators/validate_issue139_policy_fee_suppression.py`; `python tools/validators/validate_issue58_quikridr_modal_fees.py` | ISWL fees 0; non-ISWL 010367131C fees retained; UNKNOWN=0 |
| 96 | CSO val cannot use SAL MULTPL / L17 RV (PVO + QuikPl wiring) | Resolution: CSO valuation enables Plan Values Options when QuikTvs/Cvs exist for SAL MULTPL and L17 RV plans; 1SALMI shares 1SALOL M/F QuikPlCv/QuikPlTv keys. **2026-08-05:** L17 QuikTvs is the full annual LifePRO RV grid (Dur N=Dur N), not the old sparse ~38-row page-start strip; if active-cut PDAGE has no L17 RV, use dated PDAGE that contains L17 (e.g. 7/31) with provenance. | quikplan PVO; QuikPlCv/Tv for SAL/L17; rates/QuikTvs L17 family | **Source:** PDAGE RV for L17 (+ SAL OL for SAL MULTPL). **How:** PVO on when TV/CV exist; SAL QuikTvs >=500 (active-cut OK); L17 full annual grid + child fingerprint == 1L17SP; prove 1L17SP F/00 Dur1≈56.09 Dur2≈57.81. Do not invent L17 QuikCvs. Do not require frozen 38 rows. | python Issue_Log_Items/Issue_96/validate_issue96_cso_pvo.py | 1SALMI; 1SALOL; 1L17SP F/00; 10L171/10L172/117JPO/17MJPO |
| 98 | CV Endpoint Off By One (010398471C / 17085M) - #41 follow-up | Resolution: GL85 CV duration placement now starts .06 in year 3 for male issue ages 1-17 and keeps the age-100 terminal 1000 (Eric 010398471C / 17085M M age 14). Val+Reg PASS; reload Test_Validation/rates/QuikCvs.csv. | rates/QuikCvs | **Source:** GL85 / PAAGE CV grid for 17085M. **How:** Male ages 1-17: .06 starts year 3; age-100 terminal 1000 retained. | accountability #98 anchors on 17085M M/14 | 010398471C / 17085M M age 14 |
| 105 | QuikRidr MPAR for participating products | Resolution: Participating products now set QuikRidr.MPAR to True (1) from the product’s QuikPlan PAR flag by MPLAN. | quikridr.MPAR | **Source:** quikplan.PAR by MPLAN. **How:** Participating products: MPAR=1 from plan PAR flag. | python tools/validators/validate_issue105_mpar.py | participating MPLAN rows |
| 106 | RV Rates Off by One Duration (QuikTvs) | Resolution: QuikTvs RV factors now use the same duration year as LifePRO (Dur N to Dur N) instead of shifting one year early. Applies to GL85/CEN/OL fleet anchors and to L17 annual expansion (do not park LifePRO Dur1 on QuikTvs Dur0). | rates/QuikTvs | **Source:** LifePRO RV / TV duration grids (PDAGE). **How:** QuikTvs Dur N aligns to LifePRO Dur N (no off-by-one early shift). | python Issue_Log_Items/Issue_106/validate_issue106_quiktvs_duration.py | 170858 M/17 Dur2=8.76 Dur83=1000; 1659C2 SM Dur1=1 Dur83=978; 1L17SP F/00 Dur1=56.09 Dur2=57.81; follow-up #107 if LP9595 |
| 113 | Multi-source rate file load | FIXED 2026-07-25. Discover all dated files per family; merge to Staging/*_dated_merged.csv with filename YYYYMMDD newest wins on duplicate keys; older-only keys kept. Wired via plan_source_paths + rate_pipeline; PAAGE included. Smoke: PAAGE 527 / PAAGERAT 31653 / PDAGE 352395 ... | Staging/*_dated_merged.csv -> rate load | **Source:** All dated PAAGE/PAAGERAT/PDAGE under Source/. **How:** Merge all dated extracts; newest file wins duplicate keys; older-only keys kept; PAAGE wired. | merged row counts / unit tests in Issue_113 | PAAGE/PAAGERAT/PDAGE merge smoke counts |
| 114 | Total dividends credited | Fixed in v58.36. The accounting records only go back to 2018 but these policies have paid dividends for decades, so we did the same two-part approach used for premiums: load the 2,500 real dividend payments we have from 2018 on ($401,443.32), then add one catch-up line per pol... | quikbenh dividend types 1-5 (+ catch-up) | **Source:** active-cut PPBENTYP (LifePRO_Extracts_{QLA_VALUATION_DATE}/…) BA DIVIDENDS_CREDITED + PACTG. **How:** Post-2017 real dividend rows + 20171231 catch-up foot lifetime totals; do not reconcile against a stale midyear PPBENTYP on Source root. | python tools/validators/validate_issue114_dividend_history.py | 586 policies; sample 9010331768C ties to active PPBENTYP |
| 116 | Dividend interest paid-to date | Closed v58.37 after full-batch regression. Interest Paid To now comes from PACTG 0641 under both policy-number formats. Validator PASS on full Output: 59 policies updated, future paid-to with balance 15->0, balances unchanged. Accountability IN_DATA. Resolution: QuikDvdp Intere... | quikdvdp Interest Paid To | **Source:** PACTG 0641 (both policy-number formats). **How:** Interest Paid To = last 0641 credit date (not premium paid-to). If Archive BEFORE snapshot absent, validator WARNs (missing-archive) and still checks current Output has no future MINTDATE with balance — not a false GAP. | python Issue_Log_Items/Issue_116/scripts/validate_issue116.py | policies previously showing negative accrued interest |
| 117 | Dividend history missing interest and withdrawals | Closed v58.37 after full-batch regression. QuikBenh now emits ledger types 6 (interest) and 7 (withdrawals) so history foots to QuikDvdp. Validator PASS: 55/59 foot exactly; 3 pre-2018 extract gaps held by design; type 1-5 from #114 preserved. Accountability IN_DATA. Resolutio... | quikbenh types 6-7 (+ 1-5 from #114) | **Source:** PACTG dividend interest / withdrawals. **How:** History ledger includes interest (6) and withdrawals (7) so it foots to QuikDvdp balance. If Archive BEFORE snapshot absent, validator WARNs (missing-archive) and still proves type 6 + ledger footing on current Output — not a false GAP. | python Issue_Log_Items/Issue_117/scripts/validate_issue117.py | 55/59 foot exactly; document held extract gaps |
| 119 | PUA MPAR always non-participating (0) | Resolution: Paid-Up Addition coverages now set QuikRidr.MPAR to 0 (non-participating), matching QLAdmin PA-add behavior instead of copying the base coverage’s participating flag. | quikridr.MPAR on PUA | **Source:** PPBEN PUA coverages. **How:** PUA rows always MPAR=0 (do not inherit base PAR). | python tools/validators/validate_issue119_pua_mpar.py | all PUA MPHASE rows |
| 120 | Group Policies | Closed v58.48 after full batch against 20260630 source: quiklist.csv emitted with 6 active groups; full Output schema PASS; Issue 120 validator PASS; accountability #120 IN_DATA; Test_Validation published. Approved DG-QUIKMSTR-015 waiver remains for terminated-only groups 0269... | quiklist.csv | **Source:** PPOLC GROUP_NUMBER + BILLING_FORM=LST. **How:** Active list-bill groups emit in quiklist; terminated-only groups held per waiver. | python tools/validators/validate_issue120_quiklist.py | 6 active groups / 11 policies |
| 121 | ART must not emit ETI | Closed v58.44. ART-family guard suppresses PUT LE/ET on 5667AT/5646AT/57ATCR; contract status used instead. Rebatch: ART ETI 90->0; non-ART ETI preserved (120). Validator PASS; accountability IN_DATA. Resolution: Annual Renewable Term plans (5667AT, 5646AT, 57ATCR) no longer co... | quikmstr.MSTATUS on ART | **Source:** PPOLC/PPBEN for 5667AT/5646AT/57ATCR; PAID_UP_TYPE LE/ET. **How:** ART family must not emit ETI 44 from PUT LE/ET; use contract status instead. | python tools/validators/validate_issue121_art_no_eti.py | 9010764158C; 9010764248C; 9010761450C |
| 124 | ISWL zero records | Resolution: Emitted QuikIswl month-0 seed rows for all 2,268 existing ISWL base policies (MLOB=I, MLASTANNV=issue date, MDB=MUNITx1000, MMONTH=0) so QLAdmin anniversary processing can recreate monthiversary transactions after load. v58.45; validator PASS on full Output; Test_V... | QuikIswl | **Source:** ISWL base policies in quikridr/quikmstr (issue date, units). **How:** Month-0 seed: MLOB=I, MLASTANNV=issue, MDB=MUNITx1000, MMONTH=0 for all ISWL bases. | python tools/validators/validate_issue124_quikiswl.py | 2,268 ISWL base policies |
| 126 | QuikValf Issue Age vs QLAdmin | Closed 2026-08-04 after v58.66 full batch with QLA_VALUATION_DATE=20260630 aligned to 6/30 source; QuikValf issue age now matches QLAdmin at 6/30/2026 valuation. Examples: 010407670C age 14; 010374099C age 17; 010149295C age 34. Cluster #127/#129/#94. | QuikValf issue age | **Source:** PPOLC issue date + QLA_VALUATION_DATE. **How:** Issue age at valuation date matches QLAdmin (valuation date must match source package). | QuikValf age vs expected at QLA_VALUATION_DATE | 010407670C; 010374099C; 010149295C |
| 127 | QuikValf Issue Date vs QLAdmin | Closed 2026-08-04 after v58.66 full batch with QLA_VALUATION_DATE=20260630 aligned to 6/30 source; QuikValf issue date now matches QLAdmin at 6/30/2026 valuation. Examples: 9010149295C issue 1961-09-01; 9010374099C issue 1970-09-21; 9010391876C issue 1971-06-01. Cluster #126/#... | QuikValf issue date | **Source:** PPOLC ISSUE_DATE. **How:** QuikValf issue date = LifePRO issue date (valuation-aligned package). | QuikValf issue date vs PPOLC | 9010149295C; 9010374099C; 9010391876C |
| 129 | QuikVal Duration (Issue Date related) | Closed 2026-08-04 after v58.66 full batch with QLA_VALUATION_DATE=20260630 aligned to 6/30 source; QuikVal duration now matches expected policy years at 6/30/2026 valuation. Examples: 010779727C duration 40; 010407670C NFO duration 14; 010374099C NFO duration 17. Cluster #126/... | QuikVal duration | **Source:** issue date + QLA_VALUATION_DATE. **How:** Duration = policy years at valuation date; NFO duration consistent. | QuikVal duration spot-check | 010779727C dur 40; 010407670C NFO 14 |
| 133 | Conversion Rule Book delivery | Resolution: Delivered a client-readable LifePRO->QLAdmin Rule Book and Policy Crosswalk field-level Word reference for CSO/valuation, stating that conversion rules are changing. Document lists every Sync Rulebook mapping (LifePRO table/field -> QLAdmin table/field, default, how ... | (documentation deliverable) | **Source:** Sync_Rulebook_*.csv + Master_Crosswalk. **How:** Word Rule Book regenerated from current Configs; living rules remain CSVs. | rebuild docx via Issue_133/_build_rulebook_summary_docx.py | CSO_Conversion_Rule_Book_and_Policy_Crosswalk_Summary.docx |
| 134 | Death Benefit Notes | Resolution: PNOTE File_Type B death-benefit notes now load to Claims Tab memo on quikclms.MEMOTEXT and are excluded from the Policy Memo tab (quikmemo). v58.47; validator+regression PASS; QLAdmin UAT OK on 9010150740C with DBF+DBT. | quikclms.MEMOTEXT; exclude from quikmemo | **Source:** PNOTE File_Type = B. **How:** File_Type B notes -> Claims Tab memo; not on Policy Memo tab. | python QLA_Migration/_validate_issue134_claim_memos.py | 9010150740C |
| 135 | Claims Settlement vs CSO | 08/02/2026 Resolution: Death and surrender claim paid amounts now follow CSO Total_Paid with interest set to zero, missing payees filled from source accounting or policy roles, and QLAdmin claim/payee screens joining correctly. Examples: 9011156655C death four payees totaling ... | quikclms / quikclmp | **Source:** CSO Total_Paid + PACTG claim accounting + roles. **How:** Death/surrender MPAID follows CSO Total_Paid; MINTAMT=0; missing payees filled; screens join. | python Issue_Log_Items/Issue_135/tools/_validate_issue135_production.py | 9011156655C; 9011158068C |
| 136 | Plan Values Options Flags | 08/02/2026 Resolution: Plan Values Options now turn on Gender/UW/Band/State/Dividend checkboxes only when that plan family actually has varying rates; default Band 00, ALL state, and missing dividends no longer show as variances. Examples: 1658C1 Band/State/Dividend off with G... | quikplan PVO / *VARY* flags | **Source:** Actual loaded rate differentiation by family. **How:** Gender/UW/Band/State/DV flags on only when rates truly vary; Band 00 / ALL state / missing DV do not enable. | python tools/validators/validate_issue136_pvo_flags.py | 1658C1 gold; fleet BD/ST variance 0 |

---

## Release sign-off block (copy per release)

```text
Release / engine APP_VERSION: ____________
Git commit: ____________
Source package / QLA_VALUATION_DATE: ____________
Full policy batch after pull: YES / NO
Rates regenerated after pull (if needed): YES / NO / N/A
Accountability script: PASS / FAIL
High-risk smoke (#106/#98/#71/#2/#59/#135/#136/#21F + CLNT-HW): PASS / FAIL
Closed-row failures (IDs): ____________
Handoff = full Output (not Test_Validation only): YES / NO
Waivers (ID + reason + date): ____________
Signed off by: ____________  Date: ____________
```

Do **not** send the package if any of: dirty wrong commit, rates stale after a rate fix, accountability GAP, smoke FAIL, or handoff is Test_Validation-only.

---

## Related

- **Release gate script:** `tools/validators/validate_release_closed_issues.py`
- Master tracking: `Issue_Log_Items/Issue_Log_Master_Tracking_Sheet.md`
- Accountability: `tools/validators/validate_issue_log_accountability.py`
- Closure: `AI_Agents/Closure_Agent.md` (G7)
- Issue A conversion checklist: `Issue_Log_Items/Issue_A/Issue_A_Conversion_Checklist.md`

### Regenerating the seed table

```text
python Issue_Log_Items/_build_completed_issues_guide.py
python Issue_Log_Items/_generate_completed_issues_guide.py
```

After regenerate, **manually verify** new Closed rows and enrich Source/How cells before commit.
