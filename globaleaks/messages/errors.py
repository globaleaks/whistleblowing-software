"""
Here shall go all the error messages that a GLBackend can generate.
"""
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
