"""
PHASE R3 - Read-only rate reconciliation prototype.

Validates LifePRO source -> QLAdmin target rate mappings against the POPULATED QLAdmin DBFs
(ground truth). Generates NO DBFs, modifies NOTHING. Read-only.

Source     : docs/plan_conversion_reference/Rate_Table_Extract_20260427.csv
Crosswalk  : docs/plan_conversion_reference/Policy Form Crosswalk 5.22.26.xlsx  (col A -> col C)
Targets    : QuikGps/QuikCvs/QuikDbs/QuikDvs/QuikNps/QuikTvs populated DBFs

Confirmed mappings (business-finalized):
  TYPE_CODE: CV->QuikCvs DB->QuikDbs NP->QuikNps DV->QuikDvs RV->QuikTvs PR->QuikGps
             excluded: NN PN TP TX UF NF SL
  SEX:   F->F M->M J->J
  BAND:  1->01 2->02 3->03 (zero-pad 2)
  UW:    0->00 N->NS S->SM P->PR B->ST
  DUR:   QL_DURATION = SOURCE_DURATION - 1  ->  CNTL = QL_DURATION//10 ; col = QL_DURATION%10
  ISSCNTRY/ISSUEST/EFFDATE: source has none -> target defaults 0000 / 00 / 19000101
"""
import os, struct, glob, csv, json, collections

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "plan_analysis", "source_data", "reference_dbf"))
SRC_CSV = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "plan_analysis", "source_data", "rates", "Rate_Table_Extract_20260427.csv"))
XLSX = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "plan_analysis", "source_data", "crosswalk", "Policy Form Crosswalk 5.22.26.xlsx"))
OUTDIR = r"plan_analysis/phase_r3_rate_reconciliation"

TYPE_TO_TABLE = {"CV": "QuikCvs", "DB": "QuikDbs", "NP": "QuikNps",
                 "DV": "QuikDvs", "RV": "QuikTvs", "PR": "QuikGps"}
EXCLUDED = {"NN", "PN", "TP", "TX", "UF", "NF", "SL"}
SEX_MAP = {"F": "F", "M": "M", "J": "J"}
BAND_MAP = {"1": "01", "2": "02", "3": "03"}
UW_MAP = {"0": "00", "N": "NS", "S": "SM", "P": "PR", "B": "ST"}
PREFIX = {"QuikGps": "GP", "QuikCvs": "CV", "QuikDbs": "DB",
          "QuikDvs": "DV", "QuikNps": "NP", "QuikTvs": "TV"}
DEFAULT_CNTRY, DEFAULT_STATE, DEFAULT_EFF = "0000", "00", "19000101"
OVERFLOW = 9999.99  # CHAR(7) "9999.99" max
TOL = 0.005          # half-cent tolerance


def parse_dbf(path):
    f = open(path, "rb"); hdr = f.read(32)
    nrec = struct.unpack("<I", hdr[4:8])[0]
    hsize = struct.unpack("<H", hdr[8:10])[0]
    rsize = struct.unpack("<H", hdr[10:12])[0]
    fields = []
    while True:
        fd = f.read(32)
        if not fd or fd[0] == 0x0D: break
        fields.append((fd[0:11].split(b"\x00")[0].decode("ascii", "replace"), chr(fd[11]), fd[16]))
    f.seek(hsize)
    names = [x[0] for x in fields]
    while True:
        rec = f.read(rsize)
        if not rec or len(rec) < rsize: break
        if rec[0:1] == b"*": continue
        off = 1; vals = []
        for (_, _, l) in fields:
            vals.append(rec[off:off+l].decode("latin-1", "replace").strip()); off += l
        yield dict(zip(names, vals))


def find(base):
    for p in glob.glob(ROOT + "/*.dbf") + glob.glob(ROOT + "/*.DBF"):
        if os.path.basename(p).lower().startswith(base.lower()):
            return p
    return None


def load_target(table):
    """key (PLAN,AGE,CNTL,GENDER,UWCLASS,BAND,ISSCNTRY,ISSUEST,EFFDATE) -> [c0..c9]."""
    fn = {"QuikGps": "quikgps", "QuikCvs": "quikcvs", "QuikDbs": "quikdbs",
          "QuikDvs": "quikdvs", "QuikNps": "quiknps", "QuikTvs": "quiktvs"}[table]
    path = find(fn)
    pfx = PREFIX[table]
    d = {}
    if not path:
        return d, None
    for r in parse_dbf(path):
        key = (r["PLAN"], r["AGE"], r["CNTL"], r["GENDER"], r["UWCLASS"],
               r["BAND"], r["ISSCNTRY"], r["ISSUEST"], r["EFFDATE"])
        d[key] = [r.get(f"{pfx}{i}", "") for i in range(10)]
    return d, path


def to_float(s):
    s = (s or "").strip()
    if s in ("", ".", "-", "-."): return None
    try:
        return float(s)
    except ValueError:
        return None


def load_crosswalk():
    import openpyxl
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb["Sheet1"]
    m = {}
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:  # header
            continue
        cov = row[0]; plan = row[2]
        if cov is None or plan is None:
            continue
        cov = str(cov).strip(); plan = str(plan).strip()
        if cov and plan:
            m[cov] = plan
    return m


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    xwalk = load_crosswalk()
    print(f"crosswalk entries: {len(xwalk)}")

    targets = {}
    target_paths = {}
    target_plans = {}
    for t in set(TYPE_TO_TABLE.values()):
        targets[t], target_paths[t] = load_target(t)
        target_plans[t] = set(k[0] for k in targets[t])
        print(f"loaded {t}: {len(targets[t])} rows  ({target_paths[t]})")
    CAP_PER_PLAN = 25  # cap PLAN_NOT_IN_TARGET sample rows per plan to keep report compact

    # metrics
    M = collections.Counter()
    excluded = collections.defaultdict(lambda: [0, set()])  # type -> [count, set(cov)]
    in_scope_plans = set()
    resolved_plans_in_target = set()
    hit_target_keys = collections.defaultdict(set)  # table -> set(key) hit by source
    dup_seen = set()
    pilot_rows = collections.defaultdict(list)      # plan -> sample traces
    pnt_written = collections.Counter()             # plan -> #PLAN_NOT_IN_TARGET rows written (cap)
    report_rows_written = 0

    report_path = os.path.join(OUTDIR, "rate_reconciliation_report.csv")
    rf = open(report_path, "w", newline="", encoding="utf-8")
    w = csv.writer(rf)
    w.writerow(["SOURCE_COVERAGE_ID", "AUTHORITATIVE_PLAN", "TYPE_CODE", "TARGET_TABLE",
                "SEX", "BAND", "UWCLASS", "SOURCE_DURATION", "QL_DURATION",
                "SOURCE_VALUE", "TARGET_VALUE", "MATCH_STATUS", "VALUE_DIFFERENCE", "NOTES"])

    with open(SRC_CSV, encoding="utf-8-sig", errors="replace", newline="") as f:
        rd = csv.reader(f)
        header = next(rd)
        for r in rd:
            if len(r) < 8:
                continue
            cov = r[0].strip(); typ = r[1].strip(); age = r[2].strip()
            sex = r[3].strip(); band = r[4].strip(); uw = r[5].strip()
            dur = r[6].strip(); val = r[7].strip()
            if cov == "-----------" or set(cov) == {"-"}:
                continue  # dashed separator row
            M["total_source_rows"] += 1

            if typ in EXCLUDED:
                M["excluded_rows"] += 1
                excluded[typ][0] += 1
                excluded[typ][1].add(cov)
                continue
            table = TYPE_TO_TABLE.get(typ)
            if not table:
                M["unmapped_typecode_rows"] += 1
                continue

            M["in_scope_rows"] += 1
            notes = []
            plan = xwalk.get(cov)
            if not plan:
                M["plan_unresolved_rows"] += 1
                w.writerow([cov, "", typ, table, sex, band, uw, dur, "",
                            val, "", "PLAN_UNRESOLVED", "", "no authoritative PLAN in crosswalk"])
                continue
            if " " in plan or not plan:
                M["plan_invalid_rows"] += 1
                w.writerow([cov, plan, typ, table, sex, band, uw, dur, "",
                            val, "", "PLAN_INVALID", "", "PLAN contains space / blank"])
                continue
            in_scope_plans.add(plan)

            g = SEX_MAP.get(sex, sex)
            b2 = BAND_MAP.get(band, band.zfill(2))
            u2 = UW_MAP.get(uw, uw)
            try:
                ql_dur = int(dur) - 1
            except ValueError:
                M["bad_duration_rows"] += 1
                continue
            if ql_dur < 0:
                M["bad_duration_rows"] += 1
                continue
            cntl = str(ql_dur // 10).zfill(2)
            col = ql_dur % 10
            age2 = age.zfill(2)

            sval = to_float(val)
            if sval is not None and abs(sval) >= OVERFLOW + 0.005:
                M["overflow_observations"] += 1
                notes.append(f"OVERFLOW src={sval}")
            if table == "QuikTvs" and sval is not None and sval < 0:
                M["negative_reserve_observations"] += 1
                notes.append("NEGATIVE_RESERVE")

            if plan in target_plans[table]:
                resolved_plans_in_target.add(plan)
            base_key = (plan, age2, cntl, g, u2, b2, DEFAULT_CNTRY, DEFAULT_STATE, DEFAULT_EFF)
            tgt = targets[table]
            status = None; tval_s = ""; matched_key = None
            cells = tgt.get(base_key)
            if cells is not None:
                matched_key = base_key
            else:
                # documented fallbacks: collapse non-varying dims to default members
                for fb_g, fb_u, fb_b, tagn in [
                    ("0", u2, b2, "GENDER->0"),
                    (g, "00", b2, "UWCLASS->00"),
                    (g, u2, "00", "BAND->00"),
                    ("0", "00", "00", "SEG->defaults"),
                    (g, u2, b2, "AGE->00"),  # special-cased below
                ]:
                    if tagn == "AGE->00":
                        k = (plan, "00", cntl, g, u2, b2, DEFAULT_CNTRY, DEFAULT_STATE, DEFAULT_EFF)
                    else:
                        k = (plan, age2, cntl, fb_g, fb_u, fb_b, DEFAULT_CNTRY, DEFAULT_STATE, DEFAULT_EFF)
                    if k in tgt:
                        matched_key = k; cells = tgt[k]; notes.append(f"FALLBACK:{tagn}")
                        break

            # duplicate key detection (source side)
            dkey = (table, base_key, col)
            if dkey in dup_seen:
                M["duplicate_keys"] += 1
                notes.append("DUPLICATE_SOURCE_KEY")
            else:
                dup_seen.add(dkey)

            if cells is None:
                if plan not in target_plans[table]:
                    status = "PLAN_NOT_IN_TARGET"
                    M["plan_not_in_target_rows"] += 1
                else:
                    status = "MISSING_TARGET_ROW"
                    M["missing_target_rows"] += 1
                vdiff = ""
            else:
                hit_target_keys[table].add(matched_key)
                tval_s = cells[col] if col < len(cells) else ""
                tval = to_float(tval_s)
                if tval is None or tval_s == "":
                    status = "MISSING_TARGET_CELL"
                    M["missing_target_rows"] += 1
                    vdiff = ""
                else:
                    diff = round((sval if sval is not None else 0.0) - tval, 4)
                    vdiff = f"{diff:.4f}"
                    if sval is not None and abs(diff) <= TOL:
                        status = "EXACT_MATCH" if matched_key == base_key else "MATCH_FALLBACK"
                        M["exact_matches"] += 1
                    else:
                        status = "VALUE_MISMATCH"
                        M["value_mismatches"] += 1
                M["rows_reconciled"] += 1

            if len(pilot_rows[plan]) < 60:
                pilot_rows[plan].append((cov, typ, table, sex, band, uw, dur, ql_dur,
                                         cntl, col, age2, g, u2, b2, val, tval_s, status, "; ".join(notes)))
            # write full fidelity for interesting statuses; cap the dominant PLAN_NOT_IN_TARGET sample
            if status == "PLAN_NOT_IN_TARGET":
                if pnt_written[plan] >= CAP_PER_PLAN:
                    continue
                pnt_written[plan] += 1
                if notes:
                    notes.append("(sampled: capped per plan; full count in summary.json)")
                else:
                    notes = ["sampled: capped per plan; full count in summary.json"]
            w.writerow([cov, plan, typ, table, g, b2, u2, dur, ql_dur,
                        val, tval_s, status, vdiff, "; ".join(notes)])
            report_rows_written += 1
    rf.close()

    # reverse: missing source rows (target keys for in-scope plans never hit by source)
    for t, tgt in targets.items():
        miss = 0
        if in_scope_plans & target_plans[t]:  # only meaningful if plan universes overlap
            for key in tgt:
                if key[0] in in_scope_plans and key not in hit_target_keys[t]:
                    miss += 1
        M[f"missing_source_rows_{t}"] = miss
        M["missing_source_rows"] += miss

    # excluded inventory
    exc_path = os.path.join(OUTDIR, "excluded_type_code_inventory.csv")
    with open(exc_path, "w", newline="", encoding="utf-8") as ef:
        ew = csv.writer(ef)
        ew.writerow(["TYPE_CODE", "ROW_COUNT", "DISTINCT_COVERAGE_IDS", "NOTES"])
        for typ in sorted(EXCLUDED):
            cnt, covs = excluded[typ]
            ew.writerow([typ, cnt, len(covs),
                         "out-of-scope per business decision; not converted to QLAdmin"])

    # summary json
    summary = {
        "phase": "R3 read-only rate reconciliation",
        "source_file": SRC_CSV,
        "crosswalk_file": XLSX,
        "crosswalk_entries": len(xwalk),
        "target_tables": {t: len(targets[t]) for t in targets},
        "metrics": {
            "total_source_rows": M["total_source_rows"],
            "in_scope_rows": M["in_scope_rows"],
            "rows_reconciled": M["rows_reconciled"],
            "exact_matches": M["exact_matches"],
            "value_mismatches": M["value_mismatches"],
            "missing_target_rows": M["missing_target_rows"],
            "missing_source_rows": M["missing_source_rows"],
            "plan_not_in_target_rows": M["plan_not_in_target_rows"],
            "excluded_type_code_rows": M["excluded_rows"],
            "plan_unresolved_rows": M["plan_unresolved_rows"],
            "plan_invalid_rows": M["plan_invalid_rows"],
            "bad_duration_rows": M["bad_duration_rows"],
            "duplicate_keys": M["duplicate_keys"],
            "overflow_observations": M["overflow_observations"],
            "negative_reserve_observations": M["negative_reserve_observations"],
        },
        "report_rows_written": report_rows_written,
        "report_note": ("PLAN_NOT_IN_TARGET rows are sampled (cap %d/plan) to keep the CSV compact; "
                        "authoritative full counts are in metrics above." % CAP_PER_PLAN),
        "plan_universe_overlap": {
            "distinct_resolved_authoritative_plans": len(in_scope_plans),
            "resolved_plans_present_in_any_target_table": len(resolved_plans_in_target),
            "verdict": ("DISJOINT - populated target rate DBFs contain a different plan population "
                        "than the source/crosswalk resolves to; value-level ground-truth comparison "
                        "is not possible against this target drop"
                        if not resolved_plans_in_target else "PARTIAL/FULL overlap present"),
        },
        "missing_source_rows_by_table": {t: M[f"missing_source_rows_{t}"] for t in targets},
        "in_scope_authoritative_plans": sorted(in_scope_plans),
        "match_status_legend": {
            "EXACT_MATCH": "source value == target value within 0.005 on exact key",
            "MATCH_FALLBACK": "matched after documented default-collapse fallback",
            "VALUE_MISMATCH": "key matched, value differs > 0.005",
            "MISSING_TARGET_ROW": "plan present in target table but no row for the transformed key",
            "MISSING_TARGET_CELL": "target row exists but the duration cell is blank",
            "PLAN_NOT_IN_TARGET": "resolved authoritative PLAN absent from the target table entirely",
            "PLAN_UNRESOLVED": "COVERAGE_ID not in authoritative crosswalk",
            "PLAN_INVALID": "resolved PLAN blank or contains space",
        },
    }
    with open(os.path.join(OUTDIR, "rate_reconciliation_summary.json"), "w", encoding="utf-8") as jf:
        json.dump(summary, jf, indent=2)

    # stash pilot data for the md generator
    with open(os.path.join(OUTDIR, "_pilot_data.json"), "w", encoding="utf-8") as pf:
        # choose plans with most matches
        ranked = sorted(in_scope_plans,
                        key=lambda p: sum(1 for row in pilot_rows[p] if "MATCH" in row[16]), reverse=True)
        keep = {p: pilot_rows[p] for p in ranked[:5]}
        json.dump({"ranked": ranked[:10], "rows": keep,
                   "metrics": dict(summary["metrics"])}, pf, indent=1)

    print(json.dumps(summary["metrics"], indent=2))
    print("in-scope plans:", len(in_scope_plans))


if __name__ == "__main__":
    main()
