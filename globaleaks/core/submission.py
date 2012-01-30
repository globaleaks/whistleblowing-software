import tornado.database



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

    reuturn Submission(sid)


_dbpath = 'submissions.db'
