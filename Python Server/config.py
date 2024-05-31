from flask import Flask
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)
CORS(app)
engine = create_engine('mysql+pymysql://root:123578951@localhost/dataanalysisproject')
Session = sessionmaker(bind=engine)
Base = declarative_base()

def create_app():
    app = Flask(__name__)
    CORS(app)
    return app
