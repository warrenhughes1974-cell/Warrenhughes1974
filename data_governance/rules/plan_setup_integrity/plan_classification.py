"""Optional plan classification config for MYGA / UL / single-premium checks."""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field

_CONFIG_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "config", "plan_classification.csv")
)


@dataclass
class PlanClassificationConfig:
    available: bool = False
    myga_plans: set[str] = field(default_factory=set)
    ul_plans: set[str] = field(default_factory=set)
    single_premium_plans: set[str] = field(default_factory=set)
    initval_exceptions: set[str] = field(default_factory=set)


def _norm_plan(value: str) -> str:
    return (value or "").strip()


def _is_y(value: str) -> bool:
    return (value or "").strip().upper() == "Y"


def load_plan_classification(path: str | None = None) -> PlanClassificationConfig:
    cfg_path = path or _CONFIG_PATH
    result = PlanClassificationConfig()
    if not os.path.isfile(cfg_path):
        return result

    has_y_flag = False
    try:
        with open(cfg_path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            if not reader.fieldnames:
                return result
            for row in reader:
                plan = _norm_plan(row.get("PLAN", ""))
                if not plan:
                    continue
                if _is_y(row.get("IS_MYGA", "")):
                    result.myga_plans.add(plan)
                    has_y_flag = True
                if _is_y(row.get("IS_UL", "")):
                    result.ul_plans.add(plan)
                    has_y_flag = True
                if _is_y(row.get("IS_SINGLE_PREMIUM", "")):
                    result.single_premium_plans.add(plan)
                    has_y_flag = True
                if _is_y(row.get("INITVAL_EXCEPTION", "")):
                    result.initval_exceptions.add(plan)
    except OSError:
        return PlanClassificationConfig()

    result.available = has_y_flag
    return result


def is_myga(config: PlanClassificationConfig, plan: str) -> bool:
    return plan in config.myga_plans


def is_ul(config: PlanClassificationConfig, plan: str) -> bool:
    return plan in config.ul_plans


def is_single_premium(config: PlanClassificationConfig, plan: str) -> bool:
    return plan in config.single_premium_plans


def has_initval_exception(config: PlanClassificationConfig, plan: str) -> bool:
    return plan in config.initval_exceptions
