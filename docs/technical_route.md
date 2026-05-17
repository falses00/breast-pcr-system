# 技术路线

## MVP路线
1. 后端使用 FastAPI + SQLAlchemy + SQLite。
2. 三角色账号：医生、科室管理员、系统管理员。
3. 影像 MVP 支持 PNG/JPG 上传与记录管理，DICOM/NIfTI 仅预留。
4. ROI 标注先使用矩形/多边形 JSON，后端用 Pillow 计算面积、灰度均值、标准差、最小值、最大值。
5. pCR 辅助分析先使用规则模型，明确免责声明。

## 机器学习路线
1. Clinical-only Logistic Regression。
2. Radiomics-only Random Forest。
3. Clinical + ROI features XGBoost。
4. 输出 Accuracy、Precision、Recall、F1、AUC、混淆矩阵、ROC 曲线。
5. 由于本地 pCR 样例只有35例，额外使用公开 Wisconsin 乳腺癌诊断表格数据作为“机器学习流程教学基准”，但它不参与 pCR 或 MRI 预测结论。

## 深度学习预留
后续可使用 MONAI/TorchIO 构建 2.5D ResNet、3D ResNet 或 Swin UNETR 实验；必须使用合规公开数据或模拟数据，并进行患者级数据划分。

## GPT-5.5报告原则
GPT 不直接看 MRI、不直接诊断，只基于本地模型概率、特征和解释因子生成中文辅助分析报告，报告必须包含课程项目免责声明。
