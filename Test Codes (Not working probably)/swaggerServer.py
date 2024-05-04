from flask import Flask, request, jsonify
from flask_swagger_ui import get_swaggerui_blueprint
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from datetime import datetime

# Create Flask app
app = Flask(__name__)

# Swagger UI setup
SWAGGER_URL = '/swagger'
API_URL = '/swagger.yaml'
swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL, config={'app_name': "Data Processing API"})
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://@DESKTOP-T376648/DataAnalysisProject?driver=SQL+Server&Trusted_Connection=yes'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define a model for storing data
class DataEntry(db.Model):
    __tablename__ = 'DataEntries'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    entry_date = db.Column(db.Date, nullable=True)
    entry_value = db.Column(db.Float, nullable=True)

# Create all tables
with app.app_context():
    db.create_all()

# Helper functions
def predict_value_for_date(date_obj, b0, b1):
    numeric_date = date_obj.toordinal()
    predicted_y = b0 + b1 * numeric_date
    return predicted_y

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

# Route for predicting a value
@app.route('/predict', methods=['POST'])
def predict_value():
    try:
        date_str = request.json.get('date')
        date_obj = datetime.strptime(date_str, '%Y-%MM-DD')

        # Retrieve all records from the database
        records = DataEntry.query.all()
        x_vals = [r.entry_date.toordinal() for r in records]
        y_vals = [r.entry_value for r in records]

        model = IncrementalLinearRegression()
        for x, y in zip(x_vals, y_vals):
            model.update(x, y)

        predicted_value = predict_value_for_date(date_obj, *model.coefficients())
        return jsonify({'predicted_value': predicted_value})

    except Exception as e:
        return jsonify({'error': str(e)})

# Route for uploading CSV
@app.route('/upload', methods=['POST'])
def upload_csv():
    try:
        file = request.files['file']
        df = pd.read_csv(file)

        for _, row in df.iterrows():
            date_obj = pd.to_datetime(row['Date'])
            new_entry = DataEntry(entry_date=date_obj, entry_value=row['Value'])
            db.session.add(new_entry)

        db.session.commit()
        return jsonify({'status': 'success'})

    except Exception as e:
        db.session.rollback()  # Roll back the transaction in case of an error
        return jsonify({'error': str(e)})

# Running the app
if __name__ == '__main__':
    app.run(debug=True)
