# Fund Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a desktop fund NAV estimation app with PySide6 GUI, AkShare data, and SQLite persistence.

**Architecture:** Three-layer design — GUI (PySide6 widgets), core business logic (fetch/calculate/alert), data (SQLite via custom DB class). Each layer communicates through well-defined interfaces.

**Tech Stack:** Python 3.12, PySide6, Pandas, NumPy, AkShare, SQLite, Matplotlib, requests, openpyxl

---

## Task 0: Environment Setup

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: Create conda environment**

```bash
conda create -n fund_tracker python=3.12 -y
```

- [ ] **Step 2: Activate environment and install dependencies**

```bash
conda activate fund_tracker
pip install pyside6 pandas numpy akshare requests matplotlib openpyxl
```

- [ ] **Step 3: Export requirements**

```bash
pip freeze > requirements.txt
```

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: set up Python 3.12 environment with dependencies"
```

---

## Task 1: Verify AkShare Data Fetching

**Files:**
- Create: `tests/test_data_fetcher.py`
- Create: `core/__init__.py`
- Create: `core/data_fetcher.py`

- [ ] **Step 1: Write verification test for AkShare fund info fetching**

```python
# tests/test_data_fetcher.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_fetcher import DataFetcher


def test_fetch_fund_info():
    """Test fetching fund basic info by code."""
    fetcher = DataFetcher()
    # 富国互联网科技 161028
    info = fetcher.fetch_fund_info("161028")
    assert info is not None
    assert "name" in info
    assert "code" in info
    print(f"Fund info: {info}")


def test_fetch_fund_holdings():
    """Test fetching top 10 holdings for a fund."""
    fetcher = DataFetcher()
    holdings = fetcher.fetch_fund_holdings("161028")
    assert holdings is not None
    assert len(holdings) > 0
    # Each holding should have stock_code, stock_name, weight
    for h in holdings:
        assert "stock_code" in h
        assert "stock_name" in h
        assert "weight" in h
    print(f"Holdings ({len(holdings)}):")
    for h in holdings:
        print(f"  {h['stock_code']} {h['stock_name']}: {h['weight']}%")


def test_fetch_stock_quotes():
    """Test fetching real-time quotes for A-share, HK, and US stocks."""
    fetcher = DataFetcher()
    # Test A-share
    a_quotes = fetcher.fetch_stock_quotes(["600519"], "A")
    print(f"A-share quotes: {a_quotes}")
    # Test HK
    hk_quotes = fetcher.fetch_stock_quotes(["00700"], "HK")
    print(f"HK quotes: {hk_quotes}")
    # Test US
    us_quotes = fetcher.fetch_stock_quotes(["AAPL"], "US")
    print(f"US quotes: {us_quotes}")


if __name__ == "__main__":
    test_fetch_fund_info()
    test_fetch_fund_holdings()
    test_fetch_stock_quotes()
```

- [ ] **Step 2: Run test to verify it fails (DataFetcher not implemented)**

```bash
cd "C:/Users/ZhuanZ（无密码）/Desktop/美股观测程序"
python tests/test_data_fetcher.py
```
Expected: ImportError or "DataFetcher not defined"

- [ ] **Step 3: Implement DataFetcher with AkShare**

```python
# core/__init__.py
```

```python
# core/data_fetcher.py
import akshare as ak
import pandas as pd
from typing import Optional


class DataFetcher:
    """Encapsulates all AkShare data fetching operations."""

    def fetch_fund_info(self, code: str) -> Optional[dict]:
        """
        Fetch fund basic info including name and latest NAV.
        Uses akshare fund_open_fund_info_em to get fund details.
        """
        try:
            # Get fund NAV history (most recent record has latest NAV)
            df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
            if df is None or df.empty:
                return None
            # The last row has the latest data
            latest = df.iloc[-1]
            # Also try to get fund name from fund list
            name = self._get_fund_name(code)
            return {
                "code": code,
                "name": name or code,
                "nav_yesterday": float(latest["单位净值"]),
                "nav_date": str(latest["净值日期"]),
            }
        except Exception as e:
            print(f"Error fetching fund info for {code}: {e}")
            return None

    def _get_fund_name(self, code: str) -> Optional[str]:
        """Get fund name from code using akshare fund list."""
        try:
            df = ak.fund_name_em()
            match = df[df["基金代码"] == code]
            if not match.empty:
                return match.iloc[0]["基金简称"]
        except Exception:
            pass
        return None

    def fetch_fund_holdings(self, code: str) -> Optional[list]:
        """
        Fetch top 10 holdings for a fund.
        Uses akshare fund_portfolio_hold_em.
        """
        try:
            df = ak.fund_portfolio_hold_em(symbol=code, date="2025")
            if df is None or df.empty:
                # Try without year filter
                df = ak.fund_portfolio_hold_em(symbol=code)
            if df is None or df.empty:
                return None

            holdings = []
            for _, row in df.iterrows():
                stock_name = row.get("股票名称", "")
                stock_code = row.get("股票代码", "")
                weight = row.get("占净值比例", row.get("持仓占比", 0))
                if stock_name and weight:
                    market = self._detect_market(stock_code)
                    holdings.append({
                        "stock_code": str(stock_code),
                        "stock_name": str(stock_name),
                        "weight": float(weight),
                        "market": market,
                    })
            return holdings[:10]  # Top 10 only
        except Exception as e:
            print(f"Error fetching holdings for {code}: {e}")
            return None

    def _detect_market(self, code: str) -> str:
        """Detect market from stock code pattern."""
        code = str(code)
        if code.startswith(("60", "00", "30", "688")):
            return "A"
        elif len(code) == 5 and code.isdigit():
            return "HK"
        else:
            return "US"

    def fetch_stock_quotes(self, codes: list, market: str) -> Optional[dict]:
        """
        Fetch real-time quotes for a list of stock codes.
        Returns dict: {code: {"price": float, "change_pct": float, "name": str}}
        """
        if not codes:
            return {}
        try:
            if market == "A":
                return self._fetch_a_quotes(codes)
            elif market == "HK":
                return self._fetch_hk_quotes(codes)
            elif market == "US":
                return self._fetch_us_quotes(codes)
            else:
                return {}
        except Exception as e:
            print(f"Error fetching {market} quotes: {e}")
            return {}

    def _fetch_a_quotes(self, codes: list) -> dict:
        """Fetch A-share real-time quotes."""
        try:
            df = ak.stock_zh_a_spot_em()
            if df is None or df.empty:
                return {}
            result = {}
            for code in codes:
                clean_code = code.replace("SH", "").replace("SZ", "")
                match = df[df["代码"] == clean_code]
                if not match.empty:
                    row = match.iloc[0]
                    result[code] = {
                        "price": float(row["最新价"]),
                        "change_pct": float(row["涨跌幅"]),
                        "name": str(row["名称"]),
                    }
            return result
        except Exception as e:
            print(f"A-share quote error: {e}")
            return {}

    def _fetch_hk_quotes(self, codes: list) -> dict:
        """Fetch HK stock real-time quotes."""
        try:
            df = ak.stock_hk_spot_em()
            if df is None or df.empty:
                return {}
            result = {}
            for code in codes:
                clean_code = code.zfill(5)
                match = df[df["代码"] == clean_code]
                if not match.empty:
                    row = match.iloc[0]
                    result[code] = {
                        "price": float(row["最新价"]),
                        "change_pct": float(row["涨跌幅"]),
                        "name": str(row["名称"]),
                    }
            return result
        except Exception as e:
            print(f"HK quote error: {e}")
            return {}

    def _fetch_us_quotes(self, codes: list) -> dict:
        """Fetch US stock real-time quotes."""
        try:
            df = ak.stock_us_spot_em()
            if df is None or df.empty:
                return {}
            result = {}
            for code in codes:
                match = df[df["代码"] == code]
                if not match.empty:
                    row = match.iloc[0]
                    result[code] = {
                        "price": float(row["最新价"]),
                        "change_pct": float(row["涨跌幅"]),
                        "name": str(row["名称"]),
                    }
            return result
        except Exception as e:
            print(f"US quote error: {e}")
            return {}

    def search_funds(self, keyword: str) -> Optional[list]:
        """
        Search funds by keyword (code or name).
        Returns list of dicts: [{code, name, fund_type}]
        """
        try:
            df = ak.fund_name_em()
            if df is None or df.empty:
                return None
            # Search by code or name
            mask = df["基金代码"].str.contains(keyword, na=False) | \
                   df["基金简称"].str.contains(keyword, na=False)
            matches = df[mask].head(20)
            results = []
            for _, row in matches.iterrows():
                results.append({
                    "code": str(row["基金代码"]),
                    "name": str(row["基金简称"]),
                    "fund_type": str(row.get("基金类型", "")),
                })
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return None
```

- [ ] **Step 4: Run tests to verify data fetching works**

```bash
cd "C:/Users/ZhuanZ（无密码）/Desktop/美股观测程序"
python tests/test_data_fetcher.py
```
Expected: Fund info, holdings, stock quotes printed. Note any API changes needed.

- [ ] **Step 5: Document any API adjustments needed and commit**

```bash
git add core/ tests/ requirements.txt
git commit -m "feat: implement DataFetcher with AkShare integration"
```

---

## Task 2: Database Layer

**Files:**
- Create: `data/__init__.py`
- Create: `data/models.py`
- Create: `data/database.py`
- Create: `tests/test_database.py`

- [ ] **Step 1: Write test for database operations**

```python
# tests/test_database.py
import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import Database


def test_create_tables():
    """Test that database tables are created correctly."""
    db_path = os.path.join(tempfile.gettempdir(), "test_fund_tracker.db")
    db = Database(db_path)
    # Tables should exist
    tables = db.get_tables()
    assert "funds" in tables
    assert "holdings" in tables
    assert "valuation_log" in tables
    assert "settings" in tables
    print("Tables created:", tables)


def test_fund_crud():
    """Test fund CRUD operations."""
    db_path = os.path.join(tempfile.gettempdir(), "test_fund_tracker.db")
    db = Database(db_path)

    # Create
    fund = db.add_fund(
        code="161028",
        name="富国互联网科技",
        fund_type="股票型",
        nav_yesterday=1.258
    )
    assert fund["id"] is not None
    assert fund["code"] == "161028"

    # Read
    funds = db.get_all_funds()
    assert len(funds) == 1
    assert funds[0]["name"] == "富国互联网科技"

    # Read by code
    f = db.get_fund_by_code("161028")
    assert f["nav_yesterday"] == 1.258

    # Update
    db.update_fund_nav(fund["id"], 1.271)
    f = db.get_fund_by_code("161028")
    assert f["nav_yesterday"] == 1.271

    # Delete
    db.delete_fund(fund["id"])
    funds = db.get_all_funds()
    assert len(funds) == 0

    print("Fund CRUD: PASS")


def test_holding_crud():
    """Test holding operations."""
    db_path = os.path.join(tempfile.gettempdir(), "test_fund_tracker.db")
    db = Database(db_path)

    fund = db.add_fund(code="005827", name="易方达蓝筹精选",
                       fund_type="混合型", nav_yesterday=2.345)

    # Add holdings
    db.replace_holdings(fund["id"], [
        {"stock_code": "600519", "stock_name": "贵州茅台", "market": "A", "weight": 9.5},
        {"stock_code": "00700", "stock_name": "腾讯控股", "market": "HK", "weight": 8.2},
    ])

    holdings = db.get_holdings(fund["id"])
    assert len(holdings) == 2
    assert holdings[0]["stock_name"] == "贵州茅台"

    # Replace (update)
    db.replace_holdings(fund["id"], [
        {"stock_code": "600519", "stock_name": "贵州茅台", "market": "A", "weight": 10.0},
    ])
    holdings = db.get_holdings(fund["id"])
    assert len(holdings) == 1

    print("Holding CRUD: PASS")


def test_settings():
    """Test settings get/set."""
    db_path = os.path.join(tempfile.gettempdir(), "test_fund_tracker.db")
    db = Database(db_path)

    db.set_setting("alert_threshold", "2.0")
    val = db.get_setting("alert_threshold", "1.0")
    assert val == "2.0"

    # Default value
    val = db.get_setting("nonexistent", "default_val")
    assert val == "default_val"

    print("Settings: PASS")


def test_valuation_log():
    """Test valuation log writing and reading."""
    db_path = os.path.join(tempfile.gettempdir(), "test_fund_tracker.db")
    db = Database(db_path)

    fund = db.add_fund(code="110022", name="易方达消费",
                       fund_type="股票型", nav_yesterday=3.456)

    db.log_valuation(fund["id"], 3.512, 1.62)
    db.log_valuation(fund["id"], 3.489, -0.95)

    logs = db.get_valuation_history(fund["id"], limit=10)
    assert len(logs) == 2
    assert logs[0]["estimated_nav"] == 3.512
    assert logs[1]["change_pct"] == -0.95

    print("Valuation log: PASS")


if __name__ == "__main__":
    test_create_tables()
    test_fund_crud()
    test_holding_crud()
    test_settings()
    test_valuation_log()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python tests/test_database.py
```
Expected: ImportError / ModuleNotFoundError

- [ ] **Step 3: Implement models.py**

```python
# data/__init__.py
```

```python
# data/models.py
"""Data model definitions used across the application."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Fund:
    """Represents a tracked fund."""
    id: Optional[int] = None
    code: str = ""
    name: str = ""
    fund_type: str = ""
    nav_yesterday: float = 0.0
    added_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "fund_type": self.fund_type,
            "nav_yesterday": self.nav_yesterday,
            "added_at": self.added_at,
        }

    @classmethod
    def from_row(cls, row: dict) -> "Fund":
        return cls(**row)


@dataclass
class Holding:
    """Represents a single stock holding within a fund."""
    id: Optional[int] = None
    fund_id: int = 0
    stock_code: str = ""
    stock_name: str = ""
    market: str = ""
    weight: float = 0.0
    updated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "fund_id": self.fund_id,
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "market": self.market,
            "weight": self.weight,
            "updated_at": self.updated_at,
        }


@dataclass
class ValuationRecord:
    """A single valuation snapshot."""
    id: Optional[int] = None
    fund_id: int = 0
    estimated_nav: float = 0.0
    change_pct: float = 0.0
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "fund_id": self.fund_id,
            "estimated_nav": self.estimated_nav,
            "change_pct": self.change_pct,
            "created_at": self.created_at,
        }
```

- [ ] **Step 4: Implement database.py**

```python
# data/database.py
import sqlite3
import os
from datetime import datetime
from typing import Optional


class Database:
    """SQLite database manager for Fund Tracker."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(db_dir, "fund_tracker.db")
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        """Get a new connection (each call creates a new one for thread safety)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        """Create tables if they don't exist."""
        conn = self._get_conn()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS funds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    fund_type TEXT DEFAULT '',
                    nav_yesterday REAL DEFAULT 0.0,
                    added_at TEXT DEFAULT (datetime('now', 'localtime'))
                );

                CREATE TABLE IF NOT EXISTS holdings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fund_id INTEGER NOT NULL,
                    stock_code TEXT NOT NULL,
                    stock_name TEXT NOT NULL,
                    market TEXT DEFAULT '',
                    weight REAL DEFAULT 0.0,
                    updated_at TEXT DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (fund_id) REFERENCES funds(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS valuation_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fund_id INTEGER NOT NULL,
                    estimated_nav REAL DEFAULT 0.0,
                    change_pct REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (fund_id) REFERENCES funds(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT DEFAULT ''
                );

                CREATE INDEX IF NOT EXISTS idx_holdings_fund ON holdings(fund_id);
                CREATE INDEX IF NOT EXISTS idx_valuation_fund ON valuation_log(fund_id);
            """)
            conn.commit()
        finally:
            conn.close()

    def get_tables(self) -> list:
        """Return list of table names (for testing)."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            return [row["name"] for row in cursor.fetchall()]
        finally:
            conn.close()

    # ---- Fund CRUD ----

    def add_fund(self, code: str, name: str, fund_type: str = "",
                 nav_yesterday: float = 0.0) -> dict:
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "INSERT INTO funds (code, name, fund_type, nav_yesterday) VALUES (?, ?, ?, ?)",
                (code, name, fund_type, nav_yesterday)
            )
            conn.commit()
            return self.get_fund_by_code(code)
        finally:
            conn.close()

    def get_all_funds(self) -> list:
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT * FROM funds ORDER BY added_at DESC"
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_fund_by_code(self, code: str) -> Optional[dict]:
        conn = self._get_conn()
        try:
            cursor = conn.execute("SELECT * FROM funds WHERE code = ?", (code,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_fund_by_id(self, fund_id: int) -> Optional[dict]:
        conn = self._get_conn()
        try:
            cursor = conn.execute("SELECT * FROM funds WHERE id = ?", (fund_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def update_fund_nav(self, fund_id: int, nav: float):
        conn = self._get_conn()
        try:
            conn.execute(
                "UPDATE funds SET nav_yesterday = ? WHERE id = ?",
                (nav, fund_id)
            )
            conn.commit()
        finally:
            conn.close()

    def delete_fund(self, fund_id: int):
        conn = self._get_conn()
        try:
            conn.execute("DELETE FROM funds WHERE id = ?", (fund_id,))
            conn.commit()
        finally:
            conn.close()

    # ---- Holdings ----

    def replace_holdings(self, fund_id: int, holdings: list):
        """Delete old holdings for fund and insert new ones."""
        conn = self._get_conn()
        try:
            conn.execute("DELETE FROM holdings WHERE fund_id = ?", (fund_id,))
            for h in holdings:
                conn.execute(
                    "INSERT INTO holdings (fund_id, stock_code, stock_name, market, weight) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (fund_id, h["stock_code"], h["stock_name"],
                     h.get("market", ""), h.get("weight", 0.0))
                )
            conn.commit()
        finally:
            conn.close()

    def get_holdings(self, fund_id: int) -> list:
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT * FROM holdings WHERE fund_id = ? ORDER BY weight DESC",
                (fund_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    # ---- Valuation Log ----

    def log_valuation(self, fund_id: int, estimated_nav: float, change_pct: float):
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO valuation_log (fund_id, estimated_nav, change_pct) VALUES (?, ?, ?)",
                (fund_id, estimated_nav, change_pct)
            )
            conn.commit()
        finally:
            conn.close()

    def get_valuation_history(self, fund_id: int, limit: int = 50) -> list:
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT * FROM valuation_log WHERE fund_id = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (fund_id, limit)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    # ---- Settings ----

    def set_setting(self, key: str, value: str):
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
            conn.commit()
        finally:
            conn.close()

    def get_setting(self, key: str, default: str = "") -> str:
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            )
            row = cursor.fetchone()
            return row["value"] if row else default
        finally:
            conn.close()

    def get_all_stock_codes(self) -> list:
        """Get all unique stock codes across all funds (for batch quote fetching)."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT DISTINCT stock_code, market FROM holdings"
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
```

- [ ] **Step 5: Run tests to verify database layer works**

```bash
cd "C:/Users/ZhuanZ（无密码）/Desktop/美股观测程序"
python tests/test_database.py
```
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add data/ tests/
git commit -m "feat: implement SQLite database layer with full CRUD"
```

---

## Task 3: Valuation Engine

**Files:**
- Create: `core/valuation_engine.py`
- Create: `tests/test_valuation_engine.py`

- [ ] **Step 1: Write test for valuation engine**

```python
# tests/test_valuation_engine.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.valuation_engine import ValuationEngine


def test_calculate_valuation():
    """Test valuation calculation with known data."""
    engine = ValuationEngine()

    # Fund with yesterday NAV 1.258
    nav_yesterday = 1.258

    # Holdings: stock weights (as percentage of NAV)
    holdings = [
        {"stock_code": "00700", "stock_name": "腾讯控股", "market": "HK", "weight": 10.0},
        {"stock_code": "09988", "stock_name": "阿里巴巴", "market": "HK", "weight": 5.0},
        {"stock_code": "01810", "stock_name": "小米集团", "market": "HK", "weight": 6.0},
        {"stock_code": "03690", "stock_name": "美团", "market": "HK", "weight": 3.0},
    ]

    # Stock quotes: price and change_pct
    quotes = {
        "00700": {"price": 380.0, "change_pct": 2.1, "name": "腾讯控股"},
        "09988": {"price": 85.0, "change_pct": 1.3, "name": "阿里巴巴"},
        "01810": {"price": 18.0, "change_pct": 4.0, "name": "小米集团"},
        "03690": {"price": 120.0, "change_pct": -0.5, "name": "美团"},
    }

    result = engine.calculate(nav_yesterday, holdings, quotes)

    # Verify estimated NAV
    # weight_contributions:
    # 腾讯: 10% * 2.1% = 0.21%
    # 阿里: 5% * 1.3% = 0.065%
    # 小米: 6% * 4.0% = 0.24%
    # 美团: 3% * -0.5% = -0.015%
    # total_weighted_change = 0.21 + 0.065 + 0.24 + (-0.015) = 0.50%
    # estimated_nav = 1.258 * (1 + 0.50/100) = 1.258 * 1.005 = 1.26429
    expected_change = 0.21 + 0.065 + 0.24 - 0.015
    expected_nav = nav_yesterday * (1 + expected_change / 100)

    assert abs(result["estimated_nav"] - expected_nav) < 0.001
    assert abs(result["change_pct"] - expected_change) < 0.01
    assert len(result["contributions"]) == 4
    # Check contribution of Tencent
    tc = [c for c in result["contributions"] if c["stock_code"] == "00700"][0]
    assert abs(tc["contribution"] - 0.21) < 0.01
    # Check contribution of Meituan
    mt = [c for c in result["contributions"] if c["stock_code"] == "03690"][0]
    assert abs(tc["contribution"] - 0.21) < 0.01  # keep consistent

    print(f"Estimated NAV: {result['estimated_nav']:.4f}")
    print(f"Change: {result['change_pct']:.2f}%")
    print("Contributions:")
    for c in result["contributions"]:
        print(f"  {c['stock_name']}: {c['contribution']:+.2f}%")


def test_missing_quotes():
    """Test valuation when some stocks have no quote data."""
    engine = ValuationEngine()
    nav_yesterday = 1.0
    holdings = [
        {"stock_code": "A", "stock_name": "StockA", "market": "A", "weight": 5.0},
        {"stock_code": "B", "stock_name": "StockB", "market": "HK", "weight": 3.0},
    ]
    quotes = {
        "A": {"price": 10.0, "change_pct": 5.0, "name": "StockA"},
        # StockB has no quote
    }
    result = engine.calculate(nav_yesterday, holdings, quotes)
    # Only StockA should contribute
    expected_change = 5.0 * 5.0 / 100  # 0.25%
    assert abs(result["change_pct"] - 0.25) < 0.01
    assert len(result["contributions"]) == 1
    print("Missing quotes test: PASS")


if __name__ == "__main__":
    test_calculate_valuation()
    test_missing_quotes()
    print("All valuation engine tests passed!")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python tests/test_valuation_engine.py
```
Expected: ImportError

- [ ] **Step 3: Implement valuation engine**

```python
# core/valuation_engine.py
class ValuationEngine:
    """Calculates real-time fund NAV estimates from holdings and stock quotes."""

    def calculate(self, nav_yesterday: float, holdings: list,
                  quotes: dict) -> dict:
        """
        Calculate estimated NAV and each stock's contribution.

        Args:
            nav_yesterday: Yesterday's fund NAV
            holdings: List of dicts [{stock_code, stock_name, market, weight}]
                      weight is percentage (e.g., 10.0 means 10%)
            quotes: Dict {stock_code: {price, change_pct, name}}
                    change_pct is percentage (e.g., 2.1 means +2.1%)

        Returns:
            {estimated_nav, change_pct, contributions: [{stock_code, stock_name,
              weight, change_pct, contribution}]}
        """
        contributions = []
        total_weighted_change = 0.0

        for h in holdings:
            code = h["stock_code"]
            weight = h.get("weight", 0.0)

            quote = quotes.get(code)
            if quote is None:
                # Stock not found in quotes — skip
                continue

            stock_change = quote.get("change_pct", 0.0)
            # Contribution = weight% × stock_change% = weight/100 × stock_change
            # But weight is already in percentage (e.g., 10 = 10%),
            # and stock_change is also percentage (e.g., 2.1 = 2.1%)
            # So contribution in percentage points = weight × stock_change / 100
            contribution = (weight * stock_change) / 100.0
            total_weighted_change += contribution

            contributions.append({
                "stock_code": code,
                "stock_name": h["stock_name"],
                "weight": weight,
                "stock_change_pct": stock_change,
                "contribution": round(contribution, 4),
            })

        # Sort by contribution descending
        contributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)

        change_pct = round(total_weighted_change, 4)
        estimated_nav = round(nav_yesterday * (1 + change_pct / 100), 4)

        return {
            "estimated_nav": estimated_nav,
            "change_pct": change_pct,
            "contributions": contributions,
        }
```

- [ ] **Step 4: Run tests to verify**

```bash
python tests/test_valuation_engine.py
```
Expected: All tests PASS with expected NAV values

- [ ] **Step 5: Commit**

```bash
git add core/valuation_engine.py tests/test_valuation_engine.py
git commit -m "feat: implement valuation engine with contribution analysis"
```

---

## Task 4: Fund Manager (Business Logic Orchestrator)

**Files:**
- Create: `core/fund_manager.py`
- Create: `tests/test_fund_manager.py`

- [ ] **Step 1: Write test for fund manager**

```python
# tests/test_fund_manager.py
import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.fund_manager import FundManager
from data.database import Database
from core.data_fetcher import DataFetcher
from core.valuation_engine import ValuationEngine


class MockDataFetcher:
    """Mock fetcher that returns known data without API calls."""

    def fetch_fund_info(self, code):
        return {
            "code": code,
            "name": f"Test Fund {code}",
            "nav_yesterday": 1.500,
            "nav_date": "2026-06-16",
        }

    def fetch_fund_holdings(self, code):
        return [
            {"stock_code": "600519", "stock_name": "贵州茅台", "market": "A", "weight": 10.0},
            {"stock_code": "00700", "stock_name": "腾讯控股", "market": "HK", "weight": 8.0},
        ]

    def fetch_stock_quotes(self, codes, market):
        quotes = {}
        if market == "A":
            quotes = {"600519": {"price": 1800.0, "change_pct": 1.5, "name": "贵州茅台"}}
        elif market == "HK":
            quotes = {"00700": {"price": 380.0, "change_pct": 2.0, "name": "腾讯控股"}}
        return quotes

    def search_funds(self, keyword):
        return [
            {"code": "161028", "name": "富国互联网科技", "fund_type": "股票型"},
            {"code": "161029", "name": "富国互联网科技C", "fund_type": "股票型"},
        ]


def test_add_fund():
    """Test adding a fund through the manager."""
    db_path = os.path.join(tempfile.gettempdir(), "test_fm.db")
    db = Database(db_path)
    fetcher = MockDataFetcher()
    engine = ValuationEngine()
    manager = FundManager(db, fetcher, engine)

    # Add a fund
    fund = manager.add_fund("161028")
    assert fund is not None
    assert fund["code"] == "161028"
    assert fund["name"] == "Test Fund 161028"
    assert fund["nav_yesterday"] == 1.500

    # Holdings should be fetched
    holdings = db.get_holdings(fund["id"])
    assert len(holdings) == 2
    print("Add fund: PASS")


def test_refresh_valuation():
    """Test refreshing valuation for all funds."""
    db_path = os.path.join(tempfile.gettempdir(), "test_fm.db")
    db = Database(db_path)
    fetcher = MockDataFetcher()
    engine = ValuationEngine()
    manager = FundManager(db, fetcher, engine)

    # Add fund first
    fund = manager.add_fund("161028")

    # Refresh
    results = manager.refresh_all()
    assert len(results) == 1
    r = results[0]
    assert "estimated_nav" in r
    assert "change_pct" in r
    assert len(r["contributions"]) == 2
    print(f"Refresh result: NAV={r['estimated_nav']:.4f}, Change={r['change_pct']:.2f}%")
    print("Refresh valuation: PASS")


def test_search_funds():
    """Test fund search."""
    db_path = os.path.join(tempfile.gettempdir(), "test_fm.db")
    db = Database(db_path)
    fetcher = MockDataFetcher()
    engine = ValuationEngine()
    manager = FundManager(db, fetcher, engine)

    results = manager.search_funds("富国")
    assert len(results) == 2
    print(f"Search results: {results}")


def test_delete_fund():
    """Test removing a fund."""
    db_path = os.path.join(tempfile.gettempdir(), "test_fm.db")
    db = Database(db_path)
    fetcher = MockDataFetcher()
    engine = ValuationEngine()
    manager = FundManager(db, fetcher, engine)

    fund = manager.add_fund("161028")
    assert len(db.get_all_funds()) == 1

    manager.delete_fund(fund["id"])
    assert len(db.get_all_funds()) == 0
    print("Delete fund: PASS")


if __name__ == "__main__":
    test_add_fund()
    test_refresh_valuation()
    test_search_funds()
    test_delete_fund()
    print("All fund manager tests passed!")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python tests/test_fund_manager.py
```
Expected: ImportError

- [ ] **Step 3: Implement fund manager**

```python
# core/fund_manager.py
from datetime import datetime
from typing import Optional
from data.database import Database
from core.data_fetcher import DataFetcher
from core.valuation_engine import ValuationEngine


class FundManager:
    """Orchestrates fund operations: add, remove, refresh valuations."""

    def __init__(self, db: Database, fetcher: DataFetcher,
                 engine: ValuationEngine):
        self.db = db
        self.fetcher = fetcher
        self.engine = engine

    def search_funds(self, keyword: str) -> list:
        """Search for funds by keyword."""
        return self.fetcher.search_funds(keyword) or []

    def add_fund(self, code: str) -> Optional[dict]:
        """Add a fund by code: fetch info + holdings, store in DB."""
        # Check if already added
        existing = self.db.get_fund_by_code(code)
        if existing:
            return existing

        # Fetch fund info
        info = self.fetcher.fetch_fund_info(code)
        if not info:
            return None

        # Add to DB
        fund = self.db.add_fund(
            code=code,
            name=info.get("name", code),
            fund_type=info.get("fund_type", ""),
            nav_yesterday=info.get("nav_yesterday", 0.0),
        )

        # Fetch and store holdings
        holdings = self.fetcher.fetch_fund_holdings(code)
        if holdings:
            self.db.replace_holdings(fund["id"], holdings)

        return fund

    def delete_fund(self, fund_id: int):
        """Remove a fund and its associated data."""
        self.db.delete_fund(fund_id)

    def refresh_fund(self, fund: dict) -> Optional[dict]:
        """Refresh a single fund's valuation."""
        fund_id = fund["id"]
        nav_yesterday = fund["nav_yesterday"]
        holdings = self.db.get_holdings(fund_id)

        if not holdings:
            return None

        # Group holdings by market for batch fetching
        markets = {}
        for h in holdings:
            m = h.get("market", "A")
            if m not in markets:
                markets[m] = []
            markets[m].append(h["stock_code"])

        # Fetch quotes for each market
        all_quotes = {}
        for market, codes in markets.items():
            quotes = self.fetcher.fetch_stock_quotes(codes, market)
            if quotes:
                all_quotes.update(quotes)

        # Calculate valuation
        result = self.engine.calculate(nav_yesterday, holdings, all_quotes)

        # Log to DB
        self.db.log_valuation(
            fund_id, result["estimated_nav"], result["change_pct"]
        )

        result["fund_id"] = fund_id
        result["fund_code"] = fund["code"]
        result["fund_name"] = fund["name"]
        result["nav_yesterday"] = nav_yesterday
        result["refreshed_at"] = datetime.now().strftime("%H:%M:%S")

        return result

    def refresh_all(self) -> list:
        """Refresh all tracked funds. Returns list of valuation results."""
        funds = self.db.get_all_funds()
        results = []
        for fund in funds:
            result = self.refresh_fund(fund)
            if result:
                results.append(result)
        return results

    def get_all_funds(self) -> list:
        """Get all tracked funds."""
        return self.db.get_all_funds()

    def get_fund_detail(self, fund_id: int) -> dict:
        """Get full fund detail including holdings and recent valuations."""
        fund = self.db.get_fund_by_id(fund_id)
        if not fund:
            return {}
        fund["holdings"] = self.db.get_holdings(fund_id)
        fund["valuation_history"] = self.db.get_valuation_history(fund_id, limit=20)
        return fund
```

- [ ] **Step 4: Run tests**

```bash
python tests/test_fund_manager.py
```
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add core/fund_manager.py tests/test_fund_manager.py
git commit -m "feat: implement FundManager orchestrating fetch + valuation + storage"
```

---

## Task 5: Alert Service and Config

**Files:**
- Create: `core/alert_service.py`
- Create: `config.py`
- Create: `tests/test_alert_service.py`

- [ ] **Step 1: Write test for alert service**

```python
# tests/test_alert_service.py
import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.alert_service import AlertService
from data.database import Database


def test_threshold_check():
    """Test alert threshold checking."""
    db_path = os.path.join(tempfile.gettempdir(), "test_alert.db")
    db = Database(db_path)
    service = AlertService(db)

    # Default threshold is 2.0%
    assert service.get_threshold() == 2.0

    # Check that 1.5% change does NOT trigger
    result = service.check("161028", "富国互联网科技", 1.5)
    assert result["triggered"] is False

    # Check that 2.5% change DOES trigger
    result = service.check("161028", "富国互联网科技", 2.5)
    assert result["triggered"] is True
    assert result["direction"] == "up"

    # Check that -3.0% change triggers (down)
    result = service.check("161028", "富国互联网科技", -3.0)
    assert result["triggered"] is True
    assert result["direction"] == "down"


def test_custom_threshold():
    """Test setting custom threshold."""
    db_path = os.path.join(tempfile.gettempdir(), "test_alert.db")
    db = Database(db_path)
    service = AlertService(db)

    service.set_threshold(3.0)
    assert service.get_threshold() == 3.0

    # 2.5% should not trigger with 3.0% threshold
    result = service.check("161028", "test", 2.5)
    assert result["triggered"] is False

    # 3.5% should trigger
    result = service.check("161028", "test", 3.5)
    assert result["triggered"] is True


if __name__ == "__main__":
    test_threshold_check()
    test_custom_threshold()
    print("All alert service tests passed!")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python tests/test_alert_service.py
```
Expected: ImportError

- [ ] **Step 3: Implement alert service**

```python
# core/alert_service.py
from data.database import Database


class AlertService:
    """Checks valuation changes against configurable threshold."""

    DEFAULT_THRESHOLD = 2.0  # percentage

    def __init__(self, db: Database):
        self.db = db
        self._ensure_default_threshold()

    def _ensure_default_threshold(self):
        val = self.db.get_setting("alert_threshold")
        if not val:
            self.db.set_setting("alert_threshold", str(self.DEFAULT_THRESHOLD))

    def get_threshold(self) -> float:
        val = self.db.get_setting("alert_threshold", str(self.DEFAULT_THRESHOLD))
        return float(val)

    def set_threshold(self, threshold: float):
        self.db.set_setting("alert_threshold", str(threshold))

    def check(self, fund_code: str, fund_name: str, change_pct: float) -> dict:
        """
        Check if a fund's change exceeds the threshold.
        Returns: {triggered: bool, direction: "up"|"down"|"none", fund_code, fund_name}
        """
        threshold = self.get_threshold()
        abs_change = abs(change_pct)

        if abs_change >= threshold:
            direction = "up" if change_pct > 0 else "down"
            return {
                "triggered": True,
                "direction": direction,
                "fund_code": fund_code,
                "fund_name": fund_name,
                "change_pct": change_pct,
                "threshold": threshold,
            }

        return {
            "triggered": False,
            "direction": "none",
            "fund_code": fund_code,
            "fund_name": fund_name,
        }
```

- [ ] **Step 4: Implement config.py**

```python
# config.py
"""Application-level configuration constants."""


# Default refresh interval in seconds (5 minutes)
DEFAULT_REFRESH_INTERVAL = 300

# Default alert threshold percentage
DEFAULT_ALERT_THRESHOLD = 2.0

# Database file name
DB_FILENAME = "fund_tracker.db"

# Trading hours (Beijing time, 24h format)
MARKET_HOURS = {
    "A": {"open": (9, 30), "close": (15, 0)},    # A-shares
    "HK": {"open": (9, 30), "close": (16, 0)},   # HK stocks
    "US": {"open": (21, 30), "close": (4, 0)},   # US stocks (crosses midnight)
}

# Application metadata
APP_NAME = "基金实时估值助手"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
```

- [ ] **Step 5: Run tests**

```bash
python tests/test_alert_service.py
```
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add core/alert_service.py config.py tests/test_alert_service.py
git commit -m "feat: implement alert service with configurable threshold"
```

---

## Task 6: Scheduler (Timed Refresh)

**Files:**
- Create: `scheduler.py`
- Create: `tests/test_scheduler.py`

- [ ] **Step 1: Write test for scheduler**

```python
# tests/test_scheduler.py
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scheduler import RefreshScheduler, is_market_open


def test_is_market_open():
    """Test market hours detection."""
    # A-share: open 9:30-15:00
    assert is_market_open("A", 10, 0) is True   # 10:00 AM
    assert is_market_open("A", 8, 0) is False   # 8:00 AM (before open)
    assert is_market_open("A", 16, 0) is False  # 4:00 PM (after close)

    # HK: open 9:30-16:00
    assert is_market_open("HK", 14, 0) is True
    assert is_market_open("HK", 17, 0) is False

    # US: open 21:30-4:00 next day (Beijing time)
    assert is_market_open("US", 22, 0) is True   # 10:00 PM
    assert is_market_open("US", 2, 0) is True    # 2:00 AM
    assert is_market_open("US", 10, 0) is False  # 10:00 AM (closed)

    print("Market hours tests: PASS")


def test_scheduler_interval():
    """Test scheduler interval configuration."""
    scheduler = RefreshScheduler()
    assert scheduler.get_interval() == 300  # default 5 min

    scheduler.set_interval(600)
    assert scheduler.get_interval() == 600

    print("Scheduler interval tests: PASS")


if __name__ == "__main__":
    test_is_market_open()
    test_scheduler_interval()
    print("All scheduler tests passed!")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python tests/test_scheduler.py
```
Expected: ImportError

- [ ] **Step 3: Implement scheduler**

```python
# scheduler.py
from datetime import datetime
from typing import Optional, Callable
from PySide6.QtCore import QTimer, QObject


def is_market_open(market: str, hour: int = None, minute: int = None) -> bool:
    """
    Check if a market is currently in trading hours (Beijing time).
    Can also check for a specific time (for testing).
    """
    if hour is None:
        now = datetime.now()
        hour = now.hour
        minute = now.minute

    time_minutes = hour * 60 + minute

    if market == "A":
        return 9 * 60 + 30 <= time_minutes <= 15 * 60
    elif market == "HK":
        return 9 * 60 + 30 <= time_minutes <= 16 * 60
    elif market == "US":
        # US market: 21:30 - 04:00 next day (Beijing time)
        us_open = 21 * 60 + 30
        us_close = 4 * 60
        # Crosses midnight
        return time_minutes >= us_open or time_minutes <= us_close
    return False


def get_market_status() -> dict:
    """Get current trading status for all three markets."""
    return {
        "A": is_market_open("A"),
        "HK": is_market_open("HK"),
        "US": is_market_open("US"),
    }


class RefreshScheduler(QObject):
    """Manages periodic refresh of fund valuations using QTimer."""

    def __init__(self, interval_seconds: int = 300):
        super().__init__()
        self._interval = interval_seconds
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._callback: Optional[Callable] = None
        self._last_refresh: Optional[datetime] = None
        self._countdown = interval_seconds

    def set_callback(self, callback: Callable):
        """Set the function to call on each refresh tick."""
        self._callback = callback

    def start(self):
        """Start the refresh timer."""
        self._countdown = self._interval
        self._timer.start(1000)  # Tick every second for countdown

    def stop(self):
        """Stop the refresh timer."""
        self._timer.stop()

    def _on_tick(self):
        """Called every second by QTimer."""
        self._countdown -= 1
        if self._countdown <= 0:
            self._countdown = self._interval
            self._last_refresh = datetime.now()
            if self._callback:
                self._callback()

    def get_countdown(self) -> int:
        """Get seconds until next refresh."""
        return max(0, self._countdown)

    def get_last_refresh_time(self) -> Optional[str]:
        """Get last refresh time as formatted string."""
        if self._last_refresh:
            return self._last_refresh.strftime("%H:%M:%S")
        return None

    def manual_refresh(self):
        """Trigger an immediate refresh."""
        self._countdown = 0  # Force next tick to refresh

    def set_interval(self, seconds: int):
        """Change the refresh interval."""
        self._interval = max(60, seconds)  # Minimum 1 minute
        self._countdown = min(self._countdown, self._interval)

    def get_interval(self) -> int:
        return self._interval
```

- [ ] **Step 4: Run tests**

```bash
python tests/test_scheduler.py
```
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add scheduler.py tests/test_scheduler.py
git commit -m "feat: implement refresh scheduler with market hours detection"
```

---

## Task 7: GUI — Main Window Shell

**Files:**
- Create: `gui/__init__.py`
- Create: `gui/main_window.py`
- Create: `main.py`

- [ ] **Step 1: Implement main window shell and entry point**

```python
# gui/__init__.py
```

```python
# gui/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QStatusBar, QLabel, QPushButton,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from config import APP_NAME, WINDOW_WIDTH, WINDOW_HEIGHT


class MainWindow(QMainWindow):
    """Main application window with left-right split layout."""

    def __init__(self, fund_manager, alert_service, scheduler):
        super().__init__()
        self.fund_manager = fund_manager
        self.alert_service = alert_service
        self.scheduler = scheduler

        self.setWindowTitle(APP_NAME)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(900, 600)

        self._setup_ui()
        self._setup_statusbar()
        self._connect_signals()

    def _setup_ui(self):
        """Build the main layout: left fund list | right detail panel."""
        central = QWidget()
        self.setCentralWidget(central)

        # Main horizontal splitter
        self.splitter = QSplitter(Qt.Horizontal)

        # Left panel — fund list
        from gui.fund_list_panel import FundListPanel
        self.fund_list = FundListPanel()
        self.splitter.addWidget(self.fund_list)

        # Right panel — fund detail
        from gui.fund_detail_panel import FundDetailPanel
        self.fund_detail = FundDetailPanel()
        self.splitter.addWidget(self.fund_detail)

        # Default split ratio (300px left, rest right)
        self.splitter.setSizes([300, 900])

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.splitter)

        # Apply stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QStatusBar {
                background-color: #e0e0e0;
                padding: 4px 8px;
                font-size: 12px;
            }
        """)

    def _setup_statusbar(self):
        """Set up status bar with refresh info and market status."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_refresh_label = QLabel("就绪")
        self.status_market_label = QLabel("A:-- HK:-- US:--")
        self.status_countdown_label = QLabel("")

        self.status_bar.addWidget(self.status_refresh_label, 1)
        self.status_bar.addWidget(self.status_market_label)
        self.status_bar.addPermanentWidget(self.status_countdown_label)

        # Timer to update countdown display
        self._countdown_timer = QTimer(self)
        self._countdown_timer.timeout.connect(self._update_statusbar)
        self._countdown_timer.start(1000)

    def _connect_signals(self):
        """Connect signals between panels and services."""
        # Fund list: when a fund is selected, show details
        self.fund_list.fund_selected.connect(self._on_fund_selected)
        # Fund list: add fund button
        self.fund_list.add_fund_requested.connect(self._on_add_fund)
        # Fund list: refresh button
        self.fund_list.refresh_requested.connect(self._on_manual_refresh)
        # Fund list: delete request
        self.fund_list.delete_fund_requested.connect(self._on_delete_fund)

        # Scheduler: periodic refresh
        self.scheduler.set_callback(self._on_scheduled_refresh)

    def _on_fund_selected(self, fund_data: dict):
        """Show fund detail when user clicks a fund in the list."""
        fund_id = fund_data["id"]
        detail = self.fund_manager.get_fund_detail(fund_id)
        self.fund_detail.display_fund(detail)

    def _on_add_fund(self, keyword: str):
        """Handle add fund request from search dialog."""
        from gui.dialogs import SearchFundDialog
        dialog = SearchFundDialog(self.fund_manager, self)
        if dialog.exec():
            selected_code = dialog.get_selected_code()
            if selected_code:
                fund = self.fund_manager.add_fund(selected_code)
                if fund:
                    self.load_fund_list()
                    # Auto-select newly added fund
                    self.fund_list.select_fund(fund)
        dialog.deleteLater()

    def _on_manual_refresh(self):
        """Handle manual refresh button click."""
        self._do_refresh()

    def _on_scheduled_refresh(self):
        """Handle scheduled auto-refresh."""
        self._do_refresh()

    def _do_refresh(self):
        """Execute full refresh for all funds."""
        self.status_refresh_label.setText("刷新中...")
        results = self.fund_manager.refresh_all()
        if results:
            self.fund_list.update_valuations(results)
            # Update detail if a fund is selected
            current = self.fund_list.get_selected_fund()
            if current:
                self._on_fund_selected(current)
            # Check alerts
            for r in results:
                alert = self.alert_service.check(
                    r["fund_code"], r["fund_name"], r["change_pct"]
                )
                if alert["triggered"]:
                    self.fund_list.highlight_fund(
                        r["fund_code"], alert["direction"]
                    )

        self.status_refresh_label.setText(
            f"最后刷新: {self.scheduler.get_last_refresh_time() or '刚刚'}"
        )

    def _on_delete_fund(self, fund_id: int):
        """Handle fund deletion."""
        self.fund_manager.delete_fund(fund_id)
        self.load_fund_list()
        self.fund_detail.clear()

    def _update_statusbar(self):
        """Update status bar countdown and market status."""
        from scheduler import get_market_status
        markets = get_market_status()
        status_text = (
            f"A:{'●' if markets['A'] else '○'} "
            f"HK:{'●' if markets['HK'] else '○'} "
            f"US:{'●' if markets['US'] else '○'}"
        )
        self.status_market_label.setText(status_text)
        remaining = self.scheduler.get_countdown()
        self.status_countdown_label.setText(
            f"下次刷新: {remaining // 60}:{remaining % 60:02d}"
        )

    def load_fund_list(self):
        """Reload fund list from database."""
        funds = self.fund_manager.get_all_funds()
        self.fund_list.load_funds(funds)

    def start(self):
        """Start the scheduler and show window."""
        self.load_fund_list()
        self.scheduler.start()
        self.show()
```

```python
# main.py
import sys
import os

# Ensure we can import from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from config import APP_NAME
from data.database import Database
from core.data_fetcher import DataFetcher
from core.valuation_engine import ValuationEngine
from core.fund_manager import FundManager
from core.alert_service import AlertService
from scheduler import RefreshScheduler
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")

    # Initialize layers
    db = Database()
    fetcher = DataFetcher()
    engine = ValuationEngine()
    fund_manager = FundManager(db, fetcher, engine)
    alert_service = AlertService(db)
    scheduler = RefreshScheduler(interval_seconds=300)

    # Create and show main window
    window = MainWindow(fund_manager, alert_service, scheduler)
    window.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add gui/ main.py
git commit -m "feat: implement main window shell and application entry point"
```

---

## Task 8: GUI — Fund List Panel

**Files:**
- Create: `gui/fund_list_panel.py`

- [ ] **Step 1: Implement fund list panel**

```python
# gui/fund_list_panel.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QLabel,
    QMessageBox,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QColor, QBrush


class FundListPanel(QWidget):
    """Left panel: fund search bar, add/refresh buttons, fund list."""

    fund_selected = Signal(dict)          # emit when user clicks a fund
    add_fund_requested = Signal(str)      # emit when user requests to add
    refresh_requested = Signal()          # emit for manual refresh
    delete_fund_requested = Signal(int)   # emit fund id to delete

    def __init__(self):
        super().__init__()
        self._funds = {}  # code -> fund dict
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Title
        title = QLabel("📊 我的基金")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Search + Add bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入代码或关键词搜索...")
        self.search_input.returnPressed.connect(self._on_add_clicked)
        search_layout.addWidget(self.search_input)

        self.add_btn = QPushButton("+添加")
        self.add_btn.clicked.connect(self._on_add_clicked)
        self.add_btn.setFixedWidth(70)
        search_layout.addWidget(self.add_btn)
        layout.addLayout(search_layout)

        # Refresh button
        self.refresh_btn = QPushButton("🔄 立即刷新")
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)
        layout.addWidget(self.refresh_btn)

        # Fund list
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.list_widget)

        # Style
        self.setStyleSheet("""
            FundListPanel {
                background-color: #ffffff;
                border-right: 1px solid #ddd;
            }
            QLineEdit {
                padding: 6px 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f8f8f8;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
            }
            QPushButton#refresh_btn {
                background-color: #4CAF50;
                color: white;
                border: none;
            }
            QPushButton#refresh_btn:hover {
                background-color: #45a049;
            }
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1565c0;
            }
        """)
        self.refresh_btn.setObjectName("refresh_btn")

    def load_funds(self, funds: list):
        """Populate the list with funds from database."""
        self._funds = {}
        self.list_widget.clear()
        for fund in funds:
            self._funds[fund["code"]] = fund
        self._redraw_list()

    def update_valuations(self, results: list):
        """Update list items with latest valuation data."""
        for r in results:
            code = r["fund_code"]
            if code in self._funds:
                self._funds[code]["_valuation"] = r
        self._redraw_list()

    def highlight_fund(self, fund_code: str, direction: str):
        """Highlight a fund item based on alert direction."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == fund_code:
                if direction == "up":
                    item.setBackground(QBrush(QColor("#ffcdd2")))  # Red for up
                elif direction == "down":
                    item.setBackground(QBrush(QColor("#c8e6c9")))  # Green for down
                break

    def _redraw_list(self):
        """Rebuild list items from current fund data."""
        self.list_widget.clear()
        for code, fund in self._funds.items():
            val = fund.get("_valuation")
            if val:
                change = val["change_pct"]
                sign = "+" if change >= 0 else ""
                text = f"{fund['name']}\n{fund['code']} | 估值: {val['estimated_nav']:.4f} ({sign}{change:.2f}%)"
            else:
                text = f"{fund['name']}\n{fund['code']} | 待刷新"

            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, code)

            # Color based on change
            if val:
                if val["change_pct"] > 0:
                    item.setForeground(QBrush(QColor("#d32f2f")))  # Red for rise
                elif val["change_pct"] < 0:
                    item.setForeground(QBrush(QColor("#388e3c")))  # Green for fall

            self.list_widget.addItem(item)

    def _on_item_clicked(self, item: QListWidgetItem):
        """Emit selected fund data when item clicked."""
        code = item.data(Qt.UserRole)
        if code in self._funds:
            self.fund_selected.emit(self._funds[code])

    def _on_add_clicked(self):
        """Emit add request with search keyword."""
        keyword = self.search_input.text().strip()
        if keyword:
            self.add_fund_requested.emit(keyword)
            self.search_input.clear()
        else:
            QMessageBox.information(self, "提示", "请输入基金代码或关键词")

    def _show_context_menu(self, pos):
        """Right-click menu for delete."""
        item = self.list_widget.itemAt(pos)
        if not item:
            return
        code = item.data(Qt.UserRole)
        if code not in self._funds:
            return
        fund = self._funds[code]

        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        delete_action = menu.addAction("删除")
        action = menu.exec(self.list_widget.mapToGlobal(pos))
        if action == delete_action:
            reply = QMessageBox.question(
                self, "确认删除",
                f"确定要删除 {fund['name']} ({code}) 吗？\n所有历史数据将被清除。",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.delete_fund_requested.emit(fund["id"])

    def get_selected_fund(self) -> dict:
        """Get the currently selected fund data."""
        current = self.list_widget.currentItem()
        if current:
            code = current.data(Qt.UserRole)
            return self._funds.get(code)
        return None

    def select_fund(self, fund: dict):
        """Programmatically select a fund in the list."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == fund["code"]:
                self.list_widget.setCurrentItem(item)
                break
```

- [ ] **Step 2: Commit**

```bash
git add gui/fund_list_panel.py
git commit -m "feat: implement fund list panel with search, add, delete, and highlight"
```

---

## Task 9: GUI — Fund Detail Panel

**Files:**
- Create: `gui/fund_detail_panel.py`

- [ ] **Step 1: Implement fund detail panel**

```python
# gui/fund_detail_panel.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QScrollArea, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class FundDetailPanel(QWidget):
    """Right panel: fund detail card, holdings table, charts."""

    def __init__(self):
        super().__init__()
        self._current_fund = None
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Scroll area for all content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setSpacing(12)

        # --- Fund info card ---
        self.info_card = QGroupBox("基金信息")
        self.info_layout = QVBoxLayout(self.info_card)
        self.info_layout.setSpacing(6)

        self.name_label = QLabel("请选择一只基金")
        name_font = QFont()
        name_font.setPointSize(16)
        name_font.setBold(True)
        self.name_label.setFont(name_font)
        self.info_layout.addWidget(self.name_label)

        self.code_label = QLabel("")
        self.info_layout.addWidget(self.code_label)

        self.nav_frame = QFrame()
        self.nav_frame.setStyleSheet("""
            QFrame#nav_frame {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        self.nav_frame.setObjectName("nav_frame")
        nav_layout = QHBoxLayout(self.nav_frame)
        nav_layout.setSpacing(20)

        # Yesterday NAV
        left = QVBoxLayout()
        nav_y_label = QLabel("昨日净值")
        nav_y_label.setStyleSheet("font-size: 12px; color: #888;")
        self.nav_yesterday_label = QLabel("--")
        self.nav_yesterday_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        left.addWidget(nav_y_label)
        left.addWidget(self.nav_yesterday_label)
        nav_layout.addLayout(left)

        # Estimated NAV
        mid = QVBoxLayout()
        est_label = QLabel("实时估值")
        est_label.setStyleSheet("font-size: 12px; color: #888;")
        self.estimated_nav_label = QLabel("--")
        self.estimated_nav_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        mid.addWidget(est_label)
        mid.addWidget(self.estimated_nav_label)
        nav_layout.addLayout(mid)

        # Change
        right = QVBoxLayout()
        chg_label = QLabel("预计涨幅")
        chg_label.setStyleSheet("font-size: 12px; color: #888;")
        self.change_label = QLabel("--")
        self.change_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        right.addWidget(chg_label)
        right.addWidget(self.change_label)
        nav_layout.addLayout(right)

        self.info_layout.addWidget(self.nav_frame)
        self.content_layout.addWidget(self.info_card)

        # --- Holdings table ---
        from gui.holding_table import HoldingTable
        self.holding_table = HoldingTable()
        self.content_layout.addWidget(self.holding_table)

        # --- Charts ---
        from gui.chart_panel import ChartPanel
        self.chart_panel = ChartPanel()
        self.content_layout.addWidget(self.chart_panel)

        self.content_layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        self.setStyleSheet("""
            FundDetailPanel {
                background-color: #ffffff;
            }
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
        """)

    def display_fund(self, fund_detail: dict):
        """Show fund detail information."""
        self._current_fund = fund_detail

        self.name_label.setText(fund_detail.get("name", ""))
        self.code_label.setText(f"代码: {fund_detail.get('code', '')} | "
                                f"类型: {fund_detail.get('fund_type', '')}")

        nav_y = fund_detail.get("nav_yesterday", 0)
        self.nav_yesterday_label.setText(f"{nav_y:.4f}" if nav_y else "--")

        # Check if we have latest valuation in history
        history = fund_detail.get("valuation_history", [])
        if history:
            latest = history[0]
            est_nav = latest["estimated_nav"]
            change = latest["change_pct"]
            self.estimated_nav_label.setText(f"{est_nav:.4f}")
            sign = "+" if change >= 0 else ""
            self.change_label.setText(f"{sign}{change:.2f}%")
            if change > 0:
                self.change_label.setStyleSheet(
                    "font-size: 24px; font-weight: bold; color: #d32f2f;"
                )
            elif change < 0:
                self.change_label.setStyleSheet(
                    "font-size: 24px; font-weight: bold; color: #388e3c;"
                )
            else:
                self.change_label.setStyleSheet(
                    "font-size: 24px; font-weight: bold; color: #333;"
                )
        else:
            self.estimated_nav_label.setText("--")
            self.change_label.setText("--")
            self.change_label.setStyleSheet(
                "font-size: 24px; font-weight: bold; color: #333;"
            )

        # Update holdings table
        holdings = fund_detail.get("holdings", [])
        self.holding_table.load_holdings(holdings)

        # Update charts
        self.chart_panel.update_data(holdings)

    def update_valuation(self, valuation: dict):
        """Update only the valuation display (called after refresh)."""
        est_nav = valuation.get("estimated_nav", 0)
        change = valuation.get("change_pct", 0)
        self.estimated_nav_label.setText(f"{est_nav:.4f}")
        sign = "+" if change >= 0 else ""
        self.change_label.setText(f"{sign}{change:.2f}%")

        if change > 0:
            self.change_label.setStyleSheet(
                "font-size: 24px; font-weight: bold; color: #d32f2f;"
            )
        elif change < 0:
            self.change_label.setStyleSheet(
                "font-size: 24px; font-weight: bold; color: #388e3c;"
            )

        # Update holdings table with contribution data
        contributions = valuation.get("contributions", [])
        self.holding_table.update_contributions(contributions)
        self.chart_panel.update_contributions(contributions)

    def clear(self):
        """Clear the detail panel."""
        self.name_label.setText("请选择一只基金")
        self.code_label.setText("")
        self.nav_yesterday_label.setText("--")
        self.estimated_nav_label.setText("--")
        self.change_label.setText("--")
        self.change_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #333;"
        )
        self.holding_table.clear()
        self.chart_panel.clear()
```

- [ ] **Step 2: Commit**

```bash
git add gui/fund_detail_panel.py
git commit -m "feat: implement fund detail panel with NAV card"
```

---

## Task 10: GUI — Holdings Table and Chart Panel

**Files:**
- Create: `gui/holding_table.py`
- Create: `gui/chart_panel.py`

- [ ] **Step 1: Implement holdings table**

```python
# gui/holding_table.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush


class HoldingTable(QGroupBox):
    """Table displaying fund holdings with contribution data."""

    COLUMNS = ["股票名称", "股票代码", "市场", "持仓占比(%)", "涨跌幅(%)", "贡献度(%)"]

    def __init__(self):
        super().__init__("持仓明细")
        self._holdings = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e0e0e0;
                gridline-color: #f0f0f0;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 6px;
                border: none;
                border-bottom: 2px solid #e0e0e0;
                font-weight: bold;
            }
        """)

        layout.addWidget(self.table)

    def load_holdings(self, holdings: list):
        """Load holdings into table (without contribution data)."""
        self._holdings = {}
        self.table.setRowCount(len(holdings))
        for i, h in enumerate(holdings):
            self._holdings[h["stock_code"]] = h
            self.table.setItem(i, 0, QTableWidgetItem(h.get("stock_name", "")))
            self.table.setItem(i, 1, QTableWidgetItem(h.get("stock_code", "")))
            market = h.get("market", "")
            market_name = {"A": "A股", "HK": "港股", "US": "美股"}.get(market, market)
            self.table.setItem(i, 2, QTableWidgetItem(market_name))
            self.table.setItem(i, 3, QTableWidgetItem(f"{h.get('weight', 0):.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem("--"))
            self.table.setItem(i, 5, QTableWidgetItem("--"))

    def update_contributions(self, contributions: list):
        """Update stock change and contribution columns."""
        contrib_map = {c["stock_code"]: c for c in contributions}
        for i in range(self.table.rowCount()):
            code_item = self.table.item(i, 1)
            if not code_item:
                continue
            code = code_item.text()
            contrib = contrib_map.get(code)
            if contrib:
                stock_change = contrib.get("stock_change_pct", 0)
                change_text = f"{stock_change:+.2f}"
                change_item = QTableWidgetItem(change_text)
                if stock_change > 0:
                    change_item.setForeground(QBrush(QColor("#d32f2f")))
                elif stock_change < 0:
                    change_item.setForeground(QBrush(QColor("#388e3c")))
                self.table.setItem(i, 4, change_item)

                contrib_val = contrib.get("contribution", 0)
                contrib_text = f"{contrib_val:+.2f}"
                contrib_item = QTableWidgetItem(contrib_text)
                if contrib_val > 0:
                    contrib_item.setForeground(QBrush(QColor("#d32f2f")))
                elif contrib_val < 0:
                    contrib_item.setForeground(QBrush(QColor("#388e3c")))
                self.table.setItem(i, 5, contrib_item)

    def clear(self):
        """Clear the table."""
        self.table.setRowCount(0)
        self._holdings = {}
```

- [ ] **Step 2: Implement chart panel**

```python
# gui/chart_panel.py
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox


class ChartPanel(QGroupBox):
    """Panel with contribution bar chart and holding weight pie chart."""

    def __init__(self):
        super().__init__("图表分析")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Matplotlib figure with 2 subplots
        self.figure = Figure(figsize=(8, 5), dpi=100)
        self.figure.set_tight_layout(True)
        self.ax_bar = self.figure.add_subplot(1, 2, 1)  # Contribution bar chart
        self.ax_pie = self.figure.add_subplot(1, 2, 2)  # Weight pie chart

        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)

    def update_data(self, holdings: list):
        """Update both charts with holdings data."""
        self.ax_bar.clear()
        self.ax_pie.clear()

        if not holdings:
            self.canvas.draw()
            return

        # Pie chart: weight distribution
        labels = [h.get("stock_name", "") for h in holdings]
        weights = [h.get("weight", 0) for h in holdings]
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
                   "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9"]

        wedges, texts, autotexts = self.ax_pie.pie(
            weights, labels=labels, autopct="%1.1f%%",
            colors=colors[:len(holdings)],
            startangle=90, pctdistance=0.85,
        )
        for t in autotexts:
            t.set_fontsize(8)
        for t in texts:
            t.set_fontsize(8)
        self.ax_pie.set_title("持仓占比", fontsize=10)

        # Bar chart: empty placeholder (filled by update_contributions)
        stocks = [h.get("stock_name", "") for h in holdings]
        self.ax_bar.barh(stocks, [0] * len(stocks), color="#e0e0e0")
        self.ax_bar.set_title("涨跌贡献度 (%)", fontsize=10)
        self.ax_bar.axvline(x=0, color="black", linewidth=0.5)

        self.canvas.draw()

    def update_contributions(self, contributions: list):
        """Update bar chart with contribution data."""
        self.ax_bar.clear()

        if not contributions:
            self.canvas.draw()
            return

        stocks = [c["stock_name"] for c in reversed(contributions)]
        values = [c["contribution"] for c in reversed(contributions)]
        colors = ["#d32f2f" if v >= 0 else "#388e3c" for v in values]

        bars = self.ax_bar.barh(stocks, values, color=colors, height=0.6)
        self.ax_bar.set_title("涨跌贡献度 (%)", fontsize=10)
        self.ax_bar.axvline(x=0, color="black", linewidth=0.5)

        # Add value labels on bars
        for bar, val in zip(bars, values):
            x_pos = bar.get_width()
            label_x = x_pos + 0.01 if x_pos >= 0 else x_pos - 0.01
            self.ax_bar.text(
                label_x, bar.get_y() + bar.get_height() / 2,
                f"{val:+.2f}", va="center",
                fontsize=9,
                ha="left" if x_pos >= 0 else "right",
            )

        self.canvas.draw()

    def clear(self):
        """Clear both charts."""
        self.ax_bar.clear()
        self.ax_pie.clear()
        self.canvas.draw()
```

- [ ] **Step 3: Commit**

```bash
git add gui/holding_table.py gui/chart_panel.py
git commit -m "feat: implement holdings table and chart panel with matplotlib"
```

---

## Task 11: GUI — Dialogs (Search, Settings)

**Files:**
- Create: `gui/dialogs.py`

- [ ] **Step 1: Implement search and settings dialogs**

```python
# gui/dialogs.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialogButtonBox, QSpinBox, QFormLayout,
)
from PySide6.QtCore import Qt


class SearchFundDialog(QDialog):
    """Dialog for searching and selecting a fund to add."""

    def __init__(self, fund_manager, parent=None):
        super().__init__(parent)
        self.fund_manager = fund_manager
        self._selected_code = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("添加基金")
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入基金代码或关键词...")
        self.search_input.returnPressed.connect(self._do_search)
        search_layout.addWidget(self.search_input)
        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self._do_search)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["基金代码", "基金名称", "类型"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.verticalHeader().setVisible(False)
        layout.addWidget(self.results_table)

        # Status label
        self.status_label = QLabel("请输入关键词搜索")
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _do_search(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            return

        self.status_label.setText("搜索中...")
        results = self.fund_manager.search_funds(keyword)

        self.results_table.setRowCount(0)
        if not results:
            self.status_label.setText("未找到匹配的基金")
            return

        self.status_label.setText(f"找到 {len(results)} 个结果")
        for r in results:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(r["code"]))
            self.results_table.setItem(row, 1, QTableWidgetItem(r["name"]))
            self.results_table.setItem(row, 2, QTableWidgetItem(r.get("fund_type", "")))

    def _on_accept(self):
        """Get selected fund code and accept."""
        current = self.results_table.currentRow()
        if current >= 0:
            self._selected_code = self.results_table.item(current, 0).text()
            self.accept()
        else:
            # Try direct code input
            keyword = self.search_input.text().strip()
            if keyword.isdigit() and len(keyword) == 6:
                self._selected_code = keyword
                self.accept()

    def get_selected_code(self):
        return self._selected_code


class SettingsDialog(QDialog):
    """Dialog for configuring app settings."""

    def __init__(self, alert_service, scheduler, parent=None):
        super().__init__(parent)
        self.alert_service = alert_service
        self.scheduler = scheduler
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("设置")
        self.resize(350, 200)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Alert threshold
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(1, 10)
        self.threshold_spin.setSuffix("%")
        current_threshold = int(self.alert_service.get_threshold())
        self.threshold_spin.setValue(current_threshold)
        form.addRow("提醒阈值:", self.threshold_spin)

        # Refresh interval
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setSuffix(" 分钟")
        self.interval_spin.setValue(self.scheduler.get_interval() // 60)
        form.addRow("刷新间隔:", self.interval_spin)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        self.alert_service.set_threshold(float(self.threshold_spin.value()))
        self.scheduler.set_interval(self.interval_spin.value() * 60)
        self.accept()
```

- [ ] **Step 2: Commit**

```bash
git add gui/dialogs.py
git commit -m "feat: implement search and settings dialogs"
```

---

## Task 12: Integration — Wire Everything Together

**Files:**
- Modify: `gui/main_window.py` (minor additions)

- [ ] **Step 1: Run the application and verify startup**

```bash
cd "C:/Users/ZhuanZ（无密码）/Desktop/美股观测程序"
python main.py
```
Expected: Window opens with left panel showing empty fund list, right panel showing "请选择一只基金", status bar showing market indicators.

- [ ] **Step 2: Test adding a fund**

1. Click "添加" or type a code in search box
2. Search dialog opens → search "161028"
3. Select fund and confirm
4. Fund appears in left list
5. Click the fund → detail panel shows fund info, holdings table, pie chart

- [ ] **Step 3: Test manual refresh**

1. Click "立即刷新" button
2. Status bar shows "刷新中..."
3. After completion: estimated NAV appears, contributions table and bar chart update
4. Status bar shows last refresh time

- [ ] **Step 4: Verify data persistence**

Close and re-open the application. Previously added funds should still appear.

- [ ] **Step 5: Test alert highlighting**

Add a fund and change the threshold to 0.1% in settings dialog. Trigger a refresh. Observe highlighting if change exceeds threshold.

- [ ] **Step 6: Test delete functionality**

Right-click a fund → delete → confirm. Fund disappears from list.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: complete integration and end-to-end verification"
```

---

## Task 13: Polish and Edge Cases

- [ ] **Step 1: Add network error handling to data_fetcher.py**

Add connection timeout and retry logic in DataFetcher.

- [ ] **Step 2: Add "no data" empty states to all panels**

- Fund list empty: show "暂无基金，请添加" placeholder
- Holdings empty: show "暂无持仓数据"
- Charts empty: show "暂无数据"

- [ ] **Step 3: Add loading indicators**

Show QProgressBar or spinner during data fetch operations.

- [ ] **Step 4: Validate edge cases**

- Adding duplicate fund code → should return existing
- Deleting selected fund → right panel clears
- All three markets closed at once → should handle gracefully (show last known data)
- Invalid fund code → show error message
- Network timeout → show error in status bar, don't crash

- [ ] **Step 5: Final commit and export requirements**

```bash
pip freeze > requirements.txt
git add requirements.txt
git commit -m "chore: finalize requirements and handle edge cases"
```
