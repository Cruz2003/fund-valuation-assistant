"""Search fund dialog + Settings dialog."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialogButtonBox, QSpinBox, QFormLayout,
)
from PySide6.QtCore import Qt


class SearchFundDialog(QDialog):
    def __init__(self, fund_manager, parent=None):
        super().__init__(parent)
        self.fund_manager = fund_manager
        self._selected_code = None
        self.setObjectName("searchDialog")
        self._setup_ui()

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
        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self._do_search)
        search_btn.setObjectName("searchBtn")
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)

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

    def _do_search(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            return
        self.status_label.setText("搜索中...")
        results = self.fund_manager.search_funds(keyword)
        self.results_table.setRowCount(0)
        if not results:
            self.status_label.setText("未找到匹配的基金")
            return
        self.status_label.setText(f"找到 {len(results)} 个结果")
        for r in results:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(r["code"]))
            self.results_table.setItem(row, 1, QTableWidgetItem(r["name"]))
            self.results_table.setItem(row, 2, QTableWidgetItem(r.get("fund_type", "")))

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
