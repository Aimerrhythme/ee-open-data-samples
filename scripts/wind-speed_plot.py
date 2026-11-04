"""清洗并绘制 datasets/wind-speed/data.csv 的风速序列，并做威布尔拟合。

只做课堂用的最小检查：解析时间、查缺失、丢掉负风速、按时间去重排序、
核对 10 min 间隔，然后打印样本矩、滞后 1 自相关和两参数威布尔极大似然。
上图是记录开头 48 h，下图是全样本直方图和拟合密度。
打印的 k、c 是对这份文件的核对，不是作业答案。
"""

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams["font.sans-serif"] = ["WenQuanYi Micro Hei", "Droid Sans Fallback", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "datasets" / "wind-speed" / "data.csv"
FIG_PATH = ROOT / "datasets" / "wind-speed" / "wind_speed.png"

WIND_COLUMN = "wind_speed_m_s"
REQUIRED = ["timestamp", WIND_COLUMN]


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    frame = raw.copy()
    missing = [name for name in REQUIRED if name not in frame.columns]
    if missing:
        raise ValueError(f"missing columns: {missing}")

    frame["timestamp"] = pd.to_datetime(frame["timestamp"], format="%Y-%m-%dT%H:%M:%S", errors="coerce")
    frame[WIND_COLUMN] = pd.to_numeric(frame[WIND_COLUMN], errors="coerce")

    rows_in = len(frame)
    missing_rows = int(frame.loc[:, REQUIRED].isna().any(axis=1).sum())
    if missing_rows:
        print(f"warning: {missing_rows} rows have missing timestamp or wind speed")
    frame = frame.dropna(subset=list(REQUIRED))

    negative = int((frame[WIND_COLUMN] < 0).sum())
    if negative:
        print(f"warning: dropped {negative} negative wind speeds")
    frame = frame.loc[frame[WIND_COLUMN] >= 0.0]

    frame = frame.drop_duplicates(subset=["timestamp"], keep="first")
    frame = frame.sort_values("timestamp").reset_index(drop=True)

    gaps = frame["timestamp"].diff().dropna()
    irregular = int((gaps != pd.Timedelta(minutes=10)).sum())
    if irregular:
        print(f"warning: {irregular} steps are not 10 min")

    print(
        f"rows in={rows_in} out={len(frame)} dropped={rows_in - len(frame)} "
        f"missing_rows={missing_rows} negative={negative}"
    )
    return frame


def weibull_mle(speed_m_s: np.ndarray) -> tuple[float, float]:
    """两参数威布尔极大似然。位置固定为 0；非正风速不参与。

    剖面掉尺度之后，形状 k 满足
    1/k = Σ(v^k ln v) / Σ(v^k) − mean(ln v)，
    再用 c = (mean(v^k))^(1/k)。
    """
    speed = np.asarray(speed_m_s, dtype=float)
    speed = speed[np.isfinite(speed) & (speed > 0.0)]
    if len(speed) < 2:
        raise ValueError("need at least two positive speeds to fit a Weibull")

    ln_v = np.log(speed)

    def score(k: float) -> tuple[float, float]:
        vk = speed ** k
        s1 = float(vk.sum())
        s2 = float((vk * ln_v).sum())
        s3 = float((vk * ln_v * ln_v).sum())
        g = 1.0 / k + float(ln_v.mean()) - s2 / s1
        gp = -1.0 / (k * k) - (s3 * s1 - s2 * s2) / (s1 * s1)
        return g, gp

    k = 2.0
    for _ in range(60):
        g, gp = score(k)
        if not math.isfinite(gp) or gp == 0.0:
            break
        k_new = k - g / gp
        if not math.isfinite(k_new) or k_new <= 0.05:
            k_new = 0.5 * (k + 0.05)
        if abs(k_new - k) < 1e-12:
            k = float(k_new)
            break
        k = float(k_new)
    else:
        raise RuntimeError("Weibull shape Newton iteration did not converge")

    c = float(np.mean(speed ** k) ** (1.0 / k))
    return k, c


def summarize(frame: pd.DataFrame) -> tuple[float, float]:
    speed = frame[WIND_COLUMN].to_numpy(dtype=float)
    nonpositive = int(np.sum(speed <= 0.0))
    if nonpositive:
        print(f"warning: {nonpositive} non-positive speeds excluded from Weibull MLE")
    k_hat, c_hat = weibull_mle(speed)
    lag1 = float(np.corrcoef(speed[:-1], speed[1:])[0, 1])
    mean = float(speed.mean())
    cubic_mean = float(np.mean(speed ** 3))
    energy_pattern = cubic_mean / (mean ** 3)
    print(
        f"{WIND_COLUMN}: n={len(speed)} min={speed.min():.3f} m/s max={speed.max():.3f} m/s "
        f"mean={mean:.3f} m/s std={float(speed.std(ddof=1)):.3f} m/s"
    )
    print(
        f"weibull_mle: k={k_hat:.4f} c={c_hat:.4f} m/s "
        f"lag1={lag1:.4f} mean_v3={cubic_mean:.3f} energy_pattern={energy_pattern:.4f}"
    )
    return k_hat, c_hat


def weibull_pdf(speed_m_s: np.ndarray, k: float, c: float) -> np.ndarray:
    ratio = speed_m_s / c
    return (k / c) * np.power(ratio, k - 1.0) * np.exp(-(ratio ** k))


def plot(frame: pd.DataFrame, k_hat: float, c_hat: float) -> None:
    speed = frame[WIND_COLUMN].to_numpy(dtype=float)
    fig, (ax_time, ax_hist) = plt.subplots(2, 1, figsize=(9.0, 6.4))

    # 全长六周叠在一起只剩一条色带。上面只画开头 48 h，便于看见前后相关。
    preview_steps = 48 * 60 // 10
    preview = frame.iloc[:preview_steps]
    ax_time.plot(preview["timestamp"], preview[WIND_COLUMN], color="#1f4e79", linewidth=1.2)
    ax_time.set_title("Synthetic 10 min wind speed (first 48 h)")
    ax_time.set_xlabel("Clock time (no timezone)")
    ax_time.set_ylabel("Wind speed (m/s)")
    ax_time.grid(True, alpha=0.3)

    ax_hist.hist(
        speed,
        bins=30,
        density=True,
        color="#8fb4d6",
        edgecolor="white",
        label="Sample / 样本",
    )
    grid = np.linspace(0.0, float(speed.max()) * 1.05, 400)
    ax_hist.plot(
        grid,
        weibull_pdf(grid, k_hat, c_hat),
        color="#b33c3c",
        linewidth=1.8,
        label=f"Weibull MLE  k={k_hat:.3f}  c={c_hat:.3f} m/s",
    )
    ax_hist.set_xlabel("Wind speed (m/s)")
    ax_hist.set_ylabel("Density (1 / (m/s))")
    ax_hist.grid(True, alpha=0.3)
    ax_hist.legend()

    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(FIG_PATH, dpi=120)
    print(f"wrote {FIG_PATH}")


def main() -> None:
    cleaned = clean(pd.read_csv(DATA_PATH))
    k_hat, c_hat = summarize(cleaned)
    plot(cleaned, k_hat, c_hat)


if __name__ == "__main__":
    main()
