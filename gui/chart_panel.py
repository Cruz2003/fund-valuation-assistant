"""Contribution bar chart + weight pie chart via Matplotlib."""
import matplotlib
matplotlib.use("QtAgg")
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

        self.figure = Figure(figsize=(8, 4.5), dpi=100)
        self.figure.patch.set_facecolor("#0D1117")
        self.ax_bar = self.figure.add_subplot(1, 2, 1)
        self.ax_pie = self.figure.add_subplot(1, 2, 2)
        self.figure.tight_layout(pad=3.0)

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
        self.ax_pie.legend(wedges, labels, loc="lower center",
                           ncol=2, fontsize=7,
                           labelcolor="#8B949E", frameon=False)
        self.ax_pie.set_title("持仓占比", fontsize=9, color="#E6EDF3")
        self._style_ax(self.ax_pie)

        # Bar: placeholder
        stocks = [h.get("stock_name", "") for h in holdings]
        self.ax_bar.barh(stocks, [0] * len(stocks), color="#21262D", height=0.5)
        self.ax_bar.set_title("涨跌贡献度 (%)", fontsize=9, color="#E6EDF3")
        self.ax_bar.axvline(x=0, color="#30363D", linewidth=0.8)
        self._style_ax(self.ax_bar)
        self.ax_bar.tick_params(colors="#E6EDF3", labelsize=8)

        self.canvas.draw()

    def update_contributions(self, contributions: list):
        self.ax_bar.clear()

        if not contributions:
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

        for bar, val in zip(bars, values):
            x_pos = bar.get_width()
            label_x = x_pos + 0.01 if x_pos >= 0 else x_pos - 0.08
            self.ax_bar.text(
                label_x, bar.get_y() + bar.get_height() / 2,
                f"{val:+.2f}", va="center", fontsize=8,
                color="#E6EDF3",
                ha="left" if x_pos >= 0 else "right",
            )
        self.canvas.draw()

    def clear(self):
        self.ax_bar.clear()
        self.ax_pie.clear()
        self.canvas.draw()
