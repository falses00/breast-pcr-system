# 本地验证数据集画像

数据集路径：`I:\software Project\数据集`

## 文件结构

- `乳腺癌患者临床特征表.xlsx`：35例患者临床特征。
- `image/001.png` 至 `image/035.png`：35张PNG影像，与 `patient_id` 一一对应。

## 临床字段

| 字段 | 含义 |
|---|---|
| `patient_id` | 患者编号，对应影像文件名，如 001.png |
| `pcr（1=达到pcr）` | pCR标签，1为达到pCR |
| `mastectomy_post_nac` | NAC后是否乳房切除 |
| `hr(1=阳性)` | 激素受体状态 |
| `er` | ER状态 |
| `pr` | PR状态 |
| `her2` | HER2状态 |
| `nottingham_grade` | Nottingham分级 |
| `tumor_subtype` | 肿瘤亚型 |
| `age` | 年龄 |
| `menopause` | 绝经状态 |
| `ethnicity` | 种族/人群类别 |

## 当前使用方式

1. `python -m app.services.reset_to_real_dataset`：备份并清理旧业务库，只重新导入本数据集。
2. `python -m app.ml.train_from_local_dataset`：提取临床特征和整图灰度特征，训练课程演示模型。

## 当前数据库状态

- 患者：35例，编号 `LOCAL-001` 至 `LOCAL-035`。
- 临床记录：35条，包含年龄、pCR标签、HR/ER/PR/HER2、Nottingham分级、分子亚型、绝经状态和人群类别。
- 影像记录：35张，均来自 `data/uploads/local_dataset/*.png`。
- 演示上传、harness、合成数据、公开基准数据已从当前业务库和前端指标中剔除。

## 训练边界

样本量只有35例，适合课程演示、端到端链路验证和简历项目展示，不适合声明真实临床泛化性能。所有输出必须保留“仅用于课程项目辅助分析展示，不作为真实临床诊断依据”的免责声明。
