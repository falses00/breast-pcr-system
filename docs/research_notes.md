# 近三年乳腺癌 pCR 预测论文调研

检索日期：2026-05-17。关键词包括 breast cancer pCR prediction、DCE-MRI、radiomics、multimodal deep learning、3D CNN、clinical features、HER2、ER、PR。本文只提炼课程项目可实现路线，不照抄论文，不声称系统具备临床诊断能力。

## 调研结论

1. pCR 预测通常不是单纯图像分类，而是 MRI / ROI / radiomics / clinical features 的多模态融合问题。
2. 课程 MVP 适合先实现 Clinical + ROI features 的规则模型和传统机器学习模型。
3. 深度学习路线应预留，不应作为第一阶段强制实现；真实 3D MRI 模型需要合规数据、pCR 标签、患者级划分和外部验证。
4. ER、PR、HER2、Ki-67、肿瘤亚型和治疗方案是临床特征主线；DCE-MRI、ADC、肿瘤区、瘤周区和背景实质增强是影像特征主线。

## 论文记录

| 序号 | 标题 | 年份 | 数据 | 输入模态 | 模型 | 指标 | 可借鉴点 |
|---|---|---:|---|---|---|---|---|
| 1 | Machine Learning Predicts Pathologic Complete Response to Neoadjuvant Chemotherapy for ER+HER2- Breast Cancer: Integrating Tumoral and Peritumoral MRI Radiomic Features | 2023 | ER+HER2- 局部晚期乳腺癌，预治疗MRI | 肿瘤区和瘤周区MRI radiomics | 多种机器学习模型 | 论文报告联合模型优于单一区域特征 | MVP可先实现ROI特征，再预留瘤周扩展特征；链接：https://pubmed.ncbi.nlm.nih.gov/37835774 |
| 2 | Deep-learning based discrimination of pathologic complete response using MRI in HER2-positive and triple-negative breast cancer | 2024 | 852例，训练集724、验证集128 | 治疗后DCE-MRI，HER2+和TNBC | 深度学习模型 | 用于区分pCR状态 | 可作为后续2.5D/3D CNN实验参考；当前MVP不直接做临床判读；链接：https://www.nature.com/articles/s41598-024-74276-w |
| 3 | Predicting pathological complete response to neoadjuvant chemotherapy in breast cancer patients: use of MRI radiomics data from three regions with multiple machine learning algorithms | 2024 | 接受NACT的乳腺癌患者 | 肿瘤区、瘤周区、BPE多区域MRI radiomics | 多机器学习算法 | 多区域特征组合预测pCR | 说明“肿瘤区+瘤周区+BPE”比单ROI更完整；MVP先做肿瘤ROI，文档预留多区域标注；链接：https://link.springer.com/article/10.1007/s00432-024-05680-y |
| 4 | Longitudinal MRI-based fusion novel model predicts pathological complete response in breast cancer treated with neoadjuvant chemotherapy | 2023 | 4中心1262例，分HR+/HER2-、HER2+、TNBC亚型 | 纵向MRI、radiomics、深度特征、delta特征 | 融合模型 | 按分子亚型报告pCR预测能力 | 可借鉴“治疗前/中/后多时点影像”和delta特征；MVP数据库保留sequence_type与scan_date；链接：https://www.sciencedirect.com/science/article/pii/S2589537023000767 |
| 5 | The longitudinal changes in multiparametric MRI during neoadjuvant chemotherapy can predict treatment response early in patients with HER2-positive breast cancer | 2024 | HER2阳性乳腺癌患者 | 多参数MRI纵向变化 | 预测模型，使用AUC和校准曲线 | AUC、校准曲线 | 强调HER2亚型和纵向MRI变化；MVP规则模型已把HER2作为解释因子；链接：https://pubmed.ncbi.nlm.nih.gov/39098252 |
| 6 | Prediction of Breast Cancer Response to Neoadjuvant Therapy with Machine Learning: A Clinical, MRI-Qualitative, and Radiomics Approach | 2025 | 非转移乳腺癌、治疗前MRI和临床特征 | 临床特征、MRI定性特征、radiomics | 机器学习模型 | pCR和RFS预测 | 适合本项目第二阶段：Clinical-only、Radiomics-only、Clinical+ROI融合对比；链接：https://www.mdpi.com/2075-1729/15/8/1165 |
| 7 | Can radiomics from dynamic contrast-enhanced MRI effectively predict response to neoadjuvant chemotherapy in breast cancer?: A meta-analysis | 2025 | DCE-MRI radiomics相关研究汇总 | DCE-MRI radiomics | Meta-analysis | 汇总AUC约0.83，敏感度约81%，特异度约74% | 支持DCE-MRI radiomics作为技术路线，但课程MVP只能做展示级模拟，不可宣称临床性能；链接：https://www.sciencedirect.com/science/article/pii/S0009926025002909 |
| 8 | BreastDCEDL: Curating a Comprehensive DCE-MRI Dataset and developing a Transformer Implementation for Breast Cancer Treatment Response Prediction | 2025 | 2070例DCE-MRI，来自I-SPY1、I-SPY2、Duke等TCIA来源，预印本 | 3D DCE-MRI、统一肿瘤标注、临床元数据、pCR/HR/HER2 | Transformer / 深度学习数据集路线 | 面向治疗反应预测 | 为后续公开数据实验提供方向；MVP不下载大规模数据，只写扩展路线；链接：https://arxiv.org/abs/2506.12190 |
| 9 | Radiomics-guided Multimodal Self-attention Network for Predicting Pathological Complete Response in Breast MRI | 2024 | 预印本 | DCE-MRI、ADC、radiomics引导区域 | 多模态自注意力网络 | pCR预测 | 可作为深度学习融合路线参考：DCE + ADC + radiomics guidance；链接：https://arxiv.org/abs/2406.02936 |

## 对本项目的落地路线

### MVP 已采用

- PNG/JPG 影像上传与浏览。
- ROI矩形/多边形标注。
- ROI面积、灰度均值、灰度标准差、最小值、最大值。
- 年龄、ER、PR、HER2、Ki-67、治疗方案等临床病理字段。
- 规则pCR辅助分析，输出概率、解释因子和免责声明。

### 第二阶段

- Clinical-only Logistic Regression。
- Radiomics-only Random Forest。
- Clinical + ROI features XGBoost 或 Random Forest。
- 输出 Accuracy、Precision、Recall、F1、AUC、混淆矩阵、ROC 曲线。

### 第三阶段预留

- DICOM/NIfTI读取：pydicom、SimpleITK、nibabel。
- 医学影像增强和3D训练：MONAI、TorchIO。
- 2.5D ResNet / 3D ResNet / Swin UNETR。
- 多模态融合：影像编码器 + 临床MLP + 注意力融合。

## 数据与伦理边界

- 示例数据必须是模拟数据或公开合规数据。
- 禁止提交真实患者影像、姓名、联系方式、住院号等敏感信息。
- 模型输出必须显示免责声明：仅用于课程项目辅助分析展示，不作为真实临床诊断依据。
