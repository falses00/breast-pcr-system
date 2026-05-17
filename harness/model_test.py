"""模型 harness：验证规则模型与轻量 ML 模型输出 0-1 概率。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.services.ml_model import DemoClinicalMLModel  # noqa: E402
from app.services.pcr_model import rule_based_pcr_prediction  # noqa: E402


def main() -> int:
    rule = rule_based_pcr_prediction(
        age=45,
        er_status="阳性",
        pr_status="阳性",
        her2_status="阳性",
        ki67=35,
        lesion_area=820,
        gray_mean=125,
    )
    assert 0.0 <= rule.probability <= 1.0
    assert rule.explanations

    model = DemoClinicalMLModel()
    model.fit_demo()
    prob = model.predict_probability([45, 1, 1, 1, 35, 820, 125])
    assert 0.0 <= prob <= 1.0
    print("模型 harness: 通过", {"rule": round(rule.probability, 4), "ml": round(prob, 4)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
