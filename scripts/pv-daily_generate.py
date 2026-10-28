"""合成光伏日出力曲线（晴 / 多云 / 阴），15 min，固定随机种子。

晴空辐照用钟形的太阳高度角模型，三种天气各自乘一段云透射率。
教学小样，不代表任何真实光伏电站。运行后覆盖写入
datasets/pv-daily/data.csv。
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
INTERVAL_MIN = 15
# 钟面日期只作夏至几何的标签，不含时区，不对应真实运行日。
DAY = "2026-06-21"
N_STEPS = 24 * 60 // INTERVAL_MIN
# 教学用假想纬度，不是某座电站的站址。
LAT_DEG = 30.0
# 标准测试条件（GHI = 1000 W/m²、电池 25°C）下的教学额定功率。
P_STC_KW = 500.0
# 晶硅组件功率温度系数的典型量级（1/°C）。
GAMMA_PER_C = -0.004
# Haurwitz (1945) 晴空水平面总辐照近似：G = A · sin(α) · exp(-B / sin(α))。
HAURWITZ_A = 1098.0
HAURWITZ_B = 0.057

# 云透射率：均值、平稳标准差、相关时间（以 15 min 为一步）、裁剪区间。
# 顺序固定，随机数按晴 → 多云 → 阴消耗，种子才能复现。
CLOUD = {
    "sunny": {"mu": 0.96, "sigma": 0.03, "tau_steps": 3.0, "low": 0.78, "high": 1.0},
    "cloudy": {"mu": 0.55, "sigma": 0.16, "tau_steps": 2.5, "low": 0.12, "high": 0.90},
    "overcast": {"mu": 0.22, "sigma": 0.035, "tau_steps": 10.0, "low": 0.08, "high": 0.38},
}

OUT_PATH = Path(__file__).resolve().parents[1] / "datasets" / "pv-daily" / "data.csv"


def day_of_year_number(day: str) -> int:
    """非闰年的年内日序。钟面年 2026 不是闰年，6 月 21 日为第 172 天。"""
    month = int(day[5:7])
    day_of_month = int(day[8:10])
    month_lengths = (0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    return sum(month_lengths[:month]) + day_of_month


def declination_deg(day_of_year: int) -> float:
    """Cooper 近似：δ = 23.45° · sin(360°/365 · (284 + n))。"""
    argument = np.deg2rad(360.0 / 365.0 * (284 + day_of_year))
    return float(23.45 * np.sin(argument))


def solar_elevation_deg(hours: np.ndarray, lat_deg: float, decl_deg: float) -> np.ndarray:
    """当地太阳时的太阳高度角（度）。正午固定在 12:00，忽略时差与时区。"""
    lat = np.deg2rad(lat_deg)
    decl = np.deg2rad(decl_deg)
    hour_angle = np.deg2rad(15.0 * (hours - 12.0))
    sin_el = np.sin(lat) * np.sin(decl) + np.cos(lat) * np.cos(decl) * np.cos(hour_angle)
    return np.rad2deg(np.arcsin(np.clip(sin_el, -1.0, 1.0)))


def clear_sky_ghi(elevation_deg: np.ndarray) -> np.ndarray:
    """晴空水平面总辐照（W/m²）。高度角 ≤ 0 时为 0，夜间没有辐照。"""
    sin_el = np.sin(np.deg2rad(elevation_deg))
    ghi = np.zeros_like(sin_el, dtype=float)
    daylight = sin_el > 0.0
    ghi[daylight] = HAURWITZ_A * sin_el[daylight] * np.exp(-HAURWITZ_B / sin_el[daylight])
    return ghi


def ou_series(rng: np.random.Generator, n: int, mu: float, sigma: float, tau_steps: float) -> np.ndarray:
    """离散 Ornstein–Uhlenbeck。相关时间以 15 min 步计，平稳标准差为 sigma。"""
    values = np.empty(n, dtype=float)
    values[0] = mu
    phi = float(np.exp(-1.0 / tau_steps))
    shock = sigma * np.sqrt(max(1.0 - phi * phi, 0.0))
    for i in range(1, n):
        values[i] = mu + phi * (values[i - 1] - mu) + shock * float(rng.normal())
    return values


def cloud_transmittance(kind: str, n: int, rng: np.random.Generator) -> np.ndarray:
    """云透射率，乘在晴空辐照上。夜间出力另置 0，不使用这里的取值。"""
    spec = CLOUD[kind]
    raw = ou_series(rng, n, spec["mu"], spec["sigma"], spec["tau_steps"])
    return np.clip(raw, spec["low"], spec["high"])


def cell_temperature_c(ghi_w_m2: np.ndarray) -> np.ndarray:
    """由有效辐照粗算电池温度：环境底温再加辐照升温。不是实测热模型。"""
    ghi_norm = np.clip(np.asarray(ghi_w_m2, dtype=float) / 1000.0, 0.0, None)
    ambient_c = 22.0 + 10.0 * ghi_norm
    return ambient_c + 25.0 * ghi_norm


def power_kw(ghi_clear: np.ndarray, transmittance: np.ndarray) -> np.ndarray:
    """P = P_stc · (G_clear · k / 1000) · [1 + γ (T_cell − 25)]，夜间与负值为 0。"""
    ghi_effective = ghi_clear * transmittance
    temp_factor = 1.0 + GAMMA_PER_C * (cell_temperature_c(ghi_effective) - 25.0)
    power = P_STC_KW * (ghi_effective / 1000.0) * temp_factor
    power = np.where(ghi_clear <= 0.0, 0.0, power)
    return np.clip(power, 0.0, None)


def build_frame() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    hours = np.arange(N_STEPS) * (INTERVAL_MIN / 60.0)
    elevation = solar_elevation_deg(hours, LAT_DEG, declination_deg(day_of_year_number(DAY)))
    ghi = clear_sky_ghi(elevation)
    timestamps = pd.date_range(f"{DAY}T00:00:00", periods=N_STEPS, freq=f"{INTERVAL_MIN}min")
    sunny_k = cloud_transmittance("sunny", N_STEPS, rng)
    cloudy_k = cloud_transmittance("cloudy", N_STEPS, rng)
    overcast_k = cloud_transmittance("overcast", N_STEPS, rng)
    return pd.DataFrame(
        {
            "timestamp": timestamps.strftime("%Y-%m-%dT%H:%M:%S"),
            "clear_sky_ghi_w_m2": np.round(ghi, 3),
            "sunny_p_kw": np.round(power_kw(ghi, sunny_k), 3),
            "cloudy_p_kw": np.round(power_kw(ghi, cloudy_k), 3),
            "overcast_p_kw": np.round(power_kw(ghi, overcast_k), 3),
        }
    )


def main() -> None:
    frame = build_frame()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH} rows={len(frame)} cols={frame.shape[1]} seed={SEED}")


if __name__ == "__main__":
    main()
