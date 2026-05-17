"""基于本地35例生成合成教学数据。

合成数据仅用于课程演示和模型流程验证，不代表真实患者，不用于临床结论。
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[3]
SOURCE_DIR = Path(r"I:\software Project\数据集")
CLINICAL_XLSX = SOURCE_DIR / "乳腺癌患者临床特征表.xlsx"
IMAGE_DIR = SOURCE_DIR / "image"
OUT_DIR = ROOT / "data" / "synthetic"
OUT_IMAGE_DIR = OUT_DIR / "images"
OUT_CSV = OUT_DIR / "synthetic_clinical.csv"
OUT_META = OUT_DIR / "synthetic_metadata.json"


def _choice(rng: np.random.Generator, series: pd.Series):
    values = series.dropna().tolist()
    return rng.choice(values) if values else None


def _clip_int(value: float, low: int, high: int) -> int:
    return int(max(low, min(high, round(value))))


def _image_shape_and_stats() -> tuple[tuple[int, int], float, float]:
    shapes: list[tuple[int, int]] = []
    means: list[float] = []
    stds: list[float] = []
    for path in IMAGE_DIR.glob("*.png"):
        arr = np.asarray(Image.open(path).convert("L"), dtype=np.float32)
        shapes.append((arr.shape[1], arr.shape[0]))
        means.append(float(arr.mean()))
        stds.append(float(arr.std()))
    if not shapes:
        return (512, 512), 95.0, 35.0
    width = int(np.median([s[0] for s in shapes]))
    height = int(np.median([s[1] for s in shapes]))
    return (width, height), float(np.mean(means)), float(np.mean(stds))


def _probability_from_row(row: dict[str, object], rng: np.random.Generator) -> int:
    score = -1.15
    if row.get("her2") == 1:
        score += 0.75
    if row.get("er") == 0:
        score += 0.35
    if row.get("pr") == 0:
        score += 0.25
    if row.get("hr") == 0:
        score += 0.25
    if str(row.get("tumor_subtype", "")).lower().find("her2") >= 0:
        score += 0.45
    if str(row.get("tumor_subtype", "")).lower().find("triple") >= 0:
        score += 0.35
    score += rng.normal(0, 0.35)
    probability = 1 / (1 + np.exp(-score))
    return int(rng.random() < probability)


def _draw_synthetic_image(path: Path, shape: tuple[int, int], mean: float, std: float, rng: np.random.Generator, pcr: int) -> None:
    width, height = shape
    background = rng.normal(mean, max(8, std * 0.45), size=(height, width)).clip(0, 255).astype(np.uint8)
    image = Image.fromarray(background).filter(ImageFilter.GaussianBlur(radius=1.2))
    draw = ImageDraw.Draw(image)
    lesion_count = int(rng.integers(1, 4))
    for _ in range(lesion_count):
        cx = int(rng.integers(width * 0.25, width * 0.75))
        cy = int(rng.integers(height * 0.25, height * 0.75))
        rx = int(rng.integers(width * 0.05, width * 0.16))
        ry = int(rng.integers(height * 0.04, height * 0.14))
        intensity = int(np.clip(mean + (28 if pcr else 18) + rng.normal(0, 12), 0, 255))
        draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=intensity)
    image = image.filter(ImageFilter.GaussianBlur(radius=1.0)).convert("RGB")
    image.save(path)


def generate(sample_count: int = 120, seed: int = 20260517) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    source = pd.read_excel(CLINICAL_XLSX)
    source = source.rename(columns={"pcr（1=达到pcr）": "pcr", "hr(1=阳性)": "hr"})
    labelled = source[source["pcr"].notna()].copy()
    shape, image_mean, image_std = _image_shape_and_stats()
    rows: list[dict[str, object]] = []
    age_mean = float(source["age"].mean())
    age_std = float(source["age"].std() or 8)
    for idx in range(1, sample_count + 1):
        base = labelled.sample(n=1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]
        row = {
            "patient_id": 9000 + idx,
            "source_type": "synthetic",
            "pcr": int(base["pcr"]) if rng.random() < 0.65 else None,
            "mastectomy_post_nac": int(_choice(rng, source["mastectomy_post_nac"])),
            "hr": int(_choice(rng, source["hr"])),
            "er": int(_choice(rng, source["er"])),
            "pr": int(_choice(rng, source["pr"])),
            "her2": int(_choice(rng, source["her2"])),
            "nottingham_grade": _choice(rng, source["nottingham_grade"]),
            "tumor_subtype": _choice(rng, source["tumor_subtype"]),
            "age": _clip_int(rng.normal(age_mean, age_std), 24, 88),
            "menopause": _choice(rng, source["menopause"]),
            "ethnicity": _choice(rng, source["ethnicity"]),
        }
        if row["pcr"] is None:
            row["pcr"] = _probability_from_row(row, rng)
        rows.append(row)
        _draw_synthetic_image(OUT_IMAGE_DIR / f"{int(row['patient_id'])}.png", shape, image_mean, image_std, rng, int(row["pcr"]))

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    meta = {
        "sample_count": sample_count,
        "seed": seed,
        "source": str(CLINICAL_XLSX),
        "image_source_dir": str(IMAGE_DIR),
        "output_csv": str(OUT_CSV),
        "output_image_dir": str(OUT_IMAGE_DIR),
        "usage_boundary": "合成教学数据，不代表真实患者，不用于临床诊断或模型真实性能声明。",
    }
    OUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def main() -> int:
    print(json.dumps(generate(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
