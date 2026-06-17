from datetime import datetime
from typing import Optional, Callable
from PySide6.QtCore import QTimer, QObject


def is_market_open(market: str, hour: int = None, minute: int = None) -> bool:
    """Check if a market is currently in trading hours (Beijing time)."""
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
        us_open = 21 * 60 + 30
        us_close = 4 * 60
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
        self._timer.start(1000)

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
        self._countdown = 0

    def set_interval(self, seconds: int):
        """Change the refresh interval."""
        self._interval = max(60, seconds)
        self._countdown = min(self._countdown, self._interval)

    def get_interval(self) -> int:
        return self._interval
