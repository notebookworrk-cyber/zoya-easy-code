import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import math
import unittest

from zoya.stdlib.scientific import linear, ml
from zoya.stdlib.scientific import optimization as opt
from zoya.stdlib.scientific import statistics as stats

# =============================================================================
# Linear Algebra Tests
# =============================================================================


class TestMatrixConstruction(unittest.TestCase):
    """zeros, identity"""

    def test_zeros_default(self):
        m = linear.zeros(3)
        self.assertEqual(len(m), 3)
        self.assertEqual(len(m[0]), 3)
        self.assertEqual(m, [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])

    def test_zeros_rectangular(self):
        m = linear.zeros(2, 3)
        self.assertEqual(len(m), 2)
        self.assertEqual(len(m[0]), 3)
        self.assertEqual(m, [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])

    def test_zeros_empty(self):
        m = linear.zeros(0)
        self.assertEqual(m, [])

    def test_identity_2x2(self):
        I = linear.identity(2)
        self.assertEqual(I, [[1.0, 0.0], [0.0, 1.0]])

    def test_identity_3x3(self):
        I = linear.identity(3)
        self.assertEqual(I[0][0], 1.0)
        self.assertEqual(I[1][1], 1.0)
        self.assertEqual(I[2][2], 1.0)
        self.assertEqual(I[0][1], 0.0)
        self.assertEqual(I[1][0], 0.0)

    def test_identity_1x1(self):
        I = linear.identity(1)
        self.assertEqual(I, [[1.0]])


class TestMatrixArithmetic(unittest.TestCase):
    """transpose, matmul, matvec, add, sub, scale"""

    def setUp(self):
        self.A = [[1.0, 2.0], [3.0, 4.0]]
        self.B = [[5.0, 6.0], [7.0, 8.0]]
        self.v = [1.0, 2.0]

    def test_transpose(self):
        T = linear.transpose(self.A)
        self.assertEqual(T, [[1.0, 3.0], [2.0, 4.0]])

    def test_transpose_empty(self):
        self.assertEqual(linear.transpose([]), [])

    def test_transpose_rectangular(self):
        m = [[1.0, 2.0, 3.0]]
        self.assertEqual(linear.transpose(m), [[1.0], [2.0], [3.0]])

    def test_matmul(self):
        result = linear.matmul(self.A, self.B)
        self.assertAlmostEqual(result[0][0], 19.0)  # 1*5 + 2*7
        self.assertAlmostEqual(result[0][1], 22.0)  # 1*6 + 2*8
        self.assertAlmostEqual(result[1][0], 43.0)  # 3*5 + 4*7
        self.assertAlmostEqual(result[1][1], 50.0)  # 3*6 + 4*8

    def test_matmul_dim_mismatch(self):
        with self.assertRaises(ValueError):
            linear.matmul(self.A, [[1.0, 2.0, 3.0]])

    def test_matmul_empty(self):
        self.assertEqual(linear.matmul([], [[1.0]]), [])
        self.assertEqual(linear.matmul([[1.0]], []), [])

    def test_matmul_identity(self):
        I = linear.identity(2)
        result = linear.matmul(self.A, I)
        self.assertEqual(result, self.A)

    def test_matvec(self):
        result = linear.matvec(self.A, self.v)
        self.assertEqual(result, [5.0, 11.0])  # [1+4, 3+8]

    def test_matvec_dim_mismatch(self):
        with self.assertRaises(ValueError):
            linear.matvec(self.A, [1.0, 2.0, 3.0])

    def test_matvec_empty(self):
        self.assertEqual(linear.matvec([], [1.0]), [])
        self.assertEqual(linear.matvec([[1.0]], []), [])

    def test_add(self):
        result = linear.add(self.A, self.B)
        self.assertEqual(result, [[6.0, 8.0], [10.0, 12.0]])

    def test_add_dim_mismatch(self):
        with self.assertRaises(ValueError):
            linear.add(self.A, [[1.0]])

    def test_sub(self):
        result = linear.sub(self.A, self.B)
        self.assertEqual(result, [[-4.0, -4.0], [-4.0, -4.0]])

    def test_scale(self):
        result = linear.scale(self.A, 2.0)
        self.assertEqual(result, [[2.0, 4.0], [6.0, 8.0]])

    def test_scale_zero(self):
        result = linear.scale(self.A, 0.0)
        self.assertEqual(result, [[0.0, 0.0], [0.0, 0.0]])


class TestDeterminant(unittest.TestCase):
    """det"""

    def test_det_1x1(self):
        self.assertAlmostEqual(linear.det([[5.0]]), 5.0)

    def test_det_2x2(self):
        self.assertAlmostEqual(linear.det([[1.0, 2.0], [3.0, 4.0]]), -2.0)

    def test_det_3x3(self):
        A = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 10.0]]
        self.assertAlmostEqual(linear.det(A), -3.0)

    def test_det_singular(self):
        A = [[1.0, 2.0], [2.0, 4.0]]
        self.assertAlmostEqual(linear.det(A), 0.0)

    def test_det_identity(self):
        self.assertAlmostEqual(linear.det(linear.identity(4)), 1.0)

    def test_det_non_square(self):
        with self.assertRaises(ValueError):
            linear.det([[1.0, 2.0]])


class TestInverseAndSolve(unittest.TestCase):
    """inv, solve"""

    def test_inv_2x2(self):
        A = [[4.0, 7.0], [2.0, 6.0]]
        Ainv = linear.inv(A)
        I = linear.matmul(A, Ainv)
        self.assertAlmostEqual(I[0][0], 1.0, places=10)
        self.assertAlmostEqual(I[0][1], 0.0, places=10)
        self.assertAlmostEqual(I[1][0], 0.0, places=10)
        self.assertAlmostEqual(I[1][1], 1.0, places=10)

    def test_inv_1x1(self):
        self.assertEqual(linear.inv([[5.0]]), [[0.2]])

    def test_inv_singular(self):
        with self.assertRaises(ValueError):
            linear.inv([[1.0, 2.0], [2.0, 4.0]])

    def test_solve_2x2(self):
        A = [[3.0, 1.0], [1.0, 2.0]]
        b = [9.0, 8.0]
        x = linear.solve(A, b)
        self.assertAlmostEqual(x[0], 2.0, places=10)
        self.assertAlmostEqual(x[1], 3.0, places=10)

    def test_solve_3x3(self):
        A = [[3.0, 1.0, -1.0], [1.0, 4.0, 1.0], [2.0, 1.0, 2.0]]
        b = [4.0, 4.0, 5.0]
        x = linear.solve(A, b)
        residual = [sum(A[i][j] * x[j] for j in range(3)) - b[i] for i in range(3)]
        for r in residual:
            self.assertAlmostEqual(r, 0.0, places=10)

    def test_solve_singular(self):
        with self.assertRaises(ValueError):
            linear.solve([[1.0, 2.0], [2.0, 4.0]], [1.0, 2.0])

    def test_solve_dim_mismatch(self):
        with self.assertRaises(ValueError):
            linear.solve([[1.0, 2.0], [3.0, 4.0]], [1.0, 2.0, 3.0])


class TestEigenQR(unittest.TestCase):
    """eig, qr, qr_decomp"""

    def test_eig_2x2_diagonal(self):
        vals, vecs = linear.eig([[2.0, 0.0], [0.0, 3.0]])
        self.assertAlmostEqual(vals[0], 2.0, places=5)
        self.assertAlmostEqual(vals[1], 3.0, places=5)

    def test_qr_2x2(self):
        A = [[1.0, 2.0], [3.0, 4.0]]
        Q, R = linear.qr(A)
        QtQ = linear.matmul(linear.transpose(Q), Q)
        self.assertAlmostEqual(QtQ[0][0], 1.0, places=10)
        self.assertAlmostEqual(QtQ[1][1], 1.0, places=10)
        QR = linear.matmul(Q, R)
        for i in range(2):
            for j in range(2):
                self.assertAlmostEqual(QR[i][j], A[i][j], places=10)

    def test_qr_decomp_alias(self):
        A = [[1.0, 0.0], [0.0, 1.0]]
        Q1, R1 = linear.qr(A)
        Q2, R2 = linear.qr_decomp(A)
        self.assertEqual(Q1, Q2)
        self.assertEqual(R1, R2)

    def test_qr_3x3(self):
        A = [[12.0, -51.0, 4.0], [6.0, 167.0, -68.0], [-4.0, 24.0, -41.0]]
        Q, R = linear.qr(A)
        QR = linear.matmul(Q, R)
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(QR[i][j], A[i][j], places=10)


class TestNormsAndProducts(unittest.TestCase):
    """norm, dot, cross, trace, rank, mat_pow"""

    def test_norm_l2(self):
        self.assertAlmostEqual(linear.norm([3.0, 4.0]), 5.0)

    def test_norm_l1(self):
        self.assertAlmostEqual(linear.norm([1.0, -2.0, 3.0], p=1), 6.0)

    def test_norm_inf(self):
        self.assertAlmostEqual(linear.norm([1.0, -5.0, 3.0], p=float("inf")), 5.0)

    def test_norm_l3(self):
        n = linear.norm([2.0, 2.0, 2.0], p=3)
        self.assertAlmostEqual(n, (8 + 8 + 8) ** (1 / 3), places=10)

    def test_dot(self):
        self.assertAlmostEqual(linear.dot([1.0, 2.0, 3.0], [4.0, 5.0, 6.0]), 32.0)

    def test_dot_orthogonal(self):
        self.assertAlmostEqual(linear.dot([1.0, 0.0], [0.0, 1.0]), 0.0)

    def test_cross(self):
        result = linear.cross([1.0, 0.0, 0.0], [0.0, 1.0, 0.0])
        self.assertEqual(result, [0.0, 0.0, 1.0])

    def test_cross_non_3d(self):
        with self.assertRaises(ValueError):
            linear.cross([1.0, 0.0], [0.0, 1.0])

    def test_trace(self):
        self.assertAlmostEqual(linear.trace([[1.0, 2.0], [3.0, 4.0]]), 5.0)

    def test_trace_1x1(self):
        self.assertAlmostEqual(linear.trace([[7.0]]), 7.0)

    def test_rank_full(self):
        A = [[1.0, 2.0], [3.0, 4.0]]
        self.assertEqual(linear.rank(A), 2)

    def test_rank_singular(self):
        A = [[1.0, 2.0], [2.0, 4.0]]
        self.assertEqual(linear.rank(A), 1)

    def test_rank_zero_matrix(self):
        A = [[0.0, 0.0], [0.0, 0.0]]
        self.assertEqual(linear.rank(A), 0)

    def test_rank_rectangular(self):
        A = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        self.assertEqual(linear.rank(A), 2)

    def test_rank_empty(self):
        self.assertEqual(linear.rank([]), 0)

    def test_mat_pow_zero(self):
        A = [[1.0, 2.0], [3.0, 4.0]]
        result = linear.mat_pow(A, 0)
        self.assertEqual(result, linear.identity(2))

    def test_mat_pow_two(self):
        A = [[1.0, 2.0], [3.0, 4.0]]
        A2 = linear.mat_pow(A, 2)
        expected = linear.matmul(A, A)
        for i in range(2):
            for j in range(2):
                self.assertAlmostEqual(A2[i][j], expected[i][j])


class TestVectorOps(unittest.TestCase):
    """v_add, v_sub, v_mul, v_div, v_scale, v_sum, v_mean, v_std, v_var, v_corr, v_norm"""

    def test_v_add(self):
        self.assertEqual(linear.v_add([1.0, 2.0], [3.0, 4.0]), [4.0, 6.0])

    def test_v_sub(self):
        self.assertEqual(linear.v_sub([5.0, 7.0], [2.0, 3.0]), [3.0, 4.0])

    def test_v_mul(self):
        self.assertEqual(linear.v_mul([2.0, 3.0], [4.0, 5.0]), [8.0, 15.0])

    def test_v_div(self):
        self.assertEqual(linear.v_div([6.0, 15.0], [2.0, 3.0]), [3.0, 5.0])

    def test_v_scale(self):
        self.assertEqual(linear.v_scale([1.0, 2.0, 3.0], 2.0), [2.0, 4.0, 6.0])

    def test_v_sum(self):
        self.assertAlmostEqual(linear.v_sum([1.0, 2.0, 3.0]), 6.0)

    def test_v_mean(self):
        self.assertAlmostEqual(linear.v_mean([2.0, 4.0, 6.0]), 4.0)

    def test_v_mean_empty(self):
        self.assertEqual(linear.v_mean([]), 0.0)

    def test_v_var(self):
        v = [1.0, 3.0]
        self.assertAlmostEqual(linear.v_var(v), 1.0)

    def test_v_std_single(self):
        self.assertEqual(linear.v_std([5.0]), 0.0)

    def test_v_corr_perfect(self):
        a = [1.0, 2.0, 3.0]
        b = [2.0, 4.0, 6.0]
        self.assertAlmostEqual(linear.v_corr(a, b), 1.0)

    def test_v_corr_negative(self):
        a = [1.0, 2.0, 3.0]
        b = [3.0, 2.0, 1.0]
        self.assertAlmostEqual(linear.v_corr(a, b), -1.0)

    def test_v_corr_constant(self):
        a = [1.0, 1.0, 1.0]
        b = [2.0, 4.0, 6.0]
        self.assertEqual(linear.v_corr(a, b), 0.0)

    def test_v_corr_length_mismatch(self):
        with self.assertRaises(ValueError):
            linear.v_corr([1.0, 2.0], [1.0, 2.0, 3.0])

    def test_v_norm(self):
        self.assertAlmostEqual(linear.v_norm([3.0, 4.0]), 5.0)

    def test_v_norm_is_norm(self):
        self.assertIs(linear.v_norm, linear.norm)


class TestSVDRaises(unittest.TestCase):
    def test_svd_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            linear.svd([[1.0, 0.0], [0.0, 1.0]])


# =============================================================================
# Statistics Tests
# =============================================================================


class TestCentralTendency(unittest.TestCase):
    """mean, median, mode, mad"""

    def test_mean_basic(self):
        self.assertAlmostEqual(stats.mean([1.0, 2.0, 3.0, 4.0, 5.0]), 3.0)

    def test_mean_single(self):
        self.assertAlmostEqual(stats.mean([42.0]), 42.0)

    def test_mean_empty_error(self):
        with self.assertRaises(ValueError):
            stats.mean([])

    def test_median_odd(self):
        self.assertAlmostEqual(stats.median([5.0, 1.0, 3.0]), 3.0)

    def test_median_even(self):
        self.assertAlmostEqual(stats.median([1.0, 2.0, 3.0, 4.0]), 2.5)

    def test_median_single(self):
        self.assertAlmostEqual(stats.median([7.0]), 7.0)

    def test_mode_single(self):
        self.assertEqual(stats.mode([1.0, 1.0, 2.0, 3.0]), [1.0])

    def test_mode_multi(self):
        modes = stats.mode([1.0, 1.0, 2.0, 2.0])
        self.assertIn(1.0, modes)
        self.assertIn(2.0, modes)

    def test_mode_all_unique(self):
        modes = stats.mode([1.0, 2.0, 3.0])
        for m in modes:
            self.assertIn(m, [1.0, 2.0, 3.0])

    def test_mad_basic(self):
        self.assertAlmostEqual(stats.mad([1.0, 2.0, 3.0, 4.0, 5.0]), 1.0)


class TestDispersion(unittest.TestCase):
    """variance, std, percentile, quantile, iqr"""

    def test_variance_population(self):
        self.assertAlmostEqual(stats.variance([1.0, 3.0], ddof=0), 1.0)

    def test_variance_sample(self):
        self.assertAlmostEqual(stats.variance([1.0, 3.0], ddof=1), 2.0)

    def test_variance_insufficient(self):
        with self.assertRaises(ValueError):
            stats.variance([5.0], ddof=1)

    def test_std_population(self):
        self.assertAlmostEqual(stats.std([1.0, 3.0], ddof=0), 1.0)

    def test_percentile_median(self):
        self.assertAlmostEqual(stats.percentile([1.0, 2.0, 3.0, 4.0, 5.0], 50), 3.0)

    def test_percentile_min(self):
        self.assertAlmostEqual(stats.percentile([1.0, 2.0, 3.0, 4.0, 5.0], 0), 1.0)

    def test_percentile_max(self):
        self.assertAlmostEqual(stats.percentile([1.0, 2.0, 3.0, 4.0, 5.0], 100), 5.0)

    def test_percentile_interpolation(self):
        val = stats.percentile([1.0, 2.0, 3.0, 4.0], 25)
        self.assertAlmostEqual(val, 1.75)

    def test_quantile(self):
        self.assertAlmostEqual(stats.quantile([1.0, 2.0, 3.0, 4.0, 5.0], 0.5), 3.0)

    def test_iqr_basic(self):
        self.assertAlmostEqual(stats.iqr([1.0, 2.0, 3.0, 4.0, 5.0]), 2.0)


class TestDistributionShape(unittest.TestCase):
    """skewness, kurtosis"""

    def test_skewness_symmetric(self):
        self.assertAlmostEqual(
            stats.skewness([1.0, 2.0, 3.0, 4.0, 5.0]), 0.0, places=10
        )

    def test_skewness_positive(self):
        s = stats.skewness([1.0, 2.0, 2.0, 3.0, 10.0])
        self.assertGreater(s, 0)

    def test_skewness_small_data(self):
        self.assertEqual(stats.skewness([1.0, 2.0]), 0.0)

    def test_skewness_zero_variance(self):
        self.assertEqual(stats.skewness([1.0, 1.0, 1.0]), 0.0)

    def test_kurtosis_normal_like(self):
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        k = stats.kurtosis(data)
        self.assertAlmostEqual(k, -1.2, places=1)

    def test_kurtosis_small_data(self):
        data = [1.0, 2.0, 3.0]
        self.assertEqual(stats.kurtosis(data), 0.0)

    def test_kurtosis_zero_variance(self):
        self.assertEqual(stats.kurtosis([2.0, 2.0, 2.0, 2.0]), 0.0)


class TestCorrelationAndRegression(unittest.TestCase):
    """covariance, correlation, spearman_correlation, linear_regression"""

    def test_covariance(self):
        x = [1.0, 2.0, 3.0]
        y = [4.0, 5.0, 6.0]
        self.assertAlmostEqual(stats.covariance(x, y, ddof=0), 2 / 3, places=10)

    def test_covariance_length_mismatch(self):
        with self.assertRaises(ValueError):
            stats.covariance([1.0, 2.0], [1.0])

    def test_correlation_perfect(self):
        x = [1.0, 2.0, 3.0]
        y = [2.0, 4.0, 6.0]
        self.assertAlmostEqual(stats.correlation(x, y), 1.0)

    def test_correlation_negative(self):
        x = [1.0, 2.0, 3.0]
        y = [9.0, 5.0, 1.0]
        self.assertAlmostEqual(stats.correlation(x, y), -1.0, places=10)

    def test_correlation_zero_variance(self):
        x = [1.0, 1.0, 1.0]
        y = [2.0, 4.0, 6.0]
        self.assertEqual(stats.correlation(x, y), 0.0)

    def test_spearman_monotonic(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [1.0, 4.0, 9.0, 16.0, 25.0]
        self.assertAlmostEqual(stats.spearman_correlation(x, y), 1.0, places=10)

    def test_linear_regression_perfect(self):
        a, b = stats.linear_regression([1.0, 2.0, 3.0], [2.0, 4.0, 6.0])
        self.assertAlmostEqual(a, 0.0, places=10)
        self.assertAlmostEqual(b, 2.0)

    def test_linear_regression_intercept(self):
        a, b = stats.linear_regression([0.0, 1.0, 2.0], [5.0, 7.0, 9.0])
        self.assertAlmostEqual(a, 5.0, places=10)
        self.assertAlmostEqual(b, 2.0)

    def test_linear_regression_insufficient(self):
        with self.assertRaises(ValueError):
            stats.linear_regression([], [])

    def test_linear_regression_zero_variance_x(self):
        with self.assertRaises(ValueError):
            stats.linear_regression([1.0, 1.0, 1.0], [1.0, 2.0, 3.0])


class TestScalingAndOutliers(unittest.TestCase):
    """z_score, standardize, min_max_scale, outlier_bounds, outliers, describe"""

    def test_z_score(self):
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        z = stats.z_score(data)
        self.assertAlmostEqual(sum(z), 0.0, places=10)
        self.assertAlmostEqual(stats.std(z, ddof=1), 1.0, places=10)

    def test_z_score_constant(self):
        self.assertEqual(stats.z_score([5.0, 5.0, 5.0]), [0.0, 0.0, 0.0])

    def test_standardize_alias(self):
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        self.assertEqual(stats.standardize(data), stats.z_score(data))

    def test_min_max_scale_default(self):
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        scaled = stats.min_max_scale(data)
        self.assertAlmostEqual(scaled[0], 0.0)
        self.assertAlmostEqual(scaled[-1], 1.0)
        self.assertAlmostEqual(scaled[2], 0.5)

    def test_min_max_scale_custom_range(self):
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        scaled = stats.min_max_scale(data, (-1, 1))
        self.assertAlmostEqual(scaled[0], -1.0)
        self.assertAlmostEqual(scaled[-1], 1.0)
        self.assertAlmostEqual(scaled[2], 0.0)

    def test_min_max_scale_constant(self):
        data = [3.0, 3.0, 3.0]
        self.assertEqual(stats.min_max_scale(data), [0.0, 0.0, 0.0])

    def test_outlier_bounds_symmetric(self):
        lo, hi = stats.outlier_bounds([1.0, 2.0, 3.0, 4.0, 5.0, 20.0])
        self.assertLess(lo, hi)

    def test_outliers_detection(self):
        data = [1.0, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 100.0]
        out = stats.outliers(data)
        self.assertIn(100.0, out)
        self.assertNotIn(3.0, out)

    def test_describe(self):
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        d = stats.describe(data)
        self.assertAlmostEqual(d["count"], 5)
        self.assertAlmostEqual(d["mean"], 3.0)
        self.assertAlmostEqual(d["min"], 1.0)
        self.assertAlmostEqual(d["max"], 5.0)
        self.assertAlmostEqual(d["50%"], 3.0)
        self.assertIsInstance(d, dict)


# =============================================================================
# Optimization Tests
# =============================================================================


def _quad_1d(x):
    return (x[0] - 3.0) ** 2


def _quad_1d_grad(x):
    return [2.0 * (x[0] - 3.0)]


def _quad_2d(x):
    return (x[0] - 1.0) ** 2 + (x[1] - 2.0) ** 2


def _quad_2d_grad(x):
    return [2.0 * (x[0] - 1.0), 2.0 * (x[1] - 2.0)]


def _quad_2d_hess(x):
    return [[2.0, 0.0], [0.0, 2.0]]


class TestGradientBased(unittest.TestCase):
    """gradient_descent, adam"""

    def test_gradient_descent_1d(self):
        result = opt.gradient_descent(
            _quad_1d, _quad_1d_grad, [10.0], lr=0.1, max_iter=500
        )
        self.assertAlmostEqual(result[0], 3.0, places=3)

    def test_gradient_descent_2d(self):
        result = opt.gradient_descent(
            _quad_2d, _quad_2d_grad, [0.0, 0.0], lr=0.1, max_iter=500
        )
        self.assertAlmostEqual(result[0], 1.0, places=3)
        self.assertAlmostEqual(result[1], 2.0, places=3)

    def test_gradient_descent_with_momentum(self):
        result = opt.gradient_descent(
            _quad_2d, _quad_2d_grad, [5.0, 5.0], lr=0.1, momentum=0.5, max_iter=500
        )
        self.assertAlmostEqual(result[0], 1.0, places=3)
        self.assertAlmostEqual(result[1], 2.0, places=3)

    def test_gradient_descent_converges_to_tol(self):
        result = opt.gradient_descent(
            _quad_1d, _quad_1d_grad, [10.0], lr=0.1, max_iter=500, tol=1e-6
        )
        self.assertAlmostEqual(result[0], 3.0, places=4)

    def test_adam_1d(self):
        result = opt.adam(_quad_1d, _quad_1d_grad, [10.0], lr=0.5, max_iter=500)
        self.assertAlmostEqual(result[0], 3.0, places=2)

    def test_adam_2d(self):
        result = opt.adam(_quad_2d, _quad_2d_grad, [-1.0, -1.0], lr=0.5, max_iter=500)
        self.assertAlmostEqual(result[0], 1.0, places=2)
        self.assertAlmostEqual(result[1], 2.0, places=2)


class TestNewtonMethods(unittest.TestCase):
    """newton_method (1D), newton_method_nd"""

    def test_newton_method_sqrt2(self):
        def f(x):
            return x * x - 2.0

        def df(x):
            return 2.0 * x

        root = opt.newton_method(f, df, 1.5)
        self.assertAlmostEqual(root, math.sqrt(2.0), places=8)

    def test_newton_method_at_root(self):
        def f(x):
            return x - 5.0

        def df(x):
            return 1.0

        root = opt.newton_method(f, df, 5.0)
        self.assertAlmostEqual(root, 5.0)

    def test_newton_method_derivative_zero(self):
        def f(x):
            return x * x - 2.0

        def df(x):
            return 2.0 * x

        with self.assertRaises(ValueError):
            opt.newton_method(f, df, 0.0)

    def test_newton_method_nd_quadratic(self):
        result = opt.newton_method_nd(
            _quad_2d, _quad_2d_grad, _quad_2d_hess, [0.0, 0.0]
        )
        self.assertAlmostEqual(result[0], 1.0, places=8)
        self.assertAlmostEqual(result[1], 2.0, places=8)

    def test_newton_method_nd_convergence(self):
        result = opt.newton_method_nd(
            _quad_2d, _quad_2d_grad, _quad_2d_hess, [10.0, -5.0]
        )
        self.assertAlmostEqual(result[0], 1.0, places=8)
        self.assertAlmostEqual(result[1], 2.0, places=8)


class TestLineSearchAndCG(unittest.TestCase):
    """line_search, conjugate_gradient"""

    def test_line_search_returns_positive(self):
        alpha = opt.line_search(_quad_2d, _quad_2d_grad, [5.0, 5.0], [-1.0, -1.0])
        self.assertGreater(alpha, 0.0)

    def test_line_search_not_descent(self):
        alpha = opt.line_search(_quad_2d, _quad_2d_grad, [0.0, 0.0], [0.0, 0.0])
        self.assertEqual(alpha, 0.0)

    def test_conjugate_gradient_quadratic(self):
        def quad_f(x):
            return x[0] ** 2 + x[1] ** 2

        def quad_grad(x):
            return [2.0 * x[0], 2.0 * x[1]]

        result = opt.conjugate_gradient(quad_f, quad_grad, [5.0, 5.0], tol=1e-6)
        self.assertAlmostEqual(result[0], 0.0, places=4)
        self.assertAlmostEqual(result[1], 0.0, places=4)


class TestNelderMead(unittest.TestCase):
    def test_nelder_mead_quadratic(self):
        def f(x):
            return (x[0] - 4.0) ** 2 + (x[1] + 3.0) ** 2

        result = opt.nelder_mead(f, [0.0, 0.0])
        self.assertAlmostEqual(result[0], 4.0, places=3)
        self.assertAlmostEqual(result[1], -3.0, places=2)

    def test_nelder_mead_1d(self):
        def f(x):
            return (x[0] - 7.0) ** 2

        result = opt.nelder_mead(f, [0.0])
        self.assertAlmostEqual(result[0], 7.0, places=3)


class TestMinimizeDispatcher(unittest.TestCase):
    """minimize"""

    def test_minimize_gradient_descent(self):
        result = opt.minimize(
            _quad_2d,
            [0.0, 0.0],
            method="gradient_descent",
            grad=_quad_2d_grad,
            lr=0.1,
            max_iter=500,
        )
        self.assertAlmostEqual(result[0], 1.0, places=3)

    def test_minimize_adam(self):
        result = opt.minimize(
            _quad_2d,
            [-2.0, 3.0],
            method="adam",
            grad=_quad_2d_grad,
            lr=0.5,
            max_iter=500,
        )
        self.assertAlmostEqual(result[0], 1.0, places=2)

    def test_minimize_newton(self):
        result = opt.minimize(
            _quad_2d,
            [5.0, 5.0],
            method="newton",
            grad=_quad_2d_grad,
            hess=_quad_2d_hess,
        )
        self.assertAlmostEqual(result[0], 1.0, places=8)
        self.assertAlmostEqual(result[1], 2.0, places=8)

    def test_minimize_conjugate_gradient(self):
        result = opt.minimize(
            _quad_2d,
            [3.0, 3.0],
            method="conjugate_gradient",
            grad=_quad_2d_grad,
            tol=1e-6,
        )
        self.assertAlmostEqual(result[0], 1.0, places=3)
        self.assertAlmostEqual(result[1], 2.0, places=3)

    def test_minimize_nelder_mead(self):
        def f(x):
            return (x[0] - 1.5) ** 2 + (x[1] + 0.5) ** 2

        result = opt.minimize(f, [0.0, 0.0], method="nelder_mead")
        self.assertAlmostEqual(result[0], 1.5, places=3)
        self.assertAlmostEqual(result[1], -0.5, places=3)

    def test_minimize_requires_grad(self):
        with self.assertRaises(ValueError):
            opt.minimize(_quad_2d, [0.0, 0.0], method="gradient_descent")

    def test_minimize_unknown_method(self):
        with self.assertRaises(ValueError):
            opt.minimize(_quad_2d, [0.0, 0.0], method="unknown")


# =============================================================================
# Machine Learning Tests
# =============================================================================


class TestLinearModels(unittest.TestCase):
    """LinearRegression, RidgeRegression, LassoRegression"""

    def setUp(self):
        self.X = [[1.0], [2.0], [3.0], [4.0], [5.0]]
        self.y = [2.0, 4.0, 6.0, 8.0, 10.0]
        self.X_multi = [[1.0, 2.0], [2.0, 3.0], [3.0, 4.0], [4.0, 5.0]]
        self.y_multi = [3.0, 5.0, 7.0, 9.0]

    def test_linear_regression_fit_predict(self):
        model = ml.LinearRegression()
        model.fit(self.X, self.y)
        preds = model.predict(self.X)
        for p, t in zip(preds, self.y, strict=False):
            self.assertAlmostEqual(p, t, places=8)

    def test_linear_regression_score_perfect(self):
        model = ml.LinearRegression()
        model.fit(self.X, self.y)
        self.assertAlmostEqual(model.score(self.X, self.y), 1.0, places=10)

    def test_linear_regression_predict_before_fit(self):
        model = ml.LinearRegression()
        with self.assertRaises(ValueError):
            model.predict([[1.0]])

    def test_linear_regression_no_intercept(self):
        model = ml.LinearRegression(fit_intercept=False)
        model.fit([[1.0], [2.0]], [2.0, 4.0])
        self.assertAlmostEqual(model.intercept_, 0.0)
        preds = model.predict([[3.0]])
        self.assertAlmostEqual(preds[0], 6.0, places=8)

    def test_ridge_regression(self):
        model = ml.RidgeRegression(alpha=1.0)
        model.fit(self.X, self.y)
        preds = model.predict(self.X)
        self.assertEqual(len(preds), len(self.y))
        r2 = model.score(self.X, self.y)
        self.assertGreater(r2, 0.95)

    def test_ridge_regression_different_alpha(self):
        model = ml.RidgeRegression(alpha=10.0)
        model.fit(self.X_multi, self.y_multi)
        preds = model.predict([[5.0, 6.0]])
        self.assertEqual(len(preds), 1)

    def test_lasso_regression(self):
        model = ml.LassoRegression(alpha=0.01, max_iter=2000)
        model.fit(self.X, self.y)
        preds = model.predict(self.X)
        self.assertEqual(len(preds), len(self.y))
        r2 = model.score(self.X, self.y)
        self.assertGreater(r2, 0.95)

    def test_lasso_regression_no_intercept(self):
        model = ml.LassoRegression(alpha=0.1, fit_intercept=False)
        model.fit([[1.0], [2.0]], [2.0, 4.0])
        self.assertAlmostEqual(model.intercept_, 0.0)
        preds = model.predict([[3.0]])
        self.assertEqual(len(preds), 1)


class TestLogisticRegression(unittest.TestCase):
    """LogisticRegression"""

    def setUp(self):
        self.X = [[1.0], [2.0], [3.0], [10.0], [11.0], [12.0]]
        self.y = [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]

    def test_logistic_regression_fit_predict(self):
        model = ml.LogisticRegression(max_iter=2000)
        model.fit(self.X, self.y)
        preds = model.predict(self.X)
        self.assertEqual(len(preds), len(self.y))
        acc = model.score(self.X, self.y)
        self.assertGreaterEqual(acc, 0.5)

    def test_logistic_regression_predict_proba(self):
        model = ml.LogisticRegression(max_iter=2000)
        model.fit(self.X, self.y)
        probs = model.predict_proba(self.X)
        self.assertEqual(len(probs), len(self.X))
        self.assertEqual(len(probs[0]), 2)
        for p in probs:
            self.assertAlmostEqual(sum(p), 1.0, places=6)

    def test_logistic_regression_predict_before_fit(self):
        model = ml.LogisticRegression()
        with self.assertRaises(ValueError):
            model.predict([[1.0]])


class TestKMeans(unittest.TestCase):
    def test_kmeans_two_clusters(self):
        X = [[0.0, 0.0], [0.1, 0.1], [0.2, 0.2], [5.0, 5.0], [5.1, 5.1], [5.2, 5.2]]
        model = ml.KMeans(n_clusters=2, random_state=42, max_iter=100)
        model.fit(X)
        self.assertEqual(len(model.cluster_centers_), 2)
        self.assertEqual(len(model.labels_), len(X))
        preds = model.predict([[0.0, 0.0], [5.0, 5.0]])
        self.assertEqual(len(preds), 2)

    def test_kmeans_fit_predict(self):
        X = [[1.0, 1.0], [1.5, 1.5], [8.0, 8.0], [8.5, 8.5]]
        model = ml.KMeans(n_clusters=2, random_state=1)
        labels = model.fit_predict(X)
        self.assertEqual(len(labels), len(X))

    def test_kmeans_predict_before_fit(self):
        model = ml.KMeans(n_clusters=2)
        with self.assertRaises(ValueError):
            model.predict([[1.0, 2.0]])


class TestGaussianNB(unittest.TestCase):
    def setUp(self):
        self.X = [[1.0], [2.0], [3.0], [10.0], [11.0], [12.0]]
        self.y = [0, 0, 0, 1, 1, 1]

    def test_gnb_fit_predict(self):
        model = ml.GaussianNB()
        model.fit(self.X, self.y)
        preds = model.predict(self.X)
        self.assertEqual(len(preds), len(self.y))

    def test_gnb_score(self):
        model = ml.GaussianNB()
        model.fit(self.X, self.y)
        acc = model.score(self.X, self.y)
        self.assertGreater(acc, 0.5)

    def test_gnb_multi_class(self):
        X = [[1.0], [2.0], [5.0], [6.0], [9.0], [10.0]]
        y = [0, 0, 1, 1, 2, 2]
        model = ml.GaussianNB()
        model.fit(X, y)
        preds = model.predict([[3.0], [7.0]])
        self.assertEqual(len(preds), 2)

    def test_gnb_classes_property(self):
        model = ml.GaussianNB()
        model.fit(self.X, self.y)
        self.assertEqual(sorted(model.classes_), [0, 1])

    def test_gnb_predict_before_fit(self):
        model = ml.GaussianNB()
        with self.assertRaises(ValueError):
            model.predict([[1.0]])


class TestDecisionTree(unittest.TestCase):
    """DecisionTreeClassifier"""

    def setUp(self):
        # Simple XOR-like data
        self.X = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]
        self.y = [0, 1, 1, 0]

    def test_tree_fit_predict(self):
        model = ml.DecisionTreeClassifier(max_depth=3)
        model.fit(self.X, self.y)
        preds = model.predict(self.X)
        self.assertEqual(len(preds), len(self.y))

    def test_tree_score(self):
        model = ml.DecisionTreeClassifier(max_depth=3)
        model.fit(self.X, self.y)
        acc = model.score(self.X, self.y)
        self.assertGreaterEqual(acc, 0.0)

    def test_tree_pure_class_stops_early(self):
        X = [[1.0], [2.0], [3.0]]
        y = [1, 1, 1]
        model = ml.DecisionTreeClassifier(max_depth=10)
        model.fit(X, y)
        self.assertEqual(model.predict([[4.0]])[0], 1)

    def test_tree_entropy_criterion(self):
        model = ml.DecisionTreeClassifier(max_depth=3, criterion="entropy")
        model.fit(self.X, self.y)
        preds = model.predict(self.X)
        self.assertEqual(len(preds), len(self.y))

    def test_tree_predict_before_fit(self):
        model = ml.DecisionTreeClassifier()
        with self.assertRaises(ValueError):
            model.predict([[1.0]])


class TestRandomForest(unittest.TestCase):
    def setUp(self):
        self.X = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]
        self.y = [0, 1, 1, 0]

    def test_rf_fit_predict(self):
        model = ml.RandomForestClassifier(n_estimators=5, max_depth=3, random_state=42)
        model.fit(self.X, self.y)
        preds = model.predict(self.X)
        self.assertEqual(len(preds), len(self.y))

    def test_rf_score(self):
        model = ml.RandomForestClassifier(n_estimators=5, max_depth=3, random_state=42)
        model.fit(self.X, self.y)
        acc = model.score(self.X, self.y)
        self.assertGreaterEqual(acc, 0.0)

    def test_rf_predict_before_fit(self):
        model = ml.RandomForestClassifier()
        with self.assertRaises(ValueError):
            model.predict([[1.0, 2.0]])


class TestTrainTestSplit(unittest.TestCase):
    def test_split_default(self):
        X = [[1.0], [2.0], [3.0], [4.0]]
        y = [0, 1, 0, 1]
        Xtr, Xte, ytr, yte = ml.train_test_split(X, y, test_size=0.25, random_state=42)
        self.assertEqual(len(Xtr), 3)
        self.assertEqual(len(Xte), 1)
        self.assertEqual(len(ytr), 3)
        self.assertEqual(len(yte), 1)

    def test_split_no_shuffle(self):
        X = [[1.0], [2.0], [3.0], [4.0]]
        y = [0, 1, 0, 1]
        Xtr, Xte, ytr, yte = ml.train_test_split(X, y, test_size=0.5, shuffle=False)
        self.assertEqual(Xtr, [[1.0], [2.0]])
        self.assertEqual(Xte, [[3.0], [4.0]])

    def test_split_single_sample(self):
        X = [[1.0]]
        y = [0]
        Xtr, Xte, ytr, yte = ml.train_test_split(X, y, test_size=0.5)
        self.assertEqual(len(Xtr), 0)
        self.assertEqual(len(Xte), 1)

    def test_split_reproducible_seed(self):
        X = [[1.0], [2.0], [3.0], [4.0], [5.0], [6.0]]
        y = [0, 0, 1, 1, 0, 1]
        r1 = ml.train_test_split(X, y, test_size=0.33, random_state=42)
        r2 = ml.train_test_split(X, y, test_size=0.33, random_state=42)
        for a, b in zip(r1, r2, strict=False):
            self.assertEqual(a, b)


class TestMetrics(unittest.TestCase):
    """accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report"""

    def test_accuracy_perfect(self):
        self.assertAlmostEqual(ml.accuracy_score([0, 1, 0, 1], [0, 1, 0, 1]), 1.0)

    def test_accuracy_half(self):
        self.assertAlmostEqual(ml.accuracy_score([0, 1, 0, 1], [0, 0, 1, 1]), 0.5)

    def test_precision(self):
        y_true = [0, 1, 0, 1, 1]
        y_pred = [0, 1, 0, 0, 1]
        self.assertAlmostEqual(ml.precision_score(y_true, y_pred), 1.0)

    def test_precision_no_positives(self):
        self.assertEqual(ml.precision_score([0, 0, 0], [0, 0, 0]), 0.0)

    def test_recall(self):
        y_true = [0, 1, 0, 1, 1]
        y_pred = [0, 1, 0, 0, 1]
        self.assertAlmostEqual(ml.recall_score(y_true, y_pred), 2 / 3)

    def test_recall_no_positives(self):
        self.assertEqual(ml.recall_score([0, 0, 0], [0, 0, 0]), 0.0)

    def test_f1(self):
        y_true = [0, 1, 0, 1, 1]
        y_pred = [0, 1, 0, 0, 1]
        expected = 2 * (1.0 * 2 / 3) / (1.0 + 2 / 3)
        self.assertAlmostEqual(ml.f1_score(y_true, y_pred), expected)

    def test_f1_no_positives(self):
        self.assertEqual(ml.f1_score([0, 0], [0, 0]), 0.0)

    def test_f1_precision_or_recall_zero(self):
        self.assertEqual(ml.f1_score([0, 0, 1], [0, 0, 0]), 0.0)

    def test_confusion_matrix_binary(self):
        y_true = [0, 0, 1, 1, 0, 1]
        y_pred = [0, 1, 1, 1, 0, 0]
        cm = ml.confusion_matrix(y_true, y_pred)
        self.assertEqual(len(cm), 2)
        self.assertEqual(len(cm[0]), 2)
        self.assertEqual(cm[0][0], 2)  # true 0, pred 0
        self.assertEqual(cm[1][1], 2)  # true 1, pred 1

    def test_confusion_matrix_custom_labels(self):
        y_true = [1, 2, 1, 2]
        y_pred = [1, 1, 2, 2]
        cm = ml.confusion_matrix(y_true, y_pred, labels=[1, 2])
        self.assertEqual(cm[0][1], 1)
        self.assertEqual(cm[1][0], 1)

    def test_classification_report_contains_accuracy(self):
        y_true = [0, 1, 0, 1]
        y_pred = [0, 1, 1, 0]
        report = ml.classification_report(y_true, y_pred)
        self.assertIn("accuracy", report)
        self.assertIn("precision", report)
        self.assertIn("recall", report)
        self.assertIn("f1-score", report)

    def test_classification_report_custom_labels(self):
        report = ml.classification_report([0, 1], [0, 1], labels=[0, 1])
        self.assertIn("0", report)
        self.assertIn("1", report)


# LBFGS (wraps gradient_descent)
class TestLBFGS(unittest.TestCase):
    def test_lbfgs_quadratic(self):
        result = opt.lbfgs(_quad_2d, _quad_2d_grad, [5.0, 5.0], max_iter=500)
        self.assertAlmostEqual(result[0], 1.0, places=3)
        self.assertAlmostEqual(result[1], 2.0, places=3)


# SGD
class TestStochasticGradientDescent(unittest.TestCase):
    def test_sgd_quadratic(self):
        result = opt.stochastic_gradient_descent(
            _quad_1d, _quad_1d_grad, [10.0], lr=0.1, max_iter=500
        )
        self.assertAlmostEqual(result[0], 3.0, places=3)


if __name__ == "__main__":
    unittest.main()
