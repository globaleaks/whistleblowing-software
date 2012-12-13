# -*- coding: UTF-8
#
#   errors
#   ******
#
# Here shall go all the error messages that a GLBackend can generate.

class GLTypeError(Exception):

    error_message = "GLTypesError not set"
    error_code = 0
    http_status = 500 # generic Server error

class InvalidInputFormat(GLTypeError):

    def __init__(self):
        GLTypeError.error_message = "Invalid Input Format"
        GLTypeError.error_code = 100 # need to be resumed the table and come back in use them
        GLTypeError.http_status = 406 # Bad Request


# This is the struct containing the errors
def errorMessage(http_error_code=500, error_dict={}):
    """
    errorMessage may be used as inline object declaration and assignment
    """
    response = {'http_error_code':  http_error_code,
                'error_code': error_dict.get('code'),
                'error_message': error_dict.get('string')}
    return response

from cyclone.util import ObjectDict as OD

GLErrorCode = OD()

# All
GLErrorCode.malformed_requst = {'code': 0, 'message': 'Malformed Request'}

# U2,U3,U4
GLErrorCode.invalid_sID = {'code': 1, 'message': 'submission ID invalid'}

# U3
GLErrorCode.invalid_receiver = {'code': 2, 'message': 'selected receiver ID is invalid in the context'}

# U4
GLErrorCode.incomplete_fields = {'code': 3, 'message': 'fields requirement not respected'}
GLErrorCode.incomplete_upload = {'code': 4, 'message': 'An upload appears not yet completed'}

# U5 -- TODO, file upload interface
