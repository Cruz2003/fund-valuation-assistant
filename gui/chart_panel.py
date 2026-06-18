"""Contribution bar chart + weight pie chart via Matplotlib."""
import matplotlib
matplotlib.use("QtAgg")
# Configure CJK font — must run before any figure is created
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "KaiTi"]
matplotlib.rcParams["axes.unicode_minus"] = False
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QGroupBox, QVBoxLayout


class ChartPanel(QGroupBox):
    def __init__(self):
        super().__init__("图表分析")
        self.setObjectName("chartPanel")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 8)

        self.figure = Figure(figsize=(9, 5.5), dpi=100)
        self.figure.patch.set_facecolor("#0D1117")
        # bar chart (left) — contribution bars with stock-name y-tick labels
        self.ax_bar = self.figure.add_subplot(1, 2, 1)
        # pie chart (right) — weight distribution; legend outside on the right
        self.ax_pie = self.figure.add_subplot(1, 2, 2)
        self.figure.subplots_adjust(left=0.18, right=0.78, wspace=0.35)

        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)

    def _style_ax(self, ax):
        ax.set_facecolor("#0D1117")
        ax.tick_params(colors="#8B949E", labelsize=8)
        ax.spines["bottom"].set_color("#30363D")
        ax.spines["left"].set_color("#30363D")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.title.set_color("#E6EDF3")

    def update_data(self, holdings: list):
        self.ax_bar.clear()
        self.ax_pie.clear()

        if not holdings:
            self.canvas.draw()
            return

        # Pie: weight distribution
        labels = [h.get("stock_name", "") for h in holdings]
        weights = [h.get("weight", 0) for h in holdings]
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
                   "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9"]
        wedges, texts, autotexts = self.ax_pie.pie(
            weights, labels=None, autopct="%1.1f%%",
            colors=colors[:len(holdings)],
            startangle=90, pctdistance=0.82,
        )
        for t in autotexts:
            t.set_fontsize(7)
        self.ax_pie.legend(
            wedges, labels,
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            ncol=1, fontsize=7,
            labelcolor="#E6EDF3",
            frameon=False,
            handlelength=1.0,
        )
        self.ax_pie.set_title("持仓占比", fontsize=9, color="#E6EDF3")
        self._style_ax(self.ax_pie)

        # Bar: show empty state — contributions load after refresh
        self.ax_bar.set_title("涨跌贡献度 (%)", fontsize=9, color="#E6EDF3")
        self.ax_bar.axvline(x=0, color="#30363D", linewidth=0.8)
        self.ax_bar.text(0.5, 0.5, "等待刷新数据", transform=self.ax_bar.transAxes,
                         ha="center", va="center", fontsize=10, color="#484F58")
        self.ax_bar.set_xticks([])
        self.ax_bar.set_yticks([])
        self._style_ax(self.ax_bar)

        self.canvas.draw()

    def update_contributions(self, contributions: list):
        self.ax_bar.clear()

        if not contributions:
            self.ax_bar.text(0.5, 0.5, "暂无贡献度数据", transform=self.ax_bar.transAxes,
                             ha="center", va="center", fontsize=10, color="#484F58")
            self.ax_bar.set_xticks([])
            self.ax_bar.set_yticks([])
            self.canvas.draw()
            return

        stocks = [c["stock_name"] for c in reversed(contributions)]
        values = [c["contribution"] for c in reversed(contributions)]
        bar_colors = ["#FF5252" if v >= 0 else "#69F0AE" for v in values]

        bars = self.ax_bar.barh(stocks, values, color=bar_colors, height=0.6)
        self.ax_bar.set_title("涨跌贡献度 (%)", fontsize=9, color="#E6EDF3")
        self.ax_bar.axvline(x=0, color="#30363D", linewidth=0.8)
        self._style_ax(self.ax_bar)
        self.ax_bar.tick_params(colors="#E6EDF3", labelsize=8)

        # Auto-scale the x-axis and compute smart label offset
        self.ax_bar.relim()
        self.ax_bar.autoscale_view()
        x_range = abs(self.ax_bar.get_xlim()[1] - self.ax_bar.get_xlim()[0])
        offset = max(x_range * 0.04, 0.005)

        for bar, val in zip(bars, values):
            x_pos = bar.get_width()
            label_x = x_pos + offset if x_pos >= 0 else x_pos - offset
            self.ax_bar.text(
                label_x, bar.get_y() + bar.get_height() / 2,
                f"{val:+.2f}", va="center", fontsize=8,
                color="#E6EDF3",
                ha="left" if x_pos >= 0 else "right",
            )
        self.canvas.draw()

    def show_no_holdings(self, fund_detail: dict = None):
        """Display a message when the fund has no stock holdings (e.g. ETF feeder, bond fund)."""
        self.ax_bar.clear()
        self.ax_pie.clear()
        ftype = fund_detail.get("fund_type", "") if fund_detail else ""
        name = fund_detail.get("name", "") if fund_detail else ""

        if "ETF联接" in name or "ETF链接" in name:
            msg = "该基金为 ETF 联接基金\n主要通过投资目标 ETF 跟踪指数\n暂无直接持股数据"
        elif "QDII" in ftype or "QDII" in name:
            msg = "该基金为 QDII 基金\n暂无持仓明细数据"
        elif "债券" in ftype or "债" in name:
            msg = "该基金为债券型基金\n暂无股票持仓数据"
        else:
            msg = "暂无持仓数据"

        self.ax_pie.text(0.5, 0.5, msg, transform=self.ax_pie.transAxes,
                         ha="center", va="center", fontsize=9, color="#8B949E")
        self.ax_pie.set_title("持仓占比", fontsize=9, color="#E6EDF3")
        self._style_ax(self.ax_pie)

        self.ax_bar.text(0.5, 0.5, "暂无贡献度数据", transform=self.ax_bar.transAxes,
                         ha="center", va="center", fontsize=10, color="#484F58")
        self.ax_bar.set_xticks([])
        self.ax_bar.set_yticks([])
        self.ax_bar.set_title("涨跌贡献度 (%)", fontsize=9, color="#E6EDF3")
        self._style_ax(self.ax_bar)

        self.canvas.draw()

    def clear(self):
        self.ax_bar.clear()
        self.ax_pie.clear()
        self.ax_bar.text(0.5, 0.5, "请选择一只基金", transform=self.ax_bar.transAxes,
                         ha="center", va="center", fontsize=10, color="#484F58")
        self.ax_bar.set_xticks([])
        self.ax_bar.set_yticks([])
        self.canvas.draw()
