import tornado.database

"""
This module handles general customizable informations about the GL node.
XXX: should use a .cfg file or not?
"""
__all__ = ['Config']



class Config(object):
    db = database.Connection('localhost', 'gl.db')




