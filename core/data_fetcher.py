import logging
import akshare as ak
import time
import requests
import os
from typing import Optional
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)

import pandas as pd

# Path to local fund list cache
_FUND_LIST_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "fund_list.csv")


def _retry(func, *args, max_retries=2, delay=3, **kwargs):
    """Simple retry wrapper for flaky network calls."""
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt < max_retries:
                time.sleep(delay)
            else:
                raise e


class DataFetcher:
    """Encapsulates all AkShare data fetching operations."""

    def _get_fund_list(self) -> Optional[pd.DataFrame]:
        """Load fund list from local CSV cache. Returns None if cache missing."""
        try:
            if os.path.exists(_FUND_LIST_PATH):
                df = pd.read_csv(_FUND_LIST_PATH, dtype=str)
                if not df.empty:
                    return df
        except Exception as e:
            logger.error(f"Failed to load fund list cache: {e}")
        return None

    def refresh_fund_list(self) -> bool:
        """Force re-download the full fund list from AkShare and save to CSV."""
        try:
            df = ak.fund_name_em()
            if df is None or df.empty:
                return False
            os.makedirs(os.path.dirname(_FUND_LIST_PATH), exist_ok=True)
            df.to_csv(_FUND_LIST_PATH, index=False)
            logger.info(f"Fund list refreshed: {len(df)} funds saved to {_FUND_LIST_PATH}")
            return True
        except Exception as e:
            logger.error(f"Failed to refresh fund list: {e}")
            return False

    def has_cache(self) -> bool:
        """Check if local fund list cache file exists."""
        return os.path.exists(_FUND_LIST_PATH)

    def fetch_latest_nav(self, code: str) -> Optional[float]:
        """Quickly fetch the latest published NAV via Tiantian API.
        Returns the most recent closing NAV (typically yesterday's)."""
        try:
            import re
            url = f"https://fundgz.1234567.com.cn/js/{code}.js"
            r = requests.get(url, timeout=10)
            # jsonpgz({"dwjz":"2.4910",...});
            match = re.search(r'"dwjz":"([^"]+)"', r.text)
            if match:
                return float(match.group(1))
        except Exception as e:
            logger.error(f"Failed to fetch latest NAV for {code}: {e}")
        return None

    def fetch_fund_info(self, code: str) -> Optional[dict]:
        """Fetch fund basic info including name and latest NAV."""
        try:
            # Get fund NAV history (most recent record has latest NAV)
            df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
            if df is None or df.empty:
                return None
            latest = df.iloc[-1]
            meta = self._get_fund_meta(code)
            return {
                "code": code,
                "name": meta["name"] if meta else code,
                "fund_type": meta["fund_type"] if meta else "",
                "nav_yesterday": float(latest["单位净值"]),
                "nav_date": str(latest["净值日期"]),
            }
        except Exception as e:
            logger.error(f"Error fetching fund info for {code}: {e}")
            return None

    def _get_fund_meta(self, code: str) -> Optional[dict]:
        """Get fund name and type from the fund list."""
        try:
            df = self._get_fund_list()
            match = df[df["基金代码"] == code]
            if not match.empty:
                row = match.iloc[0]
                return {
                    "name": str(row["基金简称"]),
                    "fund_type": str(row.get("基金类型", "")),
                }
        except Exception:
            pass
        return None

    def _get_fund_name(self, code: str) -> Optional[str]:
        meta = self._get_fund_meta(code)
        return meta["name"] if meta else None

    def fetch_fund_holdings(self, code: str) -> Optional[list]:
        """Fetch top 10 holdings for a fund (latest quarter only)."""
        try:
            # Try latest year first, fall back to all years
            current_year = str(datetime.now().year)
            df = ak.fund_portfolio_hold_em(symbol=code, date=current_year)
            if df is None or df.empty:
                df = ak.fund_portfolio_hold_em(symbol=code)
            if df is None or df.empty:
                return None

            # Data spans multiple quarters — keep only the latest quarter
            if "季度" in df.columns:
                latest_quarter = sorted(df["季度"].unique(), reverse=True)[0]
                df = df[df["季度"] == latest_quarter]

            holdings = []
            for _, row in df.iterrows():
                stock_name = row.get("股票名称", "")
                stock_code = row.get("股票代码", "")
                weight = row.get("占净值比例", row.get("持仓占比", 0))
                if stock_name and weight:
                    market = self._detect_market(str(stock_code))
                    holdings.append({
                        "stock_code": str(stock_code),
                        "stock_name": str(stock_name),
                        "weight": float(weight),
                        "market": market,
                    })
            return holdings[:10]
        except Exception as e:
            logger.error(f"Error fetching holdings for {code}: {e}")
            return None

    def _detect_market(self, code: str) -> str:
        """Detect market from stock code pattern."""
        code = code.strip()
        if len(code) == 6 and code.isdigit() and code.startswith(("60", "00", "30", "688")):
            return "A"
        elif len(code) == 5 and code.isdigit():
            return "HK"
        else:
            return "US"

    def fetch_stock_quotes(self, codes: list, market: str) -> Optional[dict]:
        """Fetch real-time quotes for a list of stock codes.

        For codes whose primary market fetch fails, falls back to Korean
        market.  When the fallback succeeds, the resolved codes are noted
        in ``_kr_resolved`` so the caller can persist the correct market.
        """
        if not codes:
            return {}
        result = {}
        try:
            if market == "A":
                result = self._fetch_a_quotes(codes)
            elif market == "HK":
                result = self._fetch_hk_quotes(codes)
            elif market == "US":
                result = self._fetch_us_quotes(codes)
            elif market == "KR":
                result = self._fetch_kr_quotes(codes)
        except Exception as e:
            logger.error(f"Error fetching {market} quotes: {e}")

        # Fallback: try Korean market for any codes the primary fetch missed.
        # Codes already marked "KR" are fetched directly and won't reach here.
        unmatched = [c for c in codes if c not in result]
        if unmatched:
            kr_result = self._fetch_kr_quotes(unmatched)
            kr_hits = [c for c in unmatched if c in kr_result]
            if kr_hits:
                result["_kr_resolved"] = kr_hits
            result.update(kr_result)

        return result

    def _fetch_a_quotes(self, codes: list) -> dict:
        """Fetch A-share real-time quotes via Sina single-stock API.
        ~0.1s per stock, returns real-time price + change vs prev close."""
        result = {}
        for code in codes:
            try:
                # Map to Sina prefix format: sh600519, sz000001
                if code.startswith(("60", "688")):
                    symbol = "sh" + code
                elif code.startswith(("00", "30")):
                    symbol = "sz" + code
                else:
                    symbol = code
                url = f"http://hq.sinajs.cn/list={symbol}"
                r = requests.get(
                    url,
                    headers={"Referer": "https://finance.sina.com.cn"},
                    timeout=10,
                )
                # Format: var hq_str_sh600519="name,open,prev_close,price,..."
                fields = r.text.split('"')[1].split(",")
                name = fields[0]
                prev_close = float(fields[2])
                price = float(fields[3])
                change_pct = (price - prev_close) / prev_close * 100
                result[code] = {
                    "price": price,
                    "change_pct": round(change_pct, 2),
                    "name": name,
                }
            except Exception as e:
                logger.error(f"A-share quote error for {code}: {e}")
        return result

    def _fetch_hk_quotes(self, codes: list) -> dict:
        """Fetch HK stock quotes — Sina real-time first, daily fallback."""
        result = {}
        for code in codes:
            # 1. Try Sina real-time (hk00700)
            try:
                url = f"http://hq.sinajs.cn/list=hk{code}"
                r = requests.get(
                    url,
                    headers={"Referer": "https://finance.sina.com.cn"},
                    timeout=10,
                )
                fields = r.text.split('"')[1].split(",")
                name = fields[1]
                price = float(fields[6])
                prev_close = float(fields[3])
                if price > 0:
                    change_pct = (price - prev_close) / prev_close * 100
                    result[code] = {
                        "price": price,
                        "change_pct": round(change_pct, 2),
                        "name": name,
                    }
                    continue
            except Exception:
                pass

            # 2. Fallback: daily historical (yesterday's close)
            try:
                df = ak.stock_hk_daily(symbol=code, adjust="")
                if df is None or len(df) < 2:
                    continue
                latest = df.iloc[-1]
                prev = df.iloc[-2]
                close = float(latest["close"])
                prev_close = float(prev["close"])
                change_pct = (close - prev_close) / prev_close * 100
                result[code] = {
                    "price": close,
                    "change_pct": round(change_pct, 2),
                    "name": code,
                }
            except Exception as e:
                logger.error(f"HK quote error for {code}: {e}")
        return result

    def _fetch_us_quotes(self, codes: list) -> dict:
        """Fetch US stock quotes — Sina real-time first, daily fallback."""
        result = {}
        for code in codes:
            # 1. Try Sina real-time (gb_aapl, gb_brk.b)
            try:
                sina_sym = "gb_" + code.lower().replace("_", ".")
                url = f"http://hq.sinajs.cn/list={sina_sym}"
                r = requests.get(
                    url,
                    headers={"Referer": "https://finance.sina.com.cn"},
                    timeout=10,
                )
                fields = r.text.split('"')[1].split(",")
                name = fields[0]
                price = float(fields[1])
                if price > 0:
                    # fields[2] is change_pct directly from Sina
                    change_pct = float(fields[2]) if fields[2] else 0.0
                    result[code] = {
                        "price": price,
                        "change_pct": round(change_pct, 2),
                        "name": name,
                    }
                    continue
            except Exception:
                pass

            # 2. Fallback: daily historical (yesterday's close)
            try:
                symbol = code.replace("_", ".")
                df = ak.stock_us_daily(symbol=symbol, adjust="")
                if df is None or len(df) < 2:
                    continue
                latest = df.iloc[-1]
                prev = df.iloc[-2]
                close = float(latest["close"])
                prev_close = float(prev["close"])
                change_pct = (close - prev_close) / prev_close * 100
                result[code] = {
                    "price": close,
                    "change_pct": round(change_pct, 2),
                    "name": code,
                }
            except Exception as e:
                logger.error(f"US quote error for {code}: {e}")
        return result

    def _fetch_kr_quotes(self, codes: list) -> dict:
        """Fetch Korean stock quotes via FinanceDataReader.
        6-digit codes (e.g. 005930=三星电子, 000660=SK海力士).
        Data source: KRX via Yahoo Finance — may have ~15 min delay.
        """
        result = {}
        try:
            import FinanceDataReader as fdr
        except ImportError:
            logger.warning(
                "FinanceDataReader not installed. "
                "Korean stock quotes unavailable. "
                "Install with: pip install finance-datareader"
            )
            return result

        for code in codes:
            try:
                end = date.today()
                start = end - timedelta(days=10)
                df = fdr.DataReader(code, start, end)
                if df is None or df.empty:
                    continue
                latest = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else latest
                price = float(latest["Close"])
                prev_close = float(prev["Close"])
                if price <= 0:
                    continue
                change_pct = (price - prev_close) / prev_close * 100
                result[code] = {
                    "price": round(price, 2),
                    "change_pct": round(change_pct, 2),
                    "name": code,
                }
            except Exception as e:
                logger.error(f"KR quote error for {code}: {e}")
        return result

    def search_funds(self, keyword: str) -> Optional[list]:
        """Search funds by keyword (code or name)."""
        try:
            df = self._get_fund_list()
            if df is None or df.empty:
                return None
            mask = (df["基金代码"].str.contains(keyword, na=False) |
                    df["基金简称"].str.contains(keyword, na=False))
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
            logger.error(f"Search error: {e}")
            return None
