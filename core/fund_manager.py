from datetime import datetime
from typing import Optional, Callable
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

    def has_fund_list_cache(self) -> bool:
        """Check if local fund list cache exists."""
        return self.fetcher.has_cache()

    def refresh_fund_list(self) -> bool:
        """Force re-download the full fund list from AkShare."""
        return self.fetcher.refresh_fund_list()

    def add_fund(self, code: str) -> Optional[dict]:
        """Add a fund by code: fetch info + holdings, store in DB.
        ETF feeder funds (ETF联接) may have empty holdings — that's OK,
        the fund is still added with basic NAV tracking.
        """
        existing = self.db.get_fund_by_code(code)
        if existing:
            return existing

        info = self.fetcher.fetch_fund_info(code)
        if not info:
            return None

        fund = self.db.add_fund(
            code=code,
            name=info.get("name", code),
            fund_type=info.get("fund_type", ""),
            nav_yesterday=info.get("nav_yesterday", 0.0),
        )

        holdings = self.fetcher.fetch_fund_holdings(code)
        if holdings:
            self.db.replace_holdings(fund["id"], holdings)

        fund["_has_holdings"] = bool(holdings)
        return fund

    def delete_fund(self, fund_id: int):
        """Remove a fund and its associated data."""
        self.db.delete_fund(fund_id)

    def refresh_fund(self, fund: dict,
                     progress_callback: Optional[Callable] = None) -> Optional[dict]:
        """Refresh a single fund's valuation.

        Args:
            fund: fund dict from DB
            progress_callback: optional fn(str) called with progress messages
        """
        fund_id = fund["id"]
        code = fund["code"]

        # 1. Refresh nav_yesterday from the API so the baseline is always current
        latest_nav = self.fetcher.fetch_latest_nav(code)
        if latest_nav:
            self.db.update_fund_nav(fund_id, latest_nav)
            nav_yesterday = latest_nav
        else:
            nav_yesterday = fund["nav_yesterday"]

        holdings = self.db.get_holdings(fund_id)

        if not holdings:
            return None

        # Group holdings by market (keep full holding dicts for stock names)
        markets: dict[str, list] = {}
        for h in holdings:
            m = h.get("market", "A")
            if m not in markets:
                markets[m] = []
            markets[m].append(h)

        # Fetch quotes market by market, with per-stock progress
        all_quotes = {}
        kr_resolved = []  # codes whose market tag needs correcting → KR
        for market, stocks in markets.items():
            codes = [s["stock_code"] for s in stocks]

            # Per-stock fetching with progress (all markets)
            total = len(stocks)
            for i, s in enumerate(stocks, 1):
                name = s.get("stock_name", s["stock_code"])
                if progress_callback:
                    progress_callback(f"{name} ({i}/{total})")
                quotes = self.fetcher.fetch_stock_quotes(
                    [s["stock_code"]], market
                )
                if quotes:
                    # Extract market-learning metadata before merging
                    newly_kr = quotes.pop("_kr_resolved", [])
                    if newly_kr:
                        kr_resolved.extend(newly_kr)
                    all_quotes.update(quotes)

        # Persist learned market corrections so next refresh goes straight
        # to the correct source (zero wasted fallback attempts).
        for stock_code in kr_resolved:
            self.db.update_holding_market(fund_id, stock_code, "KR")

        # Calculate valuation
        if progress_callback:
            progress_callback("计算估值...")
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

    def refresh_holdings(self, fund: dict) -> Optional[dict]:
        """Fetch latest holdings from AkShare and replace in DB.
        Returns the updated fund detail dict (or None on failure)."""
        fund_id = fund["id"]
        holdings = self.fetcher.fetch_fund_holdings(fund["code"])
        if holdings:
            self.db.replace_holdings(fund_id, holdings)
        return self.get_fund_detail(fund_id)

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
