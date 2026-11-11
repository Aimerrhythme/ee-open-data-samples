# 含谐波电流波形

## 1. 名称 / slug
- 名称：含谐波电流波形（3/5/7 次，可算 THD）
- slug：`harmonic-waveform`
- 路径：`datasets/harmonic-waveform/data.csv`

## 2. 来源与生成方式
合成数据，不是实测。脚本：`scripts/harmonic-waveform_generate.py`，随机种子 `42`。

`i = 100·[sin(ωt) + 0.08 sin(3ωt+0.6) + 0.20 sin(5ωt−0.9) + 0.12 sin(7ωt+1.4)] + 噪声`（A），噪声为 N(0, 0.8²)。基波 50 Hz。

## 3. 许可
MIT（见仓库 LICENSE），含教学声明。

## 4. 规模与采样间隔
1280 行 = 10 个基波周期 × 128 点/周期，采样频率 6.4 kHz（间隔 156.25 µs）。

## 5. 列说明
| 列 | 单位 | 说明 |
|----|------|------|
| `timestamp` | 无时区，相对时刻 | ISO 8601，带微秒；起点 2026-01-01T00:00:00 只是标签 |
| `i_a` | A | 瞬时电流 |

## 6. 教学用途
- 用 FFT 估计各次谐波幅值，并算 THD。
- 改变截取长度（非整数周期）观察频谱泄漏。
- 比较手算 THD 与脚本输出。

## 7. 已知局限 / 免责
单相、稳态、谐波幅值固定，无间谐波和频率漂移；不是工程依据，也不是代写。

## 8. 快速使用
```python
import pandas as pd
df = pd.read_csv("datasets/harmonic-waveform/data.csv", parse_dates=["timestamp"])
df.iloc[:384].plot(x="timestamp", y="i_a")
```
重新生成：`python scripts/harmonic-waveform_generate.py`；清洗、FFT 与出图：`python scripts/harmonic-waveform_plot.py`。
