"""Verify AkShare data fetching APIs — fund info, holdings, stock quotes."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_fetcher import DataFetcher


def test_fetch_fund_info():
    """Test fetching fund basic info by code."""
    fetcher = DataFetcher()
    # 富国互联网科技 161028
    info = fetcher.fetch_fund_info("161028")
    assert info is not None, "fetch_fund_info returned None"
    assert "name" in info, f"Missing 'name' in {info}"
    assert "code" in info, f"Missing 'code' in {info}"
    print(f"Fund info: {info}")


def test_fetch_fund_holdings():
    """Test fetching top 10 holdings for a fund."""
    fetcher = DataFetcher()
    holdings = fetcher.fetch_fund_holdings("161028")
    assert holdings is not None, "fetch_fund_holdings returned None"
    assert len(holdings) > 0, "Holdings list is empty"
    for h in holdings:
        assert "stock_code" in h
        assert "stock_name" in h
        assert "weight" in h
    print(f"Holdings ({len(holdings)}):")
    for h in holdings:
        print(f"  {h['stock_code']} {h['stock_name']}: {h['weight']}% ({h['market']})")


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


def test_search_funds():
    """Test fund search."""
    fetcher = DataFetcher()
    results = fetcher.search_funds("互联网")
    assert results is not None, "search_funds returned None"
    assert len(results) > 0, "No search results"
    print(f"Search results ({len(results)}):")
    for r in results[:5]:
        print(f"  {r['code']} {r['name']} {r.get('fund_type', '')}")


if __name__ == "__main__":
    print("=== Test 1: Fund Info ===")
    test_fetch_fund_info()
    print("\n=== Test 2: Fund Holdings ===")
    test_fetch_fund_holdings()
    print("\n=== Test 3: Stock Quotes ===")
    test_fetch_stock_quotes()
    print("\n=== Test 4: Fund Search ===")
    test_search_funds()
    print("\nAll AkShare data fetching tests completed!")
