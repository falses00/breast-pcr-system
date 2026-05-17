# 乳腺 MRI 影像与临床病理数据辅助分析系统

课程级全栈 MVP，支持三角色登录、患者管理、临床病理信息、真实数据集 MRI 影像浏览、ROI 标注、ROI 特征提取、规则 pCR 辅助分析、统计接口、审核流程和用户管理。

## 免责声明
本系统所有医学预测仅用于课程项目辅助分析展示，不作为真实临床诊断依据，不能替代医生判断。

## 后端运行
```powershell
cd "I:\software Project\breast-pcr-system\backend"
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

访问：`http://127.0.0.1:8000/docs`

## 前端运行
```powershell
cd "I:\software Project\breast-pcr-system\frontend"
npm install
npm run dev
```

访问：`http://127.0.0.1:5173`

## 默认账号
登录页不会预填账号或密码。开发/答辩时可使用以下本地账号：

- 医生：`doctor / doctor123`
- 科室管理员：`dept_admin / admin123`
- 系统管理员：`sys_admin / admin123`

答辩演示流程见：`docs/demo_script.md`。

## Harness
```powershell
cd "I:\software Project\breast-pcr-system"
python harness\api_test.py
python harness\model_test.py
python harness\smoke_test.py
```

`smoke_test.py` 需要后端服务已启动；`api_test.py` 和 `model_test.py` 可直接运行。

## 一键初始化与验证
```powershell
cd "I:\software Project\breast-pcr-system"
powershell -ExecutionPolicy Bypass -File .\scripts\init_project.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\verify_project.ps1
```

脚本会把 `npm` 和 `pip` 缓存指向 `I:\software Project` 下的目录，避免把项目缓存写入 C 盘。

## 真实数据集重置与训练
```powershell
cd "I:\software Project\breast-pcr-system\backend"
python -m app.services.reset_to_real_dataset
python -m app.ml.train_from_local_dataset
```

重置脚本会备份旧 SQLite，清理演示、harness、合成和公开基准产物，只重新导入 `I:\software Project\数据集` 中的 35 例临床记录和 35 张 MRI PNG。训练脚本只输出本地真实数据集指标到 `data/models/local_dataset_metrics.json`。

## 本地验证数据集
用户提供的数据集位于 `I:\software Project\数据集`，包含 35 例临床表格和 35 张 PNG 影像。所有导入文件、模型输出和缓存均写入项目目录或 `I:` 盘，避免写入 C 盘。

```powershell
cd "I:\software Project\breast-pcr-system\backend"
python -m app.services.import_local_dataset
python -m app.ml.train_from_local_dataset
```

导入脚本会复制影像到 `data/uploads/local_dataset` 并写入 SQLite；训练脚本会输出本地验证集课程演示指标到 `data/models/local_dataset_metrics.json`。

## 数据来源
当前业务库只使用 `I:\software Project\数据集`。禁止提交真实患者隐私数据；PNG/JPG 上传功能保留给医生测试，但可通过重置脚本恢复到纯真实数据集状态。

## Docker 运行
```powershell
cd "I:\software Project\breast-pcr-system"
docker compose up --build
```

前端：`http://127.0.0.1:5173`；后端：`http://127.0.0.1:8000/docs`。
