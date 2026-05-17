# 合成教学数据方案

## 目的

现有本地验证集只有35例，直接训练机器学习模型容易不稳定。为增强课程演示效果，项目基于已有字段分布和影像灰度统计生成少量合成教学数据，用于展示数据增强、模型训练、指标输出和工程链路。

## 生成内容

- 合成临床记录：默认120例。
- 合成PNG影像：默认120张。
- 输出路径：
  - `data/synthetic/synthetic_clinical.csv`
  - `data/synthetic/images/`
  - `data/synthetic/synthetic_metadata.json`

## 生成原则

- 年龄、分子标志物、肿瘤亚型、绝经状态等字段从已有数据分布采样。
- pCR 标签通过已有标签和简化概率规则生成。
- PNG影像通过现有影像尺寸、灰度均值、灰度标准差生成近似的教学图像。
- 所有合成数据均标记 `source_type=synthetic`。

## 使用边界

合成数据不能证明模型具有真实临床能力。合成增强训练指标只用于说明课程项目的工程流程更完整，包括：

- 数据生成。
- 特征处理。
- 模型训练。
- 指标评估。
- 前端展示。

合成数据不应用于论文式性能宣称、临床预测、真实患者诊断或治疗建议。

## 命令

```powershell
cd "I:\software Project\breast-pcr-system\backend"
python -m app.ml.generate_synthetic_dataset
python -m app.ml.train_synthetic_augmented
```

综合验证：

```powershell
cd "I:\software Project\breast-pcr-system"
powershell -ExecutionPolicy Bypass -File .\scripts\verify_project.ps1
```
