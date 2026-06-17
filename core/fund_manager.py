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
