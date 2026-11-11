"""清洗并绘制 datasets/harmonic-waveform/data.csv，用 FFT 估各次谐波与 THD。

最小检查：解析时间、丢缺失、去重排序、核对采样间隔；取整数个周期做 FFT。
打印的数值是对这份文件的核对，不是作业答案。
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datasets" / "harmonic-waveform" / "data.csv"
FIG = ROOT / "datasets" / "harmonic-waveform" / "harmonic_waveform.png"
F0 = 50.0
SPC = 128


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["i_a"] = pd.to_numeric(df["i_a"], errors="coerce")
    n_in = len(df)
    df = df.dropna().drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    dt = df["timestamp"].diff().dropna().dt.total_seconds()
    bad = int((abs(dt - 1.0 / (F0 * SPC)) > 1e-6).sum())
    if bad:
        print(f"warning: {bad} steps deviate from the nominal sampling interval")
    print(f"rows in={n_in} out={len(df)}")
    return df


def analyze(df: pd.DataFrame):
    x = df["i_a"].to_numpy()
    n = (len(x) // SPC) * SPC
    x = x[:n]
    spec = np.abs(np.fft.rfft(x)) * 2 / n
    cycles = n // SPC
    amp = {h: spec[h * cycles] for h in (1, 3, 5, 7)}
    rest = np.sqrt(sum(spec[h * cycles] ** 2 for h in range(2, 26)))
    thd = rest / amp[1] * 100
    for h, a in amp.items():
        print(f"h{h}: peak={a:.2f} A ({a / amp[1] * 100:.1f}% of fundamental)")
    print(f"THD (h2..h25) = {thd:.2f} %")
    return spec, cycles


def plot(df: pd.DataFrame, spec, cycles) -> None:
    fig, (a, b) = plt.subplots(2, 1, figsize=(9, 6.4))
    t = (df["timestamp"] - df["timestamp"].iloc[0]).dt.total_seconds() * 1e3
    m = t < 60
    a.plot(t[m], df["i_a"][m], color="#1f4e79")
    a.set_title("Synthetic distorted current (first 3 cycles)")
    a.set_xlabel("Time (ms)")
    a.set_ylabel("Current (A)")
    a.grid(True, alpha=0.3)
    hs = np.arange(1, 26)
    b.bar(hs, [spec[h * cycles] for h in hs], color="#8fb4d6")
    b.set_xlabel("Harmonic order")
    b.set_ylabel("Peak amplitude (A)")
    b.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG, dpi=120)
    print(f"wrote {FIG}")


def main() -> None:
    df = clean(pd.read_csv(DATA))
    spec, cycles = analyze(df)
    plot(df, spec, cycles)


if __name__ == "__main__":
    main()
