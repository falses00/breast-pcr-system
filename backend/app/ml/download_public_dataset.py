"""下载小体量公开乳腺癌教学数据集。

数据集：Hugging Face scikit-learn/breast-cancer-wisconsin。
用途：仅作为乳腺癌表格分类教学基准，不用于 pCR 或 MRI 临床诊断。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_DIR = ROOT / "data" / "public" / "breast_cancer_wisconsin"
CSV_PATH = PUBLIC_DIR / "breast_cancer.csv"
META_PATH = PUBLIC_DIR / "dataset_metadata.json"
DATASET_URL = "https://huggingface.co/datasets/scikit-learn/breast-cancer-wisconsin/resolve/main/breast_cancer.csv"
DATASET_PAGE = "https://huggingface.co/datasets/scikit-learn/breast-cancer-wisconsin"
MAX_BYTES = 500_000


def _request(url: str, method: str = "GET") -> Request:
    return Request(url, method=method, headers={"User-Agent": "breast-pcr-course-project/0.1"})


def remote_size() -> int | None:
    with urlopen(_request(DATASET_URL, "HEAD"), timeout=30) as response:
        length = response.headers.get("Content-Length")
    return int(length) if length else None


def download(force: bool = False) -> dict[str, object]:
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    if CSV_PATH.exists() and not force:
        size = CSV_PATH.stat().st_size
        return {"status": "exists", "path": str(CSV_PATH), "bytes": size}

    size = remote_size()
    if size is not None and size > MAX_BYTES:
        raise RuntimeError(f"公开数据集超过限制：{size} bytes > {MAX_BYTES} bytes")

    try:
        with urlopen(_request(DATASET_URL), timeout=60) as response:
            data = response.read(MAX_BYTES + 1)
    except URLError as exc:
        raise RuntimeError(f"下载公开数据集失败：{exc}") from exc

    if len(data) > MAX_BYTES:
        raise RuntimeError(f"下载内容超过限制：{len(data)} bytes > {MAX_BYTES} bytes")

    CSV_PATH.write_bytes(data)
    meta = {
        "name": "Breast Cancer Wisconsin Diagnostic",
        "source": DATASET_PAGE,
        "download_url": DATASET_URL,
        "local_path": str(CSV_PATH),
        "bytes": len(data),
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "usage_boundary": "公开表格诊断教学基准，不用于 pCR 或 MRI 临床诊断。",
    }
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "downloaded", "path": str(CSV_PATH), "bytes": len(data)}


def main() -> int:
    print(json.dumps(download(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
