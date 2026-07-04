"""Zoya 4.0 Scientific Computing - Statistics module."""

import math

Number = int | float
Sequence = list[Number]


def _validate(data: Sequence) -> list[float]:
    """Validate and convert input to list of floats."""
    if not data:
        raise ValueError("Data cannot be empty")
    return [float(x) for x in data]


def mean(data: Sequence) -> float:
    """Arithmetic mean."""
    data = _validate(data)
    return sum(data) / len(data)


def median(data: Sequence) -> float:
    """Median (50th percentile)."""
    data = sorted(_validate(data))
    n = len(data)
    if n % 2 == 0:
        return (data[n // 2 - 1] + data[n // 2]) / 2
    return data[n // 2]


def mode(data: Sequence) -> list[float]:
    """Mode(s) - most frequent value(s)."""
    data = _validate(data)
    counts = {}
    for x in data:
        counts[x] = counts.get(x, 0) + 1
    max_count = max(counts.values())
    return [x for x, c in counts.items() if c == max_count]


def variance(data: Sequence, ddof: int = 0) -> float:
    """Variance (sample if ddof=1, population if ddof=0)."""
    data = _validate(data)
    n = len(data)
    if n <= ddof:
        raise ValueError("Insufficient data for variance")
    m = mean(data)
    return sum((x - m) ** 2 for x in data) / (n - ddof)


def std(data: Sequence, ddof: int = 0) -> float:
    """Standard deviation."""
    return math.sqrt(variance(data, ddof))


def percentile(data: Sequence, q: float) -> float:
    """Percentile (0-100). Linear interpolation."""
    data = sorted(_validate(data))
    n = len(data)
    if q <= 0:
        return data[0]
    if q >= 100:
        return data[-1]

    k = (n - 1) * q / 100
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return data[int(k)]
    d0 = data[f] * (c - k)
    d1 = data[c] * (k - f)
    return d0 + d1


def quantile(data: Sequence, q: float) -> float:
    """Quantile (0-1)."""
    return percentile(data, q * 100)


def iqr(data: Sequence) -> float:
    """Interquartile range."""
    return percentile(data, 75) - percentile(data, 25)


def mad(data: Sequence) -> float:
    """Median absolute deviation."""
    data = _validate(data)
    med = median(data)
    return median([abs(x - med) for x in data])


def skewness(data: Sequence) -> float:
    """Sample skewness (asymmetry measure)."""
    data = _validate(data)
    n = len(data)
    if n < 3:
        return 0
    m = mean(data)
    s = std(data, ddof=1)
    if s == 0:
        return 0
    return (n / ((n - 1) * (n - 2))) * sum(((x - m) / s) ** 3 for x in data)


def kurtosis(data: Sequence) -> float:
    """Sample excess kurtosis (peakedness measure)."""
    data = _validate(data)
    n = len(data)
    if n < 4:
        return 0
    m = mean(data)
    s = std(data, ddof=1)
    if s == 0:
        return 0
    term = sum(((x - m) / s) ** 4 for x in data)
    return (n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))) * term - 3 * (n - 1) ** 2 / (
        (n - 2) * (n - 3)
    )


def covariance(x: Sequence, y: Sequence, ddof: int = 0) -> float:
    """Covariance between two sequences."""
    x = _validate(x)
    y = _validate(y)
    if len(x) != len(y):
        raise ValueError("Sequences must be same length")
    n = len(x)
    if n <= ddof:
        raise ValueError("Insufficient data")
    mx, my = mean(x), mean(y)
    return sum((x[i] - mx) * (y[i] - my) for i in range(n)) / (n - ddof)


def correlation(x: Sequence, y: Sequence) -> float:
    """Pearson correlation coefficient."""
    x = _validate(x)
    y = _validate(y)
    if len(x) != len(y):
        raise ValueError("Sequences must be same length")
    n = len(x)
    if n == 0:
        return 0

    mx, my = mean(x), mean(y)
    num = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    den_x = sum((xi - mx) ** 2 for xi in x)
    den_y = sum((yi - my) ** 2 for yi in y)

    if den_x == 0 or den_y == 0:
        return 0
    return num / math.sqrt(den_x * den_y)


def spearman_correlation(x: Sequence, y: Sequence) -> float:
    """Spearman rank correlation."""
    x = _validate(x)
    y = _validate(y)
    if len(x) != len(y):
        raise ValueError("Sequences must be same length")

    def ranks(seq):
        sorted_indices = sorted(range(len(seq)), key=lambda i: seq[i])
        r = [0] * len(seq)
        for i, idx in enumerate(sorted_indices):
            r[idx] = i + 1
        for i in range(len(seq)):
            ties = sum(1 for j in range(len(seq)) if seq[j] == seq[i])
            if ties > 1:
                r[i] = sum(r[j] for j in range(len(seq)) if seq[j] == seq[i]) / ties
        return r

    rx = ranks(x)
    ry = ranks(y)
    return correlation(rx, ry)


def linear_regression(x: Sequence, y: Sequence) -> tuple[float, float]:
    """Simple linear regression: y = a + bx. Returns (a, b)."""
    n = len(x)
    if n == 0:
        raise ValueError("Insufficient data")

    mx = sum(x) / n
    my = sum(y) / n

    num = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    den = sum((x[i] - mx) ** 2 for i in range(n))

    if den == 0:
        raise ValueError("Zero variance in x")

    b = num / den
    a = my - b * mx

    return a, b


def z_score(data: Sequence) -> list[float]:
    """Standardize to z-scores."""
    data = _validate(data)
    m, s = mean(data), std(data, ddof=1)
    if s == 0:
        return [0.0] * len(data)
    return [(x - m) / s for x in data]


def standardize(data: Sequence) -> list[float]:
    """Standardize to zero mean, unit variance."""
    return z_score(data)


def min_max_scale(
    data: Sequence, feature_range: tuple[float, float] = (0, 1)
) -> list[float]:
    """Min-max scaling."""
    data = _validate(data)
    mn, mx = min(data), max(data)
    if mx == mn:
        return [feature_range[0]] * len(data)
    a, b = feature_range
    return [a + (x - mn) * (b - a) / (mx - mn) for x in data]


def outlier_bounds(data: Sequence, k: float = 1.5) -> tuple[float, float]:
    """Tukey's fence for outlier detection."""
    q1, q3 = percentile(data, 25), percentile(data, 75)
    i = iqr(data)
    return (q1 - k * i, q3 + k * i)


def outliers(data: Sequence, k: float = 1.5) -> list[float]:
    """Find outliers using Tukey's fence."""
    data = _validate(data)
    lower, upper = outlier_bounds(data, k)
    return [x for x in data if x < lower or x > upper]


def describe(data: Sequence) -> dict:
    """Summary statistics."""
    data = _validate(data)
    return {
        "count": len(data),
        "mean": mean(data),
        "std": std(data, ddof=1),
        "min": min(data),
        "25%": percentile(data, 25),
        "50%": median(data),
        "75%": percentile(data, 75),
        "max": max(data),
        "variance": variance(data, ddof=1),
        "skewness": skewness(data),
        "kurtosis": kurtosis(data),
    }
