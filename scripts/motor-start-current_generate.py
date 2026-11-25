"""生成电机直接启动电流波形（合成），写入 datasets/motor-start-current/data.csv。"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "datasets" / "motor-start-current" / "data.csv"

SEED = 42
FS = 1000          # Hz
DUR = 3.0          # s
F0 = 50.0          # Hz
I_RATED = 20.0     # A，额定电流有效值
K_START = 6.0      # 启动电流倍数
T_START = 0.2      # 合闸时刻 s
TAU_ENV = 0.6      # 启动包络衰减时间常数 s
TAU_DC = 0.05      # 直流偏置衰减时间常数 s


def main() -> None:
    rng = np.random.default_rng(SEED)
    n = int(FS * DUR)
    t = np.arange(n) / FS
    ts_on = t >= T_START
    tt = np.where(ts_on, t - T_START, 0.0)
    # 有效值包络：从 K*I_rated 指数衰减到 I_rated（空载前的示意）
    env = I_RATED + (K_START - 1) * I_RATED * np.exp(-tt / TAU_ENV)
    phi = -np.deg2rad(70)  # 启动阶段滞后角
    ac = np.sqrt(2) * env * np.sin(2 * np.pi * F0 * t + phi)
    dc = -np.sqrt(2) * (K_START * I_RATED) * np.sin(phi) * np.exp(-tt / TAU_DC)
    i_a = np.where(ts_on, ac + dc, 0.0) + rng.normal(0, 0.4, n)
    ts = pd.Timestamp("2026-01-01T00:00:00") + pd.to_timedelta(np.arange(n) / FS, unit="s")
    df = pd.DataFrame({
        "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S.%f"),
        "i_a_a": np.round(i_a, 3),
    })
    # 注入 5 个采样丢失与 3 个尖峰，供清洗练习
    miss = rng.choice(np.arange(n // 4, n), 5, replace=False)
    df.loc[miss, "i_a_a"] = np.nan
    spike = rng.choice(np.setdiff1d(np.arange(n // 4, n), miss), 3, replace=False)
    df.loc[spike, "i_a_a"] = df.loc[spike, "i_a_a"] + rng.choice([-60.0, 80.0], 3)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"wrote {OUT} rows={len(df)}")


if __name__ == "__main__":
    main()
