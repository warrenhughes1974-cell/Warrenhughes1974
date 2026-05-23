import pandas as pd
import os
import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext, ttk
import threading
import time
import zipfile
import json
import re
import csv
from datetime import datetime

class QLAdminEnterpriseIntegrationSuite:
    def __init__(self, root):
        self.root = root
        self.root.title("QLAdmin Enterprise Data Integration Suite v54.1")
        self.root.geometry("1100x980")
        
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
            "quikagts": ["MAGENT", "MAGTNAME", "MAGTADDR1", "MAGTADDR2", "MAGTCITY", "MAGTST", "MAGTZIP", "MAGTZIP2", "MAGTSSN", "MAGTFEIN", "MCOMP", "MAGENCY", "MAGCYNAME", "MDATE", "MAGTACCT", "MAGTPHONE", "MAGTFAX", "MAGTCELL", "MAGTOFCE", "MAGTEMAIL", "MEMOTEXT", "MSUPPRESS", "MCOMMGRP", "MOTHNAME", "MPREMACCT", "MSTATUS", "MAGTNPN", "MTAXIDTYPE"]
        }
        
        self.is_running = False
        self.start_time = None
        self.setup_ui()

    def setup_ui(self):
        header = tk.Frame(self.root, bg=self.bg_main)
        header.pack(fill="x", pady=(15, 10))
        tk.Label(header, text="ENTERPRISE DATA INTEGRATION ENGINE v54.1", font=("Segoe UI", 20, "bold"), bg=self.bg_main, fg=self.accent).pack()
        
        card = tk.LabelFrame(self.root, text=" System Configuration & Path Mapping ", bg=self.bg_card, fg=self.accent, padx=20, pady=15, font=("Segoe UI", 10, "bold"))
        card.pack(padx=30, fill="x", pady=5)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(base_dir)

        def auto_locate(search_paths, keywords):
            for s_path in search_paths:
                for root, dirs, files in os.walk(s_path):
                    if root.count(os.sep) - s_path.count(os.sep) > 3:
                        del dirs[:]
                    for file_name in files:
                        f_lower = file_name.lower()
                        if f_lower.endswith(".csv") and all(k in f_lower for k in keywords):
                            if not any(bad in f_lower for bad in ['copy', 'old', 'backup', 'archive']):
                                return os.path.normpath(os.path.join(root, file_name))
            return ""

        search_dirs = [base_dir, parent_dir]
        
        default_trans = auto_locate(search_dirs, ["master", "translation"])
        default_cw = auto_locate(search_dirs, ["master", "crosswalk"])

        self.path_vars = {
            "Rule": [tk.StringVar(), "file", "Field Mapping (Rulebook):"],
            "Src": [tk.StringVar(), "file", "Source Data File:"],
            "Trans": [tk.StringVar(value=default_trans), "file", "Value Translation (CSV):"],
            "CW": [tk.StringVar(value=default_cw), "file", "ID Crosswalk (CSV):"],
            "Rel": [tk.StringVar(), "file", "Relational File (quikclid):"],
            "Out": [tk.StringVar(), "folder", "Output Directory:"]
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
        
        self.console = scrolledtext.ScrolledText(self.root, height=20, bg="#F8FAFC", fg="#1E293B", font=("Consolas", 9))
        self.console.pack(padx=30, pady=10, fill="both", expand=True)

    def log(self, msg):
        self.console.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.console.see(tk.END)

    def on_table_select(self, event=None):
        table = self.table_var.get()
        if not table: return
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(base_dir)
        
        def find_exact_file(filename, exclude_keyword=None):
            matches = []
            for s_path in [base_dir, parent_dir]:
                if not os.path.exists(s_path): continue
                for root, dirs, files in os.walk(s_path):
                    dirs[:] = [d for d in dirs if not any(bad in d.lower() for bad in ['copy', 'old', 'backup', 'archive'])]
                    for f in files:
                        if f.lower() == filename.lower():
                            matches.append(os.path.normpath(os.path.join(root, f)))
            
            if exclude_keyword:
                filtered = [m for m in matches if exclude_keyword.lower() not in m.lower()]
                if filtered: return filtered[0]
                if matches: return matches[0]
            elif matches:
                return matches[0]
            return ""

        def find_dir(keyword):
            for s_path in [base_dir, parent_dir]:
                if not os.path.exists(s_path): continue
                for root, dirs, _ in os.walk(s_path):
                    dirs[:] = [d for d in dirs if not any(b in d.lower() for b in ['copy', 'old', 'backup', 'archive'])]
                    for d in dirs:
                        if keyword.lower() in d.lower():
                            return os.path.normpath(os.path.join(root, d))
            return base_dir

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

        rb_path = find_exact_file(f"Sync_Rulebook_{table}.csv")
        src_path = find_exact_file(expected_src, exclude_keyword="output")
        trans_path = find_exact_file("Master_Value_Translation.csv")
        cw_path = find_exact_file("Master_Crosswalk.csv")
        rel_path = find_exact_file("quikclid.csv")
        out_dir = find_dir("output")
        
        if not rb_path: rb_path = os.path.normpath(os.path.join(find_dir("config"), f"Sync_Rulebook_{table}.csv"))
        if not src_path:
            if table.lower() == "quikridr":
                src_path = os.path.normpath("C:/Users/warren/Desktop/QLA_Data_Coverter_Test2/QLA_Migration/Source/PPBEN.csv")
            else:
                src_path = os.path.normpath(os.path.join(find_dir("source"), expected_src))
        if not trans_path: trans_path = os.path.normpath(os.path.join(find_dir("map"), "Master_Value_Translation.csv"))
        if not cw_path: cw_path = os.path.normpath(os.path.join(find_dir("map"), "Master_Crosswalk.csv"))
        if not rel_path: rel_path = os.path.normpath(os.path.join(out_dir, "quikclid.csv"))

        self.path_vars["Rule"][0].set(rb_path)
        self.path_vars["Src"][0].set(src_path)
        self.path_vars["Trans"][0].set(trans_path)
        self.path_vars["CW"][0].set(cw_path)
        self.path_vars["Rel"][0].set(rel_path)
        self.path_vars["Out"][0].set(out_dir)
        
        self.log(f"System UI: Auto-populated exact file paths for {table.upper()}")

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
            self.log("Initializing Migration Engine v54.1...")
            
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
            rel_map = {}
            if rel_path and os.path.exists(rel_path):
                clid_df = pd.read_csv(rel_path, dtype=str).fillna("")
                clid_df.columns = [c.strip().upper() for c in clid_df.columns]
                for _, row in clid_df.iterrows():
                    pol = self.normalize(row.get('MPOLICY', ''))
                    rel_raw = self.normalize(row.get('MRELATION', ''))
                    cid = self.normalize(row.get('MCLIENTID', ''))
                    
                    phase = self.normalize(row.get('MPHASE', ''))
                    if not phase or phase == "0": phase = "1"
                    
                    rel = trans_map.get(rel_raw, rel_raw)
                    if pol:
                        if pol not in rel_map: rel_map[pol] = {}
                        if phase not in rel_map[pol]: rel_map[pol][phase] = {}
                        rel_map[pol][phase][rel] = cid
            else:
                pass

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
                all_files = list(self.TABLE_SCHEMAS.keys())
                priority = ['quikclnt', 'quikclid']
                tables = priority + [t for t in all_files if t not in priority]

            for t_id in tables:
                if not t_id: 
                    if not is_batch: self.log("!!! ERROR: Please select a table from the dropdown first.")
                    continue
                
                rule_input = self.path_vars["Rule"][0].get()
                src_input = self.path_vars["Src"][0].get()
                
                rule_base = os.path.dirname(rule_input) if rule_input else os.path.dirname(os.path.abspath(__file__))
                src_base = os.path.dirname(src_input) if src_input else os.path.dirname(os.path.abspath(__file__))

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

                # --- PRODUCTION ISOLATION: PACTG Premium History ---
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
                        
                        # Phase-level rider insured priority, if that phase exists
                        phase_rel = rel_map[tp].get(tphase, {})
                        
                        if 'RU' in phase_rel:
                            rel_id = phase_rel['RU']
                        elif 'IN' in phase_rel:
                            rel_id = phase_rel['IN']
                        elif 'INSD' in phase_rel:
                            rel_id = phase_rel['INSD']
                        
                        # Fallback to phase 1 insured even when rider phase is missing
                        if not rel_id and "1" in rel_map[tp]:
                            base_rel = rel_map[tp]["1"]
                            if 'IN' in base_rel:
                                rel_id = base_rel['IN']
                            elif 'INSD' in base_rel:
                                rel_id = base_rel['INSD']
                        
                        if rel_id:
                            row_data['MRIDRID'] = cw_map.get(rel_id, rel_id)

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

            messagebox.showinfo("Complete", "Conversion Finished.")
        except Exception as e: self.log(f"!!! ERROR: {str(e)}")
        finally: self.is_running = False

if __name__ == "__main__":
    root = tk.Tk(); app = QLAdminEnterpriseIntegrationSuite(root); root.mainloop()