from flask_restx import Resource, fields
from werkzeug.datastructures import FileStorage
from models import Session, TblWebAppRequestMaster, TblWebAppRequest, TblCoefficients
from app import api
import pandas as pd
from datetime import datetime
from IncrementalLinearRegression import IncrementalLinearRegression

# Parser for file upload
upload_parser = api.parser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True)

# Parser for single entry submission
single_entry_parser = api.parser()
single_entry_parser.add_argument('date', type=str, required=True, help='Date in YYYY-MM-DD format')
single_entry_parser.add_argument('value', type=float, required=True, help='Value as a float')
single_entry_parser.add_argument('user_name', type=str, required=True, help='User name')

@api.route('/upload_csv')
class UploadFile(Resource):
    @api.expect(upload_parser)
    def put(self):
        args = upload_parser.parse_args()
        csv_file = args['file']
        df = pd.read_csv(csv_file)  # Assuming the CSV is read correctly into the dataframe

        session = Session()

        try:
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
            return {'result': 'File uploaded, data stored, and coefficients calculated'}, 201
        except Exception as e:
            session.rollback()
            return {'error': str(e)}, 500
        finally:
            Session.remove()  # Properly remove the session

@api.route('/single_entry')
class SingleEntry(Resource):
    @api.expect(single_entry_parser)
    def post(self):
        args = single_entry_parser.parse_args()
        session = Session()

        try:
            # Create a master record for the entry
            master_record = TblWebAppRequestMaster(
                TimeStamp=datetime.now(),
                RecordCount=1,
                UserName=args['user_name']
            )
            session.add(master_record)
            session.flush()

            # Convert date string to datetime object
            data_date = pd.to_datetime(args['date']).date()

            # Store the single data entry
            new_request = TblWebAppRequest(
                MasterUniqueId=master_record.UniqueId,
                DataDate=data_date,
                DataValue=args['value']
            )
            session.add(new_request)

            # Compute and store coefficients
            regression_model = IncrementalLinearRegression()
            ordinal_date = data_date.toordinal()
            regression_model.update(ordinal_date, args['value'])
            b0, b1 = regression_model.coefficients()

            coefficients_record = TblCoefficients(b1=b1, b0=b0)
            session.add(coefficients_record)

            session.commit()
            return {'result': 'Entry added, master record created, and coefficients calculated'}, 201
        except Exception as e:
            session.rollback()
            return {'error': str(e)}, 500
        finally:
            Session.remove()  # Correctly remove the session
