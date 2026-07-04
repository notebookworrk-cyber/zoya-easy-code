"""Zoya 4.0 Scientific Computing module.

Provides matrix operations, linear algebra, statistics, optimization, and ML primitives.
"""

from zoya.stdlib.scientific.linear import (
    add,
    cross,
    # Linear algebra
    det,
    dot,
    eig,
    identity,
    inv,
    mat_pow,
    matmul,
    matvec,
    norm,
    qr,
    rank,
    scale,
    solve,
    sub,
    svd,
    trace,
    transpose,
    # Vector operations
    v_add,
    v_corr,
    v_div,
    v_mean,
    v_mul,
    v_scale,
    v_std,
    v_sub,
    v_sum,
    v_var,
    # Matrix operations
    zeros,
)
from zoya.stdlib.scientific.ml import (
    DecisionTreeClassifier,
    GaussianNB,
    KMeans,
    LassoRegression,
    LinearRegression,
    LogisticRegression,
    RandomForestClassifier,
    RidgeRegression,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    train_test_split,
)
from zoya.stdlib.scientific.optimization import (
    adam,
    conjugate_gradient,
    gradient_descent,
    lbfgs,
    line_search,
    minimize,
    nelder_mead,
    newton_method,
    newton_method_nd,
)
from zoya.stdlib.scientific.statistics import (
    correlation,
    covariance,
    describe,
    iqr,
    kurtosis,
    linear_regression,
    mad,
    mean,
    median,
    # Aliases
    min_max_scale,
    mode,
    outlier_bounds,
    outliers,
    percentile,
    quantile,
    skewness,
    spearman_correlation,
    standardize,
    std,
    variance,
    z_score,
)

# Type aliases
Matrix = list[list[float]]
Vector = list[float]

__all__ = [
    # Linear algebra
    "zeros",
    "identity",
    "transpose",
    "matmul",
    "matvec",
    "add",
    "sub",
    "scale",
    "trace",
    "rank",
    "mat_pow",
    "norm",
    "dot",
    "cross",
    "det",
    "inv",
    "solve",
    "eig",
    "svd",
    "qr",
    "v_add",
    "v_sub",
    "v_mul",
    "v_div",
    "v_scale",
    "v_sum",
    "v_mean",
    "v_std",
    "v_var",
    "v_corr",
    # Statistics
    "mean",
    "median",
    "mode",
    "variance",
    "std",
    "percentile",
    "quantile",
    "iqr",
    "mad",
    "skewness",
    "kurtosis",
    "covariance",
    "correlation",
    "spearman_correlation",
    "linear_regression",
    "z_score",
    "standardize",
    "describe",
    "min_max_scale",
    "outlier_bounds",
    "outliers",
    # Optimization
    "gradient_descent",
    "adam",
    "lbfgs",
    "newton_method",
    "newton_method_nd",
    "line_search",
    "conjugate_gradient",
    "nelder_mead",
    "minimize",
    # ML
    "LinearRegression",
    "RidgeRegression",
    "LassoRegression",
    "LogisticRegression",
    "KMeans",
    "GaussianNB",
    "DecisionTreeClassifier",
    "RandomForestClassifier",
    "train_test_split",
    "accuracy_score",
    "precision_score",
    "recall_score",
    "f1_score",
    "confusion_matrix",
    "classification_report",
    # Types
    "Matrix",
    "Vector",
]


# Convenience functions for Zoya script integration
def matrix(data: list[list[float]]) -> list[list[float]]:
    """Create a matrix (identity for type checking)."""
    return data


def vector(data: list[float]) -> list[float]:
    """Create a vector."""
    return data


def linspace(start: float, stop: float, num: int) -> list[float]:
    """Evenly spaced numbers."""
    if num == 1:
        return [start]
    step = (stop - start) / (num - 1)
    return [start + i * step for i in range(num)]


def arange(start: float, stop: float, step: float = 1.0) -> list[float]:
    """Range with floats."""
    result = []
    x = start
    while x < stop:
        result.append(x)
        x += step
    return result


def random_matrix(
    rows: int, cols: int, low: float = 0.0, high: float = 1.0, seed: int = None
) -> Matrix:
    """Random matrix."""
    import random

    if seed is not None:
        random.seed(seed)
    return [[random.uniform(low, high) for _ in range(cols)] for _ in range(rows)]


def random_vector(
    n: int, low: float = 0.0, high: float = 1.0, seed: int = None
) -> Vector:
    """Random vector."""
    import random

    if seed is not None:
        random.seed(seed)
    return [random.uniform(low, high) for _ in range(n)]
