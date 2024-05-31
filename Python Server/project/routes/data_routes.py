import base64
from io import BytesIO

import openai
import tiktoken
from flask import Blueprint, request, jsonify
from matplotlib import pyplot as plt

from project.config import OPENAI_API_KEY
from project.models import Session, WebAppRequestMaster, WebAppRequest, Coefficients, RegressionState
from project.utils import create_plot
import pandas as pd
from datetime import datetime
from sqlalchemy import func
from project.Regressions.IncrementalLinearRegression import IncrementalLinearRegression
from project.Regressions.IncrementalMultilinearRegression import IncrementalMultiLinearRegression
from project.Regressions.IncrementalLogisticRegression import IncrementalLogisticRegression


data_bp = Blueprint('data', __name__)

@data_bp.route('/submit_single_data', methods=['POST'])
def submit_single_data():
    data = request.json
    date = pd.to_datetime(data['date']).date()
    value = float(data['value'])
    user_name = data['username']
    session = Session()

    model = IncrementalLinearRegression(session)
    min_date = session.query(func.min(WebAppRequest.DataDate)).scalar() or date
    norm_date = (date - min_date).days
    model.update(norm_date, value)

    master_entry = WebAppRequestMaster(TimeStamp=datetime.now(), RecordCount=1, FileName="Single Data",
                                       UserName=user_name)
    session.add(master_entry)
    session.flush()
    dp = WebAppRequest(MasterUniqueId=master_entry.UniqueId, DataDate=date, DataValue=value)
    session.add(dp)

    coeffs = model.coefficients()
    coeffs_entry = Coefficients(ProcessDate=datetime.now(), b0=coeffs[0], b1=coeffs[1])
    session.add(coeffs_entry)
    session.commit()
    session.close()
    return jsonify({"message": "Single data submitted, model recalculated", "coefficients": coeffs}), 200

@data_bp.route('/upload_csv', methods=['POST'])
def upload_csv():
    file = request.files['file']
    df = pd.read_csv(file)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
    session = Session()
    model = IncrementalLinearRegression(session)

    database_min_date = session.query(func.min(WebAppRequest.DataDate)).scalar() or df['Date'].min()
    min_date = min(database_min_date, df['Date'].min())

    master_entry = WebAppRequestMaster(TimeStamp=datetime.now(), RecordCount=len(df), FileName=file.filename,
                                       UserName="API User")
    session.add(master_entry)
    session.flush()

    for index, row in df.iterrows():
        norm_date = (row['Date'] - min_date).days
        model.update(norm_date, row['Value'])
        dp = WebAppRequest(MasterUniqueId=master_entry.UniqueId, DataDate=row['Date'], DataValue=row['Value'])
        session.add(dp)

    coeffs = model.coefficients()
    coeffs_entry = Coefficients(ProcessDate=datetime.now(), b0=coeffs[0], b1=coeffs[1])
    session.add(coeffs_entry)
    session.commit()
    session.close()
    return jsonify({"message": "CSV uploaded and model recalculated", "coefficients": coeffs}), 200

@data_bp.route('/get_data_plot')
def get_data_plot():
    session = Session()
    model = IncrementalLinearRegression(session)

    data_points = session.query(WebAppRequest.DataDate, WebAppRequest.DataValue).order_by(WebAppRequest.DataDate).all()
    if not data_points:
        return jsonify({'message': 'No data available to plot'})

    dates = [dp.DataDate for dp in data_points]
    values = [dp.DataValue for dp in data_points]
    min_date = min(dates)
    x = [(date - min_date).days for date in dates]

    for day, value in zip(x, values):
        model.update(day, value)

    predicted = [model.predict(day) for day in x]
    mse = sum((p - v) ** 2 for p, v in zip(predicted, values)) / len(values) if values else float('inf')

    plot_data = create_plot(x, values, predicted)

    session.close()
    return jsonify({'image': plot_data, 'mse': mse})

# openai.api_key = "sk-proj-CYKnS0o1DtV9pBesZQTHT3BlbkFJ67dAw2PfmH3CaRtMrncG"
@data_bp.route('/generate_insights', methods=['POST'])
def generate_insights():
    data = request.json
    prompt = f"Generate a detailed insight based on this data: {data['summary']}"

    openai.api_key = OPENAI_API_KEY

    # Tokenize the prompt using tiktoken
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens = encoding.encode(prompt)
    token_count = len(tokens)

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        # Ensure the response handling matches the structure of the API response
        insight = response.choices[0].message.content
        return jsonify({"insight": insight, "token_count": token_count}), 200
    except Exception as e:
        data_bp.logger.error(f"Failed to generate insights: {str(e)}")
        return jsonify({"error": str(e)}), 500

@data_bp.route('/get_data_summary', methods=['GET'])
def get_data_summary():
    session = Session()
    model = IncrementalLinearRegression(session)

    # Fetch and summarize data
    data_points = session.query(WebAppRequest.DataDate, WebAppRequest.DataValue).order_by(WebAppRequest.DataDate).all()
    if not data_points:
        return jsonify({'message': 'No data available to summarize'})

    # Limit data points to a maximum of 100
    max_points = 100
    if len(data_points) > max_points:
        data_points = data_points[::len(data_points) // max_points]

    dates = [dp.DataDate for dp in data_points]
    values = [dp.DataValue for dp in data_points]
    min_date = min(dates)
    x = [(date - min_date).days for date in dates]

    for day, value in zip(x, values):
        model.update(day, value)

    predicted = [model.predict(day) for day in x]
    mse = sum((p - v) ** 2 for p, v in zip(predicted, values)) / len(values) if values else float('inf')
    coeffs = model.coefficients()

    # Generate plot
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

    summary = {
        'coefficients': {'b0': coeffs[0], 'b1': coeffs[1]},
        'mse': mse,
        'plot': plot_data,
        'data_points': [{'date': str(d), 'value': v} for d, v in zip(dates, values)]
    }

    session.close()
    return jsonify(summary)

# Routes for multi-linear and logistic regression
@data_bp.route('/submit_multi_data', methods=['POST'])
def submit_multi_data():
    data = request.json
    date = pd.to_datetime(data['date']).date()
    values = [float(v) for v in data['values']]  # Expecting multiple values
    target = float(data['target'])
    user_name = data['username']
    session = Session()

    model = IncrementalMultiLinearRegression(session)
    model.update(values, target)

    coeffs = model.coefficients()
    return jsonify({"message": "Multi-linear data submitted, model recalculated", "coefficients": coeffs}), 200

@data_bp.route('/submit_logistic_data', methods=['POST'])
def submit_logistic_data():
    data = request.json
    values = [float(v) for v in data['values']]  # Expecting multiple values
    target = int(data['target'])  # Binary target (0 or 1)
    user_name = data['username']
    session = Session()

    model = IncrementalLogisticRegression(session)
    model.update(values, target)

    coeffs = model.coefficients()
    return jsonify({"message": "Logistic data submitted, model recalculated", "coefficients": coeffs}), 200
