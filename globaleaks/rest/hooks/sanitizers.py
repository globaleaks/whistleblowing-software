"""
Sanitizer goals: every field need to be checked, escaped
if something is wrong in format, raise an exception

Sanitizer classes facts:

. The variables returned from all the following functions, 
  is a dict, because in the next step would be passed as (*arg, **kw)
. sanitizer is called after the validation, therefore we're
  guarantee that the fields here analyzed are coherent with the
  specified API
. Text would be converted in unicode in this functions
. Exist some helper function performing the checks, they are
  private modules implemented in globaleaks.utils.sanitychecks
. Modules, having a dedicated set of fields, implement their
  own sanitizer method, globaleaks.utils.modules support in that
"""

class SubmissionSanitizer(object):

    """
    finalize and root actions covered here,
    boolean or int only
    """
    @classmethod
    def default_sanitize(*arg, **kw):
        return (arg, kw)

    @classmethod
    def files(*arg, **kw):
        return (arg, kw)

    """
    status contain the fields and the group selection
    """
    @classmethod
    def status(*arg, **kw):
        return (arg, kw)



class TipSanitizer(object):

    """
    root, pertinence and finalize are covered here,
    because their fields are boolean or int
    """
    @classmethod
    def default_sanitize(*arg, **kw):
        return (arg, kw)

    @classmethod
    def files(*arg, **kw):
        return (arg, kw)

    @classmethod
    def comment(*arg, **kw):
        return (arg, kw)


class ReceiverSanitizer(object):

    """
    all the receiver actions are handler here, but
    maybe the CURD need to be splitted properly
    (and the, sanizer handled with a _HTTPMETHOD selection)
    """
    @classmethod
    def default_sanitize(*arg, **kw):
        return (arg, kw)


"""
AdminSanitezer has not default_sanitized, because all
the four action in admin API had a large set of elements
that need to be checked carefully
"""
class AdminSanitizer(object):

    @classmethod
    def contexts(*arg, **kw):
        return (arg, kw)

    @classmethod
    def receivers(*arg, **kw):
        return (arg, kw)

    @classmethod
    def modules(*arg, **kw):
        return (arg, kw)

    @classmethod
    def node(*arg, **kw):
        return (arg, kw)

