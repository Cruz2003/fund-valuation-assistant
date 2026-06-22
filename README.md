# 基金实时估值助手

基于 Python + PySide6 的桌面端基金实时估值跟踪工具。通过获取基金持仓与股票实时行情，估算基金净值的实时变化，支持 A 股、港股、美股、韩国市场。

## 功能特性

- **实时估值** — 根据基金最新持仓和股票实时行情，估算基金净值变化
- **多市场支持** — A 股 / 港股 / 美股 / 韩国市场行情自动识别与获取
- **估值图表** — 历史估值曲线可视化，直观跟踪净值走势
- **波动预警** — 可配置估值变动阈值，超限自动提醒
- **定时刷新** — 默认每 5 分钟自动刷新估值（可自定义）
- **基金搜索** — 通过关键词或基金代码搜索并添加跟踪
- **持仓明细** — 展示每只重仓股对净值的贡献度

## 技术栈

| 模块     | 技术                                       |
| -------- | ------------------------------------------ |
| GUI      | PySide6 (Qt for Python)                    |
| 数据源   | AkShare + 新浪实时行情 API                  |
| 图表     | Matplotlib                                 |
| 数据库   | SQLite（本地存储）                          |
| 行情获取 | 多源策略：实时优先，日线兜底                  |

## 项目结构

```
基金估值助手/
├── main.py                  # 应用入口
├── config.py                # 配置常量
├── scheduler.py             # 定时刷新调度器
├── core/
│   ├── data_fetcher.py      # 数据获取（基金信息、持仓、股票行情）
│   ├── fund_manager.py      # 基金业务编排层
│   ├── valuation_engine.py  # 净值估算引擎
│   ├── alert_service.py     # 预警服务
│   └── refresh_worker.py    # 刷新工作线程
├── data/
│   ├── database.py          # SQLite 数据库操作
│   └── models.py            # 数据模型
├── gui/
│   ├── main_window.py       # 主窗口
│   ├── fund_list_panel.py   # 基金列表面板
│   ├── fund_detail_panel.py # 基金详情面板
│   ├── holding_table.py     # 持仓表格
│   ├── chart_panel.py       # 图表面板
│   └── dialogs.py           # 对话框
└── tests/
    └── test_data_fetcher.py
```

## 快速开始

### 环境要求

- Python 3.10+
- Windows / macOS / Linux

### 安装

```bash
# 克隆仓库
git clone https://github.com/Cruz2003/fund-valuation-assistant.git
cd fund-valuation-assistant

# 创建虚拟环境（推荐）
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 运行

```bash
python main.py
```

### 使用说明

1. 点击 **添加基金**，输入基金名称或代码搜索
2. 选中基金后添加到跟踪列表
3. 软件自动获取持仓并开始实时估值
4. 可在详情页查看每只重仓股的贡献度
5. 在设置中调整刷新间隔和预警阈值

## 数据说明

- **估值原理**：实时估值 = 昨日净值 × (1 + Σ(持仓权重 × 股票涨跌幅) / 100)
- **行情数据**：A 股 / 港股 / 美股 / 韩国市场使用新浪实时单股 API，非交易时段自动切换为日线数据
- **基金持仓**：通过 AkShare 获取最新季报/年报持仓数据，非实时

## 交易时间（北京时间）

| 市场 | 开盘 | 收盘 |
| ---- | ---- | ---- |
| A 股 | 09:30 | 15:00 |
| 港股 | 09:30 | 16:00 |
| 美股 | 21:30 | 04:00（次日） |

## License

MIT
