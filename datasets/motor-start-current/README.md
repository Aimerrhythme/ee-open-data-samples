# 电机启动电流波形

## 1. 名称 / slug
- 名称：电机直接启动电流波形（合成）
- slug：`motor-start-current`
- 路径：`datasets/motor-start-current/data.csv`

## 2. 来源与生成方式
合成数据，不是实测。脚本：`scripts/motor-start-current_generate.py`，随机种子 `42`。

A 相电流 = 衰减有效值包络的 50 Hz 正弦 + 指数衰减直流偏置 + N(0, 0.4²) 噪声。额定电流有效值 20 A，启动倍数 6，包络时间常数 0.6 s，直流偏置时间常数 0.05 s，合闸时刻 0.2 s（此前电流为 0 加噪声）。随后人为注入 5 个缺失值和 3 个 −60/+80 A 尖峰供清洗练习。

## 3. 许可
MIT（见仓库 LICENSE），含教学声明。

## 4. 规模与采样间隔
3000 行 = 3 s × 1 kHz，间隔 1 ms（每周期 20 点）。

## 5. 列说明
| 列 | 单位 | 说明 |
|----|------|------|
| `timestamp` | 无时区，相对时刻 | ISO 8601 含毫秒；起点 2026-01-01 只是标签 |
| `i_a_a` | A | A 相瞬时电流（含缺失与尖峰） |

## 6. 教学用途
- 缺失插值、尖峰检测（滚动中位数）并比较阈值。
- 计算一周期滑动有效值，读出启动倍数与衰减时间常数。
- 观察直流偏置造成的前几个周期波形不对称。注意：一周期滑动有效值的最大值（约 180 A）高于 6×20=120 A，是因为直流偏置被计入有效值，可讨论如何滤除。

## 7. 已知局限 / 免责
简化模型：无转速—转矩耦合、无星三角/软启动、单相、无饱和；参数为示意，不是工程依据，也不是代写。

## 8. 快速使用
```python
import pandas as pd
df = pd.read_csv("datasets/motor-start-current/data.csv", parse_dates=["timestamp"])
df.plot(x="timestamp", y="i_a_a")
```
重新生成：`python scripts/motor-start-current_generate.py`；清洗并出图：`python scripts/motor-start-current_plot.py`。
