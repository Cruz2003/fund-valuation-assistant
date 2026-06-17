"""Application-level configuration constants."""

DEFAULT_REFRESH_INTERVAL = 300  # seconds (5 minutes)
DEFAULT_ALERT_THRESHOLD = 2.0   # percentage
DB_FILENAME = "fund_tracker.db"

# Trading hours (Beijing time, 24h format)
MARKET_HOURS = {
    "A":  {"open": (9, 30), "close": (15, 0)},
    "HK": {"open": (9, 30), "close": (16, 0)},
    "US": {"open": (21, 30), "close": (4, 0)},  # crosses midnight
}

APP_NAME = "基金实时估值助手"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
