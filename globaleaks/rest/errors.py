# -*- coding: UTF-8
#
#   errors
#   ******
#
# Here shall go all the error messages that a GLBackend can generate.
# GLException is the class inherit by the other Errors, and define the
# class variables expected in the Error handler routine


class GLException(Exception):

    error_message = "GLTypesError not set"
    error_code = 0
    http_status = 500 # generic Server error


class InvalidInputFormat(GLException):
    """
    The expected format described in the REST specification is not
    respected by the data body in the HTTP request.
    """

    def __init__(self):
        GLException.error_message = "invalid input format"
        GLException.error_code = 10
        GLException.http_status = 406 # Not Acceptable

class StatsNotCollectedError(GLException):
    """
    Statistics can be disabled by administrator, both for
    public and admin statistics.
    """

    def __init__(self):
        GLException.error_message = "statistics disabled"
        GLException.error_code = 11
        GLException.http_status = 500 # Internal Server Error


class ContextGusNotFound(GLException):
    """
    The context_gus used do not exist in the database.
    """

    def __init__(self):
        GLException.error_message = "Not found a Context with the specified GUS identifier"
        GLException.error_code = 12
        GLException.http_status = 404 # Not Found

class TipGusNotFound(GLException):
    """
    The Tip GUS requested do not exists in the database.
    """

    def __init__(self):
        GLException.error_message = "Not found a Tip with the specified GUS identifier"
        GLException.error_code = 13
        GLException.http_status = 404 # Not Found

class TipReceiptNotFound(GLException):
    """
    The WhisleBlower receipt is not related to any of the whistleblower tips
    """

    def __init__(self):
        GLException.error_message = "Not found a Receiver with the specified GUS identifier"
        GLException.error_code = 14
        GLException.http_status = 404 # Not Found

class TipPertinenceExpressed(GLException):
    """
    Pertinence in the Tip has been already expressed by the receiver, and only one
    vote per receiver is possible
    """

    def __init__(self):
        GLException.error_message = "Pertinence evaluation has been already expressed"
        GLException.error_code = 15
        GLException.http_status = 409 # Conflict

class NodeNotFound(GLException):
    """
    This may happen only if, via database, the node entry is removed,
    because it's created by default and do not exists a function able to
    remove the Node at all.
    """

    def __init__(self):
        GLException.error_message = "Node not found"
        GLException.error_code = 16
        GLException.http_code = 506 # Variant also negotiated

class ProfileGusNotFound(GLException):
    """
    The Profile GUS requested do not exists in the database.
    """

    def __init__(self):
        GLException.error_message = "Not found a Plugin Profile with the specified GUS identifier"
        GLException.error_code = 17
        GLException.http_status = 404 # Not Found

class ProfileNameConflict(GLException):
    """
    The name of a plugin profile need to be unique, if is proposed an already existen name
    is returned a Conflict error.
    """

    def __init__(self):
        GLException.error_message = "The proposed name is already in use by another Plugin Profile"
        GLException.error_code = 18
        GLException.http_status = 409 # Conflict

class ReceiverConfNotFound(GLException):
    """
    The receiver configuration ID do not exist in the database associated to the Receiver
    """

    def __init__(self):
        GLException.error_message = "Not found a ReceiverConf with the specified ID"
        GLException.error_code = 19
        GLException.http_status = 404 # Not Found


class ReceiverGusNotFound(GLException):
    """
    The Receiver GUS requested do not exists in the database.
    """

    def __init__(self):
        GLException.error_message = "Not found a Receiver with the specified GUS identifier"
        GLException.error_code = 20
        GLException.http_status = 404 # Not Found

class SubmissionGusNotFound(GLException):
    """
    The Submission GUS requested do not exists in the database.
    """

    def __init__(self):
        GLException.error_message = "Not found a Submission with the specified GUS identifier"
        GLException.error_code = 21
        GLException.http_status = 404 # Not Found

class SubmissionFailFields(GLException):
    """
    If the fields required values and format type do not fit the requirement, this
    error is raised. The Client has to enforce as possible the Input Format, when this
    Client output validation fail, this error may happen.
    """

    def __init__(self):
        GLException.error_message = "Submission do not validate the input fields"
        GLException.error_code = 22
        GLException.http_status = 412 # Precondition Failed


class InvalidTipAuthToken(GLException):
    """
    Authentication is failed, for Receiver or Whistleblower, because do not rely
    only in the secret Token (Tip Gus knowledge or receipt).
    """

    def __init__(self):
        GLException.error_message = "Authentication in Tip failed"
        GLException.error_code = 23
        GLException.http_status = 401 # Unauthorized


class PluginNameNotFound(GLException):
    """
    Authentication is failed, for Receiver or Whistleblower, because do not rely
    only in the secret Token (Tip Gus knowledge or receipt).
    """

    def __init__(self):
        GLException.error_message = "Authentication in Tip failed"
        GLException.error_code = 23
        GLException.http_status = 401 # Unauthorized

class ForbiddenOperation(GLException):
    """
    Receiver or Whistleblower has tried one operation not permitted by their privileges
    """

    def __init__(self):
        GLException.error_code = "Operation Forbidden"
        GLException.error_code = 24
        GLException.http_status = 401 # Unauthorized


