from flask import Flask, request
from flask_restx import Api, Resource, fields
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from werkzeug.datastructures import FileStorage
import pandas as pd
from datetime import datetime

app = Flask(__name__)
api = Api(app, version='1.0', title='Data Analysis API', description='A simple API for data analysis with incremental linear regression')

# Database setup
DATABASE_URI = 'mysql+pymysql://root:123578951@localhost/dataanalysisproject'
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class DataPoint(Base):
    __tablename__ = 'datapoints'
    id = Column(Integer, primary_key=True)
    date = Column(String(10))
    value = Column(Float)

class TblCoefficients(Base):
    __tablename__ = 'TblCoefficients'
    id = Column(Integer, primary_key=True, autoincrement=True)
    b1 = Column(Float, nullable=False)
    b0 = Column(Float, nullable=False)
    ProcessDate = Column(DateTime, default=datetime.now)

class TblWebAppRequest(Base):
    __tablename__ = 'TblWebAppRequest'
    MasterUniqueId = Column(Integer, ForeignKey('TblWebAppRequestMaster.UniqueId'), primary_key=True)
    DataDate = Column(DateTime)
    DataValue = Column(Float)

class TblWebAppRequestMaster(Base):
    __tablename__ = 'TblWebAppRequestMaster'
    UniqueId = Column(Integer, primary_key=True, autoincrement=True)
    TimeStamp = Column(DateTime, default=datetime.now)
    RecordCount = Column(Integer)
    FileName = Column(String(255))

Base.metadata.create_all(engine)

upload_parser = api.parser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True)

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

@api.route('/upload_csv')
class UploadFile(Resource):
    @api.expect(upload_parser)
    def put(self):
        args = upload_parser.parse_args()
        csv_file = args['file']
        df = pd.read_csv(csv_file)  # Assuming the CSV is read correctly into the dataframe

        session = Session()

        # Create a record for the file in TblWebAppRequestMaster
        master_record = TblWebAppRequestMaster(
            TimeStamp=datetime.now(),
            RecordCount=len(df),
            FileName=csv_file.filename
        )
        session.add(master_record)
        session.flush()

        # Store CSV data in TblWebAppRequest, use correct column names
        for index, row in df.iterrows():
            new_request = TblWebAppRequest(
                MasterUniqueId=master_record.UniqueId,
                DataDate=pd.to_datetime(row['Date'], format='%d-%m-%y'),  # Correct date format and column name
                DataValue=row['Value']  # Correct value column name
            )
            session.add(new_request)

        # Compute coefficients
        regression_model = IncrementalLinearRegression()
        for _, row in df.iterrows():
            ordinal_date = pd.to_datetime(row['Date'], format='%d-%m-%y').toordinal()  # Correct date format and column name
            regression_model.update(ordinal_date, row['Value'])  # Correct value column name

        b0, b1 = regression_model.coefficients()

        # Save coefficients in TblCoefficients
        coefficients_record = TblCoefficients(b1=b1, b0=b0)
        session.add(coefficients_record)

        session.commit()
        session.close()
        return {'result': 'File uploaded, data stored, and coefficients calculated'}, 201

if __name__ == '__main__':
    app.run(debug=True)

