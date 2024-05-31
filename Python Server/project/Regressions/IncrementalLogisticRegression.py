from project.models import LogisticRegressionState

# Incremental Logistic Regression
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