"""Zoya 4.0 Scientific Computing - Linear Algebra module."""

import math

Matrix = list[list[float]]
Vector = list[float]


def zeros(rows: int, cols: int = None) -> Matrix:
    """Create a matrix of zeros."""
    if cols is None:
        cols = rows
    return [[0.0 for _ in range(cols)] for _ in range(rows)]


def identity(n: int) -> Matrix:
    """Create an n x n identity matrix."""
    I = zeros(n, n)
    for i in range(n):
        I[i][i] = 1.0
    return I


def transpose(A: Matrix) -> Matrix:
    """Transpose a matrix."""
    if not A:
        return []
    rows, cols = len(A), len(A[0])
    return [[A[i][j] for i in range(rows)] for j in range(cols)]


def matmul(A: Matrix, B: Matrix) -> Matrix:
    """Matrix multiplication."""
    if not A or not B:
        return []
    a_rows, a_cols = len(A), len(A[0])
    b_rows, b_cols = len(B), len(B[0])
    if a_cols != b_rows:
        raise ValueError(f"Dimension mismatch: {a_cols} != {b_rows}")

    result = zeros(a_rows, b_cols)
    for i in range(a_rows):
        for j in range(b_cols):
            s = 0.0
            for k in range(a_cols):
                s += A[i][k] * B[k][j]
            result[i][j] = s
    return result


def matvec(A: Matrix, v: Vector) -> Vector:
    """Matrix-vector multiplication."""
    if not A or not v:
        return []
    rows, cols = len(A), len(A[0])
    if cols != len(v):
        raise ValueError("Dimension mismatch")
    return [sum(A[i][j] * v[j] for j in range(cols)) for i in range(rows)]


def add(A: Matrix, B: Matrix) -> Matrix:
    """Element-wise matrix addition."""
    if len(A) != len(B) or len(A[0]) != len(B[0]):
        raise ValueError("Dimension mismatch")
    return [[A[i][j] + B[i][j] for j in range(len(A[0]))] for i in range(len(A))]


def sub(A: Matrix, B: Matrix) -> Matrix:
    """Element-wise matrix subtraction."""
    if len(A) != len(B) or len(A[0]) != len(B[0]):
        raise ValueError("Dimension mismatch")
    return [[A[i][j] - B[i][j] for j in range(len(A[0]))] for i in range(len(A))]


def scale(A: Matrix, scalar: float) -> Matrix:
    """Scale matrix by scalar."""
    return [[A[i][j] * scalar for j in range(len(A[0]))] for i in range(len(A))]


def det(A: Matrix) -> float:
    """Matrix determinant (for square matrices)."""
    n = len(A)
    if n == 0 or len(A[0]) != n:
        raise ValueError("Matrix must be square")

    if n == 1:
        return A[0][0]
    if n == 2:
        return A[0][0] * A[1][1] - A[0][1] * A[1][0]

    # LU decomposition for larger matrices
    return _det_lu(A)


def _det_lu(A: Matrix) -> float:
    """Determinant via LU decomposition."""
    n = len(A)
    LU = [row[:] for row in A]
    det = 1.0

    for i in range(n):
        # Find pivot
        max_row = i
        for k in range(i + 1, n):
            if abs(LU[k][i]) > abs(LU[max_row][i]):
                max_row = k

        if max_row != i:
            LU[i], LU[max_row] = LU[max_row], LU[i]
            det = -det

        if abs(LU[i][i]) < 1e-12:
            return 0.0

        det *= LU[i][i]

        # Eliminate
        for k in range(i + 1, n):
            factor = LU[k][i] / LU[i][i]
            LU[k][i] = factor
            for j in range(i + 1, n):
                LU[k][j] -= factor * LU[i][j]

    return det


def inv(A: Matrix) -> Matrix:
    """Matrix inverse (for square invertible matrices)."""
    n = len(A)
    if n == 0 or len(A[0]) != n:
        raise ValueError("Matrix must be square")

    if n == 1:
        return [[1.0 / A[0][0]]]

    # Augment with identity
    aug = [A[i][:] + [1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

    # Gauss-Jordan elimination
    for i in range(n):
        # Find pivot
        max_row = i
        for k in range(i + 1, n):
            if abs(aug[k][i]) > abs(aug[max_row][i]):
                max_row = k
        aug[i], aug[max_row] = aug[max_row], aug[i]

        pivot = aug[i][i]
        if abs(pivot) < 1e-12:
            raise ValueError("Matrix is singular")

        # Normalize row
        for j in range(2 * n):
            aug[i][j] /= pivot

        # Eliminate other rows
        for k in range(n):
            if k != i:
                factor = aug[k][i]
                for j in range(2 * n):
                    aug[k][j] -= factor * aug[i][j]

    # Extract inverse
    return [row[n:] for row in aug]


def solve(A: Matrix, b: Vector) -> Vector:
    """Solve linear system Ax = b."""
    n = len(A)
    if len(A[0]) != n:
        raise ValueError("A must be square")
    if len(b) != n:
        raise ValueError("Dimension mismatch")

    # Use LU decomposition
    return _solve_lu(A, b)


def _solve_lu(A: Matrix, b: Vector) -> Vector:
    """Solve via LU decomposition."""
    n = len(A)
    LU = [row[:] for row in A]
    P = list(range(n))

    # LU decomposition with partial pivoting
    for i in range(n):
        # Find pivot
        max_row = i
        for k in range(i + 1, n):
            if abs(LU[k][i]) > abs(LU[max_row][i]):
                max_row = k
        LU[i], LU[max_row] = LU[max_row], LU[i]
        P[i], P[max_row] = P[max_row], P[i]

        if abs(LU[i][i]) < 1e-12:
            raise ValueError("Matrix is singular")

        for k in range(i + 1, n):
            LU[k][i] /= LU[i][i]
            for j in range(i + 1, n):
                LU[k][j] -= LU[k][i] * LU[i][j]

    # Forward substitution: Ly = Pb
    y = [0.0] * n
    for i in range(n):
        y[i] = b[P[i]] - sum(LU[i][j] * y[j] for j in range(i))

    # Back substitution: Ux = y
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (y[i] - sum(LU[i][j] * x[j] for j in range(i + 1, n))) / LU[i][i]

    return x


def eig(A: Matrix) -> tuple[Vector, Matrix]:
    """Eigenvalues and eigenvectors (power iteration for symmetric matrices)."""
    n = len(A)
    if n == 0 or len(A[0]) != n:
        raise ValueError("Matrix must be square")

    # Simple QR algorithm for small symmetric matrices
    # For production, use numpy/scipy
    return _eig_qr(A)


def _eig_qr(
    A: Matrix, max_iter: int = 100, tol: float = 1e-10
) -> tuple[Vector, Matrix]:
    """QR algorithm for eigenvalues."""
    n = len(A)
    A_k = [row[:] for row in A]
    V = identity(n)

    for _ in range(max_iter):
        # QR decomposition
        Q, R = _qr_decomp(A_k)
        A_k = matmul(R, Q)
        V = matmul(V, Q)

        # Check convergence
        off_diag = sum(A_k[i][j] ** 2 for i in range(n) for j in range(n) if i != j)
        if off_diag < tol:
            break

    eigenvals = [A_k[i][i] for i in range(n)]
    eigenvecs = [[V[j][i] for j in range(n)] for i in range(n)]
    return eigenvals, eigenvecs


def _qr_decomp(A: Matrix) -> tuple[Matrix, Matrix]:
    """QR decomposition via Gram-Schmidt."""
    n = len(A)
    m = len(A[0])
    Q = zeros(n, m)
    R = zeros(m, m)

    for j in range(m):
        v = [A[i][j] for i in range(n)]
        for i in range(j):
            R[i][j] = sum(Q[k][i] * A[k][j] for k in range(n))
            for k in range(n):
                v[k] -= R[i][j] * Q[k][i]
        norm = math.sqrt(sum(x * x for x in v))
        R[j][j] = norm
        if norm > 1e-12:
            for k in range(n):
                Q[k][j] = v[k] / norm
    return Q, R


def svd(A: Matrix) -> tuple[Matrix, Vector, Matrix]:
    """Singular Value Decomposition (placeholder - use numpy for production)."""
    # Placeholder - real implementation uses Golub-Reinsch algorithm
    raise NotImplementedError("SVD not yet implemented - use numpy for now")


def norm(v: Vector, p: int = 2) -> float:
    """Vector norm."""
    if p == 1:
        return sum(abs(x) for x in v)
    elif p == 2:
        return math.sqrt(sum(x * x for x in v))
    elif p == float("inf"):
        return max(abs(x) for x in v)
    else:
        return sum(abs(x) ** p for x in v) ** (1 / p)


def dot(a: Vector, b: Vector) -> float:
    """Dot product."""
    return sum(x * y for x, y in zip(a, b, strict=False))


def cross(a: Vector, b: Vector) -> Vector:
    """Cross product (3D only)."""
    if len(a) != 3 or len(b) != 3:
        raise ValueError("Cross product only for 3D vectors")
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


# Convenience functions
def mat_pow(A: Matrix, n: int) -> Matrix:
    """Matrix power."""
    if n == 0:
        return identity(len(A))
    result = A
    for _ in range(n - 1):
        result = matmul(result, A)
    return result


def trace(A: Matrix) -> float:
    """Matrix trace."""
    return sum(A[i][i] for i in range(len(A)))


def rank(A: Matrix) -> int:
    """Matrix rank (via Gaussian elimination)."""
    if not A:
        return 0
    rows, cols = len(A), len(A[0])
    A_copy = [row[:] for row in A]
    rank = 0
    row = 0

    for col in range(cols):
        # Find pivot
        pivot = row
        while pivot < rows and abs(A_copy[pivot][col]) < 1e-12:
            pivot += 1
        if pivot == rows:
            continue
        A_copy[row], A_copy[pivot] = A_copy[pivot], A_copy[row]
        pivot_val = A_copy[row][col]
        for j in range(col, cols):
            A_copy[row][j] /= pivot_val
        for i in range(rows):
            if i != row:
                factor = A_copy[i][col]
                for j in range(col, cols):
                    A_copy[i][j] -= factor * A_copy[row][j]
        row += 1
        rank += 1
        if row == rows:
            break
    return rank


def qr_decomp(A: Matrix) -> tuple[Matrix, Matrix]:
    """QR decomposition via Gram-Schmidt."""
    n = len(A)
    m = len(A[0])
    Q = zeros(n, m)
    R = zeros(m, m)

    for j in range(m):
        v = [A[i][j] for i in range(n)]
        for i in range(j):
            R[i][j] = sum(Q[k][i] * A[k][j] for k in range(n))
            for k in range(n):
                v[k] -= R[i][j] * Q[k][i]
        norm_v = math.sqrt(sum(x * x for x in v))
        R[j][j] = norm_v
        if norm_v > 1e-12:
            for k in range(n):
                Q[k][j] = v[k] / norm_v
    return Q, R


def qr(A: Matrix) -> tuple[Matrix, Matrix]:
    """QR decomposition."""
    return qr_decomp(A)


# Vector operations
def v_add(a: Vector, b: Vector) -> Vector:
    return [x + y for x, y in zip(a, b, strict=False)]


def v_sub(a: Vector, b: Vector) -> Vector:
    return [x - y for x, y in zip(a, b, strict=False)]


def v_mul(a: Vector, b: Vector) -> Vector:
    return [x * y for x, y in zip(a, b, strict=False)]


def v_div(a: Vector, b: Vector) -> Vector:
    return [x / y for x, y in zip(a, b, strict=False)]


def v_scale(v: Vector, s: float) -> Vector:
    return [x * s for x in v]


def v_sum(v: Vector) -> float:
    return sum(v)


def v_mean(v: Vector) -> float:
    return sum(v) / len(v) if v else 0


def v_std(v: Vector) -> float:
    m = v_mean(v)
    return math.sqrt(sum((x - m) ** 2 for x in v) / len(v)) if len(v) > 1 else 0


def v_var(v: Vector) -> float:
    return v_std(v) ** 2


def v_corr(a: Vector, b: Vector) -> float:
    if len(a) != len(b):
        raise ValueError("Vectors must be same length")
    n = len(a)
    if n == 0:
        return 0
    mean_a, mean_b = v_mean(a), v_mean(b)
    num = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n))
    den_a = sum((x - mean_a) ** 2 for x in a)
    den_b = sum((x - mean_b) ** 2 for x in b)
    if den_a == 0 or den_b == 0:
        return 0
    return num / math.sqrt(den_a * den_b)


# Alias
v_norm = norm
