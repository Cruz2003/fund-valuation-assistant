"""Search fund dialog + Settings dialog."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialogButtonBox, QSpinBox, QFormLayout,
)
from PySide6.QtCore import Qt, QThread


class SearchFundDialog(QDialog):
    def __init__(self, fund_manager, parent=None):
        super().__init__(parent)
        self.fund_manager = fund_manager
        self._selected_code = None
        self._search_thread = None
        self._search_worker = None
        self._refresh_thread = None
        self._refresh_worker = None
        self.setObjectName("searchDialog")
        self._setup_ui()
        self._update_cache_status()

    def _setup_ui(self):
        self.setWindowTitle("添加基金")
        self.resize(500, 420)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入基金代码或关键词...")
        self.search_input.returnPressed.connect(self._do_search)
        search_layout.addWidget(self.search_input)
        self.search_btn = QPushButton("搜索")
        self.search_btn.clicked.connect(self._do_search)
        self.search_btn.setObjectName("searchBtn")
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)

        # Refresh cache button row
        refresh_layout = QHBoxLayout()
        self.cache_status_label = QLabel()
        self.cache_status_label.setObjectName("cacheStatus")
        refresh_layout.addWidget(self.cache_status_label, 1)
        self.refresh_list_btn = QPushButton("🔄 刷新基金列表")
        self.refresh_list_btn.clicked.connect(self._do_refresh_list)
        self.refresh_list_btn.setObjectName("refreshListBtn")
        refresh_layout.addWidget(self.refresh_list_btn)
        layout.addLayout(refresh_layout)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["基金代码", "基金名称", "类型"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.verticalHeader().setVisible(False)
        layout.addWidget(self.results_table)

        self.status_label = QLabel("请输入关键词搜索")
        self.status_label.setObjectName("statusLabel")
        layout.addWidget(self.status_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _update_cache_status(self):
        if self.fund_manager.has_fund_list_cache():
            self.cache_status_label.setText("✅ 基金列表已就绪")
            self.search_input.setEnabled(True)
            self.search_btn.setEnabled(True)
        else:
            self.cache_status_label.setText("⚠ 尚未下载基金列表")
            self.search_input.setEnabled(False)
            self.search_btn.setEnabled(False)
            self.status_label.setText("请先点击「🔄 刷新基金列表」下载基金数据")

    def _do_refresh_list(self):
        self.refresh_list_btn.setEnabled(False)
        self.cache_status_label.setText("⏳ 正在从网络下载基金列表（可能需要几分钟）...")
        self.status_label.setText("下载中...")

        from core.refresh_worker import RefreshFundListWorker

        self._refresh_thread = QThread()
        self._refresh_worker = RefreshFundListWorker(self.fund_manager)
        self._refresh_worker.moveToThread(self._refresh_thread)

        self._refresh_thread.started.connect(self._refresh_worker.run)
        self._refresh_worker.finished.connect(self._on_refresh_done)
        self._refresh_worker.error.connect(self._on_refresh_error)
        self._refresh_worker.finished.connect(self._refresh_thread.quit)
        self._refresh_worker.error.connect(self._refresh_thread.quit)

        self._refresh_thread.start()

    def _on_refresh_done(self, ok: bool):
        self.refresh_list_btn.setEnabled(True)
        if ok:
            self._update_cache_status()
            self.status_label.setText("基金列表下载完成，可以搜索了")
        else:
            self.cache_status_label.setText("⚠ 下载失败，请重试")
            self.status_label.setText("下载基金列表失败，请检查网络后重试")
        self._cleanup_refresh_thread()

    def _on_refresh_error(self, error_msg: str):
        self.refresh_list_btn.setEnabled(True)
        self.cache_status_label.setText("⚠ 下载失败，请重试")
        self.status_label.setText(f"下载失败: {error_msg}")
        self._cleanup_refresh_thread()

    def _cleanup_refresh_thread(self):
        if self._refresh_worker:
            self._refresh_worker.deleteLater()
            self._refresh_worker = None
        if self._refresh_thread:
            self._refresh_thread.deleteLater()
            self._refresh_thread = None

    def _do_search(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            return
        if not self.fund_manager.has_fund_list_cache():
            self.status_label.setText("请先下载基金列表")
            return
        self.search_btn.setEnabled(False)
        self.status_label.setText("搜索中...")
        self.results_table.setRowCount(0)

        from core.refresh_worker import SearchWorker

        self._search_thread = QThread()
        self._search_worker = SearchWorker(self.fund_manager, keyword)
        self._search_worker.moveToThread(self._search_thread)

        self._search_thread.started.connect(self._search_worker.run)
        self._search_worker.finished.connect(self._on_search_done)
        self._search_worker.error.connect(self._on_search_error)
        self._search_worker.finished.connect(self._search_thread.quit)
        self._search_worker.error.connect(self._search_thread.quit)
        self._search_thread.finished.connect(self._cleanup_search_thread)

        self._search_thread.start()

    def _on_search_done(self, results: list):
        self.search_btn.setEnabled(True)
        self.results_table.setRowCount(0)
        if not results:
            self.status_label.setText("未找到匹配的基金，可尝试刷新基金列表后重试")
            return
        self.status_label.setText(f"找到 {len(results)} 个结果")
        for r in results:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(r["code"]))
            self.results_table.setItem(row, 1, QTableWidgetItem(r["name"]))
            self.results_table.setItem(row, 2, QTableWidgetItem(r.get("fund_type", "")))

    def _on_search_error(self, error_msg: str):
        self.search_btn.setEnabled(True)
        self.status_label.setText(f"搜索失败: {error_msg}")

    def _cleanup_search_thread(self):
        if self._search_worker:
            self._search_worker.deleteLater()
            self._search_worker = None
        if self._search_thread:
            self._search_thread.deleteLater()
            self._search_thread = None

    def reject(self):
        # Clean up any running threads before closing
        if self._search_thread and self._search_thread.isRunning():
            self._search_thread.quit()
            self._search_thread.wait(1000)
        if self._refresh_thread and self._refresh_thread.isRunning():
            self._refresh_thread.quit()
            self._refresh_thread.wait(1000)
        super().reject()

    def _on_accept(self):
        current = self.results_table.currentRow()
        if current >= 0:
            self._selected_code = self.results_table.item(current, 0).text()
            self.accept()
        else:
            keyword = self.search_input.text().strip()
            if keyword.isdigit() and len(keyword) == 6:
                self._selected_code = keyword
                self.accept()

    def get_selected_code(self):
        return self._selected_code


class SettingsDialog(QDialog):
    def __init__(self, alert_service, scheduler, parent=None):
        super().__init__(parent)
        self.alert_service = alert_service
        self.scheduler = scheduler
        self.setObjectName("settingsDialog")
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("设置")
        self.resize(360, 200)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        form = QFormLayout()
        form.setSpacing(10)

        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(1, 10)
        self.threshold_spin.setSuffix(" %")
        self.threshold_spin.setValue(int(self.alert_service.get_threshold()))
        form.addRow("涨跌提醒阈值:", self.threshold_spin)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setSuffix(" 分钟")
        self.interval_spin.setValue(self.scheduler.get_interval() // 60)
        form.addRow("自动刷新间隔:", self.interval_spin)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        self.alert_service.set_threshold(float(self.threshold_spin.value()))
        self.scheduler.set_interval(self.interval_spin.value() * 60)
        self.accept()
