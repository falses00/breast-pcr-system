"""分析任务、统计与模型指标接口。"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AnalysisTask, Annotation, AuditRecord, ClinicalRecord, ImageRecord, ModelMetric, Patient, ROIFeature, User
from app.schemas import AnalysisTaskCreate
from app.services.auth import require_roles
from app.services.pcr_model import DISCLAIMER, rule_based_pcr_prediction


router = APIRouter(tags=["辅助分析"])
MODEL_DIR = Path(__file__).resolve().parents[3] / "data" / "models"
METRIC_FILES = ["local_dataset_metrics.json"]


def task_payload(task: AnalysisTask) -> dict:
    explanations = json.loads(task.explanation_json)
    # 从 explanation_json 中提取 risk_level/molecular_subtype/key_factors（兼容旧数据）
    extra = {}
    if isinstance(explanations, dict):
        extra = explanations
        explanations = extra.pop("explanations", [])
    return {
        "id": task.id,
        "patient_id": task.patient_id,
        "image_id": task.image_id,
        "annotation_id": task.annotation_id,
        "task_type": task.task_type,
        "task_status": task.task_status,
        "pcr_probability": task.pcr_probability,
        "explanations": explanations if isinstance(explanations, list) else [],
        "risk_level": extra.get("risk_level", "中等"),
        "molecular_subtype": extra.get("molecular_subtype", "未分类"),
        "key_factors": extra.get("key_factors", []),
        "disclaimer": task.disclaimer,
        "created_at": task.created_at.isoformat(),
    }


@router.post("/analysis/tasks", status_code=status.HTTP_201_CREATED)
def create_analysis_task(payload: AnalysisTaskCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("医生"))):
    patient = db.get(Patient, payload.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    clinical = db.query(ClinicalRecord).filter(ClinicalRecord.patient_id == patient.id).order_by(ClinicalRecord.created_at.desc()).first()
    if not clinical:
        raise HTTPException(status_code=400, detail="缺少临床病理信息，无法创建分析任务")

    feature = None
    if payload.annotation_id:
        annotation = db.get(Annotation, payload.annotation_id)
        if not annotation or annotation.patient_id != patient.id:
            raise HTTPException(status_code=404, detail="标注不存在或与患者不匹配")
        feature = db.query(ROIFeature).filter(ROIFeature.annotation_id == annotation.id).order_by(ROIFeature.created_at.desc()).first()
    else:
        # 自动关联最新标注
        latest_ann = (
            db.query(Annotation)
            .filter(Annotation.patient_id == patient.id)
            .order_by(Annotation.created_at.desc())
            .first()
        )
        if latest_ann:
            feature = db.query(ROIFeature).filter(ROIFeature.annotation_id == latest_ann.id).order_by(ROIFeature.created_at.desc()).first()
            payload.annotation_id = latest_ann.id

    prediction = rule_based_pcr_prediction(
        age=patient.age,
        er_status=clinical.er_status,
        pr_status=clinical.pr_status,
        her2_status=clinical.her2_status,
        ki67=clinical.ki67,
        lesion_area=feature.area if feature else None,
        gray_mean=feature.gray_mean if feature else None,
        nottingham_grade=clinical.nottingham_grade,
        treatment_plan=clinical.treatment_plan,
        gray_entropy=feature.gray_entropy if feature else None,
        gray_contrast=feature.gray_contrast if feature else None,
        compactness=feature.compactness if feature else None,
    )

    # 存储增强分析结果
    explanation_data = json.dumps({
        "explanations": prediction.explanations,
        "risk_level": prediction.risk_level,
        "molecular_subtype": prediction.molecular_subtype,
        "key_factors": prediction.key_factors,
    }, ensure_ascii=False)

    task = AnalysisTask(
        patient_id=patient.id,
        image_id=payload.image_id,
        annotation_id=payload.annotation_id,
        task_type=payload.task_type,
        task_status="已完成",
        pcr_probability=prediction.probability,
        explanation_json=explanation_data,
        disclaimer=prediction.disclaimer,
        created_by=user.id,
    )
    db.add(task)
    db.flush()
    # 自动创建审核记录
    audit = AuditRecord(biz_type="pCR分析", biz_id=task.id, review_status="待审核")
    db.add(audit)
    db.commit()
    db.refresh(task)
    return task_payload(task)


@router.get("/analysis/tasks")
def list_analysis_tasks(patient_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(require_roles("医生", "科室管理员"))):
    query = db.query(AnalysisTask)
    if patient_id:
        query = query.filter(AnalysisTask.patient_id == patient_id)
    return [task_payload(t) for t in query.order_by(AnalysisTask.created_at.desc()).all()]


@router.get("/analysis/tasks/{task_id}")
def get_analysis_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("医生", "科室管理员"))):
    task = db.get(AnalysisTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="分析任务不存在")
    return task_payload(task)


@router.get("/analysis/tasks/{task_id}/detail")
def get_analysis_detail(task_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("医生", "科室管理员"))):
    """返回完整分析详情：患者 + 临床 + 影像 + ROI + 分析结果"""
    task = db.get(AnalysisTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="分析任务不存在")

    patient = db.get(Patient, task.patient_id)
    clinical = db.query(ClinicalRecord).filter(ClinicalRecord.patient_id == task.patient_id).order_by(ClinicalRecord.created_at.desc()).first()

    image_info = None
    if task.image_id:
        img = db.get(ImageRecord, task.image_id)
        if img:
            from app.routers.images import image_payload
            image_info = image_payload(img)

    roi_features = None
    if task.annotation_id:
        feat = db.query(ROIFeature).filter(ROIFeature.annotation_id == task.annotation_id).order_by(ROIFeature.created_at.desc()).first()
        if feat:
            from app.routers.images import feature_payload
            roi_features = feature_payload(feat)

    result = task_payload(task)
    result["patient"] = {
        "id": patient.id if patient else None,
        "patient_code": patient.patient_code if patient else "未知",
        "name_masked": patient.name_masked if patient else "未知",
        "age": patient.age if patient else None,
        "gender": patient.gender if patient else "未知",
    } if patient else None

    result["clinical"] = {
        "tumor_type": clinical.tumor_type,
        "hr_status": clinical.hr_status,
        "er_status": clinical.er_status,
        "pr_status": clinical.pr_status,
        "her2_status": clinical.her2_status,
        "nottingham_grade": clinical.nottingham_grade,
        "menopause": clinical.menopause,
        "ki67": clinical.ki67,
        "treatment_plan": clinical.treatment_plan,
        "pcr_label": clinical.pcr_label,
    } if clinical else None

    result["image"] = image_info
    result["roi_features"] = roi_features
    return result


@router.get("/stats/summary")
def stats_summary(db: Session = Depends(get_db), user: User = Depends(require_roles("医生", "科室管理员"))):
    patients = db.query(Patient).all()
    clinical = db.query(ClinicalRecord).all()
    tasks = db.query(AnalysisTask).all()
    features = db.query(ROIFeature).all()
    pcr_known = [c.pcr_label for c in clinical if c.pcr_label is not None]
    tumor_counter = Counter(c.tumor_type for c in clinical)
    er_pcr = Counter(f"{c.er_status}-{'pCR' if c.pcr_label else 'non-pCR'}" for c in clinical if c.pcr_label is not None)

    # 分子分型 pCR 统计
    subtype_pcr: dict[str, dict[str, int]] = {}
    for c in clinical:
        if c.pcr_label is None:
            continue
        st = c.tumor_type or "未知"
        if st not in subtype_pcr:
            subtype_pcr[st] = {"pcr": 0, "non_pcr": 0, "total": 0}
        subtype_pcr[st]["total"] += 1
        if c.pcr_label:
            subtype_pcr[st]["pcr"] += 1
        else:
            subtype_pcr[st]["non_pcr"] += 1

    # 年龄段分布
    age_bins = {"<40": 0, "40-49": 0, "50-59": 0, "60-69": 0, "≥70": 0}
    for p in patients:
        if p.age < 40:
            age_bins["<40"] += 1
        elif p.age < 50:
            age_bins["40-49"] += 1
        elif p.age < 60:
            age_bins["50-59"] += 1
        elif p.age < 70:
            age_bins["60-69"] += 1
        else:
            age_bins["≥70"] += 1

    return {
        "patient_count": len(patients),
        "image_count": db.query(ImageRecord).count(),
        "annotation_count": db.query(Annotation).count(),
        "task_count": len(tasks),
        "pcr_ratio": (sum(1 for x in pcr_known if x) / len(pcr_known)) if pcr_known else None,
        "pcr_positive_count": sum(1 for x in pcr_known if x),
        "pcr_negative_count": sum(1 for x in pcr_known if not x),
        "age_distribution": [{"name": k, "value": v} for k, v in age_bins.items()],
        "tumor_type_distribution": [{"name": k, "value": v} for k, v in tumor_counter.items()],
        "er_pr_her2_pcr_relation": [{"name": k, "value": v} for k, v in er_pcr.items()],
        "subtype_pcr_stats": [{"subtype": k, **v} for k, v in subtype_pcr.items()],
        "lesion_area_distribution": [f.area for f in features],
        "model_task_probabilities": [t.pcr_probability for t in tasks],
        "disclaimer": DISCLAIMER,
    }


@router.get("/model/metrics")
def list_model_metrics(db: Session = Depends(get_db), user: User = Depends(require_roles("医生", "科室管理员"))):
    metrics = db.query(ModelMetric).order_by(ModelMetric.created_at.desc()).all()
    db_metrics = [
        {
            "id": m.id,
            "model_name": m.model_name,
            "data_source": "database",
            "task_kind": "课程项目模型评估记录",
            "sample_count": None,
            "accuracy": m.accuracy,
            "precision": m.precision,
            "recall": m.recall,
            "f1": m.f1,
            "auc": m.auc,
            "confusion_matrix": json.loads(m.confusion_matrix_json),
            "roc_curve_uri": m.roc_curve_uri,
        }
        for m in metrics
    ]
    file_metrics: list[dict] = []
    for filename in METRIC_FILES:
        metrics_path = MODEL_DIR / filename
        if not metrics_path.exists():
            continue
        for item in json.loads(metrics_path.read_text(encoding="utf-8")):
            item.setdefault("data_source", filename.replace("_metrics.json", ""))
            item.setdefault("task_kind", "课程项目模型评估")
            item.setdefault("sample_count", None)
            item.setdefault("roc_curve_uri", None)
            file_metrics.append(item)
    return db_metrics + file_metrics


@router.get("/model/feature-importance")
def get_feature_importance(db: Session = Depends(get_db), user: User = Depends(require_roles("医生", "科室管理员"))):
    """返回模型特征重要性（从训练好的 joblib 模型读取）"""
    import joblib

    result = []
    for model_file in MODEL_DIR.glob("*.joblib"):
        try:
            pipeline = joblib.load(model_file)
            estimator = pipeline.steps[-1][1]
            if hasattr(estimator, "feature_importances_"):
                importances = estimator.feature_importances_.tolist()
                # 尝试获取特征名
                preprocessor = pipeline.steps[0][1]
                try:
                    feature_names = preprocessor.get_feature_names_out().tolist()
                except Exception:
                    feature_names = [f"feature_{i}" for i in range(len(importances))]
                # 排序返回 top 特征
                pairs = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
                result.append({
                    "model_name": model_file.stem,
                    "features": [{"name": n, "importance": round(v, 4)} for n, v in pairs[:15]],
                })
            elif hasattr(estimator, "coef_"):
                coefs = estimator.coef_[0].tolist() if estimator.coef_.ndim > 1 else estimator.coef_.tolist()
                preprocessor = pipeline.steps[0][1]
                try:
                    feature_names = preprocessor.get_feature_names_out().tolist()
                except Exception:
                    feature_names = [f"feature_{i}" for i in range(len(coefs))]
                pairs = sorted(zip(feature_names, [abs(c) for c in coefs]), key=lambda x: x[1], reverse=True)
                result.append({
                    "model_name": model_file.stem,
                    "features": [{"name": n, "importance": round(v, 4)} for n, v in pairs[:15]],
                })
        except Exception:
            continue
    return result
