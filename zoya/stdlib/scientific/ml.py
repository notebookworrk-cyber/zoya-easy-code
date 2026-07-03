"""Zoya 4.0 Scientific Computing - Machine Learning primitives."""

from typing import List, Tuple, Optional, Callable, Union
import math
import random

Vector = List[float]
Matrix = List[List[float]]
Data = List[Vector]


def dot(a: Vector, b: Vector) -> float:
    return sum(x * y for x, y in zip(a, b))


def matvec(A: Matrix, v: Vector) -> Vector:
    return [sum(A[i][j] * v[j] for j in range(len(v))) for i in range(len(A))]


def matmul(A: Matrix, B: Matrix) -> Matrix:
    if not A or not B:
        return []
    rows, cols = len(A), len(B[0])
    inner = len(B)
    return [[sum(A[i][k] * B[k][j] for k in range(inner)) for j in range(cols)] for i in range(rows)]


def transpose(A: Matrix) -> Matrix:
    if not A:
        return []
    return [[A[i][j] for i in range(len(A))] for j in range(len(A[0]))]


def add_bias(X: Matrix) -> Matrix:
    """Add bias column (1s) to feature matrix."""
    return [[1.0] + row for row in X]


def sigmoid(x: float) -> float:
    """Sigmoid activation."""
    if x > 20:
        return 1.0
    if x < -20:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def sigmoid_derivative(x: float) -> float:
    s = sigmoid(x)
    return s * (1 - s)


def softmax(x: Vector) -> Vector:
    """Softmax activation."""
    m = max(x)
    exps = [math.exp(xi - m) for xi in x]
    s = sum(exps)
    return [e / s for e in exps]


def mse_loss(y_true: Vector, y_pred: Vector) -> float:
    """Mean squared error."""
    return sum((yt - yp) ** 2 for yt, yp in zip(y_true, y_pred)) / len(y_true)


def mse_grad(y_true: Vector, y_pred: Vector) -> Vector:
    """Gradient of MSE."""
    n = len(y_true)
    return [2 * (yp - yt) / n for yt, yp in zip(y_true, y_pred)]


def cross_entropy_loss(y_true: Vector, y_pred: Vector) -> float:
    """Binary cross entropy."""
    eps = 1e-15
    y_pred = [max(eps, min(1 - eps, p)) for p in y_pred]
    return -sum(yt * math.log(yp) + (1 - yt) * math.log(1 - yp) for yt, yp in zip(y_true, y_pred)) / len(y_true)


class LinearRegression:
    """Ordinary Least Squares Linear Regression."""
    
    def __init__(self, fit_intercept: bool = True):
        self.fit_intercept = fit_intercept
        self.coef_: Optional[Vector] = None
        self.intercept_: float = 0.0
        self._fitted = False
    
    def fit(self, X: Matrix, y: Vector) -> "LinearRegression":
        """Fit OLS model."""
        if self.fit_intercept:
            X = add_bias(X)
        
        # Normal equation: (X^T X) w = X^T y
        XT = transpose(X)
        XTX = matmul(XT, X)
        XTy = matvec(XT, y)
        
        # Solve using our linear solver
        from zoya.stdlib.scientific.linear import solve
        try:
            w = solve(XTX, XTy)
        except ValueError:
            # Add regularization if singular
            n = len(XTX)
            for i in range(n):
                XTX[i][i] += 1e-6
            w = solve(XTX, XTy)
        
        if self.fit_intercept:
            self.intercept_ = w[0]
            self.coef_ = w[1:]
        else:
            self.intercept_ = 0.0
            self.coef_ = w
        
        self._fitted = True
        return self
    
    def predict(self, X: Matrix) -> Vector:
        """Predict using fitted model."""
        if not self._fitted:
            raise ValueError("Model not fitted")
        return [self.intercept_ + dot(row, self.coef_) for row in X]
    
    def score(self, X: Matrix, y: Vector) -> float:
        """R^2 score."""
        y_pred = self.predict(X)
        y_mean = sum(y) / len(y)
        ss_res = sum((yt - yp) ** 2 for yt, yp in zip(y, y_pred))
        ss_tot = sum((yt - y_mean) ** 2 for yt in y)
        if ss_tot == 0:
            return 1.0
        return 1 - ss_res / ss_tot


class RidgeRegression(LinearRegression):
    """Ridge Regression (L2 regularization)."""
    
    def __init__(self, alpha: float = 1.0, fit_intercept: bool = True):
        super().__init__(fit_intercept)
        self.alpha = alpha
    
    def fit(self, X: Matrix, y: Vector) -> "RidgeRegression":
        if self.fit_intercept:
            X = add_bias(X)
        
        XT = transpose(X)
        XTX = matmul(XT, X)
        XTy = matvec(XT, y)
        
        # Add L2 penalty: (X^T X + alpha * I) w = X^T y
        n = len(XTX)
        for i in range(n):
            XTX[i][i] += self.alpha
        
        from zoya.stdlib.scientific.linear import solve
        w = solve(XTX, XTy)
        
        if self.fit_intercept:
            self.intercept_ = w[0]
            self.coef_ = w[1:]
        else:
            self.intercept_ = 0.0
            self.coef_ = w
        
        self._fitted = True
        return self


class LassoRegression:
    """Lasso Regression (L1 regularization) via coordinate descent."""
    
    def __init__(self, alpha: float = 1.0, fit_intercept: bool = True, max_iter: int = 1000, tol: float = 1e-4):
        self.alpha = alpha
        self.fit_intercept = fit_intercept
        self.max_iter = max_iter
        self.tol = tol
        self.coef_: Optional[Vector] = None
        self.intercept_: float = 0.0
        self._fitted = False
    
    def fit(self, X: Matrix, y: Vector) -> "LassoRegression":
        if self.fit_intercept:
            X = add_bias(X)
        
        n_samples, n_features = len(X), len(X[0])
        w = [0.0] * n_features
        
        # Precompute X^T X and X^T y
        XT = transpose(X)
        XTX = matmul(XT, X)
        XTy = matvec(XT, y)
        
        for _ in range(self.max_iter):
            max_change = 0.0
            for j in range(n_features):
                old_w = w[j]
                # Skip intercept regularization
                if self.fit_intercept and j == 0:
                    w[j] = XTy[j] - sum(XTX[j][k] * w[k] for k in range(n_features) if k != j)
                    w[j] /= XTX[j][j]
                    max_change = max(max_change, abs(w[j] - old_w))
                    continue
                
                # Coordinate descent update
                rho = XTy[j] - sum(XTX[j][k] * w[k] for k in range(n_features) if k != j)
                if rho < -self.alpha:
                    w[j] = (rho + self.alpha) / XTX[j][j]
                elif rho > self.alpha:
                    w[j] = (rho - self.alpha) / XTX[j][j]
                else:
                    w[j] = 0.0
                
                max_change = max(max_change, abs(w[j] - old_w))
            
            if max_change < self.tol:
                break
        
        if self.fit_intercept:
            self.intercept_ = w[0]
            self.coef_ = w[1:]
        else:
            self.intercept_ = 0.0
            self.coef_ = w
        self._fitted = True
        return self
    
    def predict(self, X: Matrix) -> Vector:
        if not self._fitted:
            raise ValueError("Model not fitted")
        return [self.intercept_ + dot(row, self.coef_) for row in X]

    def score(self, X: Matrix, y: Vector) -> float:
        """R^2 score."""
        y_pred = self.predict(X)
        y_mean = sum(y) / len(y)
        ss_res = sum((yt - yp) ** 2 for yt, yp in zip(y, y_pred))
        ss_tot = sum((yt - y_mean) ** 2 for yt in y)
        if ss_tot == 0:
            return 1.0
        return 1 - ss_res / ss_tot


class LogisticRegression:
    """Binary Logistic Regression with gradient descent."""
    
    def __init__(self, learning_rate: float = 0.01, max_iter: int = 1000, tol: float = 1e-4, 
                 fit_intercept: bool = True, C: float = 1.0):
        self.learning_rate = learning_rate
        self.max_iter = max_iter
        self.tol = tol
        self.fit_intercept = fit_intercept
        self.C = C  # Inverse regularization strength
        self.coef_: Optional[Vector] = None
        self.intercept_: float = 0.0
        self._fitted = False
    
    def _sigmoid(self, z: float) -> float:
        if z > 20:
            return 1.0
        if z < -20:
            return 0.0
        return 1.0 / (1.0 + math.exp(-z))
    
    def fit(self, X: Matrix, y: Vector) -> "LogisticRegression":
        if self.fit_intercept:
            X = add_bias(X)
        
        n_samples, n_features = len(X), len(X[0])
        w = [0.0] * n_features
        
        for _ in range(self.max_iter):
            grad = [0.0] * n_features
            for i in range(n_samples):
                z = dot(X[i], w)
                p = self._sigmoid(z)
                error = p - y[i]
                for j in range(n_features):
                    grad[j] += error * X[i][j]
            
            # Regularization (except intercept)
            for j in range(n_features):
                if self.fit_intercept and j == 0:
                    grad[j] /= n_samples
                else:
                    grad[j] = grad[j] / n_samples + w[j] / (self.C * n_samples)
            
            # Update
            max_change = 0.0
            for j in range(n_features):
                change = self.learning_rate * grad[j]
                w[j] -= change
                max_change = max(max_change, abs(change))
            
            if max_change < self.tol:
                break
        
        if self.fit_intercept:
            self.intercept_ = w[0]
            self.coef_ = w[1:]
        else:
            self.intercept_ = 0.0
            self.coef_ = w
        self._fitted = True
        return self
    
    def predict_proba(self, X: Matrix) -> List[Vector]:
        if not self._fitted:
            raise ValueError("Model not fitted")
        probs = []
        for row in X:
            z = self.intercept_ + dot(row, self.coef_)
            p = self._sigmoid(z)
            probs.append([1 - p, p])
        return probs
    
    def predict(self, X: Matrix) -> Vector:
        probs = self.predict_proba(X)
        return [1 if p[1] > 0.5 else 0 for p in probs]
    
    def score(self, X: Matrix, y: Vector) -> float:
        """Accuracy."""
        preds = self.predict(X)
        return sum(1 for p, t in zip(preds, y) if p == t) / len(y)


class KMeans:
    """K-Means Clustering."""
    
    def __init__(self, n_clusters: int = 8, max_iter: int = 300, tol: float = 1e-4, 
                 random_state: Optional[int] = None):
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.tol = tol
        self.random_state = random_state
        self.cluster_centers_: Optional[Matrix] = None
        self.labels_: Optional[Vector] = None
        self._fitted = False
    
    def _distance(self, a: Vector, b: Vector) -> float:
        return sum((x - y) ** 2 for x, y in zip(a, b))
    
    def fit(self, X: Matrix) -> "KMeans":
        if self.random_state is not None:
            random.seed(self.random_state)
        
        n_samples, n_features = len(X), len(X[0])
        
        # Initialize centroids (k-means++)
        centroids = [X[random.randrange(n_samples)]]
        for _ in range(1, self.n_clusters):
            dists = [min(self._distance(x, c) for c in centroids) for x in X]
            total = sum(dists)
            r = random.random() * total
            cumsum = 0
            for i, d in enumerate(dists):
                cumsum += d
                if cumsum >= r:
                    centroids.append(X[i])
                    break
        
        for _ in range(self.max_iter):
            # Assign clusters
            labels = []
            for x in X:
                best = min(range(self.n_clusters), key=lambda k: self._distance(x, centroids[k]))
                labels.append(best)
            
            # Update centroids
            new_centroids = [[0.0] * n_features for _ in range(self.n_clusters)]
            counts = [0] * self.n_clusters
            for i, label in enumerate(labels):
                counts[label] += 1
                for j in range(n_features):
                    new_centroids[label][j] += X[i][j]
            
            for k in range(self.n_clusters):
                if counts[k] > 0:
                    centroids[k] = [v / counts[k] for v in new_centroids[k]]
            
            # Check convergence
            if all(self._distance(centroids[i], new_centroids[i]) < self.tol for i in range(self.n_clusters)):
                break
        
        self.cluster_centers_ = centroids
        self.labels_ = labels
        self._fitted = True
        return self
    
    def predict(self, X: Matrix) -> Vector:
        if not self._fitted:
            raise ValueError("Model not fitted")
        return [min(range(self.n_clusters), key=lambda k: self._distance(x, self.cluster_centers_[k])) for x in X]
    
    def fit_predict(self, X: Matrix) -> Vector:
        self.fit(X)
        return self.labels_


class GaussianNB:
    """Gaussian Naive Bayes."""
    
    def __init__(self, var_smoothing: float = 1e-9):
        self.var_smoothing = var_smoothing
        self.classes_: List = []
        self.class_prior_: List[float] = []
        self.theta_: Matrix = []  # Mean per class
        self.var_: Matrix = []    # Variance per class
        self._fitted = False
    
    def fit(self, X: Matrix, y: Vector) -> "GaussianNB":
        self.classes_ = sorted(set(y))
        n_classes = len(self.classes_)
        n_features = len(X[0])
        
        self.class_prior_ = [0.0] * n_classes
        self.theta_ = [[0.0] * n_features for _ in range(n_classes)]
        self.var_ = [[0.0] * n_features for _ in range(n_classes)]
        
        for i, c in enumerate(self.classes_):
            X_c = [row for row, label in zip(X, y) if label == c]
            self.class_prior_[i] = len(X_c) / len(X)
            
            for j in range(n_features):
                feat = [row[j] for row in X_c]
                self.theta_[i][j] = sum(feat) / len(feat)
                self.var_[i][j] = sum((x - self.theta_[i][j]) ** 2 for x in feat) / len(feat) + self.var_smoothing
        
        self._fitted = True
        return self
    
    def _log_prob(self, x: Vector, class_idx: int) -> float:
        log_prob = math.log(self.class_prior_[class_idx])
        for j, val in enumerate(x):
            mean, var = self.theta_[class_idx][j], self.var_[class_idx][j]
            log_prob += -0.5 * (math.log(2 * math.pi * var) + (val - mean) ** 2 / var)
        return log_prob
    
    def predict_proba(self, X: Matrix) -> List[Vector]:
        if not self._fitted:
            raise ValueError("Model not fitted")
        result = []
        for row in X:
            log_probs = [self._log_prob(row, i) for i in range(len(self.classes_))]
            max_log = max(log_probs)
            exp_probs = [math.exp(lp - max_log) for lp in log_probs]
            total = sum(exp_probs)
            result.append([p / total for p in exp_probs])
        return result
    
    def predict(self, X: Matrix) -> Vector:
        probs = self.predict_proba(X)
        return [self.classes_[p.index(max(p))] for p in probs]
    
    def score(self, X: Matrix, y: Vector) -> float:
        preds = self.predict(X)
        return sum(1 for p, t in zip(preds, y) if p == t) / len(y)


class DecisionTreeClassifier:
    """Simple Decision Tree Classifier (ID3/C4.5 style)."""
    
    def __init__(self, max_depth: int = 5, min_samples_split: int = 2, 
                 min_samples_leaf: int = 1, criterion: str = "gini"):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.criterion = criterion
        self.tree_ = None
        self._fitted = False
    
    def _gini(self, y: Vector) -> float:
        counts = {}
        for label in y:
            counts[label] = counts.get(label, 0) + 1
        n = len(y)
        return 1 - sum((c / n) ** 2 for c in counts.values())
    
    def _entropy(self, y: Vector) -> float:
        counts = {}
        for label in y:
            counts[label] = counts.get(label, 0) + 1
        n = len(y)
        return -sum((c / n) * math.log2(c / n) for c in counts.values() if c > 0)
    
    def _impurity(self, y: Vector) -> float:
        return self._gini(y) if self.criterion == "gini" else self._entropy(y)
    
    def _best_split(self, X: Matrix, y: Vector) -> Tuple[int, float]:
        n_samples, n_features = len(X), len(X[0])
        best_gain = -1
        best_feature = -1
        best_threshold = 0
        
        current_impurity = self._impurity(y)
        
        for feature in range(n_features):
            values = sorted(set(row[feature] for row in X))
            thresholds = [(values[i] + values[i+1]) / 2 for i in range(len(values)-1)]
            
            for threshold in thresholds:
                left_y = [y[i] for i in range(n_samples) if X[i][feature] <= threshold]
                right_y = [y[i] for i in range(n_samples) if X[i][feature] > threshold]
                
                if len(left_y) < self.min_samples_leaf or len(right_y) < self.min_samples_leaf:
                    continue
                
                n_left, n_right = len(left_y), len(right_y)
                weighted_impurity = (n_left / n_samples) * self._impurity(left_y) + \
                                   (n_right / n_samples) * self._impurity(right_y)
                gain = current_impurity - weighted_impurity
                
                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature
                    best_threshold = threshold
        
        return best_feature, best_threshold
    
    def _build_tree(self, X: Matrix, y: Vector, depth: int) -> dict:
        if depth >= self.max_depth or len(set(y)) == 1 or len(y) < self.min_samples_split:
            return {"leaf": True, "class": max(set(y), key=y.count)}
        
        feature, threshold = self._best_split(X, y)
        if feature == -1:
            return {"leaf": True, "class": max(set(y), key=y.count)}
        
        left_idx = [i for i, row in enumerate(X) if row[feature] <= threshold]
        right_idx = [i for i, row in enumerate(X) if row[feature] > threshold]
        
        return {
            "leaf": False,
            "feature": feature,
            "threshold": threshold,
            "left": self._build_tree([X[i] for i in left_idx], [y[i] for i in left_idx], depth + 1),
            "right": self._build_tree([X[i] for i in right_idx], [y[i] for i in right_idx], depth + 1)
        }
    
    def fit(self, X: Matrix, y: Vector) -> "DecisionTreeClassifier":
        self.tree_ = self._build_tree(X, y, 0)
        self._fitted = True
        return self
    
    def _predict_one(self, x: Vector, tree: dict) -> any:
        if tree["leaf"]:
            return tree["class"]
        if x[tree["feature"]] <= tree["threshold"]:
            return self._predict_one(x, tree["left"])
        return self._predict_one(x, tree["right"])
    
    def predict(self, X: Matrix) -> Vector:
        if not self._fitted:
            raise ValueError("Model not fitted")
        return [self._predict_one(row, self.tree_) for row in X]
    
    def score(self, X: Matrix, y: Vector) -> float:
        preds = self.predict(X)
        return sum(1 for p, t in zip(preds, y) if p == t) / len(y)


class RandomForestClassifier:
    """Random Forest (ensemble of decision trees)."""
    
    def __init__(self, n_estimators: int = 100, max_depth: int = 5, 
                 max_features: str = "sqrt", random_state: Optional[int] = None):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.max_features = max_features
        self.random_state = random_state
        self.estimators_ = []
        self._fitted = False
    
    def _sample_features(self, n: int) -> List[int]:
        if self.max_features == "sqrt":
            k = int(math.sqrt(n))
        elif self.max_features == "log2":
            k = int(math.log2(n))
        else:
            k = n
        return random.sample(range(n), max(1, k))
    
    def fit(self, X: Matrix, y: Vector) -> "RandomForestClassifier":
        if self.random_state is not None:
            random.seed(self.random_state)
        
        n_samples, n_features = len(X), len(X[0])
        
        for _ in range(self.n_estimators):
            # Bootstrap sample
            idx = [random.randrange(n_samples) for _ in range(n_samples)]
            X_boot = [X[i] for i in idx]
            y_boot = [y[i] for i in idx]
            
            # Feature subset
            feat_idx = self._sample_features(n_features)
            X_sub = [[row[j] for j in feat_idx] for row in X_boot]
            
            tree = DecisionTreeClassifier(max_depth=self.max_depth)
            tree.fit(X_sub, y_boot)
            self.estimators_.append((tree, feat_idx))
        
        self._fitted = True
        return self
    
    def predict(self, X: Matrix) -> Vector:
        if not self._fitted:
            raise ValueError("Model not fitted")
        
        # Majority vote
        preds = [[tree.predict([[row[j] for j in feat_idx] for row in X])[i] 
                  for tree, feat_idx in self.estimators_] for i in range(len(X))]
        
        return [max(set(p), key=p.count) for p in preds]
    
    def score(self, X: Matrix, y: Vector) -> float:
        preds = self.predict(X)
        return sum(1 for p, t in zip(preds, y) if p == t) / len(y)


def train_test_split(
    X: Matrix, y: Vector, test_size: float = 0.25, 
    random_state: Optional[int] = None, shuffle: bool = True
) -> Tuple[Matrix, Matrix, Vector, Vector]:
    """Split data into train/test sets."""
    if random_state is not None:
        random.seed(random_state)
    
    n = len(X)
    indices = list(range(n))
    if shuffle:
        random.shuffle(indices)
    
    split = int(n * (1 - test_size))
    train_idx, test_idx = indices[:split], indices[split:]
    
    X_train = [X[i] for i in train_idx]
    X_test = [X[i] for i in test_idx]
    y_train = [y[i] for i in train_idx]
    y_test = [y[i] for i in test_idx]
    
    return X_train, X_test, y_train, y_test


def accuracy_score(y_true: Vector, y_pred: Vector) -> float:
    return sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)


def precision_score(y_true: Vector, y_pred: Vector, pos_label: any = 1) -> float:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == pos_label and p == pos_label)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != pos_label and p == pos_label)
    return tp / (tp + fp) if (tp + fp) > 0 else 0


def recall_score(y_true: Vector, y_pred: Vector, pos_label: any = 1) -> float:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == pos_label and p == pos_label)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == pos_label and p != pos_label)
    return tp / (tp + fn) if (tp + fn) > 0 else 0


def f1_score(y_true: Vector, y_pred: Vector, pos_label: any = 1) -> float:
    p = precision_score(y_true, y_pred, pos_label)
    r = recall_score(y_true, y_pred, pos_label)
    return 2 * p * r / (p + r) if (p + r) > 0 else 0


def confusion_matrix(y_true: Vector, y_pred: Vector, labels: Optional[List] = None) -> Matrix:
    if labels is None:
        labels = sorted(set(y_true) | set(y_pred))
    n = len(labels)
    cm = [[0] * n for _ in range(n)]
    label_to_idx = {l: i for i, l in enumerate(labels)}
    for t, p in zip(y_true, y_pred):
        cm[label_to_idx[t]][label_to_idx[p]] += 1
    return cm


def classification_report(y_true: Vector, y_pred: Vector, labels: Optional[List] = None) -> str:
    if labels is None:
        labels = sorted(set(y_true) | set(y_pred))
    
    report = "              precision    recall  f1-score   support\n\n"
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        support = sum(1 for t in y_true if t == label)
        
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        
        report += f"          {label}     {prec:.2f}     {rec:.2f}     {f1:.2f}        {support}\n"
    
    acc = accuracy_score(y_true, y_pred)
    report += f"\n    accuracy                         {acc:.2f}      {len(y_true)}"
    return report