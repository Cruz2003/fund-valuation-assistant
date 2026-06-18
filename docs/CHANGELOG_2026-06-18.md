# 更新日志 2026-06-18

## 基金搜索优化

**问题**：首次搜索需调用 `ak.fund_name_em()` 下载全量基金列表（约 10,000+ 只），耗时 3-4 分钟。

**方案**：基金列表本地 CSV 持久化 + 手动刷新。

**改动**：
- `core/data_fetcher.py` — `_get_fund_list()` 改为从 `data/fund_list.csv` 读取，不存在则返回 None；新增 `refresh_fund_list()` 强制下载并保存 CSV；新增 `has_cache()` 检查缓存状态
- `core/fund_manager.py` — 新增 `has_fund_list_cache()`、`refresh_fund_list()` 透传方法
- `core/refresh_worker.py` — 新增 `RefreshFundListWorker` 后台下载线程
- `gui/dialogs.py` — 搜索对话框新增缓存状态提示和「🔄 刷新基金列表」按钮；无缓存时禁用搜索

**流程**：
1. 首次使用 → 提示"尚未下载基金列表" → 用户点击刷新 → 下载全量并持久化
2. 后续使用 → 直接读本地 CSV，搜索秒级响应
3. 搜索无结果 → 提示用户手动刷新，不自动下载

---

## 修复：添加/删除基金后全部显示"待刷新"

**问题**：添加或删除基金时调用 `load_fund_list()` 会从数据库重建 `_funds` 字典，导致内存中的估值缓存 `_valuation` 丢失。

**修复**：`gui/fund_list_panel.py` — `load_funds()` 在重建前保留已有基金的 `_valuation` 数据。

---

## 修复：昨日净值 (nav_yesterday) 固化不更新

**问题**：`nav_yesterday` 仅在添加基金时写入一次，之后永不更新。导致涨跌幅始终以添加当天的前一交易日为基准计算，随时间推移偏差越来越大。

**修复**：
- `core/data_fetcher.py` — 新增 `fetch_latest_nav()`，通过天天基金接口 (`fundgz.1234567.com.cn`) 快速获取最新已发布净值
- `core/fund_manager.py` — `refresh_fund()` 每次刷新前先调用 `fetch_latest_nav()` 更新 DB 中的 `nav_yesterday`

---

## 修复：估值历史数据 (valuation_log) 无限增长

**问题**：每次刷新估值都在 `valuation_log` 表追加一条记录，无清理机制。假设 5 只基金、5 分钟刷新一次，一天产生 1440 条记录，且历史数据从未在前端展示。

**修复**：`data/database.py` — `log_valuation()` 改为先删后插，每只基金仅保留最新一条估值记录。已有旧数据将在下次刷新时自动清理。
