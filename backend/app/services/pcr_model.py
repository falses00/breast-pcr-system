"""规则 pCR 辅助分析模型。

注意：该模型仅用于课程项目展示，不具备真实临床诊断能力。
增强版本：支持分子分型组合规则、Nottingham 分级、纹理特征、风险等级输出。
"""

from __future__ import annotations

from dataclasses import dataclass, field


DISCLAIMER = "仅用于课程项目辅助分析展示，不作为真实临床诊断依据，最终判断必须由临床医生结合完整病历完成。"


@dataclass
class PCRPrediction:
    probability: float
    explanations: list[str]
    risk_level: str = "中等"
    molecular_subtype: str = "未分类"
    key_factors: list[str] = field(default_factory=list)
    disclaimer: str = DISCLAIMER


def _positive(value: str | None) -> bool:
    return str(value or "").strip() in {"阳性", "positive", "Positive", "+", "3+"}


def _classify_subtype(er: str | None, pr: str | None, her2: str | None, ki67: float | None) -> tuple[str, float]:
    """基于分子分型返回分类和基础 pCR 概率调整值"""
    er_pos = _positive(er)
    pr_pos = _positive(pr)
    her2_pos = _positive(her2)
    high_ki67 = (ki67 or 0) >= 20

    if not er_pos and not pr_pos and not her2_pos:
        return "三阴性(TNBC)", 0.10  # 三阴性对化疗更敏感
    elif her2_pos and not er_pos:
        return "HER2过表达型", 0.12
    elif her2_pos and er_pos:
        return "Luminal-HER2型", 0.06
    elif er_pos and high_ki67:
        return "Luminal B型", -0.02
    elif er_pos:
        return "Luminal A型", -0.08  # Luminal A 型 pCR 率最低
    else:
        return "未分类", 0.0


def rule_based_pcr_prediction(
    *,
    age: int | None,
    er_status: str | None,
    pr_status: str | None,
    her2_status: str | None,
    ki67: float | None,
    lesion_area: float | None,
    gray_mean: float | None,
    nottingham_grade: str | None = None,
    treatment_plan: str | None = None,
    gray_entropy: float | None = None,
    gray_contrast: float | None = None,
    compactness: float | None = None,
) -> PCRPrediction:
    score = 0.35
    reasons: list[str] = ["基础概率来自课程演示规则模型。"]
    key_factors: list[str] = []

    # ── 分子分型综合评估 ──
    subtype, subtype_adj = _classify_subtype(er_status, pr_status, her2_status, ki67)
    score += subtype_adj
    reasons.append(f"分子分型判定为{subtype}，规则模型调整 {subtype_adj:+.2f}。")
    key_factors.append(f"分子分型: {subtype}")

    # ── 年龄因素 ──
    if age is not None:
        if age < 40:
            score += 0.08
            reasons.append("年龄低于40岁，年轻患者化疗敏感性较高，规则模型加分。")
            key_factors.append("年轻患者(＜40岁)")
        elif age < 50:
            score += 0.04
            reasons.append("年龄40-50岁区间，规则模型给予轻度加分。")
        elif age > 65:
            score -= 0.05
            reasons.append("年龄高于65岁，规则模型给予轻度减分。")

    # ── HER2 状态 ──
    if _positive(her2_status):
        score += 0.08
        reasons.append("HER2阳性在演示规则中与较高治疗响应相关（靶向治疗获益）。")
        key_factors.append("HER2阳性")

    # ── ER/PR 状态 ──
    if not _positive(er_status) and not _positive(pr_status):
        score += 0.06
        reasons.append("HR阴性（ER/PR双阴）在规则中给予加分，化疗敏感性较高。")
        key_factors.append("HR阴性")
    elif not _positive(er_status):
        score += 0.04
        reasons.append("ER阴性在演示规则中给予轻度加分。")
    elif not _positive(pr_status):
        score += 0.02
        reasons.append("PR阴性在演示规则中给予轻度加分。")

    # ── Ki-67 增殖指数 ──
    if ki67 is not None:
        if ki67 >= 40:
            score += 0.10
            reasons.append(f"Ki-67={ki67}%，高增殖活跃，规则模型认为化疗敏感性高。")
            key_factors.append(f"高Ki-67({ki67}%)")
        elif ki67 >= 20:
            score += 0.05
            reasons.append(f"Ki-67={ki67}%，中等增殖水平，规则模型轻度加分。")
        elif ki67 < 10:
            score -= 0.04
            reasons.append(f"Ki-67={ki67}%，低增殖水平，规则模型给予减分。")

    # ── Nottingham 分级 ──
    if nottingham_grade:
        grade = str(nottingham_grade).strip().upper()
        if "III" in grade or "3" in grade:
            score += 0.06
            reasons.append("Nottingham分级III级，高级别肿瘤化疗敏感性较高。")
            key_factors.append("Nottingham III级")
        elif "II" in grade or "2" in grade:
            score += 0.02
            reasons.append("Nottingham分级II级，规则模型轻度加分。")
        elif "I" in grade or "1" in grade:
            score -= 0.03
            reasons.append("Nottingham分级I级，低级别肿瘤pCR率较低。")

    # ── 治疗方案 ──
    if treatment_plan:
        plan = str(treatment_plan).lower()
        if "靶向" in plan or "曲妥珠单抗" in plan or "herceptin" in plan:
            score += 0.06
            reasons.append("治疗方案含靶向治疗，规则模型给予加分。")
        if "蒽环" in plan or "紫杉" in plan:
            score += 0.03
            reasons.append("治疗方案含蒽环/紫杉类化疗，为标准新辅助方案。")

    # ── ROI 面积特征 ──
    if lesion_area is not None:
        if lesion_area < 1200:
            score += 0.05
            reasons.append("ROI面积较小（<1200像素），演示规则给予轻度加分。")
        elif lesion_area > 6000:
            score -= 0.07
            reasons.append("ROI面积较大（>6000像素），演示规则给予减分。")
            key_factors.append("大病灶面积")

    # ── 影像灰度特征 ──
    if gray_mean is not None and gray_mean > 120:
        score += 0.03
        reasons.append("ROI灰度均值较高，作为影像强度提示因子。")

    # ── 纹理特征（新增）──
    if gray_entropy is not None and gray_entropy > 5.0:
        score += 0.04
        reasons.append(f"ROI纹理熵={gray_entropy:.2f}，纹理复杂度高，可能提示异质性。")
        key_factors.append("高纹理异质性")
    if gray_contrast is not None and gray_contrast > 180:
        score += 0.03
        reasons.append(f"ROI对比度={gray_contrast:.1f}，灰度范围大，提示组织异质性。")

    # ── 形态特征（新增）──
    if compactness is not None and compactness < 0.5:
        score -= 0.03
        reasons.append(f"ROI紧凑度={compactness:.3f}，形状不规则，可能提示浸润性生长。")
        key_factors.append("形状不规则")

    probability = max(0.03, min(0.97, score))

    # ── 风险等级 ──
    if probability >= 0.6:
        risk_level = "高概率"
    elif probability >= 0.35:
        risk_level = "中等"
    else:
        risk_level = "低概率"

    return PCRPrediction(
        probability=probability,
        explanations=reasons,
        risk_level=risk_level,
        molecular_subtype=subtype,
        key_factors=key_factors if key_factors else ["暂无突出因素"],
    )
