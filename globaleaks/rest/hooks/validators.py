"""
Validator perform integrity checks in the submitted field,
and perform every sanity checks in the submitted type
it may perform loggin for specific operation if enabled.

Validator perform integrity check only, not logical checks
that need knowledge of data meaning.

What's validator DO NOT:

. only a receiver can express pertinencies in a Tip,
  if a whistleblower Tip is used to express a pertinency this error
  would be detected and managed by the Tip object.

. not all contexts supports the option for delete a Tip as
  receiver option. This check would be performed by the Tip
  object, also if is a context dependent settings.

Validatator DO:

. Verify that all the fields and the matched arguments
  are coherent with the API-specification
. Perform eventually logging in a specific operations
. Act as blacklisting module if some keywork/behaviour
  would be blocked, or managed in a particular way.

Validator is the first layer of checks after the HTTP
request, after the validator procedure not all the 
request may be passed.
"""

"""
    dynamic argument schema:

    def default_validate(*arg, **kw):

    action  = name of the action looked by
    method  = name of the HTTP method used
    uriargs = the regexp matched in the URL, defined in spec.api
    body    = the raw body
"""

class SubmissionValidator(object):

    @classmethod
    def default_validate(*args, **kw):
        return True

    @classmethod
    def files(*args, **kw):
        return True

class TipValidator(object):

    """
    used by root, finalize, pertinence, download
    """
    @classmethod
    def default_validate(*args, **kw):
        return True

    @classmethod
    def files(*args, **kw):
        return True

    @classmethod
    def comment(*args, **kw):
        return True


class ReceiverValidator(object):

    @classmethod
    def validate(*args, **kw):
        return True

    @classmethod
    def modules(*args, **kw):
        return True


class AdminValidator(object):

    @classmethod
    def node(*args, **kw):
        return True

    @classmethod
    def contexts(*args, **kw):
        return True

    @classmethod
    def receivers(*args, **kw):
        return True

    @classmethod
    def modules(*args, **kw):
        """
        whistlist:
        xx = GLDO.moduleDataDict()
        for k,v kw['body']:
            xx.isValid(k, v)
        """
        return True

class ReceiverValidator(object):

    """
    This is used in R1 (GET only)
    """
    @classmethod
    def default_validate(*args, **kw):
        return True

    """
    This is used in R2 CURD
    """
    @classmethod
    def module_GET(*args, **kw):
        return True

    """
    This is used in R2 POST|PUT|DELETE
    """
    @classmethod
    def module(*args, **kw):
        print "checking ",kw['body'], "expecting a moduleDataDict and a 'method'"

        """
        if invalidPOSThack(kw['method'], kw['body']):
            return False
        """

        return True
    


class NodeValidator(object):

    """
    The simplest GET don't need to be validated
    """
    @classmethod
    def default_validate(*args, **kw):
        return True


