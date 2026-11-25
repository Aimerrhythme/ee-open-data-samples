"""清洗（缺失插值 + 去尖峰）、计算一周期滑动有效值包络并出图：电机启动电流。"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "datasets" / "motor-start-current" / "data.csv"
PNG = ROOT / "datasets" / "motor-start-current" / "motor_start_current.png"
FS = 1000
CYCLE = 20  # 50 Hz @ 1 kHz：每周期 20 点


def clean(df: pd.DataFrame, win: int = 5, thr: float = 25.0) -> pd.DataFrame:
    s = df["i_a_a"]
    med = s.rolling(win, center=True, min_periods=1).median()
    bad = (s - med).abs() > thr
    out = df.copy()
    out["is_missing"] = s.isna()
    out["is_outlier"] = bad.fillna(False)
    out["i_a_clean_a"] = s.mask(bad).interpolate(limit_direction="both")
    out["i_rms_a"] = np.sqrt((out["i_a_clean_a"] ** 2).rolling(CYCLE, min_periods=CYCLE).mean())
    return out


def main() -> None:
    df = pd.read_csv(CSV, parse_dates=["timestamp"])
    c = clean(df)
    peak = c["i_a_clean_a"].abs().max()
    rms_max = c["i_rms_a"].max()
    rms_end = c["i_rms_a"].iloc[-CYCLE * 5:].mean()
    print(f"missing={int(c.is_missing.sum())} outliers={int(c.is_outlier.sum())}")
    print(f"peak={peak:.1f} A  rms_max={rms_max:.1f} A  rms_end={rms_end:.1f} A  ratio={rms_max / rms_end:.2f}")
    t = np.arange(len(c)) / FS
    fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    ax[0].plot(t, c["i_a_a"], lw=0.5, color="tab:gray", label="raw")
    ax[0].plot(t, c["i_a_clean_a"], lw=0.6, color="tab:red", label="clean")
    ax[0].set_ylabel("current (A)")
    ax[0].legend(loc="upper right")
    ax[1].plot(t, c["i_rms_a"], lw=1.2, color="tab:blue")
    ax[1].set_ylabel("sliding RMS (A)")
    ax[1].set_xlabel("time (s)")
    fig.suptitle("Motor direct-on-line starting current (synthetic)")
    fig.tight_layout()
    fig.savefig(PNG, dpi=110)
    print(f"saved {PNG}")


if __name__ == "__main__":
    main()
