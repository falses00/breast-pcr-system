"""初始化课程演示账号。业务数据必须来自真实本地数据集导入脚本。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import User
from app.services.auth import hash_password


def seed_demo_data(db: Session) -> None:
    users = [
        ("doctor", "doctor123", "演示医生", "医生"),
        ("dept_admin", "admin123", "科室管理员", "科室管理员"),
        ("sys_admin", "admin123", "系统管理员", "系统管理员"),
    ]
    for username, password, name, role in users:
        if not db.query(User).filter(User.username == username).first():
            db.add(User(username=username, password_hash=hash_password(password), name=name, role=role))
    db.commit()
