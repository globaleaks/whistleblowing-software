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

    def default(*arg, **kw):

    action  = name of the action looked by
    method  = name of the HTTP method used
    uriargs = the regexp matched in the URL, defined in spec.api
    body    = the raw body
"""
class SubmissionValidator(object):
    @staticmethod
    def default(body, *uriargs):
        pass


class TipValidator(object):

    """
    used by root, pertinence, download
    """
    @staticmethod
    def default(body, *uriargs):
        pass


class ReceiverValidator(object):
    @staticmethod
    def default(body, *uriargs):
        pass

class AdminValidator(object):
    @staticmethod
    def default(body, *uriargs):
        pass

class ReceiverValidator(object):

    """
    This is used in R1 (GET only)
    """
    @staticmethod
    def default(body, *uriargs):
        pass


class NodeValidator(object):

    """
    The simplest GET don't need to be validated
    """
    @staticmethod
    def default(body, *uriargs):
        pass
