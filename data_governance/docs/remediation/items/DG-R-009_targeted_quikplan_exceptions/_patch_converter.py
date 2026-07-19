from pathlib import Path

p = Path(__file__).resolve().parents[4] / "qla_core" / "quikplan_converter.py"
# parents: item -> items -> remediation -> docs -> data_governance -> repo
# Wait: item=.../DG-R-009..., parents[0]=item, [1]=items, [2]=remediation, [3]=docs, [4]=data_governance — wrong
# Fix path relative to repo via known location
repo = Path(__file__).resolve().parents[5]
# item(0)/items(1)/remediation(2)/docs(3)/data_governance(4)/repo(5) — yes 5
p = repo / "qla_core" / "quikplan_converter.py"
t = p.read_text(encoding="utf-8")

marker = "def apply_rate_variation_flag_enrichment("
if marker not in t:
    raise SystemExit("marker missing")

fn = '''def default_single_premium_plans_path(repo_root: str) -> str:
    return os.path.normpath(
        os.path.join(repo_root, "QLA_Migration", "Configs", "single_premium_plans.csv")
    )


def load_single_premium_plans(repo_root: str) -> set[str]:
    """Load confirmed single-premium PLAN codes (DG-R-009).

    Primary: QLA_Migration/Configs/single_premium_plans.csv (PLAN column).
    Also merges data_governance/config/plan_classification.csv rows with
    IS_SINGLE_PREMIUM = Y when that file is present.
    """
    plans: set[str] = set()
    primary = default_single_premium_plans_path(repo_root)
    if os.path.isfile(primary):
        try:
            cfg = pd.read_csv(primary, dtype=str)
            if "PLAN" in cfg.columns:
                for raw in cfg["PLAN"].fillna(""):
                    plan = normalize(raw)
                    if plan:
                        plans.add(plan)
        except Exception:
            pass
    class_path = os.path.normpath(
        os.path.join(repo_root, "data_governance", "config", "plan_classification.csv")
    )
    if os.path.isfile(class_path):
        try:
            cfg = pd.read_csv(class_path, dtype=str)
            if "PLAN" in cfg.columns and "IS_SINGLE_PREMIUM" in cfg.columns:
                for _, row in cfg.iterrows():
                    flag = str(row.get("IS_SINGLE_PREMIUM", "") or "").strip().upper()
                    if flag in ("Y", "YES", "1", "TRUE", "T"):
                        plan = normalize(row.get("PLAN", ""))
                        if plan:
                            plans.add(plan)
        except Exception:
            pass
    return plans


def apply_single_premium_payment_settings(
    df: pd.DataFrame,
    repo_root: str | None = None,
    log=None,
) -> pd.DataFrame:
    """Force single-premium payment settings on confirmed plans (DG-R-009).

    Sets PAYYRS=1, PAYAGE=0, and SEMI/QTRL/MTHD/MTHB=0.
    No-op when config is empty or PLAN column is missing.
    """
    if df is None or df.empty or "PLAN" not in df.columns:
        return df
    repo_root = repo_root or os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    plans = load_single_premium_plans(repo_root)
    if not plans:
        return df
    updated = 0
    for idx in df.index:
        plan = normalize(df.at[idx, "PLAN"])
        if plan not in plans:
            continue
        df.at[idx, "PAYYRS"] = "1"
        if "PAYAGE" in df.columns:
            df.at[idx, "PAYAGE"] = "0"
        for col in ("SEMI", "QTRL", "MTHD", "MTHB"):
            if col in df.columns:
                df.at[idx, col] = "0"
        updated += 1
    if log is not None and updated:
        try:
            log(f"Single-premium payment settings (DG-R-009): {updated} plans PAYYRS=1")
        except Exception:
            pass
    try:
        df.attrs["single_premium_payment_updated"] = updated
    except Exception:
        pass
    return df


'''

if "def apply_single_premium_payment_settings(" not in t:
    t = t.replace(marker, fn + marker, 1)

old = "    df = apply_rate_variation_flag_enrichment(df)\n    df = apply_cso_cv_assumptions(df)"
new = (
    "    df = apply_rate_variation_flag_enrichment(df)\n"
    "    df = apply_single_premium_payment_settings(df)\n"
    "    df = apply_cso_cv_assumptions(df)"
)
if "apply_single_premium_payment_settings(df)" not in t:
    if old not in t:
        raise SystemExit("wire marker missing")
    t = t.replace(old, new, 1)

p.write_text(t, encoding="utf-8", newline="\n")
print("patched", p)
print("repo", repo)
