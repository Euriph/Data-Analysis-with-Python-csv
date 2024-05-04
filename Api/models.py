from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import scoped_session, sessionmaker
from app import app
from datetime import datetime

Base = declarative_base()
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
# Create a scoped session to manage SQLAlchemy sessions properly across different threads
Session = scoped_session(sessionmaker(bind=engine))

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
    FileName = Column(String(255), nullable=True)
    UserName = Column(String(255), nullable=True)


Base.metadata.create_all(engine)
