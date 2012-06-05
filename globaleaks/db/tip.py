import sha
import random
from sqlalchemy import Table, Column, Integer
from sqlalchemy import ForeignKey, String, PickleType, Date
from sqlalchemy.orm import relationship, backref, subqueryload, joinedload
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker

# Base = declarative_base()
(Base, engine) = DBIO()

class InternalTip(Base):
    """
    This is the internal representation of a Tip that has been submitted to the
    GlobaLeaks node.
    It has a one-to-many association with the individual Tips of every receiver
    and whistleblower.
    """
    __tablename__ = 'internaltip'

    id = Column(Integer, primary_key=True)
    children = relationship("Tip", backref='internaltip')

    fields = Column(PickleType)
    material = relationship("MaterialSet")
    comments = Column(PickleType)
    pertinence = Column(Integer)
    expiration_time = Column(Date)

    def __init__(self, fields, comments, pertinence, expiration_time):
        print "initing."
        self.fields = fields
        self.comments = comments
        self.pertinence = pertinence
        self.expiration_time = expiration_time

    def __repr__(self):
        return "<InternalTip: (%s, %s, %s, %s, %s)" % (self.fields, \
                self.material, self.comments, self.pertinence, \
                self.expiration_time)

class MaterialSet(Base):
    """
    This represents a material set: a collection of files.
    """
    __tablename__ = 'materialset'
    id = Column(Integer, primary_key=True)
    tip_id = Column(Integer, ForeignKey('internaltip.id'))
    material = relationship("Material", backref='materialset')

    description = Column(String)
    def __init__(self, description):
        self.description = description

class Material(Base):
    """
    Represents a material: a file.
    """
    __tablename__ = 'material'
    id = Column(Integer, primary_key=True)
    material_set_id = Column(Integer, ForeignKey('materialset.id'))

    file_location = Column(String)
    description = Column(String)

    def __init__(self, file_location, description):
        self.file_location = file_location
        self.description = description

class Tip(Base):
    __tablename__ = 'tip'
    id = Column(Integer, primary_key=True)
    internal_id = Column(Integer, ForeignKey('internaltip.id'))
    address = Column(String)
    password = Column(String)

    def __init__(self, internal_id):
        self.internal_id = internal_id
        self.gen_address()

class ReceiverTip(Tip):
    total_view_count = Column(Integer, default=0)
    total_download_count = Column(Integer, default=0)
    relative_view_count = Column(Integer, default=0)
    relative_download_count = Column(Integer, default=0)

    __mapper_args__ = {'polymorphic_identity':'tip'}

    def increment_visit(self):
        pass

    def increment_download(self):
        pass

    def delete_tulip(self):
        pass

    def download_material(self, id):
        pass

class WhistleblowerTip(Tip):
    def add_material(self):
        pass

"""
Execution flow test
"""
# engine = create_engine('sqlite:///test.db', echo=True)

Session = sessionmaker(bind=engine)
session = Session()

import datetime
Base.metadata.create_all(engine)
#material = Material()
internal_tip = InternalTip({'a':'b','c':'d'}, {'a':1}, 42, datetime.datetime.now())

session.add(internal_tip)
session.commit()

for x in range(1,10):
    recv_tip = ReceiverTip(internal_tip.id)
    session.add(recv_tip)
    internal_tip.children.append(recv_tip)
    session.commit()

tip_addr = recv_tip.address

res = session.query(Tip).filter_by(address=tip_addr).one()
#res = session.query(InternalTip).filter_by(InternalTip.children.address=tip_addr).one()

#res = session.query(InternalTip).options(joinedload('children')).filter_by(address=tip_addr).one()
internal_tip = session.query(InternalTip).filter_by(id=res.internal_id).one()

print internal_tip
