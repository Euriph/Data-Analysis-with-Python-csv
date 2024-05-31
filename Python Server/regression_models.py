import numpy as np
from sklearn.linear_model import LogisticRegression
from models import RegressionState, MultiLinearRegressionState, LogisticRegressionState

class IncrementalLinearRegression:
    def __init__(self, session):
        self.session = session
        state = self.session.query(RegressionState).first()
        if state:
            self.S_x = state.S_x
            self.S_y = state.S_y
            self.S_xx = state.S_xx
            self.S_xy = state.S_xy
            self.n = state.Count
        else:
            self.S_x = 0
            self.S_y = 0
            self.S_xx = 0
            self.S_xy = 0
            self.n = 0

    def update(self, x_new, y_new):
        self.S_x += x_new
        self.S_y += y_new
        self.S_xx += x_new ** 2
        self.S_xy += x_new * y_new
        self.n += 1
        state = self.session.query(RegressionState).first()
        if state:
            state.S_x = self.S_x
            state.S_y = self.S_y
            state.S_xx = self.S_xx
            state.S_xy = self.S_xy
            state.Count = self.n
        else:
            state = RegressionState(S_x=self.S_x, S_y=self.S_y, S_xx=self.S_xx, S_xy=self.S_xy, Count=self.n)
            self.session.add(state)
        self.session.commit()

    def coefficients(self):
        if self.n * self.S_xx - self.S_x**2 == 0:
            return float('inf'), float('inf')
        b1 = (self.n * self.S_xy - self.S_x * self.S_y) / (self.n * self.S_xx - self.S_x**2)
        b0 = (self.S_y - b1 * self.S_x) / self.n
        return b0, b1

    def predict(self, x):
        b0, b1 = self.coefficients()
        return b0 + b1 * x

class IncrementalMultiLinearRegression:
    def __init__(self, session):
        self.session = session
        state = self.session.query(MultiLinearRegressionState).first()
        if state:
            self.feature_sums = state.FeatureSums
            self.target_sums = state.TargetSums
            self.feature_target_sums = state.FeatureTargetSums
            self.n = state.Count
        else:
            self.feature_sums = {}
            self.target_sums = 0
            self.feature_target_sums = {}
            self.n = 0

    def update(self, X_new, y_new):
        for i, x in enumerate(X_new):
            if i not in self.feature_sums:
                self.feature_sums[i] = 0
                self.feature_target_sums[i] = 0
            self.feature_sums[i] += x
            self.feature_target_sums[i] += x * y_new
        self.target_sums += y_new
        self.n += 1
        state = self.session.query(MultiLinearRegressionState).first()
        if state:
            state.FeatureSums = self.feature_sums
            state.TargetSums = self.target_sums
            state.FeatureTargetSums = self.feature_target_sums
            state.Count = self.n
        else:
            state = MultiLinearRegressionState(
                FeatureSums=self.feature_sums,
                TargetSums=self.target_sums,
                FeatureTargetSums=self.feature_target_sums,
                Count=self.n
            )
            self.session.add(state)
        self.session.commit()

    def coefficients(self):
        X = np.array([self.feature_sums[i] for i in sorted(self.feature_sums)])
        y = self.target_sums
        XtX_inv = np.linalg.inv(np.dot(X.T, X))
        XtY = np.dot(X.T, y)
        coefs = np.dot(XtX_inv, XtY)
        return coefs

    def predict(self, X):
        coefs = self.coefficients()
        return np.dot(coefs, X)

class IncrementalLogisticRegression:
    def __init__(self, session):
        self.session = session
        state = self.session.query(LogisticRegressionState).first()
        if state:
            self.feature_sums = state.FeatureSums
            self.target_counts = state.TargetCounts
            self.feature_target_sums = state.FeatureTargetSums
            self.n = state.Count
        else:
            self.feature_sums = {}
            self.target_counts = {'0': 0, '1': 0}
            self.feature_target_sums = {}
            self.n = 0

    def update(self, X_new, y_new):
        for i, x in enumerate(X_new):
            if i not in self.feature_sums:
                self.feature_sums[i] = 0
                self.feature_target_sums[i] = 0
            self.feature_sums[i] += x
            self.feature_target_sums[i] += x * y_new
        self.target_counts[str(y_new)] += 1
        self.n += 1
        state = self.session.query(LogisticRegressionState).first()
        if state:
            state.FeatureSums = self.feature_sums
            state.TargetCounts = self.target_counts
            state.FeatureTargetSums = self.feature_target_sums
            state.Count = self.n
        else:
            state = LogisticRegressionState(
                FeatureSums=self.feature_sums,
                TargetCounts=self.target_counts,
                FeatureTargetSums=self.feature_target_sums,
                Count=self.n
            )
            self.session.add(state)
        self.session.commit()

    def coefficients(self):
        X = np.array([self.feature_sums[i] for i in sorted(self.feature_sums)])
        y = np.array([self.target_counts['0'], self.target_counts['1']])
        model = LogisticRegression()
        model.fit(X, y)
        return model.intercept_, model.coef_

    def predict(self, X):
        coefs = self.coefficients()
        return np.dot(coefs, X)
