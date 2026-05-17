"""FastAPI 入口。"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError

from app.database import ROOT_DIR
from app.database import SessionLocal, init_db
from app.routers import admin, analysis, audit, auth, images, patients, reports
from app.services.pcr_model import DISCLAIMER
from app.services.seed import seed_demo_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="乳腺MRI影像与临床病理数据辅助分析系统",
    description="课程级辅助分析系统；医学预测仅用于课程展示，不作为真实临床诊断依据。",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(images.router)
app.include_router(analysis.router)
app.include_router(audit.router)
app.include_router(admin.router)
app.include_router(reports.router)
app.mount("/uploads", StaticFiles(directory=str(ROOT_DIR / "data" / "uploads")), name="uploads")
app.mount("/sample-images", StaticFiles(directory=str(ROOT_DIR / "data" / "sample_images")), name="sample-images")

import os
from fastapi.responses import FileResponse
frontend_dist = ROOT_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
    
    @app.get("/{catchall:path}")
    async def serve_spa(catchall: str):
        # 排除 api 路由
        if catchall.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        # 尝试直接返回对应的静态文件
        file_path = frontend_dist / catchall
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        # 否则回退到 index.html (Vue Router history mode)
        return FileResponse(frontend_dist / "index.html")
def error_payload(code: str, message: str, data=None, trace_id: str | None = None):
    return {
        "code": code,
        "message": message,
        "data": data,
        "traceId": trace_id or uuid4().hex,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code = f"HTTP_{exc.status_code}"
    message = exc.detail if isinstance(exc.detail, str) else "请求处理失败"
    return JSONResponse(status_code=exc.status_code, content=error_payload(code, message))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=error_payload("VALIDATION_ERROR", "请求参数校验失败", exc.errors()),
    )


@app.get("/health", tags=["系统"])
def health():
    return {"status": "ok", "message": "系统运行中", "disclaimer": DISCLAIMER}
