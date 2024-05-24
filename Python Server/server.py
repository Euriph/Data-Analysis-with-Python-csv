from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, String, ForeignKey, func, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import pandas as pd
from datetime import datetime
from flask_cors import CORS
import base64
from io import BytesIO
import matplotlib.pyplot as plt

app = Flask(__name__)
CORS(app)
engine = create_engine('mysql+pymysql://root:123578951@localhost/dataanalysisproject')
Session = sessionmaker(bind=engine)
Base = declarative_base()


class WebAppRequestMaster(Base):
    __tablename__ = 'TblWebAppRequestMaster'
    UniqueId = Column(Integer, primary_key=True, autoincrement=True)
    TimeStamp = Column(DateTime, nullable=False)
    RecordCount = Column(Integer, nullable=False)
    FileName = Column(String(255))
    UserName = Column(String(255))
    requests = relationship("WebAppRequest", back_populates="master")


class WebAppRequest(Base):
    __tablename__ = 'TblWebAppRequest'
    MasterUniqueId = Column(Integer, ForeignKey('TblWebAppRequestMaster.UniqueId'), primary_key=True)
    DataDate = Column(DateTime, primary_key=True)
    DataValue = Column(Float, nullable=False)
    master = relationship("WebAppRequestMaster", back_populates="requests")


class Coefficients(Base):
    __tablename__ = 'TblCoefficients'
    ProcessDate = Column(DateTime, primary_key=True, nullable=False)
    b1 = Column(Float, nullable=False)
    b0 = Column(Float, nullable=False)


class RegressionState(Base):
    __tablename__ = 'TblRegressionState'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    S_x = Column(Float, nullable=False)
    S_y = Column(Float, nullable=False)
    S_xx = Column(Float, nullable=False)
    S_xy = Column(Float, nullable=False)
    Count = Column(BigInteger, nullable=False)

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



Base.metadata.create_all(engine)


@app.route('/submit_single_data', methods=['POST'])
def submit_single_data():
    data = request.json
    date = pd.to_datetime(data['date']).date()
    value = float(data['value'])
    user_name = data['username']
    session = Session()

    # Create or get the model state
    model = IncrementalLinearRegression(session)
    # Normalize date if necessary and update model
    min_date = session.query(func.min(WebAppRequest.DataDate)).scalar() or date
    norm_date = (date - min_date).days
    model.update(norm_date, value)

    # Store data and model coefficients
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


@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    file = request.files['file']
    df = pd.read_csv(file)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
    session = Session()
    model = IncrementalLinearRegression(session)

    # Normalize and update model for each data point
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


@app.route('/get_data_plot')
def get_data_plot():
    session = Session()
    model = IncrementalLinearRegression(session)

    # Fetch and plot data
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

    plt.figure()
    plt.plot(x, values, marker='o', linestyle='-', color='blue')
    plt.title('Data Plot Over Time')
    plt.xlabel('Days from start')
    plt.ylabel('Data Value')
    plt.grid(True)

    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    data = base64.b64encode(buf.getbuffer()).decode("ascii")

    session.close()
    return jsonify({'image': data, 'mse': mse})


if __name__ == '__main__':
    app.run(debug=True)
