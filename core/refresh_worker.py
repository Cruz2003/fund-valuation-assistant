"""Background workers — run network-heavy operations off the main thread."""

from PySide6.QtCore import QObject, Signal


class RefreshWorker(QObject):
    """Iterates funds one-by-one in background, emitting granular progress."""

    started = Signal()
    progress = Signal(str)            # e.g. "A股行情 (5只)" / "腾讯控股 (3/5)"
    finished = Signal(list)           # list of valuation result dicts
    error = Signal(str)

    def __init__(self, fund_manager):
        super().__init__()
        self.fund_manager = fund_manager

    def run(self):
        self.started.emit()
        try:
            funds = self.fund_manager.db.get_all_funds()
            total = len(funds)
            results = []
            for i, fund in enumerate(funds, 1):
                name = fund.get("name", fund.get("code", "?"))
                self.progress.emit(f"{name} ({i}/{total})")

                def on_progress(msg: str):
                    self.progress.emit(f"  {msg}")

                result = self.fund_manager.refresh_fund(fund, on_progress)
                if result:
                    results.append(result)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class SingleRefreshWorker(QObject):
    """Refreshes a single fund in background with per-stock progress."""

    progress = Signal(str)            # per-stock progress
    finished = Signal(object)         # single valuation result dict (or None)
    error = Signal(str)

    def __init__(self, fund_manager, fund: dict):
        super().__init__()
        self.fund_manager = fund_manager
        self.fund = fund

    def run(self):
        try:
            def on_progress(msg: str):
                self.progress.emit(msg)

            result = self.fund_manager.refresh_fund(self.fund, on_progress)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class AddFundWorker(QObject):
    """Fetches fund info + holdings in background so GUI doesn't freeze."""

    finished = Signal(object)         # fund dict or None
    error = Signal(str)

    def __init__(self, fund_manager, code: str):
        super().__init__()
        self.fund_manager = fund_manager
        self.code = code

    def run(self):
        try:
            fund = self.fund_manager.add_fund(self.code)
            self.finished.emit(fund)
        except Exception as e:
            self.error.emit(str(e))


class SearchWorker(QObject):
    """Searches funds in background so the search dialog stays responsive."""

    finished = Signal(list)           # list of search result dicts
    error = Signal(str)

    def __init__(self, fund_manager, keyword: str):
        super().__init__()
        self.fund_manager = fund_manager
        self.keyword = keyword

    def run(self):
        try:
            results = self.fund_manager.search_funds(self.keyword) or []
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class RefreshHoldingsWorker(QObject):
    """Fetches latest holdings from AkShare and replaces them in DB."""

    finished = Signal(object)    # updated fund detail dict (or None)
    error = Signal(str)

    def __init__(self, fund_manager, fund: dict):
        super().__init__()
        self.fund_manager = fund_manager
        self.fund = fund

    def run(self):
        try:
            result = self.fund_manager.refresh_holdings(self.fund)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class RefreshFundListWorker(QObject):
    """Downloads full fund list from AkShare in background."""

    finished = Signal(bool)      # success or failure
    error = Signal(str)

    def __init__(self, fund_manager):
        super().__init__()
        self.fund_manager = fund_manager

    def run(self):
        try:
            ok = self.fund_manager.refresh_fund_list()
            self.finished.emit(ok)
        except Exception as e:
            self.error.emit(str(e))
