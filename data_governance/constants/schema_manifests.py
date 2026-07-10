"""Expected column order per QLA output file.

SCHEMA_MANIFEST_VERSION is compared to app table version (GOV-012).
Aligned with validation_config/schema_manifest.json and app.py TABLE_SCHEMAS.
"""

SCHEMA_MANIFEST_VERSION = "1.0.0"

SCHEMA_MANIFESTS: dict[str, list[str]] = {
    "quikplan": [
        "PLAN", "FORM", "DESCR", "PAR", "SEX", "BASIS", "NFOINT", "LOANINT",
        "LOANINTX", "DEPINT", "VARDB", "VARGP", "LOAGE", "HIAGE", "RENEW",
        "PAYYRS", "PAYAGE", "INSYRS", "INSAGE", "ANNL", "SEMI", "QTRL", "MTHD",
        "MTHB", "ANNLFEE", "SEMIFEE", "QTRLFEE", "MTHDFEE", "MTHBFEE", "INITVAL",
        "MKTG", "PRODUCT", "CALCADV", "COMMID", "MINUNIT", "MAXUNIT", "BPOLFEE",
        "BACTIVE", "RRULE", "AGTRSV", "AUTONFO", "PLANTYPE", "INTMETHTV",
        "INTMETHCV", "DEFICIENCY", "HDEDMETHOD", "PLANVALOPT", "GDVARYGP",
        "GDVARYDB", "GDVARYCV", "GDVARYTV", "GDVARYDV", "UWVARYGP", "UWVARYDB",
        "UWVARYCV", "UWVARYTV", "UWVARYDV", "BDVARYGP", "BDVARYDB", "BDVARYCV",
        "BDVARYTV", "BDVARYDV", "STVARYGP", "STVARYDB", "STVARYCV", "STVARYTV",
        "STVARYDV", "CONVCOMM", "PLANNAME", "HRENEW", "HLOB", "HCOMMIP",
        "HRIGPKEY", "SIMPLEINT", "MLAPSE", "MNOTE10", "MNAICLOB", "MNFOANNV",
        "MGTDANNV",
    ],
    "quikmstr": [
        "MPOLICY", "MSTATUS", "MSTATDATE", "MISSDT", "MPAIDTO", "MBILLTO",
        "MNFOPT", "MDIVOPT", "MBILLFRM", "MBILLDAY", "MACCTNO", "MBANKNO",
        "MPREBILL", "MMODE", "MMODEPREM", "MSEMI", "MQTRL", "MMTHD", "MMTHB",
        "MINQUIRY", "MISSUEST", "MBFCY", "MGROUP", "MPRIMID", "MOWNRID",
        "MPAYRID", "MASGNID", "MBENPID", "MBENCID", "MAPPDATE", "MSUBMDATE",
        "MRELDATE", "MRELOTHER", "MORIGBILL", "MORIGMODE", "MISSCNTRY",
        "MOWNCID", "MACHCNT", "MACHNXTDT", "MRESSTATE", "MBLLDOM", "MSPCODE",
        "MISSCLASS", "MMSMBI", "MORGBLLDOM",
    ],
    "quikclnt": [
        "MCLIENTID", "MTYPE", "MTAXID", "MTAXIDTYPE", "MTITLE", "MFNAME",
        "MMNAME", "MLNAME", "MSUFFIX", "MADDR1", "MADDR2", "MCITY", "MSTATE",
        "MZIP", "MZIP2", "MCOUNTRY", "MPHONEHOME", "MPHONEOFC", "MPHOFCEXT",
        "MPHONECELL", "MPHONEFAX", "MEMAIL", "MDOB", "MSEX", "MMEMBERID",
        "MLANGUAGE", "MPDFPSSWD", "MEMAILCORR", "MVALID", "MDNC", "MOFAC",
        "MMEMBERDT", "MMSMBI", "MFOREIGN", "MOCCODE",
    ],
    "quikridr": [
        "MPOLICY", "MPHASE", "MPHSTAT", "MLASTANN", "MANNSTAT", "MPHDOB",
        "MSEX", "MPLAN", "MPAR", "MEFFDATE", "MEXPRY", "MPAYUP", "MAGE",
        "MUNIT", "MVPU", "MPREM", "MANNLFEE", "MSEMIFEE", "MQTRLFEE",
        "MMTHDFEE", "MMTHBFEE", "MRRULE", "MCOMMID", "MCV0", "MCV1", "MCV2",
        "MSAVEAGE", "MSAVEUNIT", "MSAVEVPU", "MSAVEPREM", "MRIDRID", "MSSN",
        "MUWCLASS", "MBAND", "MSAVESTAT", "MCOMMPREM", "MSPCODE", "MLOCKTYP",
        "MLOCKDT", "MUNLCKDT",
    ],
    "quikbenf": ["MPOLICY", "MBENFID", "MTYPE", "MRELATION", "MSPLIT"],
    "quikclid": ["MCLIENTID", "MPOLICY", "MPHASE", "MRELATION"],
    "quikdvdp": ["MPOLICY", "MDEPOSIT", "MINTYTD", "MDEPINT", "MINTDATE"],
    "quikdvpr": ["MPOLICY", "MDATE", "MDIV"],
    "quikprmh": [
        "MPOLICY", "DATEPAID", "RENEWAL", "PREMIUM", "MLIFE", "MTERM", "MSUPP",
        "MANN", "MHEALTH", "XS", "MPAIDTO", "POSTDATE", "MPOSTDATE", "MSOURCE",
        "MBATCH", "USER_ID", "MBILLFRM", "MMODEPD",
    ],
    "quikagts": [
        "MAGENT", "MAGTNAME", "MAGTADDR1", "MAGTADDR2", "MAGTCITY", "MAGTST",
        "MAGTZIP", "MAGTZIP2", "MAGTSSN", "MAGTFEIN", "MCOMP", "MAGENCY",
        "MAGCYNAME", "MDATE", "MAGTACCT", "MAGTPHONE", "MAGTFAX", "MAGTCELL",
        "MAGTOFCE", "MAGTEMAIL", "MEMOTEXT", "MSUPPRESS", "MCOMMGRP",
        "MOTHNAME", "MPREMACCT", "MSTATUS", "MAGTNPN", "MTAXIDTYPE",
    ],
    "quikmemo": ["MEMOKEY", "MEMOTEXT"],
    "quikactg": [
        "MCOMP", "MPLAN", "MPREM1ST", "MPREMREN", "MDIVCASH", "MDIVPREM",
        "MDIVACCM", "MDIVPUA", "MDIVPUT", "MDVDPINT", "MLOAN", "MLOANINT",
        "MSCHG", "MDEATH", "MCLAIM", "MCOM1ST", "MCOMREN", "MCOMMSGL",
    ],
    "quikclms": [
        "MPOLICY", "MPHASE", "CLAIMNUM", "CLAIMSTAT", "DTOFDEATH", "RPTDATE",
        "PDDATE", "MPAID", "MFACE", "DIVIDENDS", "LOAN", "NETDB", "PREMIUM",
        "SUSPENSE", "ADJUST", "CAUSE", "MEMOTEXT", "ORIGSTTUS", "ACCPTDATE",
        "MCONTEST", "MINTST", "MINTDAYS", "MINTRATE", "MINTAMT", "MSURRCHG",
        "MSEQ", "MHOLDINT", "MFEDTAX", "MSTTAX", "MCLMPNDLTR", "MFACPMT",
        "MPHPAIDTO",
    ],
    "quikclmp": [
        "MPOLICY", "MPHASE", "MCHECKNO", "MAMOUNT", "MPAYNAME", "MPAYADDR1",
        "MPAYADDR2", "MPAYCITY", "MPAYST", "MPAYZIP", "MPAYZIP2", "MTIN",
        "MBANKNO", "MHDPMT", "MHDCODE", "MCHKDATE", "MPMTDATE", "MSEQ",
        "MHOLDINT", "MFEDTAX", "MSTTAX", "MGROSS", "MDOB", "MGENDER",
        "MCOUNTRY",
    ],
    "quikloan": [
        "MPOLICY", "MLOANPRIN", "MLOANBAL", "MLOANINT", "MLOANINTX",
        "MLOANIDT", "MLOANDATE", "MLOANACCR", "MLOANBILL",
    ],
    "quikcomp": ["MCOMP", "MNAME", "MADDR1", "MADDR2", "MCITY", "MSTATE", "MZIP"],
    "quiklist": [
        "MGROUP", "MCOMP", "MBILLNAME", "MSORT", "MLAPSEL", "MLASPEH",
        "MSTATUS", "MBILLDAY", "MBILLMODE",
    ],
    "quikdate": [
        "PACBILL", "DIRBILL", "REINBILL", "ACHFILEID", "ESCDATE",
    ],
    "quikchrt": ["MCOMP", "MPLAN", "MACCT"],
    "quikqxs": ["MORT", "DESCR"],
    "quikplcv": [
        "PLAN", "MORT", "ETIMORT", "GENDER", "UWCLASS", "BAND", "ISSUEST", "EFFDATE",
    ],
    "quikpltv": [
        "PLAN", "MORT", "ETIMORT", "GENDER", "UWCLASS", "BAND", "ISSUEST", "EFFDATE",
    ],
    "quikplgp": [
        "PLAN", "MORT", "ETIMORT", "GENDER", "UWCLASS", "BAND", "ISSUEST", "EFFDATE",
    ],
    "quikpldb": [
        "PLAN", "MORT", "ETIMORT", "GENDER", "UWCLASS", "BAND", "ISSUEST", "EFFDATE",
    ],
    "quikpldv": [
        "PLAN", "MORT", "ETIMORT", "GENDER", "UWCLASS", "BAND", "ISSUEST", "EFFDATE",
    ],
}

# Per-file version tags (GOV-012 / schema alignment)
SCHEMA_VERSIONS: dict[str, str] = {k: SCHEMA_MANIFEST_VERSION for k in SCHEMA_MANIFESTS}


def expected_columns(table_key: str) -> list[str] | None:
    """Return expected columns for a table key (with or without .csv)."""
    key = table_key.lower().replace(".csv", "").strip()
    return SCHEMA_MANIFESTS.get(key)


def schema_entry(table_key: str) -> dict | None:
    """Return {expected_columns, version} for a table key."""
    cols = expected_columns(table_key)
    if cols is None:
        return None
    key = table_key.lower().replace(".csv", "").strip()
    return {
        "expected_columns": cols,
        "version": SCHEMA_VERSIONS.get(key, SCHEMA_MANIFEST_VERSION),
    }
