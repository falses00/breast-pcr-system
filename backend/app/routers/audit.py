"""审核流程接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditRecord, User
from app.schemas import AuditCreate, AuditUpdate
from app.services.auth import require_roles


router = APIRouter(prefix="/audit", tags=["审核管理"])


def audit_payload(a: AuditRecord) -> dict:
    return {
        "id": a.id,
        "biz_type": a.biz_type,
        "biz_id": a.biz_id,
        "review_status": a.review_status,
        "review_opinion": a.review_opinion,
        "reviewer_id": a.reviewer_id,
        "created_at": a.created_at.isoformat(),
    }


@router.post("/records", status_code=status.HTTP_201_CREATED)
def create_audit_record(payload: AuditCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("医生"))):
    record = AuditRecord(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return audit_payload(record)


@router.get("/records")
def list_audit_records(db: Session = Depends(get_db), user: User = Depends(require_roles("科室管理员"))):
    return [audit_payload(r) for r in db.query(AuditRecord).order_by(AuditRecord.created_at.desc()).all()]


@router.patch("/records/{record_id}")
def update_audit_record(record_id: int, payload: AuditUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles("科室管理员"))):
    record = db.get(AuditRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="审核记录不存在")
    record.review_status = payload.review_status
    record.review_opinion = payload.review_opinion
    record.reviewer_id = user.id
    db.commit()
    db.refresh(record)
    return audit_payload(record)
