"""Main window — left fund list + right detail, status bar, theme."""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QStatusBar, QLabel, QMessageBox, QFrame,
)
from PySide6.QtCore import Qt, QTimer, QThread
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
#addBtn {
    padding: 8px 0;
    border: 1px solid #30363D;
    border-radius: 4px;
    background-color: #21262D;
    color: #58A6FF;
    font-size: 13px;
    font-weight: bold;
}
#addBtn:hover {
    background-color: #1F2937;
    border-color: #58A6FF;
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
    font-size: 15px;
    font-weight: bold;
    color: #E6EDF3;
}
#fundCode {
    font-size: 11px;
    color: #8B949E;
}
#detailRefreshBtn {
    padding: 4px 10px;
    border: 1px solid #30363D;
    border-radius: 4px;
    background-color: #21262D;
    color: #58A6FF;
    font-size: 11px;
}
#detailRefreshBtn:hover {
    background-color: #30363D;
    color: #79C0FF;
}
#navFrame {
    background-color: #0D1117;
    border: 1px solid #30363D;
    border-radius: 6px;
    padding: 8px 12px;
}
#navTitle {
    font-size: 10px;
    color: #8B949E;
}
#navYesterday {
    font-size: 16px;
    font-weight: bold;
    color: #E6EDF3;
}
#navEstimated {
    font-size: 16px;
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

/* ── Loading Overlay ── */
#loadingOverlay {
    background-color: rgba(13, 17, 23, 0.85);
    border: none;
}
#loadingLabel {
    font-size: 15px;
    color: #58A6FF;
    background: transparent;
}
"""


class MainWindow(QMainWindow):
    def __init__(self, fund_manager, alert_service, scheduler):
        super().__init__()
        self.fund_manager = fund_manager
        self.alert_service = alert_service
        self.scheduler = scheduler

        # Background threads
        self._refresh_thread = None
        self._refresh_worker = None
        self._add_thread = None
        self._add_worker = None
        self._holdings_thread = None
        self._holdings_worker = None

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

        # Root layout stacks splitter + loading overlay
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Horizontal)

        from gui.fund_list_panel import FundListPanel
        self.fund_list = FundListPanel()
        self.splitter.addWidget(self.fund_list)

        from gui.fund_detail_panel import FundDetailPanel
        self.fund_detail = FundDetailPanel()
        self.splitter.addWidget(self.fund_detail)

        self.splitter.setSizes([300, 900])
        self.splitter.setHandleWidth(2)

        root_layout.addWidget(self.splitter)

        # --- Loading overlay (hidden by default) ---
        self._loading_overlay = QFrame(central)
        self._loading_overlay.setObjectName("loadingOverlay")
        self._loading_overlay.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self._loading_overlay.setCursor(Qt.WaitCursor)
        overlay_layout = QVBoxLayout(self._loading_overlay)
        overlay_layout.setAlignment(Qt.AlignCenter)

        self._loading_label = QLabel("正在刷新数据")
        self._loading_label.setObjectName("loadingLabel")
        self._loading_label.setAlignment(Qt.AlignCenter)
        overlay_layout.addWidget(self._loading_label)

        # Animated dots timer
        self._loading_dot_timer = QTimer(self)
        self._loading_dot_timer.timeout.connect(self._animate_loading_dots)
        self._loading_dots = 0

        self._loading_overlay.hide()

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
        self.fund_detail.refresh_clicked.connect(self._on_detail_refresh)
        self.fund_detail.update_holdings_clicked.connect(self._on_update_holdings)
        self.scheduler.set_callback(self._on_scheduled_refresh)

    def _on_fund_selected(self, fund_data: dict):
        detail = self.fund_manager.get_fund_detail(fund_data["id"])
        self.fund_detail.display_fund(detail)
        # Restore cached valuation so switching doesn't lose current data
        cached = fund_data.get("_valuation")
        if cached:
            self.fund_detail.update_valuation(cached)

    def _on_add_fund(self, keyword: str):
        """Open search dialog, then add selected fund via background thread."""
        from gui.dialogs import SearchFundDialog
        dialog = SearchFundDialog(self.fund_manager, self)
        if not dialog.exec():
            dialog.deleteLater()
            return
        selected_code = dialog.get_selected_code()
        dialog.deleteLater()
        if not selected_code:
            return

        self._show_loading("正在添加基金")
        self.status_refresh_label.setText("添加中...")

        from core.refresh_worker import AddFundWorker

        self._add_thread = QThread()
        self._add_worker = AddFundWorker(self.fund_manager, selected_code)
        self._add_worker.moveToThread(self._add_thread)

        self._add_thread.started.connect(self._add_worker.run)
        self._add_worker.finished.connect(self._on_add_done)
        self._add_worker.error.connect(self._on_add_error)
        self._add_worker.finished.connect(self._add_thread.quit)
        self._add_worker.error.connect(self._add_thread.quit)
        self._add_thread.finished.connect(self._cleanup_add_thread)

        self._add_thread.start()

    def _on_add_done(self, fund):
        self._hide_loading()
        if fund:
            self.load_fund_list()
            self.fund_list.select_fund(fund)
            self.status_refresh_label.setText(
                f"已添加 {fund.get('name', '')} — 点击右侧「刷新估值」获取实时数据"
            )
        else:
            QMessageBox.warning(
                self, "添加失败",
                "无法获取该基金的信息，请检查代码是否正确。\n"
                "提示：请确认网络连接正常，且基金代码有效。"
            )
            self.status_refresh_label.setText("添加失败")

    def _on_add_error(self, error_msg: str):
        self._hide_loading()
        QMessageBox.warning(self, "添加失败", f"网络错误: {error_msg}")
        self.status_refresh_label.setText("添加失败")

    def _cleanup_add_thread(self):
        if self._add_worker:
            self._add_worker.deleteLater()
            self._add_worker = None
        if self._add_thread:
            self._add_thread.deleteLater()
            self._add_thread = None

    def _on_manual_refresh(self):
        self._start_refresh()

    def _on_scheduled_refresh(self):
        self._start_refresh()

    def _on_detail_refresh(self):
        """Refresh only the currently selected fund."""
        current = self.fund_list.get_selected_fund()
        if not current:
            return
        self._start_single_refresh(current)

    def _on_update_holdings(self):
        """Update holdings for the currently selected fund."""
        current = self.fund_list.get_selected_fund()
        if not current:
            return
        if self._holdings_thread is not None and self._holdings_thread.isRunning():
            self.status_refresh_label.setText("持仓更新进行中...")
            return
        self._start_holdings_update(current)

    def _start_single_refresh(self, fund: dict):
        """Refresh a single fund in background."""
        if self._refresh_thread is not None and self._refresh_thread.isRunning():
            return  # a full refresh is already running
        if self._add_thread is not None and self._add_thread.isRunning():
            return  # an add is in progress

        name = fund.get("name", fund.get("code", "?"))
        self._show_loading(f"正在刷新 {name}")

        from core.refresh_worker import SingleRefreshWorker

        self._refresh_thread = QThread()
        self._refresh_worker = SingleRefreshWorker(self.fund_manager, fund)
        self._refresh_worker.moveToThread(self._refresh_thread)

        self._refresh_thread.started.connect(self._refresh_worker.run)
        self._refresh_worker.progress.connect(self._on_refresh_progress)
        self._refresh_worker.finished.connect(self._on_single_refresh_done)
        self._refresh_worker.error.connect(self._on_refresh_error)
        self._refresh_worker.finished.connect(self._refresh_thread.quit)
        self._refresh_worker.error.connect(self._refresh_thread.quit)
        self._refresh_thread.finished.connect(self._cleanup_thread)

        self._refresh_thread.start()

    def _on_single_refresh_done(self, result: dict):
        """Called after single-fund refresh completes."""
        self._hide_loading()
        if not result:
            self.status_refresh_label.setText("刷新失败，无数据返回")
            return

        # Update detail panel (chart + table + NAV display)
        self.fund_detail.update_valuation(result)

        # Update fund list cache and redraw (does NOT clear selection)
        self.fund_list.update_valuations([result])

        # Check alert threshold
        alert = self.alert_service.check(
            result["fund_code"], result["fund_name"], result["change_pct"]
        )
        if alert["triggered"]:
            self.fund_list.highlight_fund(
                result["fund_code"], alert["direction"]
            )

        self.status_refresh_label.setText(
            f"已刷新 {result.get('fund_name', '?')}  "
            f"{self.scheduler.get_last_refresh_time() or '刚刚'}"
        )

    def _start_holdings_update(self, fund: dict):
        """Fetch latest holdings in background and update UI."""
        name = fund.get("name", fund.get("code", "?"))
        self._show_loading(f"正在更新 {name} 持仓")

        from core.refresh_worker import RefreshHoldingsWorker

        self._holdings_thread = QThread()
        self._holdings_worker = RefreshHoldingsWorker(self.fund_manager, fund)
        self._holdings_worker.moveToThread(self._holdings_thread)

        self._holdings_thread.started.connect(self._holdings_worker.run)
        self._holdings_worker.finished.connect(self._on_holdings_update_done)
        self._holdings_worker.error.connect(self._on_refresh_error)
        self._holdings_worker.finished.connect(self._holdings_thread.quit)
        self._holdings_worker.error.connect(self._holdings_thread.quit)
        self._holdings_thread.finished.connect(self._cleanup_holdings_thread)

        self._holdings_thread.start()

    def _on_holdings_update_done(self, result: dict):
        """Update detail panel with fresh holdings data."""
        self._hide_loading()
        if not result:
            self.status_refresh_label.setText("持仓更新失败，无数据返回")
            return

        # Reload fund list to reflect any name/type changes
        self.load_fund_list()

        # Redisplay the detail panel with updated holdings
        self.fund_detail.display_fund(result)

        name = result.get("name", "?")
        holdings = result.get("holdings", [])
        self.status_refresh_label.setText(
            f"{name} 持仓已更新（{len(holdings)} 只）"
        )

    def _cleanup_holdings_thread(self):
        if self._holdings_worker:
            self._holdings_worker.deleteLater()
            self._holdings_worker = None
        if self._holdings_thread:
            self._holdings_thread.deleteLater()
            self._holdings_thread = None

    def _start_refresh(self):
        """Kick off background refresh — non-blocking."""
        if self._refresh_thread is not None and self._refresh_thread.isRunning():
            return  # already refreshing

        self._show_loading("正在刷新数据")
        self.status_refresh_label.setText("刷新中...")

        from core.refresh_worker import RefreshWorker

        self._refresh_thread = QThread()
        self._refresh_worker = RefreshWorker(self.fund_manager)
        self._refresh_worker.moveToThread(self._refresh_thread)

        self._refresh_thread.started.connect(self._refresh_worker.run)
        self._refresh_worker.progress.connect(self._on_refresh_progress)
        self._refresh_worker.finished.connect(self._on_refresh_done)
        self._refresh_worker.error.connect(self._on_refresh_error)
        self._refresh_worker.finished.connect(self._refresh_thread.quit)
        self._refresh_worker.error.connect(self._refresh_thread.quit)
        self._refresh_thread.finished.connect(self._cleanup_thread)

        self._refresh_thread.start()

    def _on_refresh_done(self, results: list):
        """Called on main thread after background refresh completes."""
        self._hide_loading()

        if not results:
            self.status_refresh_label.setText("刷新完成，无数据更新")
            return

        # Capture selected fund code BEFORE update_valuations clears the list
        current = self.fund_list.get_selected_fund()
        selected_code = current["code"] if current else None

        self.fund_list.update_valuations(results)

        # Update detail panel for the currently selected fund
        if selected_code:
            for r in results:
                if r.get("fund_code") == selected_code:
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

    def _on_refresh_progress(self, text: str):
        """Update loading overlay with current fund being refreshed."""
        self._loading_base_text = f"正在刷新 {text}"
        self._loading_label.setText(self._loading_base_text)

    def _on_refresh_error(self, error_msg: str):
        """Called on main thread when background refresh fails."""
        self._hide_loading()
        self.status_refresh_label.setText(f"刷新失败: {error_msg}")

    def _show_loading(self, text: str = "正在处理"):
        """Show semi-transparent loading overlay over the content area."""
        self._loading_dots = 0
        self._loading_base_text = text
        self._loading_label.setText(text)
        self._loading_overlay.setGeometry(self.centralWidget().rect())
        self._loading_overlay.show()
        self._loading_overlay.raise_()
        self._loading_dot_timer.start(500)

    def _hide_loading(self):
        """Hide the loading overlay."""
        self._loading_dot_timer.stop()
        self._loading_overlay.hide()

    def _animate_loading_dots(self):
        """Cycle the loading dots animation."""
        self._loading_dots = (self._loading_dots + 1) % 4
        dots = "." * self._loading_dots
        self._loading_label.setText(f"{self._loading_base_text}{dots}")

    def _cleanup_thread(self):
        """Clean up thread references after thread finishes."""
        if self._refresh_worker:
            self._refresh_worker.deleteLater()
            self._refresh_worker = None
        if self._refresh_thread:
            self._refresh_thread.deleteLater()
            self._refresh_thread = None

    def resizeEvent(self, event):
        """Keep loading overlay sized to the central widget."""
        super().resizeEvent(event)
        if hasattr(self, '_loading_overlay') and self._loading_overlay.isVisible():
            self._loading_overlay.setGeometry(self.centralWidget().rect())

    def _on_delete_fund(self, fund_id: int):
        """Delete fund from DB, clear all caches, reset detail panel."""
        self.fund_manager.delete_fund(fund_id)
        self.load_fund_list()
        self.fund_detail.clear()
        self.status_refresh_label.setText("基金已删除")

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
