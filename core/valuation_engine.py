class ValuationEngine:
    """Calculates real-time fund NAV estimates from holdings and stock quotes."""

    def calculate(self, nav_yesterday: float, holdings: list,
                  quotes: dict) -> dict:
        """
        Calculate estimated NAV and each stock's contribution.

        Args:
            nav_yesterday: Yesterday's fund NAV
            holdings: List [{stock_code, stock_name, market, weight}]
                      weight is percentage (e.g., 10.0 means 10%)
            quotes: Dict {stock_code: {price, change_pct, name}}
                    change_pct is percentage (e.g., 2.1 means +2.1%)

        Returns:
            {estimated_nav, change_pct, contributions: [{stock_code, stock_name,
              weight, stock_change_pct, contribution}]}
        """
        contributions = []
        total_weighted_change = 0.0

        for h in holdings:
            code = h["stock_code"]
            weight = h.get("weight", 0.0)

            quote = quotes.get(code)
            if quote is None:
                continue

            stock_change = quote.get("change_pct", 0.0)
            # Contribution = weight% × stock_change% / 100 (in percentage points)
            contribution = (weight * stock_change) / 100.0
            total_weighted_change += contribution

            contributions.append({
                "stock_code": code,
                "stock_name": h["stock_name"],
                "weight": weight,
                "stock_change_pct": stock_change,
                "contribution": round(contribution, 4),
            })

        contributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)

        change_pct = round(total_weighted_change, 4)
        estimated_nav = round(nav_yesterday * (1 + change_pct / 100), 4)

        return {
            "estimated_nav": estimated_nav,
            "change_pct": change_pct,
            "contributions": contributions,
        }
