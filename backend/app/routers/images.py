"""影像、标注与ROI特征接口。"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import ROOT_DIR, get_db
from app.imaging.roi_features import extract_roi_features
from app.models import Annotation, AuditRecord, ImageRecord, Patient, ROIFeature, User
from app.schemas import AnnotationCreate, ImageRecordCreate
from app.services.auth import require_roles


router = APIRouter(tags=["影像与标注"])
UPLOAD_DIR = ROOT_DIR / "data" / "uploads"
SAMPLE_IMAGE_DIR = ROOT_DIR / "data" / "sample_images"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def image_payload(img: ImageRecord) -> dict:
    file_uri = img.file_uri
    image_url = file_uri
    source_type = "外部影像引用"
    path = Path(file_uri)
    if not path.is_absolute():
        path = ROOT_DIR / path
    if path.exists():
        try:
            relative_path = path.resolve().relative_to(UPLOAD_DIR.resolve())
            image_url = f"/uploads/{relative_path.as_posix()}"
            source_type = "本地验证数据集MRI影像" if "local_dataset" in relative_path.as_posix() else "医生上传影像"
        except ValueError:
            try:
                relative_path = path.resolve().relative_to(SAMPLE_IMAGE_DIR.resolve())
                image_url = f"/sample-images/{relative_path.as_posix()}"
                source_type = "模拟样例影像"
            except ValueError:
                image_url = file_uri
    return {
        "id": img.id,
        "patient_id": img.patient_id,
        "filename": img.filename,
        "file_uri": img.file_uri,
        "image_url": image_url,
        "file_format": img.file_format,
        "modality": img.modality,
        "sequence_type": img.sequence_type,
        "status": img.status,
        "source_type": source_type,
    }


def annotation_payload(a: Annotation) -> dict:
    return {
        "id": a.id,
        "patient_id": a.patient_id,
        "image_id": a.image_id,
        "slice_no": a.slice_no,
        "roi_json": json.loads(a.roi_json),
        "lesion_type": a.lesion_type,
        "remark": a.remark,
        "version_no": a.version_no,
    }


def feature_payload(f: ROIFeature) -> dict:
    return {
        "id": f.id,
        "annotation_id": f.annotation_id,
        "area": f.area,
        "gray_mean": f.gray_mean,
        "gray_std": f.gray_std,
        "gray_min": f.gray_min,
        "gray_max": f.gray_max,
        "gray_skewness": f.gray_skewness,
        "gray_kurtosis": f.gray_kurtosis,
        "gray_entropy": f.gray_entropy,
        "gray_contrast": f.gray_contrast,
        "gray_energy": f.gray_energy,
        "perimeter": f.perimeter,
        "compactness": f.compactness,
        "circularity": f.circularity,
    }


@router.post("/images/records", status_code=status.HTTP_201_CREATED)
def create_image_record(payload: ImageRecordCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("医生"))):
    if not db.get(Patient, payload.patient_id):
        raise HTTPException(status_code=404, detail="患者不存在")
    if db.query(ImageRecord).filter(ImageRecord.file_uri == payload.file_uri).first():
        raise HTTPException(status_code=409, detail="影像文件URI已存在")
    record = ImageRecord(**payload.model_dump(), uploader_id=user.id)
    db.add(record)
    db.commit()
    db.refresh(record)
    return image_payload(record)


@router.post("/images/upload", status_code=status.HTTP_201_CREATED)
async def upload_image(patient_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_roles("医生"))):
    if not db.get(Patient, patient_id):
        raise HTTPException(status_code=404, detail="患者不存在")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg"}:
        raise HTTPException(status_code=400, detail="MVP阶段仅支持PNG/JPG，DICOM/NIfTI已预留扩展")
    dest = UPLOAD_DIR / f"patient_{patient_id}_{file.filename}"
    dest.write_bytes(await file.read())
    record = ImageRecord(patient_id=patient_id, filename=file.filename or dest.name, file_uri=str(dest), file_format=suffix.removeprefix(".").upper(), uploader_id=user.id)
    db.add(record)
    db.commit()
    db.refresh(record)
    return image_payload(record)


@router.get("/images")
def list_images(patient_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(require_roles("医生", "科室管理员"))):
    query = db.query(ImageRecord)
    if patient_id:
        query = query.filter(ImageRecord.patient_id == patient_id)
    return [image_payload(i) for i in query.order_by(ImageRecord.created_at.desc()).all()]


@router.get("/images/{image_id}")
def get_image(image_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("医生", "科室管理员"))):
    image = db.get(ImageRecord, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="影像不存在")
    data = image_payload(image)
    data["annotations"] = [annotation_payload(a) for a in image.annotations]
    return data


@router.delete("/images/{image_id}")
def delete_image(image_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("医生"))):
    image = db.get(ImageRecord, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="影像不存在")
    db.delete(image)
    db.commit()
    return {"message": "影像记录已删除"}


@router.post("/annotations", status_code=status.HTTP_201_CREATED)
def create_annotation(payload: AnnotationCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("医生"))):
    image = db.get(ImageRecord, payload.image_id)
    if not image or image.patient_id != payload.patient_id:
        raise HTTPException(status_code=404, detail="影像不存在或与患者不匹配")
    latest_version = (
        db.query(Annotation.version_no)
        .filter(Annotation.image_id == image.id)
        .order_by(Annotation.version_no.desc())
        .first()
    )
    version_no = (latest_version[0] if latest_version else 0) + 1
    annotation = Annotation(
        patient_id=payload.patient_id,
        image_id=payload.image_id,
        slice_no=payload.slice_no,
        roi_json=json.dumps(payload.roi_json, ensure_ascii=False),
        lesion_type=payload.lesion_type,
        remark=payload.remark,
        version_no=version_no,
        created_by=user.id,
    )
    db.add(annotation)
    db.flush()
    features = extract_roi_features(image.file_uri, payload.roi_json)
    feature = ROIFeature(annotation_id=annotation.id, **features)
    db.add(feature)
    image.status = "已标注"
    # 自动创建审核记录，供科室管理员审核
    audit = AuditRecord(biz_type="病灶标注", biz_id=annotation.id, review_status="待审核")
    db.add(audit)
    db.commit()
    db.refresh(annotation)
    return {**annotation_payload(annotation), "roi_features": feature_payload(feature)}


@router.get("/images/{image_id}/annotations")
def list_annotations(image_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("医生", "科室管理员"))):
    annotations = db.query(Annotation).filter(Annotation.image_id == image_id).order_by(Annotation.version_no.desc()).all()
    return [annotation_payload(a) for a in annotations]


@router.get("/annotations/{annotation_id}/features")
def get_roi_features(annotation_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("医生", "科室管理员"))):
    feature = db.query(ROIFeature).filter(ROIFeature.annotation_id == annotation_id).order_by(ROIFeature.created_at.desc()).first()
    if not feature:
        raise HTTPException(status_code=404, detail="ROI特征不存在")
    return feature_payload(feature)
