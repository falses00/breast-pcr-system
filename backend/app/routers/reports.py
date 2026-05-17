"""GPT报告接口预留：MVP生成本地中文解释，不调用外部模型。"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.database import ROOT_DIR, get_db
from app.models import AnalysisTask, User
from app.routers.analysis import task_payload
from app.services.auth import require_roles
from app.services.pcr_model import DISCLAIMER


router = APIRouter(prefix="/reports", tags=["报告生成"])
REPORT_DIR = ROOT_DIR / "data" / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))


@router.post("/gpt55-preview/{task_id}")
def generate_gpt55_preview_report(task_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("医生"))):
    task = db.get(AnalysisTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="分析任务不存在")
    data = task_payload(task)
    probability_percent = round(data["pcr_probability"] * 100, 1)
    return {
        "task_id": task_id,
        "report_type": "GPT-5.5接口预留/本地模板报告",
        "content": (
            f"本次课程演示分析显示，规则模型输出的pCR辅助概率为{probability_percent}%。"
            f"主要解释因子包括：{'；'.join(data['explanations'])}。"
            "该文本由本地模板生成，后续可改为调用GPT-5.5基于本地模型结果生成中文说明。"
        ),
        "disclaimer": DISCLAIMER,
    }


@router.get("/tasks/{task_id}/export")
def export_task_report(task_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("医生"))):
    task = db.get(AnalysisTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="分析任务不存在")
    data = task_payload(task)
    probability_percent = round(data["pcr_probability"] * 100, 1)
    path = REPORT_DIR / f"analysis_task_{task_id}.pdf"
    generated_at = datetime.utcnow()
    valid_until = generated_at + timedelta(days=30)

    pdf = canvas.Canvas(str(path), pagesize=A4)
    pdf.setTitle(f"分析任务{task_id}辅助报告")
    pdf.setFont("STSong-Light", 16)
    pdf.drawString(56, 790, "乳腺MRI影像与临床病理数据辅助分析报告")
    pdf.setFont("STSong-Light", 11)
    lines = [
        f"报告类型：单任务课程演示PDF报告",
        f"任务ID：{task_id}",
        f"患者ID：{data['patient_id']}",
        f"任务状态：{data['task_status']}",
        f"pCR辅助概率：{probability_percent}%",
        f"解释因子：{'；'.join(data['explanations'])}",
        f"生成时间：{generated_at.isoformat()}Z",
        f"有效期至：{valid_until.date().isoformat()}",
        "脱敏说明：报告仅使用患者内部ID与脱敏信息，不包含真实姓名或联系方式。",
        f"免责声明：{DISCLAIMER}",
    ]
    y = 750
    for line in lines:
        pdf.drawString(56, y, line[:80])
        y -= 28
    pdf.showPage()
    pdf.save()
    return FileResponse(path, media_type="application/pdf", filename=f"analysis_task_{task_id}.pdf")
