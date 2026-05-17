"""重置业务数据为真实本地数据集。

会备份现有 SQLite，清空演示/harness/合成/公开样例产物，只保留并重新导入
I:\\software Project\\数据集 中的 35 例临床病理表和 35 张 MRI PNG。
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from app.database import DATA_DIR, ROOT_DIR, init_db
from app.services.import_local_dataset import main as import_local_dataset


DB_PATH = DATA_DIR / "breast_pcr.db"
BACKUP_DIR = DATA_DIR / "backups"
UPLOAD_DIR = DATA_DIR / "uploads"
SAMPLE_DIR = DATA_DIR / "sample_images"


def ensure_under_data(path: Path) -> Path:
    resolved = path.resolve()
    data_root = DATA_DIR.resolve()
    if resolved != data_root and data_root not in resolved.parents:
        raise RuntimeError(f"拒绝清理非项目data目录路径：{resolved}")
    return resolved


def remove_path(path: Path) -> None:
    resolved = ensure_under_data(path)
    if not resolved.exists():
        return
    if resolved.is_dir():
        shutil.rmtree(resolved)
    else:
        resolved.unlink()


def backup_database() -> str | None:
    if not DB_PATH.exists():
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_DIR / f"breast_pcr_before_real_reset_{stamp}.db"
    shutil.copy2(DB_PATH, backup)
    return str(backup)


def main() -> int:
    backup = backup_database()
    remove_path(DB_PATH)
    for path in [
        UPLOAD_DIR,
        DATA_DIR / "reports",
        DATA_DIR / "synthetic",
        DATA_DIR / "public",
        DATA_DIR / "models",
        DATA_DIR / "processed",
        DATA_DIR / "sample_clinical.csv",
        SAMPLE_DIR / "demo_mri.png",
    ]:
        remove_path(path)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    (SAMPLE_DIR / ".gitkeep").write_text("", encoding="utf-8")
    init_db()
    import_local_dataset()
    print({"backup": backup, "active_dataset": "I:\\software Project\\数据集", "status": "reset_to_real_dataset_done"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
