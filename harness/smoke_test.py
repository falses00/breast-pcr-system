"""后端 smoke test：检查服务是否启动、核心接口是否可访问。"""

from __future__ import annotations

import os
import sys

import httpx


BASE_URL = os.getenv("PCR_BASE_URL", "http://127.0.0.1:8000")


def main() -> int:
    try:
        health = httpx.get(f"{BASE_URL}/health", timeout=5)
        health.raise_for_status()
        print("健康检查:", health.json())
    except Exception as exc:  # pragma: no cover - 命令行探针
        print(f"后端不可访问: {exc}")
        return 1

    try:
        login = httpx.post(
            f"{BASE_URL}/auth/login",
            json={"username": "doctor", "password": "doctor123"},
            timeout=5,
        )
        login.raise_for_status()
        payload = login.json()
        assert payload.get("access_token")
        print("登录检查: 通过")
    except Exception as exc:  # pragma: no cover - 命令行探针
        print(f"登录接口异常: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
