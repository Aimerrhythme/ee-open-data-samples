# 数据集规范

## 命名
- `datasets/<slug>/`，脚本 `scripts/<slug>_generate.py`、`scripts/<slug>_plot.py`。

## 数据要求
- 格式：UTF-8 CSV，首行列名，英文 snake_case，单位写在数据集卡中（或列名后缀，如 `p_kw`）。
- 时间列：`timestamp`，ISO 8601（`2026-01-01T00:00:00`），注明时区或标注「无时区，相对时刻」。
- 体积：单文件建议 < 1 MB；更大数据只给下载脚本，不入仓。
- 合成数据须固定随机种子，保证可复现。
- 公开数据须写明原始 URL、许可证、获取日期；许可不允许再分发的**不入仓**。
- **禁止**：学生姓名、学号、成绩等任何 PII；未授权的企业/电站数据。

## 数据集卡 `README.md` 必填
1. 名称 / slug
2. 来源与生成方式
3. 许可
4. 规模与采样间隔
5. 列说明表
6. 教学用途（练习建议）
7. 已知局限 / 免责
8. 快速使用（pandas 读取 + 画图 3 行示例）

## 脚本要求
- 仅依赖 numpy / pandas / matplotlib（必要时 scipy）。
- 运行 `python scripts/<slug>_generate.py` 可在 `datasets/<slug>/` 重新生成 CSV。
