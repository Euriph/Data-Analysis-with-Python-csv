class IncrementalLinearRegression:
    def __init__(self):
        self.S_x = 0
        self.S_y = 0
        self.S_xx = 0
        self.S_xy = 0
        self.n = 0

    def update(self, x_new, y_new):
        self.S_x += x_new
        self.S_y += float(y_new)
        self.S_xx += x_new**2
        self.S_xy += x_new * float(y_new)
        self.n += 1

    def coefficients(self):
        if self.n * self.S_xx - self.S_x**2 == 0:
            return float('inf'), float('inf')
        b1 = (self.n * self.S_xy - self.S_x * self.S_y) / (self.n * self.S_xx - self.S_x**2)
        b0 = (self.S_y - b1 * self.S_x) / self.n
        return b0, b1