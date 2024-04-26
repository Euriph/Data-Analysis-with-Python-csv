import pandas as pd
from datetime import datetime

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

def predict_value_for_date(date_obj, b0, b1):
    numeric_date = date_obj.toordinal()
    predicted_y = b0 + b1 * numeric_date
    return predicted_y


def calculate_mse(actual, predicted):
    return sum([(float(actual[i]) - predicted[i]) ** 2 for i in range(len(actual))]) / len(actual)

# Initialize the regression model
model = IncrementalLinearRegression()

# Create a simple dataset with known relationships: y = 2x + 1
data = {'Date': [datetime(2020, 1, 1), datetime(2020, 1, 2), datetime(2020, 1, 3)],
        'Value': [3, 5, 7]}
df_test = pd.DataFrame(data)
df_test['Date'] = pd.to_datetime(df_test['Date'])
df_test['Ordinal'] = df_test['Date'].apply(lambda x: x.toordinal())

# Update model with test data
for index, row in df_test.iterrows():
    model.update(row['Ordinal'], row['Value'])

# Check coefficients
b0, b1 = model.coefficients()
print("Calculated coefficients:")
print(f"Intercept (b0): {b0}, Slope (b1): {b1}")

# Expected coefficients are b1 = 2, b0 = -4032 (based on the ordinal date calculations)
# Predict and check the values
expected_values = [predict_value_for_date(x, b0, b1) for x in df_test['Date']]
print("Expected values:", df_test['Value'].tolist())
print("Predicted values:", expected_values)

# Calculate and print MSE
mse = calculate_mse(df_test['Value'], expected_values)
print("Mean Squared Error:", mse)
