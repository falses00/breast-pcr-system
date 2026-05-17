"""API harness：用 TestClient 验证登录、患者、影像记录和分析任务链路。"""

from __future__ import annotations

import sys
import os
from uuid import uuid4
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
HARNESS_DB = ROOT / "data" / "harness" / "api_test.db"
HARNESS_DB.parent.mkdir(parents=True, exist_ok=True)
if HARNESS_DB.exists():
    HARNESS_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{HARNESS_DB}"
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient  # noqa: E402

from app.database import engine  # noqa: E402
from app.main import app  # noqa: E402


def main() -> int:
    uploaded_path: Path | None = None
    report_path: Path | None = None
    with TestClient(app) as client:
        try:
            run_id = uuid4().hex[:8].upper()
            patient_code = f"P-HARNESS-{run_id}"
            login = client.post("/auth/login", json={"username": "doctor", "password": "doctor123"})
            assert login.status_code == 200, login.text
            token = login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            patient = client.post(
                "/patients",
                headers=headers,
                json={"patient_code": patient_code, "name_masked": "患者A", "age": 45, "gender": "女"},
            )
            assert patient.status_code in {200, 201}, patient.text
            patient_id = patient.json()["id"]

            clinical = client.post(
                f"/patients/{patient_id}/clinical",
                headers=headers,
                json={
                    "tumor_type": "浸润性导管癌",
                    "er_status": "阳性",
                    "pr_status": "阳性",
                    "her2_status": "阳性",
                    "ki67": 35.0,
                    "treatment_plan": "新辅助治疗方案A",
                    "pcr_label": None,
                },
            )
            assert clinical.status_code == 201, clinical.text

            sample_image = ROOT / "data" / "uploads" / "local_dataset" / "001.png"
            assert sample_image.exists(), f"缺少真实数据集影像：{sample_image}"
            image = client.post(
                f"/images/upload?patient_id={patient_id}",
                headers=headers,
                files={"file": (f"demo_{run_id}.png", sample_image.read_bytes(), "image/png")},
            )
            assert image.status_code == 201, image.text
            assert image.json()["image_url"].startswith("/uploads/")
            uploaded_path = Path(image.json()["file_uri"])
            image_id = image.json()["id"]

            annotation = client.post(
                "/annotations",
                headers=headers,
                json={
                    "patient_id": patient_id,
                    "image_id": image_id,
                    "slice_no": 1,
                    "roi_json": {"type": "rectangle", "points": [{"x": 5, "y": 5}, {"x": 35, "y": 30}]},
                    "lesion_type": "疑似病灶",
                    "remark": "harness矩形标注",
                },
            )
            assert annotation.status_code == 201, annotation.text
            annotation_id = annotation.json()["id"]

            task = client.post(
                "/analysis/tasks",
                headers=headers,
                json={"patient_id": patient_id, "image_id": image_id, "annotation_id": annotation_id, "task_type": "规则pCR辅助分析"},
            )
            assert task.status_code == 201, task.text
            result = task.json()
            assert 0.0 <= result["pcr_probability"] <= 1.0
            assert "仅用于课程项目辅助分析展示" in result["disclaimer"]

            annotations = client.get(f"/images/{image_id}/annotations", headers=headers)
            assert annotations.status_code == 200, annotations.text
            assert annotations.json()[0]["version_no"] >= 1

            report = client.get(f"/reports/tasks/{result['id']}/export", headers=headers)
            assert report.status_code == 200, report.text
            assert report.headers["content-type"].startswith("application/pdf")
            report_path = ROOT / "data" / "reports" / f"analysis_task_{result['id']}.pdf"

            bad = client.post("/auth/login", json={"username": "doctor", "password": "wrong"})
            assert bad.status_code == 401
            assert {"code", "message", "data", "traceId", "timestamp"}.issubset(bad.json().keys())
            print("API harness: 通过")
        finally:
            if uploaded_path and uploaded_path.exists():
                uploaded_path.unlink()
            if report_path and report_path.exists():
                report_path.unlink()
    engine.dispose()
    if HARNESS_DB.exists():
        HARNESS_DB.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
