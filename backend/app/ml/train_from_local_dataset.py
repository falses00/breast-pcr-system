"""使用本地验证数据集训练课程演示模型。

数据来源：I:\\software Project\\数据集
输出位置：项目 data/models，不写入 C 盘。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parents[3]
SOURCE_DIR = Path(r"I:\software Project\数据集")
CLINICAL_XLSX = SOURCE_DIR / "乳腺癌患者临床特征表.xlsx"
IMAGE_DIR = SOURCE_DIR / "image"
MODEL_DIR = ROOT / "data" / "models"
PROCESSED_DIR = ROOT / "data" / "processed"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def safe_model_filename(name: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", name.lower().replace("+", "plus")).strip("_")


def image_features(patient_id: int) -> dict[str, float]:
    path = IMAGE_DIR / f"{patient_id:03d}.png"
    if not path.exists():
        return {"image_mean": 0.0, "image_std": 0.0, "image_min": 0.0, "image_max": 0.0, "image_area": 0.0}
    arr = np.asarray(Image.open(path).convert("L"), dtype=np.float32)
    return {
        "image_mean": float(arr.mean()),
        "image_std": float(arr.std()),
        "image_min": float(arr.min()),
        "image_max": float(arr.max()),
        "image_area": float(arr.shape[0] * arr.shape[1]),
    }


def load_dataset() -> pd.DataFrame:
    df = pd.read_excel(CLINICAL_XLSX)
    df = df.rename(columns={"pcr（1=达到pcr）": "pcr", "hr(1=阳性)": "hr"})
    feature_rows = [image_features(int(pid)) for pid in df["patient_id"]]
    out = pd.concat([df, pd.DataFrame(feature_rows)], axis=1)
    out.to_csv(PROCESSED_DIR / "local_dataset_features.csv", index=False, encoding="utf-8-sig")
    return out


def build_preprocessor(df: pd.DataFrame) -> ColumnTransformer:
    numeric = [
        "age",
        "mastectomy_post_nac",
        "hr",
        "er",
        "pr",
        "her2",
        "image_mean",
        "image_std",
        "image_min",
        "image_max",
        "image_area",
    ]
    categorical = ["nottingham_grade", "tumor_subtype", "menopause", "ethnicity"]
    return ColumnTransformer(
        transformers=[
            ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), numeric),
            ("cat", make_pipeline(SimpleImputer(strategy="most_frequent"), OneHotEncoder(handle_unknown="ignore")), categorical),
        ]
    )


def build_clinical_preprocessor() -> ColumnTransformer:
    numeric = ["age", "mastectomy_post_nac", "hr", "er", "pr", "her2"]
    categorical = ["nottingham_grade", "tumor_subtype", "menopause", "ethnicity"]
    return ColumnTransformer(
        transformers=[
            ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), numeric),
            ("cat", make_pipeline(SimpleImputer(strategy="most_frequent"), OneHotEncoder(handle_unknown="ignore")), categorical),
        ]
    )


def build_image_preprocessor() -> ColumnTransformer:
    numeric = ["image_mean", "image_std", "image_min", "image_max", "image_area"]
    return ColumnTransformer(
        transformers=[
            ("image", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), numeric),
        ],
        remainder="drop",
    )


def evaluate_model(name: str, pipeline, x: pd.DataFrame, y: np.ndarray) -> dict:
    positives = int(y.sum())
    splits = min(5, positives, len(y) - positives)
    if splits >= 2:
        cv = StratifiedKFold(n_splits=splits, shuffle=True, random_state=42)
        prob = cross_val_predict(pipeline, x, y, cv=cv, method="predict_proba")[:, 1]
    else:
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=42, stratify=y)
        pipeline.fit(x_train, y_train)
        prob = pipeline.predict_proba(x_test)[:, 1]
        y = y_test
    pred = (prob >= 0.5).astype(int)
    auc = roc_auc_score(y, prob) if len(set(y)) > 1 else 0.0
    return {
        "model_name": name,
        "data_source": "local_35_case_dataset",
        "sample_count": int(len(y)),
        "accuracy": float(accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "auc": float(auc),
        "confusion_matrix": confusion_matrix(y, pred).tolist(),
    }


def main() -> int:
    df = load_dataset()
    df = df[df["pcr"].notna()].copy()
    y = df["pcr"].fillna(0).astype(int).to_numpy()
    x = df.drop(columns=["pcr"])
    models = {
        "Local Clinical Logistic Regression": (
            build_clinical_preprocessor(),
            LogisticRegression(max_iter=1000, class_weight="balanced"),
            "本地临床特征pCR演示模型",
        ),
        "Local Image/Radiomics Random Forest": (
            build_image_preprocessor(),
            RandomForestClassifier(n_estimators=160, random_state=42, min_samples_leaf=2, class_weight="balanced"),
            "本地整图灰度特征演示模型，近似ROI/radiomics流程",
        ),
        "Local Clinical+Image Random Forest": (
            build_preprocessor(df),
            RandomForestClassifier(n_estimators=160, random_state=42, min_samples_leaf=2, class_weight="balanced"),
            "本地临床+影像融合pCR演示模型",
        ),
        "Local Clinical+Image Gradient Boosting": (
            build_preprocessor(df),
            GradientBoostingClassifier(n_estimators=80, learning_rate=0.05, random_state=42),
            "XGBoost路线的scikit-learn轻量替代，避免额外重依赖",
        ),
    }
    metrics = []
    for name, (preprocessor, estimator, task_kind) in models.items():
        pipeline = make_pipeline(preprocessor, estimator)
        result = evaluate_model(name, pipeline, x, y)
        result["task_kind"] = task_kind
        result["disclaimer"] = "仅用于课程项目辅助分析展示，不作为真实临床诊断依据。"
        metrics.append(result)
        pipeline.fit(x, y)
        safe = safe_model_filename(name)
        joblib.dump(pipeline, MODEL_DIR / f"{safe}.joblib")

    out_path = MODEL_DIR / "local_dataset_metrics.json"
    out_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
