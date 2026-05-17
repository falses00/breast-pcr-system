# 公开小数据集补充说明

## 选择原则

- 不下载大规模 DICOM/NIfTI，避免课程项目体量失控。
- 只使用公开、可复现、小体量数据补充模型工程展示。
- 不把公开诊断数据混同为本项目 pCR 或 MRI 预测数据。
- 所有数据、模型和缓存放在项目目录或 `I:` 盘。

## 已接入数据集

| 数据集 | 来源 | 规模 | 本地用途 | 边界 |
|---|---|---:|---|---|
| Breast Cancer Wisconsin Diagnostic | https://huggingface.co/datasets/scikit-learn/breast-cancer-wisconsin | 569行，约125KB | 训练公开表格良恶性分类教学基准 | 非pCR、非MRI，不作临床诊断 |

本地保存路径：`data/public/breast_cancer_wisconsin/breast_cancer.csv`

运行命令：

```powershell
cd "I:\software Project\breast-pcr-system\backend"
python -m app.ml.download_public_dataset
python -m app.ml.train_public_benchmark
```

## 暂不下载的大型影像数据

| 数据集 | 来源 | 原因 | 后续扩展方式 |
|---|---|---|---|
| BREAST-MRI-NACT-Pilot | https://www.cancerimagingarchive.net/collection/breast-mri-nact-pilot/ | 更贴近 DCE-MRI 与新辅助治疗，但 DICOM 影像体量较大 | 只在技术路线中预留 TCIA 下载、DICOM解析、患者级划分 |

## 使用说明

公开 Wisconsin 数据只用来证明机器学习训练、评估、模型保存、指标展示的工程链路。论文、README、前端指标页都必须保留边界说明：这些结果不预测 pCR，不解释 MRI，不作为真实临床诊断依据。
