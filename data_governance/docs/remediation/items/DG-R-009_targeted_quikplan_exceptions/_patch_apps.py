from pathlib import Path

REPO = Path(__file__).resolve().parents[5]


def patch_app(path: Path) -> None:
    t = path.read_text(encoding="utf-8")
    old_import = """from qla_core.quikplan_converter import (
    convert_quikplan_to_output,
    prepare_quikplan_source,
    apply_rate_variation_flag_enrichment,
    apply_ploan_loanint_enrichment,
)"""
    new_import = """from qla_core.quikplan_converter import (
    convert_quikplan_to_output,
    prepare_quikplan_source,
    apply_rate_variation_flag_enrichment,
    apply_single_premium_payment_settings,
    apply_ploan_loanint_enrichment,
)"""
    if "apply_single_premium_payment_settings" not in t:
        if old_import not in t:
            raise SystemExit(f"import block missing in {path}")
        t = t.replace(old_import, new_import, 1)

    old_call = """                    qdf = apply_rate_variation_flag_enrichment(qdf, self._app_base_dir())
                    current_stage = "Applying rulebooks and crosswalks"
                    self.update_run_progress(4, detail="plan/rate enrichments + CSO assumptions")
                    self.log(f"Rate variation flags applied (R7B): {int((qdf['PLANVALOPT'] == 'Y').sum())} plans PLANVALOPT=Y")"""
    new_call = """                    qdf = apply_rate_variation_flag_enrichment(qdf, self._app_base_dir())
                    qdf = apply_single_premium_payment_settings(qdf, self._app_base_dir(), log=self.log)
                    current_stage = "Applying rulebooks and crosswalks"
                    self.update_run_progress(4, detail="plan/rate enrichments + CSO assumptions")
                    self.log(f"Rate variation flags applied (R7B): {int((qdf['PLANVALOPT'] == 'Y').sum())} plans PLANVALOPT=Y")"""
    if "apply_single_premium_payment_settings(qdf" not in t:
        if old_call not in t:
            raise SystemExit(f"call site missing in {path}")
        t = t.replace(old_call, new_call, 1)

    # version bump once
    if 'APP_VERSION = "v58.09"' in t:
        t = t.replace('APP_VERSION = "v58.09"', 'APP_VERSION = "v58.10"', 1)
    # changelog near history if present
    needle = "#              v57.87"
    note = (
        "#              v58.10 — DG-R-009: single-premium quikplan payment settings "
        "(PAYYRS=1, PAYAGE/SEMI/QTRL/MTHD/MTHB=0) via Configs/single_premium_plans.csv.\n"
    )
    if "v58.10 — DG-R-009" not in t and needle in t:
        t = t.replace(needle, note + needle, 1)

    path.write_text(t, encoding="utf-8", newline="\n")
    print("patched", path)


patch_app(REPO / "app.py")
patch_app(REPO / "QLA_Migration" / "app.py")
