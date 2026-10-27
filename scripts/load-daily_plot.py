"""清洗并绘制 datasets/load-daily/data.csv 的典型日负荷曲线。

只做课堂用的最小检查：解析时间、去空、去重、排序、负值剔除、
核对 15 min 间隔，然后打印峰谷与负荷率并出图。
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams["font.sans-serif"] = ["WenQuanYi Micro Hei", "Droid Sans Fallback", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "datasets" / "load-daily" / "data.csv"
FIG_PATH = ROOT / "datasets" / "load-daily" / "load_daily.png"

POWER_COLUMNS = ("residential_p_kw", "commercial_p_kw", "industrial_p_kw")
LABELS = {
    "residential_p_kw": "Residential / 居民",
    "commercial_p_kw": "Commercial / 商业",
    "industrial_p_kw": "Industrial / 工业",
}


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    frame = raw.copy()
    missing = [name for name in ("timestamp", *POWER_COLUMNS) if name not in frame.columns]
    if missing:
        raise ValueError(f"missing columns: {missing}")

    frame["timestamp"] = pd.to_datetime(frame["timestamp"], format="%Y-%m-%dT%H:%M:%S", errors="coerce")
    for name in POWER_COLUMNS:
        frame[name] = pd.to_numeric(frame[name], errors="coerce")

    rows_in = len(frame)
    frame = frame.dropna(subset=["timestamp", *POWER_COLUMNS])
    negative = (frame.loc[:, POWER_COLUMNS] < 0).any(axis=1)
    frame = frame.loc[~negative]
    frame = frame.drop_duplicates(subset=["timestamp"], keep="first")
    frame = frame.sort_values("timestamp").reset_index(drop=True)

    gaps = frame["timestamp"].diff().dropna()
    irregular = int((gaps != pd.Timedelta(minutes=15)).sum())
    if irregular:
        print(f"warning: {irregular} steps are not 15 min")

    print(f"rows in={rows_in} out={len(frame)} dropped={rows_in - len(frame)}")
    return frame


def summarize(frame: pd.DataFrame) -> None:
    for name in POWER_COLUMNS:
        series = frame[name]
        peak_at = frame.loc[series.idxmax(), "timestamp"]
        load_factor = float(series.mean() / series.max())
        print(
            f"{name}: min={series.min():.3f} kW max={series.max():.3f} kW "
            f"mean={series.mean():.3f} kW load_factor={load_factor:.3f} "
            f"peak_time={peak_at.strftime('%H:%M')}"
        )


def plot(frame: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9.0, 4.2))
    for name in POWER_COLUMNS:
        ax.plot(frame["timestamp"], frame[name], label=LABELS[name], linewidth=1.6)
    ax.set_title("Synthetic typical-day load (15 min)")
    ax.set_xlabel("Clock time (no timezone)")
    ax.set_ylabel("Active power (kW)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(FIG_PATH, dpi=120)
    print(f"wrote {FIG_PATH}")


def main() -> None:
    cleaned = clean(pd.read_csv(DATA_PATH))
    summarize(cleaned)
    plot(cleaned)


if __name__ == "__main__":
    main()
