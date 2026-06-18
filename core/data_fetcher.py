import logging
import akshare as ak
import time
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

import pandas as pd

_fund_list_cache: Optional[pd.DataFrame] = None


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
        """Fetch top 10 holdings for a fund."""
        try:
            # Try latest year first
            current_year = str(datetime.now().year)
            df = ak.fund_portfolio_hold_em(symbol=code, date=current_year)
            if df is None or df.empty:
                df = ak.fund_portfolio_hold_em(symbol=code)
            if df is None or df.empty:
                return None

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
        """Fetch real-time quotes for a list of stock codes."""
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
            logger.error(f"Error fetching {market} quotes: {e}")
            return {}

    def _fetch_a_quotes(self, codes: list) -> dict:
        """Fetch A-share real-time quotes via Sina source.
        Sina uses code format: sh600519, sz000001, bj920000."""
        try:
            df = ak.stock_zh_a_spot()
            if df is None or df.empty:
                return {}
            # Build lookup: try both raw code and with sh/sz prefix
            result = {}
            for code in codes:
                # Try exact match first
                match = df[df["代码"] == code]
                # Try with sh prefix (60xxxx, 688xxx)
                if match.empty and (code.startswith("60") or code.startswith("688")):
                    match = df[df["代码"] == ("sh" + code)]
                # Try with sz prefix (00xxxx, 30xxxx)
                if match.empty and (code.startswith("00") or code.startswith("30")):
                    match = df[df["代码"] == ("sz" + code)]
                if not match.empty:
                    row = match.iloc[0]
                    result[code] = {
                        "price": float(row["最新价"]),
                        "change_pct": float(row["涨跌幅"]),
                        "name": str(row["名称"]),
                    }
            return result
        except Exception as e:
            logger.error(f"A-share quote error: {e}")
            return {}

    def _fetch_hk_quotes(self, codes: list) -> dict:
        """Fetch HK stock quotes via daily historical data (Sina).
        Calculates change from latest two trading days."""
        result = {}
        for code in codes:
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
        """Fetch US stock quotes via daily historical data (Sina).
        Calculates change from latest two trading days."""
        result = {}
        for code in codes:
            try:
                # Normalize US stock codes: fund data uses BRK_B but
                # AkShare/Sina expects BRK.B for class-designated stocks
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
