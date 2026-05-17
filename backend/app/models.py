"""SQLAlchemy 数据模型。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(64))
    role: Mapped[str] = mapped_column(String(32), index=True)
    department: Mapped[str] = mapped_column(String(64), default="乳腺科")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Patient(Base, TimestampMixin):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name_masked: Mapped[str] = mapped_column(String(64))
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(16), default="女")
    visit_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    contact_masked: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="待提交")
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    clinical_records: Mapped[list["ClinicalRecord"]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    images: Mapped[list["ImageRecord"]] = relationship(back_populates="patient", cascade="all, delete-orphan")


class ClinicalRecord(Base, TimestampMixin):
    __tablename__ = "clinical_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    tumor_type: Mapped[str] = mapped_column(String(128))
    hr_status: Mapped[str] = mapped_column(String(32), default="未知")
    er_status: Mapped[str] = mapped_column(String(32), default="未知")
    pr_status: Mapped[str] = mapped_column(String(32), default="未知")
    her2_status: Mapped[str] = mapped_column(String(32), default="未知")
    nottingham_grade: Mapped[str | None] = mapped_column(String(32), nullable=True)
    menopause: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ethnicity: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mastectomy_post_nac: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    ki67: Mapped[float | None] = mapped_column(Float, nullable=True)
    treatment_plan: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pcr_label: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    patient: Mapped["Patient"] = relationship(back_populates="clinical_records")


class ImageRecord(Base, TimestampMixin):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_uri: Mapped[str] = mapped_column(String(500), unique=True)
    file_format: Mapped[str] = mapped_column(String(32), default="PNG/JPG")
    modality: Mapped[str] = mapped_column(String(32), default="MRI")
    sequence_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="待标注")
    uploader_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    patient: Mapped["Patient"] = relationship(back_populates="images")
    annotations: Mapped[list["Annotation"]] = relationship(back_populates="image", cascade="all, delete-orphan")


class Annotation(Base, TimestampMixin):
    __tablename__ = "annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    image_id: Mapped[int] = mapped_column(ForeignKey("images.id"), index=True)
    slice_no: Mapped[int] = mapped_column(Integer, default=1)
    roi_json: Mapped[str] = mapped_column(Text)
    lesion_type: Mapped[str] = mapped_column(String(128), default="疑似病灶")
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    version_no: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    image: Mapped["ImageRecord"] = relationship(back_populates="annotations")


class ROIFeature(Base, TimestampMixin):
    __tablename__ = "roi_features"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    annotation_id: Mapped[int] = mapped_column(ForeignKey("annotations.id"), index=True)
    area: Mapped[float] = mapped_column(Float, default=0)
    gray_mean: Mapped[float] = mapped_column(Float, default=0)
    gray_std: Mapped[float] = mapped_column(Float, default=0)
    gray_min: Mapped[float] = mapped_column(Float, default=0)
    gray_max: Mapped[float] = mapped_column(Float, default=0)
    gray_skewness: Mapped[float] = mapped_column(Float, default=0)
    gray_kurtosis: Mapped[float] = mapped_column(Float, default=0)
    gray_entropy: Mapped[float] = mapped_column(Float, default=0)
    gray_contrast: Mapped[float] = mapped_column(Float, default=0)
    gray_energy: Mapped[float] = mapped_column(Float, default=0)
    perimeter: Mapped[float] = mapped_column(Float, default=0)
    compactness: Mapped[float] = mapped_column(Float, default=0)
    circularity: Mapped[float] = mapped_column(Float, default=0)
    reserved_radiomics_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class AnalysisTask(Base, TimestampMixin):
    __tablename__ = "analysis_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    image_id: Mapped[int | None] = mapped_column(ForeignKey("images.id"), nullable=True)
    annotation_id: Mapped[int | None] = mapped_column(ForeignKey("annotations.id"), nullable=True)
    task_type: Mapped[str] = mapped_column(String(64), default="规则pCR辅助分析")
    task_status: Mapped[str] = mapped_column(String(32), default="已完成")
    pcr_probability: Mapped[float] = mapped_column(Float, default=0)
    explanation_json: Mapped[str] = mapped_column(Text, default="[]")
    disclaimer: Mapped[str] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class ModelMetric(Base, TimestampMixin):
    __tablename__ = "model_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(String(128))
    accuracy: Mapped[float] = mapped_column(Float, default=0)
    precision: Mapped[float] = mapped_column(Float, default=0)
    recall: Mapped[float] = mapped_column(Float, default=0)
    f1: Mapped[float] = mapped_column(Float, default=0)
    auc: Mapped[float] = mapped_column(Float, default=0)
    confusion_matrix_json: Mapped[str] = mapped_column(Text, default="[]")
    roc_curve_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)


class AuditRecord(Base, TimestampMixin):
    __tablename__ = "audit_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    biz_type: Mapped[str] = mapped_column(String(64))
    biz_id: Mapped[int] = mapped_column(Integer, index=True)
    review_status: Mapped[str] = mapped_column(String(32), default="待审核")
    review_opinion: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
