"""ROI 特征提取：面积、灰度统计、纹理特征（偏度/峰度/熵/对比度/能量）和形态特征（周长/紧凑度/圆度）。"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw


def _points(roi_json: dict[str, Any] | str) -> list[tuple[float, float]]:
    if isinstance(roi_json, str):
        roi_json = json.loads(roi_json)
    pts = roi_json.get("points", [])
    return [(float(p["x"]), float(p["y"])) for p in pts]


def _roi_type(roi_json: dict[str, Any] | str) -> str:
    """获取 ROI 类型：rectangle / ellipse / polygon"""
    if isinstance(roi_json, str):
        roi_json = json.loads(roi_json)
    return roi_json.get("type", "rectangle")


def polygon_area(points: list[tuple[float, float]]) -> float:
    if len(points) < 2:
        return 0.0
    if len(points) == 2:
        (x1, y1), (x2, y2) = points
        return abs((x2 - x1) * (y2 - y1))
    total = 0.0
    for i, (x1, y1) in enumerate(points):
        x2, y2 = points[(i + 1) % len(points)]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2


def polygon_perimeter(points: list[tuple[float, float]]) -> float:
    """计算多边形周长"""
    if len(points) < 2:
        return 0.0
    if len(points) == 2:
        (x1, y1), (x2, y2) = points
        return 2 * (abs(x2 - x1) + abs(y2 - y1))
    total = 0.0
    for i in range(len(points)):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % len(points)]
        total += math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return total


def _draw_roi_mask(image_size: tuple[int, int], roi_type: str, points: list[tuple[float, float]]) -> Image.Image:
    """根据 ROI 类型绘制 mask"""
    mask = Image.new("L", image_size, 0)
    draw = ImageDraw.Draw(mask)
    if roi_type == "ellipse" and len(points) == 2:
        # 椭圆用外接矩形两个角点定义
        draw.ellipse([points[0], points[1]], fill=255)
    elif len(points) == 2:
        # 矩形
        draw.rectangle([points[0], points[1]], fill=255)
    else:
        # 多边形
        draw.polygon(points, fill=255)
    return mask


def _texture_features(values: np.ndarray) -> dict[str, float]:
    """计算纹理特征：偏度、峰度、熵、对比度、能量"""
    if values.size == 0:
        return {"gray_skewness": 0.0, "gray_kurtosis": 0.0, "gray_entropy": 0.0, "gray_contrast": 0.0, "gray_energy": 0.0}

    mean = float(values.mean())
    std = float(values.std())
    n = values.size

    # 偏度 (Skewness)
    if std > 1e-6:
        skewness = float(np.mean(((values - mean) / std) ** 3))
    else:
        skewness = 0.0

    # 峰度 (Kurtosis) - 超额峰度
    if std > 1e-6:
        kurtosis = float(np.mean(((values - mean) / std) ** 4) - 3.0)
    else:
        kurtosis = 0.0

    # 熵 (Entropy)
    hist, _ = np.histogram(values, bins=64, range=(0, 255))
    prob = hist / hist.sum()
    prob = prob[prob > 0]
    entropy = float(-np.sum(prob * np.log2(prob)))

    # 对比度 (Contrast) - 灰度范围与标准差
    contrast = float(values.max() - values.min())

    # 能量 (Energy) - 灰度均匀性
    energy = float(np.sum(prob ** 2))

    return {
        "gray_skewness": round(skewness, 4),
        "gray_kurtosis": round(kurtosis, 4),
        "gray_entropy": round(entropy, 4),
        "gray_contrast": round(contrast, 4),
        "gray_energy": round(energy, 6),
    }


def _shape_features(area: float, points: list[tuple[float, float]], roi_type: str) -> dict[str, float]:
    """计算形态特征：周长、紧凑度、圆度"""
    perimeter = polygon_perimeter(points)

    # 椭圆的周长近似
    if roi_type == "ellipse" and len(points) == 2:
        (x1, y1), (x2, y2) = points
        a = abs(x2 - x1) / 2
        b = abs(y2 - y1) / 2
        # Ramanujan 近似公式
        perimeter = math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))
        area = math.pi * a * b

    # 紧凑度 (Compactness) = 4π·面积 / 周长²
    if perimeter > 1e-6:
        compactness = (4 * math.pi * area) / (perimeter ** 2)
    else:
        compactness = 0.0

    # 圆度 (Circularity) = 周长² / (4π·面积)
    if area > 1e-6:
        circularity = (perimeter ** 2) / (4 * math.pi * area)
    else:
        circularity = 0.0

    return {
        "perimeter": round(perimeter, 2),
        "compactness": round(min(compactness, 1.0), 4),
        "circularity": round(circularity, 4),
    }


def extract_roi_features(image_path: str | Path | None, roi_json: dict[str, Any] | str) -> dict[str, float]:
    """提取完整 ROI 特征集：灰度统计 + 纹理 + 形态"""
    points = _points(roi_json)
    roi_type = _roi_type(roi_json)
    area = polygon_area(points)

    empty_result = {
        "area": float(area), "gray_mean": 0.0, "gray_std": 0.0, "gray_min": 0.0, "gray_max": 0.0,
        "gray_skewness": 0.0, "gray_kurtosis": 0.0, "gray_entropy": 0.0, "gray_contrast": 0.0, "gray_energy": 0.0,
        "perimeter": 0.0, "compactness": 0.0, "circularity": 0.0,
    }

    if not image_path or not Path(image_path).exists() or len(points) < 2:
        return empty_result

    image = Image.open(image_path).convert("L")
    arr = np.asarray(image, dtype=np.float32)

    mask = _draw_roi_mask(image.size, roi_type, points)
    mask_arr = np.asarray(mask) > 0
    values = arr[mask_arr]

    if values.size == 0:
        return empty_result

    # 基础灰度统计
    result = {
        "area": float(values.size),
        "gray_mean": round(float(values.mean()), 2),
        "gray_std": round(float(values.std()), 2),
        "gray_min": float(values.min()),
        "gray_max": float(values.max()),
    }

    # 纹理特征
    result.update(_texture_features(values))

    # 形态特征
    result.update(_shape_features(result["area"], points, roi_type))

    return result
