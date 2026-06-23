"""Holdings detail table with contribution data."""
from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QTableWidget, QLabel,
    QTableWidgetItem, QHeaderView, QSizePolicy,
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
        layout.setSpacing(4)

        self.table = QTableWidget()
        self.table.setObjectName("dataTable")
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setMinimumHeight(180)
        self.table.verticalHeader().setDefaultSectionSize(32)
        layout.addWidget(self.table)

        self.total_label = QLabel("")
        self.total_label.setObjectName("totalLabel")
        self.total_label.setStyleSheet(
            "color: #8B949E; font-size: 11px; padding: 2px 4px; background: transparent;"
        )
        layout.addWidget(self.total_label)

    def load_holdings(self, holdings: list):
        total_weight = sum(h.get("weight", 0) for h in holdings)
        self.total_label.setText(f"前十大持仓合计 {total_weight:.2f}%")
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
        self.total_label.setText("")
        self.table.setRowCount(0)
