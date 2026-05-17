"""为前端演示生成一批 pCR 分析任务。"""
from __future__ import annotations
from app.database import SessionLocal, init_db
from app.models import Annotation, AnalysisTask, ClinicalRecord, Patient, ROIFeature
from app.services.pcr_model import rule_based_pcr_prediction
import json

def seed_analysis_tasks():
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(AnalysisTask).count()
        if existing > 0:
            print(f"已有 {existing} 个分析任务，跳过。")
            return
        patients = db.query(Patient).all()
        created = 0
        for p in patients:
            clinical = db.query(ClinicalRecord).filter(ClinicalRecord.patient_id == p.id).first()
            if not clinical:
                continue
            ann = db.query(Annotation).filter(Annotation.patient_id == p.id).first()
            feat = None
            if ann:
                feat = db.query(ROIFeature).filter(ROIFeature.annotation_id == ann.id).first()
            prediction = rule_based_pcr_prediction(
                age=p.age,
                er_status=clinical.er_status,
                pr_status=clinical.pr_status,
                her2_status=clinical.her2_status,
                ki67=clinical.ki67,
                lesion_area=feat.area if feat else None,
                gray_mean=feat.gray_mean if feat else None,
                nottingham_grade=clinical.nottingham_grade,
                treatment_plan=clinical.treatment_plan,
                gray_entropy=feat.gray_entropy if feat else None,
                gray_contrast=feat.gray_contrast if feat else None,
                compactness=feat.compactness if feat else None,
            )
            explanation_data = json.dumps({
                "explanations": prediction.explanations,
                "risk_level": prediction.risk_level,
                "molecular_subtype": prediction.molecular_subtype,
                "key_factors": prediction.key_factors,
            }, ensure_ascii=False)
            task = AnalysisTask(
                patient_id=p.id,
                image_id=None,
                annotation_id=ann.id if ann else None,
                task_type="规则pCR辅助分析",
                task_status="已完成",
                pcr_probability=prediction.probability,
                explanation_json=explanation_data,
                disclaimer=prediction.disclaimer,
                created_by=1,
            )
            db.add(task)
            created += 1
        db.commit()
        print(f"已创建 {created} 个分析任务。")
    finally:
        db.close()

if __name__ == "__main__":
    seed_analysis_tasks()
