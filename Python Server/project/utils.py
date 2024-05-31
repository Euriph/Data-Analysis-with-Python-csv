import base64
from io import BytesIO
import matplotlib.pyplot as plt

def create_plot(x, values, predicted):
    plt.figure(figsize=(6, 4), dpi=80)  # Smaller size and lower resolution
    plt.plot(x, values, marker='o', linestyle='-', color='blue', label='Actual')
    plt.plot(x, predicted, linestyle='-', color='red', label='Predicted')
    plt.title('Data Plot Over Time')
    plt.xlabel('Days from start')
    plt.ylabel('Data Value')
    plt.legend()
    plt.grid(True)

    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    plot_data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return plot_data
