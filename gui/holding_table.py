"""Holdings detail table with contribution data."""
from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView,
)
from PySide6.QtGui import QColor, QBrush


class HoldingTable(QGroupBox):
    COLUMNS = ["股票名称", "股票代码", "市场", "持仓占比(%)", "涨跌幅(%)", "贡献度(%)"]

    def __init__(self):
        super().__init__("持仓明细")
        self.setObjectName("holdingTable")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 8)

        self.table = QTableWidget()
        self.table.setObjectName("dataTable")
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def load_holdings(self, holdings: list):
        self.table.setRowCount(len(holdings))
        for i, h in enumerate(holdings):
            self.table.setItem(i, 0, QTableWidgetItem(h.get("stock_name", "")))
            self.table.setItem(i, 1, QTableWidgetItem(h.get("stock_code", "")))
            market = h.get("market", "")
            market_name = {"A": "A股", "HK": "港股", "US": "美股"}.get(market, market)
            self.table.setItem(i, 2, QTableWidgetItem(market_name))
            self.table.setItem(i, 3, QTableWidgetItem(f"{h.get('weight', 0):.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem("--"))
            self.table.setItem(i, 5, QTableWidgetItem("--"))

    def update_contributions(self, contributions: list):
        contrib_map = {c["stock_code"]: c for c in contributions}
        for i in range(self.table.rowCount()):
            code_item = self.table.item(i, 1)
            if not code_item:
                continue
            contrib = contrib_map.get(code_item.text())
            if not contrib:
                continue
            # Stock change
            chg = contrib.get("stock_change_pct", 0)
            chg_item = QTableWidgetItem(f"{chg:+.2f}")
            chg_item.setForeground(QBrush(
                QColor("#FF5252" if chg > 0 else "#69F0AE" if chg < 0 else "#B0BEC5")
            ))
            self.table.setItem(i, 4, chg_item)
            # Contribution
            cval = contrib.get("contribution", 0)
            c_item = QTableWidgetItem(f"{cval:+.2f}")
            c_item.setForeground(QBrush(
                QColor("#FF5252" if cval > 0 else "#69F0AE" if cval < 0 else "#B0BEC5")
            ))
            self.table.setItem(i, 5, c_item)

    def clear(self):
        self.table.setRowCount(0)
