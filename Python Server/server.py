from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, String, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import pandas as pd
from datetime import datetime
from IncrementalLinearRegression import IncrementalLinearRegression

app = Flask(__name__)
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


Base.metadata.create_all(engine)

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    file = request.files['file']
    df = pd.read_csv(file)
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%y')

    session = Session()

    # Check if there are records in the database to determine the earliest date for normalization
    database_min_date = session.query(func.min(WebAppRequest.DataDate)).scalar()
    csv_min_date = df['Date'].min().date()  # Convert pandas Timestamp to datetime.date directly

    if database_min_date:
        min_date = min(database_min_date, csv_min_date)
    else:
        min_date = csv_min_date

    master_entry = WebAppRequestMaster(
        TimeStamp=datetime.now(),
        RecordCount=len(df),
        FileName=file.filename,
        UserName="API User"
    )
    session.add(master_entry)
    session.flush()

    for index, row in df.iterrows():
        # Ensure row['Date'] is converted to datetime.date for the calculation
        normalized_date = (row['Date'].date() - min_date).days  # Convert to date and calculate days
        dp = WebAppRequest(MasterUniqueId=master_entry.UniqueId, DataDate=row['Date'], DataValue=row['Value'])
        session.add(dp)

    session.commit()

    # Initialize and update model with normalized dates
    model = IncrementalLinearRegression()
    all_data = session.query(WebAppRequest).all()
    for dp in all_data:
        norm_date = (dp.DataDate - min_date).days
        model.update(norm_date, dp.DataValue)

    coeffs = model.coefficients()
    process_date = datetime.now()
    coeffs_entry = Coefficients(ProcessDate=process_date, b0=coeffs[0], b1=coeffs[1])
    session.add(coeffs_entry)
    session.commit()

    session.close()
    return jsonify({"message": "CSV uploaded and model recalculated", "coefficients": coeffs}), 200




if __name__ == '__main__':
    app.run(debug=True)
