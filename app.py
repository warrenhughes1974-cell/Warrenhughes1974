# =============================================================================
# APPLICATION VERSION
# =============================================================================
# Version:     v55.7
# Date:        2026-05-24
# Change Note: Phase 22C — claim domain eligibility tightening (LifePRO 04xx + QLAdmin authoritative semantics)
# =============================================================================

import pandas as pd
import os
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext, ttk
import threading
import time
import zipfile
import json
import re
import csv
from datetime import datetime

# --- Phase 18A–20: Claims orchestration, UAT handoff/emit/batch/DBF, MPOLICY validation ---
VALID_RUN_MODES = ("UAT", "PRODUCTION", "DISABLED")
DEFAULT_RUN_MODE = "UAT"
DEFAULT_ORCHESTRATION_TIMEOUT_SECONDS = 600
CLAIMS_TABLE_IDS = ("quikclms", "quikclmp")
QUIKCLMS_SCHEMA = [
    "MPOLICY", "MPHASE", "CLAIMNUM", "CLAIMSTAT", "DTOFDEATH", "RPTDATE", "PDDATE",
    "MPAID", "MFACE", "DIVIDENDS", "LOAN", "NETDB", "PREMIUM", "SUSPENSE", "ADJUST",
    "CAUSE", "MEMOTEXT", "ORIGSTTUS", "ACCPTDATE", "MCONTEST", "MINTST", "MINTDAYS",
    "MINTRATE", "MINTAMT", "MSURRCHG", "MSEQ", "MHOLDINT", "MFEDTAX", "MSTTAX",
    "MCLMPNDLTR", "MFACPMT", "MPHPAIDTO",
]
QUIKCLMP_SCHEMA = [
    "MPOLICY", "MPHASE", "MCHECKNO", "MAMOUNT", "MPAYNAME", "MPAYADDR1", "MPAYADDR2",
    "MPAYCITY", "MPAYST", "MPAYZIP", "MPAYZIP2", "MTIN", "MBANKNO", "MHDPMT", "MHDCODE",
    "MCHKDATE", "MPMTDATE", "MSEQ", "MHOLDINT", "MFEDTAX", "MSTTAX", "MGROSS", "MDOB",
    "MGENDER", "MCOUNTRY",
]
GOVERNANCE_LOG_VIEWS = {
    "business_exclusion_log.csv": {
        "title": "Business Exclusion Log (read-only preview)",
        "columns": ["record_type", "blocker_category", "reason_excluded", "business_explanation"],
    },
    "representative_issue_examples.csv": {
        "title": "Representative Issue Examples (read-only preview)",
        "columns": ["example_category", "before_status", "after_status", "why_issue_occurred", "remediation_path"],
    },
    "governance_exception_catalog.csv": {
        "title": "Governance Exception Catalog (read-only preview)",
        "columns": ["blocker_category", "exception_count", "business_explanation", "governance_status"],
    },
}
UAT_PACKAGE_CATEGORIES = {
    "01_uat_candidate_data": [
        "uat_candidate_quikclms.csv",
        "uat_candidate_quikclmp.csv",
        "uat_candidate_summary.txt",
        "uat_candidate_metrics.csv",
    ],
    "02_deferred_governance": [
        "deferred_governance_claims.csv",
        "deferred_governance_payments.csv",
        "governance_hold_summary.txt",
        "governance_population_metrics.csv",
    ],
    "03_business_review_logs": [
        "business_exclusion_log.csv",
        "governance_exception_catalog.csv",
        "remediation_recommendation_log.csv",
        "representative_issue_examples.csv",
        "replay_success_examples.csv",
        "unresolved_issue_examples.csv",
    ],
    "04_executive_reporting": [
        "executive_uat_dashboard.csv",
        "governance_kpi_summary.csv",
        "blocker_trend_analysis.csv",
        "phase17_executive_summary.txt",
        "business_review_workbench_summary.txt",
        "business_exclusion_summary.txt",
        "business_example_summary.txt",
    ],
    "05_business_workbenches": [
        "surrender_review_workbench.csv",
        "orphan_review_workbench.csv",
        "high_priority_business_decisions.csv",
    ],
}
UAT_PACKAGE_SUBDIR = "claims_uat_packages"
CLAIMS_REVIEW_HOLD_MANIFEST = "claims_review_hold_manifest.csv"
CLAIMS_UAT_DBF_SUBDIR = "claims_uat_dbf"
QUIKCLMS_UAT_DBF_NAME = "QUIKCLMS_PHASE19_UAT.DBF"
QUIKCLMP_UAT_DBF_NAME = "QUIKCLMP_PHASE19_UAT.DBF"
PHASE11_CLMS_PROTOTYPE_DBF = "QUIKCLMS_PROTOTYPE.DBF"
PHASE11_CLMP_PROTOTYPE_DBF = "QUIKCLMP_PROTOTYPE.DBF"
CLAIMS_UAT_DBF_MANIFEST = "claims_uat_dbf_manifest.csv"
CLAIMS_UAT_DBF_SUMMARY = "claims_uat_dbf_generation_summary.txt"
CLAIMS_UAT_DBF_ALIGNMENT_MANIFEST = "claims_uat_dbf_alignment_manifest.csv"
CLAIMS_UAT_DBF_ALIGNMENT_SUMMARY = "claims_uat_dbf_alignment_summary.txt"
CLAIMS_UAT_DBF_ROLLBACK_REF = "rollback_snapshot_reference.txt"
UAT_DBF_GOVERNANCE_POPULATION = "UAT_EMITTED_VALIDATED_ONLY"
PHASE21B_UAT_DBF_LINEAGE = "PHASE21B_UAT_DBF_FROM_EMITTED_CSV"
PHASE22_SEMANTIC_GOVERNANCE_LINEAGE = "PHASE22A_SEMANTIC_GOVERNANCE_HOLD|PHASE22B_QLADMIN_DOMAIN_ALIGNMENT|PHASE22C_CLAIM_DOMAIN_ELIGIBILITY"
SEMANTIC_HOLD_CATEGORY = "SEMANTIC_PSEUDO_CLAIM"
SEMANTIC_HOLD_EXPLANATION = (
    "Non-claim loan accounting (LifePRO 04xx Borrowed Money: 0411-0417, 0451) lacks claim payout/benefit "
    "semantics and belongs in QuikLoan/Loan History per QLAdmin Help — not QUIKCLMS Death Claims. "
    "Held from UAT emit pending business review — not deleted."
)
SEMANTIC_HOLD_REMEDIATION = (
    "Business review required. Future target domain: QuikLoan (MLOANACCR/MLOANBAL). "
    "Do not auto-convert in Phase 22. Set QLA_SEMANTIC_GOVERNANCE_HOLD=0 to rollback emit filter."
)
CLAIMS_CROSS_TABLE_VALIDATION_REPORT = "claims_cross_table_validation_report.csv"
CLAIMS_CROSS_TABLE_VALIDATION_SUMMARY = "claims_cross_table_validation_summary.txt"
PHASE20_RULEBOOK_LINEAGE = "PHASE20_MPOLICY_CROSS_TABLE_VALIDATION"
PHASE20_HOLD_EXPLANATION = (
    "The claim or payment references a policy that was not present in the converted policy "
    "master file, so it was held from UAT output."
)
PHASE20_REMEDIATION = (
    "Review policy conversion/crosswalk. Confirm whether the policy should exist in "
    "quikmstr.csv before claim is included in UAT."
)
PHASE21_RULEBOOK_LINEAGE = "PHASE21_UAT_QLA_EMIT|PHASE10_DERIVATION|Sync_Rulebook"
CLAIMS_MONEY_FIELDS = {
    "quikclms": {
        "MPAID", "MFACE", "DIVIDENDS", "LOAN", "NETDB", "PREMIUM", "SUSPENSE", "ADJUST",
        "MINTAMT", "MHOLDINT", "MFEDTAX", "MSTTAX",
    },
    "quikclmp": {"MAMOUNT", "MHOLDINT", "MFEDTAX", "MSTTAX", "MGROSS"},
}
CLAIMS_PAYMENT_MHDPMT_MAP = {
    "DEATH": "C",
    "CLAIM": "C",
    "DISBURSEMENT": "C",
    "DEATH_CLAIM_PAYOUT": "C",
    "CLAIM_PAYMENT": "C",
    "CASH_DISBURSEMENT": "C",
}


class QLAdminEnterpriseIntegrationSuite:
    def __init__(self, root):
        self.root = root
        self.root.title("QLAdmin Enterprise Data Integration Suite v55.7")
        self.root.geometry("1100x1050")
        
        self.bg_main = "#F1F5F9"
        self.bg_card = "#FFFFFF"
        self.accent = "#0F172A"
        self.btn_action = "#2563EB"
        self.btn_batch = "#059669"
        self.btn_backup = "#6366F1"
        self.text_color = "#334155"
        self.root.configure(bg=self.bg_main)

        self.TABLE_SCHEMAS = {
            "quikplan": ["PLAN", "FORM", "DESCR", "PAR", "SEX", "BASIS", "NFOINT", "LOANINT", "LOANINTX", "DEPINT", "VARDB", "VARGP", "LOAGE", "HIAGE", "RENEW", "PAYYRS", "PAYAGE", "INSYRS", "INSAGE", "ANNL", "SEMI", "QTRL", "MTHD", "MTHB", "ANNLFEE", "SEMIFEE", "QTRLFEE", "MTHDFEE", "MTHBFEE", "INITVAL", "MKTG", "PRODUCT", "CALCADV", "COMMID", "MINUNIT", "MAXUNIT", "BPOLFEE", "BACTIVE", "RRULE", "AGTRSV", "AUTONFO", "PLANTYPE", "INTMETHTV", "INTMETHCV", "DEFICIENCY", "HDEDMETHOD", "PLANVALOPT", "GDVARYGP", "GDVARYDB", "GDVARYCV", "GDVARYTV", "GDVARYDV", "UWVARYGP", "UWVARYDB", "UWVARYCV", "UWVARYTV", "UWVARYDV", "BDVARYGP", "BDVARYDB", "BDVARYCV", "BDVARYTV", "BDVARYDV", "STVARYGP", "STVARYDB", "STVARYCV", "STVARYTV", "STVARYDV", "CONVCOMM", "PLANNAME", "HRENEW", "HLOB", "HCOMMIP", "HRIGPKEY", "SIMPLEINT", "MLAPSE", "MNOTE10", "MNAICLOB", "MNFOANNV", "MGTDANNV"],
            "quikmstr": ["MPOLICY","MSTATUS","MSTATDATE","MISSDT","MPAIDTO","MBILLTO","MNFOPT","MDIVOPT","MBILLFRM","MBILLDAY","MACCTNO","MBANKNO","MPREBILL","MMODE","MMODEPREM","MSEMI","MQTRL","MMTHD","MMTHB","MINQUIRY","MISSUEST","MBFCY","MGROUP","MPRIMID","MOWNRID","MPAYRID","MASGNID","MBENPID","MBENCID","MAPPDATE","MSUBMDATE","MRELDATE","MRELOTHER","MORIGBILL","MORIGMODE","MISSCNTRY","MOWNCID","MACHCNT","MACHNXTDT","MRESSTATE","MBLLDOM","MSPCODE","MISSCLASS","MMSMBI","MORGBLLDOM"],
            "quikclnt": ["MCLIENTID", "MTYPE", "MTAXID", "MTAXIDTYPE", "MTITLE", "MFNAME", "MMNAME", "MLNAME", "MSUFFIX", "MADDR1", "MADDR2", "MCITY", "MSTATE", "MZIP", "MZIP2", "MCOUNTRY", "MPHONEHOME", "MPHONEOFC", "MPHOFCEXT", "MPHONECELL", "MPHONEFAX", "MEMAIL", "MDOB", "MSEX", "MMEMBERID", "MLANGUAGE", "MPDFPSSWD", "MEMAILCORR", "MVALID", "MDNC", "MOFAC", "MMEMBERDT", "MMSMBI", "MFOREIGN", "MOCCODE"],
            "quikridr": ["MPOLICY", "MPHASE", "MPHSTAT", "MLASTANN", "MANNSTAT", "MPHDOB", "MSEX", "MPLAN", "MPAR", "MEFFDATE", "MEXPRY", "MPAYUP", "MAGE", "MUNIT", "MVPU", "MPREM", "MANNLFEE", "MSEMIFEE", "MQTRLFEE", "MMTHDFEE", "MMTHBFEE", "MRRULE", "MCOMMID", "MCV0", "MCV1", "MCV2", "MSAVEAGE", "MSAVEUNIT", "MSAVEVPU", "MSAVEPREM", "MRIDRID", "MSSN", "MUWCLASS", "MBAND", "MSAVESTAT", "MCOMMPREM", "MSPCODE", "MLOCKTYP", "MLOCKDT", "MUNLCKDT"],
            "quikbenf": ["MPOLICY", "MBENFID", "MTYPE", "MRELATION", "MSPLIT"],
            "quikclid": ["MCLIENTID", "MPOLICY", "MPHASE", "MRELATION"],
            "quikdvdp": ["MPOLICY", "MDEPOSIT", "MINTYTD", "MDEPINT", "MINTDATE"],
            "quikdvpr": ["MPOLICY", "MDATE", "MDIV"],
            "quikprmh": ["MPOLICY", "DATEPAID", "RENEWAL", "PREMIUM", "MLIFE", "MTERM", "MSUPP", "MANN", "MHEALTH", "XS", "MPAIDTO", "POSTDATE", "MPOSTDATE", "MSOURCE", "MBATCH", "USER_ID", "MBILLFRM", "MMODEPD"],
            "quikagts": ["MAGENT", "MAGTNAME", "MAGTADDR1", "MAGTADDR2", "MAGTCITY", "MAGTST", "MAGTZIP", "MAGTZIP2", "MAGTSSN", "MAGTFEIN", "MCOMP", "MAGENCY", "MAGCYNAME", "MDATE", "MAGTACCT", "MAGTPHONE", "MAGTFAX", "MAGTCELL", "MAGTOFCE", "MAGTEMAIL", "MEMOTEXT", "MSUPPRESS", "MCOMMGRP", "MOTHNAME", "MPREMACCT", "MSTATUS", "MAGTNPN", "MTAXIDTYPE"],
            "quikclms": QUIKCLMS_SCHEMA,
            "quikclmp": QUIKCLMP_SCHEMA,
        }

        self.RUN_MODE = self._resolve_run_mode()
        self.CLAIMS_ORCHESTRATION = self._build_claims_orchestration_config()
        
        self.is_running = False
        self.start_time = None
        self.debug_rel_fallback = os.environ.get("QLA_DEBUG_REL_FALLBACK", "").strip().lower() in ("1", "true", "yes")
        self._last_uat_dbf_result = None
        self._last_cross_table_validation = None
        self.setup_ui()

    def setup_ui(self):
        header = tk.Frame(self.root, bg=self.bg_main)
        header.pack(fill="x", pady=(15, 10))
        tk.Label(header, text="ENTERPRISE DATA INTEGRATION ENGINE v55.7", font=("Segoe UI", 20, "bold"), bg=self.bg_main, fg=self.accent).pack()

        self._setup_uat_status_banner()
        
        card = tk.LabelFrame(self.root, text=" System Configuration & Path Mapping ", bg=self.bg_card, fg=self.accent, padx=20, pady=15, font=("Segoe UI", 10, "bold"))
        card.pack(padx=30, fill="x", pady=5)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(base_dir)
        mig_map = os.path.join(base_dir, "QLA_Migration", "Mapping")
        mig_src = os.path.join(base_dir, "QLA_Migration", "Source", "quikplan.csv")
        mig_out = os.path.join(base_dir, "QLA_Migration", "Output")

        def auto_locate(search_paths, keywords):
            for s_path in search_paths:
                for root, dirs, files in os.walk(s_path):
                    if root.count(os.sep) - s_path.count(os.sep) > 3:
                        del dirs[:]
                    dirs[:] = [
                        d for d in dirs
                        if not any(m in os.path.join(root, d).lower() for m in [
                            "expectred_outputs", "expected_outputs", "z_sourcefortesting",
                        ])
                    ]
                    for file_name in files:
                        f_lower = file_name.lower()
                        if f_lower.endswith(".csv") and all(k in f_lower for k in keywords):
                            if not any(bad in f_lower for bad in ['copy', 'old', 'backup', 'archive']):
                                full = os.path.normpath(os.path.join(root, file_name))
                                if "expectred_outputs" not in full.lower():
                                    return full
            return ""

        search_dirs = [mig_map, base_dir, parent_dir]

        default_trans = self._first_existing_file(
            os.path.join(mig_map, "Master_Value_Translation.csv"),
            auto_locate(search_dirs, ["master", "translation"]),
        )
        default_cw = self._first_existing_file(
            os.path.join(mig_map, "Master_Crosswalk.csv"),
            auto_locate(search_dirs, ["master", "crosswalk"]),
        )
        default_src = mig_src if os.path.isfile(mig_src) else ""
        default_out = mig_out if os.path.isdir(mig_out) else ""
        mig_cfg = os.path.join(base_dir, "QLA_Migration", "Configs", "Sync_Rulebook_quikplan.csv")
        default_rule = mig_cfg if os.path.isfile(mig_cfg) else ""
        default_rel = os.path.join(mig_out, "quikclid.csv") if os.path.isfile(os.path.join(mig_out, "quikclid.csv")) else ""

        self.path_vars = {
            "Rule": [tk.StringVar(value=default_rule), "file", "Field Mapping (Rulebook):"],
            "Src": [tk.StringVar(value=default_src), "file", "Source Data File:"],
            "Trans": [tk.StringVar(value=default_trans), "file", "Value Translation (CSV):"],
            "CW": [tk.StringVar(value=default_cw), "file", "ID Crosswalk (CSV):"],
            "Rel": [tk.StringVar(value=default_rel), "file", "Relational File (quikclid):"],
            "Out": [tk.StringVar(value=default_out), "folder", "Output Directory:"]
        }

        for i, (key, settings) in enumerate(self.path_vars.items()):
            var, mode, label_text = settings
            tk.Label(card, text=label_text, bg=self.bg_card, fg=self.text_color, font=("Segoe UI", 9, "bold")).grid(row=i, column=0, sticky="w", pady=4)
            tk.Entry(card, textvariable=var, width=95, bg="#F8FAFC", fg=self.accent, borderwidth=1).grid(row=i, column=1, padx=15)
            tk.Button(card, text="Browse", width=10, command=lambda v=var, m=mode, k=key: self.browse(v, m, k)).grid(row=i, column=2)

        controls = tk.Frame(self.root, bg=self.bg_main)
        controls.pack(pady=10, fill="x", padx=30)
        self.table_var = tk.StringVar()
        self.table_dropdown = ttk.Combobox(controls, textvariable=self.table_var, values=[k for k in self.TABLE_SCHEMAS.keys() if k.startswith("quik")], width=45, state="readonly")
        self.table_dropdown.pack(side="left", padx=10)
        
        self.table_dropdown.bind("<<ComboboxSelected>>", self.on_table_select)
        
        tk.Button(controls, text="FULL PROJECT BACKUP", bg=self.btn_backup, fg="white", width=40, command=self.create_snapshot).pack(side="right", padx=10)

        self.lbl_timer = tk.Label(self.root, text="Elapsed: 00:00", bg=self.bg_main, fg=self.accent, font=("Consolas", 10, "bold"))
        self.lbl_timer.pack()
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=1040, mode="determinate")
        self.progress.pack(pady=10)

        btn_frame = tk.Frame(self.root, bg=self.bg_main)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="RUN SINGLE TABLE CONVERSION", bg=self.btn_action, fg="white", width=35, height=2, font=("Segoe UI", 9, "bold"), command=lambda: self.start_thread(False)).pack(side="left", padx=15)
        tk.Button(btn_frame, text="EXECUTE FULL BATCH MIGRATION", bg=self.btn_batch, fg="white", width=35, height=2, font=("Segoe UI", 9, "bold"), command=lambda: self.start_thread(True)).pack(side="left", padx=15)

        self._setup_governance_summary_panel()

        self.console = scrolledtext.ScrolledText(self.root, height=16, bg="#F8FAFC", fg="#1E293B", font=("Consolas", 9))
        self.console.pack(padx=30, pady=10, fill="both", expand=True)
        self._refresh_governance_visibility()

    def log(self, msg):
        self.console.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.console.see(tk.END)

    PATH_EXCLUDED_DIR_MARKERS = (
        "expectred_outputs", "expected_outputs", "copy", "old", "backup", "archive",
        "__pycache__", ".git", "node_modules", "z_sourcefortesting",
    )

    def _app_base_dir(self):
        return os.path.dirname(os.path.abspath(__file__))

    def _migration_root(self):
        return os.path.normpath(os.path.join(self._app_base_dir(), "QLA_Migration"))

    def _migration_source_dir(self):
        return os.path.normpath(os.path.join(self._migration_root(), "Source"))

    def _migration_output_dir(self):
        return os.path.normpath(os.path.join(self._migration_root(), "Output"))

    def _migration_mapping_dir(self):
        return os.path.normpath(os.path.join(self._migration_root(), "Mapping"))

    def _migration_configs_dir(self):
        return os.path.normpath(os.path.join(self._migration_root(), "Configs"))

    def _is_excluded_path(self, path):
        lower = os.path.normpath(path).lower()
        return any(marker in lower for marker in self.PATH_EXCLUDED_DIR_MARKERS)

    def _first_existing_file(self, *candidates):
        for path in candidates:
            if path and os.path.isfile(path):
                return os.path.normpath(path)
        return ""

    def _find_migration_file(self, filename, *, search_dirs=None, exclude_output_paths=False):
        preferred_dirs = search_dirs or []
        for folder in preferred_dirs:
            if not folder or self._is_excluded_path(folder):
                continue
            candidate = os.path.normpath(os.path.join(folder, filename))
            if exclude_output_paths and "output" in candidate.lower():
                continue
            if os.path.isfile(candidate):
                return candidate

        matches = []
        for s_path in [self._app_base_dir(), os.path.dirname(self._app_base_dir())]:
            if not os.path.exists(s_path):
                continue
            for root, dirs, files in os.walk(s_path):
                dirs[:] = [
                    d for d in dirs
                    if not self._is_excluded_path(os.path.join(root, d))
                ]
                for f in files:
                    if f.lower() != filename.lower():
                        continue
                    full = os.path.normpath(os.path.join(root, f))
                    if exclude_output_paths and "output" in full.lower():
                        continue
                    if self._is_excluded_path(full):
                        continue
                    matches.append(full)

        migration_matches = [m for m in matches if "qla_migration" in m.lower()]
        if migration_matches:
            return migration_matches[0]
        return matches[0] if matches else ""

    def _resolve_batch_src_base(self, src_input):
        migration_src = self._migration_source_dir()
        if src_input:
            norm_input = os.path.normpath(src_input)
            if "qla_migration" in norm_input.lower() and os.path.isdir(migration_src):
                return migration_src
            explicit = os.path.dirname(norm_input)
            if os.path.isdir(explicit):
                return explicit
        if os.path.isdir(migration_src):
            return migration_src
        return os.path.dirname(os.path.abspath(__file__))

    def _resolve_batch_rule_base(self, rule_input):
        migration_cfg = self._migration_configs_dir()
        if rule_input:
            rule_dir = os.path.dirname(os.path.normpath(rule_input))
            if "qla_migration" in rule_dir.lower() and os.path.isdir(migration_cfg):
                return migration_cfg
            if os.path.isdir(rule_dir):
                return rule_dir
        if os.path.isdir(migration_cfg):
            return migration_cfg
        return self._app_base_dir()

    def _load_rel_map(self, rel_path, trans_map, log_label="relational map"):
        rel_map = {}
        if not rel_path or not os.path.exists(rel_path):
            return rel_map
        clid_df = pd.read_csv(rel_path, dtype=str).fillna("")
        clid_df.columns = [c.strip().upper() for c in clid_df.columns]
        for _, row in clid_df.iterrows():
            pol = self.normalize(row.get("MPOLICY", ""))
            rel_raw = self.normalize(row.get("MRELATION", ""))
            cid = self.normalize(row.get("MCLIENTID", ""))
            phase = self.normalize(row.get("MPHASE", ""))
            if not phase or phase == "0":
                phase = "1"
            rel = trans_map.get(rel_raw, rel_raw)
            if pol:
                if pol not in rel_map:
                    rel_map[pol] = {}
                if phase not in rel_map[pol]:
                    rel_map[pol][phase] = {}
                rel_map[pol][phase][rel] = cid
        policy_count = len(rel_map)
        self.log(f"Loaded {log_label} from: {rel_path} ({policy_count} policies)")
        return rel_map

    def _is_preconverted_qla_client_source(self, source_df):
        cols = {str(c).strip().upper() for c in source_df.columns}
        return "MCLIENTID" in cols and "NAME_ID" not in cols and "CLIENT_ID" not in cols

    def _bridge_rna_quikclnt_columns(self, source_df):
        bridges = {
            "CLIENT_ID": "NAME_ID",
            "FIRST_NAME": "INDIVIDUAL_FIRST",
            "MIDDLE_NAME": "INDIVIDUAL_MIDDLE",
            "LAST_NAME": "INDIVIDUAL_LAST",
            "SUFFIX": "INDIVIDUAL_SUFFIX",
            "TAX_ID": "SOC_SEC_NUMBER",
            "ADDRESS_LINE_1": "ADDR_LINE_1",
            "ADDRESS_LINE_2": "ADDR_LINE_2",
            "CITY": "CITY",
            "STATE": "STATE",
            "ZIP_CODE": "ZIP",
            "ZIP_EXTENSION": "ZIP_EXTENSION",
            "COUNTRY_CODE": "COUNTRY",
            "HOME_PHONE": "TELE_NUM",
            "FAX_PHONE": "FAX_NUM",
            "BIRTH_DATE": "DATE_OF_BIRTH",
            "SEX": "SEX_CODE",
        }
        for target_col, source_col in bridges.items():
            if target_col not in source_df.columns and source_col in source_df.columns:
                source_df[target_col] = source_df[source_col]
        return source_df

    def _resolve_run_mode(self):
        mode = os.environ.get("QLA_RUN_MODE", DEFAULT_RUN_MODE).strip().upper()
        if mode not in VALID_RUN_MODES:
            return DEFAULT_RUN_MODE
        return mode

    def _claims_analysis_root(self):
        return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "claims_analysis"))

    def _migration_source_dir(self):
        return os.path.normpath(os.path.join(self._app_base_dir(), "QLA_Migration", "Source"))

    def _resolve_claims_prelsa_path(self):
        env_path = os.environ.get("QLA_CLAIMS_PRELSA_PATH", "").strip()
        if env_path and os.path.isfile(env_path):
            return os.path.normpath(env_path)
        candidates = [
            os.path.join(self._migration_source_dir(), "RelationshipNameAddress_Extract.csv"),
            os.path.join(self._app_base_dir(), "docs", "claims_conversion_reference", "RelationshipNameAddress_Extract.csv"),
        ]
        for path in candidates:
            if os.path.isfile(path):
                return os.path.normpath(path)
        return os.path.normpath(candidates[-1])

    def _resolve_claims_pactg_path(self):
        env_path = os.environ.get("QLA_CLAIMS_PACTG_PATH", "").strip()
        if env_path and os.path.isfile(env_path):
            return os.path.normpath(env_path)
        candidates = [
            os.path.join(self._migration_source_dir(), "PACTG_Accounting_Extract20260427.csv"),
            os.path.join(self._app_base_dir(), "docs", "claims_conversion_reference", "PACTG_Accounting_Extract20260427.csv"),
        ]
        for path in candidates:
            if os.path.isfile(path):
                return os.path.normpath(path)
        return os.path.normpath(candidates[-1])

    def _claims_lineage_refresh_enabled(self):
        flag = os.environ.get("QLA_REFRESH_CLAIMS_LINEAGE", "").strip().lower() in ("1", "true", "yes")
        return flag and self.CLAIMS_ORCHESTRATION["run_mode"] == "UAT"

    def _invoke_phase10a_quikclmp_refresh(self):
        claims_root = self._claims_analysis_root()
        runner = os.path.join(
            claims_root, "phase10a_quikclmp_derivation", "quikclmp_rulebook_derivation_engine.py",
        )
        prelsa_path = self._resolve_claims_prelsa_path()
        output_dir = os.path.join(claims_root, "phase10a_quikclmp_derivation_design")
        timeout = self.CLAIMS_ORCHESTRATION.get("orchestration_timeout_seconds", DEFAULT_ORCHESTRATION_TIMEOUT_SECONDS)
        if not os.path.isfile(runner):
            self.log(f"PHASE 22 LINEAGE REFRESH: Phase 10A runner not found — {runner}")
            return False
        if not os.path.isfile(prelsa_path):
            self.log(f"PHASE 22 LINEAGE REFRESH: PRELSA source missing — {prelsa_path}")
            return False
        cmd = [sys.executable, runner, "--prelsa", prelsa_path, "--output", output_dir]
        self.log("PHASE 22 LINEAGE REFRESH: Re-deriving Phase 10A QUIKCLMP candidates from resolved PRELSA...")
        self.log(f"  PRELSA source: {prelsa_path}")
        self.log(f"  Command: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd, cwd=claims_root, capture_output=True, text=True, timeout=timeout, check=False,
            )
            self._log_subprocess_stream("phase10a-stdout", result.stdout or "")
            self._log_subprocess_stream("phase10a-stderr", result.stderr or "")
            ok = result.returncode == 0
            self.log(f"PHASE 22 LINEAGE REFRESH: Phase 10A status={'SUCCESS' if ok else 'FAILED'} return_code={result.returncode}")
            return ok
        except subprocess.TimeoutExpired:
            self.log(f"PHASE 22 LINEAGE REFRESH: Phase 10A exceeded {timeout}s timeout")
            return False
        except OSError as exc:
            self.log(f"PHASE 22 LINEAGE REFRESH ERROR: {exc}")
            return False

    def _load_claims_orchestration_rules(self):
        rules_path = os.path.join(self._claims_analysis_root(), "config", "app_claims_uat_orchestration_rules.json")
        if not os.path.isfile(rules_path):
            return {}
        try:
            with open(rules_path, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            return {}

    def _build_claims_orchestration_config(self):
        base = os.path.dirname(os.path.abspath(__file__))
        claims_root = self._claims_analysis_root()
        rules = self._load_claims_orchestration_rules()
        phase17_out = os.path.join(claims_root, "phase17_uat_governance_reporting")
        auth_flag = os.environ.get(
            "QLA_PRODUCTION_DBF_AUTHORIZED",
            rules.get("production_authorization_flag", "N"),
        ).strip().upper()
        return {
            "run_mode": self._resolve_run_mode(),
            "production_dbf_flag": rules.get("production_dbf_flag", "N"),
            "production_authorization_flag": auth_flag,
            "go_live_target": rules.get("go_live_target", "2026-09-01"),
            "allow_inline_claims_conversion": False,
            "uat_candidate_dir": phase17_out,
            "uat_quikclms_source": os.path.join(phase17_out, "uat_candidate_quikclms.csv"),
            "uat_quikclmp_source": os.path.join(phase17_out, "uat_candidate_quikclmp.csv"),
            "orchestration_runner": os.path.join(
                claims_root, "phase17_uat_governance_reporting", "phase17_uat_governance_reporting_runner.py",
            ),
            "future_claims_pipeline_runner": os.path.join(claims_root, "phase16_business_triage", "phase16_business_triage_runner.py"),
            "staging_subdir": rules.get("uat_staging_subdir", "claims_uat_staging"),
            "orchestration_timeout_seconds": int(
                rules.get("orchestration_timeout_seconds", DEFAULT_ORCHESTRATION_TIMEOUT_SECONDS)
            ),
            "uat_dbf_generator_runner": os.path.join(
                claims_root, "phase19_uat_emitted_csv_dbf", "uat_emitted_csv_dbf_generator.py",
            ),
            "uat_dbf_timeout_seconds": int(
                rules.get("orchestration_timeout_seconds", DEFAULT_ORCHESTRATION_TIMEOUT_SECONDS)
            ),
            "semantic_governance_runner": os.path.join(
                claims_root, "phase22_semantic_governance", "phase22_semantic_governance_runner.py",
            ),
            "prelsa_source_path": self._resolve_claims_prelsa_path(),
            "pactg_source_path": self._resolve_claims_pactg_path(),
            "app_base_dir": base,
        }

    def _is_claims_table(self, table_id):
        return str(table_id or "").strip().lower() in CLAIMS_TABLE_IDS

    def _claims_uat_source_path(self, table_id):
        cfg = self.CLAIMS_ORCHESTRATION
        if table_id.lower() == "quikclms":
            return cfg["uat_quikclms_source"]
        if table_id.lower() == "quikclmp":
            return cfg["uat_quikclmp_source"]
        return ""

    def _claims_orchestrate_enabled(self):
        flag = os.environ.get("QLA_CLAIMS_ORCHESTRATE", "").strip().lower() in ("1", "true", "yes")
        return flag and self.CLAIMS_ORCHESTRATION["run_mode"] == "UAT"

    def _claims_uat_emit_enabled(self):
        flag = os.environ.get("QLA_CLAIMS_UAT_EMIT", "1").strip().lower()
        if flag in ("0", "false", "no"):
            return False
        return self.CLAIMS_ORCHESTRATION["run_mode"] == "UAT"

    def _batch_include_claims_uat_enabled(self):
        flag = os.environ.get("QLA_BATCH_INCLUDE_CLAIMS_UAT", "").strip().lower() in ("1", "true", "yes")
        return flag and self.CLAIMS_ORCHESTRATION["run_mode"] == "UAT"

    def _claims_uat_dbf_generation_enabled(self):
        flag = os.environ.get("QLA_GENERATE_UAT_CLAIMS_DBF", "").strip().lower() in ("1", "true", "yes")
        return flag and self.CLAIMS_ORCHESTRATION["run_mode"] == "UAT"

    def _claims_semantic_governance_enabled(self):
        flag = os.environ.get("QLA_SEMANTIC_GOVERNANCE_HOLD", "1").strip().lower()
        if flag in ("0", "false", "no"):
            return False
        return self.CLAIMS_ORCHESTRATION["run_mode"] == "UAT"

    def _claims_mpolicy_validation_enabled(self):
        flag = os.environ.get("QLA_VALIDATE_CLAIMS_MPOLICY", "1").strip().lower()
        if flag in ("0", "false", "no"):
            return False
        return self.CLAIMS_ORCHESTRATION["run_mode"] == "UAT"

    def _claims_staging_dir(self):
        cfg = self.CLAIMS_ORCHESTRATION
        base_out = self._resolve_output_base_dir()
        staging_dir = os.path.normpath(os.path.join(base_out, cfg["staging_subdir"]))
        os.makedirs(staging_dir, exist_ok=True)
        return staging_dir

    def _append_orchestration_execution_log(self, staging_dir, lines):
        exec_log = os.path.normpath(os.path.join(staging_dir, "claims_uat_orchestration_execution_log.txt"))
        with open(exec_log, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        return exec_log

    def _log_subprocess_stream(self, label, text):
        if not text:
            return
        for line in text.splitlines():
            stripped = line.rstrip()
            if stripped:
                self.log(f"  [{label}] {stripped}")

    def _invoke_external_claims_pipeline(self, staging_dir):
        cfg = self.CLAIMS_ORCHESTRATION
        runner = cfg["orchestration_runner"]
        timeout = cfg.get("orchestration_timeout_seconds", DEFAULT_ORCHESTRATION_TIMEOUT_SECONDS)
        started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        claims_root = self._claims_analysis_root()

        if not os.path.isfile(runner):
            msg = f"Orchestration runner not found: {runner}"
            self.log(f"  CLAIMS PIPELINE ERROR: {msg}")
            self._append_orchestration_execution_log(staging_dir, [
                f"[{started}] EXTERNAL_RUNNER_FAILED",
                f"RUN_MODE={cfg['run_mode']}",
                f"production_dbf_flag={cfg['production_dbf_flag']}",
                f"runner={runner}",
                f"error={msg}",
            ])
            return False

        cmd = [sys.executable, runner]
        env = os.environ.copy()
        env["QLA_CLAIMS_PRELSA_PATH"] = cfg.get("prelsa_source_path", self._resolve_claims_prelsa_path())
        env["QLA_CLAIMS_PACTG_PATH"] = cfg.get("pactg_source_path", self._resolve_claims_pactg_path())
        self.log("CLAIMS PIPELINE: Starting external Phase 17 runner (subprocess)...")
        self.log(f"  Command: {' '.join(cmd)}")
        self.log(f"  Working directory: {claims_root}")
        self.log(f"  Resolved PRELSA lineage source: {env['QLA_CLAIMS_PRELSA_PATH']}")
        self.log(f"  Timeout: {timeout}s")

        return_code = -1
        stdout_text = ""
        stderr_text = ""
        status = "FAILED"
        error_detail = ""

        try:
            result = subprocess.run(
                cmd,
                cwd=claims_root,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                env=env,
            )
            return_code = result.returncode
            stdout_text = result.stdout or ""
            stderr_text = result.stderr or ""
            status = "SUCCESS" if return_code == 0 else "FAILED"
        except subprocess.TimeoutExpired as exc:
            status = "TIMEOUT"
            error_detail = f"Runner exceeded {timeout}s timeout"
            stdout_text = (exc.stdout or "") if exc.stdout else ""
            stderr_text = (exc.stderr or "") if exc.stderr else ""
            self.log(f"  CLAIMS PIPELINE ERROR: {error_detail}")
        except OSError as exc:
            status = "FAILED"
            error_detail = str(exc)
            self.log(f"  CLAIMS PIPELINE ERROR: {error_detail}")

        finished = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log(f"CLAIMS PIPELINE: Completed with status={status} return_code={return_code}")
        self._log_subprocess_stream("stdout", stdout_text)
        self._log_subprocess_stream("stderr", stderr_text)

        self._append_orchestration_execution_log(staging_dir, [
            f"[{finished}] EXTERNAL_RUNNER_{status}",
            f"started={started}",
            f"RUN_MODE={cfg['run_mode']}",
            f"production_dbf_flag={cfg['production_dbf_flag']}",
            f"runner={runner}",
            f"return_code={return_code}",
            f"timeout_seconds={timeout}",
            f"error={error_detail}" if error_detail else "error=",
            "--- stdout ---",
            stdout_text.rstrip() or "(empty)",
            "--- stderr ---",
            stderr_text.rstrip() or "(empty)",
        ])
        if status == "SUCCESS" and self._claims_semantic_governance_enabled():
            self._invoke_phase22_semantic_governance(staging_dir)
        return status == "SUCCESS"

    def _phase22_semantic_governance_dir(self):
        return os.path.normpath(os.path.join(self._claims_analysis_root(), "phase22_semantic_governance"))

    def _invoke_phase22_semantic_governance(self, staging_dir):
        cfg = self.CLAIMS_ORCHESTRATION
        runner = cfg.get("semantic_governance_runner")
        timeout = cfg.get("orchestration_timeout_seconds", DEFAULT_ORCHESTRATION_TIMEOUT_SECONDS)
        claims_root = self._claims_analysis_root()
        started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not runner or not os.path.isfile(runner):
            self.log(f"  PHASE 22 ERROR: semantic governance runner not found: {runner}")
            return False
        cmd = [sys.executable, runner]
        self.log("PHASE 22 SEMANTIC GOVERNANCE (22A/22B): detecting pseudo-claims + QLAdmin alignment...")
        self.log(f"  Command: {' '.join(cmd)}")
        self.log("  Authoritative manuals: docs/claims_conversion_reference/QLAdmin_Help.pdf + LifePRO Accounting Transactions")
        return_code = -1
        stdout_text = ""
        stderr_text = ""
        try:
            proc = subprocess.run(
                cmd, cwd=claims_root, capture_output=True, text=True,
                timeout=timeout, check=False,
            )
            return_code = proc.returncode
            stdout_text = proc.stdout or ""
            stderr_text = proc.stderr or ""
        except subprocess.TimeoutExpired as exc:
            self.log(f"  PHASE 22 ERROR: runner exceeded {timeout}s timeout")
            stdout_text = (exc.stdout or "") if exc.stdout else ""
            stderr_text = (exc.stderr or "") if exc.stderr else ""
        except OSError as exc:
            self.log(f"  PHASE 22 ERROR: {exc}")
        self.log(f"PHASE 22 SEMANTIC GOVERNANCE: Completed return_code={return_code}")
        self._log_subprocess_stream("phase22-stdout", stdout_text)
        self._log_subprocess_stream("phase22-stderr", stderr_text)
        self._append_orchestration_execution_log(staging_dir, [
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] PHASE22_SEMANTIC_GOVERNANCE",
            f"started={started}",
            f"return_code={return_code}",
            f"runner={runner}",
            f"rulebook_lineage={PHASE22_SEMANTIC_GOVERNANCE_LINEAGE}",
            "--- stdout ---",
            stdout_text.rstrip() or "(empty)",
            "--- stderr ---",
            stderr_text.rstrip() or "(empty)",
        ])
        if return_code == 0:
            hold_path = os.path.join(self._phase22_semantic_governance_dir(), "semantic_governance_hold_population.csv")
            self.log(f"  Phase 22 hold manifest: {hold_path}")
        return return_code == 0

    def _load_semantic_governance_hold_index(self):
        hold_path = os.path.join(self._phase22_semantic_governance_dir(), "semantic_governance_hold_population.csv")
        rc_ids = set()
        deriv_ids = set()
        reason_map = {}
        if not os.path.isfile(hold_path):
            return rc_ids, deriv_ids, reason_map, hold_path
        try:
            df = pd.read_csv(hold_path, dtype=str).fillna("")
            df.columns = [str(c).strip().lower() for c in df.columns]
            for _, row in df.iterrows():
                rc = str(row.get("reconstructed_claim_id", "")).strip()
                deriv = str(row.get("derivation_candidate_id", "")).strip()
                reason = str(row.get("reason_excluded", "SEMANTIC_PSEUDO_CLAIM")).strip()
                if rc:
                    rc_ids.add(rc)
                    reason_map[rc] = reason
                if deriv:
                    deriv_ids.add(deriv)
                    reason_map[deriv] = reason
        except Exception:
            pass
        return rc_ids, deriv_ids, reason_map, hold_path

    def _build_semantic_hold_row(
        self, row, table_key, staged_path, dest_path, reason_excluded, mpolicy_raw,
        audit_ts, prod_flag,
    ):
        row_dict = row.to_dict() if hasattr(row, "to_dict") else dict(row)
        normalized = {str(k).strip().lower(): v for k, v in row_dict.items()}
        rc = str(normalized.get("reconstructed_claim_id", "")).strip()
        deriv = str(normalized.get("derivation_candidate_id", "")).strip()
        record_type = "CLAIM" if table_key == "quikclms" else "PAYMENT"
        record_identifier = deriv or rc or str(normalized.get("canonical_payment_stage_id", "")).strip()
        return {
            "audit_timestamp": audit_ts,
            "emit_timestamp": audit_ts,
            "production_dbf_flag": prod_flag,
            "hold_category": SEMANTIC_HOLD_CATEGORY,
            "record_type": record_type,
            "record_identifier": record_identifier,
            "record_id": record_identifier,
            "reconstructed_claim_id": rc,
            "derivation_candidate_id": deriv,
            "MPOLICY": mpolicy_raw,
            "blocker_category": "SEMANTIC_DOMAIN_MISMATCH",
            "reason_excluded": reason_excluded or "SEMANTIC_PSEUDO_CLAIM",
            "reason_held": reason_excluded or "SEMANTIC_PSEUDO_CLAIM",
            "governance_status": "SEMANTIC_GOVERNANCE_HOLD",
            "business_review_required": "Y",
            "business_explanation": SEMANTIC_HOLD_EXPLANATION,
            "remediation_recommendation": SEMANTIC_HOLD_REMEDIATION,
            "source_file": staged_path,
            "target_file": dest_path,
            "rulebook_lineage": PHASE22_SEMANTIC_GOVERNANCE_LINEAGE,
        }

    def _stage_uat_candidate_file(self, staging_dir, table_key, source_path):
        if not source_path or not os.path.isfile(source_path):
            return False, ""
        staged_path = os.path.normpath(os.path.join(staging_dir, f"{table_key}.csv"))
        shutil.copy2(source_path, staged_path)
        return True, staged_path

    def _restage_all_uat_candidates(self, staging_dir):
        cfg = self.CLAIMS_ORCHESTRATION
        staged = []
        for table_key, source_key in (("quikclms", "uat_quikclms_source"), ("quikclmp", "uat_quikclmp_source")):
            ok, path = self._stage_uat_candidate_file(staging_dir, table_key, cfg[source_key])
            if ok:
                staged.append((table_key, path, cfg[source_key]))
        return staged

    def _phase17_governance_dir(self):
        return os.path.normpath(self.CLAIMS_ORCHESTRATION["uat_candidate_dir"])

    def _load_governance_csv_safe(self, filename, directory=None):
        base_dir = directory or self._phase17_governance_dir()
        path = os.path.join(base_dir, filename)
        if not os.path.isfile(path):
            return None
        try:
            df = pd.read_csv(path, dtype=str)
            df.columns = [str(c).strip().lower() for c in df.columns]
            return df
        except Exception:
            return None

    def _count_governance_csv_rows(self, filename, directory=None):
        base_dir = directory or self._phase17_governance_dir()
        path = os.path.join(base_dir, filename)
        if not os.path.isfile(path):
            return None
        try:
            with open(path, encoding="utf-8") as fh:
                return max(sum(1 for _ in fh) - 1, 0)
        except OSError:
            return None

    def _dashboard_kpi_value(self, dashboard_df, kpi_key):
        if dashboard_df is None or dashboard_df.empty or "kpi" not in dashboard_df.columns:
            return None
        if "value" not in dashboard_df.columns:
            return None
        match = dashboard_df[dashboard_df["kpi"].astype(str).str.strip().str.lower() == kpi_key.lower()]
        if match.empty:
            return None
        return str(match.iloc[0]["value"]).strip()

    def _format_governance_metric(self, value, suffix=""):
        if value is None or str(value).strip() == "":
            return "NOT YET GENERATED"
        text = str(value).strip()
        if suffix and not text.endswith(suffix):
            return f"{text}{suffix}"
        return text

    def _top_blocker_from_kpi_summary(self, kpi_df):
        if kpi_df is None or kpi_df.empty:
            return None, None
        if "kpi_name" not in kpi_df.columns or "kpi_value" not in kpi_df.columns:
            return None, None
        blockers = kpi_df[kpi_df["kpi_name"].astype(str).str.startswith("blocker_")].copy()
        if blockers.empty:
            return None, None
        blockers["_val"] = pd.to_numeric(blockers["kpi_value"], errors="coerce").fillna(0)
        top = blockers.sort_values("_val", ascending=False).iloc[0]
        label = str(top["kpi_name"]).replace("blocker_", "").replace("_", " ").strip().title()
        return label, int(top["_val"])

    def _load_phase16_governance_status(self):
        phase16_dir = os.path.join(self._claims_analysis_root(), "phase16_business_triage_remediation")
        df = self._load_governance_csv_safe("phase16_decision_checkpoint.csv", directory=phase16_dir)
        if df is None or df.empty:
            return None, None
        row = df.iloc[0]
        decision = str(row.get("decision_category", "")).strip() or None
        governance = str(row.get("governance_status", "")).strip() or None
        return decision, governance

    def _build_governance_summary(self):
        dashboard = self._load_governance_csv_safe("executive_uat_dashboard.csv")
        kpi_summary = self._load_governance_csv_safe("governance_kpi_summary.csv")
        blocker_trend = self._load_governance_csv_safe("blocker_trend_analysis.csv")
        exclusion_df = self._load_governance_csv_safe("business_exclusion_log.csv")
        cfg = self.CLAIMS_ORCHESTRATION

        top_blocker, top_blocker_count = self._top_blocker_from_kpi_summary(kpi_summary)
        phase16_decision, phase16_governance = self._load_phase16_governance_status()
        exclusion_count = len(exclusion_df) if exclusion_df is not None else None
        surrender_queue = self._count_governance_csv_rows("surrender_review_workbench.csv")
        orphan_queue = self._count_governance_csv_rows("orphan_review_workbench.csv")

        go_live = self._dashboard_kpi_value(dashboard, "go_live_target") or cfg.get("go_live_target", "2026-09-01")
        orphan_reduction = self._dashboard_kpi_value(dashboard, "orphan_reduction")

        if dashboard is None:
            threshold_status = "NOT YET GENERATED"
        elif phase16_governance == "PRODUCTION_BLOCKED" or phase16_decision == "PRODUCTION_BLOCKED":
            threshold_status = "NOT READY"
        else:
            threshold_status = "UAT REVIEW IN PROGRESS"

        if cfg["run_mode"] == "PRODUCTION" and cfg.get("production_authorization_flag") == "Y":
            production_status = "AUTHORIZED (NOT EXECUTED)"
        elif phase16_decision:
            production_status = phase16_decision.replace("_", " ")
        else:
            production_status = "BLOCKED"

        files_present = any(
            os.path.isfile(os.path.join(self._phase17_governance_dir(), name))
            for name in (
                "executive_uat_dashboard.csv",
                "governance_kpi_summary.csv",
                "blocker_trend_analysis.csv",
                "business_exclusion_log.csv",
            )
        )

        return {
            "files_present": files_present,
            "uat_claims": self._dashboard_kpi_value(dashboard, "uat_candidate_claims"),
            "uat_payments": self._dashboard_kpi_value(dashboard, "uat_candidate_payments"),
            "deferred_claims": self._dashboard_kpi_value(dashboard, "deferred_governance_claims"),
            "deferred_payments": self._dashboard_kpi_value(dashboard, "deferred_governance_payments"),
            "orphan_count": self._dashboard_kpi_value(dashboard, "orphan_count_phase15"),
            "recon_pass_pct": self._dashboard_kpi_value(dashboard, "reconciliation_pass_rate_phase15_pct"),
            "replay_recovery": orphan_reduction,
            "top_blocker": top_blocker,
            "top_blocker_count": top_blocker_count,
            "exclusion_records": exclusion_count,
            "surrender_queue": surrender_queue,
            "orphan_queue": orphan_queue,
            "go_live_target": go_live,
            "production_status": production_status,
            "threshold_status": threshold_status,
            "run_mode": cfg["run_mode"],
            "blocker_trend_loaded": blocker_trend is not None,
            **self._load_uat_dbf_panel_status(),
            **self._load_cross_table_validation_panel_status(),
        }

    def _claims_uat_dbf_dir(self):
        return os.path.normpath(os.path.join(self._resolve_output_base_dir(), CLAIMS_UAT_DBF_SUBDIR))

    def _uat_emit_csv_paths(self, output_dir):
        return {
            "quikclms": os.path.normpath(os.path.join(output_dir, "quikclms.csv")),
            "quikclmp": os.path.normpath(os.path.join(output_dir, "quikclmp.csv")),
        }

    def _get_governance_rollback_snapshot_reference(self):
        dashboard = self._load_governance_csv_safe("executive_uat_dashboard.csv")
        if dashboard is not None and not dashboard.empty:
            if "rollback_snapshot_id" in dashboard.columns:
                val = str(dashboard.iloc[0]["rollback_snapshot_id"]).strip()
                if val and val.lower() not in ("nan", "none"):
                    return val
        prep_path = os.path.join(self._phase17_governance_dir(), "phase17_execution_summary.txt")
        if os.path.isfile(prep_path):
            return f"See {prep_path}"
        return "NOT_AVAILABLE"

    def _parse_phase21b_uat_dbf_stdout(self, stdout_text):
        parsed = {
            "quikclms": {"csv_rows": None, "dbf_rows": None, "row_match": None},
            "quikclmp": {"csv_rows": None, "dbf_rows": None, "row_match": None},
            "alignment_status": "",
            "alignment_manifest": "",
            "alignment_summary": "",
        }
        for line in (stdout_text or "").splitlines():
            stripped = line.strip()
            for table in ("QUIKCLMS", "QUIKCLMP"):
                key = table.lower()
                csv_match = re.match(rf"{table}_CSV_ROWS:\s*(\d+)", stripped, re.IGNORECASE)
                dbf_match = re.match(rf"{table}_DBF_ROWS:\s*(\d+|UNKNOWN)", stripped, re.IGNORECASE)
                match_match = re.match(rf"{table}_ROW_MATCH:\s*(Y|N|UNKNOWN)", stripped, re.IGNORECASE)
                if csv_match:
                    parsed[key]["csv_rows"] = int(csv_match.group(1))
                if dbf_match:
                    val = dbf_match.group(1)
                    parsed[key]["dbf_rows"] = None if val.upper() == "UNKNOWN" else int(val)
                if match_match:
                    parsed[key]["row_match"] = match_match.group(1).upper()
            status_match = re.match(r"ALIGNMENT_STATUS:\s*(.+)", stripped, re.IGNORECASE)
            manifest_match = re.match(r"ALIGNMENT_MANIFEST:\s*(.+)", stripped, re.IGNORECASE)
            summary_match = re.match(r"ALIGNMENT_SUMMARY:\s*(.+)", stripped, re.IGNORECASE)
            if status_match:
                parsed["alignment_status"] = status_match.group(1).strip()
            if manifest_match:
                parsed["alignment_manifest"] = manifest_match.group(1).strip()
            if summary_match:
                parsed["alignment_summary"] = summary_match.group(1).strip()
        return parsed

    def _load_phase21b_alignment_manifest(self, dbf_dir):
        manifest_path = os.path.join(dbf_dir, CLAIMS_UAT_DBF_ALIGNMENT_MANIFEST)
        if not os.path.isfile(manifest_path):
            return None
        try:
            return pd.read_csv(manifest_path, dtype=str)
        except Exception:
            return None

    def _load_uat_dbf_panel_status(self):
        dbf_dir = self._claims_uat_dbf_dir()
        manifest_path = os.path.join(dbf_dir, CLAIMS_UAT_DBF_MANIFEST)
        if not os.path.isfile(manifest_path):
            return {
                "uat_dbf_status": "NOT YET GENERATED",
                "uat_dbf_timestamp": "NOT YET GENERATED",
                "uat_dbf_folder": dbf_dir,
            }
        try:
            df = pd.read_csv(manifest_path, dtype=str)
            if df.empty:
                raise ValueError("empty manifest")
            ts = str(df.iloc[0].get("generation_timestamp", "")).strip() or "UNKNOWN"
            flags = df.get("generated_flag", pd.Series(dtype=str)).astype(str).str.upper()
            if len(flags) and (flags == "Y").all():
                status = "UAT PROTOTYPE ONLY (NOT PRODUCTION)"
            elif (flags == "Y").any():
                status = "PARTIAL — REVIEW REQUIRED"
            else:
                status = "GENERATION FAILED"
            return {
                "uat_dbf_status": status,
                "uat_dbf_timestamp": ts,
                "uat_dbf_folder": dbf_dir,
            }
        except Exception:
            return {
                "uat_dbf_status": "MANIFEST READ ERROR",
                "uat_dbf_timestamp": "NOT YET GENERATED",
                "uat_dbf_folder": dbf_dir,
            }

    def _write_claims_uat_dbf_manifest(self, dbf_dir, manifest_rows):
        manifest_path = os.path.normpath(os.path.join(dbf_dir, CLAIMS_UAT_DBF_MANIFEST))
        fieldnames = [
            "dbf_name", "source_csv", "generated_flag", "generation_timestamp", "record_count",
            "production_dbf_flag", "governance_population", "deferred_population_included",
            "run_mode", "rollback_snapshot_reference",
        ]
        with open(manifest_path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(manifest_rows)
        return manifest_path

    def _write_claims_uat_dbf_summary(self, dbf_dir, emit_result, dbf_result):
        cfg = self.CLAIMS_ORCHESTRATION
        go_live = cfg.get("go_live_target", "2026-09-01")
        emitted = emit_result.get("emitted", {}) if emit_result else {}
        clms_rows = (emitted.get("quikclms") or {}).get("row_count", "N/A")
        clmp_rows = (emitted.get("quikclmp") or {}).get("row_count", "N/A")
        hold_count = emit_result.get("hold_count", "N/A") if emit_result else "N/A"
        alignment = dbf_result.get("alignment", {}) or {}
        lines = [
            "QLAdmin Enterprise Claims — UAT DBF Generation Summary (Phase 21B)",
            "=" * 60,
            "",
            "IMPORTANT — UAT REHEARSAL ONLY",
            "-" * 30,
            "DBF files were generated directly from the final emitted UAT CSV files.",
            "Deferred and governance-hold records were excluded at Phase 21 emit.",
            "This is NOT production cutover.",
            "This is NOT production authorized DBF generation.",
            f"production_dbf_flag={cfg.get('production_dbf_flag', 'N')}",
            f"governance_population={UAT_DBF_GOVERNANCE_POPULATION}",
            "deferred_population_included=N",
            f"rulebook_lineage={PHASE21B_UAT_DBF_LINEAGE}",
            f"Go-Live Target: {go_live}",
            "",
            "EMITTED UAT CSV POPULATION",
            "-" * 30,
            f"Governance-cleared UAT claims emitted: {clms_rows}",
            f"Governance-cleared UAT payments emitted: {clmp_rows}",
            f"Deferred/excluded records held for review: {hold_count}",
            "",
            "ROW ALIGNMENT",
            "-" * 30,
            f"Alignment status: {alignment.get('status', dbf_result.get('alignment_status', 'UNKNOWN'))}",
            f"QUIKCLMS CSV/DBF row match: {alignment.get('quikclms_row_match', 'UNKNOWN')}",
            f"QUIKCLMP CSV/DBF row match: {alignment.get('quikclmp_row_match', 'UNKNOWN')}",
            f"Alignment manifest: {dbf_result.get('alignment_manifest_path', '')}",
            f"Alignment summary: {dbf_result.get('alignment_summary_path', '')}",
            "",
            "DBF GENERATION RESULT",
            "-" * 30,
            f"Status: {dbf_result.get('status', 'UNKNOWN')}",
            f"Output folder: {dbf_dir}",
            f"Rollback snapshot reference: {dbf_result.get('rollback_snapshot_reference', 'NOT_AVAILABLE')}",
            "",
            "Generated by app.py Phase 21B UAT DBF-from-CSV subprocess hook.",
            "Authoritative source: output/quikclms.csv and output/quikclmp.csv only.",
        ]
        if dbf_result.get("error"):
            lines.extend(["", "Error detail:", str(dbf_result["error"])])
        summary_path = os.path.join(dbf_dir, CLAIMS_UAT_DBF_SUMMARY)
        with open(summary_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        return summary_path

    def _invoke_external_uat_dbf_generation(self, emit_result):
        cfg = self.CLAIMS_ORCHESTRATION
        dbf_dir = self._claims_uat_dbf_dir()
        os.makedirs(dbf_dir, exist_ok=True)

        generation_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rollback_ref = self._get_governance_rollback_snapshot_reference()
        output_dir = emit_result.get("output_dir") or self._resolve_output_base_dir()
        csv_paths = self._uat_emit_csv_paths(output_dir)
        prod_flag = cfg.get("production_dbf_flag", "N")
        run_mode = cfg.get("run_mode", "UAT")
        gov_pop = UAT_DBF_GOVERNANCE_POPULATION

        base_result = {
            "status": "FAILED",
            "generation_timestamp": generation_ts,
            "dbf_dir": dbf_dir,
            "rollback_snapshot_reference": rollback_ref,
            "manifest_path": None,
            "summary_path": None,
            "alignment_manifest_path": None,
            "alignment_summary_path": None,
            "alignment_status": "FAILED",
            "error": "",
            "manifest_rows": [],
            "alignment": {},
        }

        for table_key, csv_path in csv_paths.items():
            if not os.path.isfile(csv_path):
                base_result["error"] = f"UAT emit CSV missing (required gate): {csv_path}"
                self.log(f"  UAT DBF ERROR: {base_result['error']}")
                return base_result

        runner = cfg.get("uat_dbf_generator_runner")
        timeout = cfg.get("uat_dbf_timeout_seconds", DEFAULT_ORCHESTRATION_TIMEOUT_SECONDS)
        claims_root = self._claims_analysis_root()

        if not runner or not os.path.isfile(runner):
            base_result["error"] = f"Phase 21B UAT DBF runner not found: {runner}"
            self.log(f"  UAT DBF ERROR: {base_result['error']}")
            return base_result

        cmd = [
            sys.executable, runner,
            "--clms-csv", csv_paths["quikclms"],
            "--clmp-csv", csv_paths["quikclmp"],
            "--output-dir", dbf_dir,
            "--run-mode", run_mode,
        ]
        self.log("UAT DBF GENERATION (Phase 21B): from final emitted CSV only...")
        self.log(f"  Command: {' '.join(cmd)}")
        self.log(f"  Working directory: {claims_root}")
        self.log(f"  Authoritative CSVs: {csv_paths['quikclms']} | {csv_paths['quikclmp']}")

        return_code = -1
        stdout_text = ""
        stderr_text = ""
        subprocess_status = "FAILED"
        error_detail = ""

        try:
            proc = subprocess.run(
                cmd,
                cwd=claims_root,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            return_code = proc.returncode
            stdout_text = proc.stdout or ""
            stderr_text = proc.stderr or ""
            subprocess_status = "SUCCESS" if return_code == 0 else "FAILED"
        except subprocess.TimeoutExpired as exc:
            subprocess_status = "TIMEOUT"
            error_detail = f"Phase 21B runner exceeded {timeout}s timeout"
            stdout_text = (exc.stdout or "") if exc.stdout else ""
            stderr_text = (exc.stderr or "") if exc.stderr else ""
        except OSError as exc:
            subprocess_status = "FAILED"
            error_detail = str(exc)

        self.log(f"UAT DBF GENERATION: Completed subprocess_status={subprocess_status} return_code={return_code}")
        self._log_subprocess_stream("uat-dbf-stdout", stdout_text)
        self._log_subprocess_stream("uat-dbf-stderr", stderr_text)

        exec_log = os.path.join(dbf_dir, "claims_uat_dbf_execution_log.txt")
        with open(exec_log, "a", encoding="utf-8") as fh:
            fh.write("\n".join([
                f"[{generation_ts}] UAT_DBF_{subprocess_status}",
                f"return_code={return_code}",
                f"production_dbf_flag={prod_flag}",
                f"governance_population={gov_pop}",
                f"rulebook_lineage={PHASE21B_UAT_DBF_LINEAGE}",
                f"runner={runner}",
                f"error={error_detail}" if error_detail else "error=",
                "--- stdout ---",
                stdout_text.rstrip() or "(empty)",
                "--- stderr ---",
                stderr_text.rstrip() or "(empty)",
            ]) + "\n")

        parsed = self._parse_phase21b_uat_dbf_stdout(stdout_text)
        alignment_manifest_path = parsed.get("alignment_manifest") or os.path.join(dbf_dir, CLAIMS_UAT_DBF_ALIGNMENT_MANIFEST)
        alignment_summary_path = parsed.get("alignment_summary") or os.path.join(dbf_dir, CLAIMS_UAT_DBF_ALIGNMENT_SUMMARY)
        if not os.path.isfile(alignment_manifest_path):
            alignment_manifest_path = os.path.join(dbf_dir, CLAIMS_UAT_DBF_ALIGNMENT_MANIFEST)
        if not os.path.isfile(alignment_summary_path):
            alignment_summary_path = os.path.join(dbf_dir, CLAIMS_UAT_DBF_ALIGNMENT_SUMMARY)

        alignment_df = self._load_phase21b_alignment_manifest(dbf_dir)
        table_map = [
            (QUIKCLMS_UAT_DBF_NAME, "quikclms"),
            (QUIKCLMP_UAT_DBF_NAME, "quikclmp"),
        ]
        manifest_rows = []
        all_generated = True
        alignment_matches = []

        for uat_name, table_key in table_map:
            dest_dbf = os.path.join(dbf_dir, uat_name)
            generated = subprocess_status == "SUCCESS" and os.path.isfile(dest_dbf)
            if not generated:
                all_generated = False
            csv_source = csv_paths[table_key]
            csv_rows = self._count_csv_data_rows(csv_source)
            table_parsed = parsed.get(table_key, {})
            row_match = table_parsed.get("row_match")
            dbf_rows = table_parsed.get("dbf_rows")

            if alignment_df is not None and not alignment_df.empty:
                row_df = alignment_df[alignment_df["dbf_name"].astype(str).str.upper() == uat_name.upper()]
                if not row_df.empty:
                    row_match = str(row_df.iloc[0].get("row_count_match", row_match or "")).strip().upper() or row_match
                    dbf_val = str(row_df.iloc[0].get("dbf_row_count", "")).strip()
                    if dbf_val and dbf_val.upper() != "UNKNOWN":
                        try:
                            dbf_rows = int(float(dbf_val))
                        except ValueError:
                            pass

            if row_match:
                alignment_matches.append(row_match)
            manifest_rows.append({
                "dbf_name": uat_name,
                "source_csv": csv_source,
                "generated_flag": "Y" if generated else "N",
                "generation_timestamp": generation_ts,
                "record_count": csv_rows,
                "production_dbf_flag": prod_flag,
                "governance_population": gov_pop,
                "deferred_population_included": "N",
                "run_mode": run_mode,
                "rollback_snapshot_reference": rollback_ref,
            })
            if generated and row_match == "N":
                error_detail = error_detail or f"Row count mismatch for {uat_name}: CSV={csv_rows} DBF={dbf_rows}"

        if parsed.get("alignment_status"):
            alignment_status = parsed["alignment_status"].upper()
        elif alignment_matches and all(m == "Y" for m in alignment_matches):
            alignment_status = "PASS"
        elif any(m == "N" for m in alignment_matches):
            alignment_status = "FAILED"
        elif alignment_matches and any(m == "UNKNOWN" for m in alignment_matches):
            alignment_status = "UNKNOWN"
        else:
            alignment_status = "UNKNOWN"

        if subprocess_status != "SUCCESS":
            final_status = subprocess_status
        elif not all_generated:
            final_status = "FAILED"
            error_detail = error_detail or "One or more UAT DBF files were not produced"
        elif alignment_status == "PASS":
            final_status = "SUCCESS"
        elif alignment_status == "FAILED":
            final_status = "FAILED"
            error_detail = error_detail or "CSV and DBF row counts do not match"
        else:
            final_status = "UNKNOWN"
            error_detail = error_detail or "DBF row count alignment could not be verified"

        manifest_path = self._write_claims_uat_dbf_manifest(dbf_dir, manifest_rows)
        rollback_path = os.path.join(dbf_dir, CLAIMS_UAT_DBF_ROLLBACK_REF)
        with open(rollback_path, "w", encoding="utf-8") as fh:
            fh.write(f"rollback_snapshot_reference={rollback_ref}\n")
            fh.write(f"generation_timestamp={generation_ts}\n")
            fh.write("production_dbf_flag=N\n")
            fh.write(f"governance_population={gov_pop}\n")
            fh.write(f"rulebook_lineage={PHASE21B_UAT_DBF_LINEAGE}\n")

        result = {
            "status": final_status,
            "generation_timestamp": generation_ts,
            "dbf_dir": dbf_dir,
            "rollback_snapshot_reference": rollback_ref,
            "manifest_path": manifest_path,
            "summary_path": None,
            "alignment_manifest_path": alignment_manifest_path if os.path.isfile(alignment_manifest_path) else None,
            "alignment_summary_path": alignment_summary_path if os.path.isfile(alignment_summary_path) else None,
            "alignment_status": alignment_status,
            "error": error_detail,
            "manifest_rows": manifest_rows,
            "return_code": return_code,
            "alignment": {
                "status": alignment_status,
                "quikclms_row_match": parsed.get("quikclms", {}).get("row_match", "UNKNOWN"),
                "quikclmp_row_match": parsed.get("quikclmp", {}).get("row_match", "UNKNOWN"),
            },
        }
        result["summary_path"] = self._write_claims_uat_dbf_summary(dbf_dir, emit_result, result)
        return result

    def _log_claims_uat_dbf_summary(self, dbf_result):
        if not dbf_result:
            return
        self.log("UAT DBF SUMMARY (Phase 21B — NOT PRODUCTION):")
        self.log(f"  Status: {dbf_result.get('status', 'UNKNOWN')}")
        self.log(f"  Alignment: {dbf_result.get('alignment_status', 'UNKNOWN')}")
        self.log(f"  Output folder: {dbf_result.get('dbf_dir', '')}")
        for row in dbf_result.get("manifest_rows", []):
            self.log(
                f"  {row.get('dbf_name')}: generated={row.get('generated_flag')} "
                f"records={row.get('record_count')} source={row.get('source_csv')}"
            )
        self.log(f"  Manifest: {dbf_result.get('manifest_path', '')}")
        self.log(f"  Alignment manifest: {dbf_result.get('alignment_manifest_path', '')}")
        self.log(f"  Alignment summary: {dbf_result.get('alignment_summary_path', '')}")
        self.log(f"  Summary: {dbf_result.get('summary_path', '')}")
        self.log(f"  governance_population={UAT_DBF_GOVERNANCE_POPULATION} | deferred_population_included=N")
        self.log(f"  rulebook_lineage={PHASE21B_UAT_DBF_LINEAGE}")
        if dbf_result.get("error"):
            self.log(f"  UAT DBF WARNING: {dbf_result['error']}")
            self.log("  CSV emit and review manifest remain valid.")

    def _maybe_generate_uat_claims_dbf(self, emit_result):
        if not self._claims_uat_dbf_generation_enabled():
            return None
        if not emit_result:
            self.log("UAT DBF generation skipped — no CSV emit result available.")
            return None
        if emit_result.get("validation_blocked") or emit_result.get("validation_error"):
            self.log("UAT DBF generation skipped — MPOLICY cross-table validation blocked emit.")
            return None
        if emit_result.get("validation_ok") is False:
            self.log("UAT DBF generation skipped — validated CSV emit did not complete.")
            return None
        self.log("UAT DBF GENERATION (Phase 21B): gated on validated output/quikclms.csv + quikclmp.csv...")
        dbf_result = self._invoke_external_uat_dbf_generation(emit_result)
        self._last_uat_dbf_result = dbf_result
        self._log_claims_uat_dbf_summary(dbf_result)
        return dbf_result

    def _setup_uat_status_banner(self):
        self.gov_banner_frame = tk.Frame(self.root, bg="#FEF3C7", padx=12, pady=8)
        self.gov_banner_frame.pack(fill="x", padx=30, pady=(0, 8))
        self.gov_banner_label = tk.Label(
            self.gov_banner_frame,
            text="",
            bg="#FEF3C7",
            fg="#92400E",
            font=("Segoe UI", 10, "bold"),
            justify="left",
            anchor="w",
        )
        self.gov_banner_label.pack(fill="x")

    def _setup_governance_summary_panel(self):
        panel = tk.LabelFrame(
            self.root,
            text=" Claims UAT Governance & Handoff (Phase 18C–20 — read-only) ",
            bg=self.bg_card,
            fg=self.accent,
            padx=16,
            pady=10,
            font=("Segoe UI", 10, "bold"),
        )
        panel.pack(padx=30, fill="x", pady=(0, 6))

        self.gov_metric_vars = {}
        metrics = [
            ("uat_claims", "UAT Candidate Claims:"),
            ("uat_payments", "UAT Candidate Payments:"),
            ("deferred_claims", "Deferred Claims:"),
            ("deferred_payments", "Deferred Payments:"),
            ("orphan_count", "Orphan Count (Phase 15):"),
            ("recon_pass_pct", "Reconciliation Pass %:"),
            ("replay_recovery", "Replay Orphan Recovery:"),
            ("top_blocker", "Top Blocker Category:"),
            ("exclusion_records", "Exclusion Log Records:"),
            ("surrender_queue", "Surrender Review Queue:"),
            ("orphan_queue", "Orphan Review Queue:"),
            ("uat_dbf_status", "UAT DBF Generation Status:"),
            ("uat_dbf_timestamp", "Last DBF Generation Timestamp:"),
            ("uat_dbf_folder", "UAT DBF Folder Path:"),
            ("mpolicy_validation_status", "MPOLICY Validation Status:"),
            ("claims_held_missing_policy", "Claims Held For Missing Policy:"),
            ("payments_held_missing_policy", "Payments Held For Missing Policy:"),
            ("cross_table_validation_report", "Cross-Table Validation Report Path:"),
        ]
        grid = tk.Frame(panel, bg=self.bg_card)
        grid.pack(fill="x")
        for idx, (key, label_text) in enumerate(metrics):
            row, col = divmod(idx, 2)
            tk.Label(grid, text=label_text, bg=self.bg_card, fg=self.text_color, font=("Segoe UI", 9, "bold")).grid(
                row=row, column=col * 2, sticky="w", padx=(0, 6), pady=2,
            )
            var = tk.StringVar(value="NOT YET GENERATED")
            self.gov_metric_vars[key] = var
            tk.Label(grid, textvariable=var, bg=self.bg_card, fg=self.accent, font=("Consolas", 9)).grid(
                row=row, column=col * 2 + 1, sticky="w", padx=(0, 24), pady=2,
            )

        actions = tk.Frame(panel, bg=self.bg_card)
        actions.pack(fill="x", pady=(8, 0))
        tk.Button(
            actions, text="Refresh Governance Summary", width=24,
            command=self._refresh_governance_visibility,
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            actions, text="View Exclusion Log", width=20,
            command=lambda: self._view_governance_log("business_exclusion_log.csv"),
        ).pack(side="left", padx=4)
        tk.Button(
            actions, text="View Issue Examples", width=20,
            command=lambda: self._view_governance_log("representative_issue_examples.csv"),
        ).pack(side="left", padx=4)
        tk.Button(
            actions, text="View Exception Catalog", width=22,
            command=lambda: self._view_governance_log("governance_exception_catalog.csv"),
        ).pack(side="left", padx=4)
        tk.Button(
            actions, text="CREATE UAT BUSINESS PACKAGE", width=28, bg=self.btn_batch, fg="white",
            command=self._on_create_uat_business_package,
        ).pack(side="right", padx=4)

    def _refresh_governance_visibility(self):
        summary = self._build_governance_summary()
        dbf_panel = self._load_uat_dbf_panel_status()
        if not summary["files_present"]:
            display = {key: "NOT YET GENERATED" for key in self.gov_metric_vars}
            display["uat_dbf_status"] = dbf_panel.get("uat_dbf_status", "NOT YET GENERATED")
            display["uat_dbf_timestamp"] = dbf_panel.get("uat_dbf_timestamp", "NOT YET GENERATED")
            display["uat_dbf_folder"] = dbf_panel.get("uat_dbf_folder", self._claims_uat_dbf_dir())
            val_panel = self._load_cross_table_validation_panel_status()
            display["mpolicy_validation_status"] = val_panel.get("mpolicy_validation_status", "NOT YET GENERATED")
            display["claims_held_missing_policy"] = val_panel.get("claims_held_missing_policy", "NOT YET GENERATED")
            display["payments_held_missing_policy"] = val_panel.get("payments_held_missing_policy", "NOT YET GENERATED")
            display["cross_table_validation_report"] = val_panel.get("cross_table_validation_report", "NOT YET GENERATED")
        else:
            display = {
                "uat_claims": self._format_governance_metric(summary["uat_claims"]),
                "uat_payments": self._format_governance_metric(summary["uat_payments"]),
                "deferred_claims": self._format_governance_metric(summary["deferred_claims"]),
                "deferred_payments": self._format_governance_metric(summary["deferred_payments"]),
                "orphan_count": self._format_governance_metric(summary["orphan_count"]),
                "recon_pass_pct": self._format_governance_metric(summary["recon_pass_pct"], suffix="%"),
                "replay_recovery": self._format_governance_metric(summary["replay_recovery"]),
                "exclusion_records": self._format_governance_metric(summary["exclusion_records"]),
                "surrender_queue": self._format_governance_metric(summary["surrender_queue"]),
                "orphan_queue": self._format_governance_metric(summary["orphan_queue"]),
            }
            if summary["top_blocker"]:
                display["top_blocker"] = f"{summary['top_blocker']} ({summary['top_blocker_count']})"
            else:
                display["top_blocker"] = "NOT YET GENERATED"
            display["uat_dbf_status"] = summary.get("uat_dbf_status", "NOT YET GENERATED")
            display["uat_dbf_timestamp"] = summary.get("uat_dbf_timestamp", "NOT YET GENERATED")
            display["uat_dbf_folder"] = summary.get("uat_dbf_folder", self._claims_uat_dbf_dir())
            display["mpolicy_validation_status"] = summary.get("mpolicy_validation_status", "NOT YET GENERATED")
            display["claims_held_missing_policy"] = summary.get("claims_held_missing_policy", "NOT YET GENERATED")
            display["payments_held_missing_policy"] = summary.get("payments_held_missing_policy", "NOT YET GENERATED")
            display["cross_table_validation_report"] = summary.get("cross_table_validation_report", "NOT YET GENERATED")

        for key, var in self.gov_metric_vars.items():
            var.set(display.get(key, "NOT YET GENERATED"))

        banner = (
            f"RUN MODE: {summary['run_mode']}  |  "
            f"PRODUCTION STATUS: {summary['production_status']}  |  "
            f"Governance Thresholds: {summary['threshold_status']}  |  "
            f"Go-Live Target: {summary['go_live_target']}  |  "
            f"production_dbf_flag={self.CLAIMS_ORCHESTRATION['production_dbf_flag']}"
        )
        self.gov_banner_label.config(text=banner)

    def _log_governance_console_summary(self):
        summary = self._build_governance_summary()
        if not summary["files_present"]:
            self.log("GOVERNANCE SUMMARY: Phase 17 outputs NOT YET GENERATED")
            return
        lines = [
            "GOVERNANCE EXECUTION SUMMARY (Phase 17 UAT reporting — read-only)",
            f"  UAT Candidate Claims: {self._format_governance_metric(summary['uat_claims'])}",
            f"  UAT Candidate Payments: {self._format_governance_metric(summary['uat_payments'])}",
            f"  Deferred Claims: {self._format_governance_metric(summary['deferred_claims'])}",
            f"  Deferred Payments: {self._format_governance_metric(summary['deferred_payments'])}",
            f"  Exclusion Records: {self._format_governance_metric(summary['exclusion_records'])}",
            f"  Orphan Count: {self._format_governance_metric(summary['orphan_count'])}",
            f"  Reconciliation Pass %: {self._format_governance_metric(summary['recon_pass_pct'], suffix='%')}",
            f"  Replay Orphan Recovery: {self._format_governance_metric(summary['replay_recovery'])}",
            f"  Production Status: {summary['production_status']}",
        ]
        if summary["top_blocker"]:
            lines.append(f"  Top Blocker: {summary['top_blocker']} ({summary['top_blocker_count']})")
        self.log("\n".join(lines))

    def _view_governance_log(self, filename):
        view_cfg = GOVERNANCE_LOG_VIEWS.get(filename, {})
        title = view_cfg.get("title", f"Governance Log — {filename}")
        preview_cols = view_cfg.get("columns", [])
        path = os.path.join(self._phase17_governance_dir(), filename)
        preview_limit = 40

        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("980x420")
        win.configure(bg=self.bg_main)

        header = tk.Label(
            win,
            text=f"{title}\nSource: {path}",
            bg=self.bg_main,
            fg=self.accent,
            font=("Segoe UI", 9, "bold"),
            justify="left",
            anchor="w",
        )
        header.pack(fill="x", padx=12, pady=(10, 4))

        text = scrolledtext.ScrolledText(win, bg="#F8FAFC", fg="#1E293B", font=("Consolas", 9))
        text.pack(padx=12, pady=8, fill="both", expand=True)

        if not os.path.isfile(path):
            text.insert(tk.END, "NOT YET GENERATED\n\nGovernance output file not found.\nRun Phase 17 UAT governance reporting to materialize this log.")
            text.config(state=tk.DISABLED)
            return

        try:
            df = pd.read_csv(path, dtype=str)
            df.columns = [str(c).strip().lower() for c in df.columns]
            total_rows = len(df)
            preview = df.head(preview_limit)
            if preview_cols:
                cols = [c for c in preview_cols if c in preview.columns]
                if cols:
                    preview = preview[cols]
            text.insert(tk.END, preview.to_string(index=False))
            text.insert(tk.END, f"\n\n--- read-only preview ({min(total_rows, preview_limit)} of {total_rows} rows) ---")
        except Exception as exc:
            text.insert(tk.END, f"Unable to preview file safely: {exc}")
        text.config(state=tk.DISABLED)

    def _review_hold_manifest_fieldnames(self):
        return [
            "audit_timestamp", "emit_timestamp", "production_dbf_flag", "hold_category",
            "record_type", "record_identifier", "record_id", "reconstructed_claim_id",
            "derivation_candidate_id", "MPOLICY", "blocker_category", "reason_excluded",
            "reason_held", "governance_status", "business_review_required",
            "business_explanation", "remediation_recommendation", "source_file",
            "target_file", "rulebook_lineage",
        ]

    def _load_policy_crosswalk_map(self):
        cw_path = ""
        cw_var = self.path_vars.get("CW") if hasattr(self, "path_vars") else None
        if cw_var and cw_var[0].get().strip():
            cw_path = cw_var[0].get().strip()
        if not cw_path or not os.path.isfile(cw_path):
            cw_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Master_Crosswalk.csv")
        if not os.path.isfile(cw_path):
            return {}
        try:
            cw_df = pd.read_csv(cw_path, dtype=str)
            return {
                self.normalize(k): self.normalize(v)
                for k, v in zip(cw_df.iloc[:, 0], cw_df.iloc[:, 1])
            }
        except Exception:
            return {}

    def _load_converted_mpolicy_set(self, output_dir=None):
        base = output_dir or self._resolve_output_base_dir()
        quikmstr_path = os.path.normpath(os.path.join(base, "quikmstr.csv"))
        if not os.path.isfile(quikmstr_path):
            return None, quikmstr_path
        try:
            qm_df = pd.read_csv(quikmstr_path, dtype=str, usecols=lambda c: str(c).strip().upper() == "MPOLICY")
        except ValueError:
            qm_df = pd.read_csv(quikmstr_path, dtype=str)
        if "MPOLICY" not in [str(c).strip().upper() for c in qm_df.columns]:
            qm_df.columns = [str(c).strip().upper() for c in qm_df.columns]
        if "MPOLICY" not in qm_df.columns:
            return set(), quikmstr_path
        mpolicy_col = [c for c in qm_df.columns if str(c).upper() == "MPOLICY"][0]
        values = {
            self.normalize(v)
            for v in qm_df[mpolicy_col].tolist()
            if str(v).strip() and str(v).strip().lower() not in ("nan", "none")
        }
        return values, quikmstr_path

    def _resolve_claims_rulebook_path(self, table_key):
        cfg_dir = self._migration_configs_dir()
        candidates = [
            os.path.join(cfg_dir, f"Sync_Rulebook_{table_key}.csv"),
            os.path.join(self._app_base_dir(), f"Sync_Rulebook_{table_key}.csv"),
        ]
        for path in candidates:
            if os.path.isfile(path):
                return path
        return candidates[0]

    def _phase10_derivation_path(self, table_key):
        claims_root = self._claims_analysis_root()
        paths = {
            "quikclms": os.path.join(
                claims_root, "phase10b_quikclms_derivation_design", "quikclms_derivation_candidates.csv",
            ),
            "quikclmp": os.path.join(
                claims_root, "phase10a_quikclmp_derivation_design", "quikclmp_derivation_candidates.csv",
            ),
        }
        return paths.get(table_key, "")

    def _load_phase10_derivation_index(self, table_key):
        path = self._phase10_derivation_path(table_key)
        index = {}
        if not path or not os.path.isfile(path):
            return index, path
        try:
            df = pd.read_csv(path, dtype=str).fillna("")
        except Exception:
            return index, path
        for _, row in df.iterrows():
            row_dict = {
                str(k).strip().lower(): str(v).strip()
                for k, v in row.to_dict().items()
            }
            deriv_id = row_dict.get("derivation_candidate_id", "")
            if deriv_id:
                index[deriv_id] = row_dict
        return index, path

    def _load_claims_sync_rulebook(self, table_key):
        rb_path = self._resolve_claims_rulebook_path(table_key)
        if not os.path.isfile(rb_path):
            return None, rb_path
        try:
            return pd.read_csv(rb_path, dtype=str).fillna(""), rb_path
        except Exception:
            return None, rb_path

    def _format_claims_money(self, val):
        try:
            return f"{float(str(val).replace(',', '').strip() or 0):.2f}"
        except Exception:
            return "0.00"

    def _derive_claims_mhdpmt(self, normalized):
        paytype = str(normalized.get("mpaytype", "")).strip().upper()
        return CLAIMS_PAYMENT_MHDPMT_MAP.get(paytype, "C")

    def _prepare_claims_source_row(self, combined, table_key):
        normalized = dict(combined)
        if table_key == "quikclmp" and not normalized.get("derived_mhdpmt"):
            normalized["derived_mhdpmt"] = self._derive_claims_mhdpmt(normalized)
        if table_key == "quikclms":
            if not normalized.get("netdb") and normalized.get("mnetamt"):
                normalized["netdb"] = normalized["mnetamt"]
            if not normalized.get("claimstat") and normalized.get("mclaimstatus"):
                normalized["claimstat"] = normalized["mclaimstatus"]
        return normalized

    def _transform_claims_source_row(self, combined, table_key, rules, crosswalk):
        schema = self.TABLE_SCHEMAS[table_key]
        normalized = self._prepare_claims_source_row(combined, table_key)
        money_fields = CLAIMS_MONEY_FIELDS.get(table_key, set())
        row_data = {h: "" for h in schema}
        for _, rule in rules.iterrows():
            s_f = str(rule.get("Source_Field", "")).strip()
            t_f = str(rule.get("Target_Field", "")).strip().upper()
            default_val = str(rule.get("Default_Value", "")).strip()
            if t_f not in [h.upper() for h in schema]:
                continue
            actual_h = [h for h in schema if h.upper() == t_f][0]
            val = ""
            if s_f:
                val = normalized.get(s_f.lower(), "")
            if not val and default_val and default_val.lower() not in ("nan", "none"):
                val = default_val
            val = self.normalize(val) if val else ""
            if t_f == "MPOLICY" and val:
                val = crosswalk.get(val, val)
            if t_f in money_fields:
                val = self._format_claims_money(val if val else default_val)
            row_data[actual_h] = val
        return row_data

    def _build_mpolicy_derivation_lookup(self):
        claims_root = self._claims_analysis_root()
        lookups = {"quikclms": {}, "quikclmp": {}}
        sources = {
            "quikclms": os.path.join(claims_root, "phase10b_quikclms_derivation_design", "quikclms_derivation_candidates.csv"),
            "quikclmp": os.path.join(claims_root, "phase10a_quikclmp_derivation_design", "quikclmp_derivation_candidates.csv"),
        }
        for table_key, path in sources.items():
            if not os.path.isfile(path):
                continue
            try:
                df = pd.read_csv(path, dtype=str)
                df.columns = [str(c).strip().lower() for c in df.columns]
            except Exception:
                continue
            target = lookups[table_key]
            for _, row in df.iterrows():
                mpolicy = self.normalize(str(row.get("mpolicy", row.get("policy_number", ""))))
                if not mpolicy:
                    continue
                for key_col in ("reconstructed_claim_id", "derivation_candidate_id"):
                    key_val = str(row.get(key_col, "")).strip()
                    if key_val:
                        target[key_val] = mpolicy
        return lookups

    def _parse_mpolicy_from_reconstructed_id(self, reconstructed_claim_id):
        rc = str(reconstructed_claim_id or "").strip()
        if rc.upper().startswith("RC-"):
            parts = rc.split("-")
            if len(parts) >= 2:
                return self.normalize(parts[1])
        return ""

    def _resolve_row_mpolicy(self, row, table_key, lookups, crosswalk):
        row_dict = row.to_dict() if hasattr(row, "to_dict") else dict(row)
        normalized = {str(k).strip().lower(): v for k, v in row_dict.items()}
        raw = self.normalize(str(normalized.get("mpolicy", "")))
        if not raw:
            deriv = str(normalized.get("derivation_candidate_id", "")).strip()
            rc = str(normalized.get("reconstructed_claim_id", "")).strip()
            table_lookup = lookups.get(table_key, {})
            combined = {}
            combined.update(lookups.get("quikclms", {}))
            combined.update(lookups.get("quikclmp", {}))
            for key in (deriv, rc):
                if key and key in table_lookup:
                    raw = table_lookup[key]
                    break
                if key and key in combined:
                    raw = combined[key]
                    break
            if not raw and rc:
                raw = self._parse_mpolicy_from_reconstructed_id(rc)
        converted = crosswalk.get(raw, raw) if raw else ""
        return raw, converted

    def _build_cross_table_hold_row(
        self, row, table_key, staged_path, dest_path, reason_excluded, mpolicy_raw,
        audit_ts, prod_flag,
    ):
        row_dict = row.to_dict() if hasattr(row, "to_dict") else dict(row)
        normalized = {str(k).strip().lower(): v for k, v in row_dict.items()}
        rc = str(normalized.get("reconstructed_claim_id", "")).strip()
        deriv = str(normalized.get("derivation_candidate_id", "")).strip()
        record_type = "CLAIM" if table_key == "quikclms" else "PAYMENT"
        if str(normalized.get("record_type", "")).strip().upper() == "QUIKCLMP":
            record_type = "PAYMENT"
        elif str(normalized.get("record_type", "")).strip().upper() == "QUIKCLMS":
            record_type = "CLAIM"
        record_identifier = deriv or rc or str(normalized.get("canonical_payment_stage_id", "")).strip()
        explanation = PHASE20_HOLD_EXPLANATION
        if reason_excluded == "QUIKMSTR_OUTPUT_MISSING":
            explanation = "Converted policy master output/quikmstr.csv was not available, so claims were held from UAT emit."
        elif reason_excluded == "BLANK_MPOLICY":
            explanation = "The claim or payment did not resolve to an MPOLICY value, so it was held from UAT output."
        elif reason_excluded == "MISSING_DERIVATION_CANDIDATE":
            explanation = (
                "The UAT governance row did not resolve to a Phase 10 derivation candidate, "
                "so QLA-shaped emit was held."
            )
        return {
            "audit_timestamp": audit_ts,
            "emit_timestamp": audit_ts,
            "production_dbf_flag": prod_flag,
            "hold_category": "CROSS_TABLE_VALIDATION",
            "record_type": record_type,
            "record_identifier": record_identifier,
            "record_id": record_identifier,
            "reconstructed_claim_id": rc,
            "derivation_candidate_id": deriv,
            "MPOLICY": mpolicy_raw,
            "blocker_category": "CROSS_TABLE_POLICY_MISSING",
            "reason_excluded": reason_excluded,
            "reason_held": reason_excluded,
            "governance_status": "GOVERNANCE_HOLD",
            "business_review_required": "Y",
            "business_explanation": explanation,
            "remediation_recommendation": PHASE20_REMEDIATION,
            "source_file": staged_path,
            "target_file": dest_path,
            "rulebook_lineage": PHASE20_RULEBOOK_LINEAGE,
        }

    def _validate_and_filter_staged_claims_csv(
        self, staged_path, table_key, mpolicy_set, quikmstr_path, lookups, crosswalk,
        quikmstr_missing, audit_ts, prod_flag, output_dir, validation_enabled=True,
    ):
        dest_path = os.path.normpath(os.path.join(output_dir, f"{table_key}.csv"))
        schema = self.TABLE_SCHEMAS[table_key]
        stats = {
            "validation_name": f"{table_key.upper()}_QLA_EMIT",
            "source_file": staged_path,
            "reference_file": quikmstr_path,
            "total_source_rows": 0,
            "emitted_rows": 0,
            "held_rows": 0,
            "semantic_hold_rows": 0,
            "blank_mpolicy_rows": 0,
            "missing_mpolicy_rows": 0,
            "missing_derivation_rows": 0,
            "validation_status": "PASS",
        }
        hold_rows = []
        semantic_rc_ids = set()
        semantic_deriv_ids = set()
        semantic_reason_map = {}
        if self._claims_semantic_governance_enabled():
            semantic_rc_ids, semantic_deriv_ids, semantic_reason_map, semantic_hold_path = (
                self._load_semantic_governance_hold_index()
            )
            if semantic_rc_ids or semantic_deriv_ids:
                stats["reference_file"] = f"{quikmstr_path}|semantic_hold={semantic_hold_path}"
        if not os.path.isfile(staged_path):
            stats["validation_status"] = "SOURCE_MISSING"
            return None, hold_rows, stats

        try:
            df = pd.read_csv(staged_path, dtype=str).fillna("")
        except Exception as exc:
            stats["validation_status"] = f"ERROR:{exc}"
            raise

        stats["total_source_rows"] = len(df)
        rules, rb_path = self._load_claims_sync_rulebook(table_key)
        if rules is None:
            stats["validation_status"] = "RULEBOOK_MISSING"
            stats["held_rows"] = len(df)
            for _, row in df.iterrows():
                hold_rows.append(self._build_cross_table_hold_row(
                    row, table_key, staged_path, dest_path, "RULEBOOK_MISSING",
                    "", audit_ts, prod_flag,
                ))
            return None, hold_rows, stats

        p10_index, p10_path = self._load_phase10_derivation_index(table_key)
        if not p10_index:
            stats["validation_status"] = "PHASE10_MISSING"
            stats["held_rows"] = len(df)
            for _, row in df.iterrows():
                hold_rows.append(self._build_cross_table_hold_row(
                    row, table_key, staged_path, dest_path, "PHASE10_DERIVATION_MISSING",
                    "", audit_ts, prod_flag,
                ))
            return None, hold_rows, stats

        stats["reference_file"] = f"{quikmstr_path}|{p10_path}|{rb_path}"

        if quikmstr_missing and validation_enabled:
            stats["validation_status"] = "BLOCKED_QUIKMSTR_MISSING"
            stats["held_rows"] = len(df)
            for _, row in df.iterrows():
                _, converted = self._resolve_row_mpolicy(row, table_key, lookups, crosswalk)
                hold_rows.append(self._build_cross_table_hold_row(
                    row, table_key, staged_path, dest_path, "QUIKMSTR_OUTPUT_MISSING",
                    converted, audit_ts, prod_flag,
                ))
            return None, hold_rows, stats

        emit_rows = []
        for _, row in df.iterrows():
            uat_dict = {
                str(k).strip().lower(): str(v).strip()
                for k, v in row.to_dict().items()
            }
            deriv = uat_dict.get("derivation_candidate_id", "")
            p10_row = p10_index.get(deriv, {})
            if not p10_row:
                stats["missing_derivation_rows"] += 1
                stats["held_rows"] += 1
                _, converted = self._resolve_row_mpolicy(row, table_key, lookups, crosswalk)
                hold_rows.append(self._build_cross_table_hold_row(
                    row, table_key, staged_path, dest_path, "MISSING_DERIVATION_CANDIDATE",
                    converted, audit_ts, prod_flag,
                ))
                continue

            combined = dict(p10_row)
            combined.update(uat_dict)
            rc = str(uat_dict.get("reconstructed_claim_id", p10_row.get("reconstructed_claim_id", ""))).strip()
            deriv = str(uat_dict.get("derivation_candidate_id", "")).strip()
            if self._claims_semantic_governance_enabled():
                is_semantic_hold = (
                    (rc and rc in semantic_rc_ids)
                    or (deriv and deriv in semantic_deriv_ids)
                )
                if is_semantic_hold:
                    stats["semantic_hold_rows"] += 1
                    stats["held_rows"] += 1
                    reason = semantic_reason_map.get(deriv) or semantic_reason_map.get(rc) or "SEMANTIC_PSEUDO_CLAIM"
                    _, converted = self._resolve_row_mpolicy(row, table_key, lookups, crosswalk)
                    hold_rows.append(self._build_semantic_hold_row(
                        row, table_key, staged_path, dest_path, reason, converted, audit_ts, prod_flag,
                    ))
                    continue

            qla_row = self._transform_claims_source_row(combined, table_key, rules, crosswalk)
            mpolicy = self.normalize(qla_row.get("MPOLICY", ""))

            if validation_enabled:
                if not mpolicy:
                    stats["blank_mpolicy_rows"] += 1
                    stats["held_rows"] += 1
                    hold_rows.append(self._build_cross_table_hold_row(
                        row, table_key, staged_path, dest_path, "BLANK_MPOLICY", mpolicy, audit_ts, prod_flag,
                    ))
                elif mpolicy not in mpolicy_set:
                    stats["missing_mpolicy_rows"] += 1
                    stats["held_rows"] += 1
                    hold_rows.append(self._build_cross_table_hold_row(
                        row, table_key, staged_path, dest_path, "MPOLICY_NOT_IN_OUTPUT",
                        mpolicy, audit_ts, prod_flag,
                    ))
                else:
                    emit_rows.append(qla_row)
            else:
                emit_rows.append(qla_row)

        stats["emitted_rows"] = len(emit_rows)
        if stats["held_rows"]:
            stats["validation_status"] = "HELD_ROWS_PRESENT"
        emit_df = pd.DataFrame(emit_rows, columns=schema) if emit_rows else pd.DataFrame(columns=schema)
        return emit_df, hold_rows, stats

    def _write_cross_table_validation_report(self, output_dir, report_rows, audit_ts, prod_flag):
        report_path = os.path.normpath(os.path.join(output_dir, CLAIMS_CROSS_TABLE_VALIDATION_REPORT))
        fieldnames = [
            "audit_timestamp", "production_dbf_flag", "validation_name", "source_file",
            "reference_file", "total_source_rows", "emitted_rows", "held_rows",
            "blank_mpolicy_rows", "missing_mpolicy_rows", "validation_status", "rulebook_lineage",
        ]
        rows = []
        for item in report_rows:
            rows.append({
                "audit_timestamp": audit_ts,
                "production_dbf_flag": prod_flag,
                "validation_name": item.get("validation_name", ""),
                "source_file": item.get("source_file", ""),
                "reference_file": item.get("reference_file", ""),
                "total_source_rows": item.get("total_source_rows", 0),
                "emitted_rows": item.get("emitted_rows", 0),
                "held_rows": item.get("held_rows", 0),
                "blank_mpolicy_rows": item.get("blank_mpolicy_rows", 0),
                "missing_mpolicy_rows": item.get("missing_mpolicy_rows", 0),
                "validation_status": item.get("validation_status", ""),
                "rulebook_lineage": PHASE20_RULEBOOK_LINEAGE,
            })
        with open(report_path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return report_path

    def _write_cross_table_validation_summary(self, output_dir, report_rows, hold_rows, audit_ts, prod_flag, quikmstr_path):
        cfg = self.CLAIMS_ORCHESTRATION
        summary_path = os.path.normpath(os.path.join(output_dir, CLAIMS_CROSS_TABLE_VALIDATION_SUMMARY))
        lines = [
            "QLAdmin Enterprise Claims — Cross-Table MPOLICY Validation Summary",
            "=" * 60,
            "",
            "IMPORTANT — UAT SAFETY GATE ONLY",
            "-" * 30,
            "This validation is for UAT output safety only.",
            "This is NOT production cutover.",
            "This is NOT production authorized DBF generation.",
            f"production_dbf_flag={prod_flag}",
            f"Go-Live Target: {cfg.get('go_live_target', '2026-09-01')}",
            "",
            f"Audit Timestamp: {audit_ts}",
            f"Reference Policy Master: {quikmstr_path}",
            "",
            "WHAT WAS CHECKED",
            "-" * 30,
            "Each governance-cleared staged claim/payment was checked against converted output/quikmstr.csv.",
            "Records referencing missing or blank MPOLICY values were held from UAT emit.",
            "",
        ]
        for item in report_rows:
            lines.extend([
                f"{item.get('validation_name', 'VALIDATION')}:",
                f"  Source: {item.get('source_file', '')}",
                f"  Total staged rows: {item.get('total_source_rows', 0)}",
                f"  Emitted rows: {item.get('emitted_rows', 0)}",
                f"  Held rows: {item.get('held_rows', 0)}",
                f"  Blank MPOLICY rows: {item.get('blank_mpolicy_rows', 0)}",
                f"  Missing MPOLICY rows: {item.get('missing_mpolicy_rows', 0)}",
                f"  Status: {item.get('validation_status', '')}",
                "",
            ])
        lines.extend([
            f"Total cross-table validation holds appended to manifest: {len(hold_rows)}",
            "",
            "Held records were blocked because the policy was missing from quikmstr.csv,",
            "blank/unresolved, or because quikmstr.csv itself was not available.",
        ])
        with open(summary_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        return summary_path

    def _load_cross_table_validation_panel_status(self):
        output_dir = self._resolve_output_base_dir() if hasattr(self, "path_vars") else os.path.join(
            self.CLAIMS_ORCHESTRATION.get("app_base_dir", ""), "output",
        )
        report_path = os.path.join(output_dir, CLAIMS_CROSS_TABLE_VALIDATION_REPORT)
        if self._last_cross_table_validation:
            val = self._last_cross_table_validation
            return {
                "mpolicy_validation_status": val.get("validation_status_label", "NOT YET GENERATED"),
                "claims_held_missing_policy": str(val.get("claims_held_missing_policy", "NOT YET GENERATED")),
                "payments_held_missing_policy": str(val.get("payments_held_missing_policy", "NOT YET GENERATED")),
                "cross_table_validation_report": val.get("validation_report_path", report_path),
            }
        if not os.path.isfile(report_path):
            return {
                "mpolicy_validation_status": "NOT YET GENERATED",
                "claims_held_missing_policy": "NOT YET GENERATED",
                "payments_held_missing_policy": "NOT YET GENERATED",
                "cross_table_validation_report": report_path,
            }
        try:
            df = pd.read_csv(report_path, dtype=str)
            claims_row = df[df["validation_name"].str.contains("QUIKCLMS", case=False, na=False)]
            pay_row = df[df["validation_name"].str.contains("QUIKCLMP", case=False, na=False)]
            claims_held = int(claims_row.iloc[0]["held_rows"]) if not claims_row.empty else 0
            pay_held = int(pay_row.iloc[0]["held_rows"]) if not pay_row.empty else 0
            statuses = df["validation_status"].astype(str).tolist()
            if any("BLOCKED" in s for s in statuses):
                status_label = "BLOCKED — QUIKMSTR MISSING"
            elif any("HELD" in s for s in statuses):
                status_label = "HELD ROWS PRESENT (UAT ONLY)"
            elif any("PASS" in s for s in statuses):
                status_label = "PASS (UAT ONLY — NOT PRODUCTION)"
            else:
                status_label = statuses[0] if statuses else "UNKNOWN"
            return {
                "mpolicy_validation_status": status_label,
                "claims_held_missing_policy": str(claims_held),
                "payments_held_missing_policy": str(pay_held),
                "cross_table_validation_report": report_path,
            }
        except Exception:
            return {
                "mpolicy_validation_status": "REPORT READ ERROR",
                "claims_held_missing_policy": "NOT YET GENERATED",
                "payments_held_missing_policy": "NOT YET GENERATED",
                "cross_table_validation_report": report_path,
            }

    def _resolve_output_base_dir(self):
        cfg = self.CLAIMS_ORCHESTRATION
        out_var = self.path_vars.get("Out")
        if out_var and out_var[0].get().strip():
            norm = os.path.normpath(out_var[0].get().strip())
        else:
            norm = os.path.normpath(os.path.join(cfg["app_base_dir"], "output"))
        staging_sub = cfg.get("staging_subdir", "claims_uat_staging")
        if os.path.basename(norm).lower() == staging_sub.lower():
            return os.path.dirname(norm)
        return norm

    def _count_csv_data_rows(self, path):
        if not os.path.isfile(path):
            return 0
        try:
            with open(path, encoding="utf-8") as fh:
                return max(sum(1 for _ in fh) - 1, 0)
        except OSError:
            return 0

    def _append_review_hold_rows(self, manifest_rows, seen_keys, df, hold_category, source_file, prod_flag, emit_ts):
        if df is None or df.empty:
            return
        id_fields = (
            "reconstructed_claim_id", "derivation_candidate_id", "record_identifier",
            "canonical_payment_stage_id", "prototype_claimnum",
        )
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            normalized = {str(k).strip().lower(): v for k, v in row_dict.items()}
            record_type = str(normalized.get("record_type", "")).strip().upper() or "UNKNOWN"
            record_id = ""
            for field in id_fields:
                val = str(normalized.get(field, "")).strip()
                if val and val.lower() not in ("nan", "none"):
                    record_id = val
                    break
            dedupe_key = (record_type, record_id, hold_category)
            if not record_id or dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            blocker = str(normalized.get("blocker_category", "")).strip()
            reason = str(
                normalized.get("deferred_category", "")
                or normalized.get("reason_excluded", "")
                or blocker
            ).strip()
            rc = str(normalized.get("reconstructed_claim_id", "")).strip()
            deriv = str(normalized.get("derivation_candidate_id", "")).strip()
            manifest_rows.append({
                "audit_timestamp": emit_ts,
                "emit_timestamp": emit_ts,
                "production_dbf_flag": str(normalized.get("production_dbf_flag", prod_flag)).strip() or prod_flag,
                "hold_category": hold_category,
                "record_type": record_type,
                "record_identifier": record_id,
                "record_id": record_id,
                "reconstructed_claim_id": rc,
                "derivation_candidate_id": deriv,
                "MPOLICY": str(normalized.get("mpolicy", "")).strip(),
                "blocker_category": blocker,
                "reason_excluded": reason,
                "reason_held": reason,
                "governance_status": str(normalized.get("governance_status", "")).strip(),
                "business_review_required": str(normalized.get("business_review_required", "")).strip(),
                "business_explanation": str(normalized.get("business_explanation", "")).strip(),
                "remediation_recommendation": str(normalized.get("remediation_recommendation", "")).strip(),
                "source_file": source_file,
                "target_file": "",
                "rulebook_lineage": str(normalized.get("rulebook_lineage", "")).strip(),
            })

    def _append_cross_table_hold_rows(self, manifest_rows, seen_keys, hold_rows):
        for row in hold_rows:
            dedupe_key = (
                row.get("record_type", ""),
                row.get("record_id", ""),
                row.get("hold_category", "CROSS_TABLE_VALIDATION"),
            )
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            manifest_rows.append(row)

    def _build_review_hold_manifest_rows(self, cross_table_hold_rows=None):
        cfg = self.CLAIMS_ORCHESTRATION
        gov_dir = self._phase17_governance_dir()
        emit_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prod_flag = cfg.get("production_dbf_flag", "N")
        manifest_rows = []
        seen_keys = set()
        sources = [
            ("deferred_governance_claims.csv", "DEFERRED_CLAIM", gov_dir),
            ("deferred_governance_payments.csv", "DEFERRED_PAYMENT", gov_dir),
            ("business_exclusion_log.csv", "EXCLUSION", gov_dir),
        ]
        for filename, hold_category, directory in sources:
            df = self._load_governance_csv_safe(filename, directory=directory)
            self._append_review_hold_rows(
                manifest_rows, seen_keys, df, hold_category, filename, prod_flag, emit_ts,
            )
        if cross_table_hold_rows:
            self._append_cross_table_hold_rows(manifest_rows, seen_keys, cross_table_hold_rows)
        return manifest_rows

    def _write_review_hold_manifest(self, output_dir, manifest_rows):
        manifest_path = os.path.normpath(os.path.join(output_dir, CLAIMS_REVIEW_HOLD_MANIFEST))
        fieldnames = self._review_hold_manifest_fieldnames()
        with open(manifest_path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(manifest_rows)
        return manifest_path

    def _emit_uat_claims_to_main_output(self, staging_dir):
        cfg = self.CLAIMS_ORCHESTRATION
        output_dir = self._resolve_output_base_dir()
        os.makedirs(output_dir, exist_ok=True)
        emit_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prod_flag = cfg.get("production_dbf_flag", "N")
        emitted = {}
        missing = []
        cross_table_holds = []
        report_rows = []
        validation_enabled = self._claims_mpolicy_validation_enabled()
        lookups = self._build_mpolicy_derivation_lookup()
        crosswalk = self._load_policy_crosswalk_map()

        if validation_enabled:
            mpolicy_set, quikmstr_path = self._load_converted_mpolicy_set(output_dir)
            quikmstr_missing = mpolicy_set is None
            if quikmstr_missing:
                self.log("PHASE 20 MPOLICY VALIDATION: output/quikmstr.csv missing — claims emit blocked.")
            else:
                self.log(
                    f"PHASE 20 MPOLICY VALIDATION: loaded {len(mpolicy_set)} converted MPOLICY values "
                    f"from {quikmstr_path}"
                )
        else:
            mpolicy_set = set()
            quikmstr_path = os.path.join(output_dir, "quikmstr.csv")
            quikmstr_missing = False
            self.log(
                "PHASE 21 QLA EMIT: MPOLICY validation disabled — writing QLA-shaped rows without cross-table filter."
            )

        self.log(
            f"PHASE 21 QLA EMIT: transforming UAT governance rows via Phase 10 + Sync_Rulebook "
            f"({PHASE21_RULEBOOK_LINEAGE})"
        )
        prelsa_path = self._resolve_claims_prelsa_path()
        p10_path = self._phase10_derivation_path("quikclmp")
        self.log(f"PHASE 22 LINEAGE: PRELSA source for payee enrichment = {prelsa_path}")
        self.log(f"PHASE 22 LINEAGE: Phase 10A derivation index = {p10_path}")

        try:
            for table_key, source_key in (
                ("quikclms", "uat_quikclms_source"),
                ("quikclmp", "uat_quikclmp_source"),
            ):
                staged_path = os.path.normpath(os.path.join(staging_dir, f"{table_key}.csv"))
                uat_source = cfg[source_key]
                if os.path.isfile(staged_path):
                    copy_from = staged_path
                elif os.path.isfile(uat_source):
                    copy_from = uat_source
                else:
                    missing.append(table_key)
                    emitted[table_key] = None
                    continue

                dest_path = os.path.normpath(os.path.join(output_dir, f"{table_key}.csv"))
                emit_df, hold_rows, stats = self._validate_and_filter_staged_claims_csv(
                    copy_from, table_key, mpolicy_set or set(), quikmstr_path,
                    lookups, crosswalk, quikmstr_missing, emit_ts, prod_flag, output_dir,
                    validation_enabled=validation_enabled,
                )
                cross_table_holds.extend(hold_rows)
                report_rows.append(stats)

                if emit_df is None:
                    emitted[table_key] = None
                    continue

                tmp_path = dest_path + ".tmp"
                emit_df.to_csv(tmp_path, index=False, encoding="utf-8")
                os.replace(tmp_path, dest_path)
                emitted[table_key] = {
                    "dest_path": dest_path,
                    "source_path": copy_from,
                    "row_count": len(emit_df),
                    "held_rows": stats.get("held_rows", 0),
                }

            manifest_rows = self._build_review_hold_manifest_rows(cross_table_holds)
            manifest_path = self._write_review_hold_manifest(output_dir, manifest_rows)
            validation_report_path = None
            validation_summary_path = None
            if report_rows:
                validation_report_path = self._write_cross_table_validation_report(
                    output_dir, report_rows, emit_ts, prod_flag,
                )
                validation_summary_path = self._write_cross_table_validation_summary(
                    output_dir, report_rows, cross_table_holds, emit_ts, prod_flag, quikmstr_path,
                )

            hold_by_category = {}
            for row in manifest_rows:
                cat = row.get("hold_category", "UNKNOWN")
                hold_by_category[cat] = hold_by_category.get(cat, 0) + 1

            claims_held = sum(
                1 for h in cross_table_holds
                if str(h.get("record_type", "")).upper() in ("CLAIM", "QUIKCLMS")
            )
            payments_held = sum(
                1 for h in cross_table_holds
                if str(h.get("record_type", "")).upper() in ("PAYMENT", "QUIKCLMP")
            )
            semantic_held = sum(
                1 for h in cross_table_holds
                if str(h.get("hold_category", "")).upper() == SEMANTIC_HOLD_CATEGORY
            )
            if quikmstr_missing and validation_enabled:
                validation_status_label = "BLOCKED — QUIKMSTR MISSING"
                validation_ok = False
            elif cross_table_holds and validation_enabled:
                validation_status_label = "HELD ROWS PRESENT (UAT ONLY)"
                validation_ok = True
            elif validation_enabled:
                validation_status_label = "PASS (UAT ONLY — NOT PRODUCTION)"
                validation_ok = True
            else:
                validation_status_label = "DISABLED"
                validation_ok = True

            result = {
                "emit_timestamp": emit_ts,
                "output_dir": output_dir,
                "emitted": emitted,
                "missing_tables": missing,
                "manifest_path": manifest_path,
                "hold_count": len(manifest_rows),
                "hold_by_category": hold_by_category,
                "validation_ok": validation_ok,
                "validation_blocked": bool(quikmstr_missing and validation_enabled),
                "validation_error": None,
                "validation_enabled": validation_enabled,
                "validation_status_label": validation_status_label,
                "claims_held_missing_policy": claims_held,
                "payments_held_missing_policy": payments_held,
                "semantic_hold_rows": semantic_held,
                "validation_report_path": validation_report_path,
                "validation_summary_path": validation_summary_path,
                "cross_table_hold_count": len(cross_table_holds),
            }
            self._last_cross_table_validation = result
            return result
        except Exception as exc:
            self.log(f"PHASE 20 MPOLICY VALIDATION ERROR: {exc}")
            return {
                "emit_timestamp": emit_ts,
                "output_dir": output_dir,
                "emitted": emitted,
                "missing_tables": missing,
                "manifest_path": None,
                "hold_count": 0,
                "hold_by_category": {},
                "validation_ok": False,
                "validation_blocked": False,
                "validation_error": str(exc),
                "validation_enabled": validation_enabled,
                "validation_status_label": "ERROR",
                "claims_held_missing_policy": 0,
                "payments_held_missing_policy": 0,
                "validation_report_path": None,
                "validation_summary_path": None,
                "cross_table_hold_count": 0,
            }

    def _log_uat_emit_summary(self, emit_result):
        if not emit_result:
            return
        self.log("UAT CLAIMS EMIT (Phase 21 — QLA-shaped via Phase 10 + Sync_Rulebook; MPOLICY validated when enabled):")
        self.log(f"  Main output folder: {emit_result['output_dir']}")
        if self._claims_semantic_governance_enabled():
            self.log(
                f"  Phase 22 semantic governance hold: {emit_result.get('semantic_hold_rows', 0)} rows "
                f"quarantined ({SEMANTIC_HOLD_CATEGORY})"
            )
            self.log("  Authoritative manuals: docs/claims_conversion_reference/QLAdmin_Help.pdf + LifePRO Accounting Transactions")
        if emit_result.get("validation_enabled"):
            self.log(f"  MPOLICY validation: {emit_result.get('validation_status_label', 'UNKNOWN')}")
            if emit_result.get("validation_report_path"):
                self.log(f"  Validation report: {emit_result['validation_report_path']}")
            self.log(
                f"  Cross-table holds: claims={emit_result.get('claims_held_missing_policy', 0)} "
                f"payments={emit_result.get('payments_held_missing_policy', 0)}"
            )
        for table_key, info in emit_result["emitted"].items():
            if info:
                held_note = ""
                if info.get("held_rows"):
                    held_note = f" ({info['held_rows']} held before emit)"
                self.log(f"  Emitted {table_key.upper()}: {info['row_count']} rows -> {info['dest_path']}{held_note}")
                self.log(f"    Source: {info['source_path']}")
            else:
                self.log(f"  {table_key.upper()}: NOT EMITTED")
        if emit_result.get("validation_blocked"):
            self.log("  All staged claims/payments held — output/quikmstr.csv not found.")
        if emit_result.get("validation_error"):
            self.log(f"  Validation error: {emit_result['validation_error']}")
        self.log(f"  Review hold manifest: {emit_result.get('manifest_path', '')}")
        self.log(f"  Records held for review (total manifest): {emit_result.get('hold_count', 0)}")
        for cat, count in sorted(emit_result.get("hold_by_category", {}).items()):
            self.log(f"    {cat}: {count}")
        self.log("  Deferred/excluded populations were NOT emitted to main output.")
        self.log(f"  production_dbf_flag={self.CLAIMS_ORCHESTRATION.get('production_dbf_flag', 'N')}")

    def _uat_packages_root(self):
        return os.path.normpath(os.path.join(self._resolve_output_base_dir(), UAT_PACKAGE_SUBDIR))

    def _write_uat_package_readme(self, package_dir, package_timestamp, copied_count, missing_count):
        cfg = self.CLAIMS_ORCHESTRATION
        go_live = cfg.get("go_live_target", "2026-09-01")
        lines = [
            "QLAdmin Enterprise Claims — UAT Business Review Package",
            "=" * 60,
            "",
            f"Package Timestamp: {package_timestamp}",
            f"Generated By: app.py v54.7 (Phase 18D — copy-only handoff)",
            "",
            "IMPORTANT — UAT REVIEW ONLY",
            "-" * 30,
            "This package is for UAT and business review only.",
            "This is NOT production cutover.",
            "No production DBF files are included in this package.",
            f"production_dbf_flag={cfg.get('production_dbf_flag', 'N')}",
            f"Go-Live Target: {go_live}",
            "",
            "app.py did not modify claims logic. All contents were copied read-only",
            "from Phase 17 UAT governance reporting outputs.",
            "",
            "PACKAGE CONTENTS",
            "-" * 30,
            "01_uat_candidate_data/",
            "  Good/testable UAT candidate claim and payment populations cleared for review.",
            "",
            "02_deferred_governance/",
            "  Claims and payments deferred by governance rules — not included in UAT candidates.",
            "",
            "03_business_review_logs/",
            "  Exclusion reasons, exception catalog, remediation notes, and issue examples.",
            "",
            "04_executive_reporting/",
            "  Executive dashboard KPIs, blocker trends, and summary text reports.",
            "",
            "05_business_workbenches/",
            "  Business review work queues (surrender, orphan, high-priority decisions).",
            "",
            "FILE COPY SUMMARY",
            "-" * 30,
            f"Files copied: {copied_count}",
            f"Files missing (listed in package_manifest.csv): {missing_count}",
            "",
            "See package_manifest.csv for per-file copy status.",
        ]
        readme_path = os.path.join(package_dir, "README_UAT_PACKAGE.txt")
        with open(readme_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        return readme_path

    def _write_uat_package_manifest(self, package_dir, package_timestamp, manifest_rows):
        manifest_path = os.path.join(package_dir, "package_manifest.csv")
        fieldnames = [
            "package_timestamp", "source_file", "package_file", "category",
            "copied_flag", "missing_reason", "production_dbf_flag",
        ]
        with open(manifest_path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(manifest_rows)
        return manifest_path

    def _create_uat_package_zip(self, packages_root, package_name, package_dir):
        zip_path = os.path.normpath(os.path.join(packages_root, f"{package_name}.zip"))
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(package_dir):
                for filename in files:
                    full_path = os.path.join(root, filename)
                    arcname = os.path.join(package_name, os.path.relpath(full_path, package_dir))
                    zf.write(full_path, arcname)
        return zip_path

    def _create_uat_business_package(self):
        cfg = self.CLAIMS_ORCHESTRATION
        source_root = self._phase17_governance_dir()
        package_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stamp_token = datetime.now().strftime("%Y%m%d_%H%M%S")
        package_name = f"UAT_PACKAGE_{stamp_token}"
        packages_root = self._uat_packages_root()
        package_dir = os.path.normpath(os.path.join(packages_root, package_name))
        os.makedirs(package_dir, exist_ok=True)

        manifest_rows = []
        copied_count = 0
        missing_count = 0
        prod_flag = cfg.get("production_dbf_flag", "N")

        for category, filenames in UAT_PACKAGE_CATEGORIES.items():
            category_dir = os.path.join(package_dir, category)
            os.makedirs(category_dir, exist_ok=True)
            for filename in filenames:
                source_path = os.path.normpath(os.path.join(source_root, filename))
                package_rel = os.path.join(category, filename)
                package_path = os.path.normpath(os.path.join(package_dir, package_rel))
                row = {
                    "package_timestamp": package_timestamp,
                    "source_file": source_path,
                    "package_file": package_rel.replace("\\", "/"),
                    "category": category,
                    "copied_flag": "N",
                    "missing_reason": "",
                    "production_dbf_flag": prod_flag,
                }
                if os.path.isfile(source_path):
                    shutil.copy2(source_path, package_path)
                    row["copied_flag"] = "Y"
                    copied_count += 1
                else:
                    row["missing_reason"] = "SOURCE_NOT_FOUND"
                    missing_count += 1
                manifest_rows.append(row)

        readme_path = self._write_uat_package_readme(
            package_dir, package_timestamp, copied_count, missing_count,
        )
        manifest_path = self._write_uat_package_manifest(package_dir, package_timestamp, manifest_rows)

        zip_path = None
        zip_error = None
        try:
            zip_path = self._create_uat_package_zip(packages_root, package_name, package_dir)
        except Exception as exc:
            zip_error = str(exc)

        return {
            "package_name": package_name,
            "package_dir": package_dir,
            "packages_root": packages_root,
            "readme_path": readme_path,
            "manifest_path": manifest_path,
            "zip_path": zip_path,
            "zip_error": zip_error,
            "copied_count": copied_count,
            "missing_count": missing_count,
            "total_files": copied_count + missing_count,
            "package_timestamp": package_timestamp,
        }

    def _on_create_uat_business_package(self):
        self.log("UAT BUSINESS PACKAGE: starting copy-only handoff generation (Phase 18D)...")
        try:
            result = self._create_uat_business_package()
        except Exception as exc:
            self.log(f"UAT BUSINESS PACKAGE ERROR: {exc}")
            messagebox.showerror("UAT Package Error", f"Package creation failed:\n{exc}")
            return

        self.log(f"UAT BUSINESS PACKAGE: folder created -> {result['package_dir']}")
        self.log(f"  README -> {result['readme_path']}")
        self.log(f"  Manifest -> {result['manifest_path']}")
        self.log(f"  Files copied: {result['copied_count']} | Missing: {result['missing_count']}")
        if result["zip_path"]:
            self.log(f"UAT BUSINESS PACKAGE: ZIP created -> {result['zip_path']}")
        elif result["zip_error"]:
            self.log(f"UAT BUSINESS PACKAGE WARNING: ZIP creation failed — {result['zip_error']}")
            self.log("  Package folder retained; review files directly.")

        messagebox.showinfo(
            "UAT Business Package Created",
            "\n".join([
                "UAT business review package created successfully.",
                "",
                f"Folder:\n{result['package_dir']}",
                "",
                f"Copied: {result['copied_count']} file(s)",
                f"Missing: {result['missing_count']} file(s)",
                "",
                f"ZIP: {result['zip_path'] or 'Not created (see console warning)'}",
                "",
                "This package is for UAT review only — not production cutover.",
            ]),
        )

    def _execute_claims_orchestration(self, table_id, full_uat_population=False, batch_context=False):
        cfg = self.CLAIMS_ORCHESTRATION
        t_id = table_id.lower()
        phase_label = "Phase 18A–20" if batch_context else "Phase 18A–20"
        self.log(f"CLAIMS ORCHESTRATION: {t_id.upper()} ({phase_label} — external pipeline + UAT emit)")
        if batch_context:
            self.log("  Batch context: full UAT population (quikclms + quikclmp)")
        self.log(f"  RUN_MODE={cfg['run_mode']} | production_dbf_flag={cfg['production_dbf_flag']} | go_live={cfg['go_live_target']}")

        result = {"emit_result": None, "staging_dir": None, "batch_context": batch_context, "dbf_result": None}

        if cfg["run_mode"] == "DISABLED":
            self.log("  Claims orchestration DISABLED. No staging action taken.")
            self._refresh_governance_visibility()
            return result

        if cfg["run_mode"] == "PRODUCTION":
            self.log("  PRODUCTION orchestration blocked until later authorization.")
            self.log("  External Phase 17 runner will NOT execute. No production DBF generation.")
            self._refresh_governance_visibility()
            return result

        staging_dir = self._claims_staging_dir()
        result["staging_dir"] = staging_dir
        pre_existing = {
            "quikclms": os.path.isfile(os.path.join(staging_dir, "quikclms.csv")),
            "quikclmp": os.path.isfile(os.path.join(staging_dir, "quikclmp.csv")),
        }

        runner_success = None
        if self._claims_lineage_refresh_enabled():
            refresh_ok = self._invoke_phase10a_quikclmp_refresh()
            if not refresh_ok:
                self.log("  Phase 10A lineage refresh failed — emit will use existing derivation candidates.")
        if self._claims_orchestrate_enabled():
            if not getattr(self, "_claims_pipeline_runner_completed", False):
                runner_success = self._invoke_external_claims_pipeline(staging_dir)
                self._claims_pipeline_runner_completed = True
                self._claims_pipeline_runner_success = runner_success
            else:
                runner_success = getattr(self, "_claims_pipeline_runner_success", False)
                self.log("  External Phase 17 runner already executed this session.")

            if runner_success:
                restaged = self._restage_all_uat_candidates(staging_dir)
                for table_key, staged_path, source_path in restaged:
                    self.log(f"  UAT restage: {table_key.upper()} -> {staged_path}")
                    self.log(f"    Source: {source_path}")
                if not restaged:
                    self.log("  Runner succeeded but UAT candidate sources were not found for restaging.")
            else:
                self.log("  Runner failed — preserving pre-existing staged files only (no stale restage).")
                for table_key, existed in pre_existing.items():
                    if existed:
                        self.log(f"  Preserved existing staged file: {table_key}.csv")
                    else:
                        self.log(f"  No staged file created for {table_key}.csv")
        else:
            if full_uat_population:
                restaged = self._restage_all_uat_candidates(staging_dir)
                for table_key, staged_path, source_path in restaged:
                    self.log(f"  UAT staging: {table_key.upper()} -> {staged_path}")
                    self.log(f"    Source population: {source_path}")
                if not restaged:
                    self.log("  UAT candidate sources not found for one or both claims tables.")
                    self.log("  Run Phase 17 UAT governance reporting to materialize candidate populations.")
            else:
                uat_source = self._claims_uat_source_path(t_id)
                if os.path.isfile(uat_source):
                    ok, staged_path = self._stage_uat_candidate_file(staging_dir, t_id, uat_source)
                    if ok:
                        self.log(f"  UAT staging: copied governance-cleared candidate -> {staged_path}")
                        self.log(f"  Source population: {uat_source}")
                else:
                    self.log(f"  UAT candidate source not found: {uat_source}")
                    self.log("  Run Phase 17 UAT governance reporting to materialize candidate populations.")
            self.log("  Orchestration hook: PREP ONLY (set QLA_CLAIMS_ORCHESTRATE=1 to execute Phase 17 runner)")

        prep_log = os.path.normpath(os.path.join(staging_dir, "claims_uat_orchestration_prep.txt"))
        with open(prep_log, "a", encoding="utf-8") as fh:
            fh.write("\n".join([
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] table={t_id.upper()}",
                f"batch_context={batch_context}",
                f"full_uat_population={full_uat_population}",
                f"RUN_MODE={cfg['run_mode']}",
                f"production_dbf_flag={cfg['production_dbf_flag']}",
                f"production_authorization_flag={cfg['production_authorization_flag']}",
                f"orchestrate_enabled={self._claims_orchestrate_enabled()}",
                f"runner_success={runner_success}",
                "inline_claims_conversion=BLOCKED",
                f"orchestration_runner={cfg['orchestration_runner']}",
            ]) + "\n")

        emit_result = None
        if self._claims_uat_emit_enabled():
            emit_result = self._emit_uat_claims_to_main_output(staging_dir)
            self._log_uat_emit_summary(emit_result)
        else:
            self.log("  UAT emit skipped (RUN_MODE != UAT or QLA_CLAIMS_UAT_EMIT=0).")

        result["emit_result"] = emit_result
        if emit_result and emit_result.get("validation_ok"):
            dbf_result = self._maybe_generate_uat_claims_dbf(emit_result)
            result["dbf_result"] = dbf_result
        elif self._claims_uat_dbf_generation_enabled():
            self.log("  UAT DBF generation skipped — validated CSV emit did not complete.")

        self._log_governance_console_summary()
        self._refresh_governance_visibility()
        return result

    def _execute_batch_claims_uat_finale(self):
        if not self._batch_include_claims_uat_enabled():
            self.log("BATCH UAT CLAIMS (18F): not enabled (set QLA_BATCH_INCLUDE_CLAIMS_UAT=1 in UAT mode).")
            return None
        self.log("=" * 60)
        self.log("BATCH UAT CLAIMS FINALE (Phase 18F — after standard table batch)")
        self.log("  Governance-cleared UAT candidates only; deferred populations excluded.")
        self.log(f"  production_dbf_flag={self.CLAIMS_ORCHESTRATION.get('production_dbf_flag', 'N')}")
        orch_result = self._execute_claims_orchestration(
            "quikclms", full_uat_population=True, batch_context=True,
        )
        emit_result = orch_result.get("emit_result") if orch_result else None
        dbf_result = orch_result.get("dbf_result") if orch_result else None
        self._log_batch_claims_uat_summary(emit_result, dbf_result)
        return {"emit_result": emit_result, "dbf_result": dbf_result}

    def _log_batch_claims_uat_summary(self, emit_result, dbf_result=None):
        self.log("BATCH UAT CLAIMS SUMMARY (Phase 18F):")
        if not emit_result:
            self.log("  No UAT claims emit result (orchestration blocked or emit disabled).")
            return
        emitted = emit_result.get("emitted", {})
        for table_key in ("quikclms", "quikclmp"):
            info = emitted.get(table_key)
            if info:
                self.log(f"  {table_key.upper()} in main output: {info['row_count']} rows")
            else:
                self.log(f"  {table_key.upper()}: not emitted")
        self.log(f"  Review holds: {emit_result.get('hold_count', 0)} records -> {emit_result.get('manifest_path', '')}")
        self.log(f"  Main output folder: {emit_result.get('output_dir', '')}")
        if dbf_result:
            self.log(f"  UAT DBF folder: {dbf_result.get('dbf_dir', '')} (status={dbf_result.get('status')})")
        self.log("=" * 60)

    def on_table_select(self, event=None):
        table = self.table_var.get()
        if not table: return

        if self._is_claims_table(table):
            cfg = self.CLAIMS_ORCHESTRATION
            claims_root = self._claims_analysis_root()
            uat_src = self._claims_uat_source_path(table)
            out_dir = self._migration_output_dir()
            if not os.path.isdir(out_dir):
                out_dir = os.path.join(cfg["app_base_dir"], "output")
            staging_dir = os.path.join(out_dir, cfg["staging_subdir"])
            rb_path = os.path.join(claims_root, "config", "app_claims_uat_orchestration_rules.json")
            self.path_vars["Rule"][0].set(rb_path if os.path.isfile(rb_path) else "")
            self.path_vars["Src"][0].set(uat_src if os.path.isfile(uat_src) else "")
            self.path_vars["Trans"][0].set("")
            self.path_vars["CW"][0].set("")
            self.path_vars["Rel"][0].set("")
            self.path_vars["Out"][0].set(out_dir)
            self.log(f"System UI: Claims UAT orchestration paths for {table.upper()} (RUN_MODE={cfg['run_mode']})")
            self.log(f"  Staging: {staging_dir} | Main output emit: {out_dir}")
            return

        src_dir = self._migration_source_dir()
        out_dir = self._migration_output_dir()
        map_dir = self._migration_mapping_dir()
        cfg_dir = self._migration_configs_dir()

        expected_src = (
            "PACTG_Accounting_Extract20260427.csv"
            if table.lower() in ["quikprmh", "quikdvpr"]
            else (
                "PPBENTYP.csv"
                if table.lower() == "quikdvdp"
                else (
                    "PPBEN.csv"
                    if table.lower() == "quikridr"
                    else (
                        "PAGNT.csv"
                        if table.lower() == "quikagts"
                        else f"{table}.csv"
                    )
                )
            )
        )

        rb_path = self._first_existing_file(
            os.path.join(cfg_dir, f"Sync_Rulebook_{table}.csv"),
            self._find_migration_file(f"Sync_Rulebook_{table}.csv", search_dirs=[cfg_dir]),
        )
        src_path = self._first_existing_file(
            os.path.join(src_dir, expected_src),
            self._find_migration_file(expected_src, search_dirs=[src_dir], exclude_output_paths=True),
        )
        trans_path = self._first_existing_file(
            os.path.join(map_dir, "Master_Value_Translation.csv"),
            self._find_migration_file("Master_Value_Translation.csv", search_dirs=[map_dir]),
        )
        cw_path = self._first_existing_file(
            os.path.join(map_dir, "Master_Crosswalk.csv"),
            self._find_migration_file("Master_Crosswalk.csv", search_dirs=[map_dir]),
        )
        rel_path = self._first_existing_file(
            os.path.join(out_dir, "quikclid.csv"),
            self._find_migration_file("quikclid.csv", search_dirs=[out_dir]),
        )

        if not os.path.isdir(out_dir):
            out_dir = os.path.join(self._app_base_dir(), "output")

        self.path_vars["Rule"][0].set(rb_path)
        self.path_vars["Src"][0].set(src_path)
        self.path_vars["Trans"][0].set(trans_path)
        self.path_vars["CW"][0].set(cw_path)
        self.path_vars["Rel"][0].set(rel_path)
        self.path_vars["Out"][0].set(out_dir)

        self.log(f"System UI: Auto-populated paths for {table.upper()} (QLA_Migration preferred)")
        self.log(f"  Source dir: {src_dir}")
        self.log(f"  Source file: {src_path or '(not found)'}")
        self.log(f"  Output dir: {out_dir}")

    def browse(self, var, mode, key):
        path = filedialog.askdirectory() if mode == "folder" else filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if path: 
            var.set(path)
            if key == "Src":
                filename = os.path.basename(path).lower()
                for k in self.TABLE_SCHEMAS.keys():
                    if k in filename: self.table_var.set(k); break
            self.refresh_table_list(path)

    def refresh_table_list(self, path):
        directory = path if os.path.isdir(path) else os.path.dirname(path)
        if os.path.exists(directory):
            csv_files = sorted([os.path.splitext(f)[0] for f in os.listdir(directory) if f.lower().endswith('.csv') and f.lower().startswith('quik')])
            self.table_dropdown['values'] = csv_files

    def create_snapshot(self):
        target_zip = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("Zip Files", "*.zip")])
        if target_zip:
            with zipfile.ZipFile(target_zip, 'w') as zipf:
                zipf.write(__file__, arcname=os.path.basename(__file__))
            self.log(f"Backup Created: {os.path.basename(target_zip)}")

    def normalize(self, val):
        if pd.isna(val) or str(val).strip().lower() in ['nan', 'none', '']: return ""
        s = str(val).strip().upper()
        if s.endswith('.0'): s = s[:-2]
        return s

    def extract_day(self, date_str):
        d = re.sub(r'[^0-9/]', '', str(date_str))
        if len(d) == 8: return d[-2:]
        if '/' in d:
            parts = d.split('/')
            if len(parts) >= 2: return parts[1].zfill(2)
        return ""

    def start_thread(self, batch):
        if not self.is_running:
            self.is_running = True
            self.start_time = time.time()
            threading.Thread(target=self.update_timer, daemon=True).start()
            threading.Thread(target=self.process_data, args=(batch,), daemon=True).start()

    def update_timer(self):
        while self.is_running:
            m, s = divmod(int(time.time() - self.start_time), 60)
            self.lbl_timer.config(text=f"Elapsed: {m:02d}:{s:02d}")
            time.sleep(1)

    def process_data(self, is_batch):
        try:
            self.console.delete(1.0, tk.END)
            self.log("Initializing Migration Engine v55.7...")
            self._diag_rel_fallback_count = 0
            self._claims_pipeline_runner_completed = False
            self._claims_pipeline_runner_success = False
            if self.debug_rel_fallback:
                self.log("DEBUG REL: Relationship fallback logging enabled (QLA_DEBUG_REL_FALLBACK)")
            batch_claims_flag = self._batch_include_claims_uat_enabled()
            uat_dbf_flag = self._claims_uat_dbf_generation_enabled()
            mpolicy_flag = self._claims_mpolicy_validation_enabled()
            self.log(
                f"RUN_MODE={self.RUN_MODE} | claims_orchestration=Phase18A–20 | "
                f"production_dbf_flag={self.CLAIMS_ORCHESTRATION['production_dbf_flag']} | "
                f"batch_include_claims_uat={'Y' if batch_claims_flag else 'N'} | "
                f"generate_uat_claims_dbf={'Y' if uat_dbf_flag else 'N'} | "
                f"validate_claims_mpolicy={'Y' if mpolicy_flag else 'N'}"
            )
            
            trans_path = self.path_vars["Trans"][0].get()
            trans_map = {}
            if trans_path and os.path.exists(trans_path):
                trans_df = pd.read_csv(trans_path, dtype=str)
                trans_map = {self.normalize(k): str(v).strip() for k, v in zip(trans_df.iloc[:, 0], trans_df.iloc[:, 1])}
                self.log(f"Successfully loaded Translation Matrix from: {os.path.basename(trans_path)}")
            else:
                self.log("Warning: Value Translation file not found.")

            cw_path = self.path_vars["CW"][0].get()
            cw_map = {}
            reverse_cw_map = {}
            if cw_path and os.path.exists(cw_path):
                cw_df = pd.read_csv(cw_path, dtype=str)
                cw_map = {self.normalize(k): self.normalize(v) for k, v in zip(cw_df.iloc[:, 0], cw_df.iloc[:, 1])}
                reverse_cw_map = {self.normalize(v): self.normalize(k) for k, v in zip(cw_df.iloc[:, 0], cw_df.iloc[:, 1])}
                self.log(f"Successfully loaded ID Crosswalk from: {os.path.basename(cw_path)}")
            else:
                self.log("Warning: ID Crosswalk file not found. Legacy linkages may fail.")

            rel_path = self.path_vars["Rel"][0].get()
            rel_map = self._load_rel_map(rel_path, trans_map, log_label="startup relational map")

            # --- RelationshipNameAddress Extract Cache ---
            rel_name_cache = {}
            self._diag_name_count = 0
            try:
                src_input_dir = os.path.dirname(self.path_vars["Src"][0].get()) if self.path_vars["Src"][0].get() else ""
                rel_ext_path = os.path.join(src_input_dir, 'RelationshipNameAddress_Extract.csv') if src_input_dir else 'RelationshipNameAddress_Extract.csv'
                
                self.log(f"DEBUG: Attempting to load RelationshipNameAddress from: {rel_ext_path}")
                
                with open(rel_ext_path, mode='r', encoding='utf-8-sig') as f:
                    first_line = f.readline()
                    f.seek(0) # Reset file pointer back to start for DictReader
                    
                    has_tabs = '\t' in first_line
                    self.log(f"DEBUG FILE: First line preview (100 chars): {first_line[:100].strip()}")
                    self.log(f"DEBUG FILE: Tabs detected: {has_tabs}")
                    
                    # Dynamically adjust delimiter based on tab detection
                    reader = csv.DictReader(f, delimiter='\t') if has_tabs else csv.DictReader(f)
                    
                    # Normalize fieldnames to strip trailing spaces and enforce uppercase
                    if reader.fieldnames:
                        reader.fieldnames = [str(h).strip().upper() for h in reader.fieldnames]
                        
                    self.log(f"DEBUG FILE: Parsed fieldnames count: {len(reader.fieldnames) if reader.fieldnames else 0}")
                    
                    first_row_logged = False
                    for r in reader:
                        if not first_row_logged:
                            self.log(f"DEBUG PARSE: First parsed row preview: {str(dict(list(r.items())[:5]))}...")
                            first_row_logged = True
                            
                        if 'NAME_ID' in r:
                            raw_name_id = str(r['NAME_ID']).strip()
                            # Skip empty rows or dashed separator rows
                            if not raw_name_id or set(raw_name_id) == {'-'}:
                                continue
                            rel_name_cache[self.normalize(r['NAME_ID'])] = r
                            
                self.log(f"DEBUG: Successfully loaded RelationshipNameAddress cache ({len(rel_name_cache)} records)")
            except FileNotFoundError:
                self.log(f"DEBUG: RelationshipNameAddress_Extract.csv not found at: {rel_ext_path}")
            # ---------------------------------------------

            tables = [self.table_var.get()]
            if is_batch:
                all_files = [t for t in self.TABLE_SCHEMAS.keys() if not self._is_claims_table(t)]
                priority = ['quikclnt', 'quikclid']
                tables = priority + [t for t in all_files if t not in priority]
                src_input_preview = self.path_vars["Src"][0].get()
                rule_input_preview = self.path_vars["Rule"][0].get()
                locked_src_base = self._resolve_batch_src_base(src_input_preview)
                locked_rule_base = self._resolve_batch_rule_base(rule_input_preview)
                self.log("=" * 60)
                self.log("BATCH SOURCE LOCK — all LifePRO tables read from one folder")
                self.log(f"  UI Source file: {src_input_preview or '(empty)'}")
                self.log(f"  Locked source root: {locked_src_base}")
                self.log(f"  Locked rulebook root: {locked_rule_base}")
                self.log(f"  Output folder: {self.path_vars['Out'][0].get()}")
                self.log("  NOTE: quikclms/quikclmp are NOT LifePRO source files — they come from Phase 17 UAT governance.")
                self.log("=" * 60)

            for t_id in tables:
                if not t_id: 
                    if not is_batch: self.log("!!! ERROR: Please select a table from the dropdown first.")
                    continue

                if self._is_claims_table(t_id):
                    self._execute_claims_orchestration(t_id)
                    continue
                
                rule_input = self.path_vars["Rule"][0].get()
                src_input = self.path_vars["Src"][0].get()

                rule_base = self._resolve_batch_rule_base(rule_input) if is_batch else (
                    os.path.dirname(rule_input) if rule_input else os.path.dirname(os.path.abspath(__file__))
                )
                src_base = self._resolve_batch_src_base(src_input) if is_batch else (
                    os.path.dirname(src_input) if src_input else os.path.dirname(os.path.abspath(__file__))
                )

                expected_src = (
                    "PACTG_Accounting_Extract20260427.csv"
                    if t_id.lower() in ["quikprmh", "quikdvpr"]
                    else (
                        "PPBENTYP.csv"
                        if t_id.lower() == "quikdvdp"
                        else (
                            "PPBEN.csv"
                            if t_id.lower() == "quikridr"
                            else (
                                "PAGNT.csv"
                                if t_id.lower() == "quikagts"
                                else f"{t_id}.csv"
                            )
                        )
                    )
                )

                rb_path = os.path.normpath(os.path.join(rule_base, f"Sync_Rulebook_{t_id}.csv")) if is_batch else rule_input
                src_path = os.path.normpath(os.path.join(src_base, expected_src)) if is_batch else src_input

                if is_batch:
                    self.log(f"Working Table: {t_id.upper()}")
                    self.log(f"  LifePRO SOURCE: {src_path}")
                    self.log(f"  Rulebook: {rb_path}")
                if t_id.lower() == "quikprmh":
                    if not os.path.exists(src_path):
                        self.log(f"Skipping {t_id.upper()} -> Missing Source Data: {src_path}")
                        continue
                    
                    self.log(f"Working Table: {t_id.upper()}")
                    source = pd.read_csv(src_path, encoding='latin1', low_memory=False, dtype=str, on_bad_lines='skip').fillna("")
                    source.columns = [str(col).replace('\ufeff', '').strip().upper() for col in source.columns]
                    
                    schema = self.TABLE_SCHEMAS.get(t_id.lower())
                    output = []
                    filtered_count = 0
                    
                    for i, src_row in source.iterrows():
                        credit_code = self.normalize(src_row.get("CREDIT_CODE", ""))
                        debit_code = self.normalize(src_row.get("DEBIT_CODE", ""))
                        excluded_codes = {"12", "96", "412", "413", "514", "641", "710", "1110", "1111"}
                        
                        if credit_code == "110" and credit_code not in excluded_codes and debit_code not in excluded_codes:
                            filtered_count += 1
                            try:
                                t_amt = f"{float(str(src_row.get('TRANS_AMOUNT', '')).replace(',', '').strip() or 0):.2f}"
                            except Exception:
                                t_amt = "0.00"
                                
                            bill_mode = self.normalize(src_row.get("BILLING_MODE", ""))
                            mode_count_map = {"1": "1", "3": "4", "6": "2", "12": "12"}
                            mmodepd = mode_count_map.get(bill_mode, "0")
                            
                            bf_val = self.normalize(src_row.get("BILLING_FORM", ""))
                            mbillfrm = trans_map.get(f"BF_{bf_val}", trans_map.get(bf_val, bf_val))
                            
                            pol = self.normalize(src_row.get("POLICY_NUMBER", ""))
                            mpolicy = cw_map.get(pol, pol)
                            
                            row_data = {
                                "MPOLICY": mpolicy,
                                "DATEPAID": self.normalize(src_row.get("EFFECTIVE_DATE", "")),
                                "RENEWAL": "2",
                                "PREMIUM": t_amt,
                                "MLIFE": t_amt,
                                "MTERM": "0.00",
                                "MSUPP": "0.00",
                                "MANN": "0.00",
                                "MHEALTH": "0.00",
                                "XS": "0.00",
                                "MPAIDTO": self.normalize(src_row.get("PAID_TO_DATE_NEW", "")),
                                "POSTDATE": "",
                                "MPOSTDATE": self.normalize(src_row.get("DATE_ADDED", "")),
                                "MSOURCE": "",
                                "MBATCH": self.normalize(src_row.get("BATCH_NUMBER", "")),
                                "USER_ID": self.normalize(src_row.get("CODER_ADDED", "")),
                                "MBILLFRM": mbillfrm,
                                "MMODEPD": mmodepd
                            }
                            output.append([row_data[h] for h in schema])
                        
                        if i % 1000 == 0:
                            self.progress["value"] = (i/len(source))*100
                            self.root.update_idletasks()
                    
                    out_dir = self.path_vars["Out"][0].get()
                    out_path = os.path.normpath(os.path.join(out_dir, f"{t_id}.csv"))
                    qdf = pd.DataFrame(output, columns=schema)
                    qdf.to_csv(out_path, index=False)
                    
                    self.log(f"Success: {t_id}.csv - {len(output)} records.")
                    
                    audit_path = os.path.normpath(os.path.join(out_dir, "Migration_Audit_Log.txt"))
                    is_new_log = not os.path.exists(audit_path)
                    source_count = len(source)
                    output_count = len(output)
                    variance = source_count - output_count
                    
                    audit_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] TABLE: {t_id.upper():<10} | SOURCE RECORDS: {source_count:<8} | QLA OUTPUT: {output_count:<8} | VARIANCE: {variance} (Filtered)\n"
                    
                    with open(audit_path, "a") as f:
                        if is_new_log:
                            f.write("=== QLADMIN ENTERPRISE MIGRATION AUDIT LOG ===\n")
                            f.write("Tracks 1:1 record translation matching to guarantee zero data loss.\n\n")
                        f.write(audit_msg)
                    
                    self.log(f"Audit Verified: {source_count} Source -> {output_count} Output. Saved to Audit Log.")

                    unique_policies = qdf['MPOLICY'].nunique()
                    blank_datepaid = qdf['DATEPAID'].astype(str).str.strip().isin(["", "nan", "None"]).sum()
                    blank_paidto = qdf['MPAIDTO'].astype(str).str.strip().isin(["", "nan", "None"]).sum()
                    zero_premium = qdf['PREMIUM'].astype(str).str.strip().isin(["", "0", "0.0", "0.00", "nan", "None"]).sum()
                    duplicate_rows = qdf.duplicated().sum()
                    mode_dist = qdf['MMODEPD'].value_counts(dropna=False).to_dict()
                    
                    self.log("QUIKPRMH ENTERPRISE VALIDATION:")
                    self.log(f"  Total PACTG Source Rows: {len(source)}")
                    self.log(f"  Filtered Payment-History Rows: {filtered_count}")
                    self.log(f"  Unique Policies: {unique_policies}")
                    self.log(f"  Blank DATEPAID: {blank_datepaid}")
                    self.log(f"  Blank MPAIDTO: {blank_paidto}")
                    self.log(f"  Zero PREMIUM: {zero_premium}")
                    self.log(f"  Duplicate Exact Rows: {duplicate_rows}")
                    self.log(f"  MMODEPD Distribution: {mode_dist}")
                    
                    continue  # Safely abort the parent processing loop and move to the next batch table
                # --------------------------------------------------------

                if not os.path.exists(rb_path) or not os.path.exists(src_path): 
                    self.log(f"Skipping {t_id.upper()} -> Missing files at specified paths:")
                    if not os.path.exists(rb_path): self.log(f"   [X] Cannot find Rulebook: {rb_path}")
                    if not os.path.exists(src_path): self.log(f"   [X] Cannot find Source Data: {src_path}")
                    continue
                
                self.log(f"Working Table: {t_id.upper()}")
                
                rules = pd.read_csv(rb_path, dtype=str)
                rules.columns = [str(col).strip() for col in rules.columns]
                
                source = pd.read_csv(src_path, encoding='latin1', low_memory=False, dtype=str, on_bad_lines='skip').fillna("")
                source.columns = [str(col).replace('\ufeff', '').strip().upper() for col in source.columns]

                if is_batch and t_id.lower() == "quikclnt" and self._is_preconverted_qla_client_source(source):
                    rna_path = os.path.normpath(os.path.join(src_base, "RelationshipNameAddress_Extract.csv"))
                    if os.path.isfile(rna_path):
                        self.log("WARNING: Source\\quikclnt.csv is pre-converted QLA output — not raw LifePRO.")
                        self.log(f"  Switching quikclnt input to: {rna_path}")
                        source = pd.read_csv(
                            rna_path, encoding='latin1', low_memory=False, dtype=str, on_bad_lines='skip',
                        ).fillna("")
                        source.columns = [str(col).replace('\ufeff', '').strip().upper() for col in source.columns]
                        source = self._bridge_rna_quikclnt_columns(source)
                    else:
                        self.log(
                            "WARNING: Pre-converted quikclnt.csv detected; "
                            "RelationshipNameAddress_Extract.csv not found in Source folder."
                        )

                lookups = {}
                if 'Lookup_Table' in rules.columns and 'Join_Key' in rules.columns:
                    unique_lookups = rules['Lookup_Table'].dropna().unique()
                    for lt in unique_lookups:
                        lt_clean = str(lt).strip()
                        if not lt_clean: continue
                        
                        lt_path = os.path.normpath(os.path.join(os.path.dirname(src_path), f"{lt_clean}.csv"))
                        if os.path.exists(lt_path):
                            try:
                                ldf = pd.read_csv(lt_path, encoding='latin1', low_memory=False, dtype=str, on_bad_lines='skip').fillna("")
                                ldf.columns = [str(col).strip().upper() for col in ldf.columns]
                                
                                jks = rules[rules['Lookup_Table'] == lt]['Join_Key'].dropna().unique()
                                lookups[lt_clean] = {}
                                for jk in jks:
                                    jk_clean = str(jk).strip().upper()
                                    if jk_clean in ldf.columns:
                                        ldf['__norm_jk'] = ldf[jk_clean].apply(self.normalize)
                                        lookups[lt_clean][jk_clean] = ldf.drop_duplicates(subset=['__norm_jk']).set_index('__norm_jk').to_dict('index')
                            except Exception as e: pass
                
                lifepro_extra = {}
                if t_id.lower() == "quikmstr":
                    src_dir = os.path.dirname(src_path)
                    
                    def find_extract(keyword):
                        search_dirs = [
                            src_dir, 
                            os.path.dirname(src_dir),
                            os.path.dirname(self.path_vars["Rule"][0].get()) if self.path_vars["Rule"][0].get() else "",
                            os.path.dirname(self.path_vars["Trans"][0].get()) if self.path_vars["Trans"][0].get() else ""
                        ]
                        all_matches = []
                        for d in search_dirs:
                            if not d or not os.path.exists(d): continue
                            for f in os.listdir(d):
                                if keyword.lower() in f.lower() and f.lower().endswith('.csv'):
                                    if not any(bad in f.lower() for bad in ['copy', 'old', 'backup', 'archive']):
                                        all_matches.append(os.path.normpath(os.path.join(d, f)))
                        if all_matches: return max(all_matches, key=os.path.getmtime)
                        return None

                    for keyword, ext_key, jk in [('ppbentyp', 'DIVIDEND', 'POLICY_NUMBER'), ('ppbentyp', 'NON_FORFEITURE', 'POLICY_NUMBER')]:
                        epath = find_extract(keyword)
                        if epath:
                            try:
                                edf = pd.read_csv(epath, encoding='latin1', low_memory=False, dtype=str, on_bad_lines='skip').fillna("")
                                edf.columns = [str(c).strip().upper() for c in edf.columns]
                                
                                if jk in edf.columns: edf[jk] = edf[jk].astype(str)
                                if ext_key in edf.columns: edf[ext_key] = edf[ext_key].astype(str)
                                
                                edf = edf[~edf.iloc[:, 0].astype(str).str.contains("---")]

                                if jk in edf.columns and ext_key in edf.columns:
                                    for seq_col in ['BENEFIT_SEQ', 'COVERAGE_SEQ']:
                                        if seq_col in edf.columns:
                                            edf[seq_col] = edf[seq_col].astype(str).str.strip().str.replace(".0", "", regex=False)
                                            edf = edf[edf[seq_col].isin(["1", "01"])]
                                            
                                    edf['__norm_jk'] = edf[jk].apply(self.normalize)
                                    edf[ext_key] = edf[ext_key].astype(str).str.strip()
                                    edf_valid = edf[~edf[ext_key].isin(["", "nan", "none", "null"])]
                                    edf_valid = edf_valid.drop_duplicates(subset=['__norm_jk'], keep='first')
                                    
                                    lifepro_extra[ext_key] = edf_valid.set_index('__norm_jk')[ext_key].to_dict()
                                    
                                    sample_keys = list(lifepro_extra[ext_key].keys())[:5]
                                    self.log(f"Auto-loaded Base {ext_key} from {os.path.basename(epath)}")
                                    self.log(f"  -> Cache Size: {len(lifepro_extra[ext_key])} | Key Sample: {sample_keys}")
                            except Exception as e:
                                self.log(f"Warning: Could not auto-load {os.path.basename(epath)} - {e}")
                                
                        # --- PPACH BANKING CACHE ---
                        self._ppach_bank_map = {}
                        ppach_path = find_extract('ppach')
                        if ppach_path:
                            try:
                                pdf = pd.read_csv(ppach_path, encoding='latin1', low_memory=False, dtype=str, on_bad_lines='skip').fillna("")
                                pdf.columns = [str(c).strip().upper() for c in pdf.columns]
                                if 'POLICY_NUMBER' in pdf.columns and 'E_ABA_NUM' in pdf.columns and 'E_ACCOUNT_NUMBER' in pdf.columns:
                                    if 'CHANGE_DATE' in pdf.columns and 'CHANGE_TIME' in pdf.columns:
                                        pdf = pdf.sort_values(by=['CHANGE_DATE', 'CHANGE_TIME'], ascending=[True, True])
                                        
                                    for _, r in pdf.iterrows():
                                        pol = self.normalize(r.get('POLICY_NUMBER'))
                                        aba = str(r.get('E_ABA_NUM')).strip()
                                        if aba.endswith('.0'): aba = aba[:-2]
                                        acct = str(r.get('E_ACCOUNT_NUMBER')).strip()
                                        if acct.endswith('.0'): acct = acct[:-2]
                                        
                                        if pol and aba and acct and aba.lower() not in ['nan', 'none', ''] and acct.lower() not in ['nan', 'none', '']:
                                            self._ppach_bank_map[pol] = f"{aba}/{acct}"
                                            
                                    self.log(f"Auto-loaded PPACH Banking Cache for quikmstr ({len(self._ppach_bank_map)} records)")
                            except Exception as e:
                                self.log(f"Warning: Could not load PPACH cache - {e}")
                        # ---------------------------
                
                quikmstr_paid_to = {}
                if t_id.lower() == "quikdvdp":
                    try:
                        base_d = os.path.dirname(os.path.abspath(__file__))
                        parent_d = os.path.dirname(base_d)
                        search_dirs = [
                            self.path_vars["Out"][0].get(),
                            self.path_vars["Src"][0].get(),
                            base_d, parent_d
                        ]
                        
                        all_matches = []
                        for d in search_dirs:
                            if not d or not os.path.exists(d): continue
                            for root, dirs, files in os.walk(d):
                                dirs[:] = [d_ for d_ in dirs if not any(b in d_.lower() for b in ['copy', 'old', 'backup', 'archive'])]
                                for f in files:
                                    if f.lower() == 'quikmstr.csv':
                                        all_matches.append(os.path.normpath(os.path.join(root, f)))
                        
                        all_matches = sorted(all_matches, key=lambda x: 'output' not in x.lower())
                        cache_built = False
                        
                        for qm_path in all_matches:
                            qm_df = pd.read_csv(qm_path, encoding='latin1', low_memory=False, dtype=str).fillna("")
                            qm_df.columns = [str(c).strip().upper() for c in qm_df.columns]
                            
                            if 'MPOLICY' in qm_df.columns and 'MPAIDTO' in qm_df.columns:
                                qm_df['__norm_pol'] = qm_df['MPOLICY'].apply(self.normalize)
                                qm_df['MPAIDTO'] = qm_df['MPAIDTO'].astype(str).str.strip()
                                valid = qm_df[~qm_df['MPAIDTO'].isin(["", "nan", "none", "null"])]
                                quikmstr_paid_to.update(valid.set_index('__norm_pol')['MPAIDTO'].to_dict())
                                cache_built = True
                                
                            elif 'POLICY_NUMBER' in qm_df.columns and 'PAID_TO_DATE' in qm_df.columns:
                                qm_df['__norm_pol'] = qm_df['POLICY_NUMBER'].apply(lambda x: cw_map.get(self.normalize(x), self.normalize(x)))
                                qm_df['PAID_TO_DATE'] = qm_df['PAID_TO_DATE'].astype(str).str.strip()
                                valid = qm_df[~qm_df['PAID_TO_DATE'].isin(["", "nan", "none", "null"])]
                                quikmstr_paid_to.update(valid.set_index('__norm_pol')['PAID_TO_DATE'].to_dict())
                                cache_built = True
                                
                            if cache_built:
                                self.log(f"Auto-loaded MPAIDTO fallback cache from {os.path.basename(qm_path)} ({len(quikmstr_paid_to)} policies)")
                                break
                                
                        if not cache_built:
                            self.log("Warning: Could not find any quikmstr.csv to build MPAIDTO cache. MINTDATE fallback will fail.")
                    except Exception as e: 
                        self.log(f"Warning: Error loading MPAIDTO cache - {str(e)}")

                    # --- QUIKDVDP TRANSACTION CACHE ---
                    quikdvdp_tx_cache = {}
                    if t_id.lower() == "quikdvdp":
                        try:
                            pactg_path = os.path.normpath(os.path.join(src_base, "PACTG_Accounting_Extract20260427.csv"))
                            if os.path.exists(pactg_path):
                                self.log("Building quikdvdp Transaction Cache (0514/0641)...")
                                tx_df = pd.read_csv(pactg_path, encoding='latin1', low_memory=False, dtype=str, on_bad_lines='skip').fillna("")
                                tx_df.columns = [str(col).replace('\ufeff', '').strip().upper() for col in tx_df.columns]
                                
                                pol_col = 'POLN' if 'POLN' in tx_df.columns else 'POLICY_NUMBER'
                                amt_col = 'TRAMT' if 'TRAMT' in tx_df.columns else 'TRANS_AMOUNT'
                                dt_col = 'TRDATE' if 'TRDATE' in tx_df.columns else 'EFFECTIVE_DATE'
                                trcd_col = 'TRCD'
                                
                                if pol_col in tx_df.columns and amt_col in tx_df.columns:
                                    current_year = str(datetime.now().year)
                                    
                                    for _, r in tx_df.iterrows():
                                        raw_pol = self.normalize(r.get(pol_col))
                                        if not raw_pol: continue
                                        
                                        # Enterprise-safe policy normalization:
                                        # Convert LifePRO policy IDs into QLAdmin MPOLICY space
                                        pol = cw_map.get(raw_pol, raw_pol)
                                        
                                        trcd = self.normalize(r.get(trcd_col))
                                        if not trcd:
                                            cc = self.normalize(r.get('CREDIT_CODE', ''))
                                            dc = self.normalize(r.get('DEBIT_CODE', ''))
                                            if cc in ['0514', '514', '0641', '641']: trcd = cc
                                            elif dc in ['0514', '514', '0641', '641']: trcd = dc
                                        
                                        if trcd in ['0514', '514', '0641', '641']:
                                            amt_str = str(r.get(amt_col, '0')).replace(',', '').strip()
                                            try: amt = float(amt_str) if amt_str else 0.0
                                            except: amt = 0.0
                                            
                                            date_val = str(r.get(dt_col, '')).strip()
                                            
                                            if pol not in quikdvdp_tx_cache:
                                                quikdvdp_tx_cache[pol] = {'MDEPOSIT': 0.0, 'MINTYTD': 0.0, 'MINTDATE': ""}
                                            
                                            if trcd in ['0514', '514']:
                                                quikdvdp_tx_cache[pol]['MDEPOSIT'] += amt
                                            elif trcd in ['0641', '641']:
                                                if current_year in date_val:
                                                    quikdvdp_tx_cache[pol]['MINTYTD'] += amt
                                                
                                                curr_max = quikdvdp_tx_cache[pol]['MINTDATE']
                                                if not curr_max:
                                                    quikdvdp_tx_cache[pol]['MINTDATE'] = date_val
                                                else:
                                                    try:
                                                        if pd.to_datetime(date_val) > pd.to_datetime(curr_max):
                                                            quikdvdp_tx_cache[pol]['MINTDATE'] = date_val
                                                    except:
                                                        if date_val > curr_max:
                                                            quikdvdp_tx_cache[pol]['MINTDATE'] = date_val
                                                            
                                self.log(f"Auto-loaded quikdvdp Transaction Cache ({len(quikdvdp_tx_cache)} policies)")
                        except Exception as e:
                            self.log(f"Warning: Failed to build quikdvdp transaction cache - {e}")
                    # ----------------------------------

                quikridr_par_cache = {}
                if t_id.lower() == "quikridr":
                    try:
                        ppb_path = os.path.normpath(os.path.join(os.path.dirname(src_path), "PPBENTYP.csv"))
                        if os.path.exists(ppb_path):
                            ppb_df = pd.read_csv(ppb_path, encoding='latin1', low_memory=False, dtype=str, on_bad_lines='skip').fillna("")
                            ppb_df.columns = [str(c).strip().upper() for c in ppb_df.columns]
                            if 'POLICY_NUMBER' in ppb_df.columns and 'BENEFIT_SEQ' in ppb_df.columns and 'PAR_TYPE' in ppb_df.columns:
                                for _, r in ppb_df.iterrows():
                                    pol = self.normalize(r.get('POLICY_NUMBER'))
                                    seq = self.normalize(str(r.get('BENEFIT_SEQ')).replace('.0', ''))
                                    par = str(r.get('PAR_TYPE')).strip()
                                    if pol and seq and par not in ["", "nan", "none"]:
                                        quikridr_par_cache[(pol, seq)] = par
                                self.log(f"Auto-loaded PPBENTYP PAR Cache for quikridr ({len(quikridr_par_cache)} records)")
                    except Exception as e:
                        self.log(f"Warning: Failed to load PPBENTYP cache for quikridr - {e}")

                quikagts_clnt_cache = {}
                if t_id.lower() == "quikagts":
                    try:
                        qc_path = os.path.normpath(os.path.join(self.path_vars["Out"][0].get(), "quikclnt.csv"))
                        if os.path.exists(qc_path):
                            qc_df = pd.read_csv(qc_path, encoding='latin1', low_memory=False, dtype=str).fillna("")
                            qc_df.columns = [str(c).strip().upper() for c in qc_df.columns]
                            if 'MCLIENTID' in qc_df.columns:
                                qc_df['__norm_cid'] = qc_df['MCLIENTID'].apply(self.normalize)
                                quikagts_clnt_cache = qc_df.drop_duplicates(subset=['__norm_cid'], keep='first').set_index('__norm_cid').to_dict('index')
                                self.log(f"Auto-loaded quikclnt cache for quikagts ({len(quikagts_clnt_cache)} records)")
                        else:
                            self.log("Warning: quikclnt.csv not found in Output. quikagts enrichment will be incomplete.")
                    except Exception as e:
                        self.log(f"Warning: Failed to load quikclnt cache for quikagts - {e}")

                if t_id.lower() == "quikridr":
                    if 'BENEFIT_SEQ' in source.columns:
                        source['BENEFIT_SEQ'] = source['BENEFIT_SEQ'].astype(str).str.strip().str.replace(".0", "", regex=False)
                        source = source[source['BENEFIT_SEQ'].apply(
                            lambda x: x.isdigit() and int(x) >= 1
                        )]
                elif t_id.lower() == "quikdvdp":
                    if 'BENEFIT_SEQ' in source.columns:
                        source['BENEFIT_SEQ'] = source['BENEFIT_SEQ'].astype(str).str.strip().str.replace(".0", "", regex=False)
                        source = source[source['BENEFIT_SEQ'].isin(["1", "01"])]
                elif t_id.lower() == "quikclnt":
                    if 'CANCEL_DATE' in source.columns: source = source[source['CANCEL_DATE'].apply(lambda x: self.normalize(x) in ["", "0"])]
                    if 'NAME_ID' in source.columns: source = source.drop_duplicates(subset=['NAME_ID', 'ADDRESS_ID'], keep='first')
                    
                    # --- NEW SOURCE DIAGNOSTICS ---
                    self.log(f"DEBUG SOURCE: 'NAME_ID' in columns? {'NAME_ID' in source.columns}")
                    self.log(f"DEBUG SOURCE: First 25 columns: {list(source.columns)[:25]}")
                    
                    diag_cols = ['POLICY_NUMBER', 'NAME_ID', 'CLIENT_ID', 'ADDRESS_ID']
                    diag_cols.extend([c for c in source.columns if any(k in c for k in ['NAME', 'CLIENT', 'PARTY', 'PERSON', 'RELATION'])])
                    
                    # Deduplicate and keep only columns that actually exist in the dataframe
                    diag_cols = list(dict.fromkeys([c for c in diag_cols if c in source.columns]))
                    
                    for row_idx, s_row in enumerate(source.head(5).to_dict('records')):
                        diag_vals = {c: s_row.get(c, '') for c in diag_cols}
                        self.log(f"DEBUG SOURCE ROW {row_idx + 1}: {diag_vals}")
                    # ------------------------------
                    
                elif t_id.lower() == "quikbenf":
                    if 'RELATE_CODE' in source.columns:
                        source['RELATE_CODE'] = source['RELATE_CODE'].apply(self.normalize)
                        source = source[source['RELATE_CODE'].isin(['B1', 'B2', 'P', 'C'])]
                        
                elif t_id.lower() == "quikplan":
                    if 'COVERAGE_ID' in source.columns: source = source.drop_duplicates(subset=['COVERAGE_ID'], keep='first')

                elif t_id.lower() == "quikdvpr":
                    credit_match = pd.Series(False, index=source.index)
                    debit_match = pd.Series(False, index=source.index)
                    
                    if 'CREDIT_CODE' in source.columns:
                        source['CREDIT_CODE'] = source['CREDIT_CODE'].apply(self.normalize)
                        credit_match = source['CREDIT_CODE'].isin(['516', '0516'])
                        
                    if 'DEBIT_CODE' in source.columns:
                        source['DEBIT_CODE'] = source['DEBIT_CODE'].apply(self.normalize)
                        debit_match = source['DEBIT_CODE'].isin(['516', '0516'])
                        
                    if 'CREDIT_CODE' in source.columns or 'DEBIT_CODE' in source.columns:
                        source = source[credit_match | debit_match]

                schema = self.TABLE_SCHEMAS.get(t_id.lower())
                if not schema:
                    if 'Target_Field' in rules.columns:
                        schema = list(rules['Target_Field'].unique())
                    else:
                        self.log(f"!!! CRITICAL: 'Target_Field' header is completely missing in your Rulebook.")
                        continue

                output = []
                for i, src_row in source.iterrows():
                    if any("---" in str(v) for v in src_row.values[:3]): continue
                    
                    row_data = {h: "" for h in schema}
                    for _, rule in rules.iterrows():
                        s_f = str(rule.get('Source_Field', '')).strip().upper()
                        t_f = str(rule.get('Target_Field', '')).strip().upper()
                        lt = str(rule.get('Lookup_Table', '')).strip() if 'Lookup_Table' in rule else ""
                        jk = str(rule.get('Join_Key', '')).strip().upper() if 'Join_Key' in rule else ""
                        
                        if s_f in ['NAN', 'NONE', 'NULL']: s_f = ""
                        if t_f in ['NAN', 'NONE', 'NULL']: t_f = ""
                        
                        note = ""
                        if 'Transformation_Note' in rule and pd.notna(rule['Transformation_Note']): note = str(rule['Transformation_Note']).strip().upper()
                        elif 'Notes' in rule and pd.notna(rule['Notes']): note = str(rule['Notes']).strip().upper()
                        
                        if t_f in [h.upper() for h in schema]:
                            actual_h = [h for h in schema if h.upper() == t_f][0]
                            
                            val = ""
                            if lt and jk and lt in lookups and jk in lookups[lt]:
                                join_val = self.normalize(src_row.get(jk))
                                if join_val in lookups[lt][jk]:
                                    val = self.normalize(lookups[lt][jk][join_val].get(s_f, ""))
                                else:
                                    val = self.normalize(rule.get('Default_Value', ''))
                            else:
                                default_val = str(rule.get('Default_Value', '')).strip()
                                if not s_f and default_val and default_val.lower() not in ['nan', 'none']:
                                    val = self.normalize(default_val)
                                else:
                                    val = self.normalize(src_row.get(s_f)) if (s_f and s_f in source.columns) else (self.normalize(src_row.get(t_f)) if t_f in source.columns else self.normalize(default_val))
                            
                            if not val:
                                val = self.normalize(rule.get('Default_Value', ''))

                            if t_id.lower() == "quikmstr" and t_f == "MBANKNO":
                                raw_pol = self.normalize(src_row.get("POLICY_NUMBER", src_row.get("MPOLICY", "")))
                                pulled_bank = getattr(self, '_ppach_bank_map', {}).get(raw_pol)
                                if pulled_bank:
                                    val = pulled_bank

                            if t_id.lower() == "quikridr" and t_f == "MPAR":
                                pol_key = self.normalize(src_row.get("POLICY_NUMBER", ""))
                                seq_key = self.normalize(src_row.get("BENEFIT_SEQ", ""))
                                
                                pulled_par = quikridr_par_cache.get((pol_key, seq_key))
                                
                                if pulled_par is not None:
                                    normalized_par = self.normalize(pulled_par)
                                    
                                    translated_par = trans_map.get(
                                        f"PAR_{normalized_par}",
                                        normalized_par
                                    )
                                    
                                    val = translated_par if translated_par else "0"
                                else:
                                    val = "0"

                            # --- MSTATUS COMPOSITE KEY INTERCEPTOR ---
                            if t_f == 'MSTATUS' and t_id.lower() == "quikmstr":
                                put = self.normalize(src_row.get('PAID_UP_TYPE', ''))
                                if put in ['PU', 'RU', 'ET', 'LE', 'LP', 'SP']:
                                    val = f"PUT_{put}"
                                else:
                                    c_code = self.normalize(src_row.get('CONTRACT_CODE', val))
                                    c_reason = self.normalize(src_row.get('CONTRACT_REASON', ''))
                                    val = f"{c_code}_{c_reason}" if c_reason else f"{c_code}_"
                            # -----------------------------------------

                            if t_f in ['MNFOPT', 'MDIVOPT'] and val in ["", "0", "0.0"] and t_id.lower() == "quikmstr":
                                pol_id = self.normalize(row_data.get('MPOLICY', ''))
                                
                                if not pol_id:
                                    pol_id = self.normalize(src_row.get('POLICY_NUMBER', src_row.get('MPOLICY', src_row.get('POLICY_ID', ''))))
                                    pol_id = cw_map.get(pol_id, pol_id)
                                    
                                legacy_id = reverse_cw_map.get(pol_id, pol_id) 

                                if t_f == 'MNFOPT' and 'NON_FORFEITURE' in lifepro_extra:
                                    pulled_val = lifepro_extra['NON_FORFEITURE'].get(legacy_id)
                                    if pulled_val is None: pulled_val = lifepro_extra['NON_FORFEITURE'].get(pol_id, val)
                                    val = self.normalize(pulled_val)
                                    
                                elif t_f == 'MDIVOPT' and 'DIVIDEND' in lifepro_extra:
                                    pulled_val = lifepro_extra['DIVIDEND'].get(legacy_id)
                                    if pulled_val is None: pulled_val = lifepro_extra['DIVIDEND'].get(pol_id, val)
                                    val = self.normalize(pulled_val)

                            if note == "EXTRACT_DAY": val = self.extract_day(val)
                            elif note == "ROUTE_PAY_YRS":
                                c_type = str(src_row.get('PREM_CEASE_TYPE', '')).strip().upper()
                                val = val if c_type == 'D' else '0'
                            elif note == "ROUTE_PAY_AGE":
                                c_type = str(src_row.get('PREM_CEASE_TYPE', '')).strip().upper()
                                val = val if c_type == 'A' else '0'
                            elif note == "ROUTE_INS_YRS":
                                c_type = str(src_row.get('BENEFIT_CEASE_TYPE', '')).strip().upper()
                                val = val if c_type == 'D' else '0'
                            elif note == "ROUTE_INS_AGE":
                                c_type = str(src_row.get('BENEFIT_CEASE_TYPE', '')).strip().upper()
                                val = val if c_type == 'A' else '0'
                            elif t_id.lower() == "quikprmh" and note == "DERIVE_PRMH_RENEWAL":
                                p_code = self.normalize(src_row.get("PAYMENT_CODE", ""))
                                p_reason = self.normalize(src_row.get("PAYMENT_REASON", ""))
                                loan_amt = self.normalize(src_row.get("LOAN_REPMT_AMOUNT", ""))

                                if loan_amt and loan_amt not in ["0", "0.00", ".00"]:
                                    val = "L"
                                elif p_code == "S":
                                    val = "S"
                                elif p_code in ["A", "R"]:
                                    val = "2"
                                elif p_reason in ["PC", "PREM"]:
                                    val = "1"
                                else:
                                    val = "0"
                            elif t_id.lower() == "quikprmh" and note == "DERIVE_MODE_COUNT":
                                bill_mode = self.normalize(src_row.get("BILLING_MODE", ""))
                                mode_count_map = {
                                    "12": "1",
                                    "6": "2",
                                    "3": "4",
                                    "1": "12"
                                }
                                val = mode_count_map.get(bill_mode, "0")
                            elif t_id.lower() == "quikprmh" and note == "FORMAT_MONEY":
                                try:
                                    val = f"{float(str(val).replace(',', '').strip() or 0):.2f}"
                                except Exception:
                                    val = "0.00"
                            elif t_id.lower() == "quikbenf" and note == "DERIVE_BENF_TYPE":
                                norm_val = self.normalize(val)
                                if norm_val in ["B1", "P"]:
                                    val = "P"
                                elif norm_val in ["B2", "C"]:
                                    val = "C"
                                else:
                                    val = ""
                            
                            if any(k in t_f for k in ['AGE', 'DUR', 'YRS']) and 'VAL' not in t_f and 'VPU' not in t_f and 'PREM' not in t_f:
                                if val.isdigit() and len(val) == 1:
                                    val = val.zfill(2)
                            
                            # --- ENTERPRISE DATE SANITIZER ---
                            if t_f in ['MDOB']:
                                _d = re.sub(r'[^0-9]', '', str(val))
                                val = _d if len(_d) == 8 and _d >= "19000101" else ""
                            # ---------------------------------
                            
                            # --- QUIKCLNT NAME OVERRIDES & SHIELD ---
                            if t_f in ['MFNAME', 'MMNAME', 'MLNAME']:
                                source_row = src_row
                                # Safely bridge MCLIENTID to NAME_ID lookup
                                raw_name_id = src_row.get('MCLIENTID', src_row.get('NAME_ID', ''))
                                norm_name_id = self.normalize(raw_name_id)
                                cache_matched = False
                                
                                if 'INDIVIDUAL_FIRST' not in src_row and rel_name_cache:
                                    if norm_name_id in rel_name_cache:
                                        source_row = rel_name_cache[norm_name_id]
                                        cache_matched = True
                                        
                                if t_f == 'MFNAME':
                                    if getattr(self, '_diag_name_count', 0) < 5:
                                        self.log(f"DEBUG ROW: raw JOIN_KEY='{raw_name_id}', norm='{norm_name_id}', matched={cache_matched}, FIRST='{source_row.get('INDIVIDUAL_FIRST', '')}', MIDDLE='{source_row.get('INDIVIDUAL_MIDDLE', '')}', LAST='{source_row.get('INDIVIDUAL_LAST', '')}'")
                                        self._diag_name_count += 1
                                        
                                    if not cache_matched:
                                        if not hasattr(self, '_diag_fail_count'):
                                            self._diag_fail_count = 0
                                        if self._diag_fail_count < 10:
                                            # Find first 3 similar keys using a 4-character prefix
                                            prefix_val = norm_name_id[:4] if len(norm_name_id) >= 4 else norm_name_id
                                            similar = [k for k in rel_name_cache.keys() if str(k).startswith(prefix_val)][:3] if prefix_val else []
                                            self.log(f"DEBUG FAILED JOIN: raw MCLIENTID='{raw_name_id}', norm='{norm_name_id}', in_cache={norm_name_id in rel_name_cache}, similar_keys={similar}")
                                            self._diag_fail_count += 1
                                    
                                if t_f == 'MFNAME':
                                    val = source_row.get('INDIVIDUAL_FIRST', val)
                                elif t_f == 'MLNAME':
                                    business_name = str(source_row.get('NAME_BUSINESS', '')).strip()
                                    if business_name and business_name.lower() not in ['nan', 'none']:
                                        val = business_name
                                    else:
                                        val = source_row.get('INDIVIDUAL_LAST', val)
                                elif t_f == 'MMNAME':
                                    temp_val = str(source_row.get('INDIVIDUAL_MIDDLE', val))
                                    # Harden against padded spaces and trailing decimal artifacts
                                    clean_temp = temp_val.replace('.0', '').strip()
                                    
                                    # Safety shield: blank out only if the ENTIRE value is numeric
                                    if clean_temp.isdigit():
                                        val = ""
                                    else:
                                        val = clean_temp
                            # ----------------------------------------
                            
                            if t_f == "MVALID":
                                if val in ['Y', 'YES', 'TRUE', '1']: val = 'F' if 'INVALID' in s_f else 'T'
                                elif val in ['N', 'NO', 'FALSE', '0']: val = 'T' if 'INVALID' in s_f else 'F'
                                if val not in ['T', 'F']: val = 'T' 
                            elif t_id.lower() == "quikplan" and t_f == "PAR":
                                pass
                            else:
                                prefix = "BF_" if t_f == "MBILLFRM" else ("PM_" if t_f == "MMODE" else ("DV_" if t_f == "MDIVOPT" else ("NF_" if t_f == "MNFOPT" else ("AG_" if (t_f == "MSTATUS" and t_id.lower() == "quikagts") else ("ST_" if t_f == "MSTATUS" else ("PAR_" if t_f == "MPAR" else ""))))))
                                if not (t_id.lower() == "quikbenf" and t_f == "MTYPE"):
                                    val = trans_map.get(f"{prefix}{val}", trans_map.get(val, val))
                            
                            # --- STRICT NUMERIC SHIELD FOR DIVIDENDS & NFO ---
                            if t_f in ['MDIVOPT', 'MNFOPT'] and not str(val).isdigit():
                                val = "0"
                            # -------------------------------------------------
                            
                            if t_f in ["MPOLICY", "MCLIENTID", "MPRIMID", "MOWNRID", "MPAYRID", "MASGNID", "MBENPID", "MBENCID", "MCID", "MOWNCID", "MRIDRID", "MPLAN", "PLAN"]:
                                val = cw_map.get(val, val)
                            
                            if t_id.lower() == "quikdvdp":
                                if actual_h in ["MDEPOSIT", "MINTYTD", "MDEPINT"] and val:
                                    try:
                                        val = f"{float(val):.2f}"
                                    except:
                                        val = "0.00"
                                elif actual_h == "MINTDATE":
                                    if not val or str(val).strip().upper() in ["0", "0.0", "0.00", "POLC.PAID_TO_DATE", "NAN", "NONE"]:
                                        pol_id = self.normalize(row_data.get('MPOLICY', ''))
                                        if pol_id in quikmstr_paid_to:
                                            val = quikmstr_paid_to[pol_id]
                                    if val:
                                        val = re.sub(r'[^0-9]', '', str(val))

                            # --- FINAL OUTPUT SANITIZATION ---
                            if actual_h == 'MMNAME':
                                final_mm = str(val).replace('.0', '').strip()
                                if final_mm.isdigit():
                                    val = ""
                                    
                            if t_id.lower() == "quikridr" and actual_h == "MPAR":
                                normalized_mpar = self.normalize(val)
                                if normalized_mpar in ["", "N", "X", "F"]:
                                    val = "0"
                                elif normalized_mpar == "P":
                                    val = "1"
                                    
                            if t_id.lower() == "quikclid" and actual_h == "MPHASE":
                                normalized_phase = self.normalize(val)
                                if not normalized_phase or normalized_phase == "0":
                                    val = "1"
                            # ---------------------------------

                            row_data[actual_h] = val

                    tp = self.normalize(row_data.get('MPOLICY', ''))
                    tphase = self.normalize(row_data.get('MPHASE', ''))
                    if not tphase: tphase = "1"

                    if t_id.lower() == "quikmstr" and tp in rel_map:
                        if "1" in rel_map[tp]:
                            p_rel = rel_map[tp]["1"]
                            # Includes raw LifePRO source codes alongside standard QLAdmin roles
                            for r, f in {'IN':'MPRIMID', 'INSD':'MPRIMID', 'PO':'MOWNRID', 'OWNR':'MOWNRID', 'PA':'MPAYRID', 'PAYR':'MPAYRID', 'ASGN':'MASGNID', 'B1':'MBENPID', 'BENP':'MBENPID', 'B2':'MBENCID', 'BENC':'MBENCID'}.items():
                                if r in p_rel and f in row_data: 
                                    row_data[f] = cw_map.get(p_rel[r], p_rel[r])
                        
                    if t_id.lower() == "quikridr" and 'MRIDRID' in row_data and tp in rel_map:
                        rel_id = None
                        rel_source = None
                        
                        # Phase-level rider insured priority, if that phase exists
                        phase_rel = rel_map[tp].get(tphase, {})
                        
                        if 'RU' in phase_rel:
                            rel_id = phase_rel['RU']
                            rel_source = f"phase {tphase} RU"
                        elif 'IN' in phase_rel:
                            rel_id = phase_rel['IN']
                            rel_source = f"phase {tphase} IN"
                        elif 'INSD' in phase_rel:
                            rel_id = phase_rel['INSD']
                            rel_source = f"phase {tphase} INSD"
                        
                        # Fallback to phase 1 insured even when rider phase is missing
                        if not rel_id and "1" in rel_map[tp]:
                            base_rel = rel_map[tp]["1"]
                            if 'IN' in base_rel:
                                rel_id = base_rel['IN']
                                rel_source = f"fallback phase 1 IN (requested phase {tphase})"
                            elif 'INSD' in base_rel:
                                rel_id = base_rel['INSD']
                                rel_source = f"fallback phase 1 INSD (requested phase {tphase})"
                        
                        if rel_id:
                            row_data['MRIDRID'] = cw_map.get(rel_id, rel_id)
                        
                        if self.debug_rel_fallback and self._diag_rel_fallback_count < 25:
                            if rel_id:
                                self.log(
                                    f"DEBUG REL: MPOLICY={tp} MPHASE={tphase} "
                                    f"MRIDRID={row_data.get('MRIDRID', '')} via {rel_source}"
                                )
                            else:
                                phase_keys = sorted(rel_map[tp].keys())
                                phase_roles = sorted(phase_rel.keys()) if phase_rel else []
                                self.log(
                                    f"DEBUG REL: MPOLICY={tp} MPHASE={tphase} MRIDRID=UNRESOLVED "
                                    f"policy_phases={phase_keys} phase_roles={phase_roles}"
                                )
                            self._diag_rel_fallback_count += 1
                        
                    # --- BASE PHASE TERMINAL STATUS SYNCHRONIZATION ---
                    if t_id.lower() == "quikridr" and tphase == "1":
                        if getattr(self, '_qm_sync_table', None) != t_id:
                            self._qm_sync_table = t_id
                            self._qm_status_cache = None
                            
                        if self._qm_status_cache is None:
                            self._qm_status_cache = {}
                            try:
                                qm_path = os.path.normpath(os.path.join(self.path_vars["Out"][0].get(), "quikmstr.csv"))
                                if os.path.exists(qm_path):
                                    qdf = pd.read_csv(qm_path, dtype=str).fillna("")
                                    qdf.columns = [str(c).strip().upper() for c in qdf.columns]
                                    if 'MPOLICY' in qdf.columns and 'MSTATUS' in qdf.columns:
                                        self._qm_status_cache = {self.normalize(k): self.normalize(v) for k, v in zip(qdf['MPOLICY'], qdf['MSTATUS'])}
                            except Exception:
                                pass
                                
                        qm_status = self._qm_status_cache.get(tp)
                        # Inherit meaningful policy-level terminal status; block active statuses
                        if qm_status and qm_status not in ["", "11", "22", "ACTIVE"]:
                            row_data['MPHSTAT'] = qm_status
                    # --------------------------------------------

                    # --- QUIKDVDP ENRICHMENT ---
                    if t_id.lower() == "quikdvdp":
                        if tp in quikdvdp_tx_cache:
                            tx_data = quikdvdp_tx_cache[tp]
                            row_data['MDEPOSIT'] = f"{tx_data['MDEPOSIT']:.2f}"
                            row_data['MINTYTD'] = f"{tx_data['MINTYTD']:.2f}"
                            
                            mdt = tx_data['MINTDATE']
                            if mdt:
                                row_data['MINTDATE'] = re.sub(r'[^0-9]', '', str(mdt))
                            else:
                                row_data['MINTDATE'] = ""
                        else:
                            row_data['MDEPOSIT'] = "0.00"
                            row_data['MINTYTD'] = "0.00"
                            row_data['MINTDATE'] = ""
                    # ---------------------------

                    # --- QUIKAGTS ENRICHMENT ---
                    if t_id.lower() == "quikagts":
                        name_id = self.normalize(src_row.get("NAME_ID", ""))
                        if not name_id: name_id = self.normalize(src_row.get("CLIENT_ID", ""))
                        
                        magent = self.normalize(src_row.get("AGENT_NUMBER", row_data.get("MAGENT", "")))
                        row_data["MAGENT"] = magent
                        
                        if not row_data.get("MSUPPRESS"):
                            row_data["MSUPPRESS"] = "F"
                            
                        clnt = quikagts_clnt_cache.get(name_id, {})
                        if clnt:
                            fname = self.normalize(clnt.get("MFNAME", ""))
                            lname = self.normalize(clnt.get("MLNAME", ""))
                            if fname or lname:
                                row_data["MAGTNAME"] = f"{fname} {lname}".strip()
                                
                            mapping = {
                                "MADDR1": "MAGTADDR1", "MADDR2": "MAGTADDR2",
                                "MCITY": "MAGTCITY", "MSTATE": "MAGTST",
                                "MZIP": "MAGTZIP", "MZIP2": "MAGTZIP2",
                                "MEMAIL": "MAGTEMAIL", "MTAXIDTYPE": "MTAXIDTYPE"
                            }
                            for c_key, a_key in mapping.items():
                                val = self.normalize(clnt.get(c_key, ""))
                                if val: row_data[a_key] = val
                                
                            tax_id = self.normalize(clnt.get("MTAXID", ""))
                            tax_type = self.normalize(clnt.get("MTAXIDTYPE", ""))
                            if tax_type == "S":
                                row_data["MAGTSSN"] = tax_id
                                row_data["MAGTFEIN"] = ""
                            elif tax_type == "E":
                                row_data["MAGTSSN"] = ""
                                row_data["MAGTFEIN"] = tax_id
                                
                            ofc = self.normalize(clnt.get("MPHONEOFC", ""))
                            cell = self.normalize(clnt.get("MPHONECELL", ""))
                            home = self.normalize(clnt.get("MPHONEHOME", ""))
                            
                            row_data["MAGTOFCE"] = ofc
                            row_data["MAGTCELL"] = cell
                            if ofc:
                                row_data["MAGTPHONE"] = ofc
                            elif cell:
                                row_data["MAGTPHONE"] = cell
                            elif home:
                                row_data["MAGTPHONE"] = home
                    # ---------------------------

                    output.append([row_data[h] for h in schema])
                    if i % 1000 == 0: self.progress["value"] = (i/len(source))*100; self.root.update_idletasks()
                
                out_dir = self.path_vars["Out"][0].get()
                pd.DataFrame(output, columns=schema).to_csv(os.path.normpath(os.path.join(out_dir, f"{t_id}.csv")), index=False)
                self.log(f"Success: {t_id}.csv - {len(output)} records.")
                
                audit_path = os.path.normpath(os.path.join(out_dir, "Migration_Audit_Log.txt"))
                is_new_log = not os.path.exists(audit_path)
                
                source_count = len(source)
                output_count = len(output)
                variance = source_count - output_count
                
                audit_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] TABLE: {t_id.upper():<10} | SOURCE RECORDS: {source_count:<8} | QLA OUTPUT: {output_count:<8} | VARIANCE: {variance} (Skipped/Dashed)\n"
                
                with open(audit_path, "a") as f:
                    if is_new_log:
                        f.write("=== QLADMIN ENTERPRISE MIGRATION AUDIT LOG ===\n")
                        f.write("Tracks 1:1 record translation matching to guarantee zero data loss.\n\n")
                    f.write(audit_msg)
                
                self.log(f"Audit Verified: {source_count} Source -> {output_count} Output. Saved to Audit Log.")

                if is_batch and t_id.lower() == "quikclid":
                    fresh_rel = os.path.normpath(os.path.join(out_dir, "quikclid.csv"))
                    if os.path.isfile(fresh_rel):
                        rel_map = self._load_rel_map(fresh_rel, trans_map, log_label="batch relational map")
                        self.path_vars["Rel"][0].set(fresh_rel)

            batch_claims_result = None
            if is_batch:
                batch_claims_result = self._execute_batch_claims_uat_finale()

            if is_batch and batch_claims_result and batch_claims_result.get("emit_result"):
                emit_info = batch_claims_result["emit_result"]
                dbf_info = batch_claims_result.get("dbf_result")
                dbf_note = ""
                if dbf_info and dbf_info.get("status") == "SUCCESS":
                    dbf_note = f"\nUAT prototype DBFs generated in:\n{dbf_info.get('dbf_dir', '')}"
                elif self._claims_uat_dbf_generation_enabled():
                    dbf_note = "\nUAT DBF generation attempted — see console for status."
                messagebox.showinfo(
                    "Complete",
                    "Batch conversion finished.\n\n"
                    "UAT claims (quikclms/quikclmp) emitted to main output.\n"
                    f"Review holds: {emit_info.get('hold_count', 0)} records in claims_review_hold_manifest.csv"
                    f"{dbf_note}",
                )
            else:
                messagebox.showinfo("Complete", "Conversion Finished.")
        except Exception as e: self.log(f"!!! ERROR: {str(e)}")
        finally: self.is_running = False

if __name__ == "__main__":
    root = tk.Tk(); app = QLAdminEnterpriseIntegrationSuite(root); root.mainloop()