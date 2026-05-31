"""
Generate R5 business-input templates (READ-ONLY prep; no DBFs, no decisions made).

Outputs (plan_analysis/phase_r4_loader_architecture/business_inputs/):
  rate_overflow_business_decision_sheet.csv          (2 overflow plans, decisions blank)
  plan_rate_key_assumption_mapping_template.csv      (all in-scope authoritative plans x family)
  r5_business_input_readiness_summary.md
"""
import os, csv, collections
import openpyxl

ROOT = r"plan_analysis/source_data"
R4 = r"plan_analysis/phase_r4_loader_architecture"
OUTDIR = os.path.join(R4, "business_inputs")
SRC = os.path.join(ROOT, "rates", "Rate_Table_Extract_20260427.csv")
XLSX = os.path.join(ROOT, "crosswalk", "Policy Form Crosswalk 5.22.26.xlsx")

TYPE_TO_TABLE = {"CV": "QuikCvs", "DB": "QuikDbs", "NP": "QuikNps",
                 "DV": "QuikDvs", "RV": "QuikTvs", "PR": "QuikGps"}
FAMILY = {"PR": "GROSS_PREMIUM", "CV": "CASH_VALUE", "DB": "DEATH_BENEFIT",
          "DV": "DIVIDEND", "NP": "NET_PREMIUM", "RV": "TERMINAL_RESERVE"}
EXCLUDED = {"NN", "PN", "TP", "TX", "UF", "NF", "SL"}
SEX_MAP = {"F": "F", "M": "M", "J": "J"}
BAND_MAP = {"1": "01", "2": "02", "3": "03"}
UW_MAP = {"0": "00", "N": "NS", "S": "SM", "P": "PR", "B": "ST"}
CAP_STR = "CHAR(7) fixed 2dp: pos<=9999.99, neg>=-999.99"
# assumption fields that apply per family (others left blank)
CV_FIELDS = {"MORT", "ETIMORT", "NFOINT", "INTMETHCV"}
TV_FIELDS = {"MORT", "RSVINT", "RSVMETH", "INTMETHTV", "STOREMEANS", "CALCMIDS"}


def load_xwalk():
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb["Sheet1"]
    plan2desc = {}
    cov2plan = {}
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue
        cov = row[0]; plan = row[2]; desc = row[4] if len(row) > 4 else None
        if cov and plan:
            cov2plan[str(cov).strip()] = str(plan).strip()
            plan2desc[str(plan).strip()] = (str(desc).strip() if desc else "")
    return cov2plan, plan2desc


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    cov2plan, plan2desc = load_xwalk()

    # scan source: per (plan, typ) collect distinct seg values + value stats
    stats = {}  # (plan,typ) -> dict
    with open(SRC, encoding="utf-8-sig", errors="replace", newline="") as f:
        rd = csv.reader(f); next(rd)
        for r in rd:
            if len(r) < 8:
                continue
            cov = r[0].strip(); typ = r[1].strip()
            if set(cov) == {"-"} or typ in EXCLUDED or typ not in TYPE_TO_TABLE:
                continue
            plan = cov2plan.get(cov)
            if not plan:
                continue
            age = r[2].strip(); sex = r[3].strip(); band = r[4].strip(); uw = r[5].strip()
            k = (plan, typ)
            st = stats.get(k)
            if st is None:
                st = {"cov": cov, "sex": set(), "band": set(), "uw": set(), "n": 0}
                stats[k] = st
            st["n"] += 1
            st["sex"].add(SEX_MAP.get(sex, sex))
            st["band"].add(BAND_MAP.get(band, band))
            st["uw"].add(UW_MAP.get(uw, uw))

    # ---- Deliverable 1: overflow decision sheet (known from R4) ----
    # pull worst-case example row per overflow plan from R4 overflow_detail_report
    examples = {}  # plan -> (age,dur,value)
    detail = os.path.join(R4, "overflow_detail_report.csv")
    if os.path.exists(detail):
        with open(detail, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                p = row["PLAN"]; v = float(row["VALUE"])
                if p not in examples or v > examples[p][2]:
                    examples[p] = (row["AGE"], row["DURATION"], v)

    overflow_rows = [
        # RATE_FAMILY, TYPE_CODE, PLAN, OVERFLOW_ROW_COUNT, MIN, MAX
        ("DEATH_BENEFIT", "DB", "2665ST", 1333, 2094.00, 28134.00),
        ("CASH_VALUE", "CV", "A96DAR", 300, 0.00, 26418.10),
    ]
    p1 = os.path.join(OUTDIR, "rate_overflow_business_decision_sheet.csv")
    with open(p1, "w", newline="", encoding="utf-8") as cf:
        w = csv.writer(cf)
        w.writerow(["RATE_FAMILY", "TYPE_CODE", "PLAN", "OVERFLOW_ROW_COUNT", "MIN_VALUE",
                    "MAX_VALUE", "FIELD_CAPACITY", "EXAMPLE_AGE", "EXAMPLE_DURATION",
                    "EXAMPLE_VALUE", "LIKELY_CAUSE", "BUSINESS_DECISION", "APPROVED_SCALING_FACTOR",
                    "APPROVED_TARGET_VALUE_RULE", "QUARANTINE_FLAG", "BUSINESS_OWNER",
                    "ACTUARIAL_APPROVER", "APPROVAL_DATE", "NOTES"])
        for fam, typ, plan, cnt, mn, mx in overflow_rows:
            ex = examples.get(plan, ("", "", ""))
            exval = f"{ex[2]:.2f}" if ex[2] != "" else ""
            cause = ("Factors stored as large absolute amounts (>9999.99) rather than per-unit "
                     "factors that fit CHAR(7); requires actuarial confirmation of factor basis")
            note = ("Allowed BUSINESS_DECISION values: RESCALE_PER_UNIT | CONFIRM_ALTERNATE_FACTOR_BASIS | "
                    "QUARANTINE_PLAN | EXCLUDE_FROM_INITIAL_LOAD | REQUIRE_ACTUARIAL_REVIEW. "
                    "Decision intentionally left blank for business/actuarial sign-off.")
            w.writerow([fam, typ, plan, cnt, f"{mn:.2f}", f"{mx:.2f}", CAP_STR,
                        ex[0], ex[1], exval, cause, "", "", "", "", "", "", "", note])

    # ---- Deliverable 2: plan rate key assumption mapping template ----
    p2 = os.path.join(OUTDIR, "plan_rate_key_assumption_mapping_template.csv")
    fam_order = ["PR", "DV", "DB", "CV", "RV", "NP"]
    plans_included = set()
    with open(p2, "w", newline="", encoding="utf-8") as cf:
        w = csv.writer(cf)
        w.writerow(["PLAN", "PLAN_DESCRIPTION", "RATE_FAMILY", "TYPE_CODE", "EFFDATE", "ISSCNTRY",
                    "ISSUEST", "GENDER_REQUIRED", "UWCLASS_REQUIRED", "BAND_REQUIRED",
                    "STATE_COUNTRY_REQUIRED", "MORT", "ETIMORT", "RSVINT", "RSVMETH", "INTMETHCV",
                    "INTMETHTV", "NFOINT", "STOREMEANS", "CALCMIDS", "ASSUMPTION_SOURCE",
                    "BUSINESS_OWNER", "ACTUARIAL_APPROVER", "APPROVAL_DATE", "NOTES"])
        for (plan, typ) in sorted(stats, key=lambda x: (fam_order.index(x[1]) if x[1] in fam_order else 9, x[0])):
            st = stats[(plan, typ)]
            plans_included.add(plan)
            fam = FAMILY[typ]
            gen_req = "Y" if len(st["sex"]) > 1 else "N"
            uw_req = "Y" if len(st["uw"]) > 1 else "N"
            bd_req = "Y" if len(st["band"]) > 1 else "N"
            # assumption columns: only relevant family gets them as required-to-fill, others "N/A"
            relevant = CV_FIELDS if typ == "CV" else (TV_FIELDS if typ in ("RV", "NP") else set())
            def cell(name):
                return "" if name in relevant else "N/A"
            note = "segmentation flags observed from source (distinct mapped values); assumptions left blank for actuarial input"
            if typ in ("CV", "RV", "NP"):
                note = ("assumptions REQUIRED before " + fam + " key generation (not present in rate extract); " + note)
            w.writerow([plan, plan2desc.get(plan, ""), fam, typ, "", "", "",
                        gen_req, uw_req, bd_req, "",
                        cell("MORT"), cell("ETIMORT"), cell("RSVINT"), cell("RSVMETH"),
                        cell("INTMETHCV"), cell("INTMETHTV"), cell("NFOINT"),
                        cell("STOREMEANS"), cell("CALCMIDS"),
                        "", "", "", "", note])

    print("overflow plans:", [x[2] for x in overflow_rows])
    print("distinct authoritative plans in template:", len(plans_included))
    print("plan x family rows in template:", len(stats))
    print("examples:", examples)
    # return for md
    return len(plans_included), len(stats), sorted(plans_included)


if __name__ == "__main__":
    main()
