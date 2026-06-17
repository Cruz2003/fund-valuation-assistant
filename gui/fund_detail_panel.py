"""Right panel: fund detail — NAV card, holdings table, charts."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QScrollArea, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class FundDetailPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("detailPanel")
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("detailScroll")

        content = QWidget()
        content.setObjectName("detailContent")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(16, 16, 16, 16)
        self.content_layout.setSpacing(12)

        # --- Fund info card ---
        self.info_card = QGroupBox("基金信息")
        self.info_card.setObjectName("infoCard")
        info_layout = QVBoxLayout(self.info_card)
        info_layout.setContentsMargins(16, 20, 16, 16)
        info_layout.setSpacing(8)

        self.name_label = QLabel("请选择一只基金")
        self.name_label.setObjectName("fundName")
        info_layout.addWidget(self.name_label)

        self.code_label = QLabel("")
        self.code_label.setObjectName("fundCode")
        info_layout.addWidget(self.code_label)

        # NAV row
        nav_frame = QFrame()
        nav_frame.setObjectName("navFrame")
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setSpacing(24)

        for title_text, obj_name in [
            ("昨日净值", "navYesterday"),
            ("实时估值", "navEstimated"),
            ("预计涨幅", "navChange"),
        ]:
            col = QVBoxLayout()
            t = QLabel(title_text)
            t.setObjectName("navTitle")
            col.addWidget(t)
            v = QLabel("--")
            v.setObjectName(obj_name)
            col.addWidget(v)
            nav_layout.addLayout(col)

        self.nav_yesterday_label = nav_layout.itemAt(0).layout().itemAt(1).widget()
        self.estimated_nav_label = nav_layout.itemAt(1).layout().itemAt(1).widget()
        self.change_label = nav_layout.itemAt(2).layout().itemAt(1).widget()

        info_layout.addWidget(nav_frame)
        self.content_layout.addWidget(self.info_card)

        # --- Holdings table ---
        from gui.holding_table import HoldingTable
        self.holding_table = HoldingTable()
        self.content_layout.addWidget(self.holding_table)

        # --- Charts ---
        from gui.chart_panel import ChartPanel
        self.chart_panel = ChartPanel()
        self.content_layout.addWidget(self.chart_panel)

        self.content_layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def display_fund(self, fund_detail: dict):
        self.name_label.setText(fund_detail.get("name", ""))
        self.code_label.setText(
            f"代码 {fund_detail.get('code', '')}    "
            f"类型 {fund_detail.get('fund_type', '')}"
        )

        nav_y = fund_detail.get("nav_yesterday", 0)
        self.nav_yesterday_label.setText(f"{nav_y:.4f}" if nav_y else "--")

        history = fund_detail.get("valuation_history", [])
        if history:
            latest = history[0]
            self.estimated_nav_label.setText(f"{latest['estimated_nav']:.4f}")
            change = latest["change_pct"]
            sign = "+" if change >= 0 else ""
            self.change_label.setText(f"{sign}{change:.2f}%")
            self._set_change_color(change)
        else:
            self.estimated_nav_label.setText("--")
            self.change_label.setText("--")
            self.change_label.setStyleSheet("color: #B0BEC5; font-size: 24px; font-weight: bold;")

        # Holdings
        holdings = fund_detail.get("holdings", [])
        self.holding_table.load_holdings(holdings)
        self.chart_panel.update_data(holdings)

    def update_valuation(self, valuation: dict):
        est_nav = valuation.get("estimated_nav", 0)
        change = valuation.get("change_pct", 0)

        self.estimated_nav_label.setText(f"{est_nav:.4f}")
        sign = "+" if change >= 0 else ""
        self.change_label.setText(f"{sign}{change:.2f}%")
        self._set_change_color(change)

        contributions = valuation.get("contributions", [])
        self.holding_table.update_contributions(contributions)
        self.chart_panel.update_contributions(contributions)

    def _set_change_color(self, change: float):
        if change > 0:
            color = "#FF5252"
        elif change < 0:
            color = "#69F0AE"
        else:
            color = "#B0BEC5"
        self.change_label.setStyleSheet(
            f"color: {color}; font-size: 24px; font-weight: bold;"
        )

    def clear(self):
        self.name_label.setText("请选择一只基金")
        self.code_label.setText("")
        self.nav_yesterday_label.setText("--")
        self.estimated_nav_label.setText("--")
        self.change_label.setText("--")
        self.change_label.setStyleSheet("color: #B0BEC5; font-size: 24px; font-weight: bold;")
        self.holding_table.clear()
        self.chart_panel.clear()
