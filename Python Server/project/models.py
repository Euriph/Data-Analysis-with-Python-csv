from sqlalchemy import create_engine, Column, Integer, Float, DateTime, String, ForeignKey, func, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.mysql import JSON
from config import DATABASE_URI

engine = create_engine(DATABASE_URI)
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

class MultiLinearRegressionState(Base):
    __tablename__ = 'TblMultiLinearRegressionState'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    FeatureSums = Column(JSON, nullable=False)
    TargetSums = Column(Float, nullable=False)
    FeatureTargetSums = Column(JSON, nullable=False)
    Count = Column(BigInteger, nullable=False)

class LogisticRegressionState(Base):
    __tablename__ = 'TblLogisticRegressionState'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    FeatureSums = Column(JSON, nullable=False)
    TargetCounts = Column(JSON, nullable=False)
    FeatureTargetSums = Column(JSON, nullable=False)
    Count = Column(BigInteger, nullable=False)
