"""合成典型日负荷曲线（居民 / 商业 / 工业），15 min，固定随机种子。

教学小样，不代表任何真实台区或厂站。运行后覆盖写入
datasets/load-daily/data.csv。
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
INTERVAL_MIN = 15
# 钟面日期只作典型工作日标签，不含时区，不对应真实运行日。
DAY = "2026-01-07"
N_STEPS = 24 * 60 // INTERVAL_MIN

# 三类对象的教学用峰值（kW）。量级取可比的馈线/用户群，便于叠在同一张图上。
PEAK_KW = {
    "residential": 480.0,
    "commercial": 650.0,
    "industrial": 920.0,
}

OUT_PATH = Path(__file__).resolve().parents[1] / "datasets" / "load-daily" / "data.csv"


def smoothstep(hours: np.ndarray, start: float, end: float) -> np.ndarray:
    span = end - start
    t = np.clip((hours - start) / span, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def gauss(hours: np.ndarray, center: float, sigma: float) -> np.ndarray:
    return np.exp(-0.5 * ((hours - center) / sigma) ** 2)


def shape_residential(hours: np.ndarray) -> np.ndarray:
    """夜间低谷、早晨小峰、傍晚主峰。"""
    return (
        0.18
        + 0.22 * gauss(hours, 7.4, 1.15)
        + 0.08 * gauss(hours, 12.2, 1.4)
        + 0.62 * gauss(hours, 19.6, 1.55)
        + 0.06 * gauss(hours, 22.8, 0.7)
    )


def shape_commercial(hours: np.ndarray) -> np.ndarray:
    """夜间很低，营业时段抬升并在午间略高，傍晚回落。"""
    open_hours = smoothstep(hours, 7.0, 9.2) * (1.0 - smoothstep(hours, 17.6, 20.5))
    return 0.08 + 0.78 * open_hours + 0.07 * gauss(hours, 12.4, 0.55)


def shape_industrial(hours: np.ndarray) -> np.ndarray:
    """连续生产：夜间仍有基荷，白班接近平坦，傍晚略降。"""
    day_shift = smoothstep(hours, 6.5, 8.0) * (1.0 - smoothstep(hours, 16.8, 19.0))
    evening = smoothstep(hours, 18.5, 19.5) * (1.0 - smoothstep(hours, 22.0, 23.2))
    # 白班内轻微拱起，避免平台段的峰值时刻只由噪声决定。
    crest = 0.06 * gauss(hours, 11.0, 2.0)
    return 0.48 + 0.46 * day_shift + crest + 0.10 * evening


def scale_to_peak(shape: np.ndarray, peak_kw: float, rng: np.random.Generator) -> np.ndarray:
    unit = np.asarray(shape, dtype=float)
    unit = unit / unit.max()
    noise = rng.normal(0.0, 0.012, size=unit.shape)
    power_kw = np.clip(peak_kw * unit * (1.0 + noise), 0.0, None)
    # 噪声后再归一到设定峰值，三类曲线的日最大功率可复现。
    return power_kw * (peak_kw / power_kw.max())


def build_frame() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    hours = np.arange(N_STEPS) * (INTERVAL_MIN / 60.0)
    timestamps = pd.date_range(f"{DAY}T00:00:00", periods=N_STEPS, freq=f"{INTERVAL_MIN}min")
    frame = pd.DataFrame(
        {
            "timestamp": timestamps.strftime("%Y-%m-%dT%H:%M:%S"),
            "residential_p_kw": np.round(
                scale_to_peak(shape_residential(hours), PEAK_KW["residential"], rng), 3
            ),
            "commercial_p_kw": np.round(
                scale_to_peak(shape_commercial(hours), PEAK_KW["commercial"], rng), 3
            ),
            "industrial_p_kw": np.round(
                scale_to_peak(shape_industrial(hours), PEAK_KW["industrial"], rng), 3
            ),
        }
    )
    return frame


def main() -> None:
    frame = build_frame()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH} rows={len(frame)} cols={frame.shape[1]} seed={SEED}")


if __name__ == "__main__":
    main()
