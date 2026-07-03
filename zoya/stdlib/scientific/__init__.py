"""Zoya 4.0 Scientific Computing module.

Provides matrix operations, linear algebra, statistics, optimization, and ML primitives.
"""

from zoya.stdlib.scientific.linear import (
    # Matrix operations
    zeros, identity, transpose, matmul, matvec,
    add, sub, scale, trace, rank, mat_pow, norm,
    dot, cross,
    # Linear algebra
    det, inv, solve, eig, svd, qr,
    # Vector operations
    v_add, v_sub, v_mul, v_div, v_scale, v_sum, v_mean, v_std, v_var, v_corr,
    v_norm,
)

from zoya.stdlib.scientific.statistics import (
    mean, median, mad, mode, variance, std, percentile, quantile,
    iqr, skewness, kurtosis, covariance, correlation, spearman_correlation,
    linear_regression, z_score, standardize,
    describe,
    # Aliases
    min_max_scale, outlier_bounds, outliers,
)

from zoya.stdlib.scientific.optimization import (
    gradient_descent, adam, lbfgs, newton_method, newton_method_nd,
    line_search, conjugate_gradient, nelder_mead, minimize,
)

from zoya.stdlib.scientific.ml import (
    LinearRegression, RidgeRegression, LassoRegression,
    LogisticRegression, KMeans, GaussianNB,
    DecisionTreeClassifier, RandomForestClassifier,
    train_test_split, accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, classification_report,
)

from typing import List
# Type aliases
Matrix = List[List[float]]
Vector = List[float]

__all__ = [
    # Linear algebra
    "zeros", "identity", "transpose", "matmul", "matvec",
    "add", "sub", "scale", "trace", "rank", "mat_pow", "norm",
    "dot", "cross", "det", "inv", "solve", "eig", "svd", "qr",
    "v_add", "v_sub", "v_mul", "v_div", "v_scale", "v_sum", "v_mean", "v_std", "v_var", "v_corr",
    # Statistics
    "mean", "median", "mode", "variance", "std", "percentile", "quantile",
    "iqr", "mad", "skewness", "kurtosis", "covariance", "correlation",
    "spearman_correlation", "linear_regression", "z_score", "standardize",
    "describe",
    "min_max_scale", "outlier_bounds", "outliers",
    # Optimization
    "gradient_descent", "adam", "lbfgs", "newton_method", "newton_method_nd",
    "line_search", "conjugate_gradient", "nelder_mead", "minimize",
    # ML
    "LinearRegression", "RidgeRegression", "LassoRegression",
    "LogisticRegression", "KMeans", "GaussianNB",
    "DecisionTreeClassifier", "RandomForestClassifier",
    "train_test_split", "accuracy_score", "precision_score", "recall_score",
    "f1_score", "confusion_matrix", "classification_report",
    # Types
    "Matrix", "Vector",
]

# Convenience functions for Zoya script integration
def matrix(data: List[List[float]]) -> List[List[float]]:
    """Create a matrix (identity for type checking)."""
    return data


def vector(data: List[float]) -> List[float]:
    """Create a vector."""
    return data


def linspace(start: float, stop: float, num: int) -> List[float]:
    """Evenly spaced numbers."""
    if num == 1:
        return [start]
    step = (stop - start) / (num - 1)
    return [start + i * step for i in range(num)]


def arange(start: float, stop: float, step: float = 1.0) -> List[float]:
    """Range with floats."""
    result = []
    x = start
    while x < stop:
        result.append(x)
        x += step
    return result


def random_matrix(rows: int, cols: int, low: float = 0.0, high: float = 1.0, seed: int = None) -> Matrix:
    """Random matrix."""
    import random
    if seed is not None:
        random.seed(seed)
    return [[random.uniform(low, high) for _ in range(cols)] for _ in range(rows)]


def random_vector(n: int, low: float = 0.0, high: float = 1.0, seed: int = None) -> Vector:
    """Random vector."""
    import random
    if seed is not None:
        random.seed(seed)
    return [random.uniform(low, high) for _ in range(n)]