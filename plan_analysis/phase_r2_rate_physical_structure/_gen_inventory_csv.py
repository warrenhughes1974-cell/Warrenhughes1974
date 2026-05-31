"""Generate rate_dbf_physical_structure_inventory.csv directly from parsed DBF headers (read-only)."""
import struct, glob, os, csv

SRC = r"plan_analysis/source_data/reference_dbf"
OUT = r"plan_analysis/phase_r2_rate_physical_structure/rate_dbf_physical_structure_inventory.csv"

def parse(path):
    f = open(path, "rb"); hdr = f.read(32)
    nrec = struct.unpack("<I", hdr[4:8])[0]
    hsize = struct.unpack("<H", hdr[8:10])[0]
    rsize = struct.unpack("<H", hdr[10:12])[0]
    fields = []
    while True:
        fd = f.read(32)
        if not fd or fd[0] == 0x0D: break
        fields.append((fd[0:11].split(b"\x00")[0].decode("ascii", "replace"), chr(fd[11]), fd[16], fd[17]))
    return nrec, fields

# canonical display names
DISP = {"quikgps(3).dbf": "QuikGps", "quikcvs.dbf": "QuikCvs", "quikdbs.dbf": "QuikDbs",
        "quikdvs.dbf": "QuikDvs", "quiknps.dbf": "QuikNps", "quiktvs.dbf": "QuikTvs",
        "quikpltv.dbf": "QuikPlTv", "quikplgp.dbf": "QuikPlGp", "quikplcv.dbf": "QuikPlCv",
        "quikpldb.dbf": "QuikPlDb", "quikpldv.dbf": "QuikPlDv", "quikplgd.dbf": "QuikPlGd",
        "quikplnb.dbf": "QuikPlNb", "quikplst.dbf": "QuikPlSt", "quikqxs.dbf": "QuikQxs"}

KEYFIELDS = {"PLAN", "AGE", "CNTL", "GENDER", "UWCLASS", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE",
             "GDCODE", "MORT"}

MEAN = {
    "PLAN": "Authoritative 6-char QLAdmin plan code (root of all rate lookup)",
    "AGE": "Issue age (or 00 when grid varies by policy-year/duration only)",
    "CNTL": "Duration page: column n = duration (CNTL*10 + n). CONFIRMED",
    "GENDER": "Gender segment: 0=N/A/unisex F=female M=male",
    "UWCLASS": "Underwriting risk class: 00=default NT/TB/SM/RG/UR/US etc (company-defined)",
    "BAND": "Insurance band: 00=default 01/99/FM/IN etc (company-defined)",
    "ISSCNTRY": "Issue country segment (0000=default/all)",
    "ISSUEST": "Issue state segment (00=default/all)",
    "EFFDATE": "Rate generation effective date (19000101=default generation)",
    "MORT": "Mortality table code -> QuikQxs / manual appendix 6.9",
    "ETIMORT": "Extended-term-insurance mortality table code",
    "NFOINT": "Non-forfeiture / NFO interest (rebate) code",
    "INTMETHCV": "Cash value interest method (0=curtate-style default observed)",
    "INTMETHTV": "Reserve interest method: 0=Curtate 1=Continuous (manual)",
    "RSVINT": "Reserve interest rate code",
    "RSVMETH": "Reserve method: 1=NetLevel 2=FullPrelimTerm 3=CRVM 4=ModifiedRVM (manual)",
    "STOREMEANS": "Logical: store mean reserves (T/F)",
    "CALCMIDS": "Logical: calculate mid-terminal/interpolated reserves (T/F)",
    "GDCODE": "Gender member code for this plan (PVO Gender option member)",
    "GDDESCR": "Gender member description (e.g. MALE/FEMALE/NOT APPLICABLE)",
    "TERMDATE": "Plan availability termination date for this country/state (new-business window)",
    "TABLENAME": "Human-readable mortality table name (e.g. '1980 CSO Male')",
    "RADIX": "Mortality table radix/scaling indicator (value 200 observed)",
    "CNTRYTXT": "Issue country description text (e.g. ALL (OTHER))",
    "STATETXT": "Issue state description text (e.g. ALL (OTHER))",
    "MLOANINT": "State-specific loan interest rate override (per manual; overrides plan general tab)",
    "MLOANINTX": "Loan interest type for the state override (A=advance R=arrears)",
}
def meaning(tbl, fn):
    if fn in MEAN: return MEAN[fn]
    if fn[:-1] in ("GP", "CV", "DB", "DV", "NP", "TV") and fn[-1].isdigit():
        fam = fn[:-1]; fmn = {"GP": "gross premium", "CV": "cash value", "DB": "death benefit",
                              "DV": "dividend", "NP": "net premium", "TV": "terminal reserve"}[fam]
        return f"{fmn} factor for duration (CNTL*10 + {fn[-1]}); stored as CHAR text"
    if fn.startswith("Q") and fn[1:].isdigit():
        return f"Mortality rate qx at attained age {int(fn[1:])} (NUMERIC, per radix); keyed by MORT"
    return ""

def notes(tbl, fn, t, l):
    n = []
    if fn.endswith(tuple("0123456789")) and fn[:-1] in ("GP","CV","DB","DV","NP","TV"):
        n.append("C7 text => max '9999.99'; FACTOR OVERFLOW RISK if value>=10000")
    if fn == "EFFDATE": n.append("Date type D(8); part of uniqueness key; supports multi-generation")
    if fn in ("STOREMEANS","CALCMIDS"): n.append("Logical field; empty in supplied template data")
    if fn in ("MORT","RSVINT","RSVMETH","INTMETHTV") and tbl=="QuikPlTv": n.append("Reserve assumption lives on the KEY table, not the factor grid")
    if fn in ("MORT","ETIMORT","NFOINT","INTMETHCV") and tbl=="QuikPlCv": n.append("Cash-value assumption lives on the KEY table")
    if fn == "MORT" and tbl == "QuikQxs": n.append("UNIQUENESS KEY of QuikQxs; shared global mortality library (no PLAN)")
    if fn.startswith("Q") and fn[1:].isdigit() and tbl == "QuikQxs": n.append("NUMERIC N9.4 (contrast factor grids which are CHAR)")
    if fn == "MLOANINT": n.append("State loan-rate override; NUMERIC N5.2")
    return "; ".join(n)

seen = {os.path.basename(p).lower(): p for p in glob.glob(SRC + "/*.dbf") + glob.glob(SRC + "/*.DBF")}
order = ["quikgps(3).dbf","quiknps.dbf","quikcvs.dbf","quikdbs.dbf","quikdvs.dbf","quiktvs.dbf",
         "quikplgp.dbf","quikplcv.dbf","quikpldb.dbf","quikpldv.dbf","quikpltv.dbf",
         "quikplgd.dbf","quikplnb.dbf","quikplst.dbf","quikqxs.dbf"]
with open(OUT, "w", newline="", encoding="utf-8") as fo:
    w = csv.writer(fo)
    w.writerow(["TABLE_NAME","FIELD_ORDER","FIELD_NAME","TYPE","LENGTH","DECIMALS","IS_KEY_FIELD","LIKELY_BUSINESS_MEANING","NOTES"])
    for key in order:
        if key not in seen: continue
        tbl = DISP[key]
        nrec, fields = parse(seen[key])
        for i, (fn, t, l, d) in enumerate(fields, 1):
            w.writerow([tbl, i, fn, t, l, d, "Y" if fn in KEYFIELDS else "N", meaning(tbl, fn), notes(tbl, fn, t, l)])
print("wrote", OUT)
import csv as c
rows=list(c.reader(open(OUT,encoding="utf-8")))
print("rows:",len(rows),"cols:",len(rows[0]))
