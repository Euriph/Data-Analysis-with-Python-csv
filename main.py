import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import glob

def read_data(filename):
    return pd.read_csv(filename)

def save_data(df, filename):
    df.to_csv(filename, index=False)

def predict_value_for_date(date_obj, b0, b1):
    numeric_date = date_obj.toordinal()
    predicted_y = b0 + b1 * numeric_date
    return predicted_y

def calculate_mse(actual, predicted):
    return sum([(float(actual[i]) - predicted[i]) ** 2 for i in range(len(actual))]) / len(actual)

def plot_data(df, b0, b1):
    plt.scatter(df['Date'], df['Value'], color='blue', label='Actual Data')
    dates = pd.to_datetime(df['Date'])
    predicted_values = [predict_value_for_date(date, b0, b1) for date in dates]
    plt.plot(dates, predicted_values, color='red', label='Predicted Values')
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.title('Actual Data and Predictions')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

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


def combine_csv_files(directory_path):
    data_frames = []
    csv_files = glob.glob(os.path.join(directory_path, '*.csv'))

    # Exclude Combined_Data.csv if it exists in the directory
    csv_files = [f for f in csv_files if not f.endswith('Combined_Data.csv')]

    for file in csv_files:
        df = pd.read_csv(file)
        data_frames.append(df)
        print(f'Finished reading: {file}')

    if data_frames:  # Check if there are any data frames to combine
        combined_df = pd.concat(data_frames, ignore_index=True)
        combined_df.to_csv(os.path.join(directory_path, 'Data Values/Combined_Data.csv'), index=False)

    # Rename the original files to mark as done
    for file in csv_files:
        os.rename(file, file.replace('.csv', '.done'))

    # Reload Combined_Data.csv to ensure it is up to date
    if os.path.exists(os.path.join(directory_path, 'Data Values/Combined_Data.csv')):
        return pd.read_csv(os.path.join(directory_path, 'Data Values/Combined_Data.csv'))
    else:
        return pd.DataFrame(columns=['Date', 'Value'])  # Return an empty DataFrame if no CSV was combined

# Define the path to the directory containing the CSV files
directory_path = 'C:\\Users\\Ilyas work\\PycharmProjects\\Data Analysis\\Data-Analysis-with-Python'

# Combine CSV files and get the combined DataFrame
df = combine_csv_files(directory_path)
df['Date'] = pd.to_datetime(df['Date'])

# Initialize the regression model and update it with combined data
model = IncrementalLinearRegression()
for index, row in df.iterrows():
    ordinal_date = row['Date'].toordinal()
    model.update(ordinal_date, row['Value'])

# Main interactive loop
while True:
    date_str = input("Enter a date (YYYY-MM-DD), or type 'exit' to quit: ")
    if date_str.lower() == 'exit':
        break
    date_obj = pd.to_datetime(date_str)
    ordinal_date = date_obj.toordinal()
    predicted_value = predict_value_for_date(date_obj, *model.coefficients())
    print("Predicted value for", date_str, "is", predicted_value)
    actual_value = float(input("Enter actual value for this date: "))
    error = abs(actual_value - predicted_value)
    print(f"Absolute Error between actual and predicted value: {error}")
    if actual_value != 0:
        percentage_error = (error / actual_value) * 100
        print(f"Percentage Error: {percentage_error:.2f}%")
    new_row = {'Date': date_obj, 'Value': actual_value}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    model.update(ordinal_date, actual_value)
    plot_data(df, *model.coefficients())
    actual_values = df['Value'].tolist()
    predicted_values = [predict_value_for_date(date, *model.coefficients()) for date in pd.to_datetime(df['Date'])]
    mse = calculate_mse(actual_values, predicted_values)
    print("Mean Squared Error:", mse)

# Optionally save the updated DataFrame to CSV
save_data(df, os.path.join(directory_path, 'Data Values/Combined_Data.csv'))

print("Exited the loop. Data saved to", os.path.join(directory_path, 'Data Values/Combined_Data.csv'))
