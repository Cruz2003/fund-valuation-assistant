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
        Returns: {triggered, direction, fund_code, fund_name, change_pct, threshold}
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
