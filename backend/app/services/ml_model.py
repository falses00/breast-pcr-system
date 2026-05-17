"""课程演示用轻量 ML 模型，后续可替换为 XGBoost/LightGBM。"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class DemoClinicalMLModel:
    """优先使用 scikit-learn LogisticRegression；不可用时退化为固定权重逻辑模型。"""

    fitted: bool = False
    model: object | None = None

    def fit_demo(self) -> None:
        x = [
            [45, 1, 1, 1, 35, 800, 125],
            [62, 1, 1, 0, 12, 6500, 90],
            [38, 0, 0, 1, 55, 500, 140],
            [71, 1, 0, 0, 8, 7200, 80],
            [51, 0, 1, 1, 40, 1300, 135],
            [58, 1, 1, 0, 18, 4000, 110],
        ]
        y = [1, 0, 1, 0, 1, 0]
        try:
            from sklearn.linear_model import LogisticRegression
            from sklearn.pipeline import make_pipeline
            from sklearn.preprocessing import StandardScaler

            self.model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500))
            self.model.fit(x, y)
        except Exception:
            self.model = None
        self.fitted = True

    def predict_probability(self, features: list[float]) -> float:
        if not self.fitted:
            self.fit_demo()
        if self.model is not None:
            return float(self.model.predict_proba([features])[0][1])

        age, er, pr, her2, ki67, area, gray = features
        z = -0.6 - 0.012 * age - 0.15 * er - 0.08 * pr + 0.45 * her2 + 0.018 * ki67 - 0.00008 * area + 0.004 * gray
        return 1 / (1 + math.exp(-z))
