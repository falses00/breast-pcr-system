"""Pydantic 请求/响应模型。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    role: str = Field(pattern="^(医生|科室管理员|系统管理员)$")
    department: str = "乳腺科"


class UserUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    department: str | None = None
    is_active: bool | None = None
    password: str | None = None


class PatientCreate(BaseModel):
    patient_code: str
    name_masked: str
    age: int = Field(ge=0, le=120)
    gender: str = "女"
    visit_no: str | None = None
    contact_masked: str | None = None


class PatientUpdate(BaseModel):
    name_masked: str | None = None
    age: int | None = Field(default=None, ge=0, le=120)
    gender: str | None = None
    visit_no: str | None = None
    contact_masked: str | None = None
    status: str | None = None


class ClinicalRecordCreate(BaseModel):
    tumor_type: str
    hr_status: str = "未知"
    er_status: str = "未知"
    pr_status: str = "未知"
    her2_status: str = "未知"
    nottingham_grade: str | None = None
    menopause: str | None = None
    ethnicity: str | None = None
    mastectomy_post_nac: bool | None = None
    ki67: float | None = Field(default=None, ge=0, le=100)
    treatment_plan: str | None = None
    pcr_label: bool | None = None


class ImageRecordCreate(BaseModel):
    patient_id: int
    filename: str
    file_uri: str
    file_format: str = "PNG/JPG"
    modality: str = "MRI"
    sequence_type: str | None = None


class AnnotationCreate(BaseModel):
    patient_id: int
    image_id: int
    slice_no: int = 1
    roi_json: dict[str, Any]
    lesion_type: str = "疑似病灶"
    remark: str | None = None


class AnalysisTaskCreate(BaseModel):
    patient_id: int
    image_id: int | None = None
    annotation_id: int | None = None
    task_type: str = "规则pCR辅助分析"


class AuditCreate(BaseModel):
    biz_type: str
    biz_id: int
    review_status: str = "待审核"
    review_opinion: str | None = None


class AuditUpdate(BaseModel):
    review_status: str = Field(pattern="^(通过|驳回|退回补充|待审核)$")
    review_opinion: str | None = None
