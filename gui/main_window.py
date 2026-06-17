"""Main window — left fund list + right detail, status bar, theme."""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter,
    QStatusBar, QLabel, QMessageBox,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from config import APP_NAME, WINDOW_WIDTH, WINDOW_HEIGHT

# ── Industrial Dark Theme ────────────────────────────────────────────
# Surface: deep navy-black (#0D1117 / #161B22)
# Signal: red-up #FF5252, green-down #69F0AE (Chinese market convention)
# Structure: 1px borders (#30363D), no shadows
# Typography: system sans for UI, tabular numbers for data
# ──────────────────────────────────────────────────────────────────────

STYLESHEET = """
/* ── Global ── */
QMainWindow {
    background-color: #0D1117;
    color: #E6EDF3;
}
QWidget {
    background-color: #0D1117;
    color: #E6EDF3;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}

/* ── Fund List Panel ── */
#fundListPanel {
    background-color: #161B22;
    border-right: 1px solid #30363D;
}
#panelTitle {
    font-size: 16px;
    font-weight: bold;
    color: #E6EDF3;
    padding: 4px 0;
}
#searchInput {
    padding: 6px 10px;
    border: 1px solid #30363D;
    border-radius: 4px;
    background-color: #0D1117;
    color: #E6EDF3;
    font-size: 12px;
}
#searchInput:focus {
    border-color: #58A6FF;
}
#addBtn {
    padding: 6px 0;
    border: 1px solid #30363D;
    border-radius: 4px;
    background-color: #21262D;
    color: #E6EDF3;
    font-size: 12px;
}
#addBtn:hover {
    background-color: #30363D;
}
#actionBtn {
    padding: 5px 10px;
    border: 1px solid #30363D;
    border-radius: 4px;
    background-color: #21262D;
    color: #C9D1D9;
    font-size: 11px;
}
#actionBtn:hover {
    background-color: #30363D;
    color: #E6EDF3;
}
#fundList {
    border: 1px solid #30363D;
    border-radius: 4px;
    background-color: #0D1117;
    color: #E6EDF3;
    font-size: 12px;
    outline: none;
}
#fundList::item {
    padding: 10px 12px;
    border-bottom: 1px solid #21262D;
}
#fundList::item:selected {
    background-color: #1F2937;
    border-left: 3px solid #58A6FF;
}
#emptyLabel {
    color: #484F58;
    font-size: 13px;
}

/* ── Detail Panel ── */
#detailPanel {
    background-color: #0D1117;
}
#detailScroll {
    background-color: #0D1117;
    border: none;
}
#detailContent {
    background-color: #0D1117;
}

/* ── Info Card ── */
#infoCard {
    border: 1px solid #30363D;
    border-radius: 6px;
    background-color: #161B22;
    margin-top: 8px;
    padding-top: 20px;
    font-weight: bold;
    color: #E6EDF3;
}
#infoCard::title {
    subcontrol-origin: margin;
    left: 16px;
    color: #8B949E;
}
#fundName {
    font-size: 18px;
    font-weight: bold;
    color: #E6EDF3;
}
#fundCode {
    font-size: 12px;
    color: #8B949E;
}
#navFrame {
    background-color: #0D1117;
    border: 1px solid #30363D;
    border-radius: 6px;
    padding: 16px;
}
#navTitle {
    font-size: 11px;
    color: #8B949E;
}
#navYesterday {
    font-size: 20px;
    font-weight: bold;
    color: #E6EDF3;
}
#navEstimated {
    font-size: 20px;
    font-weight: bold;
    color: #E6EDF3;
}

/* ── Holding Table ── */
#holdingTable {
    border: 1px solid #30363D;
    border-radius: 6px;
    background-color: #161B22;
    margin-top: 8px;
    padding-top: 20px;
    font-weight: bold;
    color: #E6EDF3;
}
#holdingTable::title {
    subcontrol-origin: margin;
    left: 16px;
    color: #8B949E;
}
#dataTable {
    border: 1px solid #30363D;
    background-color: #0D1117;
    color: #E6EDF3;
    gridline-color: #21262D;
    font-size: 12px;
    alternate-background-color: #161B22;
}
#dataTable QHeaderView::section {
    background-color: #161B22;
    color: #8B949E;
    padding: 6px 8px;
    border: none;
    border-bottom: 1px solid #30363D;
    font-weight: bold;
    font-size: 11px;
}

/* ── Chart Panel ── */
#chartPanel {
    border: 1px solid #30363D;
    border-radius: 6px;
    background-color: #161B22;
    margin-top: 8px;
    padding-top: 20px;
    font-weight: bold;
    color: #E6EDF3;
}
#chartPanel::title {
    subcontrol-origin: margin;
    left: 16px;
    color: #8B949E;
}

/* ── Status Bar ── */
QStatusBar {
    background-color: #161B22;
    border-top: 1px solid #30363D;
    color: #8B949E;
    font-size: 11px;
    padding: 4px 12px;
}
QStatusBar QLabel {
    color: #8B949E;
    background: transparent;
    font-size: 11px;
}

/* ── Dialogs ── */
QDialog {
    background-color: #161B22;
    color: #E6EDF3;
}
QDialog QLabel {
    background: transparent;
}
QDialog QLineEdit {
    padding: 6px 10px;
    border: 1px solid #30363D;
    border-radius: 4px;
    background-color: #0D1117;
    color: #E6EDF3;
}
QDialog QTableWidget {
    border: 1px solid #30363D;
    background-color: #0D1117;
    gridline-color: #21262D;
    color: #E6EDF3;
}
QDialog QHeaderView::section {
    background-color: #161B22;
    color: #8B949E;
    padding: 4px;
    border: none;
    border-bottom: 1px solid #30363D;
}
QDialog QPushButton {
    padding: 6px 16px;
    border: 1px solid #30363D;
    border-radius: 4px;
    background-color: #21262D;
    color: #C9D1D9;
}
QDialog QPushButton:hover {
    background-color: #30363D;
}
QDialog QSpinBox {
    padding: 4px 8px;
    border: 1px solid #30363D;
    border-radius: 4px;
    background-color: #0D1117;
    color: #E6EDF3;
}

/* ── Scrollbar ── */
QScrollBar:vertical {
    background: #161B22;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #30363D;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #484F58;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* ── Splitter ── */
QSplitter::handle {
    background-color: #30363D;
    width: 2px;
}

/* ── Tooltip ── */
QToolTip {
    background-color: #21262D;
    color: #E6EDF3;
    border: 1px solid #30363D;
    padding: 4px 8px;
    font-size: 11px;
}

/* ── Message Box ── */
QMessageBox {
    background-color: #161B22;
    color: #E6EDF3;
}
QMessageBox QLabel {
    color: #E6EDF3;
    background: transparent;
}
QMessageBox QPushButton {
    min-width: 70px;
    padding: 6px 16px;
    border: 1px solid #30363D;
    border-radius: 4px;
    background-color: #21262D;
    color: #C9D1D9;
}
QMessageBox QPushButton:hover {
    background-color: #30363D;
}

/* ── Menu ── */
QMenu {
    background-color: #161B22;
    border: 1px solid #30363D;
    color: #E6EDF3;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px;
}
QMenu::item:selected {
    background-color: #1F2937;
}
QMenu::separator {
    height: 1px;
    background: #30363D;
    margin: 4px 8px;
}
"""


class MainWindow(QMainWindow):
    def __init__(self, fund_manager, alert_service, scheduler):
        super().__init__()
        self.fund_manager = fund_manager
        self.alert_service = alert_service
        self.scheduler = scheduler

        self.setWindowTitle(APP_NAME)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(900, 600)

        self._setup_ui()
        self._setup_statusbar()
        self._connect_signals()

        # Apply dark theme
        self.setStyleSheet(STYLESHEET)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        self.splitter = QSplitter(Qt.Horizontal)

        from gui.fund_list_panel import FundListPanel
        self.fund_list = FundListPanel()
        self.splitter.addWidget(self.fund_list)

        from gui.fund_detail_panel import FundDetailPanel
        self.fund_detail = FundDetailPanel()
        self.splitter.addWidget(self.fund_detail)

        self.splitter.setSizes([300, 900])
        self.splitter.setHandleWidth(2)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.splitter)

    def _setup_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_refresh_label = QLabel("就绪")
        self.status_market_label = QLabel("A ○  HK ○  US ○")
        self.status_countdown_label = QLabel("")

        self.status_bar.addWidget(self.status_refresh_label)
        self.status_bar.addPermanentWidget(self.status_market_label)
        self.status_bar.addPermanentWidget(self.status_countdown_label)

        self._countdown_timer = QTimer(self)
        self._countdown_timer.timeout.connect(self._update_statusbar)
        self._countdown_timer.start(1000)

    def _connect_signals(self):
        self.fund_list.fund_selected.connect(self._on_fund_selected)
        self.fund_list.add_fund_requested.connect(self._on_add_fund)
        self.fund_list.refresh_requested.connect(self._on_manual_refresh)
        self.fund_list.delete_fund_requested.connect(self._on_delete_fund)
        self.fund_list.settings_requested.connect(self._on_settings)
        self.scheduler.set_callback(self._on_scheduled_refresh)

    def _on_fund_selected(self, fund_data: dict):
        detail = self.fund_manager.get_fund_detail(fund_data["id"])
        self.fund_detail.display_fund(detail)

    def _on_add_fund(self, keyword: str):
        from gui.dialogs import SearchFundDialog
        dialog = SearchFundDialog(self.fund_manager, self)
        if dialog.exec():
            selected_code = dialog.get_selected_code()
            if selected_code:
                fund = self.fund_manager.add_fund(selected_code)
                if fund:
                    self.load_fund_list()
                    self.fund_list.select_fund(fund)
                else:
                    QMessageBox.warning(
                        self, "添加失败",
                        f"无法获取基金 {selected_code} 的信息，请检查代码是否正确。"
                    )
        dialog.deleteLater()

    def _on_manual_refresh(self):
        self._do_refresh()

    def _on_scheduled_refresh(self):
        self._do_refresh()

    def _do_refresh(self):
        self.status_refresh_label.setText("刷新中...")
        try:
            results = self.fund_manager.refresh_all()
        except Exception as e:
            self.status_refresh_label.setText(f"刷新失败: {e}")
            return

        if results:
            self.fund_list.update_valuations(results)
            current = self.fund_list.get_selected_fund()
            if current:
                # Refresh detail with latest data
                fund_id = current["id"]
                detail = self.fund_manager.get_fund_detail(fund_id)
                self.fund_detail.display_fund(detail)
                # Also update valuation display
                for r in results:
                    if r["fund_id"] == fund_id:
                        self.fund_detail.update_valuation(r)
                        break
            for r in results:
                alert = self.alert_service.check(
                    r["fund_code"], r["fund_name"], r["change_pct"]
                )
                if alert["triggered"]:
                    self.fund_list.highlight_fund(
                        r["fund_code"], alert["direction"]
                    )

        self.status_refresh_label.setText(
            f"最后刷新 {self.scheduler.get_last_refresh_time() or '刚刚'}"
        )

    def _on_delete_fund(self, fund_id: int):
        self.fund_manager.delete_fund(fund_id)
        self.load_fund_list()
        self.fund_detail.clear()

    def _on_settings(self):
        from gui.dialogs import SettingsDialog
        dialog = SettingsDialog(self.alert_service, self.scheduler, self)
        dialog.exec()
        dialog.deleteLater()

    def _update_statusbar(self):
        from scheduler import get_market_status
        markets = get_market_status()
        def dot(on): return "●" if on else "○"
        self.status_market_label.setText(
            f"A {dot(markets['A'])}    "
            f"HK {dot(markets['HK'])}    "
            f"US {dot(markets['US'])}"
        )
        remaining = self.scheduler.get_countdown()
        self.status_countdown_label.setText(
            f"刷新 {remaining // 60}:{remaining % 60:02d}"
        )

    def load_fund_list(self):
        funds = self.fund_manager.get_all_funds()
        self.fund_list.load_funds(funds)

    def start(self):
        self.load_fund_list()
        self.scheduler.start()
        self.show()
