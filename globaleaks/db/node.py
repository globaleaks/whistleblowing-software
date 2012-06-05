from sqlalchemy import Table, Column, Integer
from sqlalchemy import ForeignKey, String, PickleType, Date
from sqlalchemy.orm import relationship, backref, subqueryload, joinedload
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Node(Base):
    __tablename__ = 'node'
    id = Column(Integer, primary_key=True)

    context = Column(PickleType)
    statistics = Column(PickleType)
    properties = Column(PickleType)
    description = Column(String)
    name = Column(String)
    public_site = Column(String)
    hidden_service = Column(String)

