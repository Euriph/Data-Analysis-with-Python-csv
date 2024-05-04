from flask_restx import Resource, fields
from werkzeug.datastructures import FileStorage
from models import Session, TblWebAppRequestMaster, TblWebAppRequest, TblCoefficients
from app import api
import pandas as pd
from datetime import datetime
from IncrementalLinearRegression import IncrementalLinearRegression

upload_parser = api.parser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True)

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
