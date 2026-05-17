"""训练课程演示用 Clinical + ROI 机器学习模型。

该脚本使用模拟数据，输出 joblib 模型和基础评估指标；不使用真实患者数据。
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[3]
MODEL_DIR = ROOT / "data" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def demo_dataset() -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(2026)
    rows = []
    labels = []
    for _ in range(160):
        age = rng.integers(30, 78)
        er = rng.integers(0, 2)
        pr = rng.integers(0, 2)
        her2 = rng.integers(0, 2)
        ki67 = rng.uniform(5, 70)
        area = rng.uniform(300, 9000)
        gray_mean = rng.uniform(60, 180)
        score = -0.8 - 0.012 * age - 0.18 * er - 0.06 * pr + 0.55 * her2 + 0.018 * ki67 - 0.00009 * area + 0.004 * gray_mean
        prob = 1 / (1 + np.exp(-score))
        label = int(rng.random() < prob)
        rows.append([age, er, pr, her2, ki67, area, gray_mean])
        labels.append(label)
    return np.asarray(rows, dtype=float), np.asarray(labels, dtype=int)


def evaluate(name: str, model, x_test: np.ndarray, y_test: np.ndarray) -> dict:
    prob = model.predict_proba(x_test)[:, 1]
    pred = (prob >= 0.5).astype(int)
    return {
        "model_name": name,
        "accuracy": float(accuracy_score(y_test, pred)),
        "precision": float(precision_score(y_test, pred, zero_division=0)),
        "recall": float(recall_score(y_test, pred, zero_division=0)),
        "f1": float(f1_score(y_test, pred, zero_division=0)),
        "auc": float(roc_auc_score(y_test, prob)),
        "confusion_matrix": confusion_matrix(y_test, pred).tolist(),
    }


def main() -> int:
    x, y = demo_dataset()
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=42, stratify=y)
    models = {
        "Clinical-only Logistic Regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=500)),
        "Clinical + ROI Random Forest": RandomForestClassifier(n_estimators=120, random_state=42, min_samples_leaf=3),
    }
    metrics = []
    for name, model in models.items():
        model.fit(x_train, y_train)
        safe_name = name.lower().replace(" ", "_").replace("+", "plus").replace("-", "_")
        joblib.dump(model, MODEL_DIR / f"{safe_name}.joblib")
        metrics.append(evaluate(name, model, x_test, y_test))
    (MODEL_DIR / "demo_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
