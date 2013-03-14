# -*- coding: UTF-8
#
#   errors
#   ******
#
# Here shall go all the error messages that a GLBackend can generate.
# GLException is the class inherit by the other Errors, and define the
# class variables expected in the Error handler routine

from cyclone.web import HTTPError

class GLException(HTTPError):
    reason = "GLTypesError not set"
    log_message = "GLException"
    error_code = 0
    status_code = 500 # generic Server error
    def __init__(self):
        pass

class InvalidInputFormat(GLException):
    """
    The expected format described in the REST specification is not
    respected by the data body in the HTTP request.
    """
    error_code = 10
    status_code = 406 # Not Acceptable

    def __init__(self, wrong_source):
        self.reason = "Invalid Input Format [%s]" % wrong_source


class StatsNotCollectedError(GLException):
    """
    Statistics can be disabled by administrator, both for
    public and admin statistics.
    """
    reason = "Statistics Disabled"
    error_code = 11
    status_code = 500 # Internal Server Error

class ContextGusNotFound(GLException):
    """
    The context_gus used do not exist in the database.
    """
    reason = "Not found a Context with the specified GUS identifier"
    error_code = 12
    status_code = 404 # Not Found


class TipGusNotFound(GLException):
    """
    The Tip GUS requested do not exists in the database.
    """
    reason = "Not found a Tip with the specified GUS identifier"
    error_code = 13
    status_code = 404 # Not Found

class TipReceiptNotFound(GLException):
    """
    The WhisleBlower receipt is not related to any of the whistleblower tips
    """
    reason = "Not found a Receiver with the specified GUS identifier"
    error_code = 14
    status_code = 404 # Not Found

class TipPertinenceExpressed(GLException):
    """
    Pertinence in the Tip has been already expressed by the receiver, and only one
    vote per receiver is possible
    """
    reason = "Pertinence evaluation has been already expressed"
    error_code = 15
    status_code = 409 # Conflict

class NodeNotFound(GLException):
    """
    This may happen only if, via database, the node entry is removed,
    because it's created by default and do not exists a function able to
    remove the Node at all.
    """
    reason = "Node not found"
    error_code = 16
    http_code = 506 # Variant also negotiated

class ContextParameterConflict(GLException):
    """
    Some parameters explicit in the context creation can't works together
    """
    reason = "Some parameters explicit in the context creation can't works together"
    error_code = 17
    status_code = 409 # Conflict

class AccessLimitExceeded(GLException):
    """
    The access counter for a Tip has reached the limit
    """
    reason = "Your user has reach the maximum amount of access for this Tip"
    error_code = 18
    status_code = 503 # Servie Unavailable

class ReceiverConfNotFound(GLException):
    """
    The receiver configuration ID do not exist in the database associated to the Receiver
    """
    reason = "Not found a ReceiverConf with the specified ID"
    error_code = 19
    status_code = 404 # Not Found


class ReceiverGusNotFound(GLException):
    """
    The Receiver GUS requested do not exists in the database.
    """
    reason = "Not found a Receiver with the specified GUS identifier"
    error_code = 20
    status_code = 404 # Not Found

class SubmissionGusNotFound(GLException):
    """
    The Submission GUS requested do not exists in the database.
    """
    reason = "Not found a Submission with the specified GUS identifier"
    error_code = 21
    status_code = 404 # Not Found

class SubmissionFailFields(GLException):
    """
    If the fields required values and format type do not fit the requirement, this
    error is raised. The Client has to enforce as possible the Input Format, when this
    Client output validation fail, this error may happen.
    """
    error_code = 22
    status_code = 412 # Precondition Failed

    def __init__(self, wrong_fields):
        self.reason = "Submission do not validate the input fields [%s]" % wrong_fields

class InvalidTipAuthToken(GLException):
    """
    Authentication is failed, for Receiver or Whistleblower, because do not rely
    only in the secret Token (Tip Gus knowledge or receipt).
    """
    reason = "Authentication in Tip failed"
    error_code = 23
    status_code = 401 # Unauthorized

class PluginNameNotFound(GLException):
    """
    Plugin Name do not exists between the available plugins
    """
    reason = "Plugin Name not found"
    error_code = 24
    status_code = 404 # Unauthorized

class ForbiddenOperation(GLException):
    """
    Receiver or Whistleblower has tried one operation not permitted by their privileges
    """
    reason = "Operation Forbidden"
    error_code = 25
    status_code = 401 # Unauthorized

class FileGusNotFound(GLException):
    """
    The requested file Gus do not exist in the database
    """
    reason = "Not found a File with the specified GUS identifier"
    error_code = 26
    status_code = 404 # Not Found


class SubmissionConcluded(GLException):
    """
    The submisssion accessed haa been already completed
    """
    reason = "The submission tried to be update has been already finalized"
    error_code = 28
    status_code = 409 # Conflict

class InvalidAuthRequest(GLException):
    """
    An invalid request was presented
    """
    reason = "Authentication Failed"
    error_code = 29
    status_code = 401 # Unauthorized

class NotAuthenticated(GLException):
    """
    The user attempted to access a not-authorized request.
    """
    reason = "Not Authenticated"
    error_code = 30
    status_code = 412 # Precondition Failed

class InternalServerError(GLException):
    """
    Error in interaction with the OS
    """
    reason = "Internal Server Error"
    error_code = 31
    status_code = 505

class NoEmailSpecified(GLException):
    reason = "No email was specified"
    error_code = 32
    status_code = 406

class DownloadLimitExceeded(GLException):
    reason = "You've reached the maximum amount of download for this file"
    error_code = 33
    status_code = 503 # Service Unavailable

class InvalidOldPassword(GLException):
    reason = "The specified old password is not valid"
    error_code = 34
    status_code = 406

class CommentNotFound(GLException):
    reason = "The specified comment was not found"
    error_code = 35
    status_code = 404

class StaticFileExist(GLException):
    error_code = 36
    status_code = 412 # Precondition Failed

    def __init__(self, filename):
        self.reason = "Static file [%s] is already present and overwrite is not permitted" % filename

