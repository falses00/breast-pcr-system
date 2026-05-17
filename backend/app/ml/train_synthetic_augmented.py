"""使用本地样例 + 合成教学数据训练演示模型。"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.ml.generate_synthetic_dataset import OUT_CSV, OUT_IMAGE_DIR, generate
from app.ml.train_from_local_dataset import IMAGE_DIR, load_dataset, safe_model_filename


ROOT = Path(__file__).resolve().parents[3]
MODEL_DIR = ROOT / "data" / "models"
PROCESSED_DIR = ROOT / "data" / "processed"
METRICS_PATH = MODEL_DIR / "synthetic_augmented_metrics.json"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def image_features(path: Path) -> dict[str, float]:
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


def load_augmented_dataset() -> pd.DataFrame:
    if not OUT_CSV.exists():
        generate()
    local = load_dataset().rename(columns={"pcr": "pcr"})
    local = local[local["pcr"].notna()].copy()
    local["source_type"] = "local"
    synthetic = pd.read_csv(OUT_CSV)
    feature_rows = []
    for _, row in synthetic.iterrows():
        feature_rows.append(image_features(OUT_IMAGE_DIR / f"{int(row['patient_id'])}.png"))
    synthetic = pd.concat([synthetic, pd.DataFrame(feature_rows)], axis=1)
    common = [
        "patient_id",
        "source_type",
        "pcr",
        "mastectomy_post_nac",
        "hr",
        "er",
        "pr",
        "her2",
        "nottingham_grade",
        "tumor_subtype",
        "age",
        "menopause",
        "ethnicity",
        "image_mean",
        "image_std",
        "image_min",
        "image_max",
        "image_area",
    ]
    out = pd.concat([local[common], synthetic[common]], ignore_index=True)
    out.to_csv(PROCESSED_DIR / "synthetic_augmented_features.csv", index=False, encoding="utf-8-sig")
    return out


def build_preprocessor(mode: str) -> ColumnTransformer:
    clinical_numeric = ["age", "mastectomy_post_nac", "hr", "er", "pr", "her2"]
    image_numeric = ["image_mean", "image_std", "image_min", "image_max", "image_area"]
    categorical = ["nottingham_grade", "tumor_subtype", "menopause", "ethnicity"]
    transformers = []
    if mode in {"clinical", "fusion"}:
        transformers.extend(
            [
                ("clinical_num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), clinical_numeric),
                ("cat", make_pipeline(SimpleImputer(strategy="most_frequent"), OneHotEncoder(handle_unknown="ignore")), categorical),
            ]
        )
    if mode in {"image", "fusion"}:
        transformers.append(("image", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), image_numeric))
    return ColumnTransformer(transformers=transformers, remainder="drop")


def evaluate(name: str, pipeline, x: pd.DataFrame, y: np.ndarray) -> dict[str, object]:
    splits = min(5, int(y.sum()), len(y) - int(y.sum()))
    cv = StratifiedKFold(n_splits=max(2, splits), shuffle=True, random_state=42)
    prob = cross_val_predict(pipeline, x, y, cv=cv, method="predict_proba")[:, 1]
    pred = (prob >= 0.5).astype(int)
    return {
        "model_name": name,
        "data_source": "local_plus_synthetic_demo",
        "task_kind": "本地样例+合成教学数据训练演示，不代表真实临床性能",
        "sample_count": int(len(y)),
        "accuracy": float(accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "auc": float(roc_auc_score(y, prob)),
        "confusion_matrix": confusion_matrix(y, pred).tolist(),
        "disclaimer": "合成增强指标仅用于课程项目流程展示，不作为真实临床诊断依据。",
    }


def main() -> int:
    df = load_augmented_dataset()
    y = df["pcr"].astype(int).to_numpy()
    x = df.drop(columns=["pcr"])
    configs = {
        "Synthetic Clinical Logistic Regression": (build_preprocessor("clinical"), LogisticRegression(max_iter=1000, class_weight="balanced")),
        "Synthetic Image/Radiomics Random Forest": (build_preprocessor("image"), RandomForestClassifier(n_estimators=160, random_state=42, min_samples_leaf=3, class_weight="balanced")),
        "Synthetic Clinical+Image Gradient Boosting": (build_preprocessor("fusion"), GradientBoostingClassifier(n_estimators=100, learning_rate=0.05, random_state=42)),
    }
    metrics = []
    for name, (preprocessor, estimator) in configs.items():
        pipeline = make_pipeline(preprocessor, estimator)
        metrics.append(evaluate(name, pipeline, x, y))
        pipeline.fit(x, y)
        joblib.dump(pipeline, MODEL_DIR / f"{safe_model_filename(name)}.joblib")
    METRICS_PATH.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
