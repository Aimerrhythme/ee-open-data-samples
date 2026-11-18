"""生成变压器油温与负载（合成），写入 datasets/transformer-temp/data.csv。"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "datasets" / "transformer-temp" / "data.csv"

SEED = 42
DAYS = 7
STEP_MIN = 30
DT_H = STEP_MIN / 60.0
TAU_H = 3.0           # 油温时间常数 h
DTO_R = 45.0          # 额定负载下顶层油温升 K
R_LOSS = 5.0          # 负载损耗/空载损耗之比
N_EXP = 0.8           # 油指数
S_RATED_KVA = 1000.0


def main() -> None:
    rng = np.random.default_rng(SEED)
    n = DAYS * 24 * 60 // STEP_MIN
    t_h = np.arange(n) * DT_H
    hod = t_h % 24
    # 负载标幺值：双峰日曲线 + 周末下降 + 噪声
    load = (0.55 + 0.25 * np.exp(-0.5 * ((hod - 11) / 2.5) ** 2)
            + 0.30 * np.exp(-0.5 * ((hod - 19) / 2.0) ** 2))
    day = (t_h // 24).astype(int)
    load = load * np.where(day % 7 >= 5, 0.8, 1.0) + rng.normal(0, 0.02, n)
    load = np.clip(load, 0.2, 1.3)
    # 环境温度：日周期 + 缓慢漂移
    amb = 22 + 6 * np.sin(2 * np.pi * (hod - 9) / 24) + np.cumsum(rng.normal(0, 0.05, n))
    # 一阶热模型：d(theta)/dt = (theta_u - theta)/tau
    dto = np.zeros(n)
    dto[0] = DTO_R * ((load[0] ** 2 * R_LOSS + 1) / (R_LOSS + 1)) ** N_EXP
    for k in range(1, n):
        ult = DTO_R * ((load[k] ** 2 * R_LOSS + 1) / (R_LOSS + 1)) ** N_EXP
        dto[k] = dto[k - 1] + (ult - dto[k - 1]) * (1 - np.exp(-DT_H / TAU_H))
    oil = amb + dto + rng.normal(0, 0.3, n)
    ts = pd.Timestamp("2026-01-01T00:00:00") + pd.to_timedelta(np.arange(n) * STEP_MIN, unit="min")
    df = pd.DataFrame({
        "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S"),
        "load_pu": np.round(load, 4),
        "ambient_c": np.round(amb, 2),
        "top_oil_c": np.round(oil, 2),
    })
    # 人为注入少量缺失与尖峰，供清洗练习
    miss = rng.choice(n, 6, replace=False)
    df.loc[miss, "top_oil_c"] = np.nan
    spike = rng.choice(np.setdiff1d(np.arange(n), miss), 4, replace=False)
    df.loc[spike, "top_oil_c"] = df.loc[spike, "top_oil_c"] + rng.choice([-35.0, 40.0], 4)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"wrote {OUT} rows={len(df)}")


if __name__ == "__main__":
    main()
