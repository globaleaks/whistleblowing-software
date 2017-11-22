# -*- coding: utf-8
#
#   errors
#   ******
#
# Here shall go all the error messages that a GLBackend can generate.
# GLException is the class inherit by the other Errors, and define the
# class variables expected in the Error handler routine


class GLException(Exception):
    reason = "GLTypesError not set"
    log_message = "GLException"
    error_code = 0
    status_code = 500  # generic Server error

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "%s: <<%s>> (%d) HTTP:%d" % (
            self.__class__.__name__, self.reason,
            self.error_code, self.status_code
        )


class InternalServerError(GLException):
    """
    The context_id used does not exist in the database.
    """
    error_code = 1
    status_code = 500  # Internal Server Error

    def __init__(self, error_str):
        self.reason = "InternalServerError [%s]" % error_str
        self.arguments = [error_str]


class MethodNotImplemented(GLException):
    """
    The expected format described in the REST specification is not
    respected by the data body in the HTTP request.
    """
    error_code = 2
    status_code = 405  # Not Acceptable

    def __init__(self):
        self.reason = "Method not implemented"


class InvalidInputFormat(GLException):
    """
    The expected format described in the REST specification is not
    respected by the data body in the HTTP request.
    """
    error_code = 3
    status_code = 406  # Not Acceptable

    def __init__(self, wrong_source):
        self.reason = "Invalid Input Format [%s]" % wrong_source
        self.arguments = [wrong_source]


class TokenFailure(GLException):
    """
    Some kind of reason to reject a submission Token
    """
    error_code = 4
    status_code = 401  # Unauthorized

    def __init__(self, reason):
        self.reason = ("Unacceptable condition for usage of Token: %s" % reason)


class HTTPAuthenticationRequired(GLException):
    """
    Basic Authentication Required
    """
    reason = "Basic Authentication Required"
    error_code = 5
    status_code = 401  # Not Found


class ResourceNotFound(GLException):
    """
    Resource not found
    """
    reason = "Resource not found"
    error_code = 6
    status_code = 404  # Not Found


class ModelNotFound(ResourceNotFound):
    """
    Error class for a generic model
    """
    error_code = 7
    status_code = 404

    def __init__(self, model):
        ResourceNotFound.__init__(self)
        self.reason = "Model of type {} has not been found".format(model)


# UNUSED ERROR CODE 8-15 HERE!


class InvalidModelInput(GLException):
    """
    This error is used when a Model validation fails
    """
    error_code = 16
    status_code = 406  # Not Acceptable

    def __init__(self, wrong_source):
        self.reason = "Invalid Model Input [%s]" % wrong_source
        self.arguments = [wrong_source]

class WBFileIdNotFound(ResourceNotFound):
    """
    The wbfile_id used do not exist in the database.
    """
    reason = "Not found a WBFile the specified id"
    error_code = 17
    status_code = 404 # Not Found

class UserIdNotFound(ResourceNotFound):
    """
    Unable to find a user with the specified id.
    """
    reason = "Unable to find a user with the specified id."
    error_code = 18
    status_code = 404  # Not Found


class AdminIdNotFound(ResourceNotFound):
    """
    Unable to find an admin with the specified id.
    """
    reason = "Unable to find an admin with the specified id."
    error_code = 19
    status_code = 404  # Not Found


class CustodianIdNotFound(ResourceNotFound):
    """
    Unable to find a custodian with the specified id.
    """
    reason = "Unable to find a custodian with the specified id."
    error_code = 20
    status_code = 404  # Not Found


class ReceiverIdNotFound(ResourceNotFound):
    """
    Unable to find a receiver with the specified id.
    """
    reason = "Unable to find a receiver with the specified id."
    error_code = 21
    status_code = 404  # Not Found


class SubmissionValidationFailure(GLException):
    """
    If the fields required values and format type do not fit the requirement, this
    error is raised. The Client has to enforce as possible the Input Format, when this
    Client output validation fail, this error may happen.
    """
    error_code = 22
    status_code = 412  # Precondition Failed

    def __init__(self, wrong_field):
        self.reason = "Submission do not validate the input fields [%s]" % wrong_field
        self.arguments = [wrong_field]


# UNUSED ERROR CODE 23-24 HERE!


class ForbiddenOperation(GLException):
    """
    Receiver or Whistleblower has tried one operation not permitted by their privileges
    """
    reason = "Operation Forbidden"
    error_code = 25
    status_code = 403  # Forbidden


class FileIdNotFound(ResourceNotFound):
    """
    The requested file Id do not exist in the database
    """
    reason = "Not found a file with the specified id"
    error_code = 26
    status_code = 404  # Not Found


class ShortURLIdNotFound(ResourceNotFound):
    """
    The requested shorturl id do not exist in the database
    """
    reason = "Not found a shorturl with the specified id"
    error_code = 27
    status_code = 404  # Not Found


class FailedSanityCheck(GLException):
    reason = "Exceeded usage expectations of normal humans"
    error_code = 28
    status_code = 403  # Forbidden


class InvalidAuthentication(GLException):
    """
    An invalid request was presented
    """
    reason = "Authentication Failed"
    error_code = 29
    status_code = 401  # Unauthorized


class NotAuthenticated(GLException):
    """
    The user attempted to access a not-authorized request. The output messages
    may contain reasons about the Authentication failure, but they are specify
    only if users has show knowledge of good credentials.
    """
    error_code = 30
    status_code = 412  # Precondition Failed
    reason = "Not Authenticated"


class ValidationError(GLException):
    error_code = 31
    status_code = 403  # Forbidden

    def __init__(self, reason='Extended validation failed'):
        self.reason = reason


class ExternalResourceError(GLException):
    error_code = 32
    status_code = 400

    def __init__(self, reason='External resource did not respond correctly'):
        self.reason = reason


class InvalidOldPassword(GLException):
    """
    Receiver or Node required the old password equal to the current password,
    before change with a new secret.
    """
    reason = "The specified old password is not valid"
    error_code = 33
    status_code = 406


# UNUSED ERROR CODE 34 - 36 HERE!


class TorNetworkRequired(GLException):
    """
    A connection receiver not via Tor network is required to
    be enforced with anonymity
    """
    reason = "Resource can be accessed only within Tor network"
    error_code = 37
    status_code = 403  # Forbidden


class FileTooBig(GLException):
    """
    Raised by GLHTTPConnection, when the uploaded file is bigger than acceptable
    """
    error_code = 39
    status_code = 400  # Bad Request

    def __init__(self, size_limit):
        self.reason = ("Provided file upload overcomes size limits (%d Mb)" %
                       size_limit)
        self.arguments = [size_limit]


class PGPKeyInvalid(GLException):
    """
    The provided PGP key has an invalid format and can't be imported
    """
    reason = "The proposed PGP key can't be imported"
    error_code = 40
    status_code = 406


# UNUSED ERROR CODE 41-49 HERE!

class ExtendTipLifeNotEnabled(GLException):
    """
    Ability to postpone expiration date is not enabled in the node
    """
    reason = "This node does not permit expiration date extensions"
    error_code = 50
    status_code = 403


class StaticFileNotFound(ResourceNotFound):
    """
    It has been requested an operation on a non existent static file
    """
    reason = "Requested an operation on a non existent static file"
    error_code = 51
    status_code = 404


class LangFileNotFound(ResourceNotFound):
    """
    It has been requested an operation on a non existent language file
    """
    reason = "Requested an operation on a non existent language file"
    error_code = 52
    status_code = 404


class DirectoryTraversalError(GLException):
    """
    Blocked file operation out of the expected path
    """
    reason = "Blocked file operation out of the expected path"
    error_code = 53
    status_code = 403


class SubmissionDisabled(GLException):
    reason = "Submissions are not possible right now"
    error_code = 52
    status_code = 503  # Service not available
