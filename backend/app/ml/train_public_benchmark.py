"""训练公开小数据集教学基准模型。

该脚本使用 Breast Cancer Wisconsin Diagnostic 表格数据训练“良恶性分类”
基准模型。它不预测 pCR，也不处理 MRI，不作为临床诊断依据。
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.download_public_dataset import CSV_PATH, DATASET_PAGE, download


ROOT = Path(__file__).resolve().parents[3]
MODEL_DIR = ROOT / "data" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
METRICS_PATH = MODEL_DIR / "public_benchmark_metrics.json"
DISCLAIMER = "公开数据集仅用于课程项目机器学习流程展示，不作为真实临床诊断依据。"


def load_dataset() -> tuple[pd.DataFrame, pd.Series]:
    if not CSV_PATH.exists():
        download()
    df = pd.read_csv(CSV_PATH)
    df = df.drop(columns=[col for col in df.columns if col.lower().startswith("unnamed")], errors="ignore")
    df = df.drop(columns=["id"], errors="ignore")
    if "diagnosis" not in df.columns:
        raise RuntimeError("公开数据集缺少 diagnosis 标签列")
    y = (df["diagnosis"] == "M").astype(int)
    x = df.drop(columns=["diagnosis"])
    return x, y


def evaluate(name: str, estimator, x: pd.DataFrame, y: pd.Series) -> tuple[dict[str, object], object]:
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, stratify=y, random_state=42)
    pipeline = make_pipeline(StandardScaler(), estimator)
    pipeline.fit(x_train, y_train)
    prob = pipeline.predict_proba(x_test)[:, 1]
    pred = (prob >= 0.5).astype(int)
    metrics = {
        "model_name": name,
        "data_source": "public_wisconsin_diagnostic",
        "task_kind": "公开表格良恶性分类基准（非pCR、非MRI）",
        "sample_count": int(len(y)),
        "test_count": int(len(y_test)),
        "accuracy": float(accuracy_score(y_test, pred)),
        "precision": float(precision_score(y_test, pred, zero_division=0)),
        "recall": float(recall_score(y_test, pred, zero_division=0)),
        "f1": float(f1_score(y_test, pred, zero_division=0)),
        "auc": float(roc_auc_score(y_test, prob)),
        "confusion_matrix": confusion_matrix(y_test, pred).tolist(),
        "source_url": DATASET_PAGE,
        "disclaimer": DISCLAIMER,
    }
    return metrics, pipeline


def main() -> int:
    x, y = load_dataset()
    configs = {
        "Public Wisconsin Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "Public Wisconsin Random Forest": RandomForestClassifier(n_estimators=160, random_state=42, min_samples_leaf=2, class_weight="balanced"),
    }
    all_metrics: list[dict[str, object]] = []
    for name, estimator in configs.items():
        metrics, pipeline = evaluate(name, estimator, x, y)
        all_metrics.append(metrics)
        safe = name.lower().replace(" ", "_")
        joblib.dump(pipeline, MODEL_DIR / f"{safe}.joblib")

    METRICS_PATH.write_text(json.dumps(all_metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(all_metrics, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
