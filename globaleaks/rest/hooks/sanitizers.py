# Sanitizer goals: every field need to be checked, escaped
# if something is wrong in format, raise an exception

# Sanitizer classes facts:

# . The variables returned from all the following functions,
#   is a dict, because in the next step would be passed as (*arg, **kw)
# . sanitizer is called after the validation, therefore we're
#   guarantee that the fields here analyzed are coherent with the
#  specified API
# . Text would be converted in unicode in this functions
# . Exist some helper function performing the checks, they are
#   private modules implemented in globaleaks.utils.sanitychecks
# . Modules, having a dedicated set of fields, implement their
#   own sanitizer method, globaleaks.utils.modules support in that


"""
    dynamic argument schema:

    def default(body, *uriargs):

    body  = the body of the request
    uriargs = the regexp matched in the URL, defined in spec.api
"""

class SubmissionSanitizer(object):

    """
    finalize and root actions covered here,
    boolean or int only
    """
    @staticmethod
    def default(body, *uriarg):
        return body

    @staticmethod
    def files(body, *arg, **kw):
        return body

    """
    status contain the fields and the group selection
    """
    @staticmethod
    def status(body, *arg, **kw):
        print "Going at it!"
        print arg,kw
        print body
        return body


class TipSanitizer(object):

    """
    root, pertinence and finalize are covered here,
    because their fields are boolean or int
    """
    @staticmethod
    def default(body, *uriarg):
        return body

    @staticmethod
    def files(body, *arg, **kw):
        return body

    @staticmethod
    def comment(body, *arg, **kw):
        """
        whistlist:
        retDict = genericObj()
        retDict.comment = textSanitize(kw['body']['comment'])
        """
        return body

class ReceiverSanitizer(object):

    """
    all the receiver actions are handler here, but
    maybe the CURD need to be splitted properly
    (and the, sanizer handled with a _HTTPMETHOD selection)
    """
    @staticmethod
    def default(body, *uriarg):
        return body

"""
AdminSanitezer has not defaultd, because all
the four action in admin API had a large set of elements
that need to be checked carefully
"""
class AdminSanitizer(object):

    @staticmethod
    def contexts(body, *arg, **kw):
        return body

    @staticmethod
    def receivers(body, *arg, **kw):
        return body

    @staticmethod
    def modules(body, *arg, **kw):
        return body

    @staticmethod
    def node(body, *arg, **kw):
        return body
