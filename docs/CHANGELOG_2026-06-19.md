# 更新日志 2026-06-19

## 韩国股票行情支持 + 市场自动学习

**问题**：部分 QDII 基金持仓包含韩国股票（如三星电子 005930、SK 海力士 000660），
其 6 位数字代码与 A 股重叠，被 `_detect_market` 误标为 "A" 或 "US" 市场，
导致行情获取失败，持仓表中涨跌幅和贡献度始终为空。

**数据源**：[FinanceDataReader](https://github.com/FinanceData/FinanceDataReader)
— 基于 KRX（韩国交易所）数据，免费、无需 API key。
韩国交易时间 8:00–14:30（北京时间），与 A 股有重叠。

**方案**：两级回退 + 自动学习

### 1. 行情获取回退 (`core/data_fetcher.py`)

```
fetch_stock_quotes("005930", "A")
  ├── _fetch_a_quotes  → 新浪返回异常格式 → 失败
  ├── 回退 _fetch_kr_quotes → FinanceDataReader → ✅
  └── 返回 {"005930": {...}, "_kr_resolved": ["005930"]}
```

- 新增 `_fetch_kr_quotes()` — 使用 FinanceDataReader，限制近 10 天数据避免拉全量
- `fetch_stock_quotes` 增加 `market="KR"` 直接通道
- 主市场获取失败的代码自动回退韩国，成功时附加 `_kr_resolved` 标记

### 2. 市场自动学习 (`core/fund_manager.py`)

```
refresh_fund()
  ├── quotes.pop("_kr_resolved")  → 提取学习标记
  └── db.update_holding_market(fund_id, "005930", "KR")
```

- 首次刷新后自动将 holdings 表 `market` 字段从 "A" 纠正为 "KR"
- 后续刷新直接走 `_fetch_kr_quotes`，零浪费回退

### 3. 数据库 (`data/database.py`)

- 新增 `update_holding_market(fund_id, stock_code, market)` 方法

### 4. 依赖 (`requirements.txt`)

- 新增 `finance-datareader==0.9.202`

### 架构扩展性

韩国和未来日本股票使用相同的「回退 + 学习」模式。
添加日本股票只需：
1. 实现 `_fetch_jp_quotes` 方法
2. `fetch_stock_quotes` 加 `market="JP"` 分支和 `_jp_resolved` 标记
3. `fund_manager` 加一行 `jp_resolved` 处理

（日本股票当前未实现——Yahoo Finance 全线 403、Stooq API 已变更、
东方财富/新浪不覆盖日本市场，暂无免费可靠数据源。）

---

## 韩国股票识别说明

韩国与 A 股代码均为 6 位数字，纯靠代码无法区分：

| 代码 | 实际市场 | `_detect_market` 误标为 |
|------|---------|------------------------|
| 005930 (三星电子) | 韩国 KRX | A |
| 000660 (SK 海力士) | 韩国 KRX | A |
| 035420 (NAVER)    | 韩国 KRX | US |

不做代码级识别，完全依赖「A 获取失败 → 回退韩国」机制，
首次自动纠正后持久化到 DB。
