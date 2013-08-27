# -*- coding: UTF-8
#
#   errors
#   ******
#
# Here shall go all the error messages that a GLBackend can generate.
# GLException is the class inherit by the other Errors, and define the
# class variables expected in the Error handler routine

from cyclone.web import HTTPError
from globaleaks.settings import GLSetting

class GLException(HTTPError):
    reason = "GLTypesError not set"
    log_message = "GLException"
    error_code = 0
    status_code = 500 # generic Server error
    arguments = []

    def __init__(self):
        self.record()

    def __repr__(self):
        return "%s: <<%s>> (%d) HTTP:%d" % (
            self.__class__.__name__, self.reason,
            self.error_code, self.status_code
        )

    def record(self):
        log_message = "[GLE] %s  (code %d http %d)" % ( self.reason, self.error_code, self.status_code)
        print log_message

class InvalidInputFormat(GLException):
    """
    The expected format described in the REST specification is not
    respected by the data body in the HTTP request.
    """
    error_code = 10
    status_code = 406 # Not Acceptable

    def __init__(self, wrong_source):
        self.reason = "Invalid Input Format [%s]" % wrong_source
        self.arguments.append(wrong_source)
        self.record()


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
    reason = "The receiver has reach the maximum amount of access for this Tip"
    error_code = 18
    status_code = 503 # Servie Unavailable

class ExpectedUniqueField(GLException):
    """
    The receiver configuration ID do not exist in the database associated to the Receiver
    """
    error_code = 19
    status_code = 404 # Not Found

    def __init__(self, key, existent_value):
        self.reason = "A field expected to be unique is already present (%s:%s)" % (key, existent_value)
        self.arguments.append(key)
        self.arguments.append(existent_value)
        self.record()


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
        self.arguments.append(wrong_fields)
        self.record()


class InvalidTipAuthToken(GLException):
    """
    Authentication is failed, for Receiver or Whistleblower, because do not rely
    only in the secret Token (Tip Gus knowledge or receipt).
    """
    reason = "Authentication in Tip failed"
    error_code = 23
    status_code = 401 # Unauthorized

class InvalidScopeAuth(GLException):
    """
    A good login password combo is provided, but in the wrong scope (happen
    sometime when developers works with multiple accounts)
    """
    error_code = 24
    status_code = 403 # Forbidden

    def __init__(self, details):
        self.reason = ("Invalid Authentication in scope: %s" % details)
        self.arguments.append(details)


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
    The submission accessed haa been already completed
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
    The user attempted to access a not-authorized request. The output messages
    may contain reasons about the Authentication failure, but they are specify
    only if users has show knowledge of good credentials.
    """
    error_code = 30
    status_code = 412 # Precondition Failed
    reason = "Not Authenticated"

class InternalServerError(GLException):
    """
    Error in interaction with the OS
    """
    error_code = 31
    status_code = 500

    def __init__(self, details):
        self.reason = "Internal Server Error (%s)" % details
        self.arguments.append(details)
        self.record()


class NoEmailSpecified(GLException):
    """
    Receiver has email address as requirement (username is the email address) and
    is validated by a regular expression, if do not match, this error is triggered
    """
    reason = "No email was specified"
    error_code = 32
    status_code = 406

class DownloadLimitExceeded(GLException):
    """
    Receiver has reached the limit download counter configured in the Context
    """
    reason = "You've reached the maximum amount of download for this file"
    error_code = 33
    status_code = 503 # Service Unavailable

class InvalidOldPassword(GLException):
    """
    Receiver or Node required the old password equal to the current password,
    before change with a new secret.
    """
    reason = "The specified old password is not valid"
    error_code = 34
    status_code = 406

class CommentNotFound(GLException):
    """
    A Comment UUID expected has not been found
    """
    reason = "The specified comment was not found"
    error_code = 35
    status_code = 404

class InvalidHostSpecified(GLException):
    """
    The host delcared by the client 'Host:' field is not between
    the list of the acceptable hosts
    """
    reason = "The specified host do not match a configured one"
    error_code = 36
    status_code = 417 # Expectation Fail

class TorNetworkRequired(GLException):
    """
    A connection receiver not via Tor network is required to
    be enforced with anonymity
    """
    reason = "Resource can be accessed only within Tor network"
    error_code = 37
    status_code = 417 # Expectation Fail

class ReservedFileName(GLException):
    """
    The files uploaded in the static file directory, are also used for Receivers portrait
    and Node Logo.
    """
    error_code = 38
    status_code = 403 # Forbidden
    reason = "The file uploaded has a reserved name"

class HTTPRawLimitReach(GLException):
    """
    Raised by GLHTTPServer, when a raw upload is bigger than acceptable
    """
    error_code = 39
    status_code = 400 # Generic 400 error
    reason = ("The upload request overcome the Mb limits (%d Mb)" %
          GLSetting.memory_copy.maximum_filesize )
    arguments = [ GLSetting.memory_copy.maximum_filesize ]

class GPGKeyInvalid(GLException):
    """
    The proposed GPG key has an invalid format and can't be imported
    """
    error_code = 40
    status_code = 406
    reason = "The GPG key proposed can't be imported"

class InvalidReceiptRegexp(GLException):
    """
    context.receipt_regexp don't works
    """
    error_code = 41
    status_code = 406
    reason = "The receipt regexp is an invalid regexp"

class GPGKeyIDNotUnique(GLException):
    """
    A GPG key id need to be unique in the node
    Remind: not yet used
    """
    error_code = 42
    status_code =  406
    reason = "GPG Key ID it's already used by another receiver"

class AdminSessionExpired(GLException):
    error_code = 43
    status_code = 419 # Authentication Timeout
    reason = "The time for you Administrator is expired (max time: %s seconds) " % \
             GLSetting.defaults.lifetimes['admin']

class WbSessionExpired(GLException):
    error_code = 44
    status_code = 419 # Authentication Timeout
    reason = "The time for you whistleblower is expired (max time: %s seconds) " % \
             GLSetting.defaults.lifetimes['wb']

class ReceiverSessionExpired(GLException):
    error_code = 45
    status_code = 419 # Authentication Timeout
    reason = "The time for you receiver is expired (max time: %s seconds) " % \
             GLSetting.defaults.lifetimes['receiver']

class InvalidTipTimeToLive(GLException):
    """
    tip_timetolive and submission_timetolive maybe proposed of weird values,
    here is catch
    """
    error_code =  46
    status_code = 406
    reason = "Invalid timerange in Tip time to live"

class InvalidSubmTimeToLive(GLException):
    """
    tip_timetolive and submission_timetolive maybe proposed of weird values,
    here is catch
    """
    error_code =  47
    status_code = 406
    reason = "Invalid timerange in Submission time to live"

class InvalidTipSubmCombo(GLException):
    """
    tip_timetolive and submission_timetolive maybe proposed of weird values,
    here is catch
    """
    error_code =  48
    status_code = 406
    reason = "Submission time to life can't be more than Tip"
