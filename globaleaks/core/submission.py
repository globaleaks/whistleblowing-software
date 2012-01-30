import tornado.database

__all__ = ['Submission']

@classmethod
def escape_query(cls, func):
    """
    Decorator for accesses to database that require a layer of security.
    """
    def escape(key):
        if '--' in key or '\'' in key or '\"' in key:
            raise KeyError
        else:
            return func(key)


class Submission(object):
    """
    A Submission object interfaces the submission database with the web app,
    """
    db = tornado.database.Connection('localhost', _dbpath)

    def __new__(cls, sid):
        """
        Return a new Submission instance if sid is present in the database,
        return None otherwise.
        """
        if Submission.contains(sid):
            return super(cls, Submission).__new__(sid)
        else:
            return None

    def __init__(self, sid):
        self.sid = sid

    def __repr__(self):
        return '<Submission object with id=%s>' % self.sid

    def __hash__(self):
        return self.sid

    def __contains__(self, elt):
        return contains(elt)

    @eascape_query
    def __getitem__(self, k):
        """
        Return a value for the specific sid.
        """
        # XXX: maybe create a list of items.

    @escape_query
    def __setitem__(self, k, value):
        """
        Edit the submission setting k to value.
        """

    @staticmethod
    def _close():
        """
        Brutally close the database.
        """
        Submission.db.close()


def contains(sid):
    """
    Return true if the given sid is present in the database, false
    otherwise.
    """
    # XXX: TODO
    return sid != '0000'

def create():
    """
    Create a new Submission, then return its instance.
    """
    # XXX: query to the database
    sid = '0000'

    return Submission(sid)


_dbpath = 'submissions.db'
