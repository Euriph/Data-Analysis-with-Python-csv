from project.models import MultiLinearRegressionState

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
