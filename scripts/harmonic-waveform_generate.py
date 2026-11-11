"""生成含 3/5/7 次谐波的单相电流波形（合成），写入 datasets/harmonic-waveform/data.csv。"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "datasets" / "harmonic-waveform" / "data.csv"

F0 = 50.0            # 基波频率 Hz
SAMPLES_PER_CYCLE = 128
CYCLES = 10
SEED = 42
# 次数: (相对基波幅值, 相位 rad)
HARMONICS = {1: (1.0, 0.0), 3: (0.08, 0.6), 5: (0.20, -0.9), 7: (0.12, 1.4)}
I1_PEAK_A = 100.0
NOISE_A = 0.8


def main() -> None:
    rng = np.random.default_rng(SEED)
    n = SAMPLES_PER_CYCLE * CYCLES
    fs = F0 * SAMPLES_PER_CYCLE
    t = np.arange(n) / fs
    i = np.zeros(n)
    for h, (amp, ph) in HARMONICS.items():
        i += I1_PEAK_A * amp * np.sin(2 * np.pi * h * F0 * t + ph)
    i += rng.normal(0.0, NOISE_A, n)
    ts = pd.Timestamp("2026-01-01T00:00:00") + pd.to_timedelta(np.round(t * 1e6).astype(int), unit="us")
    df = pd.DataFrame({
        "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S.%f"),
        "i_a": np.round(i, 3),
    })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"wrote {OUT} rows={len(df)}")


if __name__ == "__main__":
    main()
