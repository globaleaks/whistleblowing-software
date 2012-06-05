from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

def simple_fs_db_init():
    print "porra"
    return ( declarative_base(), create_engine('sqlite:///test.db', echo=True) )
