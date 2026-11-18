"""清洗（缺失插值 + 滚动中位数去尖峰）并出图：油温与负载。"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "datasets" / "transformer-temp" / "data.csv"
PNG = ROOT / "datasets" / "transformer-temp" / "transformer_temp.png"


def clean(df: pd.DataFrame, win: int = 7, thr: float = 5.0) -> pd.DataFrame:
    s = df["top_oil_c"]
    med = s.rolling(win, center=True, min_periods=1).median()
    bad = (s - med).abs() > thr
    out = df.copy()
    out["is_outlier"] = bad.fillna(False)
    out["is_missing"] = s.isna()
    out["top_oil_clean_c"] = s.mask(bad).interpolate(limit_direction="both")
    return out


def main() -> None:
    df = pd.read_csv(CSV, parse_dates=["timestamp"])
    c = clean(df)
    print(f"missing={int(c.is_missing.sum())} outliers={int(c.is_outlier.sum())}")
    fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    ax[0].plot(c.timestamp, c.top_oil_c, lw=0.6, color="tab:gray", label="raw")
    ax[0].plot(c.timestamp, c.top_oil_clean_c, lw=1, color="tab:red", label="clean")
    ax[0].plot(c.timestamp, c.ambient_c, lw=0.8, color="tab:blue", label="ambient")
    ax[0].set_ylabel("temperature (C)")
    ax[0].legend(loc="upper right")
    ax[1].plot(c.timestamp, c.load_pu, lw=0.8, color="tab:green")
    ax[1].set_ylabel("load (pu)")
    fig.suptitle("Transformer top-oil temperature vs load (synthetic)")
    fig.tight_layout()
    fig.savefig(PNG, dpi=110)
    print(f"saved {PNG}")


if __name__ == "__main__":
    main()
