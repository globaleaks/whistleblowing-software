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
