"""清洗并绘制 datasets/pv-daily/data.csv 的光伏日出力曲线。

只做课堂用的最小检查：解析时间、查缺失、负值裁到 0、
晴空辐照为 0 的时刻出力置 0、按时间去重排序、核对 15 min 间隔，
然后打印峰值与日电量并出图。
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams["font.sans-serif"] = ["WenQuanYi Micro Hei", "Droid Sans Fallback", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "datasets" / "pv-daily" / "data.csv"
FIG_PATH = ROOT / "datasets" / "pv-daily" / "pv_daily.png"

# 与生成脚本一致的教学额定，只用于打印容量系数，不改数据。
P_STC_KW = 500.0
INTERVAL_HOURS = 0.25

GHI_COLUMN = "clear_sky_ghi_w_m2"
POWER_COLUMNS = ["sunny_p_kw", "cloudy_p_kw", "overcast_p_kw"]
LABELS = {
    "sunny_p_kw": "Sunny / 晴",
    "cloudy_p_kw": "Cloudy / 多云",
    "overcast_p_kw": "Overcast / 阴",
}
REQUIRED = ["timestamp", GHI_COLUMN, *POWER_COLUMNS]


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    frame = raw.copy()
    missing = [name for name in REQUIRED if name not in frame.columns]
    if missing:
        raise ValueError(f"missing columns: {missing}")

    frame["timestamp"] = pd.to_datetime(frame["timestamp"], format="%Y-%m-%dT%H:%M:%S", errors="coerce")
    for name in (GHI_COLUMN, *POWER_COLUMNS):
        frame[name] = pd.to_numeric(frame[name], errors="coerce")

    rows_in = len(frame)
    missing_rows = int(frame.loc[:, REQUIRED].isna().any(axis=1).sum())
    if missing_rows:
        print(f"warning: {missing_rows} rows have missing timestamp or values")
    frame = frame.dropna(subset=list(REQUIRED))

    ghi_negative = int((frame[GHI_COLUMN] < 0).sum())
    frame[GHI_COLUMN] = frame[GHI_COLUMN].clip(lower=0.0)
    power_negative = int((frame.loc[:, POWER_COLUMNS] < 0).sum().sum())
    frame[POWER_COLUMNS] = frame[POWER_COLUMNS].clip(lower=0.0)

    night = frame[GHI_COLUMN] <= 0.0
    night_nonzero = int((night & (frame.loc[:, POWER_COLUMNS] > 0.0).any(axis=1)).sum())
    frame.loc[night, POWER_COLUMNS] = 0.0

    frame = frame.drop_duplicates(subset=["timestamp"], keep="first")
    frame = frame.sort_values("timestamp").reset_index(drop=True)

    gaps = frame["timestamp"].diff().dropna()
    irregular = int((gaps != pd.Timedelta(minutes=15)).sum())
    if irregular:
        print(f"warning: {irregular} steps are not 15 min")

    print(
        f"rows in={rows_in} out={len(frame)} dropped={rows_in - len(frame)} "
        f"missing_rows={missing_rows} clipped_ghi={ghi_negative} "
        f"clipped_power={power_negative} night_zeroed={night_nonzero}"
    )
    return frame


def summarize(frame: pd.DataFrame) -> None:
    ghi = frame[GHI_COLUMN]
    ghi_peak_at = frame.loc[ghi.idxmax(), "timestamp"]
    print(
        f"{GHI_COLUMN}: min={ghi.min():.3f} W/m^2 max={ghi.max():.3f} W/m^2 "
        f"peak_time={ghi_peak_at.strftime('%H:%M')}"
    )
    for name in POWER_COLUMNS:
        series = frame[name]
        peak_at = frame.loc[series.idxmax(), "timestamp"]
        energy_kwh = float(series.sum() * INTERVAL_HOURS)
        capacity_factor = float(series.mean() / P_STC_KW)
        print(
            f"{name}: min={series.min():.3f} kW max={series.max():.3f} kW "
            f"mean={series.mean():.3f} kW energy={energy_kwh:.3f} kWh "
            f"capacity_factor={capacity_factor:.3f} peak_time={peak_at.strftime('%H:%M')}"
        )


def plot(frame: pd.DataFrame) -> None:
    fig, (ax_power, ax_ghi) = plt.subplots(2, 1, figsize=(9.0, 6.4), sharex=True)
    for name in POWER_COLUMNS:
        ax_power.plot(frame["timestamp"], frame[name], label=LABELS[name], linewidth=1.6)
    ax_power.set_title("Synthetic PV daily output (15 min)")
    ax_power.set_ylabel("AC power (kW)")
    ax_power.grid(True, alpha=0.3)
    ax_power.legend()

    ax_ghi.plot(
        frame["timestamp"],
        frame[GHI_COLUMN],
        color="#c47b2b",
        linewidth=1.6,
        label="Clear-sky GHI / 晴空辐照",
    )
    ax_ghi.set_xlabel("Clock time (no timezone)")
    ax_ghi.set_ylabel("GHI (W/m²)")
    ax_ghi.grid(True, alpha=0.3)
    ax_ghi.legend()
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
