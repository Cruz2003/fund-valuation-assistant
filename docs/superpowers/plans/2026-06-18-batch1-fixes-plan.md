# Batch 1 Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 3 个 bug（硬编码年份、周末判断、配置重复）和 2 个工程基础问题（基金列表缓存、print→logging）

**Architecture:** 五项改动互相独立，各改不同文件。Task 3 同时改动 scheduler.py 和 config.py（配合移除重复）。Task 4 涉及多个文件但改动模式统一。其余 task 各自改一个文件。

**Tech Stack:** Python 3.12, AkShare, PySide6, sqlite3, logging

## Global Constraints

- 所有改动向后兼容，不改变现有 API 签名
- 基金列表缓存使用模块级变量，不引入新的依赖
- logging 使用标准库 `logging` 模块，不引入第三方日志库
- 每项改动后验证 `python main.py` 能正常启动（GUI 显示后手动关闭）

---

### Task 1: 基金列表缓存 — `data_fetcher.py`

**Files:**
- Modify: `core/data_fetcher.py`

**Interfaces:**
- Consumes: 无
- Produces: `_FUND_LIST_CACHE: Optional[pd.DataFrame]` (模块级)、`_get_fund_list(self, force=False) -> Optional[pd.DataFrame]`
- `_get_fund_meta()` 和 `search_funds()` 内部调用改为 `self._get_fund_list()`，外部调用者不变

- [ ] **Step 1: 在文件顶部 import 区之后添加模块级缓存变量和 `_get_fund_list` 方法**

在 `core/data_fetcher.py` 的 `import` 区（第 5 行 `from typing import Optional` 之后）加入：

```python
import pandas as pd
_fund_list_cache: Optional[pd.DataFrame] = None
```

- [ ] **Step 2: 在 `DataFetcher` 类中添加 `_get_fund_list` 方法**

在 `DataFetcher` 类的 `fetch_fund_info` 方法之前插入：

```python
    # Cache for the full fund name list (refreshed on force)
    _fund_list_cache: Optional[pd.DataFrame] = None

    def _get_fund_list(self, force: bool = False) -> Optional[pd.DataFrame]:
        """Get the full fund name list from AkShare, cached at module level."""
        if DataFetcher._fund_list_cache is not None and not force:
            return DataFetcher._fund_list_cache
        try:
            df = ak.fund_name_em()
            if df is not None and not df.empty:
                DataFetcher._fund_list_cache = df
            return df
        except Exception:
            return None
```

- [ ] **Step 3: 修改 `_get_fund_meta` 使用缓存的 `_get_fund_list`**

将 `_get_fund_meta` (第 41-54 行) 中的：
```python
df = ak.fund_name_em()
```
替换为：
```python
df = self._get_fund_list()
```

- [ ] **Step 4: 修改 `search_funds` 使用缓存的 `_get_fund_list`**

将 `search_funds` (第 191-210 行) 中的：
```python
df = ak.fund_name_em()
```
替换为：
```python
df = self._get_fund_list()
```

- [ ] **Step 5: 验证修改**

```bash
cd "C:\Users\ZhuanZ（无密码）\Desktop\美股观测程序"
python -c "from core.data_fetcher import DataFetcher; f = DataFetcher(); print(f._get_fund_meta('161028')); print('Cache size:', len(f._get_fund_list())); print(f.search_funds('互联')[:2])"
```
预期：两次调用 `_get_fund_meta` 不会重复下载，搜索结果正常返回。

- [ ] **Step 6: Commit**

```bash
git add core/data_fetcher.py
git commit -m "perf: add module-level cache for ak.fund_name_em() calls"
```

---

### Task 2: 动态年份 — `data_fetcher.py`

**Files:**
- Modify: `core/data_fetcher.py`

**Interfaces:**
- Consumes: 无外部依赖变化
- Produces: `fetch_fund_holdings` 的年份参数从硬编码变为 `str(datetime.now().year)`

- [ ] **Step 1: 在文件顶部加入 datetime import**

`data_fetcher.py` 顶部已有 `from typing import Optional`，检查是否已有 `from datetime import datetime`。若没有则添加：

```python
from datetime import datetime
```

- [ ] **Step 2: 修改 `fetch_fund_holdings` 中的硬编码年份**

将 `fetch_fund_holdings` (第 60-86 行) 中的：
```python
df = ak.fund_portfolio_hold_em(symbol=code, date="2025")
```
替换为：
```python
current_year = str(datetime.now().year)
df = ak.fund_portfolio_hold_em(symbol=code, date=current_year)
```

> **注意**: `datetime` 类如果之前未 import，需要在文件第 5 行附近 `from datetime import datetime` 添加。

- [ ] **Step 3: 验证**

```bash
cd "C:\Users\ZhuanZ（无密码）\Desktop\美股观测程序"
python -c "from core.data_fetcher import DataFetcher; f = DataFetcher(); h = f.fetch_fund_holdings('161028'); print(f'Holdings: {len(h) if h else 0}')"
```
预期：返回持仓数据（如果有的话），不会因年份 2025 失败。

- [ ] **Step 4: Commit**

```bash
git add core/data_fetcher.py
git commit -m "fix: use dynamic current year instead of hardcoded 2025 in fetch_fund_holdings"
```

---

### Task 3: 周末判断 + 复用 MARKET_HOURS — `scheduler.py`

**Files:**
- Modify: `scheduler.py`

**Interfaces:**
- Consumes: `config.MARKET_HOURS` dict
- Produces: `is_market_open(market: str) -> bool` 签名不变但增加周末判断；`get_market_status() -> dict` 不变
- 移除 `is_market_open` 的 `hour`/`minute` 参数（从未被外部传入，保持向后兼容用默认值 None 即可，或简化为无参数版本）

- [ ] **Step 1: 在 scheduler.py 顶部添加 import**

将 `scheduler.py` 顶部：
```python
from datetime import datetime
from typing import Optional, Callable
from PySide6.QtCore import QTimer, QObject
```
修改为：
```python
from datetime import datetime
from typing import Optional, Callable
from PySide6.QtCore import QTimer, QObject
from config import MARKET_HOURS
```

- [ ] **Step 2: 重写 `is_market_open` 函数**

将 `scheduler.py` 中的 `is_market_open` 函数 (第 6-23 行) 替换为：

```python
def is_market_open(market: str, hour: int = None, minute: int = None) -> bool:
    """Check if a market is currently in trading hours (Beijing time)."""
    if hour is None:
        now = datetime.now()
        # Skip weekends
        if now.weekday() >= 5:
            return False
        hour = now.hour
        minute = now.minute
    else:
        # If caller passes explicit hour/minute, trust them on the date
        pass

    hours = MARKET_HOURS.get(market)
    if not hours:
        return False

    open_minutes = hours["open"][0] * 60 + hours["open"][1]
    close_minutes = hours["close"][0] * 60 + hours["close"][1]
    time_minutes = hour * 60 + minute

    if close_minutes < open_minutes:
        # Crosses midnight (US market)
        return time_minutes >= open_minutes or time_minutes <= close_minutes
    else:
        return open_minutes <= time_minutes <= close_minutes
```

- [ ] **Step 3: 验证周末判断**

```bash
cd "C:\Users\ZhuanZ（无密码）\Desktop\美股观测程序"
python -c "
from scheduler import is_market_open, get_market_status
print('Market status:', get_market_status())
# 手动测试边界：
# 周末应该全部返回 False（用 weekday() 模拟验证）
from datetime import datetime
d = datetime(2026, 6, 20, 22, 0)  # Saturday 22:00
print('Saturday 22:00 US:', is_market_open('US', d.hour, d.minute))  # 应 True（但传了hour/min 跳过weekday检查——这是设计意图）
d2 = datetime(2026, 6, 22, 10, 0)  # Monday 10:00
print('Monday 10:00 A:', is_market_open('A', d2.hour, d2.minute))
print('Monday 10:00 HK:', is_market_open('HK', d2.hour, d2.minute))
"
```
预期：实际调用（不传 hour/minute）时周末返回 False。

- [ ] **Step 4: Commit**

```bash
git add scheduler.py
git commit -m "fix: add weekend check to is_market_open and reuse config.MARKET_HOURS"
```

---

### Task 4: print → logging — 全局

**Files:**
- Modify: `main.py` — 添加 `logging.basicConfig`
- Modify: `core/data_fetcher.py` — `print()` → `logger.error()`

> `core/fund_manager.py`, `core/valuation_engine.py`, `core/alert_service.py`, `gui/*.py`, `data/database.py` 检查后没有 print() 调用，无需修改。`tests/test_data_fetcher.py` 中的 print 是测试输出，保持不变。

- [ ] **Step 1: 在 main.py 中配置 logging**

在 `main.py` 的 import 区之后、函数定义之前（第 15 行之后）加入：

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
```

- [ ] **Step 2: 在 data_fetcher.py 中替换所有 print**

在 `core/data_fetcher.py` 顶部 import 区加入：

```python
import logging
logger = logging.getLogger(__name__)
```

然后替换文件中所有 `print()` 调用：

| 行 | 原代码 | 替换为 |
|----|--------|--------|
| `fetch_fund_info` (第 38 行) | `print(f"Error fetching fund info for {code}: {e}")` | `logger.error(f"Error fetching fund info for {code}: {e}")` |
| `fetch_fund_holdings` (第 85 行) | `print(f"Error fetching holdings for {code}: {e}")` | `logger.error(f"Error fetching holdings for {code}: {e}")` |
| `fetch_stock_quotes` (第 113 行) | `print(f"Error fetching {market} quotes: {e}")` | `logger.error(f"Error fetching {market} quotes: {e}")` |
| `_fetch_a_quotes` (第 142 行) | `print(f"A-share quote error: {e}")` | `logger.error(f"A-share quote error: {e}")` |
| `_fetch_hk_quotes` (第 165 行) | `print(f"HK quote error for {code}: {e}")` | `logger.error(f"HK quote error for {code}: {e}")` |
| `_fetch_us_quotes` (第 188 行) | `print(f"US quote error for {code}: {e}")` | `logger.error(f"US quote error for {code}: {e}")` |
| `search_funds` (第 209 行) | `print(f"Search error: {e}")` | `logger.error(f"Search error: {e}")` |

共 7 处替换。

- [ ] **Step 3: 验证**

```bash
cd "C:\Users\ZhuanZ（无密码）\Desktop\美股观测程序"
python -c "
import logging, sys
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s', handlers=[logging.StreamHandler(sys.stdout)])
from core.data_fetcher import DataFetcher
f = DataFetcher()
# 用无效代码触发错误日志
f.fetch_fund_info('999999')
print('--- If above shows [ERROR] log line, logging works ---')
"
```
预期：网络错误信息以标准 logging 格式输出到 stderr 而非 print 的 stdout。

- [ ] **Step 4: Commit**

```bash
git add main.py core/data_fetcher.py
git commit -m "refactor: replace print() with logging for all data_fetcher errors"
```

---

## Execution Order

Task 1 → 2 → 3 → 4（无依赖，但建议按顺序执行以便逐项验证）
