from server import RegressionState

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
        # Save the updated state back to the database
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
