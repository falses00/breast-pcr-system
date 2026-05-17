# TODO

## 总目标
实现课程级但可写入简历的“乳腺 MRI 影像与临床病理数据辅助分析系统”，覆盖三角色登录、患者/临床/影像/ROI/分析/审核/统计/用户管理，并保留模型与报告扩展接口。

## 当前阶段
阶段 11：真实数据集纯化、无默认登录、前端交互增强。

## 待办
- Docker Desktop 启动后，验证镜像完整构建和 `docker compose up` 运行。
- 继续细化前端表单级错误提示、审核通知和DICOM/NIfTI扩展。
- 若要冲刺医院级系统，后续补 DICOM/PACS、异步队列、消息推送、审计日志和压力测试。

## 进行中
- 下一步可继续做：可视化大盘配置、异步任务状态、站内通知、审计日志和DICOM/PACS扩展。

## 已完成
- 创建 `AGENTS.md`。
- 创建 `TODO.md`。
- 创建轻量 `harness` 目录结构。
- 搭建 FastAPI + SQLite 后端 MVP。
- 实现登录、患者、临床记录、影像记录/上传、ROI标注、ROI特征、分析任务、统计、审核、用户管理、报告预留接口。
- 建立并通过 harness `api_test.py`、`model_test.py` 最小测试。
- 后端 pytest 通过 2 个测试。
- 阅读并抽取 `乳腺影像与临床数据辅助分析系统_需求规格说明书(2).docx`，生成 `docs/requirements_traceability.md`。
- 核对 anime.js 仓库，前端按 V4 ES module 写法预留轻量动效。
- 预留 GPT-5.5 中文报告生成接口，MVP 先用本地模板报告。
- 初始化 Vue3 + Vite + TypeScript + Element Plus + ECharts + anime.js 前端工程。
- 完成登录页、仪表盘、患者管理、影像上传、Canvas ROI 标注、分析任务、审核管理、用户管理页面。
- 前端生产构建通过。
- 生成模拟 MRI PNG 样例图。
- 补充传统机器学习演示训练脚本并输出 Accuracy、Precision、Recall、F1、AUC、混淆矩阵。
- `/model/metrics` 在数据库为空时可读取演示训练指标文件。
- 前端“分析任务”页展示模型评估指标和混淆矩阵。
- 加入后端/前端 Dockerfile 与 `docker-compose.yml`。
- `docker compose config` 校验通过。
- 完成近三年 pCR / DCE-MRI / radiomics / 多模态深度学习论文调研笔记。
- 确认本地验证数据集：35例临床记录、35张PNG影像；当前无需下载额外数据集。
- 读取 `I:\software Project\数据集`，完成 `docs/dataset_profile.md`、SQLite导入脚本和本地样例训练流程。
- 本地数据集重复导入验证通过：不会重复新增患者，当前本地样例患者总数35例。
- 本地数据集训练通过：Clinical Logistic Regression 与 Clinical+Image Random Forest 指标写入 `data/models/local_dataset_metrics.json`。
- 使用 `ui-ux-pro-max` 规则优化前端：新增 PageHeader、MetricCard、StatusPill，统一医疗工作台视觉、状态胶囊、响应式导航与 anime.js 轻量动效。
- 修复本地验证集影像 URL：`data/uploads/local_dataset` 子目录可通过 `/uploads/...` 正常浏览。
- 浏览器 smoke test 通过：影像页实际加载 MRI 图像，Canvas ROI 拖拽保存成功并返回 ROI 面积。
- 失败路径探针通过：错误密码返回401，非PNG/JPG上传返回400。
- 按规则补充公开小数据集：下载 Hugging Face Breast Cancer Wisconsin Diagnostic，569行、124635 bytes，保存到 `data/public/breast_cancer_wisconsin`。
- 新增公开数据下载脚本 `backend/app/ml/download_public_dataset.py`，限制下载量并支持重复运行幂等检查。
- 新增公开基准训练脚本 `backend/app/ml/train_public_benchmark.py`，输出 Logistic Regression 与 Random Forest 教学基准指标。
- `/model/metrics` 现在合并本地35例样例、公开Wisconsin教学基准和模拟演示指标。
- 前端“模型评估指标”表格新增数据来源、任务边界、样本数，明确公开Wisconsin基准为非pCR、非MRI。
- 新增 `docs/public_dataset_notes.md`，说明已下载小数据集与暂不下载大型TCIA MRI数据的原因。
- 前端路由改为懒加载，页面级 JS chunk 已拆分，生产构建不再出现大 chunk 警告。
- 精简 ECharts 为按需引入，分离 charts、motion、Element Plus、Vue vendor chunk。
- 新增前端路由权限：医生、科室管理员、系统管理员按角色进入对应页面。
- 新增 `ForbiddenView.vue` 中文无权访问页；医生直接访问 `/users` 会跳转 `/403`。
- 侧边栏菜单按当前角色过滤：医生不显示审核管理和用户管理。
- 后端权限探针通过：医生访问 `/admin/users` 返回403，系统管理员返回200。
- 新增 `docs/demo_script.md`，整理答辩演示脚本、默认账号、推荐讲解顺序和风险说明。
- Docker 配置解析通过；完整 build/run 暂未执行，原因是 Docker Desktop 当前未启动，无法确认 Docker daemon 与存储根目录。
- 新增一键初始化脚本 `scripts/init_project.ps1`，串联依赖安装、数据导入、模型训练和前端构建，并将 npm/pip 缓存指向 I 盘。
- 新增综合验证脚本 `scripts/verify_project.ps1`，串联 pytest、harness、模型训练、Docker配置解析和前端构建。
- 本地模型训练补齐四条路线：Clinical-only Logistic Regression、Image/Radiomics-only Random Forest、Clinical+Image Random Forest、Clinical+Image Gradient Boosting。
- 新增 `docs/feature_compliance_report.md`，总结项目功能覆盖情况。
- 新增 `docs/pcr_reliability_report.md`，说明 pCR 辅助分析可靠性、机器学习/深度学习边界和大模型接入原则。
- 新增 `docs/requirements_gap_audit.md`，逐项对照需求规格说明书中的用例、接口约束与性能要求。
- 补足患者检索与空状态，支持按患者编号、脱敏姓名、门诊号查询。
- 补足标注历史列表，ROI保存时版本号自动递增。
- 补足单任务 PDF 报告导出接口和前端“导出PDF”入口，报告输出到 `data/reports`。
- 补足统一错误响应：HTTP/校验错误返回 `code/message/data/traceId/timestamp`。
- 新增 `backend/app/ml/generate_synthetic_dataset.py`，基于现有35例字段分布和影像灰度统计生成120例合成教学数据。
- 新增 `backend/app/ml/train_synthetic_augmented.py`，训练本地样例+合成数据的 Clinical、Image/Radiomics、Clinical+Image 演示模型。
- 新增 `docs/synthetic_data_plan.md`，明确合成数据只用于课程演示，不代表真实患者或临床性能。
- `/model/metrics` 已合并 `synthetic_augmented_metrics.json`；当前指标端点返回11条模型指标，其中3条为合成增强演示指标。
- 一键初始化和验证脚本已加入合成数据生成与合成增强训练步骤。
- 重新阅读需求规格说明书，确认三类角色边界：医生执行业务录入/影像/ROI/分析，科室管理员审核和科室统计，系统管理员维护账号与权限。
- 新增 `frontend/src/rolePolicy.ts`，统一前端路由、菜单和角色说明。
- 收紧后端RBAC：患者/临床/影像/ROI/分析写接口仅医生可操作，审核接口仅科室管理员可操作，报告导出仅医生可操作，用户管理仅系统管理员可操作。
- 前端按角色隐藏操作按钮：科室管理员进入患者、影像、分析页时为只读质控模式；系统管理员仅进入用户管理。
- 影像接口新增 `source_type`，前端显示本地验证数据集MRI影像、医生上传影像或模拟样例影像来源。
- 新增 `docs/role_permission_matrix.md`，记录需求文档对应的角色分级与落地方式。
- 系统管理员仪表盘不再请求患者业务统计，仅显示账号/权限维护入口。
- 影像页默认优先选择本地验证数据集 MRI 影像，并在检查器显示影像来源。
- 验证通过：后端 pytest 2项、API harness、角色越权探针、前端生产构建、Playwright 三角色菜单/只读模式/真实数据集影像加载检查。
- 已重启本地服务：后端 `http://127.0.0.1:8000`，前端 `http://127.0.0.1:5173`。
- 新增 `backend/app/services/reset_to_real_dataset.py`：备份旧SQLite，清除演示、harness、合成、公开基准和旧报告产物，只导入 `I:\software Project\数据集`。
- 当前正式业务库已重置为 35 例真实本地数据集患者、35 条临床病理记录、35 张 MRI PNG 影像；标注与分析任务清零。
- 后端临床模型新增 HR、Nottingham 分级、绝经状态、人群类别和 NAC 后乳房切除字段映射，前端患者列表展示真实分型与 pCR 标签。
- `/model/metrics` 改为仅展示 `local_dataset_metrics.json`，不再混入合成增强、公开Wisconsin或旧demo指标。
- 登录页已取消默认填入 `doctor/doctor123`，并移除明文账号提示，仅保留三角色职责说明。
- 患者页增加真实数据集统计卡、分子分型、ER/PR/HER2、pCR标签和选中患者临床摘要。
- 影像页增加 MRI 缩略图选择条、真实影像来源、当前患者临床摘要、标注版本计数，并继续使用 anime.js 轻量进入动效。
- `harness/api_test.py` 改为独立测试数据库，并在结束时清理测试上传文件，避免污染正式业务库。
- `scripts/init_project.ps1` 与 `scripts/verify_project.ps1` 改为真实数据集重置/训练主线，不再自动生成公开或合成数据。
- 综合验证通过：`scripts/verify_project.ps1`、接口真实数据探针、Playwright 登录空表单/患者真实数据/影像真实来源/本地模型指标检查。
- 重启后服务运行中：后端 `http://127.0.0.1:8000`，前端 `http://127.0.0.1:5173`。

## 风险与决策记录
- 决策：MVP 先使用 PNG/JPG + Pillow ROI 特征，DICOM/NIfTI 仅预留接口。
- 决策：pCR 第一阶段使用规则模型，输出概率与解释，不声称临床诊断能力。
- 决策：anime.js 仅用于登录页、卡片进入和图表切换等轻量动效，不牺牲可用性。
- 决策：所有数据缓存、模型输出、处理产物放在项目目录或 `I:` 盘，不写入 C 盘。
- 风险：真实医学影像模型训练需要合规数据、pCR 标签、患者级划分和外部验证，本课程项目不使用真实患者数据。
- 风险：本地验证集只有35例，其中33例可用于当前训练评估，模型指标只能说明课程链路跑通，不能说明临床泛化能力。
- 决策：公开Wisconsin数据只作为表格分类教学基准，不混入pCR或MRI结论；更贴近项目的TCIA DCE-MRI数据体量较大，当前只记录扩展路线，不批量下载。
- 风险：Docker Desktop 未运行时无法验证容器构建；启动前需确认 Docker Root Dir 不在 C 盘，避免违反数据/缓存不写 C 盘的项目规则。
- 决策：当前版本优先使用真实本地数据集纯化展示；合成和公开小数据脚本保留为历史扩展，但不进入当前业务库、前端指标或一键脚本。
