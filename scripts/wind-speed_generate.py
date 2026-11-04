"""合成 10 min 风速序列，边际为固定参数的威布尔分布，固定随机种子。

潜变量是平稳的一阶自回归高斯序列，再经标准正态 CDF 与威布尔
分位函数变成风速。教学小样，不代表任何测风塔或风电场。
运行后覆盖写入 datasets/wind-speed/data.csv。
"""

import math
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
INTERVAL_MIN = 10
# 钟面起点只作六周标签，不含时区，不对应真实测风时段。
DAY_START = "2026-03-01"
N_DAYS = 42
N_STEPS = N_DAYS * 24 * 60 // INTERVAL_MIN
# 两参数威布尔：形状 k、尺度 c（m/s）。k = 2 即瑞利分布，这里略高一点。
K_SHAPE = 2.2
C_SCALE_M_S = 7.0
# 潜变量 AR(1) 系数。10 min 一步，e 折时间约为 -10/ln(0.75) ≈ 35 min。
PHI = 0.75
# 概率积分变换时躲开 0 和 1，避免分位函数出现 inf。
U_EPS = 1e-12

OUT_PATH = Path(__file__).resolve().parents[1] / "datasets" / "wind-speed" / "data.csv"

_ERF = np.vectorize(math.erf, otypes=[float])


def standard_normal_cdf(z: np.ndarray) -> np.ndarray:
    """标准正态 CDF。用 math.erf，不依赖 scipy。"""
    return 0.5 * (1.0 + _ERF(np.asarray(z, dtype=float) / math.sqrt(2.0)))


def latent_gaussian_ar1(rng: np.random.Generator, n: int, phi: float) -> np.ndarray:
    """平稳 N(0, 1) 的 AR(1)。随机数按时间顺序各用一个标准正态。"""
    shock = rng.normal(size=n)
    values = np.empty(n, dtype=float)
    values[0] = shock[0]
    innovation = math.sqrt(max(1.0 - phi * phi, 0.0))
    for i in range(1, n):
        values[i] = phi * values[i - 1] + innovation * shock[i]
    return values


def weibull_ppf(uniform: np.ndarray, k: float, c: float) -> np.ndarray:
    """两参数威布尔分位函数：c · (−ln(1−u))^(1/k)。u 已裁剪到 (0, 1)。"""
    return c * np.power(-np.log1p(-uniform), 1.0 / k)


def build_frame() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    latent = latent_gaussian_ar1(rng, N_STEPS, PHI)
    uniform = np.clip(standard_normal_cdf(latent), U_EPS, 1.0 - U_EPS)
    speed_m_s = np.round(weibull_ppf(uniform, K_SHAPE, C_SCALE_M_S), 3)
    timestamps = pd.date_range(
        f"{DAY_START}T00:00:00", periods=N_STEPS, freq=f"{INTERVAL_MIN}min"
    )
    return pd.DataFrame(
        {
            "timestamp": timestamps.strftime("%Y-%m-%dT%H:%M:%S"),
            "wind_speed_m_s": speed_m_s,
        }
    )


def main() -> None:
    frame = build_frame()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH} rows={len(frame)} cols={frame.shape[1]} seed={SEED}")


if __name__ == "__main__":
    main()
