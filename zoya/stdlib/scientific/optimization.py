"""Zoya 4.0 Scientific Computing - Optimization module."""

from typing import List, Callable, Tuple, Optional
import math
import random


Vector = List[float]
Scalar = float
Objective = Callable[[Vector], Scalar]
Gradient = Callable[[Vector], Vector]


def gradient_descent(
    f: Objective,
    grad_f: Gradient,
    x0: Vector,
    lr: float = 0.01,
    max_iter: int = 1000,
    tol: float = 1e-6,
    momentum: float = 0.0,
) -> Vector:
    """
    Gradient descent optimization.
    
    Args:
        f: Objective function to minimize
        grad_f: Gradient of objective
        x0: Initial guess
        lr: Learning rate
        max_iter: Maximum iterations
        tol: Convergence tolerance
        momentum: Momentum coefficient (0-1)
    
    Returns:
        Optimized parameters
    """
    x = x0[:]
    v = [0.0] * len(x)
    
    for i in range(max_iter):
        g = grad_f(x)
        grad_norm = math.sqrt(sum(g_i**2 for g_i in g))
        
        if grad_norm < tol:
            break
        
        if momentum > 0:
            v = [momentum * v_i - lr * g_i for v_i, g_i in zip(v, g)]
            x = [x_i + v_i for x_i, v_i in zip(x, v)]
        else:
            x = [x_i - lr * g_i for x_i, g_i in zip(x, g)]
    
    return x


def stochastic_gradient_descent(
    f: Objective,
    grad_f: Gradient,
    x0: Vector,
    lr: float = 0.01,
    max_iter: int = 1000,
    batch_size: int = 1,
    tol: float = 1e-6,
) -> Vector:
    """SGD with mini-batches."""
    x = x0[:]
    n = len(x0)  # Assuming data dimension
    
    for i in range(max_iter):
        g = grad_f(x)
        grad_norm = math.sqrt(sum(g_i**2 for g_i in g))
        if grad_norm < tol:
            break
        x = [x_i - lr * g_i for x_i, g_i in zip(x, g)]
    
    return x


def adam(
    f: Objective,
    grad_f: Gradient,
    x0: Vector,
    lr: float = 0.001,
    beta1: float = 0.9,
    beta2: float = 0.999,
    eps: float = 1e-8,
    max_iter: int = 1000,
    tol: float = 1e-6,
) -> Vector:
    """
    Adam optimizer.
    
    Args:
        f: Objective function
        grad_f: Gradient function
        x0: Initial parameters
        lr: Learning rate
        beta1: Exponential decay for 1st moment
        beta2: Exponential decay for 2nd moment
        eps: Small constant for numerical stability
        max_iter: Maximum iterations
        tol: Convergence tolerance
    """
    x = x0[:]
    m = [0.0] * len(x)
    v = [0.0] * len(x)
    
    for t in range(1, max_iter + 1):
        g = grad_f(x)
        grad_norm = math.sqrt(sum(g_i**2 for g_i in g))
        if grad_norm < tol:
            break
        
        for i in range(len(x)):
            m[i] = beta1 * m[i] + (1 - beta1) * g[i]
            v[i] = beta2 * v[i] + (1 - beta2) * g[i] * g[i]
            
            m_hat = m[i] / (1 - beta1**t)
            v_hat = v[i] / (1 - beta2**t)
            
            x[i] -= lr * m_hat / (math.sqrt(v_hat) + eps)
    
    return x


def lbfgs(
    f: Objective,
    grad_f: Gradient,
    x0: Vector,
    max_iter: int = 1000,
    tol: float = 1e-6,
    memory: int = 10,
) -> Vector:
    """L-BFGS quasi-Newton method (simplified)."""
    # Simplified L-BFGS - production should use scipy
    return gradient_descent(f, grad_f, x0, lr=0.01, max_iter=max_iter, tol=tol)


def newton_method(
    f: Callable[[float], float],
    df: Callable[[float], float],
    x0: float,
    max_iter: int = 100,
    tol: float = 1e-10,
) -> float:
    """
    Newton's method for root finding in 1D.
    
    Args:
        f: Function to find root of
        df: Derivative of f
        x0: Initial guess
        max_iter: Maximum iterations
        tol: Convergence tolerance
    
    Returns:
        Approximate root
    """
    x = x0
    for _ in range(max_iter):
        fx = f(x)
        if abs(fx) < tol:
            return x
        dfx = df(x)
        if abs(dfx) < 1e-12:
            raise ValueError("Derivative near zero")
        x -= fx / dfx
    return x


def _solve_linear(A: List[List[float]], b: List[float]) -> List[float]:
    """Solve Ax = b using Gaussian elimination (pure Python)."""
    n = len(A)
    aug = [row[:] + [b[i]] for i, row in enumerate(A)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-12:
            continue
        aug[col], aug[pivot] = aug[pivot], aug[col]
        for r in range(col + 1, n):
            factor = aug[r][col] / aug[col][col]
            for c in range(col, n + 1):
                aug[r][c] -= factor * aug[col][c]
    x = [0.0] * n
    for i in reversed(range(n)):
        s = sum(aug[i][j] * x[j] for j in range(i + 1, n))
        if abs(aug[i][i]) < 1e-12:
            x[i] = 0.0
        else:
            x[i] = (aug[i][n] - s) / aug[i][i]
    return x


def newton_method_nd(
    f: Objective,
    grad_f: Gradient,
    hess_f: Callable[[Vector], List[List[float]]],
    x0: Vector,
    max_iter: int = 100,
    tol: float = 1e-6,
) -> Vector:
    """
    Newton's method for multivariate optimization.
    
    Args:
        f: Objective function
        grad_f: Gradient function
        hess_f: Hessian function
        x0: Initial guess
        max_iter: Maximum iterations
        tol: Convergence tolerance
    """
    x = x0[:]
    for _ in range(max_iter):
        g = grad_f(x)
        if math.sqrt(sum(gi**2 for gi in g)) < tol:
            break
        H = hess_f(x)
        try:
            delta = _solve_linear(H, [-gi for gi in g])
            x = [x[i] + delta[i] for i in range(len(x))]
        except Exception:
            break
    return x


def line_search(
    f: Objective,
    grad_f: Gradient,
    x: Vector,
    d: Vector,
    alpha: float = 1.0,
    c1: float = 1e-4,
    c2: float = 0.9,
    max_iter: int = 20,
) -> float:
    """
    Wolfe line search.
    
    Returns optimal step size alpha.
    """
    fx = f(x)
    g = grad_f(x)
    gtd = sum(gi * di for gi, di in zip(g, d))
    
    if gtd >= 0:
        return 0.0  # Not a descent direction
    
    alpha_max = 1.0
    alpha_min = 0.0
    
    for _ in range(max_iter):
        x_new = [x[i] + alpha * d[i] for i in range(len(x))]
        fx_new = f(x_new)
        
        # Armijo condition
        if fx_new > fx + c1 * alpha * gtd:
            alpha_max = alpha
            alpha = (alpha_min + alpha_max) / 2
            continue
        
        g_new = grad_f(x_new)
        gtd_new = sum(gi * di for gi, di in zip(g_new, d))
        
        # Curvature condition
        if gtd_new < c2 * gtd:
            alpha_min = alpha
            if alpha_max == 1.0:
                alpha = 2 * alpha
            else:
                alpha = (alpha_min + alpha_max) / 2
            continue
        
        return alpha
    
    return alpha


def conjugate_gradient(
    f: Objective,
    grad_f: Gradient,
    x0: Vector,
    max_iter: int = None,
    tol: float = 1e-6,
) -> Vector:
    """
    Nonlinear conjugate gradient (Fletcher-Reeves).
    """
    x = x0[:]
    n = len(x)
    if max_iter is None:
        max_iter = n * 10
    
    g = grad_f(x)
    d = [-gi for gi in g]
    
    for _ in range(max_iter):
        g_norm = math.sqrt(sum(gi**2 for gi in g))
        if g_norm < tol:
            break
        
        # Line search
        alpha = line_search(f, grad_f, x, d)
        if alpha == 0:
            break
        
        x = [x[i] + alpha * d[i] for i in range(n)]
        g_new = grad_f(x)
        
        # Fletcher-Reeves beta
        beta = sum(gi**2 for gi in g_new) / sum(gi**2 for gi in g) if sum(gi**2 for gi in g) > 0 else 0
        
        d = [-g_new[i] + beta * d[i] for i in range(n)]
        g = g_new
    
    return x


def nelder_mead(
    f: Objective,
    x0: Vector,
    max_iter: int = 1000,
    tol: float = 1e-6,
    alpha: float = 1.0,
    gamma: float = 2.0,
    rho: float = 0.5,
    sigma: float = 0.5,
) -> Vector:
    """
    Nelder-Mead simplex method (derivative-free).
    """
    n = len(x0)
    # Initialize simplex
    simplex = [x0[:]]
    for i in range(n):
        vertex = x0[:]
        vertex[i] += 0.05 if x0[i] != 0 else 0.00025
        simplex.append(vertex)
    
    for _ in range(max_iter):
        # Evaluate
        f_vals = [f(v) for v in simplex]
        
        # Sort by function value
        idx = sorted(range(n + 1), key=lambda i: f_vals[i])
        simplex = [simplex[i] for i in idx]
        f_vals = [f_vals[i] for i in idx]
        
        # Check convergence
        if f_vals[-1] - f_vals[0] < tol:
            break
        
        # Centroid of all but worst
        centroid = [0.0] * n
        for i in range(n):
            centroid[i] = sum(simplex[j][i] for j in range(n)) / n
        
        # Reflection
        xr = [centroid[i] + alpha * (centroid[i] - simplex[-1][i]) for i in range(n)]
        fr = f(xr)
        
        if f_vals[0] <= fr < f_vals[-2]:
            simplex[-1] = xr
            continue
        
        # Expansion
        if fr < f_vals[0]:
            xe = [centroid[i] + gamma * (xr[i] - centroid[i]) for i in range(n)]
            fe = f(xe)
            if fe < fr:
                simplex[-1] = xe
            else:
                simplex[-1] = xr
            continue
        
        # Contraction
        if fr >= f_vals[-2]:
            if fr < f_vals[-1]:
                # Outside contraction
                xc = [centroid[i] + rho * (xr[i] - centroid[i]) for i in range(n)]
                fc = f(xc)
                if fc <= fr:
                    simplex[-1] = xc
                    continue
            else:
                # Inside contraction
                xc = [centroid[i] - rho * (centroid[i] - simplex[-1][i]) for i in range(n)]
                fc = f(xc)
                if fc < f_vals[-1]:
                    simplex[-1] = xc
                    continue
        
        # Shrink
        for i in range(1, n + 1):
            simplex[i] = [simplex[0][j] + sigma * (simplex[i][j] - simplex[0][j]) for j in range(n)]
    
    # Return best
    best_idx = min(range(n + 1), key=lambda i: f(simplex[i]))
    return simplex[best_idx]


def minimize(
    f: Objective,
    x0: Vector,
    method: str = "BFGS",
    grad: Optional[Gradient] = None,
    **kwargs,
) -> Vector:
    """
    General minimization interface.
    
    Methods: 'gradient_descent', 'adam', 'newton', 'conjugate_gradient', 
             'nelder_mead', 'BFGS', 'L-BFGS-B'
    """
    if grad is None and method in ('gradient_descent', 'adam', 'newton', 'conjugate_gradient', 'BFGS'):
        raise ValueError(f"Method {method} requires gradient function")
    
    if method == "gradient_descent":
        return gradient_descent(f, grad, x0, **kwargs)
    elif method == "adam":
        return adam(f, grad, x0, **kwargs)
    elif method == "newton":
        hess_f = kwargs.pop('hess', lambda x: [[1.0]*len(x0)]*len(x0))
        return newton_method_nd(f, grad, hess_f, x0, **kwargs)
    elif method == "conjugate_gradient":
        return conjugate_gradient(f, grad, x0, **kwargs)
    elif method == "nelder_mead":
        return nelder_mead(f, x0, **kwargs)
    else:
        raise ValueError(f"Unknown method: {method}")