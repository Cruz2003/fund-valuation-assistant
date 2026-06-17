"""Fund Tracker — 基金实时估值助手 — Application entry point."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from config import APP_NAME
from data.database import Database
from core.data_fetcher import DataFetcher
from core.valuation_engine import ValuationEngine
from core.fund_manager import FundManager
from core.alert_service import AlertService
from scheduler import RefreshScheduler
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")

    # Enable high DPI
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Init backend
    db = Database()
    fetcher = DataFetcher()
    engine = ValuationEngine()
    fund_manager = FundManager(db, fetcher, engine)
    alert_service = AlertService(db)
    scheduler = RefreshScheduler(interval_seconds=300)

    # Start GUI
    window = MainWindow(fund_manager, alert_service, scheduler)
    window.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
