"""将本地验证数据集导入SQLite。

该脚本只写入项目 data/breast_pcr.db，不修改源数据集。
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

from app.database import ROOT_DIR, SessionLocal, init_db
from app.models import ClinicalRecord, ImageRecord, Patient, User
from app.services.auth import hash_password
from app.services.seed import seed_demo_data


SOURCE_DIR = Path(r"I:\software Project\数据集")
CLINICAL_XLSX = SOURCE_DIR / "乳腺癌患者临床特征表.xlsx"
IMAGE_DIR = SOURCE_DIR / "image"
IMPORTED_IMAGE_DIR = ROOT_DIR / "data" / "uploads" / "local_dataset"
IMPORTED_IMAGE_DIR.mkdir(parents=True, exist_ok=True)

SUBTYPE_LABELS = {
    "triple_negative": "三阴性",
    "her2_enriched": "HER2富集型",
    "her2_pure": "HER2纯型",
    "luminal": "Luminal型",
    "normal_like": "Normal-like型",
}

GRADE_LABELS = {"high": "高级别", "intermediate": "中级别", "low": "低级别"}
MENOPAUSE_LABELS = {"pre": "绝经前", "post": "绝经后"}
ETHNICITY_LABELS = {
    "african american": "非裔美国人",
    "hispanic": "西班牙裔",
    "caucasian": "白人",
    "asian": "亚裔",
}


def status(value: int | float | str) -> str:
    if pd.isna(value):
        return "未知"
    return "阳性" if int(value) == 1 else "阴性"


def bool_or_none(value: int | float | str):
    if pd.isna(value):
        return None
    return bool(int(value))


def label(value, mapping: dict[str, str]) -> str | None:
    if pd.isna(value):
        return None
    raw = str(value)
    return mapping.get(raw, raw)


def treatment_from_row(row) -> str:
    surgery = bool_or_none(row["mastectomy_post_nac"])
    surgery_label = "未知" if surgery is None else ("是" if surgery else "否")
    return f"真实本地数据集NAC；新辅助治疗后乳房切除：{surgery_label}"


def main() -> int:
    IMPORTED_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    db = SessionLocal()
    try:
        seed_demo_data(db)
        doctor = db.query(User).filter(User.username == "doctor").first()
        if not doctor:
            doctor = User(username="doctor", password_hash=hash_password("doctor123"), name="演示医生", role="医生")
            db.add(doctor)
            db.commit()
            db.refresh(doctor)

        df = pd.read_excel(CLINICAL_XLSX).rename(columns={"pcr（1=达到pcr）": "pcr", "hr(1=阳性)": "hr"})
        imported = 0
        for _, row in df.iterrows():
            patient_id = int(row["patient_id"])
            code = f"LOCAL-{patient_id:03d}"
            patient = db.query(Patient).filter(Patient.patient_code == code).first()
            if not patient:
                patient = Patient(
                    patient_code=code,
                    name_masked=f"真实样本{patient_id:03d}",
                    age=int(row["age"]),
                    gender="女",
                    visit_no=f"REAL-DATASET-{patient_id:03d}",
                    status="已导入",
                    owner_id=doctor.id,
                )
                db.add(patient)
                db.flush()
                imported += 1
            else:
                patient.name_masked = f"真实样本{patient_id:03d}"
                patient.age = int(row["age"])
                patient.visit_no = f"REAL-DATASET-{patient_id:03d}"
                patient.status = "已导入"

            clinical = db.query(ClinicalRecord).filter(ClinicalRecord.patient_id == patient.id).first()
            clinical_payload = {
                "tumor_type": label(row["tumor_subtype"], SUBTYPE_LABELS) or "未知分型",
                "hr_status": status(row["hr"]),
                "er_status": status(row["er"]),
                "pr_status": status(row["pr"]),
                "her2_status": status(row["her2"]),
                "nottingham_grade": label(row["nottingham_grade"], GRADE_LABELS),
                "menopause": label(row["menopause"], MENOPAUSE_LABELS),
                "ethnicity": label(row["ethnicity"], ETHNICITY_LABELS),
                "mastectomy_post_nac": bool_or_none(row["mastectomy_post_nac"]),
                "ki67": None,
                "treatment_plan": treatment_from_row(row),
                "pcr_label": bool_or_none(row["pcr"]),
            }
            if clinical:
                for key, value in clinical_payload.items():
                    setattr(clinical, key, value)
            else:
                db.add(ClinicalRecord(patient_id=patient.id, **clinical_payload))

            src = IMAGE_DIR / f"{patient_id:03d}.png"
            if src.exists():
                dest = IMPORTED_IMAGE_DIR / src.name
                if not dest.exists():
                    shutil.copy2(src, dest)
                if not db.query(ImageRecord).filter(ImageRecord.file_uri == str(dest)).first():
                    db.add(
                        ImageRecord(
                            patient_id=patient.id,
                            filename=src.name,
                            file_uri=str(dest),
                            file_format="PNG",
                            modality="MRI",
                            sequence_type="本地验证样例",
                            status="待标注",
                            uploader_id=doctor.id,
                        )
                    )
        db.commit()
        print({"imported_new_patients": imported, "total_local_patients": len(df), "image_dir": str(IMPORTED_IMAGE_DIR)})
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
