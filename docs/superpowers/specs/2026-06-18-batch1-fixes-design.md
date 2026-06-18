# Batch 1 Fixes — Design Spec

**Date:** 2026-06-18
**Scope:** 高优先级 bug 修复 + 性能/工程基础

---

## 改动清单

| # | 文件 | 改动 | 类型 |
|---|------|------|------|
| 1 | `data_fetcher.py` | `_get_fund_meta` / `search_funds` 给 `ak.fund_name_em()` 加模块级缓存 | 性能 |
| 2 | `data_fetcher.py` | `fetch_fund_holdings` 年份从硬编码 `"2025"` 改为动态 `str(datetime.now().year)` | Bug |
| 3 | `scheduler.py` | `is_market_open` 加周末判断（`datetime.now().weekday()`）；US 跨午夜用 `config.MARKET_HOURS` 的 close 标记正确判断 | Bug |
| 4 | `scheduler.py` + `config.py` | `scheduler.py` 复用 `config.MARKET_HOURS`，移除硬编码；`config.py` 保持现有结构不变 | 重构 |
| 5 | 全局 `*.py` | `print()` → `logging.getLogger(__name__).warning/info/error` | 工程 |

---

## 1. 基金列表缓存

### 问题
`_get_fund_meta()` 和 `search_funds()` 每次调用都执行 `ak.fund_name_em()`，下载全量几千条基金数据，网络开销大。

### 方案
在模块级别维护 `_fund_list_cache: Optional[pd.DataFrame] = None`。首次调用 `_get_fund_list()` 时下载并存入缓存，后续直接复用。

```python
import pandas as pd

_fund_list_cache: Optional[pd.DataFrame] = None

def _get_fund_list(self, force: bool = False) -> Optional[pd.DataFrame]:
    global _fund_list_cache
    if _fund_list_cache is not None and not force:
        return _fund_list_cache
    df = ak.fund_name_em()
    if df is not None and not df.empty:
        _fund_list_cache = df
    return df
```

`_get_fund_meta` 和 `search_funds` 改为调用 `self._get_fund_list()` 而非 `ak.fund_name_em()`。

不需要 TTL 过期 — 基金列表一天内不变。如需强制刷新，调用方传 `force=True`。

---

## 2. 动态年份

### 问题
`fetch_fund_holdings` 硬编码 `date="2025"`，现在已是 2026 年。

### 方案
改为 `str(datetime.now().year)`。import 文件顶部已有的 `datetime` 即可。

```python
from datetime import datetime
# ...
current_year = str(datetime.now().year)
df = ak.fund_portfolio_hold_em(symbol=code, date=current_year)
```

---

## 3. 周末判断

### 问题
`is_market_open()` 只判断时刻，不判断是否周末。周六凌晨 1 点会被判断为 "美股开盘中"。

### 方案
在函数开头加周末守卫：

```python
now = datetime.now()
if now.weekday() >= 5:  # Saturday=5, Sunday=6
    return False
```

---

## 4. 复用 config.MARKET_HOURS

### 问题
`scheduler.py` 中硬编码了 A/HK/US 的交易时间，与 `config.py` 中的 `MARKET_HOURS` 重复。

### 方案
`scheduler.py` 的 `is_market_open` 不再硬编码时间，改为从 `config.py` import `MARKET_HOURS`，解析其中的 `(open_hour, open_min)` / `(close_hour, close_min)` 并转换为分钟数比较。US 的 close 早于 open 表示跨午夜，沿用 `time_minutes >= open or time_minutes <= close` 逻辑。

### config.py 现有结构（无需改动）
```python
MARKET_HOURS = {
    "A":  {"open": (9, 30), "close": (15, 0)},
    "HK": {"open": (9, 30), "close": (16, 0)},
    "US": {"open": (21, 30), "close": (4, 0)},
}
```

`scheduler.py` 改为：
```python
from config import MARKET_HOURS

def is_market_open(market: str) -> bool:
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    hours = MARKET_HOURS.get(market)
    if not hours:
        return False
    open_minutes = hours["open"][0] * 60 + hours["open"][1]
    close_minutes = hours["close"][0] * 60 + hours["close"][1]
    time_minutes = now.hour * 60 + now.minute
    if close_minutes < open_minutes:  # crosses midnight (US)
        return time_minutes >= open_minutes or time_minutes <= close_minutes
    return open_minutes <= time_minutes <= close_minutes
```

---

## 5. print → logging

### 问题
所有错误和调试信息用 `print()`，GUI 应用下 stdout 不可见，无法追踪问题。

### 方案
每个文件顶部：
```python
import logging
logger = logging.getLogger(__name__)
```

替换规则：
- `print(f"Error ...")` → `logger.error(...)`
- `print(f"...")` (业务信息) → `logger.info(...)`

在 `main.py` 中配置 root logger：
```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
```

---

## 不改的范围

- `_retry` 函数：虽然未用但可作为公共 API 保留，后续可集成
- `models.py` dataclass：较大重构，留到 batch 2
- `fund_detail_panel.py` widget 引用：不影响功能，留到 batch 2
- 串行 HK/US 请求：性能改动较大，需更多设计，留到 batch 2
