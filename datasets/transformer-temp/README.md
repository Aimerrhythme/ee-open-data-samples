# 变压器油温与负载

## 1. 名称 / slug
- 名称：变压器油温与负载（合成）
- slug：`transformer-temp`
- 路径：`datasets/transformer-temp/data.csv`

## 2. 来源与生成方式
合成数据，不是实测。脚本：`scripts/transformer-temp_generate.py`，随机种子 `42`。

负载为双峰日曲线（11 时、19 时）加周末下降与噪声；环境温度为日周期加缓慢漂移；顶层油温用一阶热模型：目标温升 `Δθ_u = 45·((K²R+1)/(R+1))^0.8`（K 为负载标幺值，R=5），时间常数 3 h，再加 N(0, 0.3²) 噪声。随后人为注入 6 个缺失值和 4 个 ±35~40 ℃ 尖峰供清洗练习。

## 3. 许可
MIT（见仓库 LICENSE），含教学声明。

## 4. 规模与采样间隔
336 行 = 7 天 × 48 点，间隔 30 min。

## 5. 列说明
| 列 | 单位 | 说明 |
|----|------|------|
| `timestamp` | 无时区，相对时刻 | ISO 8601；起点 2026-01-01 只是标签 |
| `load_pu` | pu | 负载标幺值（以额定容量为基准） |
| `ambient_c` | ℃ | 环境温度 |
| `top_oil_c` | ℃ | 顶层油温（含缺失与尖峰） |

## 6. 教学用途
- 缺失插值、尖峰检测（滚动中位数）并比较阈值。
- 拟合油温升与 K² 的关系，或用一阶模型估计时间常数。
- 讨论过载时的温升滞后。

## 7. 已知局限 / 免责
简化一阶模型，无冷却器分级、无热点温度、无太阳辐射；参数为示意，不是工程依据，也不是代写。

## 8. 快速使用
```python
import pandas as pd
df = pd.read_csv("datasets/transformer-temp/data.csv", parse_dates=["timestamp"])
df.plot(x="timestamp", y=["top_oil_c", "ambient_c"])
```
重新生成：`python scripts/transformer-temp_generate.py`；清洗并出图：`python scripts/transformer-temp_plot.py`。
