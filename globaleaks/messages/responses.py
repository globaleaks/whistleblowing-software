# -*- coding: UTF-8
#   Answers
#   *******
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
#   This file contain the definition of all the answer struct perfomed by GLB,
#   and are used to make output validation, sanitization, and operations

# This is the struct containing the errors
def errorMessage(http_error_code=500, error_dict={}):
    """
    errorMessage may be used as inline object declaration and assignment
    """
    response = {'http_error_code':  http_error_code,
                'error_code': error_dict.get('code'),
                'error_message': error_dict.get('string')}
    return response

