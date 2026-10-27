# 主题队列 · 数据小样

状态：`todo` 待做 / `doing` 进行中 / `done` 已完成。自动化按顺序取第一条 `todo`。

| # | slug | 主题 | 状态 | 备注 |
|---|------|------|------|------|
| 1 | `load-daily` | 典型日负荷曲线（居民/商业/工业） | done | 合成，15 min |
| 2 | `pv-daily` | 光伏日出力曲线（晴/多云/阴） | todo | 合成，含云扰动 |
| 3 | `wind-speed` | 风速序列 + Weibull 拟合 | todo | 合成 |
| 4 | `harmonic-waveform` | 含谐波电流波形 | todo | 3/5/7 次，可算 THD |
| 5 | `transformer-temp` | 变压器油温与负载 | todo | 合成 |
| 6 | `motor-start-current` | 电机启动电流波形 | todo | 合成 |
| 7 | `battery-soc` | 储能 SOC 充放电日曲线 | todo | 合成 |
| 8 | `ev-charging-load` | 电动汽车充电负荷 | todo | 合成 |
| 9 | `voltage-sag-events` | 电压暂降事件样本 | todo | 合成 |
| 10 | `temperature-load` | 气温-负荷相关样本 | todo | 合成，做回归 |
