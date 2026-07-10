"""Smoke test: governance progress callback + UI progress mapping (no Tk mainloop)."""
from __future__ import annotations

import os
import sys
import tempfile
import time

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from data_governance import run_governance  # noqa: E402
from data_governance.rules import CHECK_PIPELINE  # noqa: E402
from qla_core import run_logging as RL  # noqa: E402


class _FakeWidget:
    def __init__(self, **kwargs):
        self._vals = dict(kwargs)

    def config(self, **kwargs):
        self._vals.update(kwargs)

    def cget(self, key):
        return self._vals.get(key, "")

    def __setitem__(self, key, value):
        self._vals[key] = value

    def __getitem__(self, key):
        return self._vals.get(key, 0)


def test_stage_plan():
    plan = RL.stage_plan("governance_audit")
    assert len(plan) == 5
    assert plan[0] == (1, "Initializing governance audit", 5)
    assert plan[-1][2] == 100


def test_progress_callback_and_ui_mapping():
    app_progress = _FakeWidget(value=0)
    lbl_stage = _FakeWidget(text="Stage 0")
    lbl_detail = _FakeWidget(text="")
    lbl_timer = _FakeWidget(text="Elapsed: 00:00:00")
    snapshots = []
    progress_plan = RL.stage_plan("governance_audit")

    def update_progress(stage_percent, stage_message):
        if stage_percent is not None:
            app_progress["value"] = max(0, min(100, stage_percent))
        lbl_stage.config(text=stage_message)
        snapshots.append(
            {
                "pct": app_progress["value"],
                "stage": lbl_stage.cget("text"),
                "detail": lbl_detail.cget("text"),
            }
        )

    def update_run_progress(stage_number, detail=None):
        total = len(progress_plan)
        pct = name = None
        for no, nm, p in progress_plan:
            if no == stage_number:
                pct, name = p, nm
                break
        update_progress(pct, f"Stage {stage_number} of {total} — {name}")
        lbl_detail.config(text=detail or "")

    def governance_ui_progress(event, **kwargs):
        # Mirror app._governance_ui_progress
        if event == "load":
            update_run_progress(2, detail="Loading quik*.csv outputs")
        elif event == "check":
            idx = int(kwargs.get("index", 0))
            total = max(int(kwargs.get("total", 1)), 1)
            name = str(kwargs.get("name") or "check")
            pct = 20 + int(70 * ((idx + 1) / total))
            update_progress(
                pct,
                f"Stage 3 of {len(progress_plan)} — Running governance rule checks",
            )
            lbl_detail.config(text=f"Check {idx + 1}/{total}: {name}")
        elif event == "report":
            update_run_progress(4, detail="Writing HTML / CSV / log reports")
        elif event == "done":
            update_run_progress(
                5, detail=f"Findings={kwargs.get('total_findings')}"
            )

    # Simulate timer tick (same formula as app.update_timer)
    start_time = time.time()
    time.sleep(1.05)
    lbl_timer.config(text=f"Elapsed: {RL.fmt_elapsed(time.time() - start_time)}")
    assert lbl_timer.cget("text").startswith("Elapsed: 00:00:0")
    assert lbl_timer.cget("text") != "Elapsed: 00:00:00"

    update_progress(0, "Stage 0 — Ready")
    update_run_progress(1, detail="Preparing Data Governance Audit")

    out = os.path.join(REPO, "QLA_Migration", "Output")
    assert os.path.isdir(out), out
    with tempfile.TemporaryDirectory() as td:
        report = run_governance(
            {
                "conversion_id": "UI-PROGRESS-TEST",
                "output_dir": out,
                "report_dir": td,
                "write_reports": True,
                "progress_callback": governance_ui_progress,
            }
        )
    update_progress(100, f"Complete — findings={report.total_findings}")

    pcts = [s["pct"] for s in snapshots]
    assert any(s["stage"].startswith("Stage 3") for s in snapshots)
    assert any("Check 1/" in s["detail"] for s in snapshots)
    assert any(f"Check {len(CHECK_PIPELINE)}/" in s["detail"] for s in snapshots)
    assert pcts[0] == 0
    assert pcts[-1] == 100
    assert max(pcts[:-1]) >= 55
    # Bar should climb across checks (not stuck)
    check_pcts = [s["pct"] for s in snapshots if s["stage"].startswith("Stage 3")]
    assert check_pcts[0] < check_pcts[-1]

    print("OK snapshots:", len(snapshots))
    print("  first:", snapshots[0])
    print("  mid:", next(s for s in snapshots if "Check 5/" in s["detail"]))
    print("  last:", snapshots[-1])
    print("  timer:", lbl_timer.cget("text"))
    print(f"  findings={report.total_findings}")


def test_app_methods_wired():
    import importlib.util

    for rel in ("app.py", os.path.join("QLA_Migration", "app.py")):
        path = os.path.join(REPO, rel)
        src = open(path, encoding="utf-8").read()
        assert "def _governance_ui_progress" in src
        assert 'start_run_progress("governance_audit")' in src
        assert "with_ui_progress=True" in src
        assert "threading.Thread(target=self.update_timer" in src
        assert 'APP_VERSION = "v57.68"' in src
        print(f"OK wired: {rel}")


if __name__ == "__main__":
    test_stage_plan()
    test_app_methods_wired()
    test_progress_callback_and_ui_mapping()
    print("ALL UI PROGRESS TESTS PASSED")
