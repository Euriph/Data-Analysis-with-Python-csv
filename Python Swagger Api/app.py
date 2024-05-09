from flask import Flask
from flask_restx import Api
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
api = Api(app, version='1.0', title='Data Analysis API', description='A simple API for data analysis with incremental linear regression')
