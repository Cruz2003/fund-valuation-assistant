import sqlite3
import os
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
            conn.execute(
                "INSERT INTO funds (code, name, fund_type, nav_yesterday) "
                "VALUES (?, ?, ?, ?)",
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
            # Replace any existing record — keep only the latest per fund
            conn.execute("DELETE FROM valuation_log WHERE fund_id = ?", (fund_id,))
            conn.execute(
                "INSERT INTO valuation_log (fund_id, estimated_nav, change_pct) "
                "VALUES (?, ?, ?)",
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
