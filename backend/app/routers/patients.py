"""患者与临床病理信息接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ClinicalRecord, Patient, User
from app.schemas import ClinicalRecordCreate, PatientCreate, PatientUpdate
from app.services.auth import require_roles


router = APIRouter(prefix="/patients", tags=["患者管理"])


def patient_payload(p: Patient) -> dict:
    return {
        "id": p.id,
        "patient_code": p.patient_code,
        "name_masked": p.name_masked,
        "age": p.age,
        "gender": p.gender,
        "visit_no": p.visit_no,
        "contact_masked": p.contact_masked,
        "status": p.status,
        "created_at": p.created_at.isoformat(),
        "latest_clinical": clinical_payload(p.clinical_records[-1]) if p.clinical_records else None,
    }


def clinical_payload(c: ClinicalRecord) -> dict:
    return {
        "id": c.id,
        "patient_id": c.patient_id,
        "tumor_type": c.tumor_type,
        "hr_status": c.hr_status,
        "er_status": c.er_status,
        "pr_status": c.pr_status,
        "her2_status": c.her2_status,
        "nottingham_grade": c.nottingham_grade,
        "menopause": c.menopause,
        "ethnicity": c.ethnicity,
        "mastectomy_post_nac": c.mastectomy_post_nac,
        "ki67": c.ki67,
        "treatment_plan": c.treatment_plan,
        "pcr_label": c.pcr_label,
    }


@router.get("")
def list_patients(keyword: str | None = None, db: Session = Depends(get_db), user: User = Depends(require_roles("医生", "科室管理员"))):
    query = db.query(Patient)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(or_(Patient.patient_code.like(like), Patient.name_masked.like(like), Patient.visit_no.like(like)))
    return [patient_payload(p) for p in query.order_by(Patient.created_at.desc()).all()]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("医生"))):
    if db.query(Patient).filter(Patient.patient_code == payload.patient_code).first():
        raise HTTPException(status_code=409, detail="患者编号已存在")
    patient = Patient(**payload.model_dump(), owner_id=user.id)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient_payload(patient)


@router.get("/{patient_id}")
def get_patient(patient_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("医生", "科室管理员"))):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    data = patient_payload(patient)
    data["clinical_records"] = [clinical_payload(c) for c in patient.clinical_records]
    return data


@router.patch("/{patient_id}")
def update_patient(patient_id: int, payload: PatientUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles("医生"))):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(patient, key, value)
    db.commit()
    db.refresh(patient)
    return patient_payload(patient)


@router.delete("/{patient_id}")
def delete_patient(patient_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("医生"))):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    db.delete(patient)
    db.commit()
    return {"message": "患者已删除"}


@router.post("/{patient_id}/clinical", status_code=status.HTTP_201_CREATED)
def create_clinical_record(patient_id: int, payload: ClinicalRecordCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("医生"))):
    if not db.get(Patient, patient_id):
        raise HTTPException(status_code=404, detail="患者不存在")
    record = ClinicalRecord(patient_id=patient_id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return clinical_payload(record)


@router.get("/{patient_id}/clinical")
def list_clinical_records(patient_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("医生", "科室管理员"))):
    if not db.get(Patient, patient_id):
        raise HTTPException(status_code=404, detail="患者不存在")
    records = db.query(ClinicalRecord).filter(ClinicalRecord.patient_id == patient_id).order_by(ClinicalRecord.created_at.desc()).all()
    return [clinical_payload(r) for r in records]
