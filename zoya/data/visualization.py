from .dataframe import Series


class VisualizationError(Exception):
    pass


_STYLE = {
    "line": "─",
    "bar_fill": "█",
    "bar_empty": "░",
    "point": "*",
    "axis": "│",
    "corner": "└",
    "cross": "┼",
    "hbar_fill": "█",
    "hbar_empty": "░",
    "colors": {
        "default": "",
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "reset": "\033[0m",
    },
    "use_color": False,
}


def set_style(style: dict):
    _STYLE.update(style)


class Figure:
    def __init__(self, title: str = "", width: int = 60, height: int = 20):
        self.title = title
        self.width = width
        self.height = height

    def show(self) -> str:
        lines = []
        if self.title:
            lines.append(self.title.center(self.width))
            lines.append("")
        return "\n".join(lines)


class Plot:
    @staticmethod
    def _auto_scale(values, width: int) -> tuple:
        vmin = min(values)
        vmax = max(values)
        if vmax == vmin:
            return vmin, vmax, [0.5] * len(values)
        scaled = [(v - vmin) / (vmax - vmin) * (width - 1) for v in values]
        return vmin, vmax, scaled

    @staticmethod
    def _format_axis_label(v: float) -> str:
        if abs(v) >= 1e6:
            return f"{v / 1e6:.1f}M"
        if abs(v) >= 1e3:
            return f"{v / 1e3:.1f}K"
        if v == int(v):
            return str(int(v))
        return f"{v:.2f}"

    @staticmethod
    def line(x: Series, y: Series, label: str = "") -> str:
        if len(x) != len(y):
            raise VisualizationError("x and y must have same length")

        width = 60
        height = 16
        xs = list(x)
        ys = list(y)

        pairs = sorted(zip(xs, ys, strict=False), key=lambda p: p[0])
        xs_sorted = [p[0] for p in pairs]
        ys_sorted = [p[1] for p in pairs]

        ymin, ymax, yscaled = Plot._auto_scale(ys_sorted, height)
        xmin, xmax, xscaled = Plot._auto_scale(xs_sorted, width)

        grid = [[" " for _ in range(width + 1)] for _ in range(height)]

        for i in range(len(xs_sorted)):
            col = min(int(xscaled[i]), width - 1)
            row = max(0, min(height - 1 - int(yscaled[i]), height - 1))
            grid[row][col] = _STYLE["point"]

        segments = _STYLE["line"]
        for i in range(len(xs_sorted) - 1):
            x1 = min(int(xscaled[i]), width - 1)
            y1 = max(0, min(height - 1 - int(yscaled[i]), height - 1))
            x2 = min(int(xscaled[i + 1]), width - 1)
            y2 = max(0, min(height - 1 - int(yscaled[i + 1]), height - 1))
            if x1 == x2:
                for r in range(min(y1, y2), max(y1, y2) + 1):
                    if grid[r][x1] == " ":
                        grid[r][x1] = segments
            elif y1 == y2:
                for c in range(min(x1, x2), max(x1, x2) + 1):
                    if grid[y1][c] == " ":
                        grid[y1][c] = segments
            else:
                steps = max(abs(x2 - x1), abs(y2 - y1))
                for s in range(steps + 1):
                    t = s / steps if steps else 0
                    c = int(x1 + t * (x2 - x1))
                    r = int(y1 + t * (y2 - y1))
                    if grid[r][c] == " ":
                        grid[r][c] = segments

        for i in range(len(xs_sorted)):
            col = min(int(xscaled[i]), width - 1)
            row = max(0, min(height - 1 - int(yscaled[i]), height - 1))
            grid[row][col] = _STYLE["point"]

        lines = []
        if label:
            lines.append(f"Line: {label}")
        lines.append(f"y: {Plot._format_axis_label(ymax)}")
        for r in range(height):
            row_str = "".join(grid[r])
            y_val = ymax - (r / (height - 1)) * (ymax - ymin) if height > 1 else ymin
            label_str = Plot._format_axis_label(y_val) if r % 4 == 0 else ""
            lines.append(f"{_STYLE['axis']} {row_str}  {label_str}".rstrip())
        lines.append(f"{_STYLE['corner']}{_STYLE['line'] * width}")
        lines.append(
            f"x: {Plot._format_axis_label(xmin)} {' ' * (width - 10)} {Plot._format_axis_label(xmax)}"
        )
        return "\n".join(lines)

    @staticmethod
    def bar(x: list[str], y: list[float], title: str = "") -> str:
        if len(x) == 0:
            raise VisualizationError("No data to plot")

        max_width = 50
        max_val = max(y) if y else 1
        if max_val == 0:
            max_val = 1

        lines = []
        if title:
            lines.append(title)
            lines.append("")

        max_label_len = max(len(str(label)) for label in x)
        for label, val in zip(x, y, strict=False):
            bar_len = int((val / max_val) * max_width) if max_val else 0
            bar_str = _STYLE["hbar_fill"] * bar_len + _STYLE["hbar_empty"] * (
                max_width - bar_len
            )
            val_str = Plot._format_axis_label(val)
            lines.append(f"  {str(label).ljust(max_label_len)} |{bar_str} {val_str}")

        lines.append(f"  {' ' * max_label_len} {'─' * (max_width + 2)}")
        lines.append(
            f"  {' ' * max_label_len}  0{' ' * (max_width - 6)}{Plot._format_axis_label(max_val)}"
        )
        return "\n".join(lines)

    @staticmethod
    def histogram(data: Series, bins: int = 10, title: str = "") -> str:
        vals = [v for v in data.values if v is not None]
        if not vals:
            raise VisualizationError("No data for histogram")

        vmin = min(vals)
        vmax = max(vals)
        if vmin == vmax:
            vmax = vmin + 1

        bin_width = (vmax - vmin) / bins
        bin_edges = [vmin + i * bin_width for i in range(bins + 1)]
        counts = [0] * bins
        for v in vals:
            idx = min(int((v - vmin) / bin_width), bins - 1)
            counts[idx] += 1

        max_count = max(counts)
        max_width = 40

        lines = []
        if title:
            lines.append(title)
            lines.append("")

        for i in range(bins):
            bar_len = int((counts[i] / max_count) * max_width) if max_count else 0
            bar = _STYLE["hbar_fill"] * bar_len
            lo = Plot._format_axis_label(bin_edges[i])
            hi = Plot._format_axis_label(bin_edges[i + 1])
            lines.append(f"  [{lo:>8} - {hi:<8}] |{bar} {counts[i]}")

        lines.append(f"  {' ' * 22} {'─' * (max_width + 2)}")
        lines.append(f"  {' ' * 22}  0{' ' * (max_width - 4)}{max_count}")
        return "\n".join(lines)

    @staticmethod
    def scatter(x: Series, y: Series, title: str = "") -> str:
        if len(x) != len(y):
            raise VisualizationError("x and y must have same length")

        width = 50
        height = 16
        xs = list(x)
        ys = list(y)

        ymin, ymax, yscaled = Plot._auto_scale(ys, height)
        xmin, xmax, xscaled = Plot._auto_scale(xs, width)

        grid = [[" " for _ in range(width)] for _ in range(height)]

        for xi, yi in zip(xs, ys, strict=False):
            col = min(
                (
                    int((xi - xmin) / (xmax - xmin) * (width - 1))
                    if xmax != xmin
                    else width // 2
                ),
                width - 1,
            )
            row = max(
                0,
                min(
                    (
                        height - 1 - int((yi - ymin) / (ymax - ymin) * (height - 1))
                        if ymax != ymin
                        else height // 2
                    ),
                    height - 1,
                ),
            )
            grid[row][col] = _STYLE["point"]

        lines = []
        if title:
            lines.append(title)
        lines.append(f"y: {Plot._format_axis_label(ymax)}")
        for r in range(height):
            row_str = "".join(grid[r])
            y_val = ymax - (r / (height - 1)) * (ymax - ymin) if height > 1 else ymin
            label_str = Plot._format_axis_label(y_val) if r % 4 == 0 else ""
            lines.append(f"{_STYLE['axis']} {row_str}  {label_str}".rstrip())
        lines.append(f"{_STYLE['corner']}{_STYLE['line'] * width}")
        lines.append(
            f"x: {Plot._format_axis_label(xmin)} {' ' * (width - 10)} {Plot._format_axis_label(xmax)}"
        )
        return "\n".join(lines)

    @staticmethod
    def pie(labels: list[str], values: list[float], title: str = "") -> str:
        if not labels or not values:
            raise VisualizationError("No data for pie chart")
        if len(labels) != len(values):
            raise VisualizationError("labels and values must have same length")

        total = sum(values)
        if total == 0:
            raise VisualizationError("Values sum to zero")

        # Unicode pie chart blocks: ▏▎▍▌▋▊▉█
        blocks = [" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]
        pct = [v / total * 100 for v in values]

        lines = []
        if title:
            lines.append(title)
            lines.append("")

        # Horizontal stacked bar as pie representation
        width = 30
        bars = []
        for v in values:
            frac = v / total
            count = frac * width
            full = int(count)
            partial = int((count - full) * 8)
            bars.append(full * "█" + (blocks[partial] if partial else ""))
        bar_line = "".join(bars).ljust(width, "░")
        lines.append(f"  {bar_line}")
        lines.append("")

        # Legend
        max_label_len = max(len(str(l)) for l in labels)
        for label, val, p in zip(labels, values, pct, strict=False):
            bar = _STYLE["hbar_fill"]
            lines.append(
                f"  {bar} {str(label).ljust(max_label_len)}  {Plot._format_axis_label(val)} ({p:.1f}%)"
            )

        lines.append(f"  {'─' * (max_label_len + 16)}")
        lines.append(f"  Total: {Plot._format_axis_label(total)}")
        return "\n".join(lines)
