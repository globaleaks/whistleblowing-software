# the follow file just for remind the programmers requirement
# ORMface need to became the interface usable from GL objects and SQLAlchemy ORM
# ORMface need supports storage module extensions
# ORMface need to create new table and resume previously saved
# ORMface MAY supports caching in I/O
# ORMface do not perform transparent commit, the object has the only update data in memory
# ORMface can implement different protection model by usage requirement (data, config, setting)

from sqlalchemy import Table, Column, Integer
from sqlalchemy import ForeignKey, String, PickleType, Date
from sqlalchemy.orm import relationship, backref, subqueryload, joinedload
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

"""
Main ORM interface, used by the Class files inside db/*.py
This interface provide useful feature to interact with the database
"""

class DBIO():

    def __init__(self):
        _Base = declarative_base()
        _session = Session(autocommit=True)
        _engine = engine = create_engine('sqlite:///test.db', echo=True)
        _Base.metadata.create_all(_engine)

        return (_Base, _session, _engine)

    def resume(self, ObjType, fieldname, fieldvalue)
        """
        resume function, get an object from the saved ORM or
        open a new one as objType requested. field name and value
        are optional, usable to search a specific instance.

        return an istance of objType or None
        """
        pass
