from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, String, ForeignKey
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


@app.route('/update_data', methods=['POST'])
def update_data():
    data = request.json
    date = pd.to_datetime(data['date'])
    value = float(data['value'])
    session = Session()
    master_entry = WebAppRequestMaster(TimeStamp=datetime.now(), RecordCount=1, FileName=None, UserName="API User")
    session.add(master_entry)
    session.flush()  # Ensures 'UniqueId' is available
    dp = WebAppRequest(MasterUniqueId=master_entry.UniqueId, DataDate=date, DataValue=value)
    session.add(dp)
    session.commit()

    model = IncrementalLinearRegression()
    all_data = session.query(WebAppRequest).all()
    for dp in all_data:
        model.update(dp.DataDate.toordinal(), dp.DataValue)

    coeffs = model.coefficients()
    process_date = datetime.now()
    coeffs_entry = Coefficients(ProcessDate=process_date, b0=coeffs[0], b1=coeffs[1])
    session.add(coeffs_entry)
    session.commit()
    session.close()
    return jsonify({"message": "Data updated, model recalculated", "coefficients": coeffs}), 200


@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    file = request.files['file']
    df = pd.read_csv(file)
    session = Session()

    # Create a master record for this batch of data
    master_entry = WebAppRequestMaster(
        TimeStamp=datetime.now(),
        RecordCount=len(df),
        FileName=file.filename,
        UserName="API User"  # This should be dynamically determined based on your app's context
    )
    session.add(master_entry)
    session.flush()  # Ensures 'UniqueId' is available before linking data points

    # Process each row in the CSV file
    for index, row in df.iterrows():
        date = pd.to_datetime(row['Date'])
        value = float(row['Value'])
        dp = WebAppRequest(MasterUniqueId=master_entry.UniqueId, DataDate=date, DataValue=value)
        session.add(dp)

    session.commit()

    # Update model with new data and recalculate coefficients
    model = IncrementalLinearRegression()
    all_data = session.query(WebAppRequest).all()
    for dp in all_data:
        model.update(dp.DataDate.toordinal(), dp.DataValue)

    coeffs = model.coefficients()
    process_date = datetime.now()
    # Delete old coefficients and save new ones
    session.query(Coefficients).delete()
    coeffs_entry = Coefficients(ProcessDate=process_date, b0=coeffs[0], b1=coeffs[1])
    session.add(coeffs_entry)
    session.commit()

    session.close()
    return jsonify({"message": "CSV uploaded and model recalculated", "coefficients": coeffs}), 200


if __name__ == '__main__':
    app.run(debug=True)
