"""Generate Completed_Issues_Release_Validation_Guide.md from tracking artifacts."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IL = ROOT / "Issue_Log_Items"
OUT = IL / "Completed_Issues_Release_Validation_Guide.md"
INV = IL / "_tmp_closed_inventory.json"

# Manual enrichment: source extracts + how to prove the fix still holds.
# Keyed by issue id without leading #.
SOURCE_VALIDATE: dict[str, dict[str, str]] = {
    "2": {
        "tables": "all quik* MPOLICY fields",
        "source": "PPOLC / PPBEN POLICY_NUMBER",
        "how": "Take LifePRO POLICY_NUMBER, append C, right-justify to 11 chars; compare every Output MPOLICY. No strip-9 crosswalk.",
        "validator": "python QLA_Migration/_validate_issue2_mpolicy.py",
        "examples": "any policy — e.g. source 9010374099 → 9010374099C",
    },
    "13": {
        "tables": "quikmstr.MSTATUS",
        "source": "PPOLC CONTRACT_CODE / CONTRACT_REASON / PAID_UP_TYPE",
        "how": "When CONTRACT_CODE=T, MSTATUS must follow CONTRACT_REASON (not PAID_UP_TYPE).",
        "validator": "python tools/validators/validate_issue13_mstatus.py",
        "examples": "010516211C→54; 011101663C→56",
    },
    "21A": {
        "tables": "quikmstr.MNFOPT / quikridr NFO",
        "source": "PPBENTYP BF_NON_FORFEITURE (ISWL/BF)",
        "how": "LifePRO NFO 1/2 map to APL (MNFOPT=1) for ISWL/BF from BF_NON_FORFEITURE cache.",
        "validator": "python tools/validators/validate_issue21a_mnfopt.py",
        "examples": "010765930C; 010718309C; 010818663C",
    },
    "21F": {
        "tables": "quikprmh",
        "source": "PACTG premium history + PPBEN Base/PUA/SU/SL totals",
        "how": "Non-ISWL: when LifePRO Base+PUA+SU+SL > loaded history, emit Conversion Adjustment @ 20171231. ISWL excluded.",
        "validator": "python tools/validators/validate_issue21f_premium_adjustment.py",
        "examples": "non-ISWL policies with CONV_ADJ-like quikprmh rows",
    },
    "21G": {
        "tables": "(none — not loaded)",
        "source": "LifePRO Premiums Paid / Tax Basis",
        "how": "Confirm QLAdmin has no master cost-basis field load; staged report only if needed. No quikmstr field expected.",
        "validator": "manual / New Era decision",
        "examples": "010448806C (LifePRO proof only)",
    },
    "21J": {
        "tables": "quikplan modal factors; Coverage Detail grid",
        "source": "Client modal-factor mapping + PAC GL85 overrides",
        "how": "Per-plan ANNL/SEMI/QTRL/MTHD/MTHB factors; PAC GL85 quarterly/semiannual overrides.",
        "validator": "python tools/validators/validate_issue21j_modal_factors.py",
        "examples": "010713704C Coverage Detail modal grid",
    },
    "21L": {
        "tables": "quikmstr last-change date",
        "source": "N/A (QLAdmin sets on load)",
        "how": "Confirm conversion does not invent Last Change Date; QLAdmin owns it on load.",
        "validator": "manual",
        "examples": "N/A",
    },
    "28": {
        "tables": "quikplan / quikridr MPLAN",
        "source": "Master_Crosswalk + product catalog",
        "how": "PLAN codes follow crosswalk authority (33 corrections + DISCHO25).",
        "validator": "python tools/validators/validate_issue28_plan_mapping.py",
        "examples": "client UAT catalog samples",
    },
    "36": {
        "tables": "quikmstr MSEMI/MQTRL/MMTHD/MMTHB",
        "source": "quikplan modal factors (+ PAC GL85)",
        "how": "Names-tab modal factors on quikmstr match plan factors; PAC GL85 Q=25 S=50.",
        "validator": "python tools/validators/validate_issue36_quikmstr_modal_factors.py",
        "examples": "010367131C",
    },
    "37": {
        "tables": "rates/QuikCvs",
        "source": "Rate_Table / PAAGE CV grids",
        "how": "CV duration placement matches LifePRO age/duration (fleet QuikCvs).",
        "validator": "spot-check QuikCvs + Issue_37 evidence",
        "examples": "CV grid samples in Issue_37/",
    },
    "38": {
        "tables": "quikdvdp.MDEPOSIT / MINTYTD / MINTDATE",
        "source": "PPBENTYP balance + PACTG 641",
        "how": "Dividend deposit balance from PPBENTYP; interest YTD/date from PACTG 641.",
        "validator": "python tools/validators/validate_issue38_mdeposit.py",
        "examples": "010378830C; 010380808C",
    },
    "42": {
        "tables": "rates/QuikNps, QuikTvs",
        "source": "PDAGE + segment resolve",
        "how": "PDAGE miss-fill supplies missing L01/L10 NP/RV rows; Eric N/A for terminated 0824/GPO.",
        "validator": "Issue_42 reconcile scripts / rate counts",
        "examples": "L01 10Y NP; L10 LP9595 (where present)",
    },
    "44": {
        "tables": "quikloan",
        "source": "PLOAN LAST_CHG_DATE / LAST_CHG_TIME",
        "how": "Latest PLOAN row uses HHMMSS time so same-day zero clears win over stale balances.",
        "validator": "loan row count + zero-balance samples",
        "examples": "same-day zero-clear loan policies",
    },
    "45": {
        "tables": "quikmstr.MBANKNO / ABA",
        "source": "PPACH account; PPPAC E_ACCOUNT_NUMBER fallback; routing lookup",
        "how": "Bank-draft policies: account from PPACH else PPPAC; emit MBANKNO only when account+routing both resolve.",
        "validator": "MBANKNO populated count + samples",
        "examples": "010157076C; 010161748C; 010348734C",
    },
    "47": {
        "tables": "quikmstr.MBILLDAY",
        "source": "Bill day + Paid-To date (PPOLC)",
        "how": "If Bill Day=0, MBILLDAY = day of Paid-To; non-zero #21B days unchanged.",
        "validator": "MBILLDAY non-zero fleet check",
        "examples": "zero bill-day policies with Paid-To day filled",
    },
    "49": {
        "tables": "quikmstr.MSTATUS (phase 1 MPHSTAT preserved)",
        "source": "PPBEN phases STATUS_CODE",
        "how": "If phase-1 display >=50, MSTATUS uses first active later phase; phase-1 MPHSTAT unchanged.",
        "validator": "python tools/validators/validate_issue49_mstatus.py",
        "examples": "35 policies previously 54→22",
    },
    "50": {
        "tables": "quikmemo",
        "source": "PNOTE_PolicyNotes_Extract (fixed-width)",
        "how": "Fixed-width PNOTE parse; DBF MEMOKEY left-pad for Memo tab SEEK.",
        "validator": "python tools/validators/validate_issue50_pnote_parse.py",
        "examples": "01159D276C; 01222DCC; 01ML8522C; 018495BC",
    },
    "51": {
        "tables": "rates/QuikAint",
        "source": "Closed riders A60MIR / A96DAR (stubs)",
        "how": "QuikAint stubs exist for A60MIR and A96DAR so Projected Values does not crash.",
        "validator": "python tools/validators/validate_issue51_quikaint.py",
        "examples": "010348734C Projected Values",
    },
    "54": {
        "tables": "quikbenh (+ quikloan balance close)",
        "source": "PACTG loan txns + PLOAN opening seed",
        "how": "Loan history in QuikBenh; PLOAN seed for mid-stream; CREDIT 0412→type 12 so Balance closes.",
        "validator": "python tools/validators/validate_issue54_quikbenh_loan_history.py",
        "examples": "loan history Balance vs QuikLoan",
    },
    "55": {
        "tables": "quikridr.MUNIT",
        "source": "PPBEN NUMBER_OF_UNITS",
        "how": "MUNIT < 0.001 floored to 0; decimals emit with leading digit (0.53000).",
        "validator": "python tools/validators/validate_issue55_munit_floor.py",
        "examples": "sub-floor unit riders",
    },
    "57": {
        "tables": "quikmstr.MNFOPT",
        "source": "PPBENTYP / NFO codes (not PAID_UP_TYPE)",
        "how": "NFO 3/4/5 → MNFOPT 1/2/3; PAID_UP_TYPE must not overwrite MNFOPT.",
        "validator": "python tools/validators/validate_issue57_mnfopt.py",
        "examples": "010367131C ETI; 010392763C RPU; 011221309C APL",
    },
    "59": {
        "tables": "quikmstr.MSTATUS",
        "source": "PPOLC CONTRACT_CODE / CONTRACT_REASON / PAID_UP_TYPE (named allowlist)",
        "how": "Only listed Active+LP → 22 (not 54); S+DP → 50 (not Paid Up).",
        "validator": "python tools/validators/validate_issue59_mstatus.py",
        "examples": "01122D991C; 01ML8522C Active 22; 010521213C status 50",
    },
    "70": {
        "tables": "quikplan.LOANINTX",
        "source": "PCOVR.LOAN_ADV_ARREARS",
        "how": "0/N→A (Advance), 1→R (Arrears); only A or R allowed.",
        "validator": "python QLA_Migration/_validate_issue70_loanintx.py",
        "examples": "fleet 137 A / 4 R (verify current Output counts)",
    },
    "71": {
        "tables": "rate BAND / QuikPlBd BDCODE; quikridr MBAND",
        "source": "Rate grids BAND; policy MBAND already 00",
        "how": "All rate/key BAND and BDCODE = 00 to match MBAND=00 (CV lookup).",
        "validator": "BAND domain check on rates/ + quikridr MBAND",
        "examples": "010718309C Policy Display CV",
    },
    "73": {
        "tables": "quikmstr.MISSCNTRY",
        "source": "rulebook default (not LP country invent)",
        "how": "MISSCNTRY = 0000 fleet-wide to match rate ISSCNTRY=0000.",
        "validator": "MISSCNTRY all 0000",
        "examples": "fleet 5083 policies",
    },
    "74": {
        "tables": "quikplan.VARDB",
        "source": "Sync_Rulebook VARDB mapping",
        "how": "VARDB literal 4→0; structure codes 1/2/3 unchanged.",
        "validator": "VARDB distribution (no 4 unless intentional)",
        "examples": "Test_Validation/quikplan.csv",
    },
    "75": {
        "tables": "quikmstr.MBANKNO / ABA",
        "source": "June PPCOM (checksum-valid ABA / digits-only account)",
        "how": "Bank-draft MBANKNO rebuilt from PPCOM with valid 9-digit ABA.",
        "validator": "python Issue_Log_Items/Issue_75/scripts/validate_issue75_mbankno.py",
        "examples": "draft-filled bank policies",
    },
    "76": {
        "tables": "quikridr phase-1 pay-up for ETI/RPU",
        "source": "PPBEN status / units for ETI/RPU",
        "how": "ETI/RPU phase-1 adjusted so Rebuild CV works; non-ETI/RPU unchanged.",
        "validator": "python tools/validators/validate_issue76_eti_rpu_payup.py",
        "examples": "010407670C Rebuild CV",
    },
    "77": {
        "tables": "quikplan PVO + QuikPl* keys",
        "source": "Loaded rate families per plan",
        "how": "Plans with rates have GP/DB/CV/TV/DV keys + PVO boxes; defaults only when no real codes; no invented factors.",
        "validator": "Issue_77 validators / PVO vs key presence",
        "examples": "plans with loaded rates in Output/rates",
    },
    "80": {
        "tables": "QuikPlCv / QuikPlTv / quikplan NFOINT/INTMETHCV",
        "source": "CSO Valuation_Setup workbook",
        "how": "Exact assumption codes from Valuation_Setup on 51 non-PUA plans; blank cells stay blank.",
        "validator": "spot-check QuikPlCv/Tv vs Valuation_Setup",
        "examples": "Test_Validation quikplan + QuikPlCv/Tv",
    },
    "83": {
        "tables": "QuikPlGp/Db/Cv/Tv/Dv keys",
        "source": "plan gender members vs factor presence",
        "how": "Missing F/M companion keys emitted when plan has both genders; Values=N if no factors (no invented rates).",
        "validator": "companion key presence for dual-gender plans",
        "examples": "221END",
    },
    "88": {
        "tables": "quikridr.MPREM",
        "source": "PPBEN ANN_PREM_PER_UNIT / MODE_PREMIUM / NUMBER_OF_UNITS",
        "how": "If ANN_PPU blank: MPREM = annualized MODE_PREMIUM ÷ units (not full modal).",
        "validator": "python tools/validators/validate_issue26_mprem.py + #88 samples",
        "examples": "010779727C",
    },
    "89": {
        "tables": "quikridr MANNLFEE / modal fees",
        "source": "LifePRO policy fee fields",
        "how": "Fees reload on every quikridr emit (including ridr-only); fail-closed if blank wipe.",
        "validator": "fee-bearing policies non-blank MANNLFEE",
        "examples": "fee-bearing policies after ridr-only rebatch",
    },
    "96": {
        "tables": "quikplan PVO; QuikPlCv/Tv for SAL/L17",
        "source": "QuikTvs/Cvs presence for SAL MULTPL / L17 RV",
        "how": "PVO on when TV/CV exist for SAL MULTPL & L17 RV; 1SALMI shares 1SALOL M/F keys.",
        "validator": "PVO + QuikPl* for 1SALOL/1SALMI/L17",
        "examples": "1SALMI; 1SALOL; L17 RV plans",
    },
    "98": {
        "tables": "rates/QuikCvs",
        "source": "GL85 / PAAGE CV grid for 17085M",
        "how": "Male ages 1–17: .06 starts year 3; age-100 terminal 1000 retained.",
        "validator": "accountability #98 anchors on 17085M M/14",
        "examples": "010398471C / 17085M M age 14",
    },
    "105": {
        "tables": "quikridr.MPAR",
        "source": "quikplan.PAR by MPLAN",
        "how": "Participating products: MPAR=1 from plan PAR flag.",
        "validator": "python tools/validators/validate_issue105_mpar.py",
        "examples": "participating MPLAN rows",
    },
    "106": {
        "tables": "rates/QuikTvs",
        "source": "LifePRO RV / TV duration grids",
        "how": "QuikTvs Dur N aligns to LifePRO Dur N (no off-by-one early shift).",
        "validator": "Issue_106 validation + QuikTvs spot-check",
        "examples": "RV sample durations; follow-up #107 if LP9595",
    },
    "113": {
        "tables": "Staging/*_dated_merged.csv → rate load",
        "source": "All dated PAAGE/PAAGERAT/PDAGE under Source/",
        "how": "Merge all dated extracts; newest file wins duplicate keys; older-only keys kept; PAAGE wired.",
        "validator": "merged row counts / unit tests in Issue_113",
        "examples": "PAAGE/PAAGERAT/PDAGE merge smoke counts",
    },
    "114": {
        "tables": "quikbenh dividend types 1–5 (+ catch-up)",
        "source": "PACTG dividends + lifetime dividend totals",
        "how": "Post-2017 real dividend rows + 20171231 catch-up to foot LifePRO lifetime totals (held exceptions documented).",
        "validator": "python tools/validators/validate_issue114_dividend_history.py",
        "examples": "586 policies with dividend history",
    },
    "116": {
        "tables": "quikdvdp Interest Paid To",
        "source": "PACTG 0641 (both policy-number formats)",
        "how": "Interest Paid To = last 0641 credit date (not premium paid-to).",
        "validator": "python Issue_Log_Items/Issue_116/scripts/validate_issue116.py",
        "examples": "policies previously showing negative accrued interest",
    },
    "117": {
        "tables": "quikbenh types 6–7 (+ 1–5 from #114)",
        "source": "PACTG dividend interest / withdrawals",
        "how": "History ledger includes interest (6) and withdrawals (7) so it foots to QuikDvdp balance.",
        "validator": "python Issue_Log_Items/Issue_117/scripts/validate_issue117.py",
        "examples": "55/59 foot exactly; document held extract gaps",
    },
    "119": {
        "tables": "quikridr.MPAR on PUA",
        "source": "PPBEN PUA coverages",
        "how": "PUA rows always MPAR=0 (do not inherit base PAR).",
        "validator": "python tools/validators/validate_issue119_pua_mpar.py",
        "examples": "all PUA MPHASE rows",
    },
    "120": {
        "tables": "quiklist.csv",
        "source": "PPOLC GROUP_NUMBER + BILLING_FORM=LST",
        "how": "Active list-bill groups emit in quiklist; terminated-only groups held per waiver.",
        "validator": "python tools/validators/validate_issue120_quiklist.py",
        "examples": "6 active groups / 11 policies",
    },
    "121": {
        "tables": "quikmstr.MSTATUS on ART",
        "source": "PPOLC/PPBEN for 5667AT/5646AT/57ATCR; PAID_UP_TYPE LE/ET",
        "how": "ART family must not emit ETI 44 from PUT LE/ET; use contract status instead.",
        "validator": "python tools/validators/validate_issue121_art_no_eti.py",
        "examples": "9010764158C; 9010764248C; 9010761450C",
    },
    "124": {
        "tables": "QuikIswl",
        "source": "ISWL base policies in quikridr/quikmstr (issue date, units)",
        "how": "Month-0 seed: MLOB=I, MLASTANNV=issue, MDB=MUNIT×1000, MMONTH=0 for all ISWL bases.",
        "validator": "python tools/validators/validate_issue124_quikiswl.py",
        "examples": "2,268 ISWL base policies",
    },
    "126": {
        "tables": "QuikValf issue age",
        "source": "PPOLC issue date + QLA_VALUATION_DATE",
        "how": "Issue age at valuation date matches QLAdmin (valuation date must match source package).",
        "validator": "QuikValf age vs expected at QLA_VALUATION_DATE",
        "examples": "010407670C; 010374099C; 010149295C",
    },
    "127": {
        "tables": "QuikValf issue date",
        "source": "PPOLC ISSUE_DATE",
        "how": "QuikValf issue date = LifePRO issue date (valuation-aligned package).",
        "validator": "QuikValf issue date vs PPOLC",
        "examples": "9010149295C; 9010374099C; 9010391876C",
    },
    "129": {
        "tables": "QuikVal duration",
        "source": "issue date + QLA_VALUATION_DATE",
        "how": "Duration = policy years at valuation date; NFO duration consistent.",
        "validator": "QuikVal duration spot-check",
        "examples": "010779727C dur 40; 010407670C NFO 14",
    },
    "133": {
        "tables": "(documentation deliverable)",
        "source": "Sync_Rulebook_*.csv + Master_Crosswalk",
        "how": "Word Rule Book regenerated from current Configs; living rules remain CSVs.",
        "validator": "rebuild docx via Issue_133/_build_rulebook_summary_docx.py",
        "examples": "CSO_Conversion_Rule_Book_and_Policy_Crosswalk_Summary.docx",
    },
    "134": {
        "tables": "quikclms.MEMOTEXT; exclude from quikmemo",
        "source": "PNOTE File_Type = B",
        "how": "File_Type B notes → Claims Tab memo; not on Policy Memo tab.",
        "validator": "python QLA_Migration/_validate_issue134_claim_memos.py",
        "examples": "9010150740C",
    },
    "135": {
        "tables": "quikclms / quikclmp",
        "source": "CSO Total_Paid + PACTG claim accounting + roles",
        "how": "Death/surrender MPAID follows CSO Total_Paid; MINTAMT=0; missing payees filled; screens join.",
        "validator": "python Issue_Log_Items/Issue_135/tools/_validate_issue135_production.py",
        "examples": "9011156655C; 9011158068C",
    },
    "136": {
        "tables": "quikplan PVO / *VARY* flags",
        "source": "Actual loaded rate differentiation by family",
        "how": "Gender/UW/Band/State/DV flags on only when rates truly vary; Band 00 / ALL state / missing DV do not enable.",
        "validator": "python tools/validators/validate_issue136_pvo_flags.py",
        "examples": "1658C1 gold; fleet BD/ST variance 0",
    },
    "141": {
        "tables": "quikspec.RESRVCAT",
        "source": "PCOVR.PRODUCT_TYPE via PPBEN BENEFIT_SEQ=1 PLAN_CODE (BA traditional; BF ISWL)",
        "how": "Do not copy quikplan.PRODUCT. Every quikspec row RESRVCAT = PCOVR PRODUCT_TYPE for seq-1 plan; 0 ISWLFE on RESRVCAT; plan HLOB/PRODUCT/MKTG on 1658C1/1659C2 family stay ISWLFE.",
        "validator": "python QLA_Migration/_validate_issue141_resrvcat.py",
        "examples": "9010143726C=03; 9010148272C=03; 9010713704C=05",
    },
}


def _norm_id(raw: str) -> str:
    s = re.sub(r"[*`#]", "", raw).strip()
    s = s.replace(" ", "")
    # master may have "#2" or "21A"
    return s.lstrip("#")


def load_inventory() -> dict:
    if not INV.exists():
        raise SystemExit(f"Missing {INV}; run _build_completed_issues_guide.py first")
    return json.loads(INV.read_text(encoding="utf-8"))


def build_rows(inv: dict) -> list[dict]:
    by_id: dict[str, dict] = {}

    for r in inv["master"]:
        iid = _norm_id(r["id"])
        if not iid or iid.lower() in {"id", "area"}:
            continue
        if "CLOSED" not in r.get("status", "").upper() and "CLOSED" not in r.get("resolution", "").upper():
            # master row may still say CLOSED in status
            if "CLOSED" not in str(r).upper():
                continue
        by_id[iid] = {
            "id": iid,
            "short": re.sub(r"[*`]", "", r.get("item", "")).strip(),
            "resolution": re.sub(r"[*`]", "", r.get("resolution", "")).strip(),
            "release": re.sub(r"[*`]", "", r.get("release", "")).strip(),
            "status": "Closed",
        }

    for r in inv["tsv"]:
        iid = _norm_id(r["id"])
        cur = by_id.get(iid, {"id": iid})
        cur["short"] = cur.get("short") or r.get("short", "")
        # prefer Resolution: from desc/notes
        res = r.get("desc", "")
        if "Resolution:" in r.get("notes", ""):
            res = r["notes"]
        elif r.get("desc", "").startswith("Resolution:"):
            res = r["desc"]
        elif "Resolution:" not in res and r.get("notes"):
            # keep short resolution-ish notes
            res = r.get("notes") or res
        cur["resolution"] = res
        cur["resolved"] = r.get("resolved", "")
        cur["status"] = "Closed"
        by_id[iid] = cur

    # attach resolution briefs
    for iid, meta in inv["resolutions"].items():
        nid = _norm_id(iid)
        if nid not in by_id:
            # only add if resolution path implies closed — skip open ones
            continue
        brief = meta.get("brief") or ""
        if brief and (
            not by_id[nid].get("resolution")
            or len(brief) > 40
            and "Resolution" in brief
        ):
            if brief.lower().startswith("resolution"):
                by_id[nid]["resolution"] = brief
            else:
                by_id[nid]["resolution"] = f"Resolution: {brief}"
        by_id[nid]["detail"] = meta.get("path", "")

    # drop known non-closed that leaked (e.g. 95 blocked)
    drop = {"95"}  # still open / blocked
    for d in list(by_id):
        if d in drop:
            by_id.pop(d, None)

    rows = list(by_id.values())

    def sort_key(r: dict):
        iid = r["id"]
        m = re.match(r"(\d+)([A-Z]*)", iid)
        if not m:
            return (9999, iid)
        return (int(m.group(1)), m.group(2))

    rows.sort(key=sort_key)
    return rows


def md_escape(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ").strip()


def render(rows: list[dict], inv: dict) -> str:
    vals = inv.get("validators", {})
    lines: list[str] = []
    lines.append("# Completed Issues - Release Validation Guide")
    lines.append("")
    lines.append("**Purpose:** Living checklist of every **closed / completed** conversion modification. Use this on every release to confirm each prior fix is still present in `QLA_Migration/Output/` and still agrees with LifePRO source extracts.")
    lines.append("")
    lines.append("**Canonical path:** `Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md`")
    lines.append("")
    lines.append("**Last rebuilt:** auto-generated seed - update the row when an issue closes or a modification ships.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## How to use this guide (every release)")
    lines.append("")
    lines.append("1. Run a full batch against the source package under test (`QLA_VALUATION_DATE` matching that extract).")
    lines.append("2. Run fleet accountability:")
    lines.append("")
    lines.append("```text")
    lines.append("python tools/validators/validate_issue_log_accountability.py")
    lines.append("```")
    lines.append("")
    lines.append("3. For each row below marked **Closed**, confirm:")
    lines.append("   - Resolution behavior still present in Output tables listed")
    lines.append("   - Source validation method still passes (or documented waiver)")
    lines.append("   - Issue validator (if listed) PASS")
    lines.append("4. When closing a new issue or committing a conversion change that alters Output behavior: **add or update a row in this file in the same commit**.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Maintenance rule (locked)")
    lines.append("")
    lines.append("| When | Action |")
    lines.append("|------|--------|")
    lines.append("| Issue status -> **Closed** | Add/update row: Resolution, Output tables, Source validation, Validator, Examples |")
    lines.append("| Commit ships a conversion modification | Confirm the owning issue row exists and matches the change |")
    lines.append("| Release / full batch | Walk this list; do not call the release clean if a Closed row fails without waiver |")
    lines.append("| Issue reopened | Change Status to Reopened and note the gap; do not delete history |")
    lines.append("")
    lines.append("Also required by Closure Agent G7 and `.cursor/rules/completed-issues-release-guide.mdc`.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Closed issues checklist")
    lines.append("")
    lines.append("| ID | Short name | Resolution (plain language) | Output tables | Validate from source | Validator / check | Examples |")
    lines.append("|----|------------|-----------------------------|-----------------|----------------------|-------------------|----------|")

    for r in rows:
        iid = r["id"]
        enrich = SOURCE_VALIDATE.get(iid, {})
        res = r.get("resolution") or ""
        # compress long resolutions
        if len(res) > 280:
            res = res[:277] + "..."
        # strip leading Resolution: duplication for cell brevity optional — keep
        tables = enrich.get("tables", "see Issue folder")
        how = enrich.get("how", "See Issue_*_Resolution_Summary.md and re-run issue validator on full Output.")
        source = enrich.get("source", "see resolution summary")
        src_cell = f"**Source:** {source}. **How:** {how}"
        val = enrich.get("validator") or ""
        if not val:
            key = f"#{iid}" if not iid.startswith("21") else f"#{iid}"
            paths = vals.get(key) or vals.get(iid) or []
            if paths:
                val = "python " + paths[0]
            else:
                val = "accountability + Issue folder validator"
        examples = enrich.get("examples", "")
        short = r.get("short") or enrich.get("short", "")
        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(iid),
                    md_escape(short),
                    md_escape(res),
                    md_escape(tables),
                    md_escape(src_cell),
                    md_escape(val),
                    md_escape(examples),
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Release sign-off block (copy per release)")
    lines.append("")
    lines.append("```text")
    lines.append("Release / engine: ____________")
    lines.append("Source package / QLA_VALUATION_DATE: ____________")
    lines.append("Accountability script: PASS / FAIL")
    lines.append("Closed-row failures (IDs): ____________")
    lines.append("Waivers (ID + reason + date): ____________")
    lines.append("Signed off by: ____________  Date: ____________")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Related")
    lines.append("")
    lines.append("- Master tracking: `Issue_Log_Items/Issue_Log_Master_Tracking_Sheet.md`")
    lines.append("- Accountability: `tools/validators/validate_issue_log_accountability.py`")
    lines.append("- Closure: `AI_Agents/Closure_Agent.md` (G7)")
    lines.append("- Issue A conversion checklist: `Issue_Log_Items/Issue_A/Issue_A_Conversion_Checklist.md`")
    lines.append("")
    lines.append("### Regenerating the seed table")
    lines.append("")
    lines.append("```text")
    lines.append("python Issue_Log_Items/_build_completed_issues_guide.py")
    lines.append("python Issue_Log_Items/_generate_completed_issues_guide.py")
    lines.append("```")
    lines.append("")
    lines.append("After regenerate, **manually verify** new Closed rows and enrich Source/How cells before commit.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    inv = load_inventory()
    rows = build_rows(inv)
    OUT.write_text(render(rows, inv), encoding="utf-8")
    print(f"Wrote {OUT} with {len(rows)} rows")


if __name__ == "__main__":
    main()
