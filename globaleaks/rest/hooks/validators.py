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

validator perform syntax checking, not logical.

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
from globaleaks.rest import requests

def mydirtydebug(body, uriargs, args, kw):
    print "body", type(body), body
    print "uriargs", type(uriargs), uriargs
    print "args", type(args), args
    print "kw", type(kw), kw

class SubmissionValidator(object):

    @classmethod
    def default_validate(self, action, body, uriargs, *args, **kw):
        print self.__class__.__name__,"default_validate", action, uriargs, body
        return True

    @classmethod
    def files(self, uriargs, body, *args, **kw):
        """
        That's depend from JQFU patches
        """
        return True

    @classmethod
    def status_POST(self, uriargs, body, *args, **kw):
        """
        U3, has uriargs and body
        """
        mydirtydebug(body, uriargs, args, kw)
        expected = requests.submissionUpdate()
        expected.aquire(body)
        return True
   
    @classmethod
    def finalize_POST(self, uriargs, body, *args, **kw):
        """
        finalize the folder, receive comments, stabilize fields/receivers
        """
        mydirtydebug(body, uriargs, args, kw)
        expected = requests.finalizeSubmission()
        expected.aquire(body)
        return True




class TipValidator(object):

    """
    used by root, pertinence, download
    """
    @classmethod
    def default_validate(self, action, body, uriargs, *args, **kw):
        print self.__class__.__name__,"default_validate", action, uriargs, body
        return True

    @classmethod
    def files(self, uriargs, body, *args, **kw):
        return True

    @classmethod
    def finalize_POST(self, body, uriargs, *args, **kw):
        """
        finalize the update of a new folder
        """
        mydirtydebug(body, uriargs, args, kw)

        expected = requests.finalizeIntegration()
        expected.aquire(body)

        return True

    @classmethod
    def comment_POST(self, body, uriargs, *args, **kw):
        """
        Validation of comment
        """
        mydirtydebug(body, uriargs, args, kw)

        expected = requests.sendComment()
        expected.aquire(body)

        return True


class ReceiverValidator(object):

    @classmethod
    def default_validate(self, action, body, uriargs, *args, **kw):
        print self.__class__.__name__,"default_validate", action, uriargs, body
        return True

    """
    Cover module operations, CURD, R2, 
    but we have not to cover the GET request...
    maybe nice make a decorator able to define which kind of 
    method need to be wrapped, and reduce, in handlers, the looping test,
    using just the default_valudate as fallback -- XXX
    """
    @classmethod
    def module(self, uriargs, body, *args, **kw):
        mydirtydebug(body, uriargs, args, kw)
        expected = requests.receiverOptions()
        expected.aquire(body)
        return True


class AdminValidator(object):

    @classmethod
    def node(self, uriargs, body, *args, **kw):
        return True

    @classmethod
    def contexts(self, uriargs, body, *args, **kw):
        return True

    @classmethod
    def receivers(self, uriargs, body, *args, **kw):
        return True

    @classmethod
    def modules(self, uriargs, body, *args, **kw):
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
    def default_validate(self, action, body, uriargs, *args, **kw):
        print self.__class__.__name__,"default_validate", action, uriargs, body
        return True

    """
    This is used in R2 CURD
    """
    @classmethod
    def module_GET(self, uriargs, body, *args, **kw):
        return True

    """
    This is used in R2 POST|PUT|DELETE
    """
    @classmethod
    def module(self, uriargs, body, *args, **kw):
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
    def default_validate(self, action, body, uriargs, *args, **kw):
        print self.__class__.__name__,"default_validate", action, uriargs, body
        return True


