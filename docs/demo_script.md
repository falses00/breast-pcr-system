# 答辩演示脚本

## 演示定位

本系统是课程级“乳腺 MRI 影像与临床病理数据辅助分析系统”，展示患者数据管理、影像 ROI 标注、特征提取、规则模型、机器学习评估和审核流程。所有医学预测仅作课程项目辅助分析展示，不作为真实临床诊断依据。

## 启动方式

```powershell
cd "I:\software Project\breast-pcr-system\backend"
python -m uvicorn app.main:app --reload

cd "I:\software Project\breast-pcr-system\frontend"
$env:npm_config_cache="I:\software Project\.npm-cache"
npm.cmd run dev
```

访问：`http://127.0.0.1:5173`

## 默认账号

| 角色 | 账号 | 密码 | 演示重点 |
|---|---|---|---|
| 医生 | doctor | doctor123 | 患者、影像、ROI、分析任务 |
| 科室管理员 | dept_admin | admin123 | 医生功能 + 审核管理 |
| 系统管理员 | sys_admin | admin123 | 全部功能 + 用户管理 |

## 推荐演示顺序

1. 登录医生账号 `doctor / doctor123`。
2. 打开仪表盘，说明系统展示患者数、影像数、ROI 标注、pCR 比例和模型概率分布。
3. 进入患者管理，选择或新增患者，展示临床病理字段：年龄、肿瘤类型、ER、PR、HER2、Ki-67、治疗方案、pCR 标签。
4. 进入影像与 ROI，选择本地验证数据集影像，拖拽 Canvas 绘制矩形 ROI，保存后展示面积、灰度均值、标准差、最小值、最大值。
5. 进入分析任务，创建规则 pCR 辅助分析，说明输出概率、解释因子和免责声明。
6. 展示模型评估指标：本地35例样例、公开 Wisconsin 教学基准、模拟演示指标。强调 Wisconsin 是非 pCR、非 MRI，仅用于机器学习流程展示。
7. 退出医生账号，登录科室管理员，进入审核管理，演示通过或退回补充。
8. 退出并登录系统管理员，进入用户管理，演示三角色账号维护。
9. 直接访问 `/users` 时用医生账号测试，会进入无权访问页面，说明前端路由与后端接口都有权限约束。

## 可讲技术点

- 前端：Vue3 + Vite + TypeScript + Element Plus + ECharts + anime.js。
- 后端：FastAPI + SQLAlchemy + SQLite，预留 MySQL/PostgreSQL。
- 影像：PNG/JPG MVP，Pillow 提取 ROI 灰度特征；预留 DICOM/NIfTI。
- 模型：规则 pCR 辅助分析、本地35例样例训练、公开小数据集教学基准。
- 安全边界：角色权限、脱敏患者字段、禁止真实患者数据、医学免责声明。

## 风险说明

- 本地样例数据只有35例，不足以支持临床泛化结论。
- 公开 Wisconsin 数据是表格诊断基准，不是 pCR 数据，也不是 MRI 数据。
- 深度学习 3D MRI 需要更大合规数据、患者级划分、外部验证和医学专家审核。
