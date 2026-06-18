"""Left panel: fund list with search, add, refresh, delete."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QMessageBox, QMenu,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QColor, QBrush


class FundListPanel(QWidget):
    fund_selected = Signal(dict)
    add_fund_requested = Signal(str)
    refresh_requested = Signal()
    delete_fund_requested = Signal(int)
    settings_requested = Signal()

    def __init__(self):
        super().__init__()
        self._funds = {}
        self.setObjectName("fundListPanel")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Title
        title = QLabel("基金实时估值")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        # Add fund button
        self.add_btn = QPushButton("+ 添加基金")
        self.add_btn.clicked.connect(self._on_add_clicked)
        self.add_btn.setObjectName("addBtn")
        layout.addWidget(self.add_btn)

        # Action buttons
        btn_row = QHBoxLayout()
        self.refresh_btn = QPushButton("刷新全部")
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)
        self.refresh_btn.setObjectName("actionBtn")
        btn_row.addWidget(self.refresh_btn)

        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        self.delete_btn.setObjectName("actionBtn")
        self.delete_btn.setEnabled(False)
        btn_row.addWidget(self.delete_btn)

        self.settings_btn = QPushButton("设置")
        self.settings_btn.clicked.connect(self.settings_requested.emit)
        self.settings_btn.setObjectName("actionBtn")
        btn_row.addWidget(self.settings_btn)
        layout.addLayout(btn_row)

        # Fund list
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("fundList")
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.list_widget.currentItemChanged.connect(
            lambda cur, prev: self.delete_btn.setEnabled(cur is not None)
        )
        layout.addWidget(self.list_widget)

        # Empty state
        self.empty_label = QLabel("暂无基金\n点击上方按钮添加")
        self.empty_label.setObjectName("emptyLabel")
        self.empty_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.empty_label)

    def load_funds(self, funds: list):
        # Preserve existing _valuation data so add/delete doesn't reset all funds
        for fund in funds:
            old = self._funds.get(fund["code"], {})
            if "_valuation" in old:
                fund["_valuation"] = old["_valuation"]
        self._funds = {}
        self.list_widget.clear()
        for fund in funds:
            self._funds[fund["code"]] = fund
        self._redraw_list()
        self.empty_label.setVisible(len(funds) == 0)
        self.list_widget.setVisible(len(funds) > 0)

    def update_valuations(self, results: list):
        for r in results:
            code = r["fund_code"]
            if code in self._funds:
                self._funds[code]["_valuation"] = r
        self._redraw_list()

    def highlight_fund(self, fund_code: str, direction: str):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == fund_code:
                if direction == "up":
                    item.setBackground(QBrush(QColor("#4A1515")))
                elif direction == "down":
                    item.setBackground(QBrush(QColor("#154A15")))
                break

    def _redraw_list(self):
        self.list_widget.clear()
        for code, fund in self._funds.items():
            val = fund.get("_valuation")
            if val:
                change = val["change_pct"]
                sign = "+" if change >= 0 else ""
                text = (f"{fund['name']}\n"
                        f"{fund['code']}    估值 {val['estimated_nav']:.4f}"
                        f"    {sign}{change:.2f}%")
            else:
                text = f"{fund['name']}\n{fund['code']}    待刷新"

            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, code)
            if val:
                item.setForeground(
                    QBrush(QColor("#FF5252" if val["change_pct"] > 0
                           else "#69F0AE" if val["change_pct"] < 0
                           else "#B0BEC5"))
                )
            self.list_widget.addItem(item)

    def _on_item_clicked(self, item):
        code = item.data(Qt.UserRole)
        if code in self._funds:
            self.fund_selected.emit(self._funds[code])

    def _on_add_clicked(self):
        self.add_fund_requested.emit("")

    def _on_delete_clicked(self):
        current = self.get_selected_fund()
        if not current:
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除 {current['name']} ({current['code']}) 吗？\n"
            f"基金数据、持仓和估值历史将被全部清除。",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            code = current["code"]
            # Purge from memory cache immediately
            self._funds.pop(code, None)
            self.delete_fund_requested.emit(current["id"])

    def _show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item:
            return
        code = item.data(Qt.UserRole)
        fund = self._funds.get(code)
        if not fund:
            return
        menu = QMenu(self)
        delete_action = menu.addAction("删除")
        action = menu.exec(self.list_widget.mapToGlobal(pos))
        if action == delete_action:
            reply = QMessageBox.question(
                self, "确认删除",
                f"确定要删除 {fund['name']} ({code}) 吗？\n"
                f"基金数据、持仓和估值历史将被全部清除。",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self._funds.pop(code, None)
                self.delete_fund_requested.emit(fund["id"])

    def get_selected_fund(self):
        current = self.list_widget.currentItem()
        if current:
            return self._funds.get(current.data(Qt.UserRole))
        return None

    def select_fund(self, fund):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == fund["code"]:
                self.list_widget.setCurrentItem(item)
                break
