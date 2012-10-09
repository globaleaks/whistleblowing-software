"""
This class has just dictionary values, derived by REST specification in
https://github.com/globaleaks/GlobaLeaks/wiki/API-Specification
"""

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
