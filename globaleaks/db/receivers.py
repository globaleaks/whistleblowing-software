from sqlalchemy import Table, Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Receiver(Base):
    __tablename__ = 'receiver'
    id = Column(Integer, primary_key=True)

    public_name = Column(String)
    private_name = Column(String)
    description = Column(String)


